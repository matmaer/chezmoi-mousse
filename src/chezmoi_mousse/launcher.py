import os
import shutil
import traceback
from pathlib import Path

from textual.theme import Theme

from chezmoi_mousse.gui.app import ChezmoiGUI, PreRunData
from chezmoi_mousse.gui.chezmoi import Chezmoi


def run_app():

    chezmoi_mousse_dark = Theme(
        name="chezmoi-mousse-dark",
        dark=True,
        accent="#F187FB",
        background="#000000",
        error="#ba3c5b",  # textual dark
        foreground="#DCDCDC",
        primary="#0178D4",  # textual dark
        secondary="#004578",  # textual dark
        surface="#101010",  # see also textual/theme.py
        success="#4EBF71",  # textual dark
        warning="#ffa62b",  # textual dark
    )

    chezmoi_mousse_light = Theme(
        name="chezmoi-mousse-light",
        dark=False,
        background="#DEDEDE",
        foreground="#000000",
        primary="#0060AA",
        accent="#790084",
        surface="#B8B8B8",
    )

    custom_theme_vars = chezmoi_mousse_dark.to_color_system().generate()
    dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
    changes_enabled: bool = os.environ.get("MOUSSE_ENABLE_CHANGES") == "1"
    chezmoi_found = (
        shutil.which("chezmoi") is not None
        and os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") != "1"
    )

    chezmoi_instance = Chezmoi(
        changes_enabled=changes_enabled, dev_mode=dev_mode
    )

    pre_run_data = PreRunData(
        chezmoi_instance=chezmoi_instance,
        chezmoi_mousse_dark=chezmoi_mousse_dark,
        chezmoi_mousse_light=chezmoi_mousse_light,
        custom_theme_vars=custom_theme_vars,
        changes_enabled=changes_enabled,
        chezmoi_found=chezmoi_found,
        dev_mode=dev_mode,
    )

    if dev_mode is True:
        src_dir = Path(__file__).parent.parent
        # Save stacktrace in case an exception occurs on App class init.
        try:
            app = ChezmoiGUI(pre_run_data=pre_run_data)
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
        app = ChezmoiGUI(pre_run_data=pre_run_data)
        app.run()
