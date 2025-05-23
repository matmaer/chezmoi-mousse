from pathlib import Path

from rich.text import Text
from textual.binding import Binding
from textual.app import ComposeResult
from textual.containers import VerticalScroll, HorizontalGroup
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Collapsible, DataTable

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.components import ConfigDump, AutoWarning, PathView


class Operate(ModalScreen):

    BINDINGS = [
        Binding(key="escape", action="dismiss", description="close", show=True)
    ]

    def __init__(self, path_to_add: Path) -> None:
        self.path_to_add = path_to_add
        self.files_to_add: list[Path] = []
        self.add_path_items: list[HorizontalGroup] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield AutoWarning(id="auto_warning")
        with VerticalScroll():
            yield from self.add_path_items
        yield HorizontalGroup(
            Button("- Select All -", id="selectall", classes="operate-button"),
            Button("- Add Files -", id="addfile", classes="operate-button"),
            Button("- Cancel -", id="canceladding", classes="operate-button"),
            id="button_container",
        )

    def on_mount(self) -> None:
        self.files_to_add: list[Path] = []
        if self.path_to_add.is_file():
            self.files_to_add: list[Path] = [self.path_to_add]
        elif self.path_to_add.is_dir():
            self.files_to_add = [
                f for f in chezmoi.unmanaged_in_d(self.path_to_add)
            ]
        if len(self.files_to_add) == 0:
            self.notify(
                f"The selected directory does not contain unmanaged files to add.\nDirectory: {self.path_to_add}."
            )
            self.dismiss()
        elif len(self.files_to_add) > 1:
            self.add_label = "- Add Files -"

        for f in self.files_to_add:
            self.add_path_items.append(
                HorizontalGroup(
                    Checkbox(classes="operate-checkbox"),
                    Collapsible(
                        PathView(),
                        title=str(f.relative_to(chezmoi.dest_dir)),
                        classes="operate-collapsible",
                    ),
                )
            )
        self.refresh(recompose=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "addfile":
            for f in self.files_to_add:
                chezmoi.add(f)
                self.notify(f"Added {f} to chezmoi.")
            self.screen.dismiss()
        elif event.button.id == "canceladding":
            self.notify("No files were added.")
            self.screen.dismiss()


class GitLog(ModalScreen):

    BINDINGS = [Binding(key="escape", action="dismiss", description="close")]

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="gitlogtable", show_cursor=False, classes="doctormodals"
        )

    def on_mount(self) -> None:
        table = self.query_one("#gitlogtable", DataTable)
        table.border_title = "chezmoi git log - command output"
        table.border_subtitle = "double click or escape to close"
        styles = {
            "ok": f"{self.app.current_theme.success}",
            "warning": f"{self.app.current_theme.warning}",
            "error": f"{self.app.current_theme.error}",
            "info": f"{self.app.current_theme.foreground}",
        }
        table.add_columns("COMMIT", "MESSAGE")
        for line in chezmoi.git_log:
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                row = [
                    Text(cell_text, style=f"{styles['ok']}")
                    for cell_text in columns
                ]
                table.add_row(*row)
            elif columns[1].split(maxsplit=1)[0] == "Update":
                row = [
                    Text(cell_text, style=f"{styles['warning']}")
                    for cell_text in columns
                ]
                table.add_row(*row)
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                row = [
                    Text(cell_text, style=f"{styles['error']}")
                    for cell_text in columns
                ]
                table.add_row(*row)
            else:
                table.add_row(*columns)

    def on_click(self, event: Click) -> None:
        if event.chain == 2:
            self.dismiss()


class ConfigDumpModal(ModalScreen):

    BINDINGS = [Binding(key="escape", action="dismiss", description="close")]

    def compose(self) -> ComposeResult:
        yield ConfigDump(id="configdump", classes="doctormodals")

    def on_mount(self) -> None:
        self.query_one("#configdump").border_title = (
            "chezmoi dump-config - command output"
        )
        self.query_one("#configdump").border_subtitle = (
            "double click or escape to close"
        )

    def on_click(self, event: Click) -> None:
        if event.chain == 2:
            self.dismiss()
