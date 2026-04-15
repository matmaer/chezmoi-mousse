from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run

from textual.widgets import Collapsible, Label, Static

from ._constants import CHEZMOI, GIT
from ._str_enum_names import Tcss
from ._str_enums import Chars, LogString, SectionLabel

__all__ = ["ChezmoiCommand", "CommandResult", "ReadCmd", "ReadVerb", "WriteCmd"]


class GlobalArgs(Enum):
    _default_args = (
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
    dry_run_arg = "--dry-run"
    live_run = _default_args
    dry_run = _default_args + (dry_run_arg,)


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
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadVerb(Enum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
    diff = "diff"
    doctor = "doctor"
    dump_config = "dump-config"
    git = GIT
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
    re_add = "re-add"


class WriteCmd(Enum):
    add = (WriteVerb.add.value,)
    apply = (WriteVerb.apply.value,)
    destroy = (WriteVerb.destroy.value,)
    forget = (WriteVerb.forget.value,)
    re_add = (WriteVerb.re_add.value,)


def _filtered_verb_cmd(verb_cmd: tuple[str, ...]) -> str:
    filter_git_log_args = VerbArgs.git_log.value[2:]
    exclude = set(
        filter_git_log_args
        + (VerbArgs.format_json.value, VerbArgs.path_style_absolute.value)
    )
    filtered_cmd = " ".join([part for part in verb_cmd if part and part not in exclude])
    return filtered_cmd


def run_chezmoi_cmd(
    command: tuple[str, ...], cmd_timeout: int
) -> CompletedProcess[str]:
    return run(
        command, capture_output=True, shell=False, text=True, timeout=cmd_timeout
    )


@dataclass(slots=True)
class CommandResult:
    short_global_cmd: str
    short_verb_cmd: str
    completed_process: CompletedProcess[str]
    path_arg: Path | None

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
    def std_out(self) -> str:
        return self._get_text(self.completed_process.stdout)

    @property
    def _std_err(self) -> str:
        return self._get_text(self.completed_process.stderr)

    @property
    def short_cmd_no_path(self) -> str:
        return f"{self.short_global_cmd} {self.short_verb_cmd}"

    @property
    def _exit_code_colored_cmd(self) -> str:
        cmd_color = "[$text-success]" if self.exit_code == 0 else "[$text-warning]"
        cmd_text = f"{self.short_global_cmd} {self.short_verb_cmd}"
        cmd_return = f"[dim]returncode {self.exit_code}[/]"
        if self.path_arg is not None:
            cmd_text += f" {self.path_arg}"
        return f"{cmd_color} {cmd_text}[/] {cmd_return}"

    @property
    def _is_dry_run(self) -> bool:
        return GlobalArgs.dry_run_arg.value in self.completed_process.args

    @property
    def pretty_collapsible(self, collapsed: bool = True) -> Collapsible:
        pretty_time = f"{datetime.now().strftime('%H:%M:%S')}"
        title = f"{pretty_time} {self._exit_code_colored_cmd}"
        dry_run_str = "(dry run)" if self._is_dry_run else ""
        curated_std_out = self.std_out or f"{LogString.no_stdout} {dry_run_str}"
        curated_std_err = self._std_err or f"{LogString.no_stderr} {dry_run_str}"
        contents: list[Label | Static] = [
            Label(SectionLabel.full_cmd, classes=Tcss.sub_section_label)
        ]
        full_cmd = f"{' '.join(item for item in self.completed_process.args)}"
        contents.extend([Label(full_cmd, classes=Tcss.full_cmd)])
        contents.extend(
            [
                Label(SectionLabel.stdout_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_out}", markup=False),
            ]
        )
        contents.extend(
            [
                Label(SectionLabel.stderr_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_err}", markup=False),
            ]
        )
        return Collapsible(
            *contents,
            title=title,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=collapsed,
        )


class ChezmoiCommand:

    def __init__(self) -> None:
        self.changes_enabled: bool = False
        self.chezmoi_bin: str | None = None

    def _short_global_cmd(self, dry_run: bool) -> str:
        return f"{CHEZMOI} {GlobalArgs.dry_run_arg.value}" if dry_run else f"{CHEZMOI}"

    def review_cmd(
        self, verb_cmd: ReadCmd | WriteCmd, path_arg: Path | None = None
    ) -> str:
        review_cmd = f"{CHEZMOI}"
        if isinstance(verb_cmd, WriteCmd) and not self.changes_enabled:
            review_cmd += f" {GlobalArgs.dry_run_arg.value}"
        review_cmd += f" {_filtered_verb_cmd(verb_cmd.value)}"
        if path_arg is not None:
            review_cmd += f" {path_arg}"
        return f"[$text-primary]{review_cmd}[/]"

    def read(self, read_cmd: ReadCmd, *, path_arg: Path | None = None) -> CommandResult:
        if self.chezmoi_bin is None:
            raise ValueError("chezmoi_bin is not set")
        global_cmd = (self.chezmoi_bin,) + GlobalArgs.live_run.value
        verb_cmd = read_cmd.value
        cmd_to_run = global_cmd + verb_cmd
        time_out = 4 if read_cmd == ReadCmd.doctor else 2
        if path_arg is not None:
            path_str = str(path_arg)
            if read_cmd == ReadCmd.git_log:
                source_path_str = run_chezmoi_cmd(
                    global_cmd + ReadCmd.source_path.value + (path_str,),
                    cmd_timeout=time_out,
                ).stdout.strip()
                path_str = source_path_str
            cmd_to_run += (path_str,)
        result: CompletedProcess[str] = run_chezmoi_cmd(
            cmd_to_run, cmd_timeout=time_out
        )
        command_result = CommandResult(
            short_global_cmd=self._short_global_cmd(dry_run=False),
            completed_process=result,
            short_verb_cmd=_filtered_verb_cmd(verb_cmd),
            path_arg=path_arg,
        )
        return command_result

    def perform(
        self, write_cmd: WriteCmd, *, path_arg: Path | None = None
    ) -> CommandResult:
        if self.chezmoi_bin is None:
            raise ValueError("chezmoi_bin is not set")
        global_cmd = (
            (self.chezmoi_bin,) + GlobalArgs.live_run.value
            if self.changes_enabled
            else (self.chezmoi_bin,) + GlobalArgs.dry_run.value
        )
        command: tuple[str, ...] = global_cmd + write_cmd.value
        if path_arg is not None:
            command += (str(path_arg),)
        result: CompletedProcess[str] = run_chezmoi_cmd(command, cmd_timeout=7)
        command_result = CommandResult(
            short_global_cmd=self._short_global_cmd(dry_run=(not self.changes_enabled)),
            short_verb_cmd=_filtered_verb_cmd(write_cmd.value),
            completed_process=result,
            path_arg=path_arg,
        )
        return command_result
