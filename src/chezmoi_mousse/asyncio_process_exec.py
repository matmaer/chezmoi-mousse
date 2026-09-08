from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import GlobalArgs, ReadCmd

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.str_enums import WriteCmd


type ExecResult = tuple[str, str, int]  # std_out, std_err, returncode


def check_chezmoi_cmd() -> str | None:
    return shutil.which("chezmoi")


def _get_chezmoi_cmd() -> str:
    if store.init_data.which_chezmoi is None:
        raise RuntimeError(
            "Trying to run a chezmoi command when it's not available or before it's "
            "set in store.init_data.which_chezmoi"
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


async def get_affected_paths(verb: str, path: str) -> ExecResult:
    run_cmd: tuple[str, ...] = (
        *_get_base_cmd_tuple(live_run=False),
        GlobalArgs.verbose.value,
        verb,
        path,
    )
    process = await asyncio.create_subprocess_exec(
        *run_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_paths: set[str] = set()
    stderr_paths: set[str] = set()
    path_pattern = re.compile(r"^diff --git a/.* b/(.*)$")
    time_out = 15

    async def read_stdout() -> None:
        assert process.stdout is not None, "stdout pipe was not opened"
        async for line_bytes in process.stdout:
            nonlocal stdout_paths
            std_out = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            if match := path_pattern.match(std_out):
                stdout_paths.add(match.group(1))

    async def read_stderr() -> None:
        assert process.stderr is not None, "stderr pipe was not opened"
        async for line_bytes in process.stderr:
            nonlocal stderr_paths
            line_str = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
            if match := path_pattern.match(line_str):
                stderr_paths.add(match.group(1))

    try:
        async with asyncio.timeout(time_out):
            async with asyncio.TaskGroup() as tg:
                tg.create_task(read_stdout())
                tg.create_task(read_stderr())
            # Both pipes are now completely read; wait for process exit
            returncode = await process.wait()
            result = (
                "\n".join(sorted(stdout_paths)),
                "\n".join(sorted(stderr_paths)),
                returncode,
            )
    except TimeoutError as e:
        process.kill()
        await process.wait()
        returncode = e.errno if e.errno is not None else -1
        message = (
            f"process timed out after {time_out} seconds, for command: "
            f"{' '.join(run_cmd)}"
        )
        return ("process timed out", message, returncode)

    return result


async def execute_chezmoi_command(
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
