from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static, Tabs

from chezmoi_mousse import (  # OperateData,
    IDS,
    AppType,
    CommandResult,
    NodeData,
    OpBtnLabels,
    OperateStrings,
    PathKind,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CurrentApplyNodeMsg,
    OperateButtonMsg,
    OperateButtons,
    ViewTabButtons,
)

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_container import TabVertical

__all__ = ["ApplyTab"]


class ApplyTab(TabVertical, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.apply)
        self.current_node: "NodeData | None" = None
        self.operate_result: "CommandResult | None" = None
        self.current_apply_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield Static(
            id=IDS.apply.static.operate_info, classes=Tcss.operate_info
        )
        yield Static(
            id=IDS.apply.static.operate_output, classes=Tcss.operate_output
        )
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield ViewSwitcher(ids=IDS.apply, diff_reverse=False)
        yield SwitchSlider(ids=IDS.apply)
        yield OperateButtons(ids=IDS.apply)

    def on_mount(self) -> None:
        self.apply_btn = self.query_one(
            IDS.apply.operate_btn.apply_path_q, Button
        )
        self.apply_btn.display = True
        self.forget_btn = self.query_one(
            IDS.apply.operate_btn.forget_path_q, Button
        )
        self.forget_btn.display = True
        self.destroy_btn = self.query_one(
            IDS.apply.operate_btn.destroy_path_q, Button
        )
        self.destroy_btn.display = True
        self.exit_btn = self.query_one(
            IDS.apply.operate_btn.operate_exit_q, Button
        )
        self.operate_info = self.query_one(
            IDS.apply.static.operate_info_q, Static
        )
        self.operate_info.display = False
        self.operate_output = self.query_one(
            IDS.apply.static.operate_output_q, Static
        )
        self.operate_output.display = False

    def run_operate_command(self) -> None:
        if self.current_node is None:
            return
        self.operate_result = self.app.chezmoi.perform(
            WriteCmd.apply,
            path_arg=self.current_node.path,
            changes_enabled=self.app.changes_enabled,
        )
        if self.operate_result.dry_run is True:
            self.exit_btn.label = OpBtnLabels.cancel
        elif self.operate_result.dry_run is False:
            self.exit_btn.label = OpBtnLabels.reload
        self.operate_output.update(self.operate_result.std_out)

    @on(CurrentApplyNodeMsg)
    def update_label_and_tooltip(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.current_apply_node = msg.node_data
        self.current_node = msg.node_data
        node_path = msg.node_data.path
        self.apply_btn.label = OpBtnLabels.apply_review
        if (
            node_path in self.app.chezmoi.status_dirs
            or node_path in self.app.chezmoi.apply_status_files
            or self.app.chezmoi.apply_status_files_in(node_path)
        ):
            self.apply_btn.disabled = False
        else:
            self.apply_btn.disabled = True
        self.update_other_buttons(msg.node_data)
        self.update_view_node_data(msg.node_data)

    def toggle_visibility(self) -> None:
        # Widgets shown by default
        main_tabs = self.screen.query_exactly_one(Tabs)
        main_tabs.display = False if main_tabs.display is True else True
        left_side = self.query_one(
            IDS.apply.container.left_side_q, TreeSwitcher
        )
        left_side.display = False if left_side.display is True else True
        view_switcher_buttons = self.screen.query_one(
            IDS.apply.switcher.view_buttons_q, ViewTabButtons
        )
        view_switcher_buttons.display = (
            False if view_switcher_buttons.display is True else True
        )
        # Widgets hidden by default
        self.operate_info.display = (
            True if self.operate_info.display is False else False
        )
        # Switch slider always hidden when operating
        switch_slider = self.query_one(
            IDS.apply.container.switch_slider_q, SwitchSlider
        )
        if switch_slider.has_class("-visible") is True:
            self.app.action_toggle_switch_slider

    @on(OperateButtonMsg)
    def handle_button_pressed(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        if msg.label == OpBtnLabels.apply_review:
            self.toggle_visibility()
            self.exit_btn.disabled = False
            self.exit_btn.display = True
            self.operate_output.display = True
            self.operate_info.display = True
            self.forget_btn.display = False
            self.destroy_btn.display = False
            self.apply_btn.label = OpBtnLabels.apply_run
            self.notify("Review chezmoi apply for file.")
            self.update_operate_info()
        elif msg.label == OpBtnLabels.apply_run:
            self.notify("Running command.")
            self.run_operate_command()
        elif msg.label == OpBtnLabels.cancel:
            self.toggle_visibility()

    def update_operate_info(self) -> None:
        if self.current_node is None:
            return
        lines_to_write: list[str] = []
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateStrings.changes_enabled)
        else:
            lines_to_write.append(OperateStrings.changes_disabled)
            lines_to_write.append(OperateStrings.apply_path)
            lines_to_write.append(OperateStrings.diff_color)
            self.operate_info.border_subtitle = OperateStrings.apply_subtitle
        self.operate_info.update("\n".join(lines_to_write))
        if self.current_node.path_kind == PathKind.DIR:
            self.operate_info.border_title = OpBtnLabels.apply_dir
        elif self.current_node.path_kind == PathKind.FILE:
            self.operate_info.border_title = OpBtnLabels.apply_file


# from textual import on
# from textual.app import ComposeResult
# from textual.containers import Horizontal
# from textual.widgets import Button

# from chezmoi_mousse import IDS, AppType, OpBtnLabels, OperateBtn, PathKind
# from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

# from .common.switch_slider import SwitchSlider
# from .common.switchers import TreeSwitcher, ViewSwitcher
# from .common.tabs_container import TabVertical

# __all__ = ["ApplyTab"]


# class ApplyTab(TabVertical, AppType):

#     def __init__(self) -> None:
#         super().__init__(ids=IDS.apply)

#     def compose(self) -> ComposeResult:
#         with Horizontal():
#             yield TreeSwitcher(IDS.apply)
#             yield ViewSwitcher(ids=IDS.apply, diff_reverse=False)
#         yield OperateButtons(ids=IDS.apply)
#         yield SwitchSlider(ids=IDS.apply)

#     def on_mount(self) -> None:
#         self.operate_buttons = self.query_one(
#             IDS.apply.container.operate_buttons_q, OperateButtons
#         )
#         self.operate_buttons.update_buttons(
#             (
#                 OperateBtn.apply_path,
#                 OperateBtn.forget_path,
#                 OperateBtn.destroy_path,
#             )
#         )
#         self.apply_btn = self.query_one(
#             IDS.apply.operate_btn.apply_path_q, Button
#         )

#     @on(CurrentApplyNodeMsg)
#     def update_apply_operate_buttons(self, msg: CurrentApplyNodeMsg) -> None:
#         self.apply_btn.disabled = True
#         node_path = msg.node_data.path
#         if msg.node_data.path_kind == PathKind.DIR:
#             self.apply_btn.label = OpBtnLabels.apply_dir
#             if (
#                 node_path in self.app.chezmoi.status_dirs
#                 or self.app.chezmoi.apply_status_files_in(node_path)
#             ):
#                 self.apply_btn.disabled = False
#                 self.apply_btn.tooltip = None
#         elif msg.node_data.path_kind == PathKind.FILE:
#             self.apply_btn.label = OpBtnLabels.apply_file
#             if node_path in self.app.chezmoi.apply_status_files:
#                 self.apply_btn.disabled = False
#                 self.apply_btn.tooltip = None
#         self.update_other_buttons(msg.node_data)
#         self.update_view_node_data(msg.node_data)


# from textual import on
# from textual.app import ComposeResult
# from textual.containers import Horizontal
# from textual.widgets import Button

# from chezmoi_mousse import IDS, AppType, OpBtnLabels, PathKind
# from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

# from .common.switch_slider import SwitchSlider
# from .common.switchers import TreeSwitcher, ViewSwitcher
# from .common.tabs_container import TabVertical

# __all__ = ["ApplyTab"]


# class ApplyTab(TabVertical, AppType):

#     def __init__(self) -> None:
#         super().__init__(ids=IDS.apply)

#     def compose(self) -> ComposeResult:
#         with Horizontal():
#             yield TreeSwitcher(IDS.apply)
#             yield ViewSwitcher(ids=IDS.apply, diff_reverse=False)
#         yield OperateButtons(ids=IDS.apply)
#         yield SwitchSlider(ids=IDS.apply)

#     def on_mount(self) -> None:
#         self.operate_buttons = self.query_one(
#             IDS.apply.container.operate_buttons_q, OperateButtons
#         )
#         self.apply_btn = self.query_one(
#             IDS.apply.operate_btn.apply_path_q, Button
#         )
#         self.apply_btn.display = True
#         self.forget_btn = self.query_one(
#             IDS.apply.operate_btn.forget_path_q, Button
#         )
#         self.forget_btn.display = True
#         self.destroy_btn = self.query_one(
#             IDS.apply.operate_btn.destroy_path_q, Button
#         )
#         self.destroy_btn.display = True
#         self.apply_btn = self.query_one(
#             IDS.apply.operate_btn.apply_path_q, Button
#         )

#     @on(CurrentApplyNodeMsg)
#     def update_apply_operate_buttons(self, msg: CurrentApplyNodeMsg) -> None:
#         self.apply_btn.disabled = True
#         node_path = msg.node_data.path
#         if msg.node_data.path_kind == PathKind.DIR:
#             self.apply_btn.label = OpBtnLabels.apply_dir
#             if (
#                 node_path in self.app.chezmoi.status_dirs
#                 or self.app.chezmoi.apply_status_files_in(node_path)
#             ):
#                 self.apply_btn.disabled = False
#                 self.apply_btn.tooltip = None
#         elif msg.node_data.path_kind == PathKind.FILE:
#             self.apply_btn.label = OpBtnLabels.apply_file
#             if node_path in self.app.chezmoi.apply_status_files:
#                 self.apply_btn.disabled = False
#                 self.apply_btn.tooltip = None
#         self.update_other_buttons(msg.node_data)
#         self.update_view_node_data(msg.node_data)
