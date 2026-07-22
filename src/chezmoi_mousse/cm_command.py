import shutil
from dataclasses import dataclass, fields
from enum import Enum
from functools import cached_property
from pathlib import Path
from subprocess import CompletedProcess, run

__all__ = ["ChezmoiCommand", "CommandResult", "ReadCmd", "ReadVerb", "WriteCmd"]


class GlobalArgs(Enum):
    default = (
        "--color=off",
        "--force",
        "--interactive=false",
        "--keep-going=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
        "--use-builtin-diff=true",
        "--use-builtin-git=true",
    )
    dry_run = ("--dry-run",)


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
    git = "git"
    ignored = "ignored"
    managed = "managed"
    source_path = "source-path"
    status = "status"
    unmanaged = "unmanaged"


class ReadCmd(Enum):
    cat = (ReadVerb.cat.value,)
    cat_config = (ReadVerb.cat_config.value,)
    diff = (ReadVerb.diff.value,)
    diff_reverse = (ReadVerb.diff.value, VerbArgs.reverse.value)
    doctor = (ReadVerb.doctor.value,)
    dump_config = (ReadVerb.dump_config.value, VerbArgs.format_json.value)
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
    unmanaged_dirs = (
        ReadVerb.unmanaged.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    )
    unmanaged_files = (
        ReadVerb.unmanaged.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    )

    @classmethod
    def splash_commands(cls) -> list["ReadCmd"]:
        return [
            ReadCmd.doctor,
            ReadCmd.dump_config,
            ReadCmd.template_data,
            ReadCmd.git_log,
            ReadCmd.cat_config,
            ReadCmd.ignored,
        ]

    @classmethod
    def chezmoi_managed_commands(cls) -> list["ReadCmd"]:
        return [
            ReadCmd.unmanaged_dirs,
            ReadCmd.unmanaged_files,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ]

    @classmethod
    def parse_json_commands(cls) -> list["ReadCmd"]:
        return [ReadCmd.dump_config, ReadCmd.template_data]

    @property
    def pretty_verb(self) -> str:
        exclude = (VerbArgs.path_style_absolute.value, VerbArgs.format_json.value)
        if self == ReadCmd.git_log:
            exclude += VerbArgs.git_log.value[2:]
        return " ".join(t for t in self.value if t not in exclude)

    @property
    def pretty_cmd(self) -> str:
        return f"chezmoi {self.pretty_verb}"


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

    @property
    def pretty_verb(self) -> str:
        return self.value[0]


@dataclass(frozen=True, kw_only=True)
class CommandResult:
    dry_run: bool
    full_cmd: str
    path_arg: Path | None
    pretty_args: str
    returncode: int
    std_err: str
    std_out: str
    verb_cmd: ReadCmd | WriteCmd

    @cached_property
    def pretty_cmd(self) -> str:
        return f"chezmoi {self.pretty_args}"

    @cached_property
    def out_lines(self) -> list[str]:
        return self.std_out.splitlines()

    @cached_property
    def valid_paths_cmd(self) -> bool:  # Fixed return hint
        if self.verb_cmd not in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
            ReadCmd.unmanaged_dirs,
            ReadCmd.unmanaged_files,
        ):
            raise AttributeError(
                f"Path attributes are not relevant for command '{self.verb_cmd}'"
            )
        return True

    @cached_property
    def path_list(self) -> list[Path]:
        _ = self.valid_paths_cmd
        if self.verb_cmd in (ReadCmd.status_dirs, ReadCmd.status_files):
            return [Path(p[3:]) for p in self.out_lines]
        return [Path(p) for p in self.out_lines]

    @cached_property
    def path_set(self) -> set[Path]:
        return set(self.path_list)


@dataclass(slots=False, frozen=False, kw_only=True)  # be explicit
class CmdResults:
    # will raise attribute error if field is not set
    cat_config: CommandResult
    doctor: CommandResult
    dump_config: CommandResult
    git_log: CommandResult
    ignored: CommandResult
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult
    template_data: CommandResult
    unmanaged_dirs: CommandResult
    unmanaged_files: CommandResult

    # methods below raise AttributeError when field is not assigned as slots=False

    @classmethod
    def get_all_command_results(cls) -> list[CommandResult]:
        return [getattr(cls, field.name) for field in fields(cls)]

    @classmethod
    def get_command_results(cls, field_name: str) -> CommandResult:
        return getattr(cls, field_name)


class ChezmoiCommand:

    def __init__(self) -> None:
        self.dry_run: bool = True
        self.dest_dir: Path | None = None

    def review_cmd(
        self, cmd: ReadCmd | WriteCmd, *, path_arg: Path | None = None
    ) -> str:
        return "chezmoi " + " ".join(self._get_pretty_args(cmd, path_arg=path_arg))

    def _subprocess_run(
        self, chezmoi_args: tuple[str, ...], time_out: int
    ) -> CompletedProcess[str]:
        chezmoi_bin: str | None = shutil.which("chezmoi")
        if chezmoi_bin is None:
            raise RuntimeError("cannot find chezmoi command")
        return run(
            (chezmoi_bin,) + chezmoi_args,
            capture_output=True,
            shell=False,
            text=True,
            timeout=time_out,
        )

    def _get_pretty_args(
        self, cmd: ReadCmd | WriteCmd, path_arg: Path | None = None
    ) -> str:
        pretty_args = ""
        if self.dry_run and isinstance(cmd, WriteCmd):
            pretty_args += GlobalArgs.dry_run.value[0]
        pretty_args = cmd.pretty_verb
        if path_arg is not None:
            pretty_args += (
                str(path_arg)
                if self.dest_dir is None
                else f"{path_arg.relative_to(self.dest_dir)}"
            )
        return pretty_args

    def run(
        self, verb_cmd: ReadCmd | WriteCmd, *, path_arg: Path | None = None
    ) -> CommandResult:

        def trim_blank_lines(stdout: str) -> str:
            # normally not needed as chezmoi output is clean, however do not call
            # .strip() on status lines or we lose the leading spaces in status output
            lines = stdout.splitlines()
            start = 0
            end = len(lines)
            while start < end and not lines[start].strip():
                start += 1
            while end > start and not lines[end - 1].strip():
                end -= 1
            return "\n".join(lines[start:end])

        chezmoi_args: tuple[str, ...] = GlobalArgs.default.value
        if self.dry_run:
            chezmoi_args += GlobalArgs.dry_run.value
        if isinstance(verb_cmd, WriteCmd):
            time_out = 10
        else:
            time_out = 6 if verb_cmd == ReadCmd.doctor else 3
        if path_arg is not None:
            chezmoi_args += (str(path_arg),)
        completed_process: CompletedProcess[str] = self._subprocess_run(
            chezmoi_args, time_out=time_out
        )
        command_result = CommandResult(
            dry_run=GlobalArgs.dry_run.value[0] in completed_process.args,
            full_cmd=" ".join(list(completed_process.args)),
            path_arg=path_arg,
            pretty_args=" ".join(self._get_pretty_args(verb_cmd, path_arg)),
            returncode=completed_process.returncode,
            std_err=trim_blank_lines(completed_process.stderr),
            std_out=trim_blank_lines(completed_process.stdout),
            verb_cmd=verb_cmd,
        )
        setattr(CmdResults, verb_cmd.name, command_result)
        return command_result
