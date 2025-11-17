import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Footer, Pretty, Static

from chezmoi_mousse import (
    AppType,
    ContainerName,
    DataTableName,
    FlatBtn,
    SplashData,
    Tcss,
    ViewName,
)
from chezmoi_mousse.shared import (
    CatConfigOutput,
    DoctorTableView,
    FlatButtonsVertical,
    ReactiveHeader,
    TemplateDataOutput,
)

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitSwitcher(ContentSwitcher):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        self.ids = ids
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        self.doctor_view_qid = self.ids.view_id("#", view=ViewName.doctor_view)
        super().__init__(
            id=self.ids.content_switcher_id(
                name=ContainerName.init_screen_switcher
            ),
            initial=self.doctor_view_id,
        )
        self.splash_data = splash_data
        self.doctor_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield DoctorTableView(ids=self.ids)
        yield CatConfigOutput(ids=self.ids)
        yield TemplateDataOutput(ids=self.ids)

    def on_mount(self) -> None:
        doctor_view = self.query_one(self.doctor_view_qid, DoctorTableView)
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        cat_config = self.query_one(f"#{ViewName.cat_config_view}", Static)
        cat_config.update(self.splash_data.cat_config.std_out)
        template_cmd_output = self.splash_data.template_data.std_out
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(template_cmd_output)
        pretty_template_data.update(template_data_json)


class InitScreen(Screen[None], AppType):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        super().__init__()
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
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.template_data,
                ),
            )
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
