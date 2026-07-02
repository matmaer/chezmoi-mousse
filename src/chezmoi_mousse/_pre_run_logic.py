import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

__all__ = ["PreRunLogic"]


@dataclass(frozen=True)
class VarTruth:
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


class InfoStr(StrEnum):
    CANNOT_START_APP = "Cannot start app..."
    CHEZMOI_FOUND_ = "chezmoi command found: "
    CHEZMOI_NOT_FOUND = "chezmoi command not found, see https://chezmoi.io/install/"
    GIT_FOUND_ = "git command found: "
    GIT_NOT_FOUND = "git command not found, see https://git-scm.com/install/"
    IN_SUBSHELL = (
        "You are in a 'chezmoi subshell', exit the subshell to run the app.\n"
        "Please open a discussion:\n"
        "https://github.com/matmaer/chezmoi-mousse/discussions"
    )
    PRETEND_FAIL = "Not starting app because CHEZMOI_MOUSSE_PRETEND_FAIL is true."


@dataclass(frozen=True)
class PreRunLogic:

    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    stacktrace_path: Path = Path(__file__).parent / "stacktrace.log"
    debug_mode = VarTruth.debug_mode
    pilot_mode = VarTruth.pilot_mode

    def __post_init__(self) -> None:
        if self.stacktrace_path.exists():
            self.stacktrace_path.unlink()

        start_info: list[str] = []
        error_info: list[str] = []

        if self.git_bin is None:
            error_info.append(InfoStr.GIT_NOT_FOUND)
        else:
            start_info.append(InfoStr.GIT_FOUND_ + self.git_bin)

        if self.chezmoi_bin is None:
            error_info.append(InfoStr.CHEZMOI_NOT_FOUND)
        else:
            start_info.append(InfoStr.CHEZMOI_FOUND_ + self.chezmoi_bin)

        if VarTruth.chezmoi_subshell:
            error_info.append(InfoStr.IN_SUBSHELL)

        if VarTruth.pretend_fail:
            error_info.append(InfoStr.PRETEND_FAIL)

        if error_info and not VarTruth.pretend_fail:
            sys.exit("\n".join([InfoStr.CANNOT_START_APP] + error_info))
        elif VarTruth.pretend_fail:
            sys.exit("\n".join([InfoStr.CANNOT_START_APP] + error_info + start_info))

    def save_stacktrace(self):
        with Path.open(self.stacktrace_path, "a") as f:
            traceback.print_exc(file=f)
