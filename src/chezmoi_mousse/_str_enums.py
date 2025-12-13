"""Contains StrEnum classes without other dependencies."""

from enum import StrEnum, auto

from ._chezmoi import ReadCmd

__all__ = [
    "Chars",
    "DestDirStrings",
    "FlatBtn",
    "HeaderTitle",
    "LinkBtn",
    "LogText",
    "PathKind",
    "SectionLabels",
    "TabBtn",
    "Tcss",
]

#########################################
# StrEnum classes for buttons and links #
#########################################


class FlatBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    diagram = "Diagram"
    doctor = "Doctor"
    exit_app = "Exit App"
    ignored = "Ignored"
    pw_mgr_info = "Password Managers"
    re_add_help = "Re-Add Help"
    template_data = "Template Data"


class LinkBtn(StrEnum):
    chezmoi_add = "https://www.chezmoi.io/reference/commands/add/"
    chezmoi_apply = "https://www.chezmoi.io/reference/commands/apply/"
    chezmoi_destroy = "https://www.chezmoi.io/reference/commands/destroy/"
    chezmoi_forget = "https://www.chezmoi.io/reference/commands/forget/"
    chezmoi_guess = "chezmoi guess documentation: https://www.chezmoi.io/reference/commands/init/"
    chezmoi_install = "https://www.chezmoi.io/install/"
    chezmoi_re_add = "https://www.chezmoi.io/reference/commands/re-add/"

    @property
    def link_url(self) -> str:
        return self.value

    @property
    def link_text(self) -> str:
        return (
            self.value.replace("https://", "").replace("www.", "").rstrip("/")
        )


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    contents = "Contents"
    debug_log = "Debug"
    diff = "Diff"
    git_log_global = "Git"
    git_log_path = "Git-Log"
    list = "List"
    operate_log = "Operate"
    read_log = "Read"
    tree = "Tree"


#########################
# Other StrEnum classes #
#########################


class Chars(StrEnum):
    bullet = "\u2022"  # '\N{BULLET}'
    burger = "\u2261"  # '\N{IDENTICAL TO}'
    check_mark = "\u2714"  # '\N{HEAVY CHECK MARK}'
    down_triangle = "\u25be "  # '\N{BLACK DOWN-POINTING SMALL TRIANGLE}'DOWN-POINTING TRIANGLE}'
    # gear = "\u2699"  # '\N{GEAR}'
    left_arrow = (
        f"\u2190{'\u2014' * 3}"  # '\N{LEFTWARDS ARROW}', '\N{EM DASH}'
    )
    lower_3_8ths_block = "\u2583"  # "\N{LOWER THREE EIGHTHS BLOCK}"
    right_arrow = (
        f"{'\u2014' * 3}\u2192"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    )
    right_triangle = "\u25b8 "  # '\N{BLACK RIGHT-POINTING SMALL TRIANGLE}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'


class DestDirStrings(StrEnum):
    _cat_prefix = (
        "Click a file or directory in the tree to see the output from"
    )
    _diff_prefix = "Click a path to see the output from"
    _git_log_prefix = "Click a path in the tree to see the output from"
    cat = f'{_cat_prefix} [$success]"{ReadCmd.cat.pretty_cmd}"[/].'
    diff = f'{_diff_prefix} [$success]"{ReadCmd.diff.pretty_cmd}"[/].'
    diff_reverse = (
        f'{_diff_prefix} [$success]"{ReadCmd.diff_reverse.pretty_cmd}"[/].'
    )
    dir_info = "Click a directary to see if it's managed or unmanaged."
    git_log_msg = (
        f'{_git_log_prefix} [$success]"{ReadCmd.git_log.pretty_cmd}"[/].'
    )
    in_dest_dir = (
        "This is the destination directory (chezmoi [$success]destDir[/])"
    )
    read_file = (
        'Click a file to see the output from [$success]"Path.read()"[/].'
    )


class HeaderTitle(StrEnum):
    header_dry_run_mode = (
        " -  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  - "
    )
    header_live_mode = (
        " -  c h e z m o i  m o u s s e  --  l i v e  m o d e  - "
    )
    header_install_help = (
        " - c h e z m o i  m o u s s e  --  i n s t a l l  h e l p  - "
    )


class LogText(StrEnum):
    app_log_initialized = "Application log initialized"
    debug_log_initialized = "Debug log initialized"
    chezmoi_found = "Found chezmoi command"
    chezmoi_not_found = "chezmoi command not found"
    dev_mode_enabled = "Dev mode enabled"
    operate_log_initialized = "Operate log initialized"
    read_log_initialized = "Read command log initialized"


class PathKind(StrEnum):
    DIR = auto()
    FILE = auto()


class SectionLabels(StrEnum):
    cat_config_output = '"chezmoi cat-config" output'
    debug_log_output = "Debug Log Output"
    doctor_output = '"chezmoi doctor" output'
    ignored_output = '"chezmoi ignored" output'
    init_repo = "Initialize chezmoi repository"
    operate_output = "Operate Command Output"
    password_managers = "Password Manager Information"
    path_info = "Path Information"
    project_description = "Project Description"
    project_link = "Project Link"
    template_data_output = '"chezmoi data" output'


class Tcss(StrEnum):
    border_title_top = auto()
    changes_enabled_color = auto()
    content_switcher_left = auto()
    doctor_table = auto()
    flat_button = auto()
    flat_link = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    input_field = auto()
    input_select = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    main_section_label = auto()
    operate_button = auto()
    pw_mgr_group = auto()
    read_cmd_static = auto()
    single_button_vertical = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_widget = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"
