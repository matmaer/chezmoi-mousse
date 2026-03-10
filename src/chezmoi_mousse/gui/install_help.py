import os
from enum import StrEnum

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalGroup
from textual.screen import Screen
from textual.widgets import Collapsible, Footer, Label, Pretty, Tree

from chezmoi_mousse import IDS, AppType, Chars, FlatBtnLabel, LinkBtn, ParsedJson, Tcss

from .common.actionables import FlatButton, FlatLink
from .common.screen_header import CustomHeader, HeaderTitle

__all__ = ["InstallHelpScreen"]


class InstallHelpStrings(StrEnum):
    collapsible_title = "'chezmoi' command not found in any search path"
    install_chezmoi = " Install chezmoi "
    no_path_var = "PATH variable is empty or not set."
    top_label = "Chezmoi is not installed or not found."


class CommandsTree(Tree[ParsedJson]):
    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    def __init__(self) -> None:
        super().__init__(label=InstallHelpStrings.install_chezmoi)


class InstallHelpScreen(Screen[None], AppType):

    install_help_data: "ParsedJson | None" = None

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield Label(InstallHelpStrings.top_label, classes=Tcss.main_section_label)
        yield Collapsible(
            Pretty(InstallHelpStrings.no_path_var),
            title=InstallHelpStrings.collapsible_title,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
        )
        with Horizontal():
            yield CommandsTree()
            yield VerticalGroup(
                FlatLink(LinkBtn.chezmoi_install),
                FlatButton(IDS.install_help, btn_enum=FlatBtnLabel.exit_app),
            )
        yield Footer()

    def on_mount(self) -> None:
        self.screen.title = HeaderTitle.install_help
        self._update_path_widget()
        self.populate_tree()

    def _update_path_widget(self) -> None:
        self.path_env = os.environ.get("PATH")
        entry_sep = ";" if os.name == "nt" else ":"
        if self.path_env is not None:
            self.path_env_list = self.path_env.split(entry_sep)
            pretty_widget = self.query_exactly_one(Pretty)
            pretty_widget.update(self.path_env_list)

    def populate_tree(self) -> None:
        if self.install_help_data is None:
            raise ValueError("No install help data found")
        help_tree: CommandsTree = self.query_exactly_one(CommandsTree)
        install_help: ParsedJson = self.install_help_data
        help_tree.show_root = False
        for k, v in install_help.items():
            help_tree.root.add(label=k, data=v)
        for child in help_tree.root.children:
            if child.data is None:
                self.app.notify(
                    f"InstallHelpScreen: TreeNode data is None for {child.label}",
                    severity="error",
                )
                continue
            for key, value in child.data.items():
                new_child = child.add(label=key)
                new_child.add_leaf(label=value)
