from __future__ import annotations

import asyncio
import re
import signal
import subprocess
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING

from chezmoi_mousse import store

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from chezmoi_mousse.str_enums import ReadCmd, WriteCmd


type ExecResult = tuple[str, str, int]  # std_out, std_err, returncode

# e.g. "Apply .foo (diff/yes/no/all/quit)? "
_PROMPT_RE = re.compile(r"\(([^()]*)\)\? $")


__all__ = [
    "ExecResult",
    "create_subprocess_exec_result",
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
    cmd_enum: ReadCmd | WriteCmd,
    path: Path | None,
    time_out: int = 15,
) -> ExecResult:
    chezmoi_cmd = _get_chezmoi_cmd()
    exec_args = (
        (chezmoi_cmd, *cmd_enum.value, str(path))
        if path is not None
        else (
            chezmoi_cmd,
            *cmd_enum.value,
        )
    )

    process = await asyncio.create_subprocess_exec(
        *exec_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        async with asyncio.timeout(time_out):
            stdout_bytes, stderr_bytes = await process.communicate()
    except TimeoutError as e:
        process.kill()
        await process.wait()
        raise subprocess.TimeoutExpired(
            cmd=exec_args,
            timeout=time_out,
        ) from e

    std_out = (stdout_bytes or b"").decode("utf-8", errors="replace").strip("\r\n")
    std_err = (stderr_bytes or b"").decode("utf-8", errors="replace").strip("\r\n")
    assert process.returncode is not None, "process did not return a code"
    return std_out, std_err, process.returncode


@dataclass(slots=True, frozen=True)
class StreamEvent:
    data: list[str]
    is_prompt: bool


@asynccontextmanager
async def _managed_process(
    *cmd: str,
) -> AsyncGenerator[asyncio.subprocess.Process]:
    """Manages process lifecycle, ensuring clean SIGTERM shutdown on exit."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        yield process
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except TimeoutError:
                with suppress(ProcessLookupError):
                    process.kill()
                await process.wait()


async def run_chezmoi_interactive_process(
    cmd_enum: WriteCmd,
    path: Path | None,
) -> AsyncGenerator[StreamEvent, str | None]:
    read_timeout: float = 0.05
    max_process_idle_seconds: float = 15.0
    chezmoi_cmd = _get_chezmoi_cmd()
    exec_args = (
        (chezmoi_cmd, *cmd_enum.value, str(path))
        if path is not None
        else (chezmoi_cmd, *cmd_enum.value)
    )

    async with _managed_process(*exec_args) as process:
        pipe_stdout = process.stdout
        pipe_stdin = process.stdin
        assert pipe_stdout is not None
        assert pipe_stdin is not None

        buffer = ""
        last_process_activity = time.monotonic()

        while not pipe_stdout.at_eof():
            payload: list[str] | None = None
            is_prompt = False

            try:
                raw_chunk = await asyncio.wait_for(
                    pipe_stdout.read(1024),
                    timeout=read_timeout,
                )

                if not raw_chunk:
                    # EOF: flush remaining output, it must be yielded before leaving
                    if buffer:
                        yield StreamEvent(data=buffer.splitlines(), is_prompt=False)
                    break

                last_process_activity = time.monotonic()
                buffer += raw_chunk.decode("utf-8", errors="replace")

            except TimeoutError as read_time_out:
                if time.monotonic() - last_process_activity > max_process_idle_seconds:
                    raise TimeoutError(
                        f"Chezmoi inactive for {max_process_idle_seconds} seconds."
                    ) from read_time_out

                if buffer.endswith("\n"):
                    payload = buffer.splitlines()
                    buffer = ""
                elif prompt_match := _PROMPT_RE.search(buffer):
                    # Silence for read_timeout plus a prompt-shaped ending.
                    # NOTE: prompt is different than running commands with a tty!
                    is_prompt = True
                    payload = prompt_match.group(1).split("/")
                    buffer = ""  # Only clear buffer when yielding prompt!

            if payload is not None:
                # Receive input directly back from asend()
                user_choice = yield StreamEvent(data=payload, is_prompt=is_prompt)

                if is_prompt:
                    if user_choice is None:
                        raise ValueError(
                            "A prompt needs a reply; to cancel call aclose() instead"
                        )
                    pipe_stdin.write(f"{user_choice}\n".encode())
                    await pipe_stdin.drain()

                last_process_activity = time.monotonic()
