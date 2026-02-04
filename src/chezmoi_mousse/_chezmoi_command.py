from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

from textual.containers import VerticalGroup
from textual.widgets import Collapsible, Label, Static

from ._app_state import AppState
from ._str_enum_names import Tcss
from ._str_enums import Chars, LogString, SectionLabel

if TYPE_CHECKING:
    from .gui.common.loggers import AppLog, CmdLog


__all__ = [
    "ChezmoiCommand",
    "CommandResult",
    "ReadCmd",
    "ReadVerb",
    "WriteCmd",
    "WriteVerb",
]


class LogUtils:

    @staticmethod
    def filtered_args_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        exclude = set(
            GlobalCmd.default_args.value
            + filter_git_log_args
            + [VerbArgs.format_json.value, VerbArgs.path_style_absolute.value]
        )
        return " ".join([part for part in command if part and part not in exclude])


class GlobalCmd(Enum):
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--keep-going=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
        "--verbose=true",
        "--use-builtin-git=true",
        "--use-builtin-diff=true",
    ]
    live_run = ["chezmoi"] + default_args
    _dry_run = live_run + ["--dry-run"]
    # version = live_run + ["--version"] TODO

    @classmethod
    def base_cmd(cls) -> list[str]:
        if AppState.changes_enabled() is True:
            return cls.live_run.value
        else:
            return cls._dry_run.value


class VerbArgs(Enum):
    # encrypt = "--encrypt"
    # debug = "--debug"
    format_json = "--format=json"
    git_log = [
        "--",
        "log",
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    ]
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    init_do_not_guess = "--guess-repo-url=false"
    init_guess_https = "--guess-repo-url=true"
    init_guess_ssh = ["--guess-repo-url=true", "--ssh"]
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
    # unmanaged = "unmanaged"
    verify = "verify"


