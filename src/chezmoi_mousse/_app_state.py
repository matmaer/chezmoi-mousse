import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

from ._str_enums import NoRunInfo

__all__ = ["AppState"]


chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


@dataclass(frozen=True)
class AppState:

    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    stacktrace_path: Path = Path(__file__).parent / "stacktrace.log"
    debug_mode = debug_mode
    pilot_mode = pilot_mode

    def __post_init__(self) -> None:
        if self.stacktrace_path.exists():
            self.stacktrace_path.unlink()

        message = self._create_message()
        if message is not None:
            sys.exit(message)

    def save_stacktrace(self):
        with Path.open(self.stacktrace_path, "a") as f:
            traceback.print_exc(file=f)

    def _create_message(self) -> str | None:
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

        if chezmoi_subshell:
            error_info.append(NoRunInfo.IN_SUBSHELL)
        else:
            start_info.append(NoRunInfo.NOT_IN_SUBSHELL)

        if pretend_fail:
            error_info.append(NoRunInfo.PRETEND_FAIL)
        else:
            start_info.append(NoRunInfo.NO_PRETEND_FAIL)
        lines: list[str] = []
        if error_info or pretend_fail:
            lines.append(NoRunInfo.NO_APP_RUN)
            lines.extend(error_info)
        if pretend_fail:
            lines.extend(start_info)
        if len(lines) > 0:
            return "\n".join(lines) + "\n" + NoRunInfo.FEEDBACK
        return None
