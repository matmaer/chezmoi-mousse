import os

from chezmoi_mousse.gui import ChezmoiGUI


def main():
    app = ChezmoiGUI()

    if os.environ.get("CHEZMOI_MOUSSE_DEV") == "1":
        import traceback
        from pathlib import Path

        original_handle_exception = app._handle_exception  # type: ignore[method-assign]
        src_dir = Path(__file__).parent.parent

        def patched_handle_exception(error: Exception):
            with open(src_dir / "error.log", "w") as f:
                traceback.print_exc(file=f)
            original_handle_exception(error)

        # monkey patch
        app._handle_exception = patched_handle_exception  # type: ignore[method-assign]

    app.run(inline=False, headless=False, mouse=True)


if __name__ == "__main__":
    main()
