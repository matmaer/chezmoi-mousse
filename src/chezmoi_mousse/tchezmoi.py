from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.asyncio_process_exec import create_subprocess_exec_result
from chezmoi_mousse.chezmoi_paths import ChezmoiTreePaths
from chezmoi_mousse.data_types import CommandResult
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import ReactiveVar, ReadCmd, StatusCode as Sc, WriteCmd

if TYPE_CHECKING:
    from chezmoi_mousse.asyncio_process_exec import (
        ExecResult,
    )
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


def _get_full_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    path_str = str(path) if path is not None else ""
    return f"chezmoi {' '.join(cmd.value)} {path_str}".rstrip()


def pretty_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    rel_path = path_funcs.get_rel_path(path)
    return (f"{cmd.pretty_cmd} {rel_path}").rstrip()


async def _construct_command_result(
    exec_result: ExecResult, cmd_enum: ReadCmd | WriteCmd, path_arg: Path | None
) -> CommandResult:
    std_out = exec_result[0]
    std_err = exec_result[1]
    result_code = exec_result[2]
    out_list = []
    if not std_out and not std_err:
        out_lines: list[str] = []
        out_lines.append("Output on stdout:")
        out_lines.append(std_out)
        out_lines.append("Output on stderr:")
        out_lines.append(std_err)
        out_txt = "\n\n".join(out_lines)
    elif not std_out and std_err:
        out_txt = std_err
    elif std_out and not std_err:
        out_list = std_out.splitlines()
        out_txt = std_out
    else:
        out_txt = f"Output on stdout:\n{std_out}\n\nOutput on stderr:\n{std_err}"
    return CommandResult(
        cmd_enum=cmd_enum,
        full_cmd=f"{_get_full_cmd(cmd_enum, path_arg)}",
        out_txt=out_txt,
        path_arg=path_arg,
        pretty_cmd=f"{pretty_cmd(cmd_enum, path_arg)}",
        returncode=result_code,
        std_err=std_err,
        std_out=std_out,
        out_list=out_list,
        time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
    )


async def _exec_chezmoi(
    app: ChezmoiGui,
    cmd_enum: ReadCmd | WriteCmd,
    path_arg: Path | None = None,
) -> CommandResult:
    exec_result: ExecResult = await create_subprocess_exec_result(cmd_enum, path_arg)
    command_result = await _construct_command_result(exec_result, cmd_enum, path_arg)
    if app.screen.name == "splash_screen":
        await app.splash_screen.write_log_msg(cmd_result=command_result)
    if app.init_phase is False:
        setattr(app.app_log, ReactiveVar.cmd_result, command_result)
        setattr(app.cmd_log, ReactiveVar.cmd_result, command_result)
    app.post_message(CommandResultMsg(command_result))
    return command_result


async def run_chezmoi_cmd(
    app: ChezmoiGui,
    cmd_enum: ReadCmd | WriteCmd,
    path_arg: Path | None = None,
) -> CommandResult:
    if cmd_enum is ReadCmd.git_log and path_arg is not None:
        source_path = (await _exec_chezmoi(app, ReadCmd.source_path, path_arg)).std_out
        return await _exec_chezmoi(app, ReadCmd.git_log, Path(source_path))
    elif cmd_enum in ReadCmd:
        return await _exec_chezmoi(app, cmd_enum, path_arg)
    # Only works for apply and re-add, not for add, forget and destroy
    if path_arg is None and cmd_enum in (
        WriteCmd.add,
        WriteCmd.destroy,
        WriteCmd.forget,
    ):
        app.notify(f"Cannot run chezmoi on the destDir for {cmd_enum.name}.")
    return await _exec_chezmoi(app, cmd_enum, path_arg)


async def run_in_task_group(app: ChezmoiGui, commands: tuple[ReadCmd, ...]) -> None:
    async with asyncio.TaskGroup() as tg:
        for cmd_enum in commands:
            tg.create_task(run_chezmoi_cmd(app, cmd_enum))


