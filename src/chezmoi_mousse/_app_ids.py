from ._enum_data import OpBtnEnum, OpBtnLabel, SwitchEnum
from ._str_enum_names import ContainerName, LogName, ScreenName, StaticName, ViewName
from ._str_enums import FlatBtnLabel, TabLabel

__all__ = ["IDS", "AppIds"]


class AppIds:
    __slots__ = (
        "canvas_name",
        "container",
        "label",
        "logger",
        "managed_tree",
        "managed_tree_q",
        "op_btn",
        "static",
        "switch",
        "switch_slider",
        "switch_slider_q",
        "tree",
        "view",
    )

    def __init__(self, canvas_name: TabLabel | ScreenName) -> None:
        self.canvas_name = canvas_name
        self.container = ContainerIds(self)
        self.logger = LoggerIds(self)
        self.managed_tree = f"{self.canvas_name.name}_managed_tree"
        self.managed_tree_q = f"#{self.managed_tree}"
        self.op_btn = OperateButtonIds(self)
        self.static = StaticIds(self)
        self.switch = SwitchIds(self)
        self.switch_slider = f"{self.canvas_name.name}_switch_slider"
        self.switch_slider_q = f"#{self.switch_slider}"
        self.view = ViewIds(self)

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name.name}_{name.name}"

    def flat_button_id(self, qid: str = "", *, btn: FlatBtnLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_flat_btn"

    def op_btn_id(self, qid: str = "", *, operation: OpBtnLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{operation.normalized_label}_op_btn"

    def static_id(self, qid: str = "", *, static: StaticName) -> str:
        return f"{qid}{self.canvas_name.name}_{static.name}_static"

    def switch_id(self, qid: str = "", *, switch: SwitchEnum) -> str:
        return f"{qid}{self.canvas_name.name}_{switch.name}_switch"

    def view_id(self, qid: str = "", *, view: ViewName | LogName) -> str:
        return f"{qid}{self.canvas_name.name}_{view.name}"

    @property
    def op_btn_map(self) -> dict[str, "OpBtnEnum"]:
        if self.canvas_name == TabLabel.debug:
            return {
                self.op_btn.list_test_paths: OpBtnEnum.list_test_paths,
                self.op_btn.create_paths: OpBtnEnum.create_paths,
                self.op_btn.remove_paths: OpBtnEnum.remove_paths,
                self.op_btn.create_diffs: OpBtnEnum.create_diffs,
                self.op_btn.log_memory: OpBtnEnum.log_memory,
            }
        _common_buttons = {
            self.op_btn.cancel: OpBtnEnum.cancel,
            self.op_btn.reload: OpBtnEnum.reload,
        }
        if self.canvas_name == TabLabel.add:
            return {
                self.op_btn.add_review: OpBtnEnum.add_review,
                self.op_btn.add_run: OpBtnEnum.add_run,
                **_common_buttons,
            }
        _forget_destroy_buttons = {
            self.op_btn.destroy_review: OpBtnEnum.destroy_review,
            self.op_btn.destroy_run: OpBtnEnum.destroy_run,
            self.op_btn.forget_review: OpBtnEnum.forget_review,
            self.op_btn.forget_run: OpBtnEnum.forget_run,
        }
        if self.canvas_name == TabLabel.apply:
            return {
                self.op_btn.apply_review: OpBtnEnum.apply_review,
                self.op_btn.apply_run: OpBtnEnum.apply_run,
                **_forget_destroy_buttons,
                **_common_buttons,
            }
        elif self.canvas_name == TabLabel.re_add:
            return {
                self.op_btn.re_add_review: OpBtnEnum.re_add_review,
                self.op_btn.re_add_run: OpBtnEnum.re_add_run,
                **_forget_destroy_buttons,
                **_common_buttons,
            }
        else:
            raise ValueError(
                f"Unexpected canvas_name {self.canvas_name} for op_btn_map"
            )

    @property
    def run_btn_ids(self) -> set[str]:
        return {
            btn_id
            for btn_id, btn_enum in self.op_btn_map.items()
            if "Run" in btn_enum.label
        }

    @property
    def review_btn_ids(self) -> set[str]:
        return {
            btn_id
            for btn_id, btn_enum in self.op_btn_map.items()
            if "Review" in btn_enum.label
        }

    @property
    def review_btn_qids(self) -> set[str]:
        return {
            f"#{btn_id}"
            for btn_id, btn_enum in self.op_btn_map.items()
            if "Review" in btn_enum.label
        }

    @property
    def forget_destroy_review_btn_qids(self) -> set[str]:
        return {self.op_btn.forget_review_q, self.op_btn.destroy_review_q}


class ContainerIds:
    def __init__(self, ids: AppIds):
        self.contents: str = ids.container_id(name=ContainerName.contents)
        self.contents_q: str = f"#{self.contents}"
        self.command_output: str = ids.container_id(name=ContainerName.command_output)
        self.command_output_q: str = f"#{self.command_output}"
        self.diff: str = ids.container_id(name=ContainerName.diff)
        self.diff_q: str = f"#{self.diff}"
        self.doctor: str = ids.container_id(name=ContainerName.doctor)
        self.doctor_q: str = f"#{self.doctor}"
        self.git_log: str = ids.container_id(name=ContainerName.git_log)
        self.git_log_q: str = f"#{self.git_log}"
        self.left_side: str = ids.container_id(name=ContainerName.left_side)
        self.left_side_q: str = f"#{self.left_side}"
        self.operate_buttons: str = ids.container_id(name=ContainerName.operate_buttons)
        self.operate_buttons_q: str = f"#{self.operate_buttons}"
        self.op_feed_back: str = ids.container_id(name=ContainerName.op_feed_back)
        self.op_feed_back_q: str = f"#{self.op_feed_back}"
        self.repo_input: str = ids.container_id(name=ContainerName.repo_input)
        self.repo_input_q: str = f"#{self.repo_input}"
        self.right_side: str = ids.container_id(name=ContainerName.right_side)
        self.right_side_q: str = f"#{self.right_side}"


class LoggerIds:
    def __init__(self, ids: AppIds):
        self.app: str = ids.view_id(view=LogName.app_logger)
        self.app_q: str = f"#{self.app}"
        self.cmd: str = ids.view_id(view=LogName.cmd_logger)
        self.cmd_q: str = f"#{self.cmd}"
        self.debug: str = ids.view_id(view=LogName.debug_logger)
        self.debug_q: str = f"#{self.debug}"
        self.dom_nodes: str = ids.view_id(view=LogName.dom_node_logger)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.memory: str = ids.view_id(view=LogName.memory_usage_logger)
        self.memory_q: str = f"#{self.memory}"


class OperateButtonIds:
    def __init__(self, ids: AppIds):
        self.add_review: str = ids.op_btn_id(operation=OpBtnLabel.add_review)
        self.add_review_q: str = f"#{self.add_review}"
        self.add_run: str = ids.op_btn_id(operation=OpBtnLabel.add_run)
        self.add_run_q: str = f"#{self.add_run}"

        self.apply_review: str = ids.op_btn_id(operation=OpBtnLabel.apply_review)
        self.apply_review_q: str = f"#{self.apply_review}"
        self.apply_run: str = ids.op_btn_id(operation=OpBtnLabel.apply_run)
        self.apply_run_q: str = f"#{self.apply_run}"

        self.cancel: str = ids.op_btn_id(operation=OpBtnLabel.cancel)
        self.cancel_q: str = f"#{self.cancel}"

        self.destroy_review: str = ids.op_btn_id(operation=OpBtnLabel.destroy_review)
        self.destroy_review_q: str = f"#{self.destroy_review}"
        self.destroy_run: str = ids.op_btn_id(operation=OpBtnLabel.destroy_run)
        self.destroy_run_q: str = f"#{self.destroy_run}"

        self.forget_review: str = ids.op_btn_id(operation=OpBtnLabel.forget_review)
        self.forget_review_q: str = f"#{self.forget_review}"
        self.forget_run: str = ids.op_btn_id(operation=OpBtnLabel.forget_run)
        self.forget_run_q: str = f"#{self.forget_run}"

        self.re_add_review: str = ids.op_btn_id(operation=OpBtnLabel.re_add_review)
        self.re_add_review_q: str = f"#{self.re_add_review}"
        self.re_add_run: str = ids.op_btn_id(operation=OpBtnLabel.re_add_run)
        self.re_add_run_q: str = f"#{self.re_add_run}"

        self.refresh_tree: str = ids.op_btn_id(operation=OpBtnLabel.refresh_tree)
        self.refresh_tree_q: str = f"#{self.refresh_tree}"
        self.reload: str = ids.op_btn_id(operation=OpBtnLabel.reload)
        self.reload_q: str = f"#{self.reload}"

        # for test_paths only
        self.create_paths: str = ids.op_btn_id(operation=OpBtnLabel.create_paths)
        self.create_paths_q: str = f"#{self.create_paths}"
        self.remove_paths: str = ids.op_btn_id(operation=OpBtnLabel.remove_paths)
        self.remove_paths_q: str = f"#{self.remove_paths}"
        self.list_test_paths: str = ids.op_btn_id(operation=OpBtnLabel.list_test_paths)
        self.list_test_paths_q: str = f"#{self.list_test_paths}"
        self.create_diffs: str = ids.op_btn_id(operation=OpBtnLabel.create_diffs)
        self.create_diffs_q: str = f"#{self.create_diffs}"
        self.log_memory: str = ids.op_btn_id(operation=OpBtnLabel.log_memory)
        self.log_memory_q: str = f"#{self.log_memory}"


class StaticIds:
    def __init__(self, ids: AppIds):
        self.added_paths: str = ids.static_id(static=StaticName.added_paths)
        self.added_paths_q: str = f"#{self.added_paths}"
        self.removed_paths: str = ids.static_id(static=StaticName.removed_paths)
        self.removed_paths_q: str = f"#{self.removed_paths}"
        self.changed_status: str = ids.static_id(static=StaticName.changed_status)
        self.changed_status_q: str = f"#{self.changed_status}"
        self.debug_test_paths: str = ids.static_id(static=StaticName.debug_test_paths)
        self.debug_test_paths_q: str = f"#{self.debug_test_paths}"
        self.init_info: str = ids.static_id(static=StaticName.init_info)
        self.init_info_q: str = f"#{self.init_info}"
        self.operate_info: str = ids.static_id(static=StaticName.operate_info)
        self.operate_info_q: str = f"#{self.operate_info}"


class SwitchIds:
    def __init__(self, ids: AppIds):
        self.expand_all: str = ids.switch_id(switch=SwitchEnum.expand_all)
        self.expand_all_q: str = f"#{self.expand_all}"
        self.unchanged: str = ids.switch_id(switch=SwitchEnum.unchanged)
        self.unchanged_q: str = f"#{self.unchanged}"
        self.managed_dirs: str = ids.switch_id(switch=SwitchEnum.managed_dirs)
        self.managed_dirs_q: str = f"#{self.managed_dirs}"
        self.unwanted: str = ids.switch_id(switch=SwitchEnum.unwanted)
        self.unwanted_q: str = f"#{self.unwanted}"


class ViewIds:
    """View Container id's used by ContentSwitcher classes."""

    def __init__(self, ids: AppIds):

        self.diagram: str = ids.view_id(view=ViewName.diagram_view)
        self.diagram_q: str = f"#{self.diagram}"

        # Config tab
        self.cat_config: str = ids.view_id(view=ViewName.cat_config_view)
        self.cat_config_q: str = f"#{self.cat_config}"
        self.ignored: str = ids.view_id(view=ViewName.git_ignored_view)
        self.ignored_q: str = f"#{self.ignored}"

        # Debug tab
        self.debug_log: str = ids.view_id(view=ViewName.debug_log_view)
        self.debug_log_q: str = f"#{self.debug_log}"
        self.dom_nodes: str = ids.view_id(view=ViewName.dom_nodes_view)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.memory_usage: str = ids.view_id(view=ViewName.memory_usage_view)
        self.memory_usage_q: str = f"#{self.memory_usage}"
        self.test_paths: str = ids.view_id(view=ViewName.test_paths_view)
        self.test_paths_q: str = f"#{self.test_paths}"

        # Views or shared across canvases
        self.pw_mgr_info: str = ids.view_id(view=ViewName.pw_mgr_info_view)
        self.pw_mgr_info_q: str = f"#{self.pw_mgr_info}"
        self.template_data: str = ids.view_id(view=ViewName.template_data_view)
        self.template_data_q: str = f"#{self.template_data}"


class CanvasIds:
    def __init__(self) -> None:
        # Screens
        self.install_help = AppIds(ScreenName.install_help)
        self.splash = AppIds(ScreenName.splash)
        self.main = AppIds(ScreenName.main)
        # TabPanes
        self.add = AppIds(TabLabel.add)
        self.apply = AppIds(TabLabel.apply)
        self.config = AppIds(TabLabel.config)
        self.debug = AppIds(TabLabel.debug)
        self.logs = AppIds(TabLabel.logs)
        self.re_add = AppIds(TabLabel.re_add)


IDS = CanvasIds()
