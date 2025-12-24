from enum import StrEnum, auto

__all__ = ["Tcss"]


class Tcss(StrEnum):
    border_title_top = auto()
    changes_enabled_color = auto()
    content_switcher_left = auto()
    diff_line_added = auto()
    diff_line_changed_mode = auto()
    diff_line_context = auto()
    diff_line_removed = auto()
    doctor_table = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    guess_link = auto()
    input_field = auto()
    input_select = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    main_section_label = auto()
    operate_button = auto()
    operate_error = auto()
    operate_info = auto()
    operate_success = auto()
    pw_mgr_group = auto()
    read_cmd_static = auto()
    single_button_vertical = auto()
    single_switch = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_widget = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"
