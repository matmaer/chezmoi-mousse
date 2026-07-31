from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from textual import getters, on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import (
    Button,
    ContentSwitcher,
    DirectoryTree,
    Label,
    Pretty,
    RichLog,
    Static,
    Switch,
    TabPane,
)

from chezmoi_mousse.debug.test_paths import TestPaths
from chezmoi_mousse.enum_data import OpBtnEnum, OpBtnLabel
from chezmoi_mousse.str_enums import (
    ColorVar,
    FlatBtnLabel,
    SectionLabel,
    TabLabel,
    Tcss,
)

from .common.actionables import (
    FlatButtonsVertical,
    OpButton,
    OperateButtons,
    SwitchSlider,
    TabButtons,
)
from .common.contents import ContentsView
from .common.doctor_data import DoctorTable, PwMgrInfoView
from .common.filtered_dir_tree import FilteredDirTree
from .common.loggers import AppLog, CmdLog, DebugLog
from .common.managed_tree import DestDirTree, ManagedTree
from .common.switchers import ViewSwitcher

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui

__all__ = ["AddTab", "ApplyTab", "ConfigTab", "DebugTab", "LogsTab", "ReAddTab"]


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
                OpButton(
                    btn_enum=OpBtnEnum.refresh_tree,
                    btn_id=self.ids.op_btn.refresh_tree,
                    app_ids=self.ids,
                ),
                id=self.ids.container.left_side,
                classes=Tcss.tab_left_vertical,
            )
            with Vertical():
                yield ContentsView(self.ids)
                yield OperateButtons(self.ids)
        yield SwitchSlider(self.ids)

    def on_mount(self) -> None:
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.contents_view = self.query_one(self.ids.container.contents_q, ContentsView)
        self.contents_view.add_class(Tcss.add_tab_contents_view)
        self.contents_view.border_title = f" {self.app.cmattr.dest_dir} "
        self.contents_view.show_path = self.app.cmattr.dest_dir
        self.add_review_btn = self.query_one(self.ids.op_btn.add_review_q, OpButton)

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
        # Set path_arg for the btn_enums in OperateMode
        operate_buttons = self.query_one(
            self.ids.container.operate_buttons_q, OperateButtons
        )
        operate_buttons.set_path_arg(event.node.data.path)
        if isinstance(event, DirectoryTree.DirectorySelected):
            self.add_review_btn.disabled = True
        else:  # isinstance(event, DirectoryTree.FileSelected):
            self.add_review_btn.disabled = False

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
            yield Vertical(ViewSwitcher(self.ids), OperateButtons(self.ids))
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


class CatConfigView(Vertical):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    class CatConfigStatic(Static): ...

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.cat_config_output, classes=Tcss.main_section_label)
        yield self.CatConfigStatic("Loading...")

    def on_mount(self) -> None:
        static = self.query_exactly_one(self.CatConfigStatic)
        static.update(
            "\n".join(line for line in self.app.cmattr.cmd_results.cat_config.out_lines)
        )


class IgnoredView(Vertical):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:

        yield Label(SectionLabel.ignored_output, classes=Tcss.main_section_label)
        yield ScrollableContainer(Pretty("Loading..."))

    def on_mount(self) -> None:
        pretty_ignored: Pretty = self.query_exactly_one(Pretty)
        pretty_ignored.update(self.app.cmattr.cmd_results.ignored.out_lines)


class DiagramView(Vertical):

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.diagram, classes=Tcss.main_section_label)
        yield Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram)


class DoctorTableView(Vertical):

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.doctor_output, classes=Tcss.main_section_label)
        yield DoctorTable()


class TemplateDataView(Vertical):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.template_data_output, classes=Tcss.main_section_label)
        yield ScrollableContainer(Pretty("Updating..."))

    def on_mount(self) -> None:
        pretty_widget = self.query_exactly_one(Pretty)
        pretty_widget.update(self.app.cmattr.cmd_results.parsed_template_data)


class ConfigTab(TabPane):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

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
                yield DoctorTableView(id=self.ids.container.doctor)
                yield PwMgrInfoView(id=self.ids.container.pw_mgr_info)
                yield CatConfigView(id=self.ids.container.cat_config)
                yield IgnoredView(id=self.ids.container.ignored)
                yield TemplateDataView(id=self.ids.container.template_data)
                yield DiagramView(id=self.ids.container.diagram)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)

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


