from datetime import datetime

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ContentSwitcher, RichLog, Static

from chezmoi_mousse import (
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

    def __init__(self) -> None:
        self.op_btn_dict: dict[str, OpBtnLabel] = {
            IDS.debug.op_btn.create_paths: OpBtnLabel.create_paths,
            IDS.debug.op_btn.remove_paths: OpBtnLabel.remove_paths,
            IDS.debug.op_btn.create_diffs: OpBtnLabel.create_diffs,
            IDS.debug.op_btn.log_memory: OpBtnLabel.log_memory,
        }
        super().__init__()
        self._max_rss: float = 0.0
        self.MiB = 1024 * 1024

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(IDS.debug, buttons=self.FLAT_BTN_TUPLE)
        with Vertical():
            with ContentSwitcher(
                initial=IDS.debug.static.debug_test_paths,
                classes=Tcss.debug_content_switcher,
            ):
                yield Static(
                    "[$text-primary]No test paths exist.[/]",
                    id=IDS.debug.static.debug_test_paths,
                )
                yield DebugLog(IDS.debug)
                yield RichLog(id=IDS.debug.logger.dom_nodes, highlight=True)
                yield RichLog(id=IDS.debug.logger.memory, highlight=True)
            yield OperateButtons(IDS.debug, btn_dict=self.op_btn_dict)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.switcher.border_title = BorderTitle.test_paths
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        existing_paths = TEST_PATHS.list_existing_test_paths()
        if isinstance(existing_paths, str):
            self.test_paths_static.update(existing_paths)
        elif existing_paths:
            self.test_paths_static.update("\n".join([str(p) for p in existing_paths]))
        self.dom_node_logger = self.query_one(IDS.debug.logger.dom_nodes_q, RichLog)
        self.memory_logger = self.query_one(IDS.debug.logger.memory_q, RichLog)
        self.app.call_later(self._log_dom_nodes)

        import psutil

        self._process = psutil.Process()
        self.set_interval(5.0, self._auto_log_peak_memory)

    def _mem_log_msg(self, rss: float, vms: float) -> str:
        time = f"{datetime.now().strftime('%H:%M:%S')}"
        return f"{time} New MiB max: {rss:.0f} (RSS) | {vms:.0f} (VMS)"

    def _auto_log_peak_memory(self) -> None:
        mem_info = self._process.memory_info()
        rss = mem_info.rss / self.MiB
        if rss > self._max_rss * 1.02:
            self._max_rss = rss
            self.memory_logger.write(self._mem_log_msg(rss, mem_info.vms / self.MiB))

    def _log_memory_usage(self) -> None:
        mem_info = self._process.memory_info()
        rss = mem_info.rss / self.MiB
        self.memory_logger.write(self._mem_log_msg(rss, mem_info.vms / self.MiB))

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
        if event.button.label == FlatBtnLabel.debug_log:
            self.switcher.current = IDS.debug.logger.debug
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
            self.test_paths_static.update(result)
        elif event.button.label == OpBtnLabel.log_memory:
            self._log_memory_usage()
