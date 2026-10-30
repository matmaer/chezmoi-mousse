import ctypes
import os
import shutil
import sys

from chezmoi_mousse import store
from chezmoi_mousse.data_types import InitData
from chezmoi_mousse.debug.pilot_mode import run_with_pilot
from chezmoi_mousse.debug.utils import DebugUtils
from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["run_app"]


def run_app() -> None:
    which_chezmoi = _PreRunChecks.sys_exit_if_cannot_run()
    store.init_data = InitData(
        which_chezmoi=which_chezmoi,
        pilot_mode=(
            os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
            or "--pilot-mode" in sys.argv
        ),
        debug_utils=DebugUtils(),
    )
    try:
        app = ChezmoiGui()
        if store.init_data.pilot_mode:
            try:
                run_with_pilot(app)
            except:
                store.init_data.debug_utils.save_stacktrace()
        else:
            app.run()
    except:
        store.init_data.debug_utils.save_stacktrace()


class _PreRunChecks:
    @staticmethod
    def _is_elevated() -> bool:
        # Windows platform check
        if os.name == "nt":
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:  # noqa: BLE001
                return False

        # POSIX / Unix platform check
        is_root = getattr(os, "getuid", None) and (
            os.getuid() == 0 or os.geteuid() == 0
        )
        was_sudo = "SUDO_UID" in os.environ
        return bool(is_root or was_sudo)

    @staticmethod
    def sys_exit_if_cannot_run() -> str:

        cm_not_found = "'chezmoi' command not found, see https://chezmoi.io/install/"
        cm_found = "'chezmoi' command found."
        elevated = (
            "Refusing to run: Process is running with elevated (root/Administrator) "
            "privileges."
        )
        elevated_ok = (
            "Process is not running with elevated (root/Administrator) privileges."
        )
        feedback = (
            "Feedback welcome! https://github.com/matmaer/chezmoi-mousse/discussions"
        )
        git_not_found = "'git' command not found, see https://git-scm.com/install/"
        git_found = "'git' command found."
        in_subshell = (
            "You are in a 'chezmoi subshell', exit the subshell to run the app."
        )
        pretend_fail = "Pretending the app cannot run."

        success_info: list[str] = []
        error_info: list[str] = []

        which_chezmoi = shutil.which("chezmoi")
        which_git = shutil.which("git")
        if which_chezmoi is None:
            error_info.append(cm_not_found)
        else:
            success_info.append(cm_found)
        if which_git is None:
            error_info.append(git_not_found)
        else:
            success_info.append(git_found)
        if os.environ.get("CHEZMOI_SUBSHELL") == "1":
            error_info.append(in_subshell)
        if (
            os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"
            or "--pretend-fail" in sys.argv
        ):
            error_info.append(pretend_fail)
        if _PreRunChecks._is_elevated():
            error_info.append(elevated)
        else:
            success_info.append(elevated_ok)

        if which_chezmoi is None or which_git is None or error_info:
            all_info = success_info + error_info
            all_info.append(feedback)
            sys.exit("\n".join(all_info))

        return which_chezmoi
