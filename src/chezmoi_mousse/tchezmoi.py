from __future__ import annotations

import asyncio
import re
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
from chezmoi_mousse.data_types import CommandResult, DryRunData
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LogStr,
    ReadCmd,
    StatusCode as Sc,
    WriteCmd,
)

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncGenerator, Awaitable, Callable, Iterable

    from chezmoi_mousse.asyncio_process_exec import ExecResult
    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

_PATH_PATTERN = re.compile(r"^diff --git a/.* b/(.*)$")


def _highlight_str(to_highlight: str) -> Text:
    text = Text(to_highlight)
    ReprHighlighter().highlight(text)
    return text


def pretty_cmd(cmd: ReadCmd | WriteCmd, verb_arg: Path | str | None) -> str:
    if verb_arg is None:
        pretty_verb_arg = ""
    elif isinstance(verb_arg, Path):
        pretty_verb_arg = path_funcs.get_rel_path_str(verb_arg)
    else:
        pretty_verb_arg = verb_arg
    return (f"{cmd.pretty_cmd} {pretty_verb_arg}").rstrip()


async def _exec_chezmoi(
    app: ChezmoiGui,
    cmd_enum: ReadCmd | WriteCmd,
    chezmoi_args: tuple[str, ...],
    pretty_verb_arg: str | None,
) -> CommandResult:
    if cmd_enum in (
        ReadCmd.dry_add,
        ReadCmd.dry_apply,
        ReadCmd.dry_destroy,
        ReadCmd.dry_forget,
        ReadCmd.dry_re_add,
    ):
        isolated_index = True
    else:
        isolated_index = False

    exec_result: ExecResult = await create_subprocess_exec_result(
        chezmoi_args, use_isolated_index=isolated_index, cmd_enum=cmd_enum
    )
    command_result = CommandResult(
        cmd_enum=cmd_enum,
        full_cmd=exec_result.full_cmd,
        pretty_cmd=f"{pretty_cmd(cmd_enum, pretty_verb_arg)}",
        returncode=exec_result.returncode,
        std_err=exec_result.std_err,
        std_out=exec_result.std_out,
        time_stamp=exec_result.time_stamp,
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
    if cmd_enum is not ReadCmd.source_path and isinstance(verb_arg, list):
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
    app: ChezmoiGui, commands: Iterable[ReadCmd], path: Path | None = None
) -> dict[ReadCmd, CommandResult]:
    tasks_by_cmd: dict[ReadCmd, Task[CommandResult]] = {}
    async with asyncio.TaskGroup() as tg:
        for cmd_enum in commands:
            tasks_by_cmd[cmd_enum] = tg.create_task(
                run_chezmoi_cmd(app, cmd_enum, verb_arg=path, pretty_verb_arg=None)
            )
    cmd_to_cr_map: dict[ReadCmd, CommandResult] = {
        cmd: task.result() for cmd, task in tasks_by_cmd.items()
    }
    return cmd_to_cr_map


