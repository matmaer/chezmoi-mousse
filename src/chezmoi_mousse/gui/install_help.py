import json
import os
from enum import StrEnum
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalGroup
from textual.screen import Screen
from textual.widgets import Footer, Pretty, Tree

from chezmoi_mousse import (
    AppType,
    BindingAction,
    BindingDescription,
    Chars,
    FlatBtn,
    HeaderTitle,
    LinkBtn,
    ScreenIds,
)
from chezmoi_mousse.shared import (
    CustomCollapsible,
    CustomHeader,
    FlatButton,
    FlatLink,
    MainSectionLabel,
)

type ParsedJson = dict[str, Any]

__all__ = ["InstallHelp"]


IDS = ScreenIds().install_help


class InstallHelpStrings(StrEnum):
    collapsible_title = "'chezmoi' command not found in any search path"
    install_chezmoi = " Install chezmoi "
    no_path_var = "PATH variable is empty or not set."
    top_label = "Chezmoi is not installed or not found."


class CommandsTree(Tree[ParsedJson]):
    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self) -> None:
        super().__init__(label=InstallHelpStrings.install_chezmoi)


class InstallHelp(Screen[None], AppType):

    def compose(self) -> ComposeResult:
        yield CustomHeader(ids=IDS)
        yield MainSectionLabel(InstallHelpStrings.top_label)
        yield CustomCollapsible(
            Pretty(InstallHelpStrings.no_path_var),
            title=InstallHelpStrings.collapsible_title,
        )
        with Horizontal():
            yield CommandsTree()
            yield VerticalGroup(
                FlatLink(ids=IDS, link_enum=LinkBtn.chezmoi_install),
                FlatButton(ids=IDS, button_enum=FlatBtn.exit_app),
            )
        yield Footer(id=IDS.footer)

    def on_mount(self) -> None:
        self.screen.title = HeaderTitle.header_install_help
        self.app.update_binding_description(
            binding_action=BindingAction.exit_screen,
            new_description=BindingDescription.exit_app,
        )
        self.update_path_widget()
        self.populate_tree()

    def update_path_widget(self) -> None:
        self.path_env = os.environ.get("PATH")
        entry_sep = ";" if os.name == "nt" else ":"
        if self.path_env is not None:
            self.path_env_list = self.path_env.split(entry_sep)
            pretty_widget = self.query_exactly_one(Pretty)
            pretty_widget.update(self.path_env_list)

    def populate_tree(self) -> None:
        help_tree: CommandsTree = self.query_exactly_one(CommandsTree)
        data_file = Path(__file__).parent / "chezmoi_install_commands.json"
        install_help: ParsedJson = json.loads(data_file.read_text())
        help_tree.show_root = False
        for k, v in install_help.items():
            help_tree.root.add(label=k, data=v)
        for child in help_tree.root.children:
            if child.data is None:
                self.app.notify(
                    f"InstallHelp: TreeNode data is None for {child.label}",
                    severity="error",
                )
                continue
            install_commands: dict[str, str] = child.data
            for key, value in install_commands.items():
                new_child = child.add(label=key)
                new_child.add_leaf(label=value)

    @on(FlatButton.Pressed)
    def exit_application(self) -> None:
        self.app.exit()
