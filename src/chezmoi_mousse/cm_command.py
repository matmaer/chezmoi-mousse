import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING, ClassVar, NamedTuple

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson


__all__ = ["ChezmoiCommand", "CommandResult", "ReadCmd", "WriteCmd"]


type StrTup = tuple[str, ...]  # args after the chezmoi command


CHEZMOI = "chezmoi"

UGLY_ARGS: set[str] = set()  # args to filter when showing pretty command


class GlobalArgs:
    global_defaults: ClassVar[StrTup] = (
        "--color=off",
        "--force",
        "--interactive=false",
        "--keep-going=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
        "--use-builtin-diff",
        "--use-builtin-git",
    )
    dry_run: ClassVar[str] = "--dry-run"
    UGLY_ARGS.update(global_defaults)


class ChezmoiGitArgs:
    # args for 'chezmoi git'
    _ot: ClassVar[str] = "--"
    _global_args: ClassVar[StrTup] = ("--no-pager", "--no-advice")
    _default_args: ClassVar[StrTup] = (_ot,) + _global_args
    _verbose: ClassVar[str] = "--verbose"
    # _dry_run: ClassVar[str] = "--dry-run" # noqa: ERA001
    _git_log_args: ClassVar[StrTup] = (
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    )
    git_log: ClassVar[StrTup] = _default_args + ("log",) + _git_log_args
    git_remote: ClassVar[StrTup] = _default_args + ("remote", _verbose)
    UGLY_ARGS.update(_global_args, _git_log_args, _verbose)


class VerbArgs(NamedTuple):
    format_json: str = "--format=json"
    include_dirs: str = "--include=dirs"
    include_files: str = "--include=files"
    path_style_absolute: str = "--path-style=absolute"
    reverse: str = "--reverse"
    UGLY_ARGS.update((format_json, path_style_absolute))


class ReadCmd(Enum):
    cat = ("cat",)
    cat_config = ("cat-config",)
    diff = ("diff",)
    diff_reverse = ("diff", VerbArgs.reverse)
    doctor = ("doctor",)
    dump_config = ("dump-config", VerbArgs.format_json)
    git_log = ("git",) + ChezmoiGitArgs.git_log
    git_remote = ("git",) + ChezmoiGitArgs.git_remote
    ignored = ("ignored",)
    managed_dirs = ("managed", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    managed_files = ("managed", VerbArgs.path_style_absolute, VerbArgs.include_files)
    source_path = ("source-path",)
    status_dirs = ("status", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    status_files = ("status", VerbArgs.path_style_absolute, VerbArgs.include_files)
    template_data = ("template-data", VerbArgs.format_json)
    unmanaged_dirs = ("unmanaged", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    unmanaged_files = (
        "unmanaged",
        VerbArgs.path_style_absolute,
        VerbArgs.include_files,
    )

    @property
    def subprocess_args(self) -> StrTup:
        return (CHEZMOI,) + self.value

    @property
    def full_cmd_str(self) -> str:
        return f"{CHEZMOI} " + " ".join(self.value)

    @property
    def pretty_cmd(self) -> str:
        return f"{CHEZMOI} " + " ".join(
            arg for arg in self.value if arg not in UGLY_ARGS
        )


class WriteCmd(Enum):
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)

    @classmethod
    def subprocess_args(cls, cmd: "WriteCmd", dry_run: bool) -> StrTup:
        if dry_run:
            return (CHEZMOI, GlobalArgs.dry_run) + cmd.value
        else:
            return (CHEZMOI,) + cmd.value

    @classmethod
    def full_cmd_str(cls, cmd: "WriteCmd", dry_run: bool) -> str:
        return f"{CHEZMOI} " + " ".join(cls.subprocess_args(cmd, dry_run))

    @classmethod
    def pretty_cmd(cls, write_cmd: "WriteCmd", dry_run: bool) -> str:
        return f"{CHEZMOI} " + " ".join(
            arg
            for arg in (
                (GlobalArgs.dry_run,) + write_cmd.value if dry_run else write_cmd.value
            )
            if arg not in UGLY_ARGS
        )


@dataclass(slots=True, frozen=True, kw_only=True)
class CommandResult:
    dry_run: bool
    err_lines: list[str]
    full_cmd: str
    out_lines: list[str]
    parsed_json: ParsedJson
    path_arg: Path | None
    returncode: int
    std_err: str
    std_out: str
    verb_cmd: ReadCmd | WriteCmd


class ChezmoiCommand:
    def __init__(self) -> None:
        self.dry_run: bool = True
        self.dest_dir: Path | None = None

    def review_cmd(
        self,
        cmd: ReadCmd | WriteCmd,
        *,
        dry_run: bool | None = None,
        rel_path: str = "",
    ) -> str:
        if isinstance(cmd, ReadCmd):
            return cmd.pretty_cmd + rel_path
        elif dry_run is not None:
            return cmd.pretty_cmd(write_cmd=cmd, dry_run=dry_run) + rel_path
        else:
            raise ValueError(f"Receiving write cmd {cmd} and dry run is {dry_run}")

    def _subprocess_run(self, run_args: StrTup, time_out: int) -> CompletedProcess[str]:
        return run(
            run_args, capture_output=True, shell=False, text=True, timeout=time_out
        )

    def run(
        self,
        cmd: ReadCmd | WriteCmd,
        *,
        dry_run: bool | None = None,
        path_arg: Path | None = None,
    ) -> CommandResult:
        time_out: int = 10 if isinstance(cmd, ReadCmd) else 20
        if isinstance(cmd, WriteCmd):
            if dry_run is None:
                raise ValueError(f"dry_run is None for a write cmd: {cmd}")
            else:
                full_cmd_str = cmd.full_cmd_str(cmd, dry_run)
                run_args = cmd.subprocess_args(cmd, dry_run) + (str(path_arg),)
        else:
            full_cmd_str = cmd.full_cmd_str
            run_args = cmd.subprocess_args + (str(path_arg),)

        completed_process: CompletedProcess[str] = self._subprocess_run(
            run_args, time_out
        )

        out_lines = [
            line for line in completed_process.stdout.splitlines() if line.strip()
        ]
        std_out = "\n".join(out_lines)

        err_lines = [
            line for line in completed_process.stderr.splitlines() if line.strip()
        ]
        std_err = "\n".join(err_lines)

        if isinstance(cmd, ReadCmd) and cmd in (
            ReadCmd.template_data,
            ReadCmd.dump_config,
        ):
            parsed_json: ParsedJson = json.loads(std_out)
        else:
            parsed_json = {}

        return CommandResult(
            dry_run=GlobalArgs.dry_run in run_args,
            err_lines=err_lines,
            full_cmd=full_cmd_str,
            out_lines=out_lines,
            parsed_json=parsed_json,
            path_arg=path_arg,
            returncode=completed_process.returncode,
            std_err=std_err,
            std_out=std_out,
            verb_cmd=cmd,
        )
