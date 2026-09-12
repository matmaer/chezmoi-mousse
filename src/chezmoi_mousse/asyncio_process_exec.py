from __future__ import annotations

import asyncio
import subprocess
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import GlobalArgs, ReadCmd

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.str_enums import WriteCmd


type ExecResult = tuple[str, str, int]  # std_out, std_err, returncode


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


def _get_base_cmd_tuple(*, live_run: bool) -> tuple[str, ...]:
    chezmoi_cmd = _get_chezmoi_cmd()
    if live_run is True:
        return (
            chezmoi_cmd,
            *GlobalArgs.global_defaults.value,
        )
    return (
        chezmoi_cmd,
        GlobalArgs.dry_run.value,
        *GlobalArgs.global_defaults.value,
    )


async def create_subprocess_exec_result(
    cmd_enum: ReadCmd | WriteCmd,
    path: Path | None,
    time_out: int = 15,
) -> ExecResult:
    live_run = store.live_run or isinstance(cmd_enum, ReadCmd)
    base_cmd = _get_base_cmd_tuple(live_run=live_run)
    exec_args = base_cmd + cmd_enum.value
    if path is not None:
        exec_args = (*exec_args, str(path))

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
