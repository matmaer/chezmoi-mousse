import os
import shutil
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from ._run_cmd import GlobalCmd, ReadCmd, run_chezmoi_cmd
from .gui.textual_app import ChezmoiGUI

if TYPE_CHECKING:
    from subprocess import CompletedProcess


def run_app():
    dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
    chezmoi_found = (
        shutil.which(GlobalCmd.chezmoi.value[0]) is not None
        and os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") != "1"
    )
    chezmoi_init_needed = False
    if chezmoi_found:
        completed: CompletedProcess[str] = run_chezmoi_cmd(
            command=GlobalCmd.live_run.value + ReadCmd.status.value,
            read_cmd=ReadCmd.status,
        )
        if (
            completed.returncode != 0
            or os.environ.get("PRETEND_CHEZMOI_INIT_NEEDED") == "1"
        ):
            chezmoi_init_needed = True

    if dev_mode is True:
        # Save stacktrace in case an exception occurs on App class init.
        src_dir = Path(__file__).parent.parent
        stack_trace_path = src_dir / "stack_trace.trace"

        def save_stacktrace():
            with Path.open(stack_trace_path, "a") as f:
                traceback.print_exc(file=f)

        try:
            app = ChezmoiGUI(
                chezmoi_found=chezmoi_found,
                dev_mode=dev_mode,
                chezmoi_init_needed=chezmoi_init_needed,
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
            dev_mode=dev_mode,
            chezmoi_init_needed=chezmoi_init_needed,
        )
        app.run()
