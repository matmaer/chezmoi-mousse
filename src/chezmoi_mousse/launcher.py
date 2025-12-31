import os
import shutil
import traceback
from pathlib import Path

from ._app_state import AppState
from .gui.textual_app import ChezmoiGUI


def run_app():

    dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
    chezmoi_found = (
        shutil.which("chezmoi") is not None
        and os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") != "1"
    )
    pretend_init_needed = os.environ.get("PRETEND_CHEZMOI_INIT_NEEDED") == "1"

    if dev_mode is True or pretend_init_needed is True:
        # Set dev mode in _app_state so we always dry run chezmoi commands
        AppState.set_dev_mode(dev_mode)
        # Save stacktrace in case an exception occurs on App class init.
        src_dir = Path(__file__).parent.parent
        stack_trace_path = src_dir / "stack_trace.txt"

        def save_stacktrace():
            with open(stack_trace_path, "a") as f:
                traceback.print_exc(file=f)

        try:
            app = ChezmoiGUI(
                chezmoi_found=chezmoi_found,
                pretend_init_needed=pretend_init_needed,
            )

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
        app = ChezmoiGUI(
            chezmoi_found=chezmoi_found,
            pretend_init_needed=pretend_init_needed,
        )
        app.run()
