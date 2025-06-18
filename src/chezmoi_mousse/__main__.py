"""Runs the textual App an monkey patches the scrollbar renderer."""

import os

from chezmoi_mousse.gui import ChezmoiGUI


def main():
    app = ChezmoiGUI()

    if os.environ.get("CHEZMOI_DEV") == "1":
        import traceback
        from pathlib import Path

        original_handle_exception = app._handle_exception
        src_dir = Path(__file__).parent.parent

        def patched_handle_exception(error):
            with open(src_dir / "error.log", "w") as f:
                traceback.print_exc(file=f)
            original_handle_exception(error)

        app._handle_exception = patched_handle_exception

    app.run(inline=False, headless=False, mouse=True)


if __name__ == "__main__":
    main()
