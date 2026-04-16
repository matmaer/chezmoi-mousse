import asyncio
import os
import shutil
import traceback
from pathlib import Path

from chezmoi_mousse._constants import CHEZMOI, GIT
from chezmoi_mousse._pilot_mode import test_app_with_pilot
from chezmoi_mousse.gui.textual_app import ChezmoiGUI

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
CHEZMOI_MOUSSE_PILOT_MODE = "CHEZMOI_MOUSSE_PILOT_MODE"
CHEZMOI_MOUSSE_DEV = "CHEZMOI_MOUSSE_DEV"
CHEZMOI_SUBSHELL = "CHEZMOI_SUBSHELL"
PRETEND_CHEZMOI_NOT_FOUND = "PRETEND_CHEZMOI_NOT_FOUND"


def run_app():
    if shutil.which(GIT) is None:
        print(GIT_NOT_FOUND)  # pytest-cov: ignore
        return
    if os.environ.get(CHEZMOI_SUBSHELL) == "1":
        print(IN_SUBSHELL)  # pytest-cov: ignore
        return

    chezmoi_bin = shutil.which(CHEZMOI)
    dev_mode = os.environ.get(CHEZMOI_MOUSSE_DEV) == "1"
    pretend_not_found = os.environ.get(PRETEND_CHEZMOI_NOT_FOUND) == "1"
    pilot_mode = os.environ.get(CHEZMOI_MOUSSE_PILOT_MODE) == "1"

    if dev_mode or pretend_not_found or pilot_mode:

        def save_stacktrace():
            with Path.open(Path(__file__).parent.parent / STACK_TRACE_FILE, "a") as f:
                traceback.print_exc(file=f)

        try:
            if pretend_not_found:
                chezmoi_bin = None
            app = ChezmoiGUI(chezmoi_bin=chezmoi_bin, dev_mode=True)

            # Patch app._handle_exception to save stacktrace during runtime
            original_handle_exception = app._handle_exception  # type: ignore[method-assign]

            def patched_handle_exception(error: Exception):
                save_stacktrace()
                original_handle_exception(error)

            # monkey patch
            app._handle_exception = patched_handle_exception  # type: ignore[method-assign]

            if pilot_mode:
                asyncio.run(test_app_with_pilot(app))
                return
            app.run()

        except Exception:
            # Save stacktrace in case an exception occurs on App class init.
            save_stacktrace()
            raise

    else:
        app = ChezmoiGUI(chezmoi_bin=chezmoi_bin)
        app.run()


if __name__ == "__main__":
    run_app()
