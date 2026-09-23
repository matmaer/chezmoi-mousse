from __future__ import annotations

from chezmoi_mousse.str_enums import (
    BtnLabel,
    ContainerName,
    LabelStr,
    RichLogName,
    TreeName,
)

__all__ = ["AppIds"]


class AppIds:
    def __init__(self, tab_label: BtnLabel) -> None:
        self.tab_label = tab_label
        self.container = _ContainerIds(self)
        self.op_btn = _OperateButtonIds(self)
        self.richlog = _RichLogIds(self)
        self.switch = _SwitchIds(self)
        self.tree = _TreeIds(self)
        self.switch_slider = f"{self.tab_label.name}_switch_slider"

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.tab_label.name}_{name.name}_id"

    def btn_id(self, qid: str = "", *, btn_label: BtnLabel) -> str:
        return f"{qid}{self.tab_label.name}_{btn_label.name}_btn_id"

    def switch_id(self, qid: str = "", *, switch_label: LabelStr) -> str:
        return f"{qid}{self.tab_label.name}_{switch_label.name}_switch_id"

    def richlog_id(self, qid: str = "", *, richlog: RichLogName) -> str:
        return f"{qid}{self.tab_label.name}_{richlog.name}_id"

    def tree_id(self, qid: str = "", *, tree_name: TreeName) -> str:
        return f"{qid}{self.tab_label.name}_{tree_name.name}_tree_id"


class _ContainerIds:
    def __init__(self, ids: AppIds) -> None:
        self.cat_config: str = ids.container_id(name=ContainerName.cat_config)
        self.cat_config_q: str = f"#{self.cat_config}"
        self.cmd_log: str = ids.container_id(name=ContainerName.cmd_log)
        self.cmd_log_q: str = f"#{self.cmd_log}"
        self.dump_config: str = ids.container_id(name=ContainerName.contents)
        self.dump_config_q: str = f"#{self.dump_config}"
        self.contents: str = ids.container_id(name=ContainerName.contents)
        self.contents_q: str = f"#{self.contents}"
        self.debug_log: str = ids.container_id(name=ContainerName.debug_log)
        self.debug_log_q: str = f"#{self.debug_log}"
        self.diagram: str = ids.container_id(name=ContainerName.diagram)
        self.diagram_q: str = f"#{self.diagram}"
        self.diff: str = ids.container_id(name=ContainerName.diff)
        self.diff_q: str = f"#{self.diff}"
        self.diff_reverse: str = ids.container_id(name=ContainerName.diff_reverse)
        self.diff_reverse_q: str = f"#{self.diff_reverse}"
        self.doctor: str = ids.container_id(name=ContainerName.doctor)
        self.doctor_q: str = f"#{self.doctor}"
        self.dom_nodes: str = ids.container_id(name=ContainerName.dom_nodes)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.flat_buttons: str = ids.container_id(name=ContainerName.flat_buttons)
        self.flat_buttons_q: str = f"#{self.flat_buttons}"
        self.git_log: str = ids.container_id(name=ContainerName.git_log)
        self.git_log_q: str = f"#{self.git_log}"
        self.ignored: str = ids.container_id(name=ContainerName.git_ignored)
        self.ignored_q: str = f"#{self.ignored}"
        self.left_side: str = ids.container_id(name=ContainerName.left_side)
        self.left_side_q: str = f"#{self.left_side}"
        self.middle: str = ids.container_id(name=ContainerName.middle)
        self.middle_q: str = f"#{self.middle}"
        self.env_vars: str = ids.container_id(name=ContainerName.env_vars)
        self.env_vars_q: str = f"#{self.env_vars}"
        self.operate_buttons: str = ids.container_id(name=ContainerName.operate_buttons)
        self.operate_buttons_q: str = f"#{self.operate_buttons}"
        self.right_side: str = ids.container_id(name=ContainerName.right_side)
        self.right_side_q: str = f"#{self.right_side}"
        self.template_data: str = ids.container_id(name=ContainerName.template_data)
        self.template_data_q: str = f"#{self.template_data}"
        self.test_paths_view: str = ids.container_id(name=ContainerName.test_paths_view)
        self.test_paths_view_q: str = f"#{self.test_paths_view}"


class _RichLogIds:
    def __init__(self, ids: AppIds) -> None:
        self.app: str = ids.richlog_id(richlog=RichLogName.app_logger)
        self.app_q: str = f"#{self.app}"
        self.debug: str = ids.richlog_id(richlog=RichLogName.debug_logger)
        self.debug_q: str = f"#{self.debug}"
        self.dom_nodes: str = ids.richlog_id(richlog=RichLogName.dom_node_logger)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.env_vars: str = ids.richlog_id(richlog=RichLogName.env_var_logger)
        self.env_vars_q: str = f"#{self.env_vars}"
        self.memory: str = ids.richlog_id(richlog=RichLogName.memory_usage_logger)
        self.memory_q: str = f"#{self.memory}"


