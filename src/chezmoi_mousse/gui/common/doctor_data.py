from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual import getters, work
from textual.widgets import DataTable

from chezmoi_mousse.str_enums import ColorVar

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["DoctorTable"]


class DoctorTable(DataTable[Text]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        super().__init__(cursor_type="row", show_cursor=False)

    def on_mount(self) -> None:
        self.row_color = {
            "ok": self.app.get_color(ColorVar.text_success),
            "info": self.app.get_color(ColorVar.info),
            "warning": self.app.get_color(ColorVar.text_warning),
            "failed": self.app.get_color(ColorVar.text_error),
            "error": self.app.get_color(ColorVar.text_error),
        }

    @work
    async def populate_table(self, doctor_std_out: str) -> None:
        doctor_lines = doctor_std_out.splitlines()
        if not doctor_lines:
            self.notify("No doctor output available to display.")
            return
        self.add_columns(*doctor_lines[0].split())

        for line in doctor_lines[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                new_row = [
                    Text(cell_text, style=self.row_color["info"]) for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.row_color[row[0]]}")
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                new_row = [
                    Text(cell_text, style=self.row_color["warning"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            else:
                text_row = [Text(cell_text) for cell_text in row]
                self.add_row(*text_row)
