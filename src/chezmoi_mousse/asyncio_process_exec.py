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
from chezmoi_mousse.data_types import ExecResult
from chezmoi_mousse.str_enums import ChezmoiPrompts

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from chezmoi_mousse.str_enums import ReadCmd, WriteCmd

# e.g. "Apply .foo (diff/yes/no/all/quit)? "
_PROMPT_RE = re.compile(r"\(([^()]*)\)\? \Z")
_PROMPT_OPTIONS = frozenset(prompt.prompt_item for prompt in ChezmoiPrompts)
_GLOBAL_TIMEOUT = 15

__all__ = ["create_subprocess_exec_result", "run_chezmoi_interactive_process"]


async def create_subprocess_exec_result(
    chezmoi_args: tuple[str, ...],
    *,
    use_isolated_index: bool,
    cmd_enum: ReadCmd | WriteCmd,
) -> ExecResult:
    exec_args = (store.init_data.which_chezmoi, *chezmoi_args)

    env_vars: dict[str, str] | None = None
    temp_index_path: Path | None = None

    # Avoid locking the index when dry running a bunch of commands in parallel
    if use_isolated_index and store.cfg.git_index.exists():
        with tempfile.NamedTemporaryFile(prefix="cm_git_idx", delete=False) as tmp_file:
            temp_index_path = Path(tmp_file.name)

        shutil.copyfile(store.cfg.git_index, temp_index_path)
        env_vars = os.environ.copy()
        env_vars["GIT_INDEX_FILE"] = str(temp_index_path)

    try:
        process = await asyncio.create_subprocess_exec(
            *exec_args,
            env=env_vars,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async with asyncio.timeout(_GLOBAL_TIMEOUT):
                stdout_bytes, stderr_bytes = await process.communicate()
        except TimeoutError as time_out_error:
            process.kill()
            await process.wait()
            raise subprocess.TimeoutExpired(
                cmd=exec_args, timeout=_GLOBAL_TIMEOUT
            ) from time_out_error

        std_out = (stdout_bytes or b"").decode("utf-8", errors="replace")
        std_err = (stderr_bytes or b"").decode("utf-8", errors="replace")
        assert process.returncode is not None, "process did not return a code"
        return ExecResult(
            cmd_enum=cmd_enum,
            full_cmd=" ".join(exec_args),
            returncode=process.returncode,
            std_err=std_err,
            std_out=std_out,
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )

    finally:
        if temp_index_path and temp_index_path.exists():
            temp_index_path.unlink(missing_ok=True)
            Path(f"{temp_index_path}.lock").unlink(missing_ok=True)


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
async def _managed_process(*cmd: str) -> AsyncGenerator[asyncio.subprocess.Process]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        yield process
    finally:
        await _stop_process(process)


async def run_chezmoi_interactive_process(
    chezmoi_args: tuple[str, ...],
    prompt_handler: Callable[[str, list[str]], Awaitable[str]],
    *,
    cmd_enum: ReadCmd | WriteCmd,
) -> AsyncGenerator[list[str] | ExecResult]:
    read_timeout: float = 0.05
    interactive_approved = False
    exec_args = (store.init_data.which_chezmoi, *chezmoi_args)
    async with _managed_process(*exec_args) as process:
        pipe_stdout = process.stdout
        pipe_stdin = process.stdin
        pipe_stderr = process.stderr
        assert pipe_stdout is not None
        assert pipe_stdin is not None
        assert pipe_stderr is not None

        buffer = ""
        stderr_chunks: list[bytes] = []
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

                    prompt_match = _PROMPT_RE.search(buffer)
                    if prompt_match is None:
                        continue
                    prompt_options = prompt_match.group(1).split("/")
                    if any(option not in _PROMPT_OPTIONS for option in prompt_options):
                        continue

                    output_before_prompt, _, prompt_question = buffer[
                        : prompt_match.start()
                    ].rpartition("\n")
                    if output_before_prompt:
                        yield output_before_prompt.splitlines()
                    # Only post-prompt output belongs in the final result.
                    buffer = ""
                    user_choice = await prompt_handler(
                        prompt_question.strip(), prompt_options
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
                decoded_chunk = raw_chunk.decode("utf-8", errors="replace")
                buffer += decoded_chunk

            # EOF: flush remaining output, it must be yielded before leaving
            if buffer:
                yield buffer.splitlines()

            if timed_out:
                await _stop_process(process)
            returncode = await process.wait()

        std_err = b"".join(stderr_chunks).decode("utf-8", errors="replace")
        if timed_out:
            std_err = f"{std_err}\nChezmoi inactive for {_GLOBAL_TIMEOUT} seconds."
        yield ExecResult(
            cmd_enum=cmd_enum,
            full_cmd=" ".join(exec_args),
            interactive_approved=interactive_approved,
            returncode=returncode,
            std_err=std_err,
            std_out=buffer,
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )
