from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Footer, Pretty

from chezmoi_mousse import (
    AppType,
    ContainerName,
    FlatBtn,
    SplashData,
    Tcss,
    ViewName,
)
from chezmoi_mousse.shared import (
    CatConfigOutput,
    DoctorTable,
    FlatButtonsVertical,
    MainSectionLabelText,
    ReactiveHeader,
    SectionLabel,
    TemplateDataOutput,
)

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitSwitcher(ContentSwitcher):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        self.ids = ids
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        super().__init__(
            id=self.ids.content_switcher_id(
                name=ContainerName.init_screen_switcher
            ),
            initial=self.doctor_view_id,
        )
        self.splash_data = splash_data
        self.doctor_table_qid = ids.datatable_id(
            "#", view_name=ViewName.doctor_view
        )

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(
            SectionLabel(MainSectionLabelText.doctor_output),
            DoctorTable(ids=self.ids),
        )
        yield CatConfigOutput(ids=self.ids)
        yield TemplateDataOutput(ids=self.ids)

    def on_mount(self) -> None:
        pretty_cat_config = self.query_one(
            f"#{ViewName.pretty_cat_config_view}", Pretty
        )
        pretty_cat_config.update(
            self.splash_data.cat_config.std_out.splitlines()
        )
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        pretty_template_data.update(self.splash_data.template_data.std_out)


class InitScreen(Screen[None], AppType):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        super().__init__(id=ids.canvas_name, classes=Tcss.screen_base.name)
        self.ids = ids
        self.tab_vertical_id = ids.tab_vertical_id(
            name=ContainerName.left_side
        )
        self.splash_data = splash_data
        self.cat_config_defaults = self.splash_data.cat_config.std_out
        # Button IDs
        self.cat_config_btn_id = self.ids.button_id(btn=(FlatBtn.cat_config))
        # View IDs
        self.cat_config_view_id = self.ids.view_id(
            view=ViewName.cat_config_view
        )
        self.template_data_stdout = self.splash_data.template_data.std_out

    def compose(self) -> ComposeResult:
        yield ReactiveHeader(self.app.init_screen_ids)
        with Horizontal(id=self.ids.canvas_container_id):
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
            with Vertical():
                yield InitSwitcher(ids=self.ids, splash_data=self.splash_data)
        yield Footer()

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            self.ids.content_switcher_id(
                "#", name=ContainerName.init_screen_switcher
            ),
            ContentSwitcher,
        )
        if event.button.id == self.cat_config_btn_id:
            switcher.current = self.cat_config_view_id
        elif event.button.id == self.ids.button_id(btn=FlatBtn.template_data):
            switcher.current = self.ids.view_id(
                view=ViewName.template_data_view
            )
