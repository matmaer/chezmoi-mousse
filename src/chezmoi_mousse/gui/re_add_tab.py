from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Switch

from chezmoi_mousse import CMD, IDS, AppType, OpBtnEnum, SwitchEnum, TabLabel

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.git_log import GitLogView
from .common.messages import CurrentReAddNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher

__all__ = ["ReAddTab"]


class ReAddTab(Container, AppType):

    def __init__(self) -> None:
        super().__init__()
        self.op_btn_dict = OpBtnEnum.op_btn_enum_dict(IDS.re_add)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TreeSwitcher(IDS.re_add)
            yield Vertical(
                ViewSwitcher(IDS.re_add),
                OperateButtons(IDS.re_add, btn_dict=self.op_btn_dict),
            )
        yield SwitchSlider(IDS.re_add)

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(ViewSwitcher).query_exactly_one(
            Horizontal
        )
        self.git_log_view = self.query_one(IDS.re_add.container.git_log_q, GitLogView)
        self.contents_view = self.query_one(
            IDS.re_add.container.contents_q, ContentsView
        )
        self.diff_view = self.query_one(IDS.re_add.container.diff_q, DiffView)
        if CMD.cache.no_status_paths:
            self.app.call_later(self.toggle_unchanged)

    def toggle_unchanged(self) -> None:
        unchanged_switch = self.query_one(IDS.re_add.switch.unchanged_q, Switch)
        unchanged_switch.toggle()

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(self, msg: CurrentReAddNodeMsg) -> None:
        msg.stop()
        self.tab_buttons.border_subtitle = f" {msg.path.name} "
        self.git_log_view.show_path = msg.path
        self.diff_view.show_path = msg.path
        self.contents_view.show_path = msg.path
        # Set path_arg for the btn_enums in OperateMode
        for btn_enum in self.op_btn_dict.values():
            if isinstance(btn_enum, OpBtnEnum):
                btn_enum.path_arg = msg.path
        # disable forget and destroy buttons when in the dest_dir
        self.query_one(IDS.re_add.op_btn.forget_review_q, Button).disabled = (
            msg.path == CMD.cache.dest_dir
        )
        self.query_one(IDS.re_add.op_btn.destroy_review_q, Button).disabled = (
            msg.path == CMD.cache.dest_dir
        )
        # disable/enable re_add review button
        self.query_one(IDS.re_add.op_btn.re_add_review_q, Button).disabled = bool(
            msg.path in CMD.cache.managed_file_paths
            and msg.path not in CMD.cache.status_paths
        )
        if (
            msg.path in CMD.cache.managed_dir_paths
            and msg.path not in CMD.cache.status_paths
        ):
            dir_node = CMD.cache.re_add_dir_nodes[msg.path]
            self.query_one(IDS.re_add.op_btn.re_add_review_q, Button).disabled = (
                not dir_node.has_status_paths
            )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree_switcher = self.query_exactly_one(TreeSwitcher)
        if event.switch.id == IDS.re_add.switch_id(switch=SwitchEnum.unchanged):
            tree_switcher.unchanged = event.value
        elif event.switch.id == IDS.re_add.switch_id(switch=SwitchEnum.expand_all):
            tree_switcher.expand_all = event.value

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        expand_all_switch = self.query_one(IDS.re_add.switch.expand_all_q, Switch)
        if event.button.label == TabLabel.tree:
            expand_all_switch.disabled = False
            expand_all_switch.tooltip = SwitchEnum.expand_all.enabled_tooltip
        elif event.button.label == TabLabel.list:
            expand_all_switch.disabled = True
            expand_all_switch.tooltip = SwitchEnum.expand_all.disabled_tooltip
