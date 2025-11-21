import os
import shutil
import traceback
from pathlib import Path

from . import PreRunData
from .gui.textual_app import ChezmoiGUI


def run_app():

    dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
    chezmoi_found = (
        shutil.which("chezmoi") is not None
        and os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") != "1"
    )
    pretend_init_needed = os.environ.get("PRETEND_CHEZMOI_INIT_NEEDED") == "1"
    pre_run_data = PreRunData(
        chezmoi_found=chezmoi_found,
        dev_mode=dev_mode,
        force_init_screen=pretend_init_needed,
    )

    if dev_mode is True:
        src_dir = Path(__file__).parent.parent
        # Save stacktrace in case an exception occurs on App class init.
        try:
            app = ChezmoiGUI(pre_run_data=pre_run_data)
        except Exception:
            with open((Path.joinpath(src_dir, "stack_trace.txt")), "w") as f:
                traceback.print_exc(file=f)
            raise

        # Patch app._handle_exception method to save stacktrace in case of an
        # uncaught exception while the app is running.

        # keep the original method for pretty exception output in the console
        original_handle_exception = app._handle_exception  # type: ignore[method-assign]

        def patched_handle_exception(error: Exception):
            with open(src_dir / "stack_trace.txt", "w") as stack_trace_file:
                traceback.print_exc(file=stack_trace_file)
            original_handle_exception(error)

        # monkey patch
        app._handle_exception = patched_handle_exception  # type: ignore[method-assign]
        app.run()

    else:
        app = ChezmoiGUI(pre_run_data=pre_run_data)
        app.run()
