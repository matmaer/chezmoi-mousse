from __future__ import annotations

import asyncio
import signal
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


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
    cmd: tuple[str, ...],
    read_timeout: float = 0.05,
    max_process_idle_seconds: float = 15.0,
) -> AsyncGenerator[StreamEvent]:
    """Yields StreamEvent objects containing (lines_or_choices, is_prompt)."""
    async with _managed_process(*cmd) as process:
        pipe_stdout = process.stdout
        assert pipe_stdout is not None

        buffer = ""
        result = ""
        last_process_activity = time.monotonic()

        while not pipe_stdout.at_eof():
            payload: list[str] = []
            is_prompt = False

            try:
                raw_chunk = await asyncio.wait_for(
                    pipe_stdout.read(1024),
                    timeout=read_timeout,
                )

                if not raw_chunk:
                    # EOF hit: flush remaining output on process completion
                    result = buffer
                    buffer = ""
                    break

                # Bytes arrived: accumulate strictly into buffer
                last_process_activity = time.monotonic()
                buffer += raw_chunk.decode("utf-8", errors="replace")

            except TimeoutError as read_time_out:
                if time.monotonic() - last_process_activity > max_process_idle_seconds:
                    raise TimeoutError(
                        f"Chezmoi inactive for {max_process_idle_seconds} seconds."
                    ) from read_time_out

                # Nothing new arrived after 0.05s -> evaluate result
                is_prompt = not result.endswith("\n")
                if is_prompt:
                    payload = list(result.rsplit(">", 1)[1].split("/"))
                else:
                    payload = buffer.splitlines()

                buffer = ""
                result = ""

            yield StreamEvent(data=payload, is_prompt=is_prompt)
            last_process_activity = time.monotonic()
