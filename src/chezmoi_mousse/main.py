import asyncio
import os
import shutil
import sys
from enum import StrEnum

from chezmoi_mousse import save_stacktrace
from chezmoi_mousse.cm_attributes import CmAttributes
from chezmoi_mousse.debug.pilot_mode import test_app_with_pilot
from chezmoi_mousse.textual_app import ChezmoiGui


class NoRunInfo(StrEnum):
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


def _will_not_run_message() -> str | None:
    error_info: list[str] = []
    start_info: list[str] = []

    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"

    if git_bin is None:
        error_info.append(NoRunInfo.GIT_NOT_FOUND)
    else:
        start_info.append(NoRunInfo.git_found(git_bin))

    if chezmoi_bin is None:
        error_info.append(NoRunInfo.CHEZMOI_NOT_FOUND)
    else:
        start_info.append(NoRunInfo.chezmoi_found(chezmoi_bin))

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


def run_app():

    wil_not_run_msg = _will_not_run_message()

    if wil_not_run_msg is not None:
        sys.exit(wil_not_run_msg)

    cm_attr_instance = CmAttributes()

    try:
        app = ChezmoiGui(cm_attr=cm_attr_instance)
        if os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1":
            asyncio.run(test_app_with_pilot(app))
        else:
            app.run()
    except:
        save_stacktrace()
        raise


if __name__ == "__main__":
    run_app()
