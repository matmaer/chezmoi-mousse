from ._enum_data import SwitchEnum
from ._str_enum_names import (
    ContainerName,
    LabelName,
    LogName,
    ScreenName,
    StaticName,
    TabName,
    TreeName,
    ViewName,
)
from ._str_enums import FlatBtnLabel, OpBtnLabel, TabLabel

__all__ = ["IDS", "AppIds"]


class AppIds:
    __slots__ = (
        "canvas_name",
        "container",
        "label",
        "logger",
        "op_btn",
        "static",
        "switch",
        "tree",
        "view",
    )

    def __init__(self, canvas_name: TabName | ScreenName) -> None:
        self.canvas_name = canvas_name
        self.container = ContainerIds(self)
        self.label = LabelIds(self)
        self.logger = LoggerIds(self)
        self.op_btn = OperateButtonIds(self)
        self.static = StaticIds(self)
        self.switch = SwitchIds(self)
        self.tree = TreeIds(self)
        self.view = ViewIds(self)

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name.name}_{name.name}"

    def flat_button_id(self, qid: str = "", *, btn: FlatBtnLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_flat_btn"

    def label_id(self, qid: str = "", *, label: LabelName) -> str:
        return f"{qid}{self.canvas_name.name}_{label.name}_label"

    def operate_button_id(self, qid: str = "", *, operation: OpBtnLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{operation.normalized_label}_op_btn"

    def static_id(self, qid: str = "", *, static: StaticName) -> str:
        return f"{qid}{self.canvas_name.name}_{static.name}_static"

    def switch_id(self, qid: str = "", *, switch: SwitchEnum) -> str:
        return f"{qid}{self.canvas_name.name}_{switch.name}_switch"

    def tab_button_id(self, qid: str = "", *, btn: TabLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_tab_btn"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name.name}_{tree.name}"

    def view_id(self, qid: str = "", *, view: ViewName | LogName) -> str:
        return f"{qid}{self.canvas_name.name}_{view.name}"


class ContainerIds:
    def __init__(self, ids: AppIds):
        self.contents = ids.container_id(name=ContainerName.contents)
        self.contents_q = f"#{self.contents}"
        self.command_output = ids.container_id(name=ContainerName.command_output)
        self.command_output_q = f"#{self.command_output}"
        self.diff = ids.container_id(name=ContainerName.diff)
        self.diff_q = f"#{self.diff}"
        self.dir_contents = ids.container_id(name=ContainerName.dir_contents)
        self.dir_contents_q = f"#{self.dir_contents}"
        self.doctor = ids.container_id(name=ContainerName.doctor)
        self.doctor_q = f"#{self.doctor}"
        self.file_contents = ids.container_id(name=ContainerName.file_contents)
        self.file_contents_q = f"#{self.file_contents}"
        self.git_log = ids.container_id(name=ContainerName.git_log)
        self.git_log_q = f"#{self.git_log}"
        self.left_side = ids.container_id(name=ContainerName.left_side)
        self.left_side_q = f"#{self.left_side}"
        self.operate_buttons = ids.container_id(name=ContainerName.operate_buttons)
        self.operate_buttons_q = f"#{self.operate_buttons}"
        self.op_mode = ids.container_id(name=ContainerName.op_mode)
        self.op_mode_q = f"#{self.op_mode}"
        self.op_cmd_results = ids.container_id(name=ContainerName.op_cmd_results)
        self.op_cmd_results_q = f"#{self.op_cmd_results}"
        self.repo_input = ids.container_id(name=ContainerName.repo_input)
        self.repo_input_q = f"#{self.repo_input}"
        self.right_side = ids.container_id(name=ContainerName.right_side)
        self.right_side_q = f"#{self.right_side}"
        self.switch_slider = ids.container_id(name=ContainerName.switch_slider)
        self.switch_slider_q = f"#{self.switch_slider}"


class LabelIds:
    """Label widgets their id's to target for show/hide or update the text."""

    def __init__(self, ids: AppIds):
        self.cat_config_output = ids.label_id(label=LabelName.cat_config_output)
        self.cat_config_output_q = f"#{self.cat_config_output}"
        self.loading = ids.label_id(label=LabelName.loading)
        self.loading_q = f"#{self.loading}"


class LoggerIds:
    """RichLog widgets their id's."""

    def __init__(self, ids: AppIds):
        self.app = ids.view_id(view=LogName.app_logger)
        self.app_q = f"#{self.app}"
        self.cmd = ids.view_id(view=LogName.cmd_logger)
        self.cmd_q = f"#{self.cmd}"
        self.debug = ids.view_id(view=LogName.debug_logger)
        self.debug_q = f"#{self.debug}"
        self.dom_nodes = ids.view_id(view=LogName.dom_node_logger)
        self.dom_nodes_q = f"#{self.dom_nodes}"
        self.memory = ids.view_id(view=LogName.memory_usage_logger)
        self.memory_q = f"#{self.memory}"


class OperateButtonIds:
    def __init__(self, ids: AppIds):
        self.add_review = ids.operate_button_id(operation=OpBtnLabel.add_review)
        self.add_review_q = f"#{self.add_review}"
        self.add_run = ids.operate_button_id(operation=OpBtnLabel.add_run)
        self.add_run_q = f"#{self.add_run}"

        self.apply_review = ids.operate_button_id(operation=OpBtnLabel.apply_review)
        self.apply_review_q = f"#{self.apply_review}"
        self.apply_run = ids.operate_button_id(operation=OpBtnLabel.apply_run)
        self.apply_run_q = f"#{self.apply_run}"

        self.destroy_review = ids.operate_button_id(operation=OpBtnLabel.destroy_review)
        self.destroy_review_q = f"#{self.destroy_review}"
        self.destroy_run = ids.operate_button_id(operation=OpBtnLabel.destroy_run)
        self.destroy_run_q = f"#{self.destroy_run}"

        self.forget_review = ids.operate_button_id(operation=OpBtnLabel.forget_review)
        self.forget_review_q = f"#{self.forget_review}"
        self.forget_run = ids.operate_button_id(operation=OpBtnLabel.forget_run)
        self.forget_run_q = f"#{self.forget_run}"

        self.init_review = ids.operate_button_id(operation=OpBtnLabel.init_review)
        self.init_review_q = f"#{self.init_review}"
        self.init_run = ids.operate_button_id(operation=OpBtnLabel.init_run)
        self.init_run_q = f"#{self.init_run}"

        self.re_add_review = ids.operate_button_id(operation=OpBtnLabel.re_add_review)
        self.re_add_review_q = f"#{self.re_add_review}"
        self.re_add_run = ids.operate_button_id(operation=OpBtnLabel.re_add_run)
        self.re_add_run_q = f"#{self.re_add_run}"

        # Close button, can be either cancel, exit app or reload
        self.cancel = ids.operate_button_id(operation=OpBtnLabel.cancel)
        self.cancel_q = f"#{self.cancel}"
        self.reload = ids.operate_button_id(operation=OpBtnLabel.reload)
        self.reload_q = f"#{self.reload}"
        self.exit_app = ids.operate_button_id(operation=OpBtnLabel.exit_app)
        self.exit_app_q = f"#{self.exit_app}"

        # for test_paths only
        self.create_paths = ids.operate_button_id(operation=OpBtnLabel.create_paths)
        self.create_paths_q = f"#{self.create_paths}"
        self.remove_paths = ids.operate_button_id(operation=OpBtnLabel.remove_paths)
        self.remove_paths_q = f"#{self.remove_paths}"
        self.create_diffs = ids.operate_button_id(operation=OpBtnLabel.create_diffs)
        self.create_diffs_q = f"#{self.create_diffs}"
        self.log_memory = ids.operate_button_id(operation=OpBtnLabel.log_memory)
        self.log_memory_q = f"#{self.log_memory}"


class StaticIds:
    def __init__(self, ids: AppIds):
        self.contents_info = ids.static_id(static=StaticName.contents_info)
        self.contents_info_q = f"#{self.contents_info}"
        self.debug_test_paths = ids.static_id(static=StaticName.debug_test_paths)
        self.debug_test_paths_q = f"#{self.debug_test_paths}"
        self.diff_info = ids.static_id(static=StaticName.diff_info)
        self.diff_info_q = f"#{self.diff_info}"
        self.diff_lines = ids.static_id(static=StaticName.diff_lines)
        self.diff_lines_q = f"#{self.diff_lines}"
        self.git_log_info = ids.static_id(static=StaticName.git_log_info)
        self.git_log_info_q = f"#{self.git_log_info}"
        self.init_info = ids.static_id(static=StaticName.init_info)
        self.init_info_q = f"#{self.init_info}"
        self.operate_info = ids.static_id(static=StaticName.operate_info)
        self.operate_info_q = f"#{self.operate_info}"


class TreeIds:
    """Tree widget their id's."""

    def __init__(self, ids: AppIds):
        self.list = ids.tree_id(tree=TreeName.list_tree)
        self.list_q = f"#{self.list}"
        self.managed = ids.tree_id(tree=TreeName.managed_tree)
        self.managed_q = f"#{self.managed}"


class SwitchIds:
    def __init__(self, ids: AppIds):
        self.expand_all = ids.switch_id(switch=SwitchEnum.expand_all)
        self.expand_all_q = f"#{self.expand_all}"
        self.unchanged = ids.switch_id(switch=SwitchEnum.unchanged)
        self.unchanged_q = f"#{self.unchanged}"
        self.unmanaged_dirs = ids.switch_id(switch=SwitchEnum.unmanaged_dirs)
        self.unmanaged_dirs_q = f"#{self.unmanaged_dirs}"
        self.unwanted = ids.switch_id(switch=SwitchEnum.unwanted)
        self.unwanted_q = f"#{self.unwanted}"


class ViewIds:
    """View Container id's used by ContentSwitcher classes."""

    def __init__(self, ids: AppIds):

        # Help tab
        self.add_help = ids.view_id(view=ViewName.add_help_view)
        self.add_help_q = f"#{self.add_help}"
        self.apply_help = ids.view_id(view=ViewName.apply_help_view)
        self.apply_help_q = f"#{self.apply_help}"
        self.re_add_help = ids.view_id(view=ViewName.re_add_help_view)
        self.re_add_help_q = f"#{self.re_add_help}"
        self.diagram = ids.view_id(view=ViewName.diagram_view)
        self.diagram_q = f"#{self.diagram}"

        # Config tab
        self.cat_config = ids.view_id(view=ViewName.cat_config_view)
        self.cat_config_q = f"#{self.cat_config}"
        self.ignored = ids.view_id(view=ViewName.git_ignored_view)
        self.ignored_q = f"#{self.ignored}"

        # Views or shared across canvases
        self.pw_mgr_info = ids.view_id(view=ViewName.pw_mgr_info_view)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.template_data = ids.view_id(view=ViewName.template_data_view)
        self.template_data_q = f"#{self.template_data}"


class CanvasIds:
    def __init__(self) -> None:
        # Screens
        self.install_help = AppIds(ScreenName.install_help)
        self.splash = AppIds(ScreenName.splash)
        self.main_tabs = AppIds(ScreenName.main_tabs)
        self.init = AppIds(ScreenName.init)
        # TabPanes
        self.add = AppIds(TabName.add)
        self.apply = AppIds(TabName.apply)
        self.config = AppIds(TabName.config)
        self.debug = AppIds(TabName.debug)
        self.help = AppIds(TabName.help)
        self.logs = AppIds(TabName.logs)
        self.re_add = AppIds(TabName.re_add)


IDS = CanvasIds()
