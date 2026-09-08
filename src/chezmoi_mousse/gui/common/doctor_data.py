from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual import work
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse.str_enums import ColorVar

if TYPE_CHECKING:
    from textual import getters

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult


__all__ = ["DoctorTable"]


class DoctorTable(DataTable[Text]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(show_cursor=False)

    def on_mount(self) -> None:
        self.row_color = {
            "ok": self.app.theme_variables[ColorVar.text_success],
            "info": self.app.theme_variables[ColorVar.info],
            "warning": self.app.theme_variables[ColorVar.text_warning],
            "failed": self.app.theme_variables[ColorVar.text_error],
            "error": self.app.theme_variables[ColorVar.text_error],
        }

    @work
    async def _populate_dr_table(self, cmd_result: CommandResult) -> None:
        doctor_lines = cmd_result.std_out.splitlines()
        if cmd_result.returncode != 0:
            self.notify(f"{cmd_result.std_err}", severity="error")
            return
        elif not doctor_lines:
            self.notify("No doctor output available to display.", severity="error")
            return

        self.add_columns(*doctor_lines[0].split())
        rows: list[list[Text]] = []

        for line in doctor_lines[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                new_row = [
                    Text(cell_text, style=self.row_color["info"]) for cell_text in row
                ]
                rows.append(new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.row_color[row[0]]}")
                    for cell_text in row
                ]
                rows.append(new_row)
            elif row[0] == "info" and row[2] == "not set":
                new_row = [
                    Text(cell_text, style=self.row_color["warning"])
                    for cell_text in row
                ]
                rows.append(new_row)
            else:
                new_row = [Text(cell_text) for cell_text in row]
                rows.append(new_row)

        self.add_rows(rows)

    def watch_cmd_result(self, cmd_result: CommandResult | None) -> None:
        if cmd_result is not None:
            self._populate_dr_table(cmd_result)
