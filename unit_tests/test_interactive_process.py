from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest import mock

import pytest

from chezmoi_mousse import asyncio_process_exec as proc

if TYPE_CHECKING:
    from chezmoi_mousse.data_types import StreamEvent
    from chezmoi_mousse.str_enums import WriteCmd


def run_fake_chezmoi(
    script: str, replies: list[str | None], global_timeout: float = 15
) -> list[StreamEvent]:
    """Runs python code as stand-in for chezmoi, answering prompts with replies."""
    fake_cmd = cast("WriteCmd", SimpleNamespace(value=("-c", script)))

    async def drive() -> list[StreamEvent]:
        events: list[StreamEvent] = []
        pending = iter(replies)
        gen = proc.run_chezmoi_interactive_process(fake_cmd, None)
        reply: str | None = None
        try:
            while True:
                event = await gen.asend(reply)
                events.append(event)
                reply = next(pending) if event.is_prompt else None
        except StopAsyncIteration:
            return events
        finally:
            await gen.aclose()

    with (
        mock.patch.object(proc, "_get_chezmoi_cmd", return_value=sys.executable),
        mock.patch.object(proc, "_GLOBAL_TIMEOUT", global_timeout),
    ):
        return asyncio.run(drive())


def test_prompt_is_answered_and_result_collected() -> None:
    script = "print('Apply foo (yes/no)? ', end='', flush=True);print('got ' + input())"
    events = run_fake_chezmoi(script, ["yes"])

    prompt = events[0]
    assert prompt.is_prompt
    assert prompt.prompt_question == "Apply foo"
    assert prompt.data == ["yes", "no"]
    final = events[-1]
    assert final.returncode == 0
    assert "got yes" in final.std_out


def test_output_before_prompt_is_one_event() -> None:
    script = (
        "print('line 1'); print('line 2');"
        "print('Apply foo (yes/no)? ', end='', flush=True); input()"
    )
    events = run_fake_chezmoi(script, ["no"])

    assert not events[0].is_prompt
    assert events[0].data == ["line 1", "line 2"]
    assert events[1].is_prompt


def test_silence_ends_with_failed_result_instead_of_raising() -> None:
    script = "import time; print('hello', flush=True); time.sleep(30)"
    events = run_fake_chezmoi(script, [], global_timeout=1)

    final = events[-1]
    assert final.returncode != 0
    assert final.std_out == "hello"
    assert "inactive" in final.std_err


def test_process_ignoring_sigterm_is_killed() -> None:
    script = (
        "import signal, time;"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
        "print('hello', flush=True); time.sleep(30)"
    )
    events = run_fake_chezmoi(script, [], global_timeout=1)

    assert events[-1].returncode == -9


def test_prompt_shaped_line_with_trailing_newline_is_not_a_prompt() -> None:
    # stays alive so the silence check runs on the buffer before EOF arrives
    script = "import time; print('Apply foo (yes/no)? ', flush=True); time.sleep(0.5)"
    events = run_fake_chezmoi(script, [])

    assert not any(event.is_prompt for event in events)
    assert events[-1].returncode == 0


def test_prompt_without_reply_raises_value_error() -> None:
    script = "print('Apply foo (yes/no)? ', end='', flush=True); input()"

    with pytest.raises(ValueError, match="needs a reply"):
        run_fake_chezmoi(script, [None])
