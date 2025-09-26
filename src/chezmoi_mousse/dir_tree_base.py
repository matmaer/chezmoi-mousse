from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import Literal

from rich.style import Style
from rich.text import Text
from textual.reactive import reactive
from textual.widgets import DirectoryTree, Tree
from textual.widgets.tree import TreeNode
from textual.worker import Worker

from chezmoi_mousse.constants import Chars, UnwantedDirs, UnwantedFiles
from chezmoi_mousse.id_typing import Any, AppType


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


class VirtualDirTreeBase(DirectoryTree):
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


class ApplyDirTree(VirtualDirTreeBase):
    pass


class ReAddDirTree(VirtualDirTreeBase):
    pass


class AddDirTree(VirtualDirTreeBase):
    pass


class FilteredDirTree(DirectoryTree, AppType):

    unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    # TODO: add filter switch to see already added files as otherwise when
    # wanting to add a file which was already added, you have to check if the
    # file exists outside of the chezmoi-mousse app
    unwanted: reactive[bool] = reactive(False, init=False)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = self.app.chezmoi.managed_status.managed_dirs
        managed_files = self.app.chezmoi.managed_status.managed_files

        # Switches: Red - Red (default)
        if not self.unmanaged_dirs and not self.unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent == self.app.destDir
                    )
                    and not self.is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not self.is_unwanted_path(p)
                    and p in managed_dirs
                )
            )
        # Switches: Green - Red
        elif self.unmanaged_dirs and not self.unwanted:
            return (
                p
                for p in paths
                if p not in managed_files and not self.is_unwanted_path(p)
            )
        # Switches: Red - Green
        elif not self.unmanaged_dirs and self.unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent == self.app.destDir
                    )
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            )
        # Switches: Green - Green, include all unmanaged paths
        elif self.unmanaged_dirs and self.unwanted:
            return (
                p
                for p in paths
                if p.is_dir() or (p.is_file() and p not in managed_files)
            )
        else:
            return paths

    def is_unwanted_path(self, path: Path) -> bool:
        if path.is_dir():
            try:
                UnwantedDirs(path.name)
                return True
            except ValueError:
                pass
        if path.is_file():
            extension = path.suffix
            try:
                UnwantedFiles(extension)
                return True
            except ValueError:
                pass
        return False
