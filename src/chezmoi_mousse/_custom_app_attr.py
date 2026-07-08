import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from ._app_ids import AppIds
from ._str_enums import NoRunInfo, ScreenName, TabLabel

__all__ = ["CustomAppAttribute"]


class CustomEnvVars(NamedTuple):
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


class CanvasIds(NamedTuple):
    # Screens
    splash = AppIds(ScreenName.splash)
    main = AppIds(ScreenName.main)
    # TabPanes
    add = AppIds(TabLabel.add)
    apply = AppIds(TabLabel.apply)
    config = AppIds(TabLabel.config)
    debug = AppIds(TabLabel.debug)
    logs = AppIds(TabLabel.logs)
    re_add = AppIds(TabLabel.re_add)


@dataclass(frozen=True)
class CustomAppAttribute:

    custom_env_vars = CustomEnvVars()
    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    stacktrace_path: Path = Path(__file__).parent / "stacktrace.log"
    canvas_ids: CanvasIds = CanvasIds()

    def __post_init__(self) -> None:
        if self.stacktrace_path.exists():
            self.stacktrace_path.unlink()

        message = self._will_not_run_message()
        if message is not None:
            sys.exit(message)

    def save_stacktrace(self):
        with Path.open(self.stacktrace_path, "a") as f:
            traceback.print_exc(file=f)

    def _will_not_run_message(self) -> str | None:
        error_info: list[str] = []
        start_info: list[str] = []
        if self.git_bin is None:
            error_info.append(NoRunInfo.GIT_NOT_FOUND)
        else:
            start_info.append(NoRunInfo.git_found(self.git_bin))

        if self.chezmoi_bin is None:
            error_info.append(NoRunInfo.CHEZMOI_NOT_FOUND)
        else:
            start_info.append(NoRunInfo.chezmoi_found(self.chezmoi_bin))

        if self.custom_env_vars.chezmoi_subshell:
            error_info.append(NoRunInfo.IN_SUBSHELL)
        else:
            start_info.append(NoRunInfo.NOT_IN_SUBSHELL)

        if self.custom_env_vars.pretend_fail:
            error_info.append(NoRunInfo.PRETEND_FAIL)
        else:
            start_info.append(NoRunInfo.NO_PRETEND_FAIL)
        lines: list[str] = []
        if error_info or self.custom_env_vars.pretend_fail:
            lines.append(NoRunInfo.NO_APP_RUN)
            lines.extend(error_info)
        if self.custom_env_vars.pretend_fail:
            lines.extend(start_info)
        if len(lines) > 0:
            return "\n".join(lines) + "\n" + NoRunInfo.FEEDBACK
        return None
