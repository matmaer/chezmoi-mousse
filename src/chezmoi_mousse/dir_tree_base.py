from collections.abc import Iterator
from dataclasses import dataclass, field
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


@dataclass
class DirPathStatus:
    path: Path
    status: str


@dataclass
class FilePathStatus:
    path: Path
    status: str


@dataclass
class StatusPaths:
    managed_dirs: list[Path] = field(default_factory=list[Path])
    managed_files: list[Path] = field(default_factory=list[Path])
    status_dirs: list[DirPathStatus] = field(
        default_factory=list[DirPathStatus]
    )
    status_files: list[FilePathStatus] = field(
        default_factory=list[FilePathStatus]
    )


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

    # def refresh_status_paths_dataclass(
    #     self, splash_data: SplashReturnData | None = None
    # ) -> None:
    #     if splash_data is not None:
    #         managed_dir_paths = [
    #             Path(line)
    #             for line in SplashReturnData.managed_dirs.splitlines()
    #         ]
    #         managed_file_paths = [
    #             Path(line)
    #             for line in SplashReturnData.managed_files.splitlines()
    #         ]
    #         status_dir_paths = [
    #             PathStatus(Path(line[3:]), StatusCodes(line[:2]))
    #             for line in SplashReturnData.dir_status_lines.splitlines()
    #         ]
    #         status_file_paths = [
    #             PathStatus(Path(line[3:]), StatusCodes(line[:2]))
    #             for line in SplashReturnData.file_status_lines.splitlines()
    #         ]
    #         self.status_paths = StatusPaths(
    #             managed_dirs=managed_dir_paths,
    #             managed_files=managed_file_paths,
    #             status_dirs=status_dir_paths,
    #             status_files=status_file_paths,
    #         )
    #         return
    #     # get data from chezmoi managed stdout
    #     managed_dir_paths: list[Path] = [
    #         Path(line) for line in self.read(ReadCmd.managed_dirs).splitlines()
    #     ]
    #     managed_file_paths: list[Path] = [
    #         Path(line)
    #         for line in self.read(ReadCmd.managed_files).splitlines()
    #     ]
    #     # get data from chezmoi status stdout
    #     status_dir_paths: list[PathStatus] = [
    #         PathStatus(Path(line[3:]), StatusCodes(line[:2]))
    #         for line in self.read(ReadCmd.dir_status_lines).splitlines()
    #     ]
    #     status_file_paths: list[PathStatus] = [
    #         PathStatus(Path(line[3:]), StatusCodes(line[:2]))
    #         for line in self.read(ReadCmd.file_status_lines).splitlines()
    #     ]

    #     self.status_paths = StatusPaths(
    #         managed_dirs=managed_dir_paths,
    #         managed_files=managed_file_paths,
    #         status_dirs=status_dir_paths,
    #         status_files=status_file_paths,
    #     )
