from __future__ import annotations

import asyncio
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.data_types import CommandResult
from chezmoi_mousse.str_enums import ChezmoiPrompts, WriteCmd

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from chezmoi_mousse.str_enums import ReadCmd

CHEZMOI = shutil.which("chezmoi")


# e.g. "Apply .foo (diff/yes/no/all/quit)? "
_PROMPT_RE = re.compile(r"\(([^()]*)\)\? \Z")
_PROMPT_OPTIONS = frozenset(prompt.prompt_item for prompt in ChezmoiPrompts)
_GLOBAL_TIMEOUT = 15

__all__ = ["create_interactive_managed_process", "get_process_cmd_result"]


async def get_process_cmd_result(
    chezmoi_args: tuple[str, ...], *, cmd_enum: ReadCmd | WriteCmd, pretty_cmd: str
) -> CommandResult:
    if cmd_enum in WriteCmd.no_op_commands():
        raise ValueError(f"Received wrong cmd_enum: {cmd_enum}")
    assert CHEZMOI is not None
    exec_args = (CHEZMOI, *chezmoi_args)

    async with _managed_process(*chezmoi_args, use_isolated_index=False) as process:
        try:
            async with asyncio.timeout(_GLOBAL_TIMEOUT):
                stdout_bytes, stderr_bytes = await process.communicate()
        except TimeoutError as time_out_error:
            raise subprocess.TimeoutExpired(
                cmd=exec_args, timeout=_GLOBAL_TIMEOUT
            ) from time_out_error

    std_out = (stdout_bytes or b"").decode("utf-8", errors="replace")
    std_err = (stderr_bytes or b"").decode("utf-8", errors="replace")
    assert process.returncode is not None, "process did not return a code"
    return CommandResult(
        cmd_enum=cmd_enum,
        full_cmd=" ".join(exec_args),
        pretty_cmd=pretty_cmd,
        returncode=process.returncode,
        std_err=std_err,
        std_out=std_out,
        time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
    )


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    """SIGTERM first, SIGKILL if the process hasn't exited after 2 seconds."""
    if process.returncode is not None:
        return
    with suppress(ProcessLookupError):
        process.send_signal(signal.SIGTERM)
    try:
        await asyncio.wait_for(process.wait(), timeout=2.0)
    except TimeoutError:
        with suppress(ProcessLookupError):
            process.kill()
        await process.wait()


@asynccontextmanager
async def _managed_process(
    *cmd: str, use_isolated_index: bool = False
) -> AsyncGenerator[asyncio.subprocess.Process]:
    assert CHEZMOI is not None
    env_vars: dict[str, str] | None = None
    temp_index_path: Path | None = None
    try:
        # Parallel scope checks must not compete for the real Git index.
        if use_isolated_index and store.cfg.git_index.exists():
            with tempfile.NamedTemporaryFile(
                prefix="cm_git_idx", delete=False
            ) as tmp_file:
                temp_index_path = Path(tmp_file.name)
            shutil.copyfile(store.cfg.git_index, temp_index_path)
            env_vars = os.environ.copy()
            env_vars["GIT_INDEX_FILE"] = str(temp_index_path)

        process = await asyncio.create_subprocess_exec(
            CHEZMOI,
            *cmd,
            env=env_vars,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            yield process
        finally:
            await _stop_process(process)
    finally:
        if temp_index_path is not None:
            temp_index_path.unlink(missing_ok=True)
            Path(f"{temp_index_path}.lock").unlink(missing_ok=True)


async def create_interactive_managed_process(
    chezmoi_args: tuple[str, ...],
    prompt_handler: Callable[[str, list[str], str], Awaitable[str]],
    output_handler: Callable[[str], Awaitable[None]],
    *,
    cmd_enum: ReadCmd | WriteCmd,
    pretty_cmd: str,
) -> CommandResult:
    read_timeout: float = 0.05
    interactive_approved = False
    async with _managed_process(
        *chezmoi_args, use_isolated_index=cmd_enum in WriteCmd.no_op_commands()
    ) as process:
        pipe_stdout = process.stdout
        pipe_stdin = process.stdin
        pipe_stderr = process.stderr
        assert pipe_stdout is not None
        assert pipe_stdin is not None
        assert pipe_stderr is not None

        buffer = b""
        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []
        displayed_stderr_chunks = 0
        last_activity = time.monotonic()
        timed_out = False

        async def read_stderr() -> None:
            nonlocal last_activity
            while stderr_chunk := await pipe_stderr.read(1024):
                stderr_chunks.append(stderr_chunk)
                last_activity = time.monotonic()

        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(read_stderr())

            while not pipe_stdout.at_eof():
                try:
                    raw_chunk = await asyncio.wait_for(
                        pipe_stdout.read(1024), timeout=read_timeout
                    )
                except TimeoutError:
                    if time.monotonic() - last_activity > _GLOBAL_TIMEOUT:
                        timed_out = True
                        break

                    decoded_buffer = buffer.decode("utf-8", errors="replace")
                    prompt_match = _PROMPT_RE.search(decoded_buffer)
                    if prompt_match is None:
                        continue
                    prompt_options = prompt_match.group(1).split("/")
                    if any(option not in _PROMPT_OPTIONS for option in prompt_options):
                        continue

                    output_before_prompt, separator, prompt_question = decoded_buffer[
                        : prompt_match.start()
                    ].rpartition("\n")
                    pending_stderr = b"".join(
                        stderr_chunks[displayed_stderr_chunks:]
                    ).decode("utf-8", errors="replace")
                    displayed_stderr_chunks = len(stderr_chunks)
                    if pending_stderr:
                        await output_handler(pending_stderr)
                    buffer = b""
                    user_choice = await prompt_handler(
                        prompt_question.strip(),
                        prompt_options,
                        output_before_prompt + separator,
                    )
                    if user_choice not in ChezmoiPrompts.non_operation_replies():
                        interactive_approved = True
                    pipe_stdin.write(f"{user_choice}\n".encode())
                    await pipe_stdin.drain()
                    last_activity = time.monotonic()
                    continue

                if not raw_chunk:
                    break

                last_activity = time.monotonic()
                stdout_chunks.append(raw_chunk)
                buffer += raw_chunk

            if timed_out:
                await _stop_process(process)
            returncode = await process.wait()

        remaining_output = buffer.decode("utf-8", errors="replace") + b"".join(
            stderr_chunks[displayed_stderr_chunks:]
        ).decode("utf-8", errors="replace")
        if remaining_output:
            await output_handler(remaining_output)
        std_err = b"".join(stderr_chunks).decode("utf-8", errors="replace")
        if timed_out:
            std_err = f"{std_err}\nChezmoi inactive for {_GLOBAL_TIMEOUT} seconds."
        return CommandResult(
            cmd_enum=cmd_enum,
            full_cmd=" ".join(["chezmoi", *chezmoi_args]),
            interactive_approved=interactive_approved,
            pretty_cmd=pretty_cmd,
            returncode=returncode,
            std_err=std_err,
            std_out=b"".join(stdout_chunks).decode("utf-8", errors="replace"),
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )
