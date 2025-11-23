"""Contains classes to enable setting widget id's without hardcoded strings.

Easy access, autocomplete, type checking or to generated the id dynamically.
"""

from ._button_data import FlatBtn, LinkBtn, OperateBtn, TabBtn
from ._str_enums import (
    ContainerName,
    ContentSwitcherName,
    DataTableName,
    LogName,
    ScreenName,
    TabName,
    TreeName,
    ViewName,
)
from ._switch_data import Switches

__all__ = ["AppIds"]


class AppIds:
    __slots__ = (
        "_canvas_name",
        "container",
        "datatable",
        "filter",
        "flat_btn",
        "footer",
        "header",
        "logger",
        "screen_name",
        "switcher",
        "tab_btn",
        "tab_name",
        "tree",
        "view",
    )

    def __init__(self, canvas_name: TabName | ScreenName) -> None:
        self._canvas_name: str = canvas_name.name
        self.tab_name: str = canvas_name.name
        self.screen_name: str = canvas_name.name
        self.footer = f"{self._canvas_name}_footer"
        self.header = f"{self._canvas_name}_header"

        self.container = ContainerIds(self)
        self.datatable = DataTableIds(self)
        self.filter = FilterIds(self)
        self.flat_btn = FlatButtonIds(self)
        self.logger = LoggerIds(self)
        self.switcher = ContentSwitcherIds(self)
        self.tree = TreeIds(self)
        self.view = ViewIds(self)
        self.tab_btn = TabButtonIds(self)

    def button_id(self, qid: str = "", *, btn: LinkBtn | OperateBtn) -> str:
        if isinstance(btn, OperateBtn):
            suffix = "_op_btn"
            return f"{qid}{self._canvas_name}_{btn.name}{suffix}"
        else:
            suffix = "_link_btn"
        return f"{qid}{self._canvas_name}_{btn.name}{suffix}"

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self._canvas_name}_{name.name}"

    def content_switcher_id(
        self, qid: str = "", *, switcher: ContentSwitcherName
    ) -> str:
        return f"{qid}{self._canvas_name}_{switcher.name}"

    def datatable_id(
        self, qid: str = "", *, datatable_name: DataTableName
    ) -> str:
        return f"{qid}{self._canvas_name}_{datatable_name.name}_datatable"

    def flat_button_id(self, qid: str = "", *, btn: FlatBtn) -> str:
        return f"{qid}{self._canvas_name}_{btn.name}_flat_btn"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return (
            f"{qid}{self._canvas_name}_{switch.switch_name}_switch_horizontal"
        )

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self._canvas_name}_{switch.switch_name}_switch"

    def tab_button_id(self, qid: str = "", *, btn: TabBtn) -> str:
        return f"{qid}{self._canvas_name}_{btn.name}_tab_btn"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self._canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName | LogName) -> str:
        return f"{qid}{self._canvas_name}_{view}"


class ContainerIds:
    def __init__(self, canvas_ids: AppIds):
        self.dest_dir_info = canvas_ids.container_id(
            name=ContainerName.dest_dir_info
        )
        self.dest_dir_info_q = f"#{self.dest_dir_info}"
        self.doctor = canvas_ids.container_id(name=ContainerName.doctor)
        self.doctor_q = f"#{self.doctor}"
        self.git_log_path = canvas_ids.container_id(
            name=ContainerName.git_log_path
        )
        self.git_log_path_q = f"#{self.git_log_path}"
        self.git_log_global = canvas_ids.container_id(
            name=ContainerName.git_log_global
        )
        self.git_log_global_q = f"#{self.git_log_global}"
        self.left_side = canvas_ids.container_id(name=ContainerName.left_side)
        self.left_side_q = f"#{self.left_side}"
        self.operate_buttons = canvas_ids.container_id(
            name=ContainerName.operate_buttons
        )
        self.operate_buttons_q = f"#{self.operate_buttons}"
        self.post_operate = canvas_ids.container_id(
            name=ContainerName.post_operate
        )
        self.post_operate_q = f"#{self.post_operate}"
        self.pre_operate = canvas_ids.container_id(
            name=ContainerName.pre_operate
        )
        self.pre_operate_q = f"#{self.pre_operate}"
        self.right_side = canvas_ids.container_id(
            name=ContainerName.right_side
        )
        self.right_side_q = f"#{self.right_side}"
        self.switch_slider = canvas_ids.container_id(
            name=ContainerName.switch_slider
        )
        self.switch_slider_q = f"#{self.switch_slider}"


