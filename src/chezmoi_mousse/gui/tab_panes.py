from __future__ import annotations

from typing import TYPE_CHECKING

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.widgets import (
    Button,
    ContentSwitcher,
    DirectoryTree,
    Label,
    Pretty,
    Static,
    Switch,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.enum_data import PwMgrEnum
from chezmoi_mousse.named_tuples import PwMgrData
from chezmoi_mousse.str_enums import (
    FlatBtnLabel,
    OpBtnLabel,
    PwMgrInfo,
    SectionLabel,
    TabLabel,
    Tcss,
)

from .common.actionables import (
    FlatButtonsVertical,
    RefreshBtn,
    ReviewBtn,
    ReviewBtnGroup,
    SwitchSlider,
    TabButtons,
)
from .common.ascii_constants import FLOW_DIAGRAM
from .common.components import CatConfigStatic
from .common.contents import ContentsView
from .common.doctor_data import DoctorTable, PwCollapsible
from .common.filtered_dir_tree import FilteredDirTree
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import DestDirTree, ManagedTree
from .common.messages import TabBtnMsg
from .common.switchers import ViewSwitcher

if TYPE_CHECKING:
    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["AddTab", "ApplyTab", "ConfigTab", "LogsTab", "ReAddTab"]


class AddTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.add, title=TabLabel.add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Vertical(
                FilteredDirTree(dest_dir=self.app.cmattr.dest_dir),
                RefreshBtn(self.ids),
                id=self.ids.container.left_side,
                classes=Tcss.tab_left_vertical,
            )
            with Vertical():
                yield ContentsView(self.ids)
                yield ReviewBtnGroup(self.ids, (OpBtnLabel.add_review,))
        yield SwitchSlider(self.ids)

    def on_mount(self) -> None:
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.contents_view = self.query_one(self.ids.container.contents_q, ContentsView)
        self.contents_view.add_class(Tcss.add_tab_contents_view)
        self.contents_view.border_title = f" {self.app.cmattr.dest_dir} "
        self.contents_view.show_path = self.app.cmattr.dest_dir
        self.add_review_btn = self.query_one(self.ids.op_btn.add_review_q, ReviewBtn)

    @on(DirectoryTree.FileSelected)
    @on(DirectoryTree.DirectorySelected)
    def update_contents_view(
        self, event: DirectoryTree.FileSelected | DirectoryTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is None:
            raise ValueError("event.node.data is None in update_contents_view")
        self.contents_view.show_path = event.node.data.path
        if event.node.data.path == self.app.cmattr.dest_dir:
            self.contents_view.border_title = f" {self.app.cmattr.dest_dir} "
        else:
            self.contents_view.border_title = f" {event.node.data.path.name} "

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch.show_managed:
            self.dir_tree.show_managed = event.value
        elif event.switch.id == self.ids.switch.show_unwanted:
            self.dir_tree.show_unwanted = event.value
        self.dir_tree.reload()


class ApplyTab(TabPane):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.apply, title=TabLabel.apply)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(self.ids)
            yield Vertical(
                ViewSwitcher(self.ids),
                ReviewBtnGroup(
                    self.ids,
                    (
                        OpBtnLabel.apply_review,
                        OpBtnLabel.forget_review,
                        OpBtnLabel.destroy_review,
                    ),
                ),
            )
        yield SwitchSlider(self.ids)

    def on_mount(self) -> None:
        self.managed_tree = self.query_one(self.ids.managed_tree_q, ManagedTree)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch.show_unchanged:
            self.managed_tree.show_unchanged = event.value
        elif event.switch.id == self.ids.switch.show_unmanaged:
            self.managed_tree.show_unmanaged = event.value
        elif event.switch.id == self.ids.switch.expand_all:
            self.managed_tree.expand_all = event.value


class ConfigTab(TabPane):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.config, title=TabLabel.config)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                self.ids,
                labels=(
                    FlatBtnLabel.doctor,
                    FlatBtnLabel.pw_mgr_info,
                    FlatBtnLabel.cat_config,
                    FlatBtnLabel.ignored,
                    FlatBtnLabel.template_data,
                    FlatBtnLabel.diagram,
                ),
            )
            with ContentSwitcher(initial=self.ids.container.doctor):
                yield Vertical(
                    Label(SectionLabel.doctor_output, classes=Tcss.main_section_label),
                    DoctorTable(),
                    id=self.ids.container.doctor,
                )
                yield Vertical(
                    Label(
                        SectionLabel.password_managers, classes=Tcss.main_section_label
                    ),
                    id=self.ids.container.pw_mgr_info,
                )
                yield Vertical(
                    Label(
                        SectionLabel.cat_config_output, classes=Tcss.main_section_label
                    ),
                    CatConfigStatic("Loading..."),
                    id=self.ids.container.cat_config,
                )
                yield Vertical(
                    Label(SectionLabel.ignored_output, classes=Tcss.main_section_label),
                    ScrollableContainer(Pretty("Loading...")),
                    id=self.ids.container.ignored,
                )
                yield Vertical(
                    Label(
                        SectionLabel.template_data_output,
                        classes=Tcss.main_section_label,
                    ),
                    ScrollableContainer(Pretty("Loading...")),
                    id=self.ids.container.template_data,
                )
                yield Vertical(
                    Label(SectionLabel.diagram, classes=Tcss.main_section_label),
                    Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram),
                    id=self.ids.container.diagram,
                )

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self._load_views()

    def _get_pw_mgr_data(self, doctor_check: str) -> PwMgrData:
        for member in PwMgrEnum:
            if member.value.doctor_check == doctor_check:
                return PwMgrEnum[member.name].value
        raise ValueError(f"No PwMgrEnum member for doctor_check '{doctor_check}'")

    @work
    async def _populate_pw_mgr_info(self, doctor_lines: list[str]) -> None:
        pw_mgr_info = self.query_one(self.ids.container.pw_mgr_info_q, Vertical)

        pw_mgr_entries: list[tuple[PwMgrData, str]] = []
        all_pw_mgr_commands = [pw_mgr.value.doctor_check for pw_mgr in PwMgrEnum]

        for line in doctor_lines[1:]:  # Skip header line
            row = tuple(line.split(maxsplit=2))
            if row[1] not in all_pw_mgr_commands:
                continue
            pw_mgr_data = self._get_pw_mgr_data(row[1])
            pw_mgr_entries.append((pw_mgr_data, row[2]))

        for pw_mgr_data, doctor_message in pw_mgr_entries:
            pw_collapsible = PwCollapsible(
                pw_mgr_data=pw_mgr_data, dr_message=doctor_message
            )
            pw_mgr_info.mount(pw_collapsible)
        pw_mgr_info.mount(Static(f"\n{PwMgrInfo.info_warning}"))

    @work
    async def _load_views(self) -> None:
        doctor_view = self.query_one(self.ids.container.doctor_q, Vertical)
        doctor_table = doctor_view.query_exactly_one(DoctorTable)
        doctor_table.populate_table(store.doctor_result.std_out.splitlines())

        self._populate_pw_mgr_info(store.doctor_result.std_out.splitlines())

        cat_config_static = self.query_exactly_one(CatConfigStatic)
        cat_config_static.update(
            "\n".join(line for line in (store.cat_config_result.std_out.splitlines()))
        )

        ignored_view = self.query_one(self.ids.container.ignored_q, Vertical)
        pretty_ignored = ignored_view.query_exactly_one(Pretty)
        pretty_ignored.update(store.ignored_result.std_out.splitlines())

        template_data_view = self.query_one(
            self.ids.container.template_data_q, Vertical
        )
        template_data_pretty = template_data_view.query_exactly_one(Pretty)
        template_data_pretty.update(store.parsed_template_data)

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == FlatBtnLabel.doctor:
            self.switcher.current = self.ids.container.doctor
        elif event.button.label == FlatBtnLabel.pw_mgr_info:
            self.switcher.current = self.ids.container.pw_mgr_info
        elif event.button.label == FlatBtnLabel.cat_config:
            self.switcher.current = self.ids.container.cat_config
        elif event.button.label == FlatBtnLabel.ignored:
            self.switcher.current = self.ids.container.ignored
        elif event.button.label == FlatBtnLabel.template_data:
            self.switcher.current = self.ids.container.template_data
        elif event.button.label == FlatBtnLabel.diagram:
            self.switcher.current = self.ids.container.diagram


