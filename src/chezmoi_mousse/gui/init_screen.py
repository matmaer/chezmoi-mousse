from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Pretty

from chezmoi_mousse import ContainerName, FlatBtn, SplashData, Tcss, ViewName
from chezmoi_mousse.shared import (
    DoctorTable,
    FlatButtonsVertical,
    MainSectionLabelText,
    SectionLabel,
)

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitSwitcher(ContentSwitcher):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.doctor_list_view_id = self.ids.view_id(view=ViewName.doctor_view)
        super().__init__(
            id=self.ids.content_switcher_id(
                name=ContainerName.init_screen_switcher
            ),
            initial=self.doctor_list_view_id,
        )
        self.doctor_table_qid = ids.datatable_id(
            "#", view_name=ViewName.doctor_view
        )

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(
            SectionLabel(MainSectionLabelText.doctor_output),
            DoctorTable(ids=self.ids),
        )
        yield ScrollableContainer(
            SectionLabel(MainSectionLabelText.cat_config_output),
            Pretty("<cat-config>", id=ViewName.pretty_cat_config_view),
            id=self.ids.view_id(view=ViewName.cat_config_view),
        )
        yield ScrollableContainer(
            SectionLabel(MainSectionLabelText.template_data_output),
            Pretty("<template_data>", id=ViewName.pretty_template_data_view),
            id=self.ids.view_id(view=ViewName.template_data_view),
        )


class InitScreen(Screen[None]):

    def __init__(
        self, *, ids: "CanvasIds", commands_data: "SplashData"
    ) -> None:
        self.ids = ids
        super().__init__(id=ids.canvas_name, classes=Tcss.screen_base.name)
        self.commands_data = commands_data
        self.tab_vertical_id = ids.tab_vertical_id(
            name=ContainerName.left_side
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.tab_vertical_id, classes=Tcss.tab_left_vertical.name
        ):
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.template_data,
                ),
            )
        yield InitSwitcher(self.ids)
