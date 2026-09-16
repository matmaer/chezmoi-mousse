from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.asyncio_process_exec import create_subprocess_exec_result
from chezmoi_mousse.data_classes import ChangedPaths, ChezmoiPaths
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.named_tuples import CommandResult, ScanDirItem
from chezmoi_mousse.str_enums import ReadCmd, WriteCmd

if TYPE_CHECKING:
    from chezmoi_mousse.asyncio_process_exec import (
        ExecResult,
    )
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

type ScanDirResult = list[ScanDirItem]

__all__ = ["ScanDirResult"]


def get_base_cmd(cmd: ReadCmd | WriteCmd) -> str:
    if isinstance(cmd, ReadCmd):
        return "chezmoi"
    return "chezmoi --dry-run" if store.live_run is False else "chezmoi"


def get_full_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    path_str = str(path) if path is not None else ""
    return f"{get_base_cmd(cmd)} {' '.join(cmd.value)} {path_str}".rstrip()


def pretty_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    rel_path = path_funcs.get_rel_path(path)
    if isinstance(cmd, ReadCmd):
        return (f"{cmd.pretty_cmd} {rel_path}").rstrip()
    else:
        base_cmd = get_base_cmd(cmd)
        return (f"{base_cmd} {cmd.pretty_cmd} {path_funcs.get_rel_path(path)}").rstrip()


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
        full_cmd=f"{get_full_cmd(cmd_enum, path_arg)}",
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
    if cmd_enum not in (ReadCmd.git_dir, WriteCmd.init, ReadCmd.dump_config) and (
        path_arg == store.cfg.dest_dir
    ):
        raise ValueError(f"Path {path_arg} cannot be the destination directory")
    exec_result: ExecResult = await create_subprocess_exec_result(cmd_enum, path_arg)
    cmd_result = await _construct_command_result(exec_result, cmd_enum, path_arg)
    is_queued = app.post_message(CommandResultMsg(cmd_result))
    assert is_queued, "Failed to queue CommandResultMsg"
    return cmd_result


async def run_chezmoi_command(
    app: ChezmoiGui,
    cmd_enum: ReadCmd | WriteCmd,
    path_arg: Path | None = None,
) -> CommandResult:
    if cmd_enum is ReadCmd.git_log and path_arg is not None:
        cr: CommandResult = await _run_chezmoi_git_log_on_path(app, path_arg)
    else:
        cr: CommandResult = await _exec_chezmoi(app, cmd_enum, path_arg)
    return cr


async def _run_chezmoi_git_log_on_path(
    app: ChezmoiGui, path_arg: Path
) -> CommandResult:
    source_path_result = await _exec_chezmoi(app, ReadCmd.source_path, path_arg)
    source_path = Path(source_path_result.std_out)
    cmd_result = await _exec_chezmoi(app, ReadCmd.git_log, source_path)
    return cmd_result


async def run_managed_commands(app: ChezmoiGui) -> ChezmoiPaths:
    _man_dir_list = (await _exec_chezmoi(app, ReadCmd.managed_dirs, None)).out_list
    _man_file_list = (await _exec_chezmoi(app, ReadCmd.managed_files, None)).out_list
    _status_dirs_list = (await _exec_chezmoi(app, ReadCmd.status_dirs, None)).out_list
    _status_files_list = (await _exec_chezmoi(app, ReadCmd.status_files, None)).out_list
    _unmanaged_list = (await _exec_chezmoi(app, ReadCmd.unmanaged, None)).out_list
    _unmanaged_paths = [Path(line) for line in _unmanaged_list]
    _unmanaged_dirs_list = [path for path in _unmanaged_paths if path.is_dir()]
    _unmanaged_files_list = [path for path in _unmanaged_paths if path.is_file()]

    def get_managed_dict(managed: list[str], status: list[str]) -> dict[Path, str]:
        status_dict = {Path(line[3:]): line[:2] for line in status}
        paths = [Path(line) for line in managed]
        paths_dict: dict[Path, str] = {}
        for path in paths:
            paths_dict[path] = status_dict.get(path, "  ")
        return paths_dict

    _managed_dirs = get_managed_dict(_man_dir_list, _status_dirs_list)
    _managed_files = get_managed_dict(_man_file_list, _status_files_list)

    def get_unmanaged_dict(
        unmanaged: list[Path],
    ) -> dict[Path, str]:
        return dict.fromkeys(unmanaged, "XX")

    _unmanaged_dirs = get_unmanaged_dict(_unmanaged_dirs_list)
    _unmanaged_files = get_unmanaged_dict(_unmanaged_files_list)

    _chezmoi_dirs = path_funcs.sort_path_dict(_unmanaged_dirs | _managed_dirs)
    _chezmoi_files = path_funcs.sort_path_dict(_unmanaged_files | _managed_files)
    _removed_dirs = [p for p in store.cm_paths.managed_dirs if p not in _managed_dirs]
    _removed_files = [
        p for p in store.cm_paths.managed_files if p not in _managed_files
    ]

    _added_dirs = {
        p: s for p, s in _managed_dirs.items() if p not in store.cm_paths.managed_dirs
    }
    _added_files = {
        p: s for p, s in _managed_files.items() if p not in store.cm_paths.managed_files
    }

    def get_changes_dict(
        dict1: dict[Path, str], dict2: dict[Path, str]
    ) -> dict[Path, str]:
        return {
            key: dict2[key]
            for key in dict1.keys() & dict2.keys()
            if dict1[key] != dict2[key]
        }

    _changed_dirs = get_changes_dict(store.cm_paths.managed_dirs, _managed_dirs)
    _changed_files = get_changes_dict(store.cm_paths.managed_files, _managed_files)

    _changes = ChangedPaths(
        added_dirs=_added_dirs,
        added_files=_added_files,
        removed_dirs=_removed_dirs,
        removed_files=_removed_files,
        changed_dirs=_changed_dirs,
        changed_files=_changed_files,
        top_removed_dirs=path_funcs.get_sorted_top_parents(_removed_dirs),
    )
    new_cm_paths = ChezmoiPaths(
        managed_dirs=_managed_dirs,
        managed_files=_managed_files,
        changes=_changes,
        chezmoi_dirs=_chezmoi_dirs,
        chezmoi_files=_chezmoi_files,
    )
    return new_cm_paths


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
