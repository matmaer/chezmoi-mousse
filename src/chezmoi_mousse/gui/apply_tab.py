from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Switch

from chezmoi_mousse import CMD, IDS, AppType, SwitchEnum, TabLabel

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.git_log import GitLogView
from .common.messages import CurrentApplyNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher

__all__ = ["ApplyTab"]


class ApplyTab(Container, AppType):

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield Vertical(ViewSwitcher(IDS.apply), OperateButtons(IDS.apply))
        yield SwitchSlider(IDS.apply)

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(ViewSwitcher).query_exactly_one(
            Horizontal
        )
        self.contents_view = self.query_one(
            IDS.apply.container.contents_q, ContentsView
        )
        self.git_log_view = self.query_one(IDS.apply.container.git_log_q, GitLogView)
        self.diff_view = self.query_one(IDS.apply.container.diff_q, DiffView)
        if CMD.cache.no_status_paths:
            self.app.call_later(self.toggle_unchanged)

    def toggle_unchanged(self) -> None:
        unchanged_switch = self.query_one(IDS.apply.switch.unchanged_q, Switch)
        unchanged_switch.toggle()

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.tab_buttons.border_subtitle = f" {msg.path.name} "
        self.git_log_view.show_path = msg.path
        self.diff_view.show_path = msg.path
        self.contents_view.show_path = msg.path
        # Set path_arg for the btn_enums in OperateMode
        operate_buttons = self.query_one(
            IDS.apply.container.operate_buttons_q, OperateButtons
        )
        operate_buttons.set_path_arg(msg.path)
        # disable forget and destroy buttons when in the dest_dir
        self.query_one(IDS.apply.op_btn.forget_review_q, Button).disabled = (
            msg.path == CMD.cache.dest_dir
        )
        self.query_one(IDS.apply.op_btn.destroy_review_q, Button).disabled = (
            msg.path == CMD.cache.dest_dir
        )
        # disable/enable apply review button
        self.query_one(IDS.apply.op_btn.apply_review_q, Button).disabled = bool(
            msg.path in CMD.cache.managed_file_paths
            and msg.path not in CMD.cache.status_paths
        )
        if (
            msg.path in CMD.cache.managed_dir_paths
            and msg.path not in CMD.cache.status_paths
        ):
            dir_node = CMD.cache.apply_dir_nodes[msg.path]
            self.query_one(IDS.apply.op_btn.apply_review_q, Button).disabled = (
                not dir_node.has_status_paths
            )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree_switcher = self.query_exactly_one(TreeSwitcher)
        if event.switch.id == IDS.apply.switch_id(switch=SwitchEnum.unchanged):
            tree_switcher.unchanged = event.value
        elif event.switch.id == IDS.apply.switch_id(switch=SwitchEnum.expand_all):
            tree_switcher.expand_all = event.value

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        expand_all_switch = self.query_one(IDS.apply.switch.expand_all_q, Switch)
        if event.button.label == TabLabel.tree:
            expand_all_switch.disabled = False
            expand_all_switch.tooltip = SwitchEnum.expand_all.enabled_tooltip
        elif event.button.label == TabLabel.list:
            expand_all_switch.disabled = True
            expand_all_switch.tooltip = SwitchEnum.expand_all.disabled_tooltip
