from __future__ import annotations

from enum import Enum, StrEnum

__all__ = ["ReadCmd", "WriteCmd"]


def get_ugly_args() -> set[str]:
    ugly_args: set[str] = set()
    ugly_args.update(
        GlobalArgs.global_defaults.value,
        ChezmoiGitArgs.global_args.value,
        ChezmoiGitArgs.git_log_args.value,
        (
            ChezmoiGitArgs.verbose.value,
            VerbArgs.format_json.value,
            VerbArgs.path_style_absolute.value,
        ),
    )
    return ugly_args


class GlobalArgs(Enum):
    global_defaults = (
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
    dry_run = "--dry-run"


class VerbArgs(StrEnum):
    option_terminator = "--"  # option terminator
    format_json = "--format=json"
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ChezmoiGitArgs(Enum):
    # args for 'chezmoi git'
    global_args = ("--no-pager", "--no-advice")
    default_args = (VerbArgs.option_terminator,) + global_args
    verbose = "--verbose"
    # _dry_run = "--dry-run" # noqa: ERA001
    git_log_args = (
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    )
    git_log = default_args + ("log",) + git_log_args
    git_remote = default_args + ("remote", verbose)


class ReadCmd(Enum):
    cat = ("cat",)
    cat_config = ("cat-config",)
    diff = ("diff",)
    diff_reverse = ("diff", VerbArgs.reverse)
    doctor = ("doctor",)
    dump_config = ("dump-config", VerbArgs.format_json)
    git_log = ("git",) + ChezmoiGitArgs.git_log.value
    git_remote = ("git",) + ChezmoiGitArgs.git_remote.value
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


class WriteCmd(Enum):
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)
