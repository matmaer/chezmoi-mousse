from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import ContentSwitcher, RichLog

from chezmoi_mousse import (
    AppType,
    AreaName,
    Canvas,
    Chars,
    LogUtils,
    ReadCmd,
    Tcss,
    TreeName,
    ViewName,
)

from .contents_view import ContentsView
from .expanded_tree import ExpandedTree
from .flat_tree import FlatTree
from .git_log import GitLogView
from .managed_tree import ManagedTree

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import ActiveCanvas, AppType, CanvasIds

__all__ = ["DiffView"]


class TreeSwitcher(ContentSwitcher, AppType):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.left),
            initial=self.ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        )

    def compose(self) -> ComposeResult:
        yield ManagedTree(ids=self.ids)
        yield FlatTree(ids=self.ids)
        yield ExpandedTree(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)


class ViewSwitcher(ContentSwitcher, AppType):
    def __init__(self, *, ids: "CanvasIds", diff_reverse: bool):
        self.ids = ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.right),
            initial=self.ids.view_id(view=ViewName.diff_view),
        )

    def compose(self) -> ComposeResult:
        yield DiffView(ids=self.ids, reverse=self.reverse)
        yield ContentsView(ids=self.ids)
        yield GitLogView(ids=self.ids)


class DiffView(RichLog, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds", reverse: bool) -> None:
        self.ids = ids
        self.reverse = reverse
        self.destDir: "Path | None" = None
        self.active_canvas: "ActiveCanvas | None" = None
        self.diff_read_cmd: ReadCmd = (
            ReadCmd.diff_reverse if self.reverse else ReadCmd.diff
        )
        self.pretty_diff_cmd = LogUtils.pretty_cmd_str(
            self.diff_read_cmd.value
        )
        self.active_canvas = Canvas.re_add if self.reverse else Canvas.apply
        super().__init__(
            id=self.ids.view_id(view=ViewName.diff_view),
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            classes=Tcss.border_title_top.name,
        )
        self.click_colored_file = Text(
            f"Click a colored file in the tree to see the output from {self.pretty_diff_cmd}.",
            style="dim",
        )

    def on_mount(self) -> None:
        self.write('This is the destination directory "chezmoi destDir"\n')
        self.write(self.click_colored_file)

    def _write_dir_info(self) -> None:
        self.write(f"Managed directory {self.path}\n")
        self.write(self.click_colored_file)

    def _write_unchanged_file_info(self) -> None:
        self.write(
            f'No diff available for "{self.path}", the file is unchanged.'
        )
        self.write(self.click_colored_file)

    def watch_path(self) -> None:
        self.border_title = f" {self.path} "
        if self.path == self.destDir:
            return
        self.clear()
        # write lines for an unchanged file or directory except when we are in
        # either the ApplyTab or ReAddTab
        if (
            self.active_canvas is not None
            and self.path in self.app.chezmoi.managed_dirs
        ):
            self._write_dir_info()
            return

        # create the diff view for a changed file
        diff_output: list[str] = []
        diff_output = self.app.chezmoi.read(
            self.diff_read_cmd, self.path
        ).splitlines()

        diff_lines: list[str] = [
            line
            for line in diff_output
            if line.strip() != ""
            and (
                line[0] in "+- "
                or line.startswith("old mode")
                or line.startswith("new mode")
            )
            and not line.startswith(("+++", "---"))
        ]
        if not diff_lines:
            self._write_unchanged_file_info()
            return

        for line in diff_lines.copy():
            line = line.rstrip("\n")  # each write call contains a newline
            if line.startswith("old mode") or line.startswith("new mode"):
                self.write("Permissions/mode will be changed:")
                self.write(f" {Chars.bullet} {line}")
                # remove the line from diff_lines
                diff_lines.remove(line)

        self.write(f'Output from "{self.pretty_diff_cmd} {self.path}":\n')
        for line in diff_lines:
            if line.startswith("-"):
                self.write(Text(line, self.app.theme_variables["text-error"]))
            elif line.startswith("+"):
                self.write(
                    Text(line, self.app.theme_variables["text-success"])
                )
