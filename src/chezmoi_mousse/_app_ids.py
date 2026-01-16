"""Contains the IDS singleton and  classes to enable setting widget id's without
hardcoded strings.

Provides easy access, autocomplete, type checking or to generate the id dynamically.
"""

from ._chezmoi_command import WriteVerb
from ._enum_data import SwitchEnum
from ._str_enum_names import (
    ContainerName,
    ContentSwitcherName,
    DataTableName,
    LabelName,
    LogName,
    ScreenName,
    StaticName,
    TabName,
    TreeName,
    ViewName,
)
from ._str_enums import FlatBtnLabel, LinkBtn, SubTabLabel

__all__ = ["AppIds", "IDS"]


class AppIds:
    __slots__ = (
        "canvas_name",
        "close_q",
        "close",
        "container",
        "datatable",
        "filter",
        "footer",
        "header",
        "label",
        "logger",
        "op_btn",
        "static",
        "switcher",
        "tab_id",
        "tree",
        "view",
    )

    def __init__(self, canvas_name: TabName | ScreenName) -> None:
        self.canvas_name = canvas_name
        self.footer = f"{self.canvas_name.name}_footer"
        self.header = f"{self.canvas_name.name}_header"
        self.tab_id = f"{self.canvas_name.name}_tab_container"
        self.close = f"{self.canvas_name.name}_close_btn"
        self.close_q = f"#{self.close}"

        self.container = ContainerIds(self)
        self.datatable = DataTableIds(self)
        self.filter = FilterIds(self)
        self.label = LabelIds(self)
        self.logger = LoggerIds(self)
        self.op_btn = OperateButtonIds(self)
        self.static = StaticIds(self)
        self.switcher = ContentSwitcherIds(self)
        self.tree = TreeIds(self)
        self.view = ViewIds(self)

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name.name}_{name.name}"

    def content_switcher_id(
        self, qid: str = "", *, switcher: ContentSwitcherName
    ) -> str:
        return f"{qid}{self.canvas_name.name}_{switcher.name}"

    def datatable_id(self, qid: str = "", *, datatable_name: DataTableName) -> str:
        return f"{qid}{self.canvas_name.name}_{datatable_name.name}_datatable"

    def flat_button_id(self, qid: str = "", *, btn: FlatBtnLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_flat_btn"

    def label_id(self, qid: str = "", *, label: LabelName) -> str:
        return f"{qid}{self.canvas_name.name}_{label.name}_label"

    def link_button_id(self, qid: str = "", *, btn: LinkBtn) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_link_btn"

    def operate_button_id(self, qid: str = "", *, write_verb: WriteVerb) -> str:
        return f"{qid}{self.canvas_name.name}_{write_verb.name}_op_btn"

    def static_id(self, qid: str = "", *, static: StaticName) -> str:
        return f"{qid}{self.canvas_name.name}_{static.name}_static"

    def switch_horizontal_id(self, qid: str = "", *, switch: SwitchEnum) -> str:
        return f"{qid}{self.canvas_name.name}_{switch.name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: SwitchEnum) -> str:
        return f"{qid}{self.canvas_name.name}_{switch.name}_switch"

    def tab_button_id(self, qid: str = "", *, btn: SubTabLabel) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_tab_btn"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name.name}_{tree.name}"

    def view_id(self, qid: str = "", *, view: ViewName | LogName) -> str:
        return f"{qid}{self.canvas_name.name}_{view.name}"


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


class ContainerIds:
    def __init__(self, ids: AppIds):
        self.contents = ids.container_id(name=ContainerName.contents)
        self.contents_q = f"#{self.contents}"
        self.command_output = ids.container_id(name=ContainerName.command_output)
        self.command_output_q = f"#{self.command_output}"
        self.diff = ids.container_id(name=ContainerName.diff)
        self.diff_q = f"#{self.diff}"
        self.doctor = ids.container_id(name=ContainerName.doctor)
        self.doctor_q = f"#{self.doctor}"
        self.git_log = ids.container_id(name=ContainerName.git_log)
        self.git_log_q = f"#{self.git_log}"
        self.left_side = ids.container_id(name=ContainerName.left_side)
        self.left_side_q = f"#{self.left_side}"
        self.operate_buttons = ids.container_id(name=ContainerName.operate_buttons)
        self.operate_buttons_q = f"#{self.operate_buttons}"
        self.op_mode = ids.container_id(name=ContainerName.op_mode)
        self.op_mode_q = f"#{self.op_mode}"
        self.op_result = ids.container_id(name=ContainerName.op_result)
        self.op_result_q = f"#{self.op_result}"
        self.op_review = ids.container_id(name=ContainerName.op_review)
        self.op_review_q = f"#{self.op_review}"
        self.repo_input = ids.container_id(name=ContainerName.repo_input)
        self.repo_input_q = f"#{self.repo_input}"
        self.right_side = ids.container_id(name=ContainerName.right_side)
        self.right_side_q = f"#{self.right_side}"
        self.switch_slider = ids.container_id(name=ContainerName.switch_slider)
        self.switch_slider_q = f"#{self.switch_slider}"


class ContentSwitcherIds:
    def __init__(self, ids: AppIds):
        self.ids = ids
        self.apply_trees = ids.content_switcher_id(
            switcher=ContentSwitcherName.apply_tree_switcher
        )
        self.apply_trees_q = f"#{self.apply_trees}"
        self.apply_views = ids.content_switcher_id(
            switcher=ContentSwitcherName.apply_view_switcher
        )
        self.apply_views_q = f"#{self.apply_views}"
        self.re_add_trees = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_tree_switcher
        )
        self.re_add_trees_q = f"#{self.re_add_trees}"
        self.re_add_views = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_view_switcher
        )
        self.re_add_views_q = f"#{self.re_add_views}"

    @property
    def trees(self) -> str:
        if self.ids.canvas_name == TabName.apply:
            return self.apply_trees
        elif self.ids.canvas_name == TabName.re_add:
            return self.re_add_trees
        else:
            raise ValueError(
                "ContentSwitcherIds.trees accessed when not in Apply or ReAdd tab"
            )

    @property
    def trees_q(self) -> str:
        return f"#{self.trees}"


