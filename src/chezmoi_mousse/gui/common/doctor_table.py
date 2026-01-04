from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import DataTable

from chezmoi_mousse import AppType, CommandResult, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable

__all__ = ["DoctorTable"]


class DoctorTable(DataTable[Text], AppType):

    def __init__(self, ids: "AppIds", doctor_data: CommandResult) -> None:
        super().__init__(
            id=ids.datatable.doctor,
            show_cursor=False,
            classes=Tcss.doctor_table,
        )
        self.doctor_data = doctor_data.std_out.splitlines()

    def on_mount(self) -> None:
        if len(self.doctor_data) < 2:
            self.app.notify("No doctor data to display", severity="error")
            return
        self.dr_style = {
            "ok": self.app.theme_variables["text-success"],
            "info": self.app.theme_variables["foreground-darken-1"],
            "warning": self.app.theme_variables["text-warning"],
            "failed": self.app.theme_variables["text-error"],
            "error": self.app.theme_variables["text-error"],
        }
        if not self.columns:
            self.add_columns(*self.doctor_data[0].split())

        for line in self.doctor_data[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
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
                new_row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            else:
                row = [Text(cell_text) for cell_text in row]
                self.add_row(*row)
