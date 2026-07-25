from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, NamedTuple

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson, StrTup


__all__ = ["CommandResult", "ReadCmd", "WriteCmd"]


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

    @classmethod
    def splash_commands(cls) -> list[ReadCmd]:
        return [ReadCmd.doctor, ReadCmd.git_log, ReadCmd.cat_config, ReadCmd.ignored]

    @classmethod
    def json_output_commands(cls) -> list[ReadCmd]:
        return [ReadCmd.dump_config, ReadCmd.template_data]

    @classmethod
    def chezmoi_managed_commands(cls) -> list[ReadCmd]:
        return [
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
            ReadCmd.unmanaged_dirs,
            ReadCmd.unmanaged_files,
        ]


class WriteCmd(Enum):
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)

    @classmethod
    def subprocess_args(cls, cmd: WriteCmd, dry_run: bool) -> StrTup:
        if dry_run:
            return (CHEZMOI, GlobalArgs.dry_run) + cmd.value
        else:
            return (CHEZMOI,) + cmd.value

    @classmethod
    def full_cmd_str(cls, cmd: WriteCmd, dry_run: bool) -> str:
        return f"{CHEZMOI} " + " ".join(cls.subprocess_args(cmd, dry_run))

    @classmethod
    def pretty_cmd(cls, write_cmd: WriteCmd, dry_run: bool) -> str:
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
