import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Pretty

from chezmoi_mousse import (
    AppType,
    ContainerName,
    DataTableName,
    FlatBtn,
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
    from chezmoi_mousse import CanvasIds, CommandResult

__all__ = ["ConfigTab", "ConfigTabSwitcher"]


class ConfigTabSwitcher(ContentSwitcher):

    doctor_results: reactive["CommandResult | None"] = reactive(None)
    cat_config_results: reactive["CommandResult | None"] = reactive(None)
    ignored_results: reactive["CommandResult | None"] = reactive(None)
    template_data_results: reactive["CommandResult | None"] = reactive(None)

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        super().__init__(
            id=self.ids.content_switcher_id(
                name=ContainerName.config_switcher
            ),
            initial=self.doctor_view_id,
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

    def watch_doctor_results(self):
        doctor_table = self.query_one(self.doctor_table_qid, DoctorTable)
        if self.doctor_results is None:
            return
        doctor_table.populate_doctor_data(
            doctor_data=self.doctor_results.std_out.splitlines()
        )
        pw_mgr_info_view = self.query_one(self.pw_mgr_info_qid, PwMgrInfoView)
        pw_mgr_info_view.populate_pw_mgr_info(self.doctor_results)

    def watch_cat_config_results(self):
        if self.cat_config_results is None:
            return
        pretty_cat_config = self.query_one(
            f"#{ViewName.pretty_cat_config_view}", Pretty
        )
        pretty_cat_config.update(self.cat_config_results.std_out.splitlines())

    def watch_ignored_results(self):
        if self.ignored_results is None:
            return
        pretty_ignored = self.query_one(
            f"#{ViewName.pretty_ignored_view}", Pretty
        )
        pretty_ignored.update(self.ignored_results.std_out.splitlines())

    def watch_template_data_results(self):
        if self.template_data_results is None:
            return
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(self.template_data_results.std_out)
        pretty_template_data.update(template_data_json)


class ConfigTab(Horizontal, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.canvas_container_id)

        self.tab_vertical_id = ids.tab_vertical_id(
            name=ContainerName.left_side
        )
        self.content_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.config_switcher
        )
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
        with Vertical(
            id=self.tab_vertical_id, classes=Tcss.tab_left_vertical.name
        ):
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
