from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
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
    Pretty,
    Static,
    Switch,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import (
    FlatBtnLabel,
    OpBtnLabel,
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
from .common.components import MainSectionLabel
from .common.contents import ContentsView
from .common.doctor_data import DoctorTable
from .common.filtered_dir_tree import FilteredDirTree
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import DestDirTree, ManagedTree
from .common.messages import TabBtnMsg
from .common.switchers import ViewSwitcher

if TYPE_CHECKING:
    from chezmoi_mousse.app_ids import AppIds

__all__ = ["AddTab", "ApplyTab", "ConfigTab", "LogsTab", "ReAddTab"]


class AddTab(TabPane):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.add, title=TabLabel.add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Vertical(
                FilteredDirTree(dest_dir=store.cfg.dest_dir),
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
        self.contents_view.border_title = f" {store.cfg.dest_dir} "
        self.contents_view.show_path = store.cfg.dest_dir
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
        if event.node.data.path == store.cfg.dest_dir:
            self.contents_view.border_title = f" {store.cfg.dest_dir} "
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
            yield ViewSwitcher(self.ids)
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
    class CatConfigStatic(Static): ...

    class PrettyIgnored(Pretty): ...

    class PrettyTemplateData(Pretty): ...

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.config, title=TabLabel.config)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                self.ids,
                labels=(
                    FlatBtnLabel.doctor,
                    FlatBtnLabel.cat_config,
                    FlatBtnLabel.ignored,
                    FlatBtnLabel.template_data,
                    FlatBtnLabel.diagram,
                ),
            )
            with ContentSwitcher(initial=self.ids.container.doctor):
                yield Vertical(
                    MainSectionLabel(SectionLabel.doctor_output),
                    DoctorTable(),
                    id=self.ids.container.doctor,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.cat_config_output),
                    ConfigTab.CatConfigStatic("Loading..."),
                    id=self.ids.container.cat_config,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.ignored_output),
                    ScrollableContainer(ConfigTab.PrettyIgnored("Loading...")),
                    id=self.ids.container.ignored,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.template_data_output),
                    ScrollableContainer(ConfigTab.PrettyTemplateData("Loading...")),
                    id=self.ids.container.template_data,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.diagram),
                    Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram),
                    id=self.ids.container.diagram,
                )

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == FlatBtnLabel.doctor:
            self.switcher.current = self.ids.container.doctor
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
            yield ViewSwitcher(self.ids)
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