async def run_affected_paths(
    app: ChezmoiGui, n_data: NodeData, path_arg: Path | None = None
) -> DryRunData:

    default_result: dict[BtnLabel, list[Path] | None] = {
        BtnLabel.chezmoi_add: None,
        BtnLabel.chezmoi_apply: None,
        BtnLabel.chezmoi_destroy: None,
        BtnLabel.chezmoi_forget: None,
        BtnLabel.chezmoi_re_add: None,
    }

    # basic affected paths for dest_dir
    if n_data.dest_dir:
        default_result[BtnLabel.chezmoi_add] = []
        default_result[BtnLabel.chezmoi_destroy] = []
        default_result[BtnLabel.chezmoi_forget] = []
        if not n_data.nested_status:
            default_result[BtnLabel.chezmoi_apply] = []
            default_result[BtnLabel.chezmoi_re_add] = []
    # basic affected paths for dirs other than the dest dir
    elif n_data.un_managed_dir:
        default_result[BtnLabel.chezmoi_apply] = []
        default_result[BtnLabel.chezmoi_destroy] = []
        default_result[BtnLabel.chezmoi_forget] = []
        default_result[BtnLabel.chezmoi_re_add] = []
    # basic affected paths for managed dirs without nested conditions
    elif n_data.managed_dir:
        if not (n_data.nested_un_managed or n_data.nested_status or n_data.status_dir):
            default_result[BtnLabel.chezmoi_add] = []
        if not (n_data.nested_status or n_data.status_dir):
            default_result[BtnLabel.chezmoi_apply] = []
            default_result[BtnLabel.chezmoi_re_add] = []
        elif not n_data.nested_managed and n_data.status_dir:
            default_result[BtnLabel.chezmoi_apply] = [n_data.path]
            default_result[BtnLabel.chezmoi_re_add] = [n_data.path]
        if not n_data.exists:
            default_result[BtnLabel.chezmoi_destroy] = []
        elif n_data.exists and not (n_data.nested_managed or n_data.nested_un_managed):
            default_result[BtnLabel.chezmoi_destroy] = [n_data.path]
        if not n_data.nested_managed:
            default_result[BtnLabel.chezmoi_forget] = [n_data.path]
    # basic affected paths for files
    elif n_data.managed_file:
        default_result[BtnLabel.chezmoi_add] = []
        default_result[BtnLabel.chezmoi_forget] = [n_data.path]
        if n_data.exists:
            default_result[BtnLabel.chezmoi_destroy] = [n_data.path]
        else:
            default_result[BtnLabel.chezmoi_destroy] = []
        if n_data.status_file:
            default_result[BtnLabel.chezmoi_apply] = [n_data.path]
            default_result[BtnLabel.chezmoi_re_add] = [n_data.path]
        elif not n_data.status_file:
            default_result[BtnLabel.chezmoi_apply] = []
            default_result[BtnLabel.chezmoi_re_add] = []
    elif n_data.un_managed_file:
        default_result[BtnLabel.chezmoi_add] = [n_data.path]
        default_result[BtnLabel.chezmoi_apply] = []
        default_result[BtnLabel.chezmoi_destroy] = []
        default_result[BtnLabel.chezmoi_forget] = []
        default_result[BtnLabel.chezmoi_re_add] = []

    dry_run_data = DryRunData()

    for k, v in default_result.items():
        if v is not None:
            setattr(dry_run_data, k.name, default_result[k])

    def parse_paths(cr: CommandResult) -> list[Path]:
        # Matches standard git diff paths (capturing the target path in group 1)
        paths: set[Path] = set()
        for line in cr.out_list:
            match = _PATH_PATTERN.match(line)
            if match:
                relative_path = Path(match.group(1))
                abs_path = store.cfg.dest_dir / relative_path
                paths.add(abs_path)
        return path_funcs.sort_paths(paths)

    commands_to_run = [k.dry_cmd for k, v in default_result.items() if v is None]
    path_arg = None if n_data.dest_dir else n_data.path
    cr_results: dict[ReadCmd, CommandResult] = await run_in_task_group(
        app, commands_to_run, path_arg
    )
    for k, cr in cr_results.items():
        setattr(dry_run_data, k.name, parse_paths(cr))
    return dry_run_data


async def run_managed_commands(app: ChezmoiGui) -> ChezmoiTreePaths:

    def parse_paths(path_strings: list[str]) -> list[Path]:
        return [Path(line) for line in path_strings]

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

    target_dirs = parse_paths(man_dirs_cr.out_list)
    target_files = parse_paths(man_files_cr.out_list)
    source_dirs = parse_paths(source_dirs_task.result().out_list)
    source_files = parse_paths(source_files_task.result().out_list)

    return ChezmoiTreePaths(
        _dest_dir=store.cfg.dest_dir,
        _man_dirs=dict(zip(target_dirs, source_dirs, strict=True)),
        _man_files=dict(zip(target_files, source_files, strict=True)),
        _status_dirs=parse_status_output(cm_path_cr[ReadCmd.status_dirs]),
        _status_files=parse_status_output(cm_path_cr[ReadCmd.status_files]),
        _un_man_dirs=parse_paths_to_set(cm_path_cr[ReadCmd.unmanaged_dirs]),
        _un_man_files=parse_paths_to_set(cm_path_cr[ReadCmd.unmanaged_files]),
    )


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
    return _highlight_str(f_contents)


async def get_highlighted_chezmoi_cat_output(
    app: ChezmoiGui, *, file_path: Path
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
    return _highlight_str(f_contents)


def run_chezmoi_interactive(
    cmd_enum: WriteCmd,
    verb_arg: Path | list[str] | None,
    prompt_handler: Callable[[str, list[str]], Awaitable[str]],
) -> AsyncGenerator[list[str] | ExecResult]:
    chezmoi_args: tuple[str, ...] | None = None
    if cmd_enum is not WriteCmd.add and isinstance(verb_arg, list):
        raise ValueError(
            f"Passing verb args as strings is only allowed for "
            f"{WriteCmd.add.pretty_cmd}"
        )
    elif cmd_enum in (WriteCmd.add, WriteCmd.destroy, WriteCmd.forget) and (
        verb_arg is None or verb_arg == store.cfg.dest_dir
    ):
        raise ValueError(f"{WriteCmd.add.pretty_cmd} cannot run on the dest dir.")
    if isinstance(verb_arg, list):
        chezmoi_args = (*cmd_enum.value, *verb_arg)
    elif verb_arg is None or verb_arg == store.cfg.dest_dir:
        chezmoi_args = (*cmd_enum.value,)
    else:
        chezmoi_args = (*cmd_enum.value, str(verb_arg))
    return run_chezmoi_interactive_process(
        chezmoi_args, prompt_handler, cmd_enum=cmd_enum
    )