@staticmethod
async def get_affected_paths(
    app: ChezmoiGui, write_cmd: WriteCmd, path: Path
) -> list[Path]:
    if write_cmd not in (
        WriteCmd.dry_add,
        WriteCmd.dry_apply,
        WriteCmd.dry_re_add,
        WriteCmd.dry_forget,
        WriteCmd.dry_destroy,
    ):
        app.notify(
            f"Wrong write command:{write_cmd.name} for get_affected_paths.",
            severity="error",
        )
        return []
    command_result = await _exec_chezmoi(app, write_cmd, path)
    # Matches standard git diff paths (capturing the target path in group 1)
    path_pattern = re.compile(r"^diff --git a/.* b/(.*)$")
    affected_paths: set[Path] = set()

    for line in command_result.out_list:
        match = path_pattern.match(line)
        if match:
            affected_paths.add(Path(match.group(1)))
    return path_funcs.sort_paths(affected_paths)


async def run_managed_commands(app: ChezmoiGui) -> None:

    async with asyncio.TaskGroup() as tg:
        man_dir_task = tg.create_task(run_chezmoi_cmd(app, ReadCmd.managed_dirs))
        man_file_task = tg.create_task(run_chezmoi_cmd(app, ReadCmd.managed_files))
        status_dirs_task = tg.create_task(run_chezmoi_cmd(app, ReadCmd.status_dirs))
        status_files_task = tg.create_task(run_chezmoi_cmd(app, ReadCmd.status_files))
        unman_dirs_task = tg.create_task(run_chezmoi_cmd(app, ReadCmd.unmanaged_dirs))
        unman_files_task = tg.create_task(run_chezmoi_cmd(app, ReadCmd.unmanaged_files))

    def parse_paths(cmd_result: CommandResult) -> set[Path]:
        return {Path(line) for line in cmd_result.out_list}

    def parse_status_output(cmd_result: CommandResult) -> dict[Path, Sc]:
        return {
            Path(line[3:]): Sc(line[:2])
            for line in cmd_result.out_list
            if Sc.R.value not in line[:2]  # TODO: implement R
        }

    man_dir_set: set[Path] = parse_paths(man_dir_task.result())
    man_file_set: set[Path] = parse_paths(man_file_task.result())
    status_dirs_pcr: dict[Path, Sc] = parse_status_output(status_dirs_task.result())
    status_files_pcr: dict[Path, Sc] = parse_status_output(status_files_task.result())
    un_man_dir_set: set[Path] = parse_paths(unman_dirs_task.result())
    un_man_file_set: set[Path] = parse_paths(unman_files_task.result())

    tree_paths = ChezmoiTreePaths(
        _dest_dir=store.cfg.dest_dir,
        _space_dir_set=man_dir_set - status_dirs_pcr.keys(),
        _space_file_set=man_file_set - status_files_pcr.keys(),
        _status_dirs_pcr=status_dirs_pcr,
        _status_files_pcr=status_files_pcr,
        _un_man_dir_set=un_man_dir_set,
        _un_man_file_set=un_man_file_set,
        _un_man_path_set=un_man_file_set | un_man_dir_set,
        man_dir_set=man_dir_set,
        man_file_set=man_file_set,
        man_path_set=man_dir_set | man_file_set,
        status_path_set=status_files_pcr.keys() | status_dirs_pcr.keys(),
        un_wanted_dir_set={p for p in un_man_dir_set if path_funcs.is_unwanted_dir(p)},
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
    file_path: Path,
) -> Text:
    cmd_result = await _exec_chezmoi(app, ReadCmd.cat, file_path)
    f_contents = cmd_result.std_out
    if not f_contents.strip():
        f_contents = "File is empty or contains only whitespace"
    text_contents = Text(f_contents)
    ReprHighlighter().highlight(text_contents)
    return text_contents
