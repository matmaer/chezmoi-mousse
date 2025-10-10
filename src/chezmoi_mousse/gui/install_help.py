import json
import os
from enum import StrEnum
from importlib.resources import files
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Collapsible, Label, Link, Pretty, Tree

from chezmoi_mousse import Id, ParsedJson, Tcss
from chezmoi_mousse.gui import AppType

__all__ = ["InstallHelpScreen"]


class InstallHelpIds(StrEnum):
    screen_id = "install_help_screen"
    exit_button_id = "exit_button"
    chezmoi_docs_link_id = "chezmoi_docs_link"


class InstallHelpScreen(Screen[None], AppType):

    BINDINGS = [Binding(key="escape", action="exit_application", show=False)]

    def __init__(self) -> None:
        super().__init__(
            id=InstallHelpIds.screen_id, classes=Tcss.screen_base.name
        )
        self.path_env = os.environ.get("PATH") or ""

    def compose(self) -> ComposeResult:
        with Vertical(classes=Tcss.install_help.name):
            yield Center(Label(("Chezmoi is not installed or not found.")))
            if not self.path_env:
                yield Center(Label(("The $PATH variable is empty")))
            else:
                yield Collapsible(
                    Pretty(self.path_env),
                    title="'chezmoi' command not found in any search path",
                )

            with Center():
                with Horizontal():
                    yield Tree(label=" Install chezmoi ")
                    with VerticalGroup():
                        yield Link(
                            "chezmoi.io/install",
                            url="https://chezmoi.io/install",
                            id=InstallHelpIds.chezmoi_docs_link_id,
                        )
                        yield Button(
                            "exit app",
                            id=InstallHelpIds.exit_button_id,
                            variant="primary",
                            flat=True,
                        )

    def on_mount(self) -> None:
        self.border_subtitle = self.border_subtitle = (
            Id.operate_screen.border_subtitle()
        )
        help_tree: Tree[ParsedJson] = self.query_exactly_one(Tree[ParsedJson])
        help_tree.show_root = False
        pkg_root = (
            Path(str(files(__package__)))
            if __package__
            else Path(__file__).resolve().parent
        )
        data_file: Path = pkg_root / "data" / "chezmoi_install_commands.json"
        install_help: ParsedJson = json.loads(data_file.read_text())
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
