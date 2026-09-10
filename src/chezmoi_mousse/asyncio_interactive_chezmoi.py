from __future__ import annotations

import asyncio
import signal
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

type OutputHandler = Callable[[str], None]
type PromptHandler = Callable[[str], Awaitable[str]]


@asynccontextmanager
async def _managed_process(
    *cmd: str,
) -> AsyncGenerator[asyncio.subprocess.Process]:
    """Spawns an asyncio subprocess with guaranteed graceful cleanup on
    exit/cancellation."""
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
            # 1. Ask chezmoi nicely to terminate and release file locks
            with suppress(ProcessLookupError):
                process.send_signal(signal.SIGTERM)

            # 2. Give chezmoi a grace period to flush git state and exit
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except TimeoutError:
                # 3. Fallback to force kill if it hangs or ignores SIGTERM
                with suppress(ProcessLookupError):
                    process.kill()
                await process.wait()


async def run_interactive_stream(
    cmd: tuple[str, ...],
    on_output: OutputHandler,
    on_prompt: PromptHandler,
    read_timeout: float = 0.05,
) -> int:
    """Executes a chezmoi command, streams merged stdout/stderr, and intercepts
    prompts."""
    async with _managed_process(*cmd) as process:
        pipe_stdout = process.stdout
        pipe_stdin = process.stdin

        assert pipe_stdout is not None
        assert pipe_stdin is not None

        accumulated_text = ""

        while True:
            try:
                # Read bytes from the output pipe with a tight timeout
                raw_chunk = await asyncio.wait_for(
                    pipe_stdout.read(1024),
                    timeout=read_timeout,
                )

                if not raw_chunk:
                    # Process closed the pipe (EOF)
                    if accumulated_text:
                        on_output(accumulated_text)
                    break

                decoded_chunk = raw_chunk.decode("utf-8", errors="replace")
                accumulated_text += decoded_chunk

                # Flush completed lines to the UI
                if "\n" in accumulated_text:
                    complete_lines, accumulated_text = accumulated_text.rsplit("\n", 1)
                    on_output(complete_lines + "\n")

            except TimeoutError:
                # If buffer lacks a trailing newline, chezmoi is waiting on stdin!
                if accumulated_text and not accumulated_text.endswith("\n"):
                    prompt_text = accumulated_text
                    accumulated_text = (
                        ""  # Clear buffer before waiting for user decision
                    )

                    # 1. Ask Textual Modal for response
                    user_choice = await on_prompt(prompt_text)

                    # 2. Write response bytes directly into the stdin pipe
                    pipe_stdin.write(f"{user_choice}\n".encode())
                    await pipe_stdin.drain()

                elif accumulated_text:
                    # Buffer ends in a newline; normal operational pause between long
                    # outputs.
                    on_output(accumulated_text)
                    accumulated_text = ""

        return await process.wait()
