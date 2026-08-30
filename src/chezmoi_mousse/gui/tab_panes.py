from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
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
    BtnLabel,
    SectionLabel,
    Tcss,
)

from .common.actionables import (
    FlatButtonsVertical,
    RefreshBtn,
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
    from textual.app import ComposeResult


__all__ = ["AddTab", "ApplyTab", "ConfigTab", "LogsTab", "ReAddTab"]


class AddTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.add.pane_id, title=BtnLabel.add)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Vertical(
                # TODO: Lazy(FilteredDirTree(dest_dir=store.cfg.dest_dir)),
                RefreshBtn(app_ids=store.add_ids),
                id=store.add_ids.container.left_side,
                classes=Tcss.tab_left_vertical,
            )
            with Vertical():
                yield ContentsView(store.add_ids)
                yield ReviewBtnGroup(
                    app_ids=store.add_ids, labels=(BtnLabel.add_review,)
                )
        yield SwitchSlider(app_ids=store.add_ids)

    def on_mount(self) -> None:
        self.contents_view = self.query_one(
            store.add_ids.container.contents_q, ContentsView
        )
        self.contents_view.add_class(Tcss.add_tab_contents_view)

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
        dir_tree = self.query_exactly_one(FilteredDirTree)
        if event.switch.id == store.add_ids.switch.show_managed:
            dir_tree.show_managed = event.value
        elif event.switch.id == store.add_ids.switch.show_unwanted:
            dir_tree.show_unwanted = event.value
        dir_tree.reload()


class ApplyTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.apply.pane_id, title=BtnLabel.apply)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(store.apply_ids)
            yield ViewSwitcher(store.apply_ids)
        yield SwitchSlider(app_ids=store.apply_ids)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        managed_tree = self.query_one(store.apply_ids.managed_tree_q, ManagedTree)
        if event.switch.id == store.apply_ids.switch.show_unchanged:
            managed_tree.show_unchanged = event.value
        elif event.switch.id == store.apply_ids.switch.show_unmanaged:
            managed_tree.show_unmanaged = event.value
        elif event.switch.id == store.apply_ids.switch.expand_all:
            managed_tree.expand_all = event.value


class ReAddTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.re_add.pane_id, title=BtnLabel.re_add)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(store.re_add_ids)
            yield ViewSwitcher(store.re_add_ids)
        yield SwitchSlider(app_ids=store.re_add_ids)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        managed_tree = self.query_one(store.re_add_ids.managed_tree_q, ManagedTree)

        if event.switch.id == store.re_add_ids.switch.show_unchanged:
            managed_tree.show_unchanged = event.value
        elif event.switch.id == store.re_add_ids.switch.show_unmanaged:
            managed_tree.show_unmanaged = event.value
        elif event.switch.id == store.re_add_ids.switch.expand_all:
            managed_tree.expand_all = event.value


class LogsTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.logs.pane_id, title=BtnLabel.logs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TabButtons(
                app_ids=store.logs_ids, labels=(BtnLabel.cmd_log, BtnLabel.app_log)
            )
            with ContentSwitcher(initial=store.logs_ids.container.cmd_log):
                yield CmdLog()
                yield AppLog()

    @on(TabBtnMsg)
    def switch_content(self, msg: TabBtnMsg) -> None:
        msg.stop()
        switcher = self.query_exactly_one(ContentSwitcher)
        if msg.button.label == BtnLabel.app_log:
            switcher.current = store.logs_ids.richlog.app
        elif msg.button.label == BtnLabel.cmd_log:
            switcher.current = store.logs_ids.container.cmd_log


class ConfigTab(TabPane):
    class CatConfigStatic(Static): ...

    class PrettyIgnored(Pretty): ...

    class PrettyTemplateData(Pretty): ...

    def __init__(self) -> None:
        super().__init__(id=BtnLabel.config.pane_id, title=BtnLabel.config)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                app_ids=store.config_ids,
                labels=(
                    BtnLabel.doctor,
                    BtnLabel.cat_config,
                    BtnLabel.ignored,
                    BtnLabel.template_data,
                    BtnLabel.diagram,
                ),
            )
            with ContentSwitcher(initial=store.config_ids.container.doctor):
                yield Vertical(
                    MainSectionLabel(SectionLabel.doctor_output),
                    DoctorTable(),
                    id=store.config_ids.container.doctor,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.cat_config_output),
                    ConfigTab.CatConfigStatic("Loading..."),
                    id=store.config_ids.container.cat_config,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.ignored_output),
                    ScrollableContainer(ConfigTab.PrettyIgnored("Loading...")),
                    id=store.config_ids.container.ignored,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.template_data_output),
                    ScrollableContainer(ConfigTab.PrettyTemplateData("Loading...")),
                    id=store.config_ids.container.template_data,
                )
                yield Vertical(
                    MainSectionLabel(SectionLabel.diagram),
                    Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram),
                    id=store.config_ids.container.diagram,
                )

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.label == BtnLabel.doctor:
            switcher.current = store.config_ids.container.doctor
        elif event.button.label == BtnLabel.cat_config:
            switcher.current = store.config_ids.container.cat_config
        elif event.button.label == BtnLabel.ignored:
            switcher.current = store.config_ids.container.ignored
        elif event.button.label == BtnLabel.template_data:
            switcher.current = store.config_ids.container.template_data
        elif event.button.label == BtnLabel.diagram:
            switcher.current = store.config_ids.container.diagram
