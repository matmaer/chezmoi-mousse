from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import TYPE_CHECKING

from textual.content import Content
from textual.highlight import HighlightTheme, highlight

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.asyncio_process_exec import (
    create_interactive_process,
    get_process_cmd_result,
)
from chezmoi_mousse.chezmoi_paths import ChezmoiTreePaths
from chezmoi_mousse.data_types import BtnDryData
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import (
    Chars,
    ChezmoiPrompts,
    ColorVar,
    LogStr,
    ReadCmd,
    StatusCode as Sc,
    WriteCmd,
)

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import Awaitable, Callable, Iterable

    from chezmoi_mousse.data_types import BtnLabelDryDict, CommandResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import BtnLabel

_PATH_PATTERN = re.compile(r"^diff --git a/.* b/(.*)$")


class _NoErrorHighlightTheme(HighlightTheme): ...


# Content based language guesses can be wrong, don't flag the mismatches as errors in
# the highlighting.
_NoErrorHighlightTheme.STYLES = {
    token: style
    for token, style in HighlightTheme.STYLES.items()
    if "error-muted" not in style
}


async def _log_in_app(app: ChezmoiGui, messages: list[str]) -> None:
    for message in messages:
        app.logs_tab.mount_line(message, ColorVar.secondary)


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

    command_result = await get_process_cmd_result(
        chezmoi_args,
        cmd_enum=cmd_enum,
        pretty_cmd=pretty_cmd(cmd_enum, pretty_verb_arg),
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


async def _parse_paths(path_strings: list[str]) -> list[Path]:
    return [Path(line) for line in path_strings]


async def _parse_managed_data(
    app: ChezmoiGui, cmd_results: list[CommandResult]
) -> dict[ReadCmd, list[Path] | dict[Path, Sc]]:

    async def parse_and_filter_paths(path_strings: list[str]) -> list[Path]:
        parsed_paths = await _parse_paths(path_strings)
        return [path for path in parsed_paths if not path_funcs.is_ignored_dir(path)]

    async def parse_and_filter_files(path_strings: list[str]) -> list[Path]:
        return [
            Path(line)
            for line in path_strings
            if not path_funcs.is_ignored_dir(Path(line))
        ]

    async def parse_status_output(out_lines: list[str]) -> dict[Path, Sc]:
        return {Path(line[3:]): Sc(line[:2]) for line in out_lines}

    tasks_by_cmd: dict[ReadCmd, Task[list[Path] | dict[Path, Sc]]] = {}
    async with asyncio.TaskGroup() as tg:
        for result in cmd_results:
            assert isinstance(result.cmd_enum, ReadCmd)
            if result.cmd_enum == ReadCmd.unmanaged_dirs:
                tasks_by_cmd[result.cmd_enum] = tg.create_task(
                    parse_and_filter_paths(result.out_list)
                )
            elif result.cmd_enum == ReadCmd.unmanaged_files:
                tasks_by_cmd[result.cmd_enum] = tg.create_task(
                    parse_and_filter_files(result.out_list)
                )
            elif result.cmd_enum in (ReadCmd.status_dirs, ReadCmd.status_files):
                tasks_by_cmd[result.cmd_enum] = tg.create_task(
                    parse_status_output(result.out_list)
                )
            else:
                tasks_by_cmd[result.cmd_enum] = tg.create_task(
                    _parse_paths(result.out_list)
                )
    parsed_data: dict[ReadCmd, list[Path] | dict[Path, Sc]] = {}
    for cmd, task in tasks_by_cmd.items():
        parsed_data[cmd] = task.result()
    log_messages: list[str] = []
    for cmd, paths in parsed_data.items():
        log_messages.append(f"{cmd.pretty_cmd} (parsed {len(paths)})")
    app.call_later(_log_in_app, app, log_messages)
    return parsed_data


async def run_managed_commands(app: ChezmoiGui) -> ChezmoiTreePaths:

    cmd_to_cr_map: dict[ReadCmd, CommandResult] = await run_in_task_group(
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

    man_dirs_cr = cmd_to_cr_map[ReadCmd.managed_dirs]
    man_files_cr = cmd_to_cr_map[ReadCmd.managed_files]

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
    source_dirs = await _parse_paths(source_dirs_task.result())
    source_files = await _parse_paths(source_files_task.result())

    parsed_data = await _parse_managed_data(
        app,
        [
            cmd_to_cr_map[ReadCmd.managed_dirs],
            cmd_to_cr_map[ReadCmd.managed_files],
            cmd_to_cr_map[ReadCmd.status_dirs],
            cmd_to_cr_map[ReadCmd.status_files],
            cmd_to_cr_map[ReadCmd.unmanaged_dirs],
            cmd_to_cr_map[ReadCmd.unmanaged_files],
        ],
    )
    managed_dirs = parsed_data[ReadCmd.managed_dirs]
    managed_files = parsed_data[ReadCmd.managed_files]
    status_dirs = parsed_data[ReadCmd.status_dirs]
    status_files = parsed_data[ReadCmd.status_files]
    assert isinstance(status_dirs, dict)
    assert isinstance(status_files, dict)

    return ChezmoiTreePaths(
        _dest_dir=store.cfg.dest_dir,
        _man_dirs=dict(zip(managed_dirs, source_dirs, strict=True)),
        _man_files=dict(zip(managed_files, source_files, strict=True)),
        _status_dirs=status_dirs,
        _status_files=status_files,
        _un_man_dirs=set(parsed_data[ReadCmd.unmanaged_dirs]),
        _un_man_files=set(parsed_data[ReadCmd.unmanaged_files]),
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
    cmd_result = await run_chezmoi_cmd(
        app,
        ReadCmd.cat,
        verb_arg=file_path,
        pretty_verb_arg=str(file_path.relative_to(store.cfg.dest_dir)),
    )
    f_contents = cmd_result.std_out
    if not f_contents.strip():
        return Content("File is empty or contains only whitespace")
    return _highlight_str(f_contents, file_path)


async def collect_chezmoi_paths_in_scope(
    app: ChezmoiGui, path: Path
) -> BtnLabelDryDict:
    async def ignore_output(_output: str) -> None:
        pass

    async def collect_command(cmd_enum: WriteCmd) -> BtnDryData:
        paths: list[str] = []

        async def answer_no(
            question: str, options: list[str], _output_before_prompt: str
        ) -> str:
            _, separator, path_text = question.partition(" ")
            if not separator or not path_text:
                raise ValueError(f"Unexpected chezmoi question: {question!r}")
            if cmd_enum is WriteCmd.no_op_destroy:
                path_text = path_text.partition(f" and {store.cfg.source_dir_str}")[0]
            paths.append(path_text)

            if ChezmoiPrompts.no.prompt_item not in options:
                return ChezmoiPrompts.quit.reply
            return ChezmoiPrompts.no.reply

        cr: CommandResult = await run_chezmoi_interactive(
            cmd_enum, path, answer_no, ignore_output, pretty_verb_arg=None
        )
        app.logs_tab.cmd_result = cr
        if cr.std_err or cr.returncode != 0:
            return BtnDryData(
                op_path=path,
                no_op=True,
                pretty_str=(
                    cr.std_err or f"{cr.pretty_cmd} exited with {cr.returncode}"
                ),
            )
        return BtnDryData(
            op_path=path,
            no_op=not paths,
            pretty_str=(
                "\n".join(f"{Chars.bullet} {item}" for item in paths)
                if paths
                else LogStr.no_op
            ),
        )

    results: BtnLabelDryDict = {}
    tasks: dict[BtnLabel, Task[BtnDryData]] = {}
    async with asyncio.TaskGroup() as task_group:
        for command in WriteCmd.no_op_commands():
            if path == store.cfg.dest_dir and command in (
                WriteCmd.no_op_add,
                WriteCmd.no_op_destroy,
                WriteCmd.no_op_forget,
            ):
                results[command.btn_label] = BtnDryData(op_path=path, no_op=True)
            else:
                tasks[command.btn_label] = task_group.create_task(
                    collect_command(command)
                )
    results.update({label: task.result() for label, task in tasks.items()})
    return dict(sorted(results.items()))


async def run_chezmoi_interactive(
    cmd_enum: WriteCmd,
    verb_arg: Path | list[str] | None,
    prompt_handler: Callable[[str, list[str], str], Awaitable[str]],
    output_handler: Callable[[str], Awaitable[None]],
    *,
    pretty_verb_arg: Path | str | None,
) -> CommandResult:
    chezmoi_args: tuple[str, ...] | None = None
    if cmd_enum in (WriteCmd.add, WriteCmd.destroy, WriteCmd.forget) and (
        verb_arg is None or verb_arg == store.cfg.dest_dir
    ):
        raise ValueError(f"{cmd_enum.pretty_cmd} cannot run on the dest dir.")
    if isinstance(verb_arg, list):
        chezmoi_args = (*cmd_enum.value, *verb_arg)
    elif verb_arg is None or verb_arg == store.cfg.dest_dir:
        chezmoi_args = (*cmd_enum.value,)
    else:
        chezmoi_args = (*cmd_enum.value, str(verb_arg))
    return await create_interactive_process(
        chezmoi_args,
        prompt_handler,
        output_handler,
        cmd_enum=cmd_enum,
        pretty_cmd=pretty_cmd(cmd_enum, pretty_verb_arg),
    )
