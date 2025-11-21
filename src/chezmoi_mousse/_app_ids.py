"""Contains classes to enable setting widget id's without hardcoded strings.

Easy access, autocomplete, type checking or to generated the id dynamically.
"""

from ._button_data import FlatBtn, LinkBtn, OperateBtn, TabBtn
from ._str_enums import (
    ContainerName,
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
        "canvas_name",
        "container",
        "data_table",
        "header_id",
        "footer_id",
        "view",
        "view_btn",
        "logger",
    )

    def __init__(self, canvas_name: TabName | ScreenName) -> None:
        self.canvas_name: str = canvas_name.name
        self.footer_id = f"{self.canvas_name}_footer"
        self.header_id = f"{self.canvas_name}_header"

        self.container = ContainerIds(self)
        self.data_table = DataTableIds(self)
        self.logger = LoggerIds(self)
        self.view = ViewIds(self)
        self.view_btn = ViewButtons(self)

    def button_id(
        self, qid: str = "", *, btn: FlatBtn | LinkBtn | OperateBtn | TabBtn
    ) -> str:
        if isinstance(btn, OperateBtn):
            suffix = "_op_btn"
            return f"{qid}{self.canvas_name}_{btn.name}{suffix}"
        elif isinstance(btn, TabBtn):
            suffix = "_tab_btn"
        elif isinstance(btn, FlatBtn):
            suffix = "_flat_btn"
        else:
            suffix = "_link_btn"
        return f"{qid}{self.canvas_name}_{btn.name}{suffix}"

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name}_{name.name}"

    def datatable_id(
        self, qid: str = "", *, data_table_name: DataTableName
    ) -> str:
        return f"{qid}{self.canvas_name}_{data_table_name.name}_datatable"

    def initial_header_id(self, qid: str = "", *, view_name: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view_name.name}_initial_header"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return (
            f"{qid}{self.canvas_name}_{switch.switch_name}_switch_horizontal"
        )

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name}_{switch.switch_name}_switch"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName | LogName) -> str:
        return f"{qid}{self.canvas_name}_{view}"


class ContainerIds:
    def __init__(self, canvas_ids: AppIds):
        self.canvas = canvas_ids.container_id(name=ContainerName.canvas)
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
        self.logs_switcher = canvas_ids.container_id(
            name=ContainerName.logs_switcher
        )
        self.logs_switcher_q = f"#{self.logs_switcher}"
        self.right_side = canvas_ids.container_id(
            name=ContainerName.right_side
        )
        self.right_side_q = f"#{self.right_side}"
        self.switch_slider = canvas_ids.container_id(
            name=ContainerName.switch_slider
        )
        self.switch_slider_q = f"#{self.switch_slider}"
        self.view_switcher = canvas_ids.container_id(
            name=ContainerName.view_switcher
        )
        self.view_switcher_q = f"#{self.view_switcher}"


class DataTableIds:
    """DataTable widget their id's."""

    def __init__(self, canvas_ids: AppIds):
        self.doctor = canvas_ids.datatable_id(
            data_table_name=DataTableName.doctor_table
        )
        self.doctor_q = f"#{self.doctor}"
        self.apply_git_log = canvas_ids.datatable_id(
            data_table_name=DataTableName.apply_git_log_table
        )
        self.apply_git_log_q = f"#{self.apply_git_log}"
        self.re_add_git_log = canvas_ids.datatable_id(
            data_table_name=DataTableName.re_add_git_log_table
        )
        self.re_add_git_log_q = f"#{self.re_add_git_log}"
        self.git_global_log = canvas_ids.datatable_id(
            data_table_name=DataTableName.git_global_log_table
        )
        self.git_global_log_q = f"#{self.git_global_log}"


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


class ViewButtons:
    """Buttons used by ContentSwitcher classes to switch views."""

    def __init__(self, canvas_ids: AppIds):
        # Logs tab
        self.app_log = canvas_ids.button_id(btn=TabBtn.app_log)
        self.debug_log = canvas_ids.button_id(btn=TabBtn.debug_log)
        self.operate_log = canvas_ids.button_id(btn=TabBtn.operate_log)
        self.read_log = canvas_ids.button_id(btn=TabBtn.read_log)

        # Help tab
        self.add_help = canvas_ids.button_id(btn=FlatBtn.add_help)
        self.apply_help = canvas_ids.button_id(btn=FlatBtn.apply_help)
        self.diagram = canvas_ids.button_id(btn=FlatBtn.diagram)
        self.re_add_help = canvas_ids.button_id(btn=FlatBtn.re_add_help)

        # Init screen
        self.clone_repo = canvas_ids.button_id(btn=FlatBtn.init_clone_repo)
        self.new_repo = canvas_ids.button_id(btn=FlatBtn.init_new_repo)

        # Shared across canvases
        self.cat_config = canvas_ids.button_id(btn=FlatBtn.cat_config)
        self.diff = canvas_ids.button_id(btn=TabBtn.diff)
        self.doctor = canvas_ids.button_id(btn=FlatBtn.doctor)
        self.ignored = canvas_ids.button_id(btn=FlatBtn.ignored)
        self.pw_mgr_info = canvas_ids.button_id(btn=FlatBtn.pw_mgr_info)
        self.template_data = canvas_ids.button_id(btn=FlatBtn.template_data)


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
