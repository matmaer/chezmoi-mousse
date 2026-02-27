from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Switch

from chezmoi_mousse import IDS, PARSED, AppType, OpBtnEnum, SubTabLabel, SwitchEnum

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.git_log import GitLog
from .common.messages import CurrentApplyNodeMsg
from .common.operate_mode import OperateMode
from .common.switchers import TreeSwitcher, ViewSwitcher

__all__ = ["ApplyTab"]


class ApplyTab(Container, AppType):

    def compose(self) -> ComposeResult:
        yield OperateMode(IDS.apply)
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield Vertical(
                ViewSwitcher(IDS.apply),
                OperateButtons(
                    IDS.apply, btn_dict=OpBtnEnum.op_btn_enum_dict(IDS.apply)
                ),
            )
        yield SwitchSlider(IDS.apply)

    def on_mount(self) -> None:
        self.operate_mode_container = self.query_one(
            IDS.apply.container.op_mode_q, OperateMode
        )
        self.contents_view = self.query_one(
            IDS.apply.container.contents_q, ContentsView
        )
        self.git_log_view = self.query_one(IDS.apply.container.git_log_q, GitLog)
        self.diff_view = self.query_one(IDS.apply.container.diff_q, DiffView)
        if PARSED.no_status_paths:
            self.app.call_later(self.toggle_unchanged)

    def toggle_unchanged(self) -> None:
        unchanged_switch = self.query_one(IDS.apply.switch.unchanged_q, Switch)
        unchanged_switch.toggle()
        managed_tree = self.query_one(IDS.apply.tree.managed_q)
        managed_tree.refresh()

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.git_log_view.show_path = msg.path
        self.operate_mode_container.path_arg = msg.path
        self.diff_view.show_path = msg.path
        self.contents_view.show_path = msg.path

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
        if event.button.label == SubTabLabel.tree:
            expand_all_switch.disabled = False
            expand_all_switch.tooltip = SwitchEnum.expand_all.enabled_tooltip
        elif event.button.label == SubTabLabel.list:
            expand_all_switch.disabled = True
            expand_all_switch.tooltip = SwitchEnum.expand_all.disabled_tooltip
