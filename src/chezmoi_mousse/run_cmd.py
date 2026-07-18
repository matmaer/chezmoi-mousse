import shutil
from dataclasses import dataclass
from enum import Enum
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
    unmanaged_files = (ReadVerb.unmanaged.value, VerbArgs.path_style_absolute.value)

    @property
    def filtered(self) -> str:
        exclude: list[str] = [
            VerbArgs.path_style_absolute.value,
            VerbArgs.format_json.value,
        ]
        if self == ReadCmd.git_log:
            exclude.extend(list(VerbArgs.git_log.value[2:]))
        return " ".join([part for part in self.value if part and part not in exclude])

    @classmethod
    def splash_commands(cls) -> list["ReadCmd"]:
        return [
            ReadCmd.cat_config,
            ReadCmd.doctor,
            ReadCmd.dump_config,
            ReadCmd.git_log,
            ReadCmd.ignored,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
            ReadCmd.template_data,
        ]

    @classmethod
    def managed_status_commands(cls) -> list["ReadCmd"]:
        return [
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ]


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
    def filtered(self) -> str:
        return self.value[0]


@dataclass(slots=True, frozen=True, kw_only=True)
class CommandResult:
    completed_process: CompletedProcess[str]
    path: Path | None
    pretty_cmd: str

    @property
    def was_dry_run(self) -> bool:
        return GlobalArgs.dry_run.value[0] in self.completed_process.args

    @property
    def full_cmd(self) -> str:
        return " ".join(self.completed_process.args)

    @property
    def returncode(self) -> int:
        return self.completed_process.returncode

    @property
    def std_out(self) -> str:
        return self.completed_process.stdout.strip()

    @property
    def std_err(self) -> str:
        return self.completed_process.stderr.strip()


class ChezmoiCommand:

    def __init__(self) -> None:
        self.changes_enabled: bool = False
        self.dest_dir: Path | None = None

    def _run_chezmoi_cmd(
        self,
        *,
        chezmoi_args: tuple[str, ...],
        time_out: int,
        filtered_args: str,
        path: Path | None = None,
    ) -> CommandResult:
        chezmoi_bin: str | None = shutil.which("chezmoi")
        if chezmoi_bin is None:
            raise RuntimeError("cannot find chezmoi command")
        subprocess_run_args = (chezmoi_bin,) + chezmoi_args
        result: CompletedProcess[str] = run(
            subprocess_run_args,
            capture_output=True,
            shell=False,
            text=True,
            timeout=time_out,
        )
        pretty_cmd_items = ["chezmoi"]
        pretty_cmd_items.append(filtered_args)
        return CommandResult(
            completed_process=result, path=path, pretty_cmd=" ".join(pretty_cmd_items)
        )

    def get_relative_path(self, path: Path) -> str:
        if self.dest_dir is None:
            # this happens when we have not yet parsed the config in the splash screen
            return str(path)
        else:
            return f"{path.relative_to(self.dest_dir)}"

    def run_command(
        self, cmd: ReadCmd | WriteCmd, *, path_arg: Path | None = None
    ) -> CommandResult:
        is_write_cmd = isinstance(cmd, WriteCmd)
        chezmoi_args: tuple[str, ...] = GlobalArgs.default.value
        filtered_args: list[str] = []
        time_out = 20
        if self.changes_enabled and is_write_cmd:
            chezmoi_args += GlobalArgs.dry_run.value
            filtered_args.append(f"{GlobalArgs.dry_run.value[0]}")
            time_out = 10
        elif not is_write_cmd:
            time_out = 6 if cmd == ReadCmd.doctor else 3
        filtered_args.append(cmd.filtered)
        if path_arg is not None:
            chezmoi_args += (str(path_arg),)
            filtered_args.append(self.get_relative_path(path_arg))
        return self._run_chezmoi_cmd(
            chezmoi_args=chezmoi_args,
            time_out=time_out,
            filtered_args=" ".join(filtered_args),
        )
