# ruff: noqa: E501
# nuitka-project: --standalone
# nuitka-project: --onefile
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --output-filename=chezmoi-mousse
# nuitka-project: --include-data-file=src/chezmoi_mousse/gui.tcss=chezmoi_mousse/gui.tcss
# nuitka-project: --include-package-data=textual

from chezmoi_mousse.main import run_app

if __name__ == "__main__":
    run_app()