class DataTableIds:
    def __init__(self, ids: AppIds):
        self.doctor = ids.datatable_id(datatable_name=DataTableName.doctor_table)
        self.doctor_q = f"#{self.doctor}"
        self.git_log = ids.datatable_id(datatable_name=DataTableName.git_log_table)
        self.git_log_q = f"#{self.git_log}"


class FilterIds:
    def __init__(self, ids: AppIds):
        self.expand_all = ids.switch_id(switch=SwitchEnum.expand_all)
        self.expand_all_q = f"#{self.expand_all}"
        self.unchanged = ids.switch_id(switch=SwitchEnum.unchanged)
        self.unchanged_q = f"#{self.unchanged}"
        self.unmanaged_dirs = ids.switch_id(switch=SwitchEnum.unmanaged_dirs)
        self.unmanaged_dirs_q = f"#{self.unmanaged_dirs}"
        self.unwanted = ids.switch_id(switch=SwitchEnum.unwanted)
        self.unwanted_q = f"#{self.unwanted}"


class LabelIds:
    """Label widgets their id's to target for show/hide or update the text."""

    def __init__(self, ids: AppIds):
        self.cat_config_output = ids.label_id(label=LabelName.cat_config_output)
        self.cat_config_output_q = f"#{self.cat_config_output}"
        self.contents_info = ids.label_id(label=LabelName.contents_info)
        self.contents_info_q = f"#{self.contents_info}"
        self.file_read_output = ids.label_id(label=LabelName.file_read_output)
        self.file_read_output_q = f"#{self.file_read_output}"


class LoggerIds:
    """RichLog widgets their id's."""

    def __init__(self, ids: AppIds):
        self.app = ids.view_id(view=LogName.app_logger)
        self.app_q = f"#{self.app}"
        self.cmd = ids.view_id(view=LogName.cmd_logger)
        self.cmd_q = f"#{self.cmd}"
        self.contents = ids.view_id(view=LogName.contents_logger)
        self.contents_q = f"#{self.contents}"
        self.debug = ids.view_id(view=LogName.debug_logger)
        self.debug_q = f"#{self.debug}"
        self.diff = ids.view_id(view=LogName.diff_logger)
        self.diff_q = f"#{self.diff}"
        self.dom_nodes = ids.view_id(view=LogName.dom_node_logger)
        self.dom_nodes_q = f"#{self.dom_nodes}"
        self.splash = ids.view_id(view=LogName.splash_logger)
        self.splash_q = f"#{self.splash}"


class OperateButtonIds:
    def __init__(self, ids: AppIds):
        self.add = ids.operate_button_id(write_verb=WriteVerb.add)
        self.add_q = f"#{self.add}"
        self.apply = ids.operate_button_id(write_verb=WriteVerb.apply)
        self.apply_q = f"#{self.apply}"
        self.destroy = ids.operate_button_id(write_verb=WriteVerb.destroy)
        self.destroy_q = f"#{self.destroy}"
        self.forget = ids.operate_button_id(write_verb=WriteVerb.forget)
        self.forget_q = f"#{self.forget}"
        self.init = ids.operate_button_id(write_verb=WriteVerb.init)
        self.init_q = f"#{self.init}"
        self.re_add = ids.operate_button_id(write_verb=WriteVerb.re_add)
        self.re_add_q = f"#{self.re_add}"


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
        self.op_review_info = ids.static_id(static=StaticName.op_review_info)
        self.op_review_info_q = f"#{self.op_review_info}"
        self.op_result_info = ids.static_id(static=StaticName.op_result_info)
        self.op_result_info_q = f"#{self.op_result_info}"


class TreeIds:
    """Tree widget their id's."""

    def __init__(self, ids: AppIds):
        self.dir_tree = ids.tree_id(tree=TreeName.dir_tree)
        self.dir_tree_q = f"#{self.dir_tree}"
        self.expanded = ids.tree_id(tree=TreeName.expanded_tree)
        self.expanded_q = f"#{self.expanded}"
        self.list = ids.tree_id(tree=TreeName.list_tree)
        self.list_q = f"#{self.list}"
        self.managed = ids.tree_id(tree=TreeName.managed_tree)
        self.managed_q = f"#{self.managed}"


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

        # Debug tab
        self.debug_log = ids.view_id(view=ViewName.debug_log_view)
        self.debug_log_q = f"#{self.debug_log}"
        self.test_paths = ids.view_id(view=ViewName.debug_test_paths_view)
        self.test_paths_q = f"#{self.test_paths}"

        # Views or shared across canvases
        self.pw_mgr_info = ids.view_id(view=ViewName.pw_mgr_info_view)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.template_data = ids.view_id(view=ViewName.template_data_view)
        self.template_data_q = f"#{self.template_data}"
        self.test_paths = ids.view_id(view=ViewName.debug_test_paths_view)
        self.test_paths_q = f"#{self.test_paths}"


IDS = CanvasIds()
