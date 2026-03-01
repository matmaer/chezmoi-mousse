from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import NamedTuple

from textual.widgets import Collapsible, Label, Static

from ._str_enum_names import Tcss
from ._str_enums import Chars, LogString, SectionLabel

__all__ = ["ChezmoiCommand", "CommandResult", "ReadCmd", "ReadVerb", "WriteCmd"]


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
    dry_run = live_run + ["--dry-run"]


class VerbArgs(Enum):
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


class RunCmdResult(NamedTuple):
    completed_process: CompletedProcess[str]
    filtered_cmd: str


def _run_chezmoi_cmd(
    command: list[str],
    read_cmd: ReadCmd | None = None,
    write_cmd: WriteCmd | None = None,
) -> RunCmdResult:
    if read_cmd == ReadCmd.doctor:
        time_out = 4
    elif read_cmd is not None:
        time_out = 2
    elif write_cmd is not None:
        time_out = 7
    else:
        raise ValueError("Both read_cmd and write_cmd are None")

    filter_git_log_args = VerbArgs.git_log.value[3:]
    exclude = set(
        GlobalCmd.default_args.value
        + filter_git_log_args
        + [VerbArgs.format_json.value, VerbArgs.path_style_absolute.value]
    )
    return RunCmdResult(
        completed_process=run(
            command, capture_output=True, shell=False, text=True, timeout=time_out
        ),
        filtered_cmd=" ".join(
            [part for part in command if part and part not in exclude]
        ),
    )


@dataclass(slots=True)
class CommandResult:
    completed_process: CompletedProcess[str]
    filtered_cmd: str
    cmd_enum: ReadCmd | WriteCmd
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
    def pretty_cmd(self) -> str:
        success_color = "$text-success" if self.cmd_enum in WriteCmd else "$success"
        warning_color = "$text-warning" if self.cmd_enum in WriteCmd else "$warning"
        return (
            f"[{success_color}]{self.filtered_cmd}[/]"
            if self.completed_process.returncode == 0
            else f"[{warning_color}]{self.filtered_cmd}[/]"
        )

    @property
    def _log_entry(self) -> str:
        pretty_time = f"[$text-success][{datetime.now().strftime('%H:%M:%S')}][/]"
        return f"{pretty_time} {self.pretty_cmd}"

    @property
    def pretty_collapsible(self, collapsed: bool = True) -> Collapsible:
        dry_run_str = "(dry run)" if "--dry-run" in self.completed_process.args else ""
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
            title=self._log_entry,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=collapsed,
        )


class ChezmoiCommand:

    def __init__(self) -> None:
        self.changes_enabled: bool = False

    @property
    def _global_cmd(self) -> list[str]:
        if self.changes_enabled is True:
            return GlobalCmd.live_run.value
        else:
            return GlobalCmd.dry_run.value

    def review_cmd(self, *, global_args: list[str]) -> str:
        command = self._global_cmd + global_args
        filter_git_log_args = VerbArgs.git_log.value[3:]
        exclude = set(
            GlobalCmd.default_args.value
            + filter_git_log_args
            + [VerbArgs.format_json.value, VerbArgs.path_style_absolute.value]
        )
        cmd_str = " ".join([part for part in command if part and part not in exclude])
        return f"[$text-primary bold]{cmd_str}[/]"

    def read(self, read_cmd: ReadCmd, *, path_arg: Path | None = None) -> CommandResult:
        command = self._global_cmd + read_cmd.value
        if path_arg is not None:
            path_str = str(path_arg)
            if read_cmd == ReadCmd.git_log:
                source_path_str = _run_chezmoi_cmd(
                    self._global_cmd + ReadCmd.source_path.value + [path_str],
                    read_cmd=ReadCmd.source_path,
                ).completed_process.stdout.strip()
                path_str = source_path_str
            command += [path_str]
        result: RunCmdResult = _run_chezmoi_cmd(command, read_cmd=read_cmd)
        command_result = CommandResult(
            cmd_enum=read_cmd,
            completed_process=result.completed_process,
            filtered_cmd=result.filtered_cmd,
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
        command: list[str] = self._global_cmd + write_cmd.value

        if init_arg is not None:
            if write_cmd != WriteCmd.init_new:
                raise ValueError("init_arg only valid with WriteCmd.init_new")
            command.append(init_arg)
        elif path_arg is not None:
            command.append(str(path_arg))

        result: RunCmdResult = _run_chezmoi_cmd(command, write_cmd=write_cmd)
        command_result = CommandResult(
            cmd_enum=write_cmd,
            completed_process=result.completed_process,
            filtered_cmd=result.filtered_cmd,
            path_arg=path_arg,
        )
        return command_result
