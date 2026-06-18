import asyncio
import os
import shutil
import traceback
from pathlib import Path

from chezmoi_mousse._pilot_mode import test_app_with_pilot
from chezmoi_mousse.gui.textual_app import ChezmoiGUI

# startup env var names for dev
DEV_MODE = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
PILOT_MODE = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
PRETEND_NOT_FOUND = os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") == "1"
STACKTRACE_PATH = Path(__file__).parent / "stacktrace.log"
if STACKTRACE_PATH.exists():
    STACKTRACE_PATH.unlink()


def _save_stacktrace():
    with Path.open(STACKTRACE_PATH, "a") as f:
        traceback.print_exc(file=f)


def run_app():
    not_found_info: list[str] = []

    chezmoi_bin = shutil.which("chezmoi")

    if chezmoi_bin is None:
        not_found_info.append(
            "Command not found: 'chezmoi', see https://chezmoi.io/install/"
        )
    if shutil.which("git") is None:
        not_found_info.append(
            "Command not found: 'git', see https://git-scm.com/install/"
        )
    if not_found_info:
        print("\n".join(not_found_info))
        return

    if os.environ.get("CHEZMOI_SUBSHELL") == "1":
        print(
            (
                "You are in a 'chezmoi subshell', likely because you issued ",
                "'chezmoi cd' earlier on. Exit the chezmoi subshell before running ",
                "the app, e.g. press Ctrl+D, or exit and start a new terminal.",
            )
        )
        return

    chezmoi_bin = str(chezmoi_bin)

    if DEV_MODE or PILOT_MODE:

        class DevChezmoiGUI(ChezmoiGUI):

            CSS_PATH = str(Path("gui", "gui.tcss"))

            def _handle_exception(self, error: Exception) -> None:
                _save_stacktrace()
                super()._handle_exception(error)

        try:
            app = DevChezmoiGUI(chezmoi_bin=chezmoi_bin, dev_mode=True)
            app.run() if not PILOT_MODE else asyncio.run(test_app_with_pilot(app))

        except Exception:
            _save_stacktrace()
            raise

    else:
        app = ChezmoiGUI(chezmoi_bin=chezmoi_bin)
        app.run()


if __name__ == "__main__":
    run_app()
