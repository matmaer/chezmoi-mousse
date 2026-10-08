from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.asyncio_process_exec import (
    create_subprocess_exec_result,
    run_chezmoi_interactive_process,
)
from chezmoi_mousse.chezmoi_paths import ChezmoiTreePaths
from chezmoi_mousse.data_types import CommandResult
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import LogStr, ReadCmd, StatusCode as Sc, WriteCmd

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from chezmoi_mousse.asyncio_process_exec import ExecResult
    from chezmoi_mousse.data_types import StreamEvent
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


def pretty_cmd(cmd: ReadCmd | WriteCmd, verb_arg: Path | str | None) -> str:
    if verb_arg is None:
        pretty_verb_arg = ""
    elif isinstance(verb_arg, Path):
        pretty_verb_arg = path_funcs.get_rel_path_str(verb_arg)
    else:
        pretty_verb_arg = verb_arg
    return (f"{cmd.pretty_cmd} {pretty_verb_arg}").rstrip()


async def _construct_command_result(
    exec_result: ExecResult,
    cmd_enum: ReadCmd | WriteCmd,
    chezmoi_args: tuple[str, ...],
    pretty_verb_arg: str | None,
) -> CommandResult:
    std_out = exec_result[0]
    std_err = exec_result[1]
    result_code = exec_result[2]
    out_list = std_out.splitlines()
    full_cmd: str = f"chezmoi {' '.join(chezmoi_args)}"
    return CommandResult(
        cmd_enum=cmd_enum,
        full_cmd=full_cmd,
        pretty_cmd=f"{pretty_cmd(cmd_enum, pretty_verb_arg)}",
        returncode=result_code,
        std_err=std_err,
        std_out=std_out,
        out_list=out_list,
        time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
    )


async def _exec_chezmoi(
    app: ChezmoiGui,
    cmd_enum: ReadCmd | WriteCmd,
    chezmoi_args: tuple[str, ...],
    pretty_verb_arg: str | None,
) -> CommandResult:
    exec_result: ExecResult = await create_subprocess_exec_result(chezmoi_args)
    command_result = await _construct_command_result(
        exec_result, cmd_enum, chezmoi_args, pretty_verb_arg
    )
    if app.screen.name == "splash_screen":
        if cmd_enum is ReadCmd.source_path:
            prefix_suffix = (ReadCmd.source_path.pretty_cmd, LogStr(pretty_verb_arg))
            await app.splash_screen.write_log_msg(prefix_suffix=prefix_suffix)
        else:
            await app.splash_screen.write_log_msg(cmd_result=command_result)
    if app.init_phase is False:
        app.app_log.cmd_result = command_result
        app.cmd_log.cmd_result = command_result
    app.post_message(CommandResultMsg(command_result))
    return command_result


async def run_chezmoi_cmd(
    app: ChezmoiGui,
    cmd_enum: ReadCmd | WriteCmd,
    *,
    verb_arg: Path | list[str] | None,
    pretty_verb_arg: str | None = None,
) -> CommandResult:
    chezmoi_args: tuple[str, ...] | None = None
    if cmd_enum is not ReadCmd.source_path and isinstance(verb_arg, (str, list)):
        raise ValueError(
            f"Passing verb args as strings is only allowed for "
            f"{ReadCmd.source_path.pretty_cmd}"
        )
    elif cmd_enum is ReadCmd.source_path and pretty_verb_arg is None:
        raise ValueError(
            f"Passing a string to represent the pretty version of the verb arg is "
            f"mandatory for {ReadCmd.source_path.pretty_cmd}"
        )

    if isinstance(verb_arg, list):
        chezmoi_args = (*cmd_enum.value, *verb_arg)
    elif isinstance(verb_arg, Path):
        chezmoi_args = (*cmd_enum.value, str(verb_arg))
        pretty_verb_arg = path_funcs.get_rel_path_str(verb_arg)
    elif verb_arg is None:
        chezmoi_args = (*cmd_enum.value,)
    return await _exec_chezmoi(app, cmd_enum, chezmoi_args, pretty_verb_arg)


async def run_in_task_group(app: ChezmoiGui, commands: tuple[ReadCmd, ...]) -> None:
    async with asyncio.TaskGroup() as tg:
        for cmd_enum in commands:
            tg.create_task(
                run_chezmoi_cmd(app, cmd_enum, verb_arg=None, pretty_verb_arg=None)
            )


@staticmethod
async def get_affected_paths(
    app: ChezmoiGui, write_cmd: WriteCmd, path: Path
) -> list[Path]:
    if write_cmd in (
        WriteCmd.dry_add,
        WriteCmd.dry_apply,
        WriteCmd.dry_re_add,
        WriteCmd.dry_forget,
        WriteCmd.dry_destroy,
    ):
        app.notify(f"Running dry command: {write_cmd.name} on path: {path}")
        command_result = await _exec_chezmoi(
            app,
            write_cmd,
            (*write_cmd.value, str(path)),
            str(path.relative_to(store.cfg.dest_dir)),
        )
        # Matches standard git diff paths (capturing the target path in group 1)
        path_pattern = re.compile(r"^diff --git a/.* b/(.*)$")
        affected_paths: set[Path] = set()
        for line in command_result.out_list:
            match = path_pattern.match(line)
            if match:
                affected_paths.add(Path(match.group(1)))
        return path_funcs.sort_paths(affected_paths)
    else:
        app.notify(
            f"Wrong write command:{write_cmd.name} for get_affected_paths.",
            severity="error",
        )
        return []


