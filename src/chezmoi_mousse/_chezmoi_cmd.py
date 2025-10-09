from enum import Enum

__all__ = ["ChangeCmd", "GlobalCmd", "ReadCmd", "ReadVerbs", "VerbArgs"]


class GlobalCmd(Enum):
    chezmoi = ["chezmoi"]
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
    ]
    live_run = chezmoi + default_args
    dry_run = live_run + ["--dry-run"]


class VerbArgs(Enum):
    # encrypt = "--encrypt"
    format_json = "--format=json"
    git_log = [
        "--",
        "--no-pager",
        "log",
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=50",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    ]
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"
    tree = "--tree"


class ReadVerbs(Enum):
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


class ReadCmd(Enum):
    cat = GlobalCmd.live_run.value + [ReadVerbs.cat.value]
    cat_config = GlobalCmd.live_run.value + [ReadVerbs.cat_config.value]
    diff = GlobalCmd.live_run.value + [ReadVerbs.diff.value]
    diff_reverse = GlobalCmd.live_run.value + [
        ReadVerbs.diff.value,
        VerbArgs.reverse.value,
    ]
    doctor = GlobalCmd.live_run.value + [ReadVerbs.doctor.value]
    dump_config = GlobalCmd.live_run.value + [
        VerbArgs.format_json.value,
        ReadVerbs.dump_config.value,
    ]
    git_log = (
        GlobalCmd.live_run.value
        + [ReadVerbs.git.value]
        + VerbArgs.git_log.value
    )
    ignored = GlobalCmd.live_run.value + [ReadVerbs.ignored.value]
    managed = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
    ]
    managed_dirs = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    source_path = GlobalCmd.live_run.value + [ReadVerbs.source_path.value]
    status_paths = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
    ]
    status_dirs = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    status_files = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    template_data = GlobalCmd.live_run.value + [ReadVerbs.data.value]


class ChangeCmd(Enum):
    add = ["add"]
    # add_encrypt = ["add", VerbArgs.encrypt.value]
    apply = ["apply"]
    # destroy = ["destroy"]
    # forget = ["forget"]
    init = ["init"]
    purge = ["purge"]
    re_add = ["re-add"]
