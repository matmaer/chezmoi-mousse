import json

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Label, Pretty

from chezmoi_mousse import AreaName, CanvasIds, Id, NavBtn, Tcss, ViewName
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.button_groups import NavButtonsVertical
from chezmoi_mousse.gui.widgets import DoctorListView, DoctorTable

__all__ = ["ConfigTab"]


class ConfigTabSwitcher(ContentSwitcher, AppType):

    doctor_stdout: reactive[str | None] = reactive(None)
    cat_config_stdout: reactive[str | None] = reactive(None)
    ignored_stdout: reactive[str | None] = reactive(None)
    template_data_stdout: reactive[str | None] = reactive(None)

    def __init__(self, canvas_ids: CanvasIds):
        self.canvas_ids = canvas_ids
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.right),
            initial=self.canvas_ids.view_id(view=ViewName.doctor_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label('"chezmoi doctor" output', classes=Tcss.section_label.name),
            DoctorTable(),
            Label(
                "Password managers not found in $PATH",
                classes=Tcss.section_label.name,
            ),
            DoctorListView(),
            id=self.canvas_ids.view_id(view=ViewName.doctor_view),
            classes=Tcss.doctor_vertical_scroll.name,
        )
        yield Vertical(
            Label(
                '"chezmoi cat-config" output', classes=Tcss.section_label.name
            ),
            Pretty("<cat-config>", id=ViewName.pretty_cat_config_view),
            id=self.canvas_ids.view_id(view=ViewName.cat_config_view),
        )
        yield Vertical(
            Label('"chezmoi ignored" output', classes=Tcss.section_label.name),
            Pretty("<ignored>", id=ViewName.pretty_ignored_view),
            id=self.canvas_ids.view_id(view=ViewName.git_ignored_view),
        )
        yield Vertical(
            Label('"chezmoi data" output', classes=Tcss.section_label.name),
            Pretty("<template_data>", id=ViewName.pretty_template_data_view),
            id=self.canvas_ids.view_id(view=ViewName.template_data_view),
        )

    def watch_doctor_stdout(self):
        doctor_table = self.query_exactly_one(DoctorTable)
        if self.doctor_stdout is None:
            return
        pw_mgr_cmds: list[str] = doctor_table.populate_doctor_data(
            doctor_data=self.doctor_stdout.splitlines()
        )
        doctor_list_view = self.query_exactly_one(DoctorListView)
        doctor_list_view.populate_listview(pw_mgr_cmds)

    def watch_cat_config_stdout(self):
        if self.cat_config_stdout is None:
            return
        pretty_cat_config = self.query_one(
            f"#{ViewName.pretty_cat_config_view}", Pretty
        )
        pretty_cat_config.update(self.cat_config_stdout.splitlines())

    def watch_ignored_stdout(self):
        if self.ignored_stdout is None:
            return
        pretty_ignored = self.query_one(
            f"#{ViewName.pretty_ignored_view}", Pretty
        )
        pretty_ignored.update(self.ignored_stdout.splitlines())

    def watch_template_data_stdout(self):
        if self.template_data_stdout is None:
            return
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(self.template_data_stdout)
        pretty_template_data.update(template_data_json)


class ConfigTab(Horizontal, AppType):

    def __init__(self) -> None:
        self.ids = Id.config_tab
        super().__init__(id=self.ids.tab_container_id)

    def compose(self) -> ComposeResult:
        yield NavButtonsVertical(
            canvas_ids=self.ids,
            buttons=(
                NavBtn.doctor,
                NavBtn.cat_config,
                NavBtn.ignored,
                NavBtn.template_data,
            ),
        )
        yield ConfigTabSwitcher(self.ids)

    @on(Button.Pressed, Tcss.nav_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(ConfigTabSwitcher)
        if event.button.id == self.ids.button_id(btn=(NavBtn.doctor)):
            switcher.current = self.ids.view_id(view=ViewName.doctor_view)
        elif event.button.id == self.ids.button_id(btn=(NavBtn.cat_config)):
            switcher.current = self.ids.view_id(view=ViewName.cat_config_view)
        elif event.button.id == self.ids.button_id(btn=NavBtn.ignored):
            switcher.current = self.ids.view_id(view=ViewName.git_ignored_view)
        elif event.button.id == self.ids.button_id(btn=NavBtn.template_data):
            switcher.current = self.ids.view_id(
                view=ViewName.template_data_view
            )