class ContentSwitcherIds:
    def __init__(self, canvas_ids: AppIds):
        self.config_tab = canvas_ids.content_switcher_id(
            switcher=ContentSwitcherName.config_switcher
        )
        self.config_tab_q = f"#{self.config_tab}"
        self.help_tab = canvas_ids.content_switcher_id(
            switcher=ContentSwitcherName.help_switcher
        )
        self.help_tab_q = f"#{self.help_tab}"
        self.init_screen = canvas_ids.content_switcher_id(
            switcher=ContentSwitcherName.init_screen_switcher
        )
        self.init_screen_q = f"#{self.init_screen}"
        self.logs_tab = canvas_ids.content_switcher_id(
            switcher=ContentSwitcherName.logs_switcher
        )
        self.logs_tab_q = f"#{self.logs_tab}"
        self.trees = canvas_ids.content_switcher_id(
            switcher=ContentSwitcherName.tree_switcher
        )
        self.trees_q = f"#{self.trees}"
        self.views = canvas_ids.content_switcher_id(
            switcher=ContentSwitcherName.view_switcher
        )
        self.views_q = f"#{self.views}"


class DataTableIds:
    """DataTable widget their id's."""

    def __init__(self, canvas_ids: AppIds):
        self.doctor = canvas_ids.datatable_id(
            datatable_name=DataTableName.doctor_table
        )
        self.doctor_q = f"#{self.doctor}"
        self.git_log = canvas_ids.datatable_id(
            datatable_name=DataTableName.git_log_table
        )
        self.git_log_q = f"#{self.git_log}"


class FilterIds:
    def __init__(self, canvas_ids: AppIds):
        self.expand_all = canvas_ids.switch_id(switch=Switches.expand_all)
        self.expand_all_q = f"#{self.expand_all}"
        self.unchanged = canvas_ids.switch_id(switch=Switches.unchanged)
        self.unchanged_q = f"#{self.unchanged}"
        self.unmanaged_dirs = canvas_ids.switch_id(
            switch=Switches.unmanaged_dirs
        )
        self.unmanaged_dirs_q = f"#{self.unmanaged_dirs}"
        self.unwanted = canvas_ids.switch_id(switch=Switches.unwanted)
        self.unwanted_q = f"#{self.unwanted}"


class FlatButtonIds:
    def __init__(self, canvas_ids: AppIds):
        self.add_help = canvas_ids.flat_button_id(btn=FlatBtn.add_help)
        self.add_help_q = f"#{self.add_help}"
        self.apply_help = canvas_ids.flat_button_id(btn=FlatBtn.apply_help)
        self.apply_help_q = f"#{self.apply_help}"
        self.cat_config = canvas_ids.flat_button_id(btn=FlatBtn.cat_config)
        self.cat_config_q = f"#{self.cat_config}"
        self.clone_repo = canvas_ids.flat_button_id(btn=FlatBtn.clone_repo)
        self.clone_repo_q = f"#{self.clone_repo}"
        self.diagram = canvas_ids.flat_button_id(btn=FlatBtn.diagram)
        self.diagram_q = f"#{self.diagram}"
        self.doctor = canvas_ids.flat_button_id(btn=FlatBtn.doctor)
        self.doctor_q = f"#{self.doctor}"
        self.exit_app = canvas_ids.flat_button_id(btn=FlatBtn.exit_app)
        self.exit_app_q = f"#{self.exit_app}"
        self.ignored = canvas_ids.flat_button_id(btn=FlatBtn.ignored)
        self.ignored_q = f"#{self.ignored}"
        self.new_repo = canvas_ids.flat_button_id(btn=FlatBtn.new_repo)
        self.new_repo_q = f"#{self.new_repo}"
        self.pw_mgr_info = canvas_ids.flat_button_id(btn=FlatBtn.pw_mgr_info)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.re_add_help = canvas_ids.flat_button_id(btn=FlatBtn.re_add_help)
        self.re_add_help_q = f"#{self.re_add_help}"
        self.template_data = canvas_ids.flat_button_id(
            btn=FlatBtn.template_data
        )
        self.template_data_q = f"#{self.template_data}"