FLOW_DIAGRAM = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │                   │                   │                   │
       │     Add Tab       │    autoCommit     │     git push      │
       │   Re-Add Tab      │──────────────────>│──────────────────>│
       │──────────────────>│                   │                   │
       │                   │                autopush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
       │     Apply Tab     │     chezmoi init & chezmoi git pull   │
       │<──────────────────│<──────────────────────────────────────│
       │                   │                   │                   │
       │     Diff View     │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │                   │
       │                   │                   │                   │
       │                   │    chezmoi init & chezmoi git pull    │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │        chezmoi init --one-shot & chezmoi init --apply     │
       │<──────────────────────────────────────────────────────────│
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────────────────┴───────┐    ┌──────┴───────┐
│ destination  │    │    target state / source state   │    │  git remote  │
└──────────────┘    └──────────────────────────────────┘    └──────────────┘
"""


class DebugTab(TabPane):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    class TestPathsView(Static): ...

    MiB = 1024 * 1024
    INTERVAL = 2

    _previous_rss: float = 0.0

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, ids: AppIds):
        super().__init__(id=TabLabel.debug, title=TabLabel.debug)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                self.ids,
                labels=(
                    FlatBtnLabel.test_paths,
                    FlatBtnLabel.debug_log,
                    FlatBtnLabel.dom_nodes,
                    FlatBtnLabel.memory_usage,
                ),
            )
            with ContentSwitcher(initial=self.ids.container.test_paths_view):
                yield Vertical(
                    Label(SectionLabel.test_paths, classes=Tcss.main_section_label),
                    DebugTab.TestPathsView(classes=Tcss.info),
                    id=self.ids.container.test_paths_view,
                )
                yield Vertical(
                    Label(SectionLabel.debug_log, classes=Tcss.main_section_label),
                    DebugLog(ids=self.ids),
                    id=self.ids.container.debug_log,
                )
                yield Vertical(
                    Label(SectionLabel.dom_nodes, classes=Tcss.main_section_label),
                    RichLog(
                        id=self.ids.richlog.dom_nodes, highlight=True, auto_scroll=False
                    ),
                    id=self.ids.container.dom_nodes,
                )
                yield Vertical(
                    Label(SectionLabel.memory_usage, classes=Tcss.main_section_label),
                    RichLog(id=self.ids.richlog.memory, markup=True),
                    id=self.ids.container.memory_usage,
                )
        yield OperateButtons(self.ids)

    def on_mount(self) -> None:
        self.test_paths = TestPaths()
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.test_paths_view = self.query_one(self.ids.container.test_paths_view_q)
        self.test_paths_static = self.query_exactly_one(DebugTab.TestPathsView)
        self.test_paths_static.update(self._list_existing_test_paths())
        self.dom_node_logger = self.query_one(self.ids.richlog.dom_nodes_q, RichLog)
        self.memory_logger = self.query_one(self.ids.richlog.memory_q, RichLog)
        self.mem_log_op_btn = self.query_one(self.ids.op_btn.log_memory_q, Button)
        self.list_test_paths_op_btn = self.query_one(
            self.ids.op_btn.list_test_paths_q, Button
        )
        self.create_diffs_op_btn = self.query_one(
            self.ids.op_btn.create_diffs_q, Button
        )
        self.create_paths_op_btn = self.query_one(
            self.ids.op_btn.create_paths_q, Button
        )
        self.remove_paths_op_btn = self.query_one(
            self.ids.op_btn.remove_paths_q, Button
        )
        self.test_paths_op_btns = [
            self.list_test_paths_op_btn,
            self.create_diffs_op_btn,
            self.create_paths_op_btn,
            self.remove_paths_op_btn,
        ]
        self.app.call_later(self._log_dom_nodes)

        import psutil

        self._process = psutil.Process()
        self.set_interval(self.INTERVAL, lambda: self._write_to_memory_log())

    def _list_existing_test_paths(self) -> str:
        path_lines = "\n".join(f"{self.test_paths.get_existing_test_paths()}")
        if path_lines:
            return path_lines
        else:
            return f"[${ColorVar.warning} bold]No test paths exist.[/]"

    def _write_to_memory_log(self, auto: bool = True) -> None:
        mem_info = self._process.memory_info()
        time = f"[green]{datetime.now().strftime('%H:%M:%S')}[/]"
        rss = mem_info.rss / self.MiB
        vms = mem_info.vms / self.MiB
        pc2_increase = rss > self._previous_rss * 1.02
        pc2_decrease = rss < self._previous_rss * 0.98
        pc2_change = pc2_increase or pc2_decrease
        self._previous_rss = rss
        now_prefix = "Current memory usage log:"
        pc2_prefix = "Auto log 2 percent delta:"
        color = (
            "[cyan bold]"
            if pc2_increase
            else "[green bold]" if pc2_decrease else "[yellow bold]"
        )
        rss_str = f"{color}{rss:3.0f}[/] MiB rss"
        vms_str = f"{color}{vms:4.0f}[/] MiB vms"
        prefix = pc2_prefix if auto else now_prefix
        if pc2_change and auto or not auto:
            self.memory_logger.write(f"{time} {prefix} {rss_str} | {vms_str}")

    def _log_dom_nodes(self) -> None:
        # App dom nodes
        app_nodes = list(self.app.walk_children())
        self.dom_node_logger.write(f"self.app DOMNode count: {len(app_nodes)}\n")
        app_nodes_with_id = [item for item in app_nodes if item.id is not None]
        app_nodes_without_id = [item for item in app_nodes if item.id is None]
        self.dom_node_logger.write(f"DOMNodes with id: {len(app_nodes_with_id)}")
        for item in sorted(app_nodes_with_id, key=str):
            self.dom_node_logger.write(f"{item}")
        self.dom_node_logger.write(
            f"\nDOMNodes without id: {len(app_nodes_without_id)}"
        )
        for item in sorted(app_nodes_without_id, key=str):
            self.dom_node_logger.write(f"{item}")
        # Screen dom nodes
        screen_nodes = list(self.screen.walk_children())
        self.dom_node_logger.write(
            f"\nself.screen DOMNode count: {len(screen_nodes)}\n"
        )
        screen_nodes_with_id = [item for item in screen_nodes if item.id is not None]
        screen_nodes_without_id = [item for item in screen_nodes if item.id is None]
        self.dom_node_logger.write(f"DOMNodes with id: {len(screen_nodes_with_id)}")
        for item in sorted(screen_nodes_with_id, key=str):
            self.dom_node_logger.write(f"{item}")
        self.dom_node_logger.write(
            f"\nDOMNodes without id: {len(screen_nodes_without_id)}"
        )
        for item in sorted(screen_nodes_without_id, key=str):
            self.dom_node_logger.write(f"{item}")

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == FlatBtnLabel.memory_usage:
            self.mem_log_op_btn.display = True
            for btn in self.test_paths_op_btns:
                btn.display = False
            self.switcher.current = self.ids.container.memory_usage
        else:
            self.mem_log_op_btn.display = False
            for btn in self.test_paths_op_btns:
                btn.display = True
        if event.button.label == FlatBtnLabel.test_paths:
            self.switcher.current = self.test_paths_view.id
        elif event.button.label == FlatBtnLabel.debug_log:
            self.switcher.current = self.ids.container.debug_log
        elif event.button.label == FlatBtnLabel.dom_nodes:
            self.switcher.current = self.ids.container.dom_nodes

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OpBtnLabel.log_memory:
            self._write_to_memory_log(auto=False)
            return
        result: str | list[str] = ""
        if event.button.label == OpBtnLabel.list_test_paths:
            result = self._list_existing_test_paths()
            return
        if event.button.label == OpBtnLabel.create_diffs:
            result = self.test_paths.create_diffs()
        elif event.button.label == OpBtnLabel.create_paths:
            result = self.test_paths.create_paths_on_disk()
        elif event.button.label == OpBtnLabel.remove_paths:
            result = self.test_paths.remove_test_paths()
        # TODO: self.app.cmattr.update_attributes(ReadCmd.managed_status_commands())
        if isinstance(result, str):
            self.test_paths_static.update(result)
        else:
            self.test_paths_static.update("\n".join(result))


class LogsTab(TabPane):

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.logs, title=TabLabel.logs)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TabButtons(self.ids, (TabLabel.cmd_log, TabLabel.app_log))
            with ContentSwitcher(initial=self.ids.richlog.cmd):
                yield CmdLog()
                yield AppLog()

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(TabButtons)
        self.switcher = self.query_exactly_one(ContentSwitcher)

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == TabLabel.app_log:
            self.switcher.current = self.ids.richlog.app
        elif event.button.label == TabLabel.cmd_log:
            self.switcher.current = self.ids.richlog.cmd


class ReAddTab(TabPane):

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.re_add, title=TabLabel.re_add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(self.ids)
            yield Vertical(ViewSwitcher(self.ids), OperateButtons(self.ids))
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
