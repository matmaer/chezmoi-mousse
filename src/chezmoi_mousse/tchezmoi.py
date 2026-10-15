from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
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
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LogStr,
    ReadCmd,
    StatusCode as Sc,
)

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncGenerator, Iterable

    from chezmoi_mousse.asyncio_process_exec import ExecResult
    from chezmoi_mousse.data_types import NodeData, StreamEvent
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import (
        WriteCmd,
    )

__all__ = ["OperatePaths"]


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


async def run_in_task_group(
    app: ChezmoiGui,
    commands: Iterable[ReadCmd],
    path: Path | None = None,
) -> dict[ReadCmd, CommandResult]:
    tasks_by_cmd: dict[ReadCmd, Task[CommandResult]] = {}
    verb_arg = None if path is None else path
    async with asyncio.TaskGroup() as tg:
        for cmd_enum in commands:
            tasks_by_cmd[cmd_enum] = tg.create_task(
                run_chezmoi_cmd(app, cmd_enum, verb_arg=verb_arg, pretty_verb_arg=None)
            )
    cmd_to_cr_map: dict[ReadCmd, CommandResult] = {
        cmd: task.result() for cmd, task in tasks_by_cmd.items()
    }
    return cmd_to_cr_map


@dataclass
class OperatePaths:
    _affected_paths: dict[Path, dict[str, list[Path]]] = field(
        default_factory=dict[Path, dict[str, list[Path]]]
    )

    async def enable_button(
        self, app: ChezmoiGui, btn_label: str, node_data: NodeData
    ) -> bool:
        result = await self.get_affected_paths(app, btn_label, node_data)
        return len(result) > 0

    async def get_affected_paths(
        self, app: ChezmoiGui, btn_label: str, node_data: NodeData
    ) -> list[Path]:
        if node_data.path in self._affected_paths:
            return self._affected_paths[node_data.path][btn_label]
        else:
            result: dict[str, list[Path]] = await _run_affected_paths(app, node_data)
            self._affected_paths[node_data.path] = result
            return self._affected_paths[node_data.path][btn_label]


@staticmethod
async def _run_affected_paths(
    app: ChezmoiGui, n_data: NodeData
) -> dict[str, list[Path]]:
    result: dict[ReadCmd, list[Path] | None] = {
        ReadCmd.dry_add: None,
        ReadCmd.dry_apply: None,
        ReadCmd.dry_destroy: None,
        ReadCmd.dry_forget: None,
        ReadCmd.dry_re_add: None,
    }

    # basic affected paths for dest_dir
    if n_data.dest_dir:
        result[ReadCmd.dry_add] = []
        result[ReadCmd.dry_destroy] = []
        result[ReadCmd.dry_forget] = []
    # basic affected paths for dirs other than the dest dir
    elif n_data.un_managed_dir:
        result[ReadCmd.dry_apply] = []
        result[ReadCmd.dry_destroy] = []
        result[ReadCmd.dry_forget] = []
        result[ReadCmd.dry_re_add] = []
    # basic affected paths for files
    elif n_data.managed_file:
        result[ReadCmd.dry_forget] = [n_data.path]
        result[ReadCmd.dry_destroy] = [n_data.path]
        if n_data.status_file:
            result[ReadCmd.dry_apply] = [n_data.path]
            result[ReadCmd.dry_re_add] = [n_data.path]
        elif not n_data.status_file:
            result[ReadCmd.dry_apply] = []
            result[ReadCmd.dry_re_add] = []
    elif n_data.un_managed_file:
        result[ReadCmd.dry_add] = [n_data.path]
        result[ReadCmd.dry_apply] = []
        result[ReadCmd.dry_destroy] = []
        result[ReadCmd.dry_forget] = []
        result[ReadCmd.dry_re_add] = []

    read_cmd_to_write_btn_label: dict[ReadCmd, BtnLabel] = {
        ReadCmd.dry_add: BtnLabel.chezmoi_add,
        ReadCmd.dry_apply: BtnLabel.chezmoi_apply,
        ReadCmd.dry_destroy: BtnLabel.chezmoi_destroy,
        ReadCmd.dry_forget: BtnLabel.chezmoi_forget,
        ReadCmd.dry_re_add: BtnLabel.chezmoi_re_add,
    }
    to_run: list[ReadCmd] = [cmd for cmd, value in result.items() if value is None]
    path_arg = None if n_data.dest_dir else n_data.path
    cmd_results: dict[ReadCmd, CommandResult] = await run_in_task_group(
        app, to_run, path_arg
    )
    for cmd, cr in cmd_results.items():
        result[cmd] = path_funcs.parse_paths(cr.out_list)

    to_return: dict[str, list[Path]] = {}
    for cmd, value in result.items():
        to_return[read_cmd_to_write_btn_label[cmd]] = value if value is not None else []

    return to_return


async def run_managed_commands(app: ChezmoiGui) -> None:

    def parse_paths_to_set(cmd_result: CommandResult) -> set[Path]:
        return {Path(line) for line in cmd_result.out_list}

    def parse_status_output(cmd_result: CommandResult) -> dict[Path, Sc]:
        return {Path(line[3:]): Sc(line[:2]) for line in cmd_result.out_list}

    cm_path_cr: dict[ReadCmd, CommandResult] = await run_in_task_group(
        app,
        [
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
            ReadCmd.unmanaged_dirs,
            ReadCmd.unmanaged_files,
        ],
    )
    man_dirs_cr = cm_path_cr[ReadCmd.managed_dirs]
    man_files_cr = cm_path_cr[ReadCmd.managed_files]

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

    target_dirs = path_funcs.parse_paths(man_dirs_cr.out_list)
    target_files = path_funcs.parse_paths(man_files_cr.out_list)
    source_dirs = path_funcs.parse_paths(source_dirs_task.result().out_list)
    source_files = path_funcs.parse_paths(source_files_task.result().out_list)

    tree_paths = ChezmoiTreePaths(
        _dest_dir=store.cfg.dest_dir,
        _man_dirs=dict(zip(target_dirs, source_dirs, strict=True)),
        _man_files=dict(zip(target_files, source_files, strict=True)),
        _status_dirs=parse_status_output(cm_path_cr[ReadCmd.status_dirs]),
        _status_files=parse_status_output(cm_path_cr[ReadCmd.status_files]),
        _un_man_dirs=parse_paths_to_set(cm_path_cr[ReadCmd.unmanaged_dirs]),
        _un_man_files=parse_paths_to_set(cm_path_cr[ReadCmd.unmanaged_files]),
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
