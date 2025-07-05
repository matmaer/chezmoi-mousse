"""Textual overrides."""

from math import ceil

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from rich.text import Text
from textual.scrollbar import ScrollBarRender
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse.id_typing import NodeData


class CustomScrollBarRender(ScrollBarRender):
    """Used to monkey path the textual ScrollBar.renderer method in gui.py."""

    SLIM_HORIZONTAL_BAR = "▃"

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
            if vertical:
                segments[start_index:end_index] = [
                    _Segment(
                        blank,
                        _Style(color=bar, reverse=True, meta=foreground_meta),
                    )
                ] * (end_index - start_index)
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


class CustomRenderLabel(Tree[NodeData]):
    """Base class for TreeBase with custom render_label override."""

    # These attributes should be defined by subclasses
    _first_focus: bool
    _initial_render: bool
    _user_interacted: bool

    def style_label(self, node_data: NodeData) -> Text:
        """Style the label for a node.

        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "style_label must be implemented by subclasses"
        )

    def render_label(
        self,
        node: TreeNode[NodeData],
        base_style: Style,
        style: Style,  # needed for valid overriding
    ) -> Text:
        assert node.data is not None
        node_label = self.style_label(node.data)

        if node is self.cursor_node:
            current_style = node_label.style
            # Apply bold styling when tree is first focused
            if not self._first_focus and self._initial_render:
                if isinstance(current_style, str):
                    cursor_style = Style.parse(current_style) + Style(
                        bold=True
                    )
                else:
                    cursor_style = current_style + Style(bold=True)
                node_label = Text(node_label.plain, style=cursor_style)
            # Apply underline styling only after actual user interaction
            elif self._user_interacted:
                if isinstance(current_style, str):
                    cursor_style = Style.parse(current_style) + Style(
                        underline=True
                    )
                else:
                    cursor_style = current_style + Style(underline=True)
                node_label = Text(node_label.plain, style=cursor_style)

        if node.allow_expand:
            # import this as render_label is not in its natural habitat
            from textual.widgets._tree import TOGGLE_STYLE

            prefix = (
                (
                    self.ICON_NODE_EXPANDED
                    if node.is_expanded
                    else self.ICON_NODE
                ),
                base_style + TOGGLE_STYLE,
            )
        else:
            prefix = ("", base_style)

        text = Text.assemble(prefix, node_label)
        return text
