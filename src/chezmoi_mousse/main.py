import os
import shutil
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from ._constants import CHEZMOI, GIT
from ._run_cmd import GlobalArgs, ReadCmd, run_chezmoi_cmd
from .gui.textual_app import ChezmoiGUI

if TYPE_CHECKING:
    from subprocess import CompletedProcess


GIT_NOT_FOUND = (
    "'git' command not found. Install git as this app provides no safeguards when "
    "git is not available."
)
IN_SUBSHELL = (
    "You are in a 'chezmoi subshell', likely because you issued "
    "'chezmoi cd' earlier on. Exit the chezmoi subshell before running the "
    "app, e.g. press Ctrl+D, or exit and start a new terminal."
)
STACK_TRACE_FILE = "stack_trace.log"

# Env var related
CHEZMOI_MOUSSE_DEV = "CHEZMOI_MOUSSE_DEV"
CHEZMOI_SUBSHELL = "CHEZMOI_SUBSHELL"
PRETEND_CHEZMOI_NOT_FOUND = "PRETEND_CHEZMOI_NOT_FOUND"


def run_app():
    git_bin = shutil.which(GIT)
    if git_bin is None:
        print(GIT_NOT_FOUND)  # pytest-cov: ignore
        return
    if os.environ.get(CHEZMOI_SUBSHELL) == "1":
        print(IN_SUBSHELL)  # pytest-cov: ignore
        return

    chezmoi_bin = shutil.which(CHEZMOI)
    if chezmoi_bin is not None:
        completed: CompletedProcess[str] = run_chezmoi_cmd(
            command=(chezmoi_bin,) + GlobalArgs.live_run.value + ReadCmd.version.value,
            cmd_timeout=1,
        )
        if completed.returncode != 0:
            # If the command fails, we aussume chezmoi was not found.
            chezmoi_bin = None

    dev_mode = os.environ.get(CHEZMOI_MOUSSE_DEV) == "1"
    pretend_not_found = os.environ.get(PRETEND_CHEZMOI_NOT_FOUND) == "1"

    if dev_mode or pretend_not_found:
        if pretend_not_found:
            chezmoi_bin = None
        # Save stacktrace in case an exception occurs on App class init.
        src_dir = Path(__file__).parent.parent
        stack_trace_path = src_dir / STACK_TRACE_FILE

        def save_stacktrace():
            with Path.open(stack_trace_path, "a") as f:
                traceback.print_exc(file=f)

        try:
            app = ChezmoiGUI(chezmoi_bin=chezmoi_bin, dev_mode=True)

            # Patch app._handle_exception to save stacktrace during runtime
            original_handle_exception = app._handle_exception  # type: ignore[method-assign]

            def patched_handle_exception(error: Exception):
                save_stacktrace()
                original_handle_exception(error)

            # monkey patch
            app._handle_exception = patched_handle_exception  # type: ignore[method-assign]
            app.run()

        except Exception:
            save_stacktrace()
            raise

    else:
        app = ChezmoiGUI(chezmoi_bin=chezmoi_bin)
        app.run()


if __name__ == "__main__":
    run_app()
