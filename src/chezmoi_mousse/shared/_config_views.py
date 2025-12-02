import json
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import DataTable, Pretty, Static

from chezmoi_mousse import AppType, CommandResult, SectionLabels, Tcss

from ._section_headers import MainSectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable


__all__ = [
    "CatConfigView",
    "DoctorTable",
    "DoctorTableView",
    "IgnoredView",
    "PrettyTemplateData",
    "TemplateDataView",
]


class CatConfigView(Vertical):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.cat_config)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.cat_config_output)

    def mount_cat_config_output(self, command_result: CommandResult) -> None:
        self.mount(ScrollableContainer(Static(command_result.std_out)))


class DoctorTable(DataTable[Text], AppType):

    def __init__(self, ids: "AppIds", doctor_data: CommandResult) -> None:
        super().__init__(
            id=ids.datatable.doctor,
            show_cursor=False,
            classes=Tcss.doctor_table,
        )
        self.doctor_data = doctor_data.std_out.splitlines()

    def on_mount(self) -> None:
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


class DoctorTableView(Vertical, AppType):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.doctor)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.doctor_output)

    def populate_doctor_data(self, command_result: CommandResult) -> None:
        self.mount(DoctorTable(ids=self.ids, doctor_data=command_result))


class IgnoredView(Vertical):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.ignored)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.ignored_output)

    def mount_ignored_output(self, command_result: CommandResult) -> None:
        self.mount(
            ScrollableContainer(Pretty(command_result.std_out.splitlines()))
        )


class PrettyTemplateData(Pretty):
    def __init__(self, template_data: CommandResult) -> None:
        parsed = json.loads(template_data.std_out)
        super().__init__(parsed)


class TemplateDataView(Vertical):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.template_data)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.template_data_output)

    def mount_template_data_output(
        self, command_result: CommandResult
    ) -> None:
        self.mount(PrettyTemplateData(template_data=command_result))
