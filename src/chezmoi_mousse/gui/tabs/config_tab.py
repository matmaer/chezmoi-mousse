from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import TAB_IDS, AppType, FlatBtn, SplashData, Tcss
from chezmoi_mousse.shared import (
    CatConfigView,
    DoctorTableView,
    FlatButtonsVertical,
    IgnoredView,
    PwMgrInfoView,
    TemplateDataView,
)

__all__ = ["ConfigTab", "ConfigTabSwitcher"]


class ConfigTabSwitcher(ContentSwitcher):

    splash_data: reactive["SplashData | None"] = reactive(None)

    def __init__(self):
        super().__init__(
            id=TAB_IDS.config.switcher.config_tab,
            initial=TAB_IDS.config.container.doctor,
        )

    def compose(self) -> ComposeResult:
        yield DoctorTableView(ids=TAB_IDS.config)
        yield PwMgrInfoView(ids=TAB_IDS.config)
        yield CatConfigView(ids=TAB_IDS.config)
        yield IgnoredView(ids=TAB_IDS.config)
        yield TemplateDataView(ids=TAB_IDS.config)

    def watch_splash_data(self):
        if self.splash_data is None:
            return

        doctor_view = self.query_one(
            TAB_IDS.config.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        pw_mgr_info_view = self.query_one(
            TAB_IDS.config.view.pw_mgr_info_q, PwMgrInfoView
        )
        pw_mgr_info_view.populate_pw_mgr_info(self.splash_data.doctor)

        cat_config_view = self.query_one(
            TAB_IDS.config.view.cat_config_q, CatConfigView
        )
        cat_config_view.mount_cat_config_output(self.splash_data.cat_config)

        ignored_view = self.query_one(
            TAB_IDS.config.view.ignored_q, IgnoredView
        )
        ignored_view.mount_ignored_output(self.splash_data.ignored)

        template_data_view = self.query_one(
            TAB_IDS.config.view.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.splash_data.template_data
        )


class ConfigTab(Horizontal, AppType):

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            ids=TAB_IDS.config,
            buttons=(
                FlatBtn.doctor,
                FlatBtn.pw_mgr_info,
                FlatBtn.cat_config,
                FlatBtn.ignored,
                FlatBtn.template_data,
            ),
        )
        yield ConfigTabSwitcher()

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            TAB_IDS.config.switcher.config_tab_q, ConfigTabSwitcher
        )
        if event.button.id == TAB_IDS.config.flat_btn.doctor:
            switcher.current = TAB_IDS.config.container.doctor
        if event.button.id == TAB_IDS.config.flat_btn.pw_mgr_info:
            switcher.current = TAB_IDS.config.view.pw_mgr_info
        elif event.button.id == TAB_IDS.config.flat_btn.cat_config:
            switcher.current = TAB_IDS.config.view.cat_config
        elif event.button.id == TAB_IDS.config.flat_btn.ignored:
            switcher.current = TAB_IDS.config.view.ignored
        elif event.button.id == TAB_IDS.config.flat_btn.template_data:
            switcher.current = TAB_IDS.config.view.template_data
