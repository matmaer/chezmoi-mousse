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
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.data_types import StreamEvent

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


type ExecResult = tuple[str, str, int]  # std_out, std_err, returncode

# e.g. "Apply .foo (diff/yes/no/all/quit)? "
_PROMPT_RE = re.compile(r"\(([^()]*)\)\? \Z")
_GLOBAL_TIMEOUT = 15

__all__ = [
    "ExecResult",
    "create_subprocess_exec_result",
    "run_chezmoi_interactive_process",
]


def _get_chezmoi_cmd() -> str:
    if store.init_data.which_chezmoi is None:
        raise RuntimeError(
            "Trying to run a chezmoi command when it's not available or before it's "
            "set in store.init_data.which_chezmoi"
        )
    elif store.init_data.which_git is None:
        raise RuntimeError(
            "Trying to run a chezmoi command when git is not available or before it's "
            "set in store.init_data.which_git"
        )
    return store.init_data.which_chezmoi


async def create_subprocess_exec_result(
    chezmoi_args: tuple[str, ...],
    *,
    use_isolated_index: bool,
) -> ExecResult:
    chezmoi_cmd = _get_chezmoi_cmd()
    exec_args = (chezmoi_cmd, *chezmoi_args)

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
                cmd=exec_args,
                timeout=_GLOBAL_TIMEOUT,
            ) from time_out_error

        std_out = (stdout_bytes or b"").decode("utf-8", errors="replace").strip("\r\n")
        std_err = (stderr_bytes or b"").decode("utf-8", errors="replace").strip("\r\n")
        assert process.returncode is not None, "process did not return a code"
        return std_out, std_err, process.returncode

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
async def _managed_process(
    *cmd: str,
) -> AsyncGenerator[asyncio.subprocess.Process]:
    """Manages process lifecycle, ensuring clean SIGTERM shutdown on exit."""
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
) -> AsyncGenerator[StreamEvent, str | None]:
    read_timeout: float = 0.05
    chezmoi_cmd = _get_chezmoi_cmd()
    exec_args = (chezmoi_cmd, *chezmoi_args)
    async with _managed_process(*exec_args) as process:
        pipe_stdout = process.stdout
        pipe_stdin = process.stdin
        assert pipe_stdout is not None
        assert pipe_stdin is not None
        assert process.stderr is not None

        # Drained concurrently, a full stderr pipe would block chezmoi
        stderr_task = asyncio.create_task(process.stderr.read())

        buffer = ""
        full_std_out = ""
        last_process_activity = time.monotonic()
        timed_out = False

        while not pipe_stdout.at_eof():
            try:
                raw_chunk = await asyncio.wait_for(
                    pipe_stdout.read(1024),
                    timeout=read_timeout,
                )
            except TimeoutError:
                if time.monotonic() - last_process_activity > _GLOBAL_TIMEOUT:
                    timed_out = True
                    break

                prompt_match = _PROMPT_RE.search(buffer)
                if prompt_match is None:
                    continue

                # Silence for read_timeout plus a prompt-shaped ending.
                # NOTE: prompt is different than running commands with a tty!
                # Complete lines before the prompt line, e.g. the output of the
                # diff option, must not be lost.
                output_before_prompt, _, prompt_question = buffer[
                    : prompt_match.start()
                ].rpartition("\n")
                if output_before_prompt:
                    yield StreamEvent(
                        data=output_before_prompt.splitlines(), is_prompt=False
                    )
                prompt_options = prompt_match.group(1).split("/")
                buffer = ""  # Only clear buffer when yielding prompt!

                # Receive input directly back from asend()
                user_choice = yield StreamEvent(
                    data=prompt_options,
                    is_prompt=True,
                    prompt_question=prompt_question.strip(),
                )
                if user_choice is None:
                    raise ValueError(
                        "A prompt needs a reply; to cancel call aclose() instead"
                    ) from None
                pipe_stdin.write(f"{user_choice}\n".encode())
                await pipe_stdin.drain()
                last_process_activity = time.monotonic()
                continue

            if not raw_chunk:
                break

            last_process_activity = time.monotonic()
            decoded_chunk = raw_chunk.decode("utf-8", errors="replace")
            buffer += decoded_chunk
            full_std_out += decoded_chunk

        # EOF: flush remaining output, it must be yielded before leaving
        if buffer:
            yield StreamEvent(data=buffer.splitlines(), is_prompt=False)

        if timed_out:
            await _stop_process(process)
        returncode = await process.wait()
        std_err = (await stderr_task).decode("utf-8", errors="replace")
        if timed_out:
            std_err = f"{std_err}\nChezmoi inactive for {_GLOBAL_TIMEOUT} seconds."
        yield StreamEvent(
            data=[],
            is_prompt=False,
            returncode=returncode,
            std_out=full_std_out.strip("\r\n"),
            std_err=std_err.strip("\r\n"),
        )
