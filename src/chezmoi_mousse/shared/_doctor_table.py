from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import DataTable

from chezmoi_mousse import AppType, DataTableName, Tcss, ViewName

from ._section_headers import MainSectionLabelText, SectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["DoctorTableView"]


class DoctorTable(DataTable[Text], AppType):

    def __init__(self, ids: "CanvasIds") -> None:

        super().__init__(
            id=ids.datatable_id(data_table_name=DataTableName.doctor_table),
            show_cursor=False,
            classes=Tcss.doctor_table.name,
        )

        self.pw_mgr_commands: list[str] = []

    def on_mount(self) -> None:
        self.dr_style = {
            "ok": self.app.theme_variables["text-success"],
            "info": self.app.theme_variables["foreground-darken-1"],
            "warning": self.app.theme_variables["text-warning"],
            "failed": self.app.theme_variables["text-error"],
            "error": self.app.theme_variables["text-error"],
        }

    def populate_doctor_data(self, doctor_data: list[str]) -> list[str]:

        if not self.columns:
            self.add_columns(*doctor_data[0].split())

        for line in doctor_data[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                self.pw_mgr_commands.append((row[1]))
                new_row = [
                    Text(cell_text, style=self.dr_style["info"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.dr_style[row[0]]}")
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                self.pw_mgr_commands.append((row[1]))
                new_row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            else:
                row = [Text(cell_text) for cell_text in row]
                self.add_row(*row)
        return self.pw_mgr_commands


class DoctorTableView(Vertical):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        super().__init__(id=self.doctor_view_id)

    def compose(self) -> ComposeResult:
        yield SectionLabel(MainSectionLabelText.doctor_output)
        yield ScrollableContainer(DoctorTable(ids=self.ids))
