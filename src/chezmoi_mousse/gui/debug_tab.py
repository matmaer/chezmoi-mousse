from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, ScrollableContainer
from textual.widgets import Button, ContentSwitcher, RichLog, Static

from chezmoi_mousse import IDS, AppType, FlatBtnLabel, OpBtnLabel, Tcss, TestPaths

from .common.actionables import FlatButtonsVertical
from .common.loggers import DebugLog

__all__ = ["DebugTab"]


class DebugTab(Horizontal, AppType):

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            IDS.debug,
            buttons=(
                FlatBtnLabel.test_paths,
                FlatBtnLabel.debug_log,
                FlatBtnLabel.dom_nodes,
            ),
        )
        with ContentSwitcher(initial=IDS.debug.view.test_paths):
            yield ScrollableContainer(
                Static(
                    "[$text-primary]No test paths exist.[/]",
                    id=IDS.debug.static.debug_test_paths,
                ),
                HorizontalGroup(
                    Button(classes=Tcss.operate_button, label=OpBtnLabel.create_paths),
                    Button(classes=Tcss.operate_button, label=OpBtnLabel.remove_paths),
                    Button(classes=Tcss.operate_button, label=OpBtnLabel.toggle_diffs),
                ),
                id=IDS.debug.view.test_paths,
                classes=Tcss.border_title_top,
            )
            yield DebugLog(IDS.debug)
            yield RichLog(
                id=IDS.debug.logger.dom_nodes,
                auto_scroll=False,
                highlight=True,
                classes=Tcss.border_title_top,
            )

    def on_mount(self) -> None:
        self.test_paths = TestPaths()
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        existing_paths = self.test_paths.list_existing_test_paths()
        if existing_paths:
            self.test_paths_static.update(existing_paths)
        self.debug_test_path_view = self.query_one(
            IDS.debug.view.test_paths_q, ScrollableContainer
        )
        self.debug_test_path_view.border_title = " Test Paths "
        self.dom_node_logger = self.query_one(IDS.debug.logger.dom_nodes_q, RichLog)
        self.dom_node_logger.border_title = " DOM Nodes "
        self.app.call_later(self.log_dom_nodes)

    def log_dom_nodes(self) -> None:
        dom_items = [
            item for item in self.app.walk_children(with_self=True, method="depth")
        ]
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
        switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.label == FlatBtnLabel.debug_log:
            switcher.current = IDS.debug.logger.debug
        elif event.button.label == FlatBtnLabel.test_paths:
            switcher.current = IDS.debug.view.test_paths
        elif event.button.label == FlatBtnLabel.dom_nodes:
            switcher.current = IDS.debug.logger.dom_nodes

    @on(Button.Pressed)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OpBtnLabel.toggle_diffs:
            result = self.test_paths.create_file_diffs()
            self.test_paths_static.update(result)
        elif event.button.label == OpBtnLabel.create_paths:
            result = self.test_paths.create_paths_on_disk()
            self.test_paths_static.update("\n".join(result))
        elif event.button.label == OpBtnLabel.remove_paths:
            result = self.test_paths.remove_test_paths()
            self.test_paths_static.update(result)
