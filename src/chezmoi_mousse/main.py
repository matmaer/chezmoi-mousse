import ctypes
import os
import shutil
import sys

from chezmoi_mousse import store
from chezmoi_mousse.debug.pilot_mode import run_with_pilot
from chezmoi_mousse.debug.utils import DebugUtils
from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["run_app"]


def is_elevated() -> bool:
    # Windows platform check
    if os.name == "nt":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:  # noqa: BLE001
            return False

    # POSIX / Unix platform check
    is_root = getattr(os, "getuid", None) and (os.getuid() == 0 or os.geteuid() == 0)
    was_sudo = "SUDO_UID" in os.environ
    return bool(is_root or was_sudo)


def _check_if_we_can_run() -> None:

    if is_elevated():
        sys.exit(
            "Refusing to run: Process is running with elevated (root/Administrator) "
            "privileges."
        )

    cm_not_found = "'chezmoi' command not found, see https://chezmoi.io/install/"
    feedback = "Feedback welcome! https://github.com/matmaer/chezmoi-mousse/discussions"
    git_not_found = "'git' command not found, see https://git-scm.com/install/"
    in_subshell = "You are in a 'chezmoi subshell', exit the subshell to run the app."
    pretend_fail = "Pretending the app cannot run."
    started_elevated = "App was started with root/elevated permissions, not supported."

    error_info: list[str] = []

    is_root = os.getuid() == 0 or os.geteuid() == 0
    was_sudo = "SUDO_UID" in os.environ

    if is_root or was_sudo:
        sys.exit(f"{started_elevated}")

    if shutil.which("chezmoi") is None:
        error_info.append(cm_not_found)
    if shutil.which("git") is None:
        error_info.append(git_not_found)
    if os.environ.get("CHEZMOI_SUBSHELL") == "1":
        error_info.append(in_subshell)
    if (
        os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"
        or "--pretend-fail" in sys.argv
    ):
        error_info.append(pretend_fail)
    if error_info or os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1":
        error_info.append(feedback)
        sys.exit("\n".join(list(error_info)))


def run_app() -> None:
    DebugUtils.clear_stacktrace()
    _check_if_we_can_run()

    app = ChezmoiGui()
    if store.PILOT_MODE:
        run_with_pilot(app)
    else:
        app.run()


if __name__ == "__main__":
    run_app()
