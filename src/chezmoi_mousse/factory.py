from pathlib import Path

from textual.widgets import RichLog

from chezmoi_mousse.chezmoi import chezmoi


def rich_file_content(path: Path) -> RichLog:
    file_content = chezmoi.file_content(path)
    rich_log = RichLog(
        highlight=True, auto_scroll=False, wrap=True, max_lines=500
    )
    rich_log.write(file_content)
    return rich_log
