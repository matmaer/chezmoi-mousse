import json
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import DataTable, Pretty, Static

from chezmoi_mousse import (
    AppType,
    CommandResult,
    DataTableName,
    Tcss,
    ViewName,
)

from ._section_headers import SectionLabel, SectionLabelText

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable


__all__ = [
    "CatConfigView",
    "DoctorTableView",
    "IgnoredView",
    "TemplateDataView",
]


class CatConfigView(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.views.cat_config)

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.cat_config_output)

    def mount_cat_config_output(self, command_result: CommandResult) -> None:
        self.mount(ScrollableContainer(Static(command_result.std_out)))


class DoctorTableView(Vertical, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        self.view_id = self.ids.view_id(view=ViewName.doctor_view)
        super().__init__(id=self.view_id)
        self.doctor_table_id = self.ids.datatable_id(
            data_table_name=DataTableName.doctor_table
        )
        self.doctor_table_qid = self.ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.doctor_output)
        yield DataTable(
            id=self.doctor_table_id,
            show_cursor=False,
            classes=Tcss.doctor_table.name,
        )

    def on_mount(self) -> None:
        self.dr_style = {
            "ok": self.app.theme_variables["text-success"],
            "info": self.app.theme_variables["foreground-darken-1"],
            "warning": self.app.theme_variables["text-warning"],
            "failed": self.app.theme_variables["text-error"],
            "error": self.app.theme_variables["text-error"],
        }

    def populate_doctor_data(self, command_result: CommandResult) -> None:

        doctor_data = command_result.std_out.splitlines()

        doctor_table = self.query_one(self.doctor_table_qid, DataTableText)

        if not doctor_table.columns:
            doctor_table.add_columns(*doctor_data[0].split())

        for line in doctor_data[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                new_row = [
                    Text(cell_text, style=self.dr_style["info"])
                    for cell_text in row
                ]
                doctor_table.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.dr_style[row[0]]}")
                    for cell_text in row
                ]
                doctor_table.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                new_row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                doctor_table.add_row(*new_row)
            else:
                row = [Text(cell_text) for cell_text in row]
                doctor_table.add_row(*row)


class IgnoredView(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.views.ignored)

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.ignored_output)

    def mount_ignored_output(self, command_result: CommandResult) -> None:
        self.mount(
            ScrollableContainer(Pretty(command_result.std_out.splitlines()))
        )


class TemplateDataView(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.template_data_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.template_data_output)

    def mount_template_data_output(
        self, command_result: CommandResult
    ) -> None:
        parsed = json.loads(command_result.std_out)
        self.mount(
            ScrollableContainer(
                Pretty(parsed, id=ViewName.pretty_template_data_view)
            )
        )
