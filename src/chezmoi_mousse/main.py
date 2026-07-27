import asyncio
import os

from chezmoi_mousse.cm_attributes import CmAttributes
from chezmoi_mousse.debug.pilot_mode import test_app_with_pilot
from chezmoi_mousse.debug.utils import DebugUtils
from chezmoi_mousse.textual_app import ChezmoiGui


def check_if_we_can_run() -> str | None:
    import os
    import shutil
    import sys

    cm_not_found = "'chezmoi' command not found, see https://chezmoi.io/install/"
    feedback = "Feedback welcome! https://github.com/matmaer/chezmoi-mousse/discussions"
    git_not_found = "'git' command not found, see https://git-scm.com/install/"
    in_subshell = "You are in a 'chezmoi subshell', exit the subshell to run the app."
    pretend_fail = "Pretending the app cannot run."

    error_info: list[str] = []

    if shutil.which("chezmoi") is None:
        error_info.append(cm_not_found)
    if shutil.which("git") is None:
        error_info.append(git_not_found)
    if os.environ.get("CHEZMOI_SUBSHELL") == "1":
        error_info.append(in_subshell)
    if os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1":
        error_info.append(pretend_fail)
    if error_info or os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1":
        error_info.append(feedback)
        sys.exit("\n".join(list(error_info)))


def run_app():
    DebugUtils.clear_stacktrace()
    check_if_we_can_run()

    try:
        cm_attr_instance = CmAttributes()
        app = ChezmoiGui(cm_attr=cm_attr_instance)
        if os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1":
            asyncio.run(test_app_with_pilot(app))
        else:
            app.run()
    except Exception:
        DebugUtils.save_stacktrace()


if __name__ == "__main__":
    run_app()
