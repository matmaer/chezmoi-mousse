import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run

from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

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
    unmanaged_files = (ReadVerb.unmanaged.value, VerbArgs.path_style_absolute.value)

    @classmethod
    def splash_commands(cls) -> list["ReadCmd"]:
        return [
            # order is related to thread worker logic in splash screen
            ReadCmd.doctor,
            ReadCmd.dump_config,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
            ReadCmd.template_data,
            ReadCmd.git_log,
            ReadCmd.cat_config,
            ReadCmd.ignored,
        ]

    # TODO added again to make the app start
    @classmethod
    def managed_status_commands(cls) -> list["ReadCmd"]:
        return [
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ]

    @property
    def pretty_args(self) -> tuple[str, ...]:
        exclude = (VerbArgs.path_style_absolute.value, VerbArgs.format_json.value)
        if self == ReadCmd.git_log:
            exclude += VerbArgs.git_log.value[2:]
        return tuple(t for t in self.value if t not in exclude)


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
    def pretty_args(self) -> tuple[str, ...]:
        return self.value


@dataclass(slots=True, frozen=True, kw_only=True)
class CommandResult:
    args: tuple[str, ...]
    dry_run: bool
    full_cmd: str
    path_arg: Path | None
    pretty_cmd: str
    returncode: int
    std_err: str
    std_out: str
    verb_cmd: ReadCmd | WriteCmd


@dataclass(slots=True, kw_only=True)
class CmdResults:
    # will raise attribute error if field is not set and trying to access CommandResult
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

    @classmethod
    def get_managed_dict(cls, path_kind: PathKind) -> dict[Path, StatusCode]:
        result: dict[Path, StatusCode] = {}
        source = cls.managed_dirs if path_kind == PathKind.dir else cls.managed_files
        for line in source.std_out.splitlines():
            path = Path(line)
            result[path] = StatusCode.Exists if path.exists() else StatusCode.NotExists
        return result

    @classmethod
    def status_dict(
        cls, tab_label: TabLabel, path_kind: PathKind
    ) -> dict[Path, StatusCode]:
        result: dict[Path, StatusCode] = {}
        source = cls.status_dirs if path_kind == PathKind.dir else cls.managed_files
        idx = 1 if tab_label == TabLabel.apply else 0
        for line in source.std_out.splitlines():
            if line[idx] == StatusCode.Space:
                continue
            path = Path(line[3:])
            result[path] = StatusCode(line[idx])
        return result


class ChezmoiCommand:

    def __init__(self) -> None:
        self.dry_run: bool = True
        self.dest_dir: Path | None = None

    def review_cmd(
        self, cmd: ReadCmd | WriteCmd, *, path_arg: Path | None = None
    ) -> str:
        return "chezmoi " + " ".join(
            list(self._get_pretty_args(cmd, path_arg=path_arg))
        )

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

    def _get_relative_path(self, path: Path) -> str:
        # this happens when we have not yet parsed the config in the splash screen
        return (
            str(path) if self.dest_dir is None else f"{path.relative_to(self.dest_dir)}"
        )

    def _get_pretty_args(
        self, cmd: ReadCmd | WriteCmd, path_arg: Path | None = None
    ) -> tuple[str, ...]:
        pretty_args: tuple[str, ...] = ()
        if self.dry_run:
            pretty_args += GlobalArgs.dry_run.value + cmd.pretty_args
        else:
            pretty_args = cmd.pretty_args
        if path_arg is not None:
            pretty_args += (self._get_relative_path(path_arg),)
        return pretty_args

    def run(
        self, verb_cmd: ReadCmd | WriteCmd, *, path_arg: Path | None = None
    ) -> CommandResult:
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
        return CommandResult(
            args=completed_process.args,
            dry_run=GlobalArgs.dry_run.value[0] in completed_process.args,
            full_cmd=" ".join(list(completed_process.args)),
            path_arg=path_arg,
            pretty_cmd="chezmoi"
            + " ".join(list(self._get_pretty_args(verb_cmd, path_arg))),
            returncode=completed_process.returncode,
            std_err=completed_process.stderr.strip(),
            std_out=completed_process.stdout.strip(),
            verb_cmd=verb_cmd,
        )
