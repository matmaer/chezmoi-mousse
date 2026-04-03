"""Preliminary script to start automating screenshot creation. Tested by running
`PYTHONPATH=src uv run --no-dev --with textual screenshots/take.py`
from the repo root.
"""

import os
import threading
import time
from pathlib import Path

from textual import messages

from chezmoi_mousse.gui.textual_app import ChezmoiGUI


def trigger_screenshot_and_exit(app: ChezmoiGUI, screenshot_dir: Path) -> None:
    def take_screenshot() -> None:
        app.action_screenshot(filename="startup_screen.svg", path=str(screenshot_dir))

    time.sleep(5)
    app.post_message(messages.InvokeLater(take_screenshot))

    time.sleep(1)
    app.post_message(messages.ExitApp())


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    screenshot_dir = repo_root / "screenshots"

    os.chdir(src_dir)

    app = ChezmoiGUI(
        chezmoi_bin="chezmoi", dev_mode=False, git_found=True, repo_found=True
    )
    trigger_thread = threading.Thread(
        target=trigger_screenshot_and_exit, args=(app, screenshot_dir), daemon=True
    )
    trigger_thread.start()
    app.run()


if __name__ == "__main__":
    main()
