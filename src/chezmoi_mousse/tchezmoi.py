from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual import work

from chezmoi_mousse import _func, store
from chezmoi_mousse.asyncio_process_exec import (
    execute_chezmoi_command,
)
from chezmoi_mousse.gui.common.messages import CommandResultMsg
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
    from chezmoi_mousse.asyncio_process_exec import (
        ExecResult,
    )
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

type ScanDirResult = list[ScanDirItem] | PathKind

__all__ = ["ScanDirResult"]


def pretty_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    rel_path = _func.get_rel_path(path)
    if isinstance(cmd, ReadCmd):
        return (f"{cmd.pretty_cmd} {rel_path}").rstrip()
    else:
        base_cmd = _func.get_base_cmd(cmd)
        return (f"{base_cmd} {cmd.pretty_cmd} {_func.get_rel_path(path)}").rstrip()


async def construct_command_result(
    exec_result: ExecResult, cmd_enum: ReadCmd | WriteCmd, path_arg: Path | None
) -> CommandResult:
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
        full_cmd=f"{_func.get_full_cmd(cmd_enum, path_arg)}",
        out_txt=out_txt,
        path_arg=path_arg,
        pretty_cmd=f"{pretty_cmd(cmd_enum, path_arg)}",
        returncode=result_code,
        std_err=std_err,
        std_out=std_out,
        time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
    )


@work
async def exec_chezmoi_cmd(
    app: ChezmoiGui, cmd_enum: ReadCmd | WriteCmd, path_arg: Path | None = None
) -> CommandResult:
    if cmd_enum not in (ReadCmd.git_dir, WriteCmd.init, ReadCmd.dump_config) and (
        path_arg == store.cfg.dest_dir
    ):
        raise ValueError(f"Path {path_arg} cannot be the destination directory")
    exec_result: ExecResult = await execute_chezmoi_command(cmd_enum, path_arg)
    cmd_result = await construct_command_result(exec_result, cmd_enum, path_arg)
    if store.pre_mount is False:
        app.post_message(CommandResultMsg(cmd_result))
    return cmd_result


@work
async def run_chezmoi_git_log(
    app: ChezmoiGui, path_arg: Path | None = None
) -> CommandResult:

    if store.pre_mount is True:
        # don't access store.cfg.dest_dir
        cmd_result = await exec_chezmoi_cmd(app, ReadCmd.git_log, None).wait()
        return cmd_result
    elif path_arg is None or path_arg == store.cfg.dest_dir:
        cmd_result = await exec_chezmoi_cmd(app, ReadCmd.git_log, None).wait()
        return cmd_result
    else:
        source_path_result = await exec_chezmoi_cmd(app, ReadCmd.git_log).wait()
        source_path = Path(source_path_result.std_out)
        cmd_result = await exec_chezmoi_cmd(app, ReadCmd.git_log, source_path).wait()
        return cmd_result


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
    cmd_result = await exec_chezmoi_cmd(app, ReadCmd.cat, file_path).wait()
    f_contents = cmd_result.std_out
    if not f_contents.strip():
        f_contents = "File is empty or contains only whitespace"
    text_contents = Text(f_contents)
    ReprHighlighter().highlight(text_contents)
    return text_contents


async def run_chezmoi_diff(
    app: ChezmoiGui, diff_cmd: ReadCmd, path: Path
) -> CommandResult:
    return await exec_chezmoi_cmd(app, diff_cmd, path).wait()