class _OperateButtonIds:
    def __init__(self, ids: AppIds) -> None:
        self.add_review: str = ids.btn_id(btn_label=BtnLabel.add_review)
        self.add_review_q: str = f"#{self.add_review}"
        self.add_run: str = ids.btn_id(btn_label=BtnLabel.add_run)
        self.add_run_q: str = f"#{self.add_run}"

        self.apply_review: str = ids.btn_id(btn_label=BtnLabel.apply_review)
        self.apply_review_q: str = f"#{self.apply_review}"
        self.apply_run: str = ids.btn_id(btn_label=BtnLabel.apply_run)
        self.apply_run_q: str = f"#{self.apply_run}"

        self.destroy_review: str = ids.btn_id(btn_label=BtnLabel.destroy_review)
        self.destroy_review_q: str = f"#{self.destroy_review}"
        self.destroy_run: str = ids.btn_id(btn_label=BtnLabel.destroy_run)
        self.destroy_run_q: str = f"#{self.destroy_run}"

        self.exit_op_modal: str = ids.btn_id(btn_label=BtnLabel.cancel)
        self.exit_op_modal_q: str = f"#{self.exit_op_modal}"

        self.forget_review: str = ids.btn_id(btn_label=BtnLabel.forget_review)
        self.forget_review_q: str = f"#{self.forget_review}"
        self.forget_run: str = ids.btn_id(btn_label=BtnLabel.forget_run)
        self.forget_run_q: str = f"#{self.forget_run}"

        self.re_add_review: str = ids.btn_id(btn_label=BtnLabel.re_add_review)
        self.re_add_review_q: str = f"#{self.re_add_review}"
        self.re_add_run: str = ids.btn_id(btn_label=BtnLabel.re_add_run)
        self.re_add_run_q: str = f"#{self.re_add_run}"

        self.refresh_tree: str = ids.btn_id(btn_label=BtnLabel.refresh_trees)
        self.refresh_tree_q: str = f"#{self.refresh_tree}"

        self.reload: str = ids.btn_id(btn_label=BtnLabel.reload)
        self.reload_q: str = f"#{self.reload}"

        # for test_paths only
        self.create_paths: str = ids.btn_id(btn_label=BtnLabel.create_paths)
        self.create_paths_q: str = f"#{self.create_paths}"
        self.remove_paths: str = ids.btn_id(btn_label=BtnLabel.remove_paths)
        self.remove_paths_q: str = f"#{self.remove_paths}"
        self.list_test_paths: str = ids.btn_id(btn_label=BtnLabel.list_test_paths)
        self.list_test_paths_q: str = f"#{self.list_test_paths}"
        self.create_diffs: str = ids.btn_id(btn_label=BtnLabel.create_diffs)
        self.create_diffs_q: str = f"#{self.create_diffs}"
        self.log_memory: str = ids.btn_id(btn_label=BtnLabel.log_memory)
        self.log_memory_q: str = f"#{self.log_memory}"


class _SwitchIds:
    def __init__(self, ids: AppIds) -> None:

        # Apply and Re-Add tab
        self.show_unchanged: str = ids.switch_id(switch_label=LabelStr.show_unchanged)
        self.show_unchanged_q: str = f"#{self.show_unchanged}"

        self.show_unmanaged: str = ids.switch_id(switch_label=LabelStr.show_unmanaged)
        self.show_unmanaged_q: str = f"#{self.show_unmanaged}"

        self.expand_managed: str = ids.switch_id(switch_label=LabelStr.expand_managed)
        self.expand_managed_q: str = f"#{self.expand_managed}"

        self.show_unwanted: str = ids.switch_id(switch_label=LabelStr.show_unwanted)
        self.show_unwanted_q: str = f"#{self.show_unwanted}"


class _TreeIds:
    def __init__(self, ids: AppIds) -> None:

        self.status: str = ids.tree_id(tree_name=TreeName.status)
        self.status_q: str = f"#{self.status}"
        self.status_xpd: str = ids.tree_id(tree_name=TreeName.status_xpd)
        self.status_xpd_q: str = f"#{self.status_xpd}"

        self.managed: str = ids.tree_id(tree_name=TreeName.managed)
        self.managed_q: str = f"#{self.managed}"
        self.managed_xpd: str = ids.tree_id(tree_name=TreeName.managed_xpd)
        self.managed_xpd_q: str = f"#{self.managed_xpd}"

        self.un_managed: str = ids.tree_id(tree_name=TreeName.un_managed)
        self.un_managed_q: str = f"#{self.un_managed}"
        self.un_managed_xpd: str = ids.tree_id(tree_name=TreeName.un_managed_xpd)
        self.un_managed_xpd_q: str = f"#{self.un_managed_xpd}"

        self.un_wanted: str = ids.tree_id(tree_name=TreeName.un_wanted)
        self.un_wanted_q: str = f"#{self.un_wanted}"
        self.un_wanted_xpd: str = ids.tree_id(tree_name=TreeName.un_wanted_xpd)
        self.un_wanted_xpd_q: str = f"#{self.un_wanted_xpd}"
