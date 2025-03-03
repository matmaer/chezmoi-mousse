"""
Main module for the Chezmoi Mousse TUI application.
Gets executed when starting the application with
`python -m chezmoi_mousse`.
"""

from chezmoi_mousse.tui import ChezmoiTUI

if __name__ == "__main__":
    app = ChezmoiTUI()
    setattr(app, "MEGATEST", "mega mega test line")
    app.run()
