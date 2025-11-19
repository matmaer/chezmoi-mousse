from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import (
    AppType,
    ContainerName,
    DataTableName,
    FlatBtn,
    SplashData,
    Tcss,
)
from chezmoi_mousse.shared import (
    CatConfigView,
    DoctorTableView,
    FlatButtonsVertical,
    IgnoredView,
    PwMgrInfoView,
    TemplateDataView,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["ConfigTab", "ConfigTabSwitcher"]


class ConfigTabSwitcher(ContentSwitcher):

    splash_data: reactive["SplashData | None"] = reactive(None)

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.container_id = self.ids.container_id(
            name=ContainerName.config_switcher
        )
        super().__init__(
            id=self.container_id, initial=self.ids.container.doctor
        )
        self.doctor_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield DoctorTableView(ids=self.ids)
        yield PwMgrInfoView(ids=self.ids)
        yield CatConfigView(ids=self.ids)
        yield IgnoredView(ids=self.ids)
        yield TemplateDataView(ids=self.ids)

    def watch_splash_data(self):
        if self.splash_data is None:
            return

        doctor_view = self.query_one(
            self.ids.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        pw_mgr_info_view = self.query_one(
            self.ids.views.pw_mgr_info_q, PwMgrInfoView
        )
        pw_mgr_info_view.populate_pw_mgr_info(self.splash_data.doctor)

        cat_config_view = self.query_one(
            self.ids.views.cat_config_q, CatConfigView
        )
        cat_config_view.mount_cat_config_output(self.splash_data.cat_config)

        ignored_view = self.query_one(self.ids.views.ignored_q, IgnoredView)
        ignored_view.mount_ignored_output(self.splash_data.ignored)

        template_data_view = self.query_one(
            self.ids.views.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.splash_data.template_data
        )


class ConfigTab(Horizontal, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.canvas_container_id)

        self.content_switcher_qid = self.ids.container_id(
            "#", name=ContainerName.config_switcher
        )

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            ids=self.ids,
            buttons=(
                FlatBtn.doctor,
                FlatBtn.pw_mgr_info,
                FlatBtn.cat_config,
                FlatBtn.ignored,
                FlatBtn.template_data,
            ),
        )
        yield ConfigTabSwitcher(self.ids)

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(self.content_switcher_qid, ContentSwitcher)
        if event.button.id == self.ids.view_btn.doctor:
            switcher.current = self.ids.container.doctor
        if event.button.id == self.ids.view_btn.pw_mgr_info:
            switcher.current = self.ids.views.pw_mgr_info
        elif event.button.id == self.ids.view_btn.cat_config:
            switcher.current = self.ids.views.cat_config
        elif event.button.id == self.ids.view_btn.ignored:
            switcher.current = self.ids.views.ignored
        elif event.button.id == self.ids.view_btn.template_data:
            switcher.current = self.ids.views.template_data
