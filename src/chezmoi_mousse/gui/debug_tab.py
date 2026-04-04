from datetime import datetime
from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ContentSwitcher, Label, RichLog, Static

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    FlatBtnLabel,
    OpBtnLabel,
    SectionLabel,
    Tcss,
    TestPaths,
)

from .common.actionables import FlatButtonsVertical, OperateButtons
from .common.loggers import DebugLog

__all__ = ["DebugTab"]


class TestPathColors(StrEnum):
    managed_dir = "[$text-accent bold]"
    status_dir = "[$text-warning bold]"
    unmanaged_dir = "[$text-primary bold]"
    managed_file = "[$text-accent]"
    status_file = "[$text-warning]"
    unmanaged_file = "[$text-primary]"
    unhandled = "[$text-error bold]"


class TestPathsView(Vertical):

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.test_paths, classes=Tcss.main_section_label)
        yield Static(id=IDS.debug.static.debug_test_paths)


class DebugLogView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.debug_log, classes=Tcss.main_section_label)
        yield DebugLog()


class DomNodesView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.dom_nodes, classes=Tcss.main_section_label)
        yield RichLog(id=IDS.debug.logger.dom_nodes, highlight=True, auto_scroll=False)


class MemoryUsageView(Vertical):
    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.memory_usage, classes=Tcss.main_section_label)
        yield RichLog(id=IDS.debug.logger.memory, markup=True)


class DebugTab(Horizontal, AppType):

    MiB = 1024 * 1024
    INTERVAL = 2

    def __init__(self) -> None:
        super().__init__()
        self._previous_rss: float = 0.0

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            IDS.debug,
            buttons=(
                FlatBtnLabel.test_paths,
                FlatBtnLabel.debug_log,
                FlatBtnLabel.dom_nodes,
                FlatBtnLabel.memory_usage,
            ),
        )
        with Vertical(), ContentSwitcher(initial=IDS.debug.view.test_paths):
            yield TestPathsView(id=IDS.debug.view.test_paths)
            yield DebugLogView(id=IDS.debug.view.debug_log)
            yield DomNodesView(id=IDS.debug.view.dom_nodes)
            yield MemoryUsageView(id=IDS.debug.view.memory_usage)
        yield OperateButtons(IDS.debug)

    def on_mount(self) -> None:
        self.test_paths = TestPaths()
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        self.test_paths_static.update(self._list_existing_test_paths())
        self.dom_node_logger = self.query_one(IDS.debug.logger.dom_nodes_q, RichLog)
        self.memory_logger = self.query_one(IDS.debug.logger.memory_q, RichLog)
        self.mem_log_op_btn = self.query_one(IDS.debug.op_btn.log_memory_q, Button)
        self.list_test_paths_op_btn = self.query_one(
            IDS.debug.op_btn.list_test_paths_q, Button
        )
        self.create_diffs_op_btn = self.query_one(
            IDS.debug.op_btn.create_diffs_q, Button
        )
        self.create_paths_op_btn = self.query_one(
            IDS.debug.op_btn.create_paths_q, Button
        )
        self.remove_paths_op_btn = self.query_one(
            IDS.debug.op_btn.remove_paths_q, Button
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
        colored_paths: list[str] = []
        for path in self.test_paths.get_existing_test_paths():
            if path in CMD.cache.sets.managed_dirs:
                if path not in CMD.cache.sets.status_dirs:
                    colored_paths.append(f"{TestPathColors.managed_dir}{path}[/]")
                elif path in CMD.cache.sets.status_dirs:
                    colored_paths.append(f"{TestPathColors.status_dir}{path}[/]")
            elif path in CMD.cache.sets.managed_files:
                if path not in CMD.cache.sets.status_files:
                    colored_paths.append(f"{TestPathColors.managed_file}{path}[/]")
                elif path in CMD.cache.sets.status_files:
                    colored_paths.append(f"{TestPathColors.status_file}{path}[/]")
            elif path.is_dir():
                colored_paths.append(f"{TestPathColors.unmanaged_dir}{path}[/]")
            elif path.is_file():
                colored_paths.append(f"{TestPathColors.unmanaged_file}{path}[/]")
            else:
                colored_paths.append(f"{TestPathColors.unhandled}{path}[/]")

        if colored_paths:
            colored_paths.extend(
                [
                    "\n[bold]Color legend:[/]",
                    f"{TestPathColors.managed_dir}Managed dir[/]",
                    f"{TestPathColors.status_dir}Status dir[/]",
                    f"{TestPathColors.unmanaged_dir}Unmanaged dir[/]",
                    f"{TestPathColors.managed_file}Managed file[/]",
                    f"{TestPathColors.status_file}Status file[/]",
                    f"{TestPathColors.unmanaged_file}Unmanaged file[/]",
                    f"{TestPathColors.unhandled}Unhandled condition[/]",
                    "\n",
                ]
            )
            return "\n".join(colored_paths)
        else:
            return "[$text-warning bold]No test paths exist.[/]"

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
            self.switcher.current = IDS.debug.view.memory_usage
        else:
            self.mem_log_op_btn.display = False
            for btn in self.test_paths_op_btns:
                btn.display = True
        if event.button.label == FlatBtnLabel.test_paths:
            self.switcher.current = IDS.debug.view.test_paths
        elif event.button.label == FlatBtnLabel.debug_log:
            self.switcher.current = IDS.debug.view.debug_log
        elif event.button.label == FlatBtnLabel.dom_nodes:
            self.switcher.current = IDS.debug.view.dom_nodes

    @on(Button.Pressed)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OpBtnLabel.list_test_paths:
            result = self._list_existing_test_paths()
            self.test_paths_static.update(result)
        elif event.button.label == OpBtnLabel.create_diffs:
            result = self.test_paths.create_diffs()
            CMD.cache.update_path_sets()
            self.test_paths_static.update(result)
        elif event.button.label == OpBtnLabel.create_paths:
            result = self.test_paths.create_paths_on_disk()
            CMD.cache.update_path_sets()
            self.test_paths_static.update("\n".join(result))
        elif event.button.label == OpBtnLabel.remove_paths:
            result = self.test_paths.remove_test_paths()
            CMD.cache.update_path_sets()
            self.test_paths_static.update("\n".join(result))
        elif event.button.label == OpBtnLabel.log_memory:
            self._write_to_memory_log(auto=False)
