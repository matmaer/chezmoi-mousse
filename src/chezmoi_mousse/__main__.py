import rich.repr
from typing import ClassVar
from textual.scrollbar import ScrollBar, ScrollBarRender
from chezmoi_mousse.gui import ChezmoiTUI


class CustomScrollBarRender(ScrollBarRender):
    SLIM_HORIZONTAL_BAR: ClassVar[str] | None = "▂"


@rich.repr.auto
class CustomScrollBar(ScrollBar):
    renderer: ClassVar[type[ScrollBarRender]] = CustomScrollBarRender


def main():
    app = ChezmoiTUI()
    ScrollBar.renderer = CustomScrollBarRender
    app.run(inline=False, headless=False, mouse=True)


if __name__ == "__main__":
    main()