class LogsTab(TabPane):
    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=TabLabel.logs, title=TabLabel.logs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TabButtons(self.app_ids, (TabLabel.cmd_log, TabLabel.app_log))
            with ContentSwitcher(initial=self.app_ids.richlog.cmd):
                yield CmdLog(self.app_ids)
                yield AppLog()

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(TabButtons)
        self.switcher = self.query_exactly_one(ContentSwitcher)

    @on(TabBtnMsg)
    def switch_content(self, msg: TabBtnMsg) -> None:
        msg.stop()
        if msg.button.label == TabLabel.app_log:
            self.switcher.current = self.app_ids.richlog.app
        elif msg.button.label == TabLabel.cmd_log:
            self.switcher.current = self.app_ids.richlog.cmd


class ReAddTab(TabPane):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.re_add, title=TabLabel.re_add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(self.ids)
            yield Vertical(
                ViewSwitcher(self.ids),
                ReviewBtnGroup(
                    self.ids,
                    (
                        OpBtnLabel.re_add_review,
                        OpBtnLabel.forget_review,
                        OpBtnLabel.destroy_review,
                    ),
                ),
            )
        yield SwitchSlider(self.ids)

    def on_mount(self) -> None:
        self.managed_tree = self.query_one(self.ids.managed_tree_q, ManagedTree)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch.show_unchanged:
            self.managed_tree.show_unchanged = event.value
        elif event.switch.id == self.ids.switch.show_unmanaged:
            self.managed_tree.show_unmanaged = event.value
        elif event.switch.id == self.ids.switch.expand_all:
            self.managed_tree.expand_all = event.value
