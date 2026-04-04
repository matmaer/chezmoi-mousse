"""Preliminary script to start automating screenshot creation. Tested by running
`PYTHONPATH=src uv run --no-dev --with textual screenshots/take.py`
from the repo root.
"""

import os
import shutil
import threading
import time
from enum import StrEnum
from pathlib import Path

from textual import messages
from textual.widgets import TabbedContent

from chezmoi_mousse import TabLabel
from chezmoi_mousse.gui.textual_app import ChezmoiGUI

CHEZMOI_BIN = shutil.which("chezmoi")
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCREENSHOT_DIR = str(REPO_ROOT / "screenshots")


class FileNames(StrEnum):
    STARTUP = "startup.svg"
    DEBUG_SCREEN = "debug_screen.svg"


def startup_screenshot(app: ChezmoiGUI) -> None:
    time.sleep(5)
    app.action_screenshot(filename=FileNames.STARTUP, path=SCREENSHOT_DIR)
    app.exit()


def debug_screenshot(app: ChezmoiGUI) -> None:
    def activate_debug_tab() -> None:
        app.screen.query_exactly_one(TabbedContent).active = TabLabel.debug

    time.sleep(5)
    app.post_message(messages.InvokeLater(activate_debug_tab))
    time.sleep(1)
    app.action_screenshot(filename=FileNames.DEBUG_SCREEN, path=SCREENSHOT_DIR)
    app.exit()


def run_app(*, dev_mode: bool) -> None:
    app = ChezmoiGUI(
        chezmoi_bin=CHEZMOI_BIN, dev_mode=dev_mode, git_found=True, repo_found=True
    )
    if dev_mode is True:
        thread = threading.Thread(target=debug_screenshot, args=(app,), daemon=True)
    else:
        thread = threading.Thread(target=startup_screenshot, args=(app,), daemon=True)
    thread.start()
    app.run()


if __name__ == "__main__":
    os.chdir(SRC_DIR)

    run_app(dev_mode=False)
    run_app(dev_mode=True)
