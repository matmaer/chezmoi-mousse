from pathlib import Path

from rich.text import Text
from textual.widgets import RichLog

from chezmoi_mousse.chezmoi import chezmoi


def rich_file_content(path: Path) -> RichLog:
    file_content = chezmoi.file_content(path)
    rich_log = RichLog(
        highlight=True, auto_scroll=False, wrap=True, max_lines=500
    )
    rich_log.write(file_content)
    return rich_log


def colored_diff(diff_list: list[str]) -> RichLog:

    rich_log = RichLog(auto_scroll=False, wrap=True, max_lines=2000)
    added = str(rich_log.app.current_theme.success)
    removed = str(rich_log.app.current_theme.error)
    dimmed = f"{rich_log.app.current_theme.foreground} dim"

    for line in diff_list:
        if line.startswith("+ "):
            rich_log.write(Text(line, style=added))
        elif line.startswith("- "):
            rich_log.write(Text(line, style=removed))
        elif line.startswith("  "):
            rich_log.write(Text(line, style=dimmed))

    return rich_log
