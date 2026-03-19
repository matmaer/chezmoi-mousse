from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run

from textual.widgets import Collapsible, Label, Static

from ._str_enum_names import Tcss
from ._str_enums import Chars, LogString, SectionLabel

__all__ = ["ChezmoiCommand", "CommandResult", "ReadCmd", "ReadVerb", "WriteCmd"]


class GlobalCmd(Enum):
    default_args = (
        "--color=off",
        "--force",
        "--interactive=false",
        "--keep-going=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
        "--use-builtin-git=true",
        "--use-builtin-diff=true",
    )
    live_run = ("chezmoi",) + default_args
    dry_run = live_run + ("--dry-run",)


class VerbArgs(Enum):
    format_json = "--format=json"
    git_log = (
        "--",
        "log",
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    )
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    init_do_not_guess = "--guess-repo-url=false"
    init_guess_https = "--guess-repo-url=true"
    init_guess_ssh = ("--guess-repo-url=true", "--ssh")
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadVerb(Enum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
    diff = "diff"
    doctor = "doctor"
    dump_config = "dump-config"
    git = "git"
    ignored = "ignored"
    managed = "managed"
    source_path = "source-path"
    status = "status"
    verify = "verify"


class ReadCmd(Enum):
    cat = (ReadVerb.cat.value,)
    cat_config = (ReadVerb.cat_config.value,)
    diff = (ReadVerb.diff.value,)
    diff_reverse = (ReadVerb.diff.value, VerbArgs.reverse.value)
    doctor = (ReadVerb.doctor.value,)
    dump_config = (VerbArgs.format_json.value, ReadVerb.dump_config.value)
    git_log = (ReadVerb.git.value,) + VerbArgs.git_log.value
    ignored = (ReadVerb.ignored.value,)
    managed = (ReadVerb.managed.value, VerbArgs.path_style_absolute.value)
    managed_dirs = (
        ReadVerb.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    )
    managed_files = (
        ReadVerb.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    )
    source_path = (ReadVerb.source_path.value,)
    status = (ReadVerb.status.value, VerbArgs.path_style_absolute.value)
    status_dirs = (
        ReadVerb.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    )
    status_files = (
        ReadVerb.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    )
    template_data = (ReadVerb.data.value,)
    verify = (ReadVerb.verify.value,)


class WriteVerb(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    re_add = "re-add"


class WriteCmd(Enum):
    add = (WriteVerb.add.value,)
    apply = (WriteVerb.apply.value,)
    destroy = (WriteVerb.destroy.value,)
    forget = (WriteVerb.forget.value,)
    init_guess_https = (WriteVerb.init.value, VerbArgs.init_guess_https.value)
    init_guess_ssh = (WriteVerb.init.value,) + VerbArgs.init_guess_ssh.value
    init_new = (WriteVerb.init.value,)
    init_no_guess = (WriteVerb.init.value, VerbArgs.init_do_not_guess.value)
    re_add = (WriteVerb.re_add.value,)


def _get_filtered_cmd(cmd_args: tuple[str, ...], review_color: bool) -> str:
    filter_git_log_args = VerbArgs.git_log.value[2:]
    exclude = set(
        GlobalCmd.default_args.value
        + filter_git_log_args
        + (VerbArgs.format_json.value, VerbArgs.path_style_absolute.value)
    )
    filtered_cmd = " ".join([part for part in cmd_args if part and part not in exclude])
    if review_color:
        return f"[$text-primary]{filtered_cmd}[/]"
    return filtered_cmd


def _run_chezmoi_cmd(
    command: tuple[str, ...],
    read_cmd: ReadCmd | None = None,
    write_cmd: WriteCmd | None = None,
) -> CompletedProcess[str]:
    if read_cmd == ReadCmd.doctor:
        time_out = 4
    elif read_cmd is not None:
        time_out = 2
    elif write_cmd is not None:
        time_out = 7
    else:
        raise ValueError("Both read_cmd and write_cmd are None")
    return run(command, capture_output=True, shell=False, text=True, timeout=time_out)


@dataclass(slots=True)
class CommandResult:
    cmd_without_path_arg: tuple[str, ...]
    completed_process: CompletedProcess[str]
    path_arg: Path | None
    std_out: str = ""
    std_err: str = ""

    def __post_init__(self) -> None:
        self.std_out = self._get_text(self.completed_process.stdout)
        self.std_err = self._get_text(self.completed_process.stderr)

    def _get_text(self, output: str) -> str:
        def _line_has_text(line: str) -> bool:
            return line != "" and not line.isspace()

        if not _line_has_text(output):
            return ""
        lines = output.splitlines()
        if len(lines) == 1:
            return "" if not _line_has_text(lines[0]) else lines[0]
        # Remove leading lines with no text
        start = 0
        while start < len(lines) and not _line_has_text(lines[start]):
            start += 1
        # Remove trailing lines with no text
        end = len(lines)
        while end > start and not _line_has_text(lines[end - 1]):
            end -= 1
        if start == end:
            return "" if not _line_has_text(lines[start]) else lines[start]
        return "\n".join(lines[start:end])

    @property
    def exit_code(self) -> int:
        return self.completed_process.returncode

    @property
    def full_cmd_filtered(self) -> str:
        return _get_filtered_cmd(self.completed_process.args, review_color=False)

    @property
    def exit_code_colored_cmd(self) -> str:
        cmd_color = "[$text-success]" if self.exit_code == 0 else "[$text-warning]"
        return f"{cmd_color}{self.full_cmd_filtered}[/]"

    @property
    def filtered_cmd_without_path_arg(self) -> str:
        return _get_filtered_cmd(self.cmd_without_path_arg, review_color=False)

    @property
    def is_dry_run(self) -> bool:
        return "--dry-run" in self.completed_process.args

    @property
    def pretty_collapsible(self, collapsed: bool = True) -> Collapsible:
        pretty_time = f"{datetime.now().strftime('%H:%M:%S')}"
        title = f"{pretty_time} {self.exit_code_colored_cmd}"
        dry_run_str = "(dry run)" if self.is_dry_run else ""
        curated_std_out = self.std_out or f"{LogString.no_stdout} {dry_run_str}"
        curated_std_err = self.std_err or f"{LogString.no_stderr} {dry_run_str}"
        collapsible_contents: list[Label | Static] = []
        collapsible_contents.extend(
            [
                Label(SectionLabel.stdout_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_out}", markup=False),
            ]
        )
        collapsible_contents.extend(
            [
                Label(SectionLabel.stderr_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_err}", markup=False),
            ]
        )
        return Collapsible(
            *collapsible_contents,
            title=title,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=collapsed,
        )


class ChezmoiCommand:

    def __init__(self) -> None:
        self.changes_enabled: bool = False

    @property
    def _global_cmd(self) -> tuple[str, ...]:
        if self.changes_enabled is True:
            return GlobalCmd.live_run.value
        else:
            return GlobalCmd.dry_run.value

    def review_cmd(self, global_args: tuple[str, ...]) -> str:
        command = self._global_cmd + global_args
        return _get_filtered_cmd(command, review_color=True)

    def read(self, read_cmd: ReadCmd, *, path_arg: Path | None = None) -> CommandResult:
        read_global_cmd = tuple(arg for arg in self._global_cmd if arg != "--dry-run")
        cmd_without_path_arg = read_global_cmd + read_cmd.value
        cmd_to_run = cmd_without_path_arg
        if path_arg is not None:
            path_str = str(path_arg)
            if read_cmd == ReadCmd.git_log:
                source_path_str = _run_chezmoi_cmd(
                    self._global_cmd + ReadCmd.source_path.value + (path_str,),
                    read_cmd=ReadCmd.source_path,
                ).stdout.strip()
                path_str = source_path_str
            cmd_to_run += (path_str,)
        result: CompletedProcess[str] = _run_chezmoi_cmd(cmd_to_run, read_cmd=read_cmd)
        command_result = CommandResult(
            completed_process=result,
            cmd_without_path_arg=cmd_without_path_arg,
            path_arg=path_arg,
        )
        return command_result

    def perform(
        self,
        write_cmd: WriteCmd,
        *,
        path_arg: Path | None = None,
        init_arg: str | None = None,
    ) -> CommandResult:
        command: tuple[str, ...] = self._global_cmd + write_cmd.value

        cmd_without_path_arg = command
        cmd_to_run = command
        if init_arg is not None:
            if write_cmd != WriteCmd.init_new:
                raise ValueError("init_arg only valid with WriteCmd.init_new")
            cmd_to_run += (init_arg,)
        elif path_arg is not None:
            cmd_to_run += (str(path_arg),)

        result: CompletedProcess[str] = _run_chezmoi_cmd(
            cmd_to_run, write_cmd=write_cmd
        )
        command_result = CommandResult(
            cmd_without_path_arg=cmd_without_path_arg,
            completed_process=result,
            path_arg=path_arg,
        )
        return command_result
