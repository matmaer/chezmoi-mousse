from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse import store
from chezmoi_mousse.asyncio_process_exec import (
    execute_chezmoi_command,
)
from chezmoi_mousse.named_tuples import (
    CommandResult,
    ScanDirItem,
)
from chezmoi_mousse.str_enums import (
    PathKind,
    ReadCmd,
    WriteCmd,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.asyncio_process_exec import (
        ExecResult,
    )

type ScanDirResult = list[ScanDirItem] | PathKind

__all__ = ["ScanDirResult"]


def _get_rel_path(path: Path) -> str:
    return str(path.relative_to(store.cfg.dest_dir))


def _get_base_cmd(cmd: ReadCmd | WriteCmd) -> str:
    if isinstance(cmd, ReadCmd):
        return "chezmoi"
    return "chezmoi --dry-run" if store.live_run is False else "chezmoi"


def _full_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    path_str = str(path) if path is not None else ""
    return f"{_get_base_cmd(cmd)} {' '.join(cmd.value)} {path_str}"


def pretty_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    path_str = _get_rel_path(path) if path is not None else ""
    if isinstance(cmd, ReadCmd):
        return cmd.pretty_cmd if path is None else f"{cmd.pretty_cmd} {path_str}"
    base_cmd = _get_base_cmd(cmd)
    return f"{base_cmd} {' '.join(cmd.value)} {path_str}".rstrip()


async def exec_chezmoi_cmd(
    cmd_enum: ReadCmd | WriteCmd,
    path_arg: Path | None = None,
) -> CommandResult:
    if cmd_enum not in (ReadCmd.git_dir, WriteCmd.init, ReadCmd.dump_config) and (
        path_arg == store.cfg.dest_dir
    ):
        raise ValueError(f"Path {path_arg} cannot be the destination directory")
    exec_result: ExecResult = await execute_chezmoi_command(cmd_enum, path_arg)

    std_out = exec_result[0]
    std_err = exec_result[1]
    result_code = exec_result[2]
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
        out_txt = std_out
    else:
        out_txt = f"Output on stdout:\n{std_out}\n\nOutput on stderr:\n{std_err}"
    return CommandResult(
        cmd_enum=cmd_enum,
        full_cmd=f"{_full_cmd(cmd_enum, path_arg)}",
        out_txt=out_txt,
        path_arg=path_arg,
        pretty_cmd=f"{pretty_cmd(cmd_enum, path_arg)}",
        returncode=result_code,
        std_err=std_err,
        std_out=std_out,
        time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
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
    text_contents = Text(f_contents)
    ReprHighlighter().highlight(text_contents)
    return text_contents


async def get_highlighted_chezmoi_cat_output(
    file_path: Path,
) -> Text:
    cmd_result = await exec_chezmoi_cmd(ReadCmd.cat, file_path)
    f_contents = cmd_result.std_out
    if not f_contents.strip():
        f_contents = "File is empty or contains only whitespace"
    text_contents = Text(f_contents)
    ReprHighlighter().highlight(text_contents)
    return text_contents


async def run_chezmoi_diff(diff_cmd: ReadCmd, path: Path) -> CommandResult:
    return await exec_chezmoi_cmd(diff_cmd, path)
