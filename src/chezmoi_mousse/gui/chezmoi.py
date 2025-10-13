from pathlib import Path
from subprocess import CompletedProcess, run

from chezmoi_mousse import (
    ActiveCanvas,
    Canvas,
    ChangeCmd,
    GlobalCmd,
    PathDict,
    ReadCmd,
)
from chezmoi_mousse.gui.rich_logs import AppLog, DebugLog, OutputLog

__all__ = ["Chezmoi"]


class Utils:
    @staticmethod
    def strip_stdout(stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )


class Chezmoi:

    def __init__(self, *, changes_enabled: bool, dev_mode: bool) -> None:

        # set by main App class in its on_mount method
        self._changes_enabled = changes_enabled
        self.app_log: AppLog | None = None
        self.output_log: OutputLog | None = None
        if dev_mode is True:
            self.debug_log: DebugLog | None = None

        # cached command outputs
        self.managed_dirs_stdout: str = ""  # ReadCmd.managed_dirs
        self.managed_files_stdout: str = ""  # ReadCmd.managed_files
        self.status_dirs_stdout: str = ""  # ReadCmd.status_dirs
        self.status_files_stdout: str = ""  # ReadCmd.status_files
        self.status_paths_stdout: str = ""  # ReadCmd.status

    #################################
    # Command execution and logging #
    #################################

    def _log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = Utils.strip_stdout(result.stdout)
        if self.app_log is not None and self.output_log is not None:
            self.app_log.completed_process(result)
            self.output_log.completed_process(result)

    def read(self, read_cmd: ReadCmd, path: Path | None = None) -> str:
        command: list[str] = read_cmd.value
        if path is not None:
            command: list[str] = command + [str(path)]
        if read_cmd == ReadCmd.doctor:
            time_out = 3
        else:
            time_out = 1
        result: CompletedProcess[str] = run(
            command,
            capture_output=True,
            shell=False,
            text=True,
            timeout=time_out,
        )
        self._log_in_app_and_output_log(result)
        return Utils.strip_stdout(result.stdout)

    def perform(
        self, change_sub_cmd: ChangeCmd, change_arg: str | None = None
    ) -> None:
        if self._changes_enabled is True:
            base_cmd: list[str] = GlobalCmd.live_run.value
        else:
            base_cmd: list[str] = GlobalCmd.dry_run.value
        command: list[str] = base_cmd + change_sub_cmd.value

        if change_arg is not None:
            command: list[str] = command + [change_arg]

        self._log_in_app_and_output_log(
            run(
                command, capture_output=True, shell=False, text=True, timeout=5
            )
        )

    def refresh_managed_paths_data(self):
        # get data from chezmoi managed stdout
        self.managed_dirs_stdout = self.read(ReadCmd.managed_dirs)
        self.managed_files_stdout = self.read(ReadCmd.managed_files)
        # get data from chezmoi status stdout
        self.status_dirs_stdout = self.read(ReadCmd.status_dirs)
        self.status_files_stdout = self.read(ReadCmd.status_files)
        self.status_paths_stdout = self.read(ReadCmd.status_paths)

    ###################################################
    # Cached command outputs and processed properties

    # chezmoi status codes processed: A, D, M, or a space
    # "node status" codes:
    #   X (no status but managed)

    @property
    def managed_dirs(self) -> list[Path]:
        return [Path(line) for line in self.managed_dirs_stdout.splitlines()]

    @property
    def managed_files(self) -> list[Path]:
        return [Path(line) for line in self.managed_files_stdout.splitlines()]

    @property
    def _all_status_paths_dict(self) -> PathDict:
        return {
            Path(line[3:]): line[:2]
            for line in self.status_paths_stdout.splitlines()
        }

    @property
    def _apply_status_paths(self) -> PathDict:
        return {
            path: status_pair[1]
            for path, status_pair in self._all_status_paths_dict.items()
            if status_pair[1] in "ADM"  # Check second character only
        }

    @property
    def _re_add_status_paths(self) -> PathDict:
        # Consider paths which a status for apply operations but no status
        # themselves to have a status, will be handled in the Tree to only
        # show them if they exist on disk
        return {
            path: status_pair[0]
            for path, status_pair in self._all_status_paths_dict.items()
            if status_pair[0] == "M"
            or (status_pair[0] == " " and status_pair[1] in "ADM")
        }

    @property
    def _apply_status_files(self) -> PathDict:
        return {
            path: status_code
            for path, status_code in self._apply_status_paths.items()
            if path in self.managed_files
        }

    @property
    def _re_add_status_files(self) -> PathDict:
        # consider these files to always have status M, will be handled by the
        # Tree view widget to only show them for re-add operations if they
        # also exist on disk.
        return {
            key: "M"
            for key, _ in self._re_add_status_paths.items()
            if key in self.managed_files
        }

    def all_status_files(self, active_canvas: ActiveCanvas) -> PathDict:
        if active_canvas == Canvas.apply:
            return self._apply_status_files
        else:
            return self._re_add_status_files

    def status_files_in(
        self, active_canvas: ActiveCanvas, dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            return {
                path: status
                for path, status in self._apply_status_paths.items()
                if path.parent == dir_path and path in self.managed_files
            }
        else:
            return {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path.parent == dir_path
                and path in self.managed_files
                and path.exists()
            }

    def status_dirs_in(
        self, active_canvas: ActiveCanvas, dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            result = {
                path: status
                for path, status in self._apply_status_paths.items()
                if path.parent == dir_path and path in self.managed_dirs
            }
            # Add dirs that contain status files but don't have direct status
            for path in self.managed_dirs:
                if (
                    path.parent == dir_path
                    and path not in result
                    and self._has_apply_status_files_in(path)
                ):
                    result[path] = " "
            return dict(sorted(result.items()))
        else:
            result = {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path.parent == dir_path
                and path in self.managed_dirs
                and path.exists()
            }
            # Add dirs that contain status files but don't have direct status
            # Check exists() only once per directory
            for path in self.managed_dirs:
                if (
                    path.parent == dir_path
                    and path not in result
                    and path.exists()
                    and self._has_re_add_status_files_in(path)
                ):
                    result[path] = " "
            return dict(sorted(result.items()))

    def files_without_status_in(
        self, active_canvas: ActiveCanvas, dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            return {
                path: "X"
                for path in self.managed_files
                if path.parent == dir_path
                and path not in self._apply_status_paths
            }
        else:
            return {
                path: "X"
                for path in self.managed_files
                if path.parent == dir_path
                and path not in self._re_add_status_paths
                and path.exists()
            }

    def dirs_without_status_in(
        self, active_canvas: ActiveCanvas, dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            return {
                path: "X"
                for path in self.managed_dirs
                if path.parent == dir_path
                and path not in self._apply_status_paths
                and not self.has_status_paths_in(active_canvas, path)
            }
        else:
            return {
                path: "X"
                for path in self.managed_dirs
                if path.parent == dir_path
                and path not in self._re_add_status_paths
                and not self.has_status_paths_in(active_canvas, path)
            }

    def has_status_paths_in(
        self, active_canvas: ActiveCanvas, dir_path: Path
    ) -> bool:
        if active_canvas == Canvas.apply:
            return self._has_apply_status_files_in(dir_path)
        else:
            return self._has_re_add_status_files_in(dir_path)

    def _has_apply_status_files_in(self, dir_path: Path) -> bool:
        """Check if directory contains any status files (apply canvas)."""
        return any(
            path.is_relative_to(dir_path) and path in self.managed_files
            for path in self._apply_status_paths.keys()
        )

    def _has_re_add_status_files_in(self, dir_path: Path) -> bool:
        """Check if directory contains any status files that exist on disk
        (re_add canvas)."""
        return any(
            path.is_relative_to(dir_path)
            and path in self.managed_files
            and path.exists()
            for path in self._re_add_status_paths.keys()
        )
