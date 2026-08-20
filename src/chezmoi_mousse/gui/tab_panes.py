from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    ScrollableContainer,
    Vertical,
)
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
from chezmoi_mousse.enum_data import PwMgrEnum
from chezmoi_mousse.functions import ResultCollector
from chezmoi_mousse.named_tuples import PwMgrData
from chezmoi_mousse.str_enums import (
    ColorVar,
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
from .common.loggers import AppLog, CmdLog, DebugLog
from .common.managed_tree import DestDirTree, ManagedTree
from .common.switchers import ViewSwitcher

if TYPE_CHECKING:
    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

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
                RefreshBtn(self.ids),
                id=self.ids.container.left_side,
                classes=Tcss.tab_left_vertical,
            )
            with Vertical():
                yield ContentsView(self.ids)
                yield ReviewBtnGroup(self.ids)
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
        # Set path_arg
        review_op_buttons = self.query_one(
            self.ids.container.operate_buttons_q, ReviewBtnGroup
        )
        review_op_buttons.set_path_arg(event.node.data.path)
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
            yield Vertical(ViewSwitcher(self.ids), ReviewBtnGroup(self.ids))
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
        doctor_table.populate_table(ResultCollector.doctor_result.std_out.splitlines())

        self._populate_pw_mgr_info(ResultCollector.doctor_result.std_out.splitlines())

        cat_config_static = self.query_exactly_one(CatConfigStatic)
        cat_config_static.update(
            "\n".join(
                line
                for line in (ResultCollector.cat_config_result.std_out.splitlines())
            )
        )

        ignored_view = self.query_one(self.ids.container.ignored_q, Vertical)
        pretty_ignored = ignored_view.query_exactly_one(Pretty)
        pretty_ignored.update(ResultCollector.ignored_result.std_out.splitlines())

        template_data_view = self.query_one(
            self.ids.container.template_data_q, Vertical
        )
        template_data_pretty = template_data_view.query_exactly_one(Pretty)
        template_data_pretty.update(ResultCollector.parsed_template_data)

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


class DebugTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    class TestPathsView(Static): ...

    MiB = 1024 * 1024
    INTERVAL = 2

    _previous_rss: float = 0.0

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, ids: AppIds) -> None:
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
        with HorizontalGroup(
            id=self.ids.container.operate_buttons, classes=Tcss.op_btn_group
        ):
            yield Button(
                classes=Tcss.operate_button,
                id=self.ids.op_btn.log_memory,
                label=OpBtnLabel.log_memory,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=self.ids.op_btn.list_test_paths,
                label=OpBtnLabel.list_test_paths,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=self.ids.op_btn.create_diffs,
                label=OpBtnLabel.create_diffs,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=self.ids.op_btn.create_paths,
                label=OpBtnLabel.create_paths,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=self.ids.op_btn.remove_paths,
                label=OpBtnLabel.remove_paths,
            )

    def on_mount(self) -> None:
        self.test_paths = TestPaths()
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.test_paths_view = self.query_one(self.ids.container.test_paths_view_q)
        self.test_paths_static = self.query_exactly_one(DebugTab.TestPathsView)
        self.test_paths_static.update(self._list_existing_test_paths())
        self.dom_node_logger = self.query_one(self.ids.richlog.dom_nodes_q, RichLog)
        self.memory_logger = self.query_one(self.ids.richlog.memory_q, RichLog)
        self.mem_log_op_btn = self.query_one(self.ids.op_btn.log_memory_q, Button)
        self.mem_log_op_btn.display = False
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
        path_lines = "\n".join(
            str(p) for p in self.test_paths.get_existing_test_paths()
        )
        if path_lines:
            return path_lines
        else:
            return f"[${ColorVar.text_warning} bold]No test paths exist.[/]"

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
            else "[green bold]"
            if pc2_decrease
            else "[yellow bold]"
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
        if event.button.label == OpBtnLabel.log_memory.value:
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

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == TabLabel.app_log:
            self.switcher.current = self.app_ids.richlog.app
        elif event.button.label == TabLabel.cmd_log:
            self.switcher.current = self.app_ids.richlog.cmd


class ReAddTab(TabPane):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=TabLabel.re_add, title=TabLabel.re_add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(self.ids)
            yield Vertical(ViewSwitcher(self.ids), ReviewBtnGroup(self.ids))
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