async def run_managed_commands(app: ChezmoiGui) -> None:

    def parse_paths_to_set(cmd_result: CommandResult) -> set[Path]:
        return {Path(line) for line in cmd_result.out_list}

    def parse_paths(cmd_result: CommandResult) -> list[Path]:
        return [Path(line) for line in cmd_result.out_list]

    def parse_status_output(cmd_result: CommandResult) -> dict[Path, Sc]:
        return {Path(line[3:]): Sc(line[:2]) for line in cmd_result.out_list}

    async with asyncio.TaskGroup() as tg:
        man_dirs_task = tg.create_task(
            run_chezmoi_cmd(app, ReadCmd.managed_dirs, verb_arg=None)
        )
        man_files_task = tg.create_task(
            run_chezmoi_cmd(app, ReadCmd.managed_files, verb_arg=None)
        )
        status_dirs_task = tg.create_task(
            run_chezmoi_cmd(app, ReadCmd.status_dirs, verb_arg=None)
        )
        status_files_task = tg.create_task(
            run_chezmoi_cmd(app, ReadCmd.status_files, verb_arg=None)
        )
        unman_dirs_task = tg.create_task(
            run_chezmoi_cmd(app, ReadCmd.unmanaged_dirs, verb_arg=None)
        )
        unman_files_task = tg.create_task(
            run_chezmoi_cmd(app, ReadCmd.unmanaged_files, verb_arg=None)
        )

    man_dirs_cr: CommandResult = man_dirs_task.result()
    man_files_cr: CommandResult = man_files_task.result()

    async with asyncio.TaskGroup() as tg:
        source_dirs_task = tg.create_task(
            run_chezmoi_cmd(
                app,
                ReadCmd.source_path,
                verb_arg=man_dirs_cr.out_list,
                pretty_verb_arg=LogStr.on_managed_dirs,
            )
        )
        source_files_task = tg.create_task(
            run_chezmoi_cmd(
                app,
                ReadCmd.source_path,
                verb_arg=man_files_cr.out_list,
                pretty_verb_arg=LogStr.on_managed_files,
            )
        )

    target_dirs: list[Path] = parse_paths(man_dirs_cr)
    target_files: list[Path] = parse_paths(man_files_cr)
    source_dirs: list[Path] = parse_paths(source_dirs_task.result())
    source_files: list[Path] = parse_paths(source_files_task.result())

    man_dirs: dict[Path, Path] = dict(zip(target_dirs, source_dirs, strict=True))
    man_files: dict[Path, Path] = dict(zip(target_files, source_files, strict=True))

    status_dirs: dict[Path, Sc] = parse_status_output(status_dirs_task.result())
    status_files: dict[Path, Sc] = parse_status_output(status_files_task.result())
    un_man_dirs: set[Path] = parse_paths_to_set(unman_dirs_task.result())
    un_man_files: set[Path] = parse_paths_to_set(unman_files_task.result())

    tree_paths = ChezmoiTreePaths(
        _dest_dir=store.cfg.dest_dir,
        _man_dirs=man_dirs,
        _man_files=man_files,
        _status_dirs=status_dirs,
        _status_files=status_files,
        _status_path_set=status_files.keys() | status_dirs.keys(),
        _un_man_dirs=un_man_dirs,
        _un_man_files=un_man_files,
        _un_man_paths=un_man_files | un_man_dirs,
    )
    await store.handle_new_tree_paths(app, tree_paths)


def get_highlighted_file_contents(file_path: Path) -> Text:
    if file_path.is_dir():
        raise ValueError(f"Trying to get file contents for a directory: {file_path}")
    try:
        max_chars = 500000
        with file_path.open("r", encoding="utf-8") as f:
            # Over-read by 1 char to test truncation in 1 I/O btn_label
            data = f.read(max_chars + 1)
        truncated = len(data) > max_chars
        f_contents = data[:max_chars]
        if not f_contents.strip():
            f_contents = "File is empty or contains only whitespace"
        elif truncated:
            f_contents += f"\n--- Read file limited to {max_chars} characters ---"
    except (PermissionError, OSError, UnicodeDecodeError) as e:
        f_contents = str(e)
    text_contents = Text(f_contents)
    ReprHighlighter().highlight(text_contents)
    return text_contents


async def get_highlighted_chezmoi_cat_output(
    app: ChezmoiGui,
    *,
    file_path: Path,
) -> Text:
    cmd_result = await _exec_chezmoi(
        app,
        ReadCmd.cat,
        (*ReadCmd.cat.value, str(file_path)),
        str(file_path.relative_to(store.cfg.dest_dir)),
    )
    f_contents = cmd_result.std_out
    if not f_contents.strip():
        f_contents = "File is empty or contains only whitespace"
    text_contents = Text(f_contents)
    ReprHighlighter().highlight(text_contents)
    return text_contents


def run_chezmoi_interactive(
    app: ChezmoiGui,
    cmd_enum: WriteCmd,
    path_arg: Path | None,
) -> AsyncGenerator[StreamEvent, str | None]:
    app.notify(f"Running {cmd_enum.name} on {path_arg}")
    return run_chezmoi_interactive_process(cmd_enum, path_arg)
