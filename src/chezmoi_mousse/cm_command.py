from __future__ import annotations

from enum import Enum

from chezmoi_mousse.str_enums import ChezmoiGitArgs, VerbArgs

__all__ = ["ReadCmd", "WriteCmd"]


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
    template_data = ("data", VerbArgs.format_json)

    @classmethod
    def splash_only_commands(cls) -> tuple[ReadCmd, ...]:
        return (cls.cat_config, cls.doctor, cls.git_log, cls.git_remote, cls.ignored)

    @classmethod
    def json_parsable_commands(cls) -> tuple[ReadCmd, ...]:
        return (cls.dump_config, cls.template_data)

    @classmethod
    def managed_commands(cls) -> tuple[ReadCmd, ...]:
        return (cls.managed_dirs, cls.managed_files, cls.status_dirs, cls.status_files)

    @classmethod
    def grouped_commands_count(cls) -> int:
        return len(
            cls.json_parsable_commands()
            + cls.managed_commands()
            + cls.splash_only_commands()
        )


class WriteCmd(Enum):
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)
