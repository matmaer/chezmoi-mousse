from __future__ import annotations

from chezmoi_mousse.enum_data import SwitchEnum
from chezmoi_mousse.str_enums import (
    ContainerName,
    FlatBtnLabel,
    OpBtnLabel,
    RichLogName,
    TabLabel,
)

__all__ = ["AppIds"]


class AppIds:
    __slots__ = (
        "tab_label",
        "container",
        "managed_tree",
        "managed_tree_q",
        "op_btn",
        "richlog",
        "switch",
        "switch_slider",
        "switch_slider_q",
    )

    def __init__(self, tab_label: TabLabel) -> None:
        self.tab_label = tab_label
        self.container = ContainerIds(self)
        self.managed_tree = f"{self.tab_label.name}_managed_tree"
        self.managed_tree_q = f"#{self.managed_tree}"
        self.op_btn = OperateButtonIds(self)
        self.richlog = RichLogIds(self)
        self.switch = SwitchIds(self)
        self.switch_slider = f"{self.tab_label.name}_switch_slider"
        self.switch_slider_q = f"#{self.switch_slider}"

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.tab_label.name}_{name.name}"

    def flat_button_id(self, qid: str = "", *, btn: FlatBtnLabel) -> str:
        return f"{qid}{self.tab_label.name}_{btn.name}_flat_btn"

    def op_btn_id(self, qid: str = "", *, operation: OpBtnLabel) -> str:
        return f"{qid}{self.tab_label.name}_{operation.normalized_label}_op_btn"

    def switch_id(self, qid: str = "", *, switch: SwitchEnum) -> str:
        return f"{qid}{self.tab_label.name}_{switch.name}_switch"

    def richlog_id(self, qid: str = "", *, richlog: RichLogName) -> str:
        return f"{qid}{self.tab_label.name}_{richlog.name}"


class ContainerIds:
    def __init__(self, ids: AppIds) -> None:
        self.cat_config: str = ids.container_id(name=ContainerName.cat_config)
        self.cat_config_q: str = f"#{self.cat_config}"
        self.contents: str = ids.container_id(name=ContainerName.contents)
        self.contents_q: str = f"#{self.contents}"
        self.debug_log: str = ids.container_id(name=ContainerName.debug_log)
        self.debug_log_q: str = f"#{self.debug_log}"
        self.diagram: str = ids.container_id(name=ContainerName.diagram)
        self.diagram_q: str = f"#{self.diagram}"
        self.diff: str = ids.container_id(name=ContainerName.diff)
        self.diff_q: str = f"#{self.diff}"
        self.doctor: str = ids.container_id(name=ContainerName.doctor)
        self.doctor_q: str = f"#{self.doctor}"
        self.dom_nodes: str = ids.container_id(name=ContainerName.dom_nodes)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.git_log: str = ids.container_id(name=ContainerName.git_log)
        self.git_log_q: str = f"#{self.git_log}"
        self.ignored: str = ids.container_id(name=ContainerName.git_ignored)
        self.ignored_q: str = f"#{self.ignored}"
        self.left_side: str = ids.container_id(name=ContainerName.left_side)
        self.left_side_q: str = f"#{self.left_side}"
        self.memory_usage: str = ids.container_id(name=ContainerName.memory_usage)
        self.memory_usage_q: str = f"#{self.memory_usage}"
        self.operate_buttons: str = ids.container_id(name=ContainerName.operate_buttons)
        self.operate_buttons_q: str = f"#{self.operate_buttons}"
        self.pw_mgr_info: str = ids.container_id(name=ContainerName.pw_mgr_info)
        self.pw_mgr_info_q: str = f"#{self.pw_mgr_info}"
        self.right_side: str = ids.container_id(name=ContainerName.right_side)
        self.right_side_q: str = f"#{self.right_side}"
        self.template_data: str = ids.container_id(name=ContainerName.template_data)
        self.template_data_q: str = f"#{self.template_data}"
        self.test_paths_view: str = ids.container_id(name=ContainerName.test_paths_view)
        self.test_paths_view_q: str = f"#{self.test_paths_view}"


class RichLogIds:
    def __init__(self, ids: AppIds) -> None:
        self.app: str = ids.richlog_id(richlog=RichLogName.app_logger)
        self.app_q: str = f"#{self.app}"
        self.cmd: str = ids.richlog_id(richlog=RichLogName.cmd_logger)
        self.cmd_q: str = f"#{self.cmd}"
        self.debug: str = ids.richlog_id(richlog=RichLogName.debug_logger)
        self.debug_q: str = f"#{self.debug}"
        self.dom_nodes: str = ids.richlog_id(richlog=RichLogName.dom_node_logger)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.memory: str = ids.richlog_id(richlog=RichLogName.memory_usage_logger)
        self.memory_q: str = f"#{self.memory}"


class OperateButtonIds:
    def __init__(self, ids: AppIds) -> None:
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


class SwitchIds:
    def __init__(self, ids: AppIds) -> None:

        # Apply and Re-Add tab
        self.show_unchanged: str = ids.switch_id(switch=SwitchEnum.show_unchanged)
        self.show_unchanged_q: str = f"#{self.show_unchanged}"

        self.show_unmanaged: str = ids.switch_id(switch=SwitchEnum.show_unmanaged)
        self.show_unmanaged_q: str = f"#{self.show_unmanaged}"

        self.expand_all: str = ids.switch_id(switch=SwitchEnum.expand_all)
        self.expand_all_q: str = f"#{self.expand_all}"

        # Add tab
        self.show_managed: str = ids.switch_id(switch=SwitchEnum.show_managed)
        self.show_managed_q: str = f"#{self.show_managed}"

        self.show_unwanted: str = ids.switch_id(switch=SwitchEnum.show_unwanted)
        self.show_unwanted_q: str = f"#{self.show_unwanted}"
