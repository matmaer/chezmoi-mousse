from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import TYPE_CHECKING

from textual.content import Content
from textual.highlight import HighlightTheme, highlight

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.asyncio_process_exec import (
    create_subprocess_exec_result,
    run_chezmoi_interactive_process,
)
from chezmoi_mousse.chezmoi_paths import ChezmoiTreePaths
from chezmoi_mousse.data_types import BtnDryData, CommandResult
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Chars,
    LogStr,
    ReadCmd,
    StatusCode as Sc,
    WriteCmd,
)

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import AsyncGenerator, Awaitable, Callable, Iterable

    from chezmoi_mousse.data_types import ExecResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

_PATH_PATTERN = re.compile(r"^diff --git a/.* b/(.*)$")


class _NoErrorHighlightTheme(HighlightTheme): ...


# Content based language guesses can be wrong, don't flag the mismatches as errors in
# the highlighting.
_NoErrorHighlightTheme.STYLES = {
    token: style
    for token, style in HighlightTheme.STYLES.items()
    if "error-muted" not in style
}


def _highlight_str(to_highlight: str, file_path: Path) -> Content:
    return highlight(to_highlight, path=str(file_path), theme=_NoErrorHighlightTheme)


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
    isolated_index = cmd_enum in ReadCmd.dry_commands()
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
        app.logs_tab.cmd_result = command_result
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


async def _get_btn_dry_run_data(
    app: ChezmoiGui, btn_label: BtnLabel, path: Path
) -> BtnDryData:
    verb_arg = None if path == store.cfg.dest_dir else path

    def parse_paths(out_list: list[str]) -> list[Path]:
        # Matches standard git diff paths (capturing the target path in group 1)
        paths: set[Path] = set()
        for line in out_list:
            match = _PATH_PATTERN.match(line)
            if match:
                relative_path = Path(match.group(1))
                abs_path = store.cfg.dest_dir / relative_path
                paths.add(abs_path)
        return path_funcs.sort_paths(paths)

    def pretty_op_paths(parsed_paths: list[Path]) -> str:
        strings: list[str] = [f"{Chars.bullet} {line}" for line in parsed_paths]
        return "\n".join(strings)

    cr: CommandResult = await run_chezmoi_cmd(app, btn_label.dry_cmd, verb_arg=verb_arg)
    parsed_paths: list[Path] = parse_paths(cr.out_list)
    if not parsed_paths:
        return BtnDryData(op_path=path, no_op=True, pretty_str=LogStr.no_op)
    return BtnDryData(
        op_path=path, no_op=False, pretty_str=pretty_op_paths(parsed_paths)
    )


async def get_dry_run_data(app: ChezmoiGui, path: Path) -> dict[BtnLabel, BtnDryData]:
    result_dict: dict[BtnLabel, BtnDryData] = {}
    task_workers: dict[BtnLabel, Task[BtnDryData]] = {}
    if path == store.cfg.dest_dir:
        no = [BtnLabel.chezmoi_add, BtnLabel.chezmoi_forget, BtnLabel.chezmoi_destroy]
        result_dict.update(
            {label: BtnDryData(op_path=path, no_op=True) for label in no}
        )
    async with asyncio.TaskGroup() as tg:
        for btn_label in BtnLabel.op_btn_labels():
            if btn_label in result_dict:
                continue
            task_workers[btn_label] = tg.create_task(
                _get_btn_dry_run_data(app, btn_label, path)
            )

    for label, data in task_workers.items():
        btn_dry_data: BtnDryData = data.result()
        result_dict[label] = btn_dry_data
    return dict(sorted(result_dict.items()))


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
            ReadCmd.dry_apply,
            ReadCmd.dry_re_add,
        ],
    )
    man_dirs_cr = cm_path_cr[ReadCmd.managed_dirs]
    man_files_cr = cm_path_cr[ReadCmd.managed_files]
    dry_apply_cr = cm_path_cr[ReadCmd.dry_apply]
    dry_re_add_cr = cm_path_cr[ReadCmd.dry_re_add]

    async def get_source_paths(
        targets: list[str], pretty_verb_arg: LogStr
    ) -> list[str]:
        # Without arguments, "chezmoi source-path" returns the source dir itself.
        if not targets:
            return []
        cmd_result = await run_chezmoi_cmd(
            app, ReadCmd.source_path, verb_arg=targets, pretty_verb_arg=pretty_verb_arg
        )
        return cmd_result.out_list

    async with asyncio.TaskGroup() as tg:
        source_dirs_task = tg.create_task(
            get_source_paths(man_dirs_cr.out_list, LogStr.on_managed_dirs)
        )
        source_files_task = tg.create_task(
            get_source_paths(man_files_cr.out_list, LogStr.on_managed_files)
        )

    target_dirs = parse_paths(man_dirs_cr.out_list)
    target_files = parse_paths(man_files_cr.out_list)
    source_dirs = parse_paths(source_dirs_task.result())
    source_files = parse_paths(source_files_task.result())
    dry_apply = parse_paths(dry_apply_cr.out_list)
    dry_re_add = parse_paths(dry_re_add_cr.out_list)

    return ChezmoiTreePaths(
        _dest_dir=store.cfg.dest_dir,
        _man_dirs=dict(zip(target_dirs, source_dirs, strict=True)),
        _man_files=dict(zip(target_files, source_files, strict=True)),
        _status_dirs=parse_status_output(cm_path_cr[ReadCmd.status_dirs]),
        _status_files=parse_status_output(cm_path_cr[ReadCmd.status_files]),
        _un_man_dirs=parse_paths_to_set(cm_path_cr[ReadCmd.unmanaged_dirs]),
        _un_man_files=parse_paths_to_set(cm_path_cr[ReadCmd.unmanaged_files]),
        _dry_apply={BtnLabel.chezmoi_apply: dry_apply},
        _dry_re_add={BtnLabel.chezmoi_re_add: dry_re_add},
    )


def get_highlighted_file_contents(file_path: Path) -> Content:
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
        return Content(str(e))
    return _highlight_str(f_contents, file_path)


async def get_highlighted_chezmoi_cat_output(
    app: ChezmoiGui, *, file_path: Path
) -> Content:
    cmd_result = await _exec_chezmoi(
        app,
        ReadCmd.cat,
        (*ReadCmd.cat.value, str(file_path)),
        str(file_path.relative_to(store.cfg.dest_dir)),
    )
    f_contents = cmd_result.std_out
    if not f_contents.strip():
        return Content("File is empty or contains only whitespace")
    return _highlight_str(f_contents, file_path)


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
