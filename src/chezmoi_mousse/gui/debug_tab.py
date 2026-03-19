from datetime import datetime

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ContentSwitcher, RichLog, Static

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    BorderTitle,
    FlatBtnLabel,
    OpBtnLabel,
    Tcss,
    TestPaths,
)

from .common.actionables import FlatButtonsVertical, OperateButtons
from .common.loggers import DebugLog

__all__ = ["DebugTab"]

TEST_PATHS = TestPaths()


class DebugTab(Horizontal, AppType):

    FLAT_BTN_TUPLE: tuple[FlatBtnLabel, ...] = (
        FlatBtnLabel.test_paths,
        FlatBtnLabel.debug_log,
        FlatBtnLabel.dom_nodes,
        FlatBtnLabel.memory_usage,
    )
    MiB = 1024 * 1024
    INTERVAL = 2

    def __init__(self) -> None:
        super().__init__()
        self._previous_rss: float = 0.0

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(IDS.debug, buttons=self.FLAT_BTN_TUPLE)
        with Vertical():
            with ContentSwitcher(
                initial=IDS.debug.static.debug_test_paths,
                classes=Tcss.debug_content_switcher,
            ):
                yield Static(id=IDS.debug.static.debug_test_paths)
                yield DebugLog()
                yield RichLog(
                    id=IDS.debug.logger.dom_nodes, highlight=True, auto_scroll=False
                )
                yield RichLog(id=IDS.debug.logger.memory, markup=True)
            yield OperateButtons(IDS.debug)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.switcher.border_title = BorderTitle.test_paths
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        self.dom_node_logger = self.query_one(IDS.debug.logger.dom_nodes_q, RichLog)
        self.memory_logger = self.query_one(IDS.debug.logger.memory_q, RichLog)
        self.app.call_later(self._log_dom_nodes)
        self._update_existing_test_paths()
        import psutil

        self._process = psutil.Process()
        self.set_interval(self.INTERVAL, lambda: self._write_to_memory_log())

    def _update_existing_test_paths(self) -> None:
        colored_paths: list[str] = []
        for path in TEST_PATHS.list_existing_test_paths():
            if path in CMD.cache.sets.managed_dirs:
                colored_paths.append(f"[$text-accent bold]{path}[/]")
            elif path in CMD.cache.sets.managed_files:
                colored_paths.append(f"[$text-accent]{path}[/]")
            else:
                colored_paths.append(f"[$text-disabled]{path}[/]")

        if colored_paths:
            self.test_paths_static.update(
                "[$text-primary bold]Existing test paths:[/]\n"
                + "\n".join(colored_paths)
            )
        else:
            self.test_paths_static.update("[$text-warning bold]No test paths exist.[/]")

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
        dom_items = list(self.app.walk_children(with_self=True, method="depth"))
        self.dom_node_logger.write(f"DOMNode count: {len(dom_items)}\n")
        nodes_with_id = [item for item in dom_items if item.id is not None]
        nodes_without_id = [item for item in dom_items if item.id is None]
        for item in sorted(nodes_with_id, key=str):
            self.dom_node_logger.write(f"{item}")
        for item in sorted(nodes_without_id, key=str):
            self.dom_node_logger.write(f"{item}")

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        self._update_existing_test_paths()
        if event.button.label == FlatBtnLabel.debug_log:
            self.switcher.current = IDS.logs.logger.debug
            self.switcher.border_title = BorderTitle.debug_log
        elif event.button.label == FlatBtnLabel.test_paths:
            self.switcher.current = IDS.debug.static.debug_test_paths
            self.switcher.border_title = BorderTitle.test_paths
        elif event.button.label == FlatBtnLabel.dom_nodes:
            self.switcher.current = IDS.debug.logger.dom_nodes
            self.switcher.border_title = BorderTitle.dom_nodes
        elif event.button.label == FlatBtnLabel.memory_usage:
            self.switcher.current = IDS.debug.logger.memory
            self.switcher.border_title = BorderTitle.memory_usage

    @on(Button.Pressed)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OpBtnLabel.create_diffs:
            result = TEST_PATHS.create_diffs()
            self.test_paths_static.update(result)
        elif event.button.label == OpBtnLabel.create_paths:
            result = TEST_PATHS.create_paths_on_disk()
            self.test_paths_static.update("\n".join(result))
        elif event.button.label == OpBtnLabel.remove_paths:
            result = TEST_PATHS.remove_test_paths()
            self.test_paths_static.update("\n".join(result))
        elif event.button.label == OpBtnLabel.log_memory:
            self._update_existing_test_paths()
            self._write_to_memory_log(auto=False)
