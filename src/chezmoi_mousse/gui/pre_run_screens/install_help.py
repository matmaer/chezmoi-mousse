# from importlib.resources import files
import json
import os
from enum import StrEnum
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Collapsible, Label, Link, Pretty, Tree

from chezmoi_mousse import AppType, Canvas, Chars, NavBtn, Tcss

type ParsedJson = dict[str, Any]

__all__ = ["InstallHelp"]


class Strings(StrEnum):
    chezmoi_docs_link_id = "chezmoi_docs_link"
    escape_exit_app = " escape key to exit app "
    install_chezmoi = " Install chezmoi "


class CommandsTree(Tree[ParsedJson]):
    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self) -> None:
        super().__init__(label=Strings.install_chezmoi.value)


class InstallHelp(Screen[None], AppType):

    BINDINGS = [Binding(key="escape", action="exit_application", show=False)]

    def __init__(self, chezmoi_found: bool) -> None:
        self.chezmoi_found = chezmoi_found
        super().__init__(
            id=Canvas.install_help_screen, classes=Tcss.screen_base.name
        )

    def compose(self) -> ComposeResult:
        if self.chezmoi_found is True:
            return
        with Vertical(classes=Tcss.install_help.name):
            yield Center(Label(("Chezmoi is not installed or not found.")))
            yield Collapsible(
                Pretty("PATH variable is empty or not set."),
                title="'chezmoi' command not found in any search path",
            )

            with Center():
                with Horizontal():
                    yield CommandsTree()
                    with VerticalGroup():
                        yield Link(
                            "chezmoi.io/install",
                            url="https://chezmoi.io/install",
                            id=Strings.chezmoi_docs_link_id,
                        )
                        yield Button(
                            NavBtn.exit_app.value, variant="primary", flat=True
                        )

    def on_mount(self) -> None:
        if self.chezmoi_found is False:
            self.border_subtitle = Strings.escape_exit_app.value
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
            assert child.data is not None
            install_commands: dict[str, str] = child.data
            for k, v in install_commands.items():
                child_label = Text(k, style="warning")
                new_child = child.add(label=child_label)
                cmd_label = Text(v)
                new_child.add_leaf(label=cmd_label)

    @on(Button.Pressed)
    def exit_application(self, event: Button.Pressed) -> None:
        self.app.exit()

    def action_exit_application(self) -> None:
        self.app.exit()
