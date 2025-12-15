"""Contains classes to enable setting widget id's without hardcoded strings.

Easy access, autocomplete, type checking or to generated the id dynamically.
"""

from ._operate_button_data import OperateBtn
from ._str_enum_names import (
    ContainerName,
    ContentSwitcherName,
    DataTableName,
    LogName,
    ScreenName,
    StaticName,
    TabName,
    TreeName,
    ViewName,
)
from ._str_enums import FlatBtn, LinkBtn, TabBtn
from ._switch_data import Switches

__all__ = ["AppIds", "IDS"]


class AppIds:
    __slots__ = (
        "canvas_name",
        "container",
        "datatable",
        "filter",
        "flat_btn",
        "footer",
        "header",
        "logger",
        "operate_btn",
        "static",
        "switcher",
        "tab_btn",
        "tree",
        "view",
    )

    def __init__(self, canvas_name: TabName | ScreenName) -> None:
        self.canvas_name = canvas_name
        self.footer = f"{self.canvas_name.name}_footer"
        self.header = f"{self.canvas_name.name}_header"

        self.container = ContainerIds(self)
        self.datatable = DataTableIds(self)
        self.filter = FilterIds(self)
        self.flat_btn = FlatButtonIds(self)
        self.logger = LoggerIds(self)
        self.operate_btn = OperateButtonIds(self)
        self.static = StaticIds(self)
        self.switcher = ContentSwitcherIds(self)
        self.tab_btn = TabButtonIds(self)
        self.tree = TreeIds(self)
        self.view = ViewIds(self)

    def operate_button_id(self, qid: str = "", *, btn: OperateBtn) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_op_btn"

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name.name}_{name.name}"

    def content_switcher_id(
        self, qid: str = "", *, switcher: ContentSwitcherName
    ) -> str:
        return f"{qid}{self.canvas_name.name}_{switcher.name}"

    def datatable_id(
        self, qid: str = "", *, datatable_name: DataTableName
    ) -> str:
        return f"{qid}{self.canvas_name.name}_{datatable_name.name}_datatable"

    def flat_button_id(self, qid: str = "", *, btn: FlatBtn) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_flat_btn"

    def link_button_id(self, qid: str = "", *, btn: LinkBtn) -> str:
        return f"{qid}{self.canvas_name.name}_{btn.name}_link_btn"

    def static_id(self, qid: str = "", *, static: StaticName) -> str:
        return f"{qid}{self.canvas_name.name}_{static.name}_static"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name.name}_{switch.name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name.name}_{switch.name}_switch"

    def tab_button_id(self, qid: str = "", *, btn: TabBtn) -> str:
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
        self.main = AppIds(ScreenName.main)
        self.operate_init = AppIds(ScreenName.operate_init)
        self.operate_chezmoi = AppIds(ScreenName.operate_chezmoi)
        # TabPanes
        self.add = AppIds(TabName.add)
        self.apply = AppIds(TabName.apply)
        self.config = AppIds(TabName.config)
        self.help = AppIds(TabName.help)
        self.logs = AppIds(TabName.logs)
        self.re_add = AppIds(TabName.re_add)


class ContainerIds:
    def __init__(self, ids: AppIds):
        self.contents = ids.container_id(name=ContainerName.contents)
        self.contents_q = f"#{self.contents}"
        self.dest_dir_info = ids.container_id(name=ContainerName.dest_dir_info)
        self.dest_dir_info_q = f"#{self.dest_dir_info}"
        self.doctor = ids.container_id(name=ContainerName.doctor)
        self.doctor_q = f"#{self.doctor}"
        self.diff = ids.container_id(name=ContainerName.diff)
        self.diff_q = f"#{self.diff}"
        self.git_log_path = ids.container_id(name=ContainerName.git_log_path)
        self.git_log_path_q = f"#{self.git_log_path}"
        self.git_log_global = ids.container_id(
            name=ContainerName.git_log_global
        )
        self.git_log_global_q = f"#{self.git_log_global}"
        self.left_side = ids.container_id(name=ContainerName.left_side)
        self.left_side_q = f"#{self.left_side}"
        self.operate_buttons = ids.container_id(
            name=ContainerName.operate_buttons
        )
        self.operate_buttons_q = f"#{self.operate_buttons}"
        self.post_operate = ids.container_id(name=ContainerName.post_operate)
        self.post_operate_q = f"#{self.post_operate}"
        self.pre_operate = ids.container_id(name=ContainerName.pre_operate)
        self.pre_operate_q = f"#{self.pre_operate}"
        self.repo_input = ids.container_id(name=ContainerName.repo_input)
        self.repo_input_q = f"#{self.repo_input}"
        self.right_side = ids.container_id(name=ContainerName.right_side)
        self.right_side_q = f"#{self.right_side}"
        self.switch_slider = ids.container_id(name=ContainerName.switch_slider)
        self.switch_slider_q = f"#{self.switch_slider}"


class ContentSwitcherIds:
    def __init__(self, ids: AppIds):
        self.ids = ids

        self.config_tab = ids.content_switcher_id(
            switcher=ContentSwitcherName.config_switcher
        )
        self.config_tab_q = f"#{self.config_tab}"

        self.help_tab = ids.content_switcher_id(
            switcher=ContentSwitcherName.help_switcher
        )
        self.help_tab_q = f"#{self.help_tab}"

        self.init_screen = ids.content_switcher_id(
            switcher=ContentSwitcherName.init_screen_switcher
        )
        self.init_screen_q = f"#{self.init_screen}"

        self.logs_tab = ids.content_switcher_id(
            switcher=ContentSwitcherName.logs_switcher
        )
        self.logs_tab_q = f"#{self.logs_tab}"
        self.logs_tab_buttons = ids.content_switcher_id(
            switcher=ContentSwitcherName.logs_tab_buttons
        )
        self.logs_tab_buttons_q = f"#{self.logs_tab_buttons}"

        self.apply_trees = ids.content_switcher_id(
            switcher=ContentSwitcherName.apply_tree_switcher
        )
        self.apply_trees_q = f"#{self.apply_trees}"
        self.apply_tree_buttons = ids.content_switcher_id(
            switcher=ContentSwitcherName.apply_tree_buttons
        )
        self.apply_tree_buttons_q = f"#{self.apply_tree_buttons}"

        self.re_add_trees = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_tree_switcher
        )
        self.re_add_trees_q = f"#{self.re_add_trees}"
        self.re_add_tree_buttons = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_tree_buttons
        )
        self.re_add_tree_buttons_q = f"#{self.re_add_tree_buttons}"

        self.apply_views = ids.content_switcher_id(
            switcher=ContentSwitcherName.apply_view_switcher
        )
        self.apply_views_q = f"#{self.apply_views}"
        self.apply_view_buttons = ids.content_switcher_id(
            switcher=ContentSwitcherName.apply_view_buttons
        )

        self.re_add_views = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_view_switcher
        )
        self.re_add_views_q = f"#{self.re_add_views}"
        self.re_add_view_buttons = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_view_buttons
        )
        self.re_add_view_buttons_q = f"#{self.re_add_view_buttons}"
        self.re_add_views_vertical = ids.content_switcher_id(
            switcher=ContentSwitcherName.re_add_views_vertical
        )
        self.re_add_views_vertical_q = f"#{self.re_add_views_vertical}"

    @property
    def tree_buttons(self) -> str:
        if self.ids.canvas_name == TabName.apply:
            return self.apply_tree_buttons
        elif self.ids.canvas_name == TabName.re_add:
            return self.re_add_tree_buttons
        else:
            raise ValueError(
                "ContentSwitcherIds.switcher_buttons accessed when not in Apply, ReAdd, or Logs tab"
            )

    @property
    def tree_buttons_q(self) -> str:
        return f"#{self.tree_buttons}"

    @property
    def view_buttons(self) -> str:
        if self.ids.canvas_name == TabName.apply:
            return self.apply_view_buttons
        elif self.ids.canvas_name == TabName.re_add:
            return self.re_add_view_buttons
        else:
            raise ValueError(
                "ContentSwitcherIds.switcher_buttons accessed when not in Apply, ReAdd, or Logs tab"
            )

    @property
    def view_buttons_q(self) -> str:
        return f"#{self.view_buttons}"

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

    @property
    def views(self) -> str:
        if self.ids.canvas_name == TabName.apply:
            return self.apply_views
        elif self.ids.canvas_name == TabName.re_add:
            return self.re_add_views
        else:
            raise ValueError(
                "ContentSwitcherIds.views accessed when not in Apply or ReAdd tab"
            )

    @property
    def views_q(self) -> str:
        return f"#{self.views}"


class DataTableIds:
    """DataTable widget their id's."""

    def __init__(self, ids: AppIds):
        self.doctor = ids.datatable_id(
            datatable_name=DataTableName.doctor_table
        )
        self.doctor_q = f"#{self.doctor}"
        self.git_log = ids.datatable_id(
            datatable_name=DataTableName.git_log_table
        )
        self.git_log_q = f"#{self.git_log}"


class FilterIds:
    def __init__(self, ids: AppIds):
        self.expand_all = ids.switch_id(switch=Switches.expand_all)
        self.expand_all_q = f"#{self.expand_all}"
        self.unchanged = ids.switch_id(switch=Switches.unchanged)
        self.unchanged_q = f"#{self.unchanged}"
        self.unmanaged_dirs = ids.switch_id(switch=Switches.unmanaged_dirs)
        self.unmanaged_dirs_q = f"#{self.unmanaged_dirs}"
        self.unwanted = ids.switch_id(switch=Switches.unwanted)
        self.unwanted_q = f"#{self.unwanted}"


