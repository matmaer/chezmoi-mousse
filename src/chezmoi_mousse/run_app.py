import os
import traceback
from pathlib import Path

from chezmoi_mousse.chezmoi import Chezmoi
from chezmoi_mousse.gui import ChezmoiGUI

chezmoi = Chezmoi()


def run_app():

    if os.environ.get("CHEZMOI_MOUSSE_DEV") == "1":

        src_dir = Path(__file__).parent.parent

        # Save stacktrace in case an exception occurs on App class init.
        try:
            app = ChezmoiGUI(chezmoi_instance=chezmoi)
        except Exception:
            with open(src_dir / "stack_trace.txt", "w") as f:
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
        app = ChezmoiGUI(chezmoi_instance=chezmoi)
        app.run()