class ReadCmd(Enum):
    cat = [ReadVerb.cat.value]
    cat_config = [ReadVerb.cat_config.value]
    diff = [ReadVerb.diff.value]
    diff_reverse = [ReadVerb.diff.value, VerbArgs.reverse.value]
    doctor = [ReadVerb.doctor.value]
    dump_config = [VerbArgs.format_json.value, ReadVerb.dump_config.value]
    git_log = [ReadVerb.git.value] + VerbArgs.git_log.value
    ignored = [ReadVerb.ignored.value]
    managed_dirs = [
        ReadVerb.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = [
        ReadVerb.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    source_path = [ReadVerb.source_path.value]
    status_dirs = [
        ReadVerb.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    status_files = [
        ReadVerb.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    template_data = [ReadVerb.data.value]
    # unmanaged = [ReadVerb.unmanaged.value, VerbArgs.path_style_absolute.value]
    verify = [ReadVerb.verify.value]


class WriteVerb(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    re_add = "re-add"


class WriteCmd(Enum):
    add = [WriteVerb.add.value]
    apply = [WriteVerb.apply.value]
    destroy = [WriteVerb.destroy.value]
    forget = [WriteVerb.forget.value]
    init_guess_https = [WriteVerb.init.value, VerbArgs.init_guess_https.value]
    init_guess_ssh = [WriteVerb.init.value] + VerbArgs.init_guess_ssh.value
    init_new = [WriteVerb.init.value]
    init_no_guess = [WriteVerb.init.value, VerbArgs.init_do_not_guess.value]
    re_add = [WriteVerb.re_add.value]

    @property
    def bold_review_cmd(self) -> str:
        return (
            f"[$text-success bold]"
            f"{LogUtils.filtered_args_str(GlobalCmd.base_cmd() + self.value)}[/]"
        )


def _run_chezmoi_cmd(
    command: list[str],
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
    completed_process: CompletedProcess[str]
    write_cmd: bool
    path_arg: Path | None = None
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
        if len(lines) == 0:
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
    def pretty_time(self) -> str:
        # formats time with square brackets and green text like "[13:33:04]"
        return f"[$text-success][{datetime.now().strftime('%H:%M:%S')}][/]"

    @property
    def dry_run_str(self) -> str:
        dry_run = "--dry-run" in self.completed_process.args and self.write_cmd is True
        return "(dry run)" if dry_run else ""

    @property
    def exit_code(self) -> int:
        return self.completed_process.returncode

    @property
    def filtered_cmd(self) -> str:
        return f"{LogUtils.filtered_args_str(self.completed_process.args)}"

    @property
    def full_command(self) -> str:
        return " ".join([a for a in self.completed_process.args])

    @property
    def log_entry(self) -> str:
        success_color = "$text-success" if self.write_cmd else "$success"
        warning_color = "$text-warning" if self.write_cmd else "$warning"
        colored_command = (
            f"[{success_color}]{self.filtered_cmd}[/]"
            if self.completed_process.returncode == 0
            else f"[{warning_color}]{self.filtered_cmd}[/]"
        )
        return f"{self.pretty_time} {colored_command}"

    @property
    def curated_std_out(self):
        return self.std_out or f"{LogString.no_stdout} {self.dry_run_str}"

    @property
    def curated_std_err(self):
        return self.std_err or f"{LogString.no_stderr} {self.dry_run_str}"

    @property
    def pretty_collapsible(self, collapsed: bool = True) -> VerticalGroup:
        collapsible_contents: list[Label | Static] = []
        collapsible_contents.extend(
            [
                Label(SectionLabel.stdout_output, classes=Tcss.sub_section_label),
                Static(f"{self.curated_std_out}", markup=False),
            ]
        )
        collapsible_contents.extend(
            [
                Label(SectionLabel.stderr_output, classes=Tcss.sub_section_label),
                Static(f"{self.curated_std_err}", markup=False),
            ]
        )
        return VerticalGroup(
            Collapsible(
                *collapsible_contents,
                title=self.log_entry,
                collapsed_symbol=Chars.right_triangle,
                expanded_symbol=Chars.down_triangle,
                collapsed=collapsed,
            )
        )


class ChezmoiCommand:

    def __init__(self) -> None:
        self.app = AppState.get_app()
        self.app_log: AppLog | None = None
        self.cmd_log: CmdLog | None = None

    #################################
    # Command execution and logging #
    #################################

    def _log_chezmoi_command(self, result: CommandResult):
        if self.app_log is None or self.cmd_log is None:
            return
        self.cmd_log.log_cmd_results(result)
        self.app_log.log_cmd_results(result)

    def read(self, read_cmd: ReadCmd, *, path_arg: Path | None = None) -> CommandResult:
        base_cmd = GlobalCmd.live_run.value  # read commands always run live
        command = base_cmd + read_cmd.value
        if path_arg is not None:
            path_str = str(path_arg)
            source_path_str = _run_chezmoi_cmd(
                base_cmd + ReadCmd.source_path.value + [path_str],
                read_cmd=ReadCmd.source_path,
            ).stdout.strip()
            if read_cmd == ReadCmd.cat and not path_arg.exists():
                path_str = source_path_str
            elif read_cmd == ReadCmd.git_log:
                path_str = source_path_str
            command += [path_str]
        result: CompletedProcess[str] = _run_chezmoi_cmd(command, read_cmd=read_cmd)
        command_result = CommandResult(
            completed_process=result, path_arg=path_arg, write_cmd=False
        )
        self._log_chezmoi_command(command_result)
        return command_result

    def perform(
        self,
        write_cmd: WriteCmd,
        *,
        path_arg: Path | None = None,
        init_arg: str | None = None,
    ) -> CommandResult:
        command: list[str] = GlobalCmd.base_cmd() + write_cmd.value

        if init_arg is not None:
            if write_cmd != WriteCmd.init_new:
                raise ValueError("init_arg only valid with WriteCmd.init_new")
            command.append(init_arg)
        elif path_arg is not None:
            command.append(str(path_arg))

        result: CompletedProcess[str] = _run_chezmoi_cmd(command, write_cmd=write_cmd)
        command_result = CommandResult(
            completed_process=result, path_arg=path_arg, write_cmd=True
        )
        self._log_chezmoi_command(command_result)
        if write_cmd in (
            WriteCmd.add,
            WriteCmd.apply,
            WriteCmd.destroy,
            WriteCmd.forget,
            WriteCmd.re_add,
        ):
            if self.app is None:
                raise ValueError("self.app is None")
            if self.app.paths is None:
                raise ValueError("self.app.paths is None")
        return command_result
