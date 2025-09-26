from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import Literal

from rich.style import Style
from rich.text import Text
from textual.widgets import DirectoryTree, Tree
from textual.widgets.tree import TreeNode
from textual.worker import Worker

from chezmoi_mousse.constants import Chars
from chezmoi_mousse.id_typing import Any


class DirTreeName(StrEnum):
    add_dir_tree = auto()
    apply_dir_tree = auto()
    re_ad_dir_tree = auto()


@dataclass
class NodeDataBase:
    found: bool
    path: Path


@dataclass
class DirNodeData(NodeDataBase):
    status: Literal["X", "A", "D"] = "X"
    has_leaves: bool = False
    has_sub_dirs: bool = False


@dataclass
class FileNodeData(NodeDataBase):
    status: Literal["X", "A", "D", "M"] = "X"


type VirtualNode = TreeNode[DirNodeData | FileNodeData]


class VirtualTree(Tree[VirtualNode]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._first_focus = True
        self._initial_render = True
        self._user_interacted = False

    def style_label(self, node_data: VirtualNode) -> Text:
        """Style the label for a node.

        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "style_label must be implemented by subclasses"
        )

    def render_label(
        self,
        node: TreeNode[VirtualNode],
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


class VirtualDirTree(DirectoryTree):
    ICON_NODE_EXPANDED = Chars.down_triangle
    ICON_NODE = Chars.right_triangle
    ICON_FILE = " "

    @staticmethod
    def _safe_is_dir(path: Path) -> bool:
        """Override DirectoryTree method as we are in a virtual tree of managed
        paths, so it is by definition safe."""
        return True

    # override all methods that access the filesystem and provide the
    # sourceDir path if not present on the filesystem WIP

    def _directory_content(
        self, location: Path, worker: Worker[None]
    ) -> Iterator[Path]:
        """Override base class method so it also returns non-existing paths
        which do exist in the chezmoi repository."""
        ...
