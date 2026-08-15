from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual import getters, work
from textual.containers import VerticalGroup
from textual.widgets import Collapsible, DataTable, Label, Link, Static

from chezmoi_mousse.named_tuples import PwMgrData
from chezmoi_mousse.str_enums import Chars, ColorVar, SectionLabel, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["DoctorTable", "PwCollapsible"]


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
    async def populate_table(self, doctor_lines: list[str]) -> None:
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


class PwCollapsible(Collapsible):

    def __init__(self, pw_mgr_data: PwMgrData, dr_message: str) -> None:
        self.pw_mgr_data = pw_mgr_data
        self.dr_message = dr_message
        self.stripped_link = self.pw_mgr_data.link.replace("https://", "").replace(
            "www.", ""
        )

        super().__init__(
            VerticalGroup(
                Label(SectionLabel.project_link, classes=Tcss.sub_section_label),
                Link(self.stripped_link, url=self.pw_mgr_data.link),
                Label(SectionLabel.project_description, classes=Tcss.sub_section_label),
                Static(self.pw_mgr_data.description, markup=False),
                Label(
                    SectionLabel.pw_mgr_additional_info, classes=Tcss.sub_section_label
                ),
                Static(self.pw_mgr_data.info, markup=False),
                classes=Tcss.pw_mgr_group,
            ),
            title=(
                f"[${ColorVar.text_primary}]Doctor check: "
                f"{self.pw_mgr_data.doctor_check}[/] "
                f"[{ColorVar.dimmed}]({self.dr_message})[/]"
            ),
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
        )
