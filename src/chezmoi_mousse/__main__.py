"""Runs the textual App an monkey patches the scrollbar renderer."""

import traceback
from chezmoi_mousse.gui import ChezmoiGUI


def main():

    app = ChezmoiGUI()

    original_handle_exception = app._handle_exception

    # generate an unformatted stacktrace to copy/paste in AI dev tooling.
    def patched_handle_exception(error):
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        original_handle_exception(error)

    # MONKEY PATCH:
    app._handle_exception = patched_handle_exception

    app.run(inline=False, headless=False, mouse=True)


if __name__ == "__main__":
    main()
