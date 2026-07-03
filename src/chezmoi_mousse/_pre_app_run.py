import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

__all__ = ["PreAppRun"]


@dataclass(frozen=True)
class VarTruth:
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


class InfoStr(StrEnum):
    _CHEZMOI_FOUND = "'chezmoi' command found: "
    _GIT_FOUND = "'git' command found: "
    CHEZMOI_NOT_FOUND = "'chezmoi' command not found, see https://chezmoi.io/install/"
    FEEDBACK = "Feedback welcome! https://github.com/matmaer/chezmoi-mousse/discussions"
    GIT_NOT_FOUND = "'git' command not found, see https://git-scm.com/install/"
    IN_SUBSHELL = "You are in a 'chezmoi subshell', exit the subshell to run the app."
    NOT_IN_SUBSHELL = "Not in a 'chezmoi subshell' detected."
    NO_APP_RUN = "Please check:"
    PRETEND_FAIL = "Pretending the app cannot run."
    NO_PRETEND_FAIL = "Not pretending that the app cannot run."

    @classmethod
    def git_found(cls, which: str) -> str:
        return cls._GIT_FOUND + which

    @classmethod
    def chezmoi_found(cls, which: str) -> str:
        return cls._CHEZMOI_FOUND + which


@dataclass(frozen=True)
class PreAppRun:

    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    stacktrace_path: Path = Path(__file__).parent / "stacktrace.log"
    debug_mode = VarTruth.debug_mode
    pilot_mode = VarTruth.pilot_mode

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
            error_info.append(InfoStr.GIT_NOT_FOUND)
        else:
            start_info.append(InfoStr.git_found(self.git_bin))

        if self.chezmoi_bin is None:
            error_info.append(InfoStr.CHEZMOI_NOT_FOUND)
        else:
            start_info.append(InfoStr.chezmoi_found(self.chezmoi_bin))

        if VarTruth.chezmoi_subshell:
            error_info.append(InfoStr.IN_SUBSHELL)
        else:
            start_info.append(InfoStr.NOT_IN_SUBSHELL)

        if VarTruth.pretend_fail:
            error_info.append(InfoStr.PRETEND_FAIL)
        else:
            start_info.append(InfoStr.NO_PRETEND_FAIL)
        lines: list[str] = []
        if error_info or VarTruth.pretend_fail:
            lines.append(InfoStr.NO_APP_RUN)
            lines.extend(error_info)
        if VarTruth.pretend_fail:
            lines.extend(start_info)
        if len(lines) > 0:
            return "\n".join(lines) + "\n" + InfoStr.FEEDBACK
