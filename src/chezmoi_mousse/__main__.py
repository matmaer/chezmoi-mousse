from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.gui import ChezmoiGUI


def main():
    app = ChezmoiGUI()

    if chezmoi.app_cfg.dev_mode:
        """Patched app._handle_exception method which will save a stacktrace to
        error.log in the source directory in case an exception occurs."""
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
