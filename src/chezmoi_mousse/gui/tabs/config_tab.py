import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Pretty, Static

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
    DoctorTable,
    FlatButtonsVertical,
    PwMgrInfoView,
    SectionLabel,
    SectionLabelText,
    TemplateDataOutput,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["ConfigTab", "ConfigTabSwitcher"]


class ConfigTabSwitcher(ContentSwitcher):

    splash_data: reactive["SplashData | None"] = reactive(None)

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        self.content_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.config_switcher
        )
        super().__init__(
            id=self.content_switcher_id, initial=self.doctor_view_id
        )
        self.pw_mgr_info_qid = f"#{self.ids.view_id(
            view=ViewName.pw_mgr_info_view
        )}"
        self.doctor_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield Vertical(
            SectionLabel(SectionLabelText.doctor_output),
            DoctorTable(ids=self.ids),
            id=self.doctor_view_id,
        )
        yield PwMgrInfoView(ids=self.ids)
        yield CatConfigOutput(ids=self.ids)
        yield ScrollableContainer(
            SectionLabel(SectionLabelText.ignored_output),
            Pretty("<ignored>", id=ViewName.pretty_ignored_view),
            id=self.ids.view_id(view=ViewName.git_ignored_view),
        )
        yield TemplateDataOutput(ids=self.ids)

    def watch_splash_data(self):
        if self.splash_data is None:
            return

        doctor_table = self.query_one(self.doctor_table_qid, DoctorTable)
        doctor_table.populate_doctor_data(
            doctor_data=self.splash_data.doctor.std_out.splitlines()
        )
        pw_mgr_info_view = self.query_one(self.pw_mgr_info_qid, PwMgrInfoView)
        pw_mgr_info_view.populate_pw_mgr_info(self.splash_data.doctor)

        cat_config_view = self.query_one(
            f"#{ViewName.cat_config_view}", Static
        )
        cat_config_view.update(self.splash_data.cat_config.std_out)

        pretty_ignored = self.query_one(
            f"#{ViewName.pretty_ignored_view}", Pretty
        )
        pretty_ignored.update(self.splash_data.ignored.std_out.splitlines())

        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(self.splash_data.template_data.std_out)
        pretty_template_data.update(template_data_json)


class ConfigTab(Horizontal, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.canvas_container_id)

        self.content_switcher_qid = self.ids.content_switcher_id(
            "#", name=ContainerName.config_switcher
        )

        # Button IDs
        self.cat_config_btn_id = self.ids.button_id(btn=(FlatBtn.cat_config))
        self.doctor_btn_id = self.ids.button_id(btn=(FlatBtn.doctor))
        self.pw_mgr_info_btn_id = self.ids.button_id(btn=FlatBtn.pw_mgr_info)
        self.ignored_btn_id = self.ids.button_id(btn=FlatBtn.ignored)
        self.template_data_btn_id = self.ids.button_id(
            btn=FlatBtn.template_data
        )
        # View IDs
        self.cat_config_view_id = self.ids.view_id(
            view=ViewName.cat_config_view
        )
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        self.ignored_view_id = self.ids.view_id(view=ViewName.git_ignored_view)
        self.pw_mgr_info_view_id = self.ids.view_id(
            view=ViewName.pw_mgr_info_view
        )
        self.template_data_view_id = self.ids.view_id(
            view=ViewName.template_data_view
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
        if event.button.id == self.doctor_btn_id:
            switcher.current = self.doctor_view_id
        if event.button.id == self.pw_mgr_info_btn_id:
            switcher.current = self.pw_mgr_info_view_id
        elif event.button.id == self.cat_config_btn_id:
            switcher.current = self.cat_config_view_id
        elif event.button.id == self.ignored_btn_id:
            switcher.current = self.ignored_view_id
        elif event.button.id == self.template_data_btn_id:
            switcher.current = self.template_data_view_id