class LoggerIds:
    """RichLog widgets their id's."""

    def __init__(self, canvas_ids: AppIds):
        self.app = canvas_ids.view_id(view=LogName.app_logger)
        self.app_q = f"#{self.app}"
        self.contents = canvas_ids.view_id(view=LogName.contents_logger)
        self.contents_q = f"#{self.contents}"
        self.debug = canvas_ids.view_id(view=LogName.debug_logger)
        self.debug_q = f"#{self.debug}"
        self.diff = canvas_ids.view_id(view=LogName.diff_logger)
        self.diff_q = f"#{self.diff}"
        self.operate = canvas_ids.view_id(view=LogName.operate_logger)
        self.operate_q = f"#{self.operate}"
        self.read = canvas_ids.view_id(view=LogName.read_logger)
        self.read_q = f"#{self.read}"
        self.splash = canvas_ids.view_id(view=LogName.splash_logger)
        self.splash_q = f"#{self.splash}"


class TabButtonIds:
    """Buttons used by ContentSwitcher classes to switch views."""

    def __init__(self, canvas_ids: AppIds):
        self.app_log = canvas_ids.tab_button_id(btn=TabBtn.app_log)
        self.contents = canvas_ids.tab_button_id(btn=TabBtn.contents)
        self.debug_log = canvas_ids.tab_button_id(btn=TabBtn.debug_log)
        self.diff = canvas_ids.tab_button_id(btn=TabBtn.diff)
        self.git_log = canvas_ids.tab_button_id(btn=TabBtn.git_log_path)
        self.git_log_global = canvas_ids.tab_button_id(
            btn=TabBtn.git_log_global
        )
        self.list = canvas_ids.tab_button_id(btn=TabBtn.list)
        self.operate_log = canvas_ids.tab_button_id(btn=TabBtn.operate_log)
        self.read_log = canvas_ids.tab_button_id(btn=TabBtn.read_log)
        self.tree = canvas_ids.tab_button_id(btn=TabBtn.tree)


class TreeIds:
    """Tree widget their id's."""

    def __init__(self, canvas_ids: AppIds):
        self.dir_tree = canvas_ids.tree_id(tree=TreeName.dir_tree)
        self.dir_tree_q = f"#{self.dir_tree}"
        self.expanded = canvas_ids.tree_id(tree=TreeName.expanded_tree)
        self.expanded_q = f"#{self.expanded}"
        self.list = canvas_ids.tree_id(tree=TreeName.list_tree)
        self.list_q = f"#{self.list}"
        self.managed = canvas_ids.tree_id(tree=TreeName.managed_tree)
        self.managed_q = f"#{self.managed}"


class ViewIds:
    """View Container id's used by ContentSwitcher classes."""

    def __init__(self, canvas_ids: AppIds):

        # Help tab
        self.add_help = canvas_ids.view_id(view=ViewName.add_help_view)
        self.add_help_q = f"#{self.add_help}"
        self.apply_help = canvas_ids.view_id(view=ViewName.apply_help_view)
        self.apply_help_q = f"#{self.apply_help}"
        self.re_add_help = canvas_ids.view_id(view=ViewName.re_add_help_view)
        self.re_add_help_q = f"#{self.re_add_help}"
        self.diagram = canvas_ids.view_id(view=ViewName.diagram_view)
        self.diagram_q = f"#{self.diagram}"

        # Init screen
        self.clone_repo = canvas_ids.view_id(view=ViewName.init_clone_view)
        self.clone_repo_q = f"#{self.clone_repo}"
        self.new_repo = canvas_ids.view_id(view=ViewName.init_new_view)
        self.new_repo_q = f"#{self.new_repo}"

        # Config tab
        self.cat_config = canvas_ids.view_id(view=ViewName.cat_config_view)
        self.cat_config_q = f"#{self.cat_config}"
        self.ignored = canvas_ids.view_id(view=ViewName.git_ignored_view)
        self.ignored_q = f"#{self.ignored}"

        # Views or shared across canvases
        self.pw_mgr_info = canvas_ids.view_id(view=ViewName.pw_mgr_info_view)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.template_data = canvas_ids.view_id(
            view=ViewName.template_data_view
        )
        self.template_data_q = f"#{self.template_data}"
