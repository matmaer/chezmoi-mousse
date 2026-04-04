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
    APPLY_TAB = "apply_tab.svg"
    DEBUG_TAB = "debug_tab.svg"
    LOGS_TAB = "logs_tab.svg"
    CONFIG_TAB = "config_tab.svg"
    INSTALL_SCREEN = "install_screen.svg"


def create_screenshot(app: ChezmoiGUI, filename: str, exit_app: bool = True) -> None:
    def exit_from_thread() -> None:
        app.call_from_thread(app.exit)

    svg = app.export_screenshot(simplify=True)
    # remove all blank lines from the svg string
    svg = "\n".join([line for line in svg.splitlines() if line.strip()])
    with Path(SCREENSHOT_DIR, filename).open("w", encoding="utf-8") as f:
        f.write(svg)

    if exit_app:
        exit_from_thread()


def apply_tab_screenshot(app: ChezmoiGUI) -> None:
    time.sleep(5)
    create_screenshot(app, FileNames.APPLY_TAB)


def config_tab_screenshot(app: ChezmoiGUI) -> None:
    def activate_config_tab() -> None:
        app.screen.query_exactly_one(TabbedContent).active = TabLabel.config

    time.sleep(5)
    app.post_message(messages.InvokeLater(activate_config_tab))
    time.sleep(1)
    create_screenshot(app, FileNames.CONFIG_TAB)


def debug_tab_screenshot(app: ChezmoiGUI) -> None:
    def activate_debug_tab() -> None:
        app.screen.query_exactly_one(TabbedContent).active = TabLabel.debug

    time.sleep(5)
    app.post_message(messages.InvokeLater(activate_debug_tab))
    time.sleep(1)
    create_screenshot(app, FileNames.DEBUG_TAB)


def logs_tab_screenshot(app: ChezmoiGUI) -> None:
    def activate_logs_tab() -> None:
        app.screen.query_exactly_one(TabbedContent).active = TabLabel.logs

    time.sleep(5)
    app.post_message(messages.InvokeLater(activate_logs_tab))
    time.sleep(1)
    create_screenshot(app, FileNames.LOGS_TAB)


def install_help_screenshot(app: ChezmoiGUI) -> None:
    time.sleep(5)
    create_screenshot(app, FileNames.INSTALL_SCREEN)


def run_app(
    apply_tab: bool = False,
    config_tab: bool = False,
    debug_tab: bool = False,
    install_screen: bool = False,
    logs_tab: bool = False,
) -> None:
    bin_path = None if install_screen else CHEZMOI_BIN
    dev_mode = bool(debug_tab)
    app = ChezmoiGUI(
        chezmoi_bin=bin_path, dev_mode=dev_mode, git_found=True, repo_found=True
    )
    if install_screen is True:
        thread = threading.Thread(
            target=install_help_screenshot, args=(app,), daemon=True
        )
    elif apply_tab is True:
        thread = threading.Thread(target=apply_tab_screenshot, args=(app,), daemon=True)
    elif logs_tab is True:
        thread = threading.Thread(target=logs_tab_screenshot, args=(app,), daemon=True)
    elif config_tab is True:
        thread = threading.Thread(
            target=config_tab_screenshot, args=(app,), daemon=True
        )
    elif debug_tab is True:
        thread = threading.Thread(target=debug_tab_screenshot, args=(app,), daemon=True)
    else:
        raise ValueError("No screenshot type specified.")
    thread.start()
    app.run()


if __name__ == "__main__":
    os.chdir(SRC_DIR)

    run_app(apply_tab=True)
    run_app(config_tab=True)
    run_app(debug_tab=True)
    run_app(install_screen=True)
    run_app(logs_tab=True)