class FlatButtonIds:
    def __init__(self, ids: AppIds):
        self.add_help = ids.flat_button_id(btn=FlatBtn.add_help)
        self.add_help_q = f"#{self.add_help}"
        self.apply_help = ids.flat_button_id(btn=FlatBtn.apply_help)
        self.apply_help_q = f"#{self.apply_help}"
        self.cat_config = ids.flat_button_id(btn=FlatBtn.cat_config)
        self.cat_config_q = f"#{self.cat_config}"
        self.diagram = ids.flat_button_id(btn=FlatBtn.diagram)
        self.diagram_q = f"#{self.diagram}"
        self.doctor = ids.flat_button_id(btn=FlatBtn.doctor)
        self.doctor_q = f"#{self.doctor}"
        self.exit_app = ids.flat_button_id(btn=FlatBtn.exit_app)
        self.exit_app_q = f"#{self.exit_app}"
        self.ignored = ids.flat_button_id(btn=FlatBtn.ignored)
        self.ignored_q = f"#{self.ignored}"
        self.pw_mgr_info = ids.flat_button_id(btn=FlatBtn.pw_mgr_info)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.re_add_help = ids.flat_button_id(btn=FlatBtn.re_add_help)
        self.re_add_help_q = f"#{self.re_add_help}"
        self.template_data = ids.flat_button_id(btn=FlatBtn.template_data)
        self.template_data_q = f"#{self.template_data}"


class LoggerIds:
    """RichLog widgets their id's."""

    def __init__(self, ids: AppIds):
        self.app = ids.view_id(view=LogName.app_logger)
        self.app_q = f"#{self.app}"
        self.contents = ids.view_id(view=LogName.contents_logger)
        self.contents_q = f"#{self.contents}"
        self.debug = ids.view_id(view=LogName.debug_logger)
        self.debug_q = f"#{self.debug}"
        self.diff = ids.view_id(view=LogName.diff_logger)
        self.diff_q = f"#{self.diff}"
        self.operate = ids.view_id(view=LogName.operate_logger)
        self.operate_q = f"#{self.operate}"
        self.read = ids.view_id(view=LogName.read_logger)
        self.read_q = f"#{self.read}"
        self.splash = ids.view_id(view=LogName.splash_logger)
        self.splash_q = f"#{self.splash}"


class OperateButtonIds:
    def __init__(self, ids: AppIds):
        self.add_dir = ids.operate_button_id(btn=OperateBtn.add_dir)
        self.add_dir_q = f"#{self.add_dir}"
        self.add_file = ids.operate_button_id(btn=OperateBtn.add_file)
        self.add_file_q = f"#{self.add_file}"
        self.apply_path = ids.operate_button_id(btn=OperateBtn.apply_path)
        self.apply_path_q = f"#{self.apply_path}"
        self.destroy_path = ids.operate_button_id(btn=OperateBtn.destroy_path)
        self.destroy_path_q = f"#{self.destroy_path}"
        self.forget_path = ids.operate_button_id(btn=OperateBtn.forget_path)
        self.forget_path_q = f"#{self.forget_path}"
        self.init_repo = ids.operate_button_id(btn=OperateBtn.init_repo)
        self.init_repo_q = f"#{self.init_repo}"
        self.operate_exit = ids.operate_button_id(btn=OperateBtn.operate_exit)
        self.operate_exit_q = f"#{self.operate_exit}"
        self.re_add_path = ids.operate_button_id(btn=OperateBtn.re_add_path)
        self.re_add_path_q = f"#{self.re_add_path}"


class StaticIds:
    def __init__(self, ids: AppIds):
        self.init_info = ids.static_id(static=StaticName.init_info)
        self.init_info_q = f"#{self.init_info}"
        self.operate_info = ids.static_id(static=StaticName.operate_info)
        self.operate_info_q = f"#{self.operate_info}"


class TabButtonIds:
    """Buttons used by ContentSwitcher classes to switch views."""

    def __init__(self, ids: AppIds):
        self.app_log = ids.tab_button_id(btn=TabBtn.app_log)
        self.contents = ids.tab_button_id(btn=TabBtn.contents)
        self.debug_log = ids.tab_button_id(btn=TabBtn.debug_log)
        self.diff = ids.tab_button_id(btn=TabBtn.diff)
        self.git_log = ids.tab_button_id(btn=TabBtn.git_log_path)
        self.git_log_global = ids.tab_button_id(btn=TabBtn.git_log_global)
        self.list = ids.tab_button_id(btn=TabBtn.list)
        self.operate_log = ids.tab_button_id(btn=TabBtn.operate_log)
        self.read_log = ids.tab_button_id(btn=TabBtn.read_log)
        self.tree = ids.tab_button_id(btn=TabBtn.tree)


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

        # Views or shared across canvases
        self.pw_mgr_info = ids.view_id(view=ViewName.pw_mgr_info_view)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.template_data = ids.view_id(view=ViewName.template_data_view)
        self.template_data_q = f"#{self.template_data}"


IDS = CanvasIds()
