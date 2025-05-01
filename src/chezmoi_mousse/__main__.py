from __future__ import annotations
from typing import ClassVar

from math import ceil

import rich.repr
from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style

from textual.scrollbar import ScrollBar, ScrollBarRender

from chezmoi_mousse.gui import ChezmoiTUI


class CustomScrollBarRender(ScrollBarRender):
    SLIM_HORIZONTAL_BAR: ClassVar[str] | None = "▂"

    @classmethod
    def render_bar(
        cls,
        size: int = 25,
        virtual_size: float = 50,
        window_size: float = 20,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        back_color: Color = Color.parse("#555555"),
        bar_color: Color = Color.parse("bright_magenta"),
    ) -> Segments:
        if vertical:
            bars = cls.VERTICAL_BARS
        else:
            bars = cls.HORIZONTAL_BARS

        back = back_color
        bar = bar_color

        len_bars = len(bars)

        width_thickness = thickness if vertical else 1

        _Segment = Segment
        _Style = Style
        blank = cls.BLANK_GLYPH * width_thickness

        foreground_meta = {"@mouse.down": "grab"}
        if window_size and size and virtual_size and size != virtual_size:
            bar_ratio = virtual_size / size
            thumb_size = max(1, window_size / bar_ratio)

            position_ratio = position / (virtual_size - window_size)
            position = (size - thumb_size) * position_ratio

            start = int(position * len_bars)
            end = start + ceil(thumb_size * len_bars)

            start_index, start_bar = divmod(max(0, start), len_bars)
            end_index, end_bar = divmod(max(0, end), len_bars)

            upper = {"@mouse.up": "scroll_up"}
            lower = {"@mouse.up": "scroll_down"}

            upper_back_segment = Segment(
                blank, _Style(bgcolor=back, meta=upper)
            )
            lower_back_segment = Segment(
                blank, _Style(bgcolor=back, meta=lower)
            )

            segments = [upper_back_segment] * int(size)
            segments[end_index:] = [lower_back_segment] * (size - end_index)
            if vertical or cls.SLIM_HORIZONTAL_BAR is None:
                segments[start_index:end_index] = [
                    _Segment(
                        blank,
                        _Style(color=bar, reverse=True, meta=foreground_meta),
                    )
                ] * (end_index - start_index)
                # Apply the smaller bar characters to head and tail of scrollbar for more "granularity"
                if start_index < len(segments):
                    bar_character = bars[len_bars - 1 - start_bar]
                    if bar_character != " ":
                        segments[start_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                )
                                if vertical
                                else _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                    reverse=True,
                                )
                            ),
                        )
                if end_index < len(segments):
                    bar_character = bars[len_bars - 1 - end_bar]
                    if bar_character != " ":
                        segments[end_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                    reverse=True,
                                )
                                if vertical
                                else _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                )
                            ),
                        )

            else:
                # Render a slim horizontal bar
                segments = [
                    _Segment(blank * width_thickness, _Style(bgcolor=back))
                ] * int(size)

                for i in range(start_index, end_index):
                    segments[i] = _Segment(
                        cls.SLIM_HORIZONTAL_BAR * width_thickness,
                        _Style(bgcolor=back, color=bar, meta=foreground_meta),
                    )
        else:
            style = _Style(bgcolor=back)
            segments = [_Segment(blank, style=style)] * int(size)
        if vertical:
            return Segments(segments, new_lines=True)
        else:
            return Segments(
                (segments + [_Segment.line()]) * thickness, new_lines=False
            )


@rich.repr.auto
class CustomScrollBar(ScrollBar):
    renderer: ClassVar[type[ScrollBarRender]] = CustomScrollBarRender


def main():
    app = ChezmoiTUI()
    ScrollBar.renderer = CustomScrollBarRender
    app.run(inline=False, headless=False, mouse=True)


if __name__ == "__main__":
    main()
