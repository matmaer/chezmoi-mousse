"""Contains only StrEnum classes or pure constants."""

from enum import StrEnum, auto

#######################################################################
# StrEnum classes used for id's, should be integrated in id_typing.py #
#######################################################################


class DoctorCollapsibles(StrEnum):
    pw_mgr_info = "supported password managers (link and description)"

    @property
    def qid(self) -> str:
        return f"#{self.name}"


class LogIds(StrEnum):
    init_log = auto()
    operate_log = auto()


########################
# Pure StrEnum classes #
########################


class Area(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class BorderTitle(StrEnum):
    # border_title = top border
    app_log = " App Log "
    debug_log = " Debug Log "
    init_log = " Init Log "
    operante_log = " Operate Log "
    output_log = " Commands With Raw Stdout "


class BorderSubTitle(StrEnum):
    esc_to_close = " escape key to close "
    double_click_esc_to_close = " double click or escape key to close "
    esc_to_exit_app = " escape key to exit app "


class Chars(StrEnum):
    add_file_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    apply_file_info_border = f"local \u2190{'\u2014' * 3} chezmoi"  # '\N{LEFTWARDS ARROW}', '\N{EM DASH}'
    bullet = "\u2022"  # '\N{BULLET}'
    burger = "\u2261"  # '\N{IDENTICAL TO}'
    check_mark = "\u2714"  # '\N{HEAVY CHECK MARK}'
    destroy_file_info_border = "\u274c destroy file \u274c"  # '\N{CROSS MARK}'
    forget_file_info_border = (
        "\u2716 forget file \u2716"  # '\N{HEAVY MULTIPLICATION X}'
    )
    # gear = "\u2699"  # '\N{GEAR}'
    lower_3_8ths_block = "\u2583"  # "\N{LOWER THREE EIGHTHS BLOCK}"
    re_add = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    re_add_file_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'


class IoVerbs(StrEnum):
    doctor = "doctor"
    dump_config = "dump-config"
    managed = "managed"
    status = "status"


class NavBtn(StrEnum):
    cat_config = "Cat Config"
    clone_repo = "Clone"
    diagram = "Diagram"
    ignored = "Ignored"
    new_repo = "New Repo"
    purge_repo = "Purge Repo"
    template_data = "Template Data"


class OperateBtn(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_file = "Apply File"
    clone_repo = "Clone Existing Repo"
    destroy_file = "Destroy File"
    forget_file = "Forget File"
    new_repo = "Initialize New Repo"
    operate_dismiss = "Cancel"
    purge_repo = "Purge Existing Repo"
    re_add_file = "Re-Add File"
    refresh_doctor_data = "Re-run 'chezmoi doctor' command (refresh data)"


class OperateVerbs(StrEnum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    purge = "purge"
    re_add = "re-add"


class ReadVerbs(StrEnum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
    diff = "diff"
    git = "git"
    ignored = "ignored"
    source_path = "source-path"


class ScreenName(StrEnum):
    install_help = auto()
    maximized = auto()
    operate = auto()


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    contents = "Contents"
    diff = "Diff"
    git_log = "Git-Log"
    list = "List"
    tree = "Tree"
    output_log = "Output"
    debug_log = "Debug"


class TabName(StrEnum):
    add_tab = auto()
    apply_tab = auto()
    config_tab = auto()
    doctor_tab = auto()
    init_tab = auto()
    log_tab = auto()
    re_add_tab = auto()


class TcssStr(StrEnum):
    border_title_top = auto()
    bottom_docked_log = auto()
    config_tab_label = auto()
    content_switcher_left = auto()
    content_switcher_right = auto()
    dir_tree_widget = auto()
    doctor_vertical = auto()
    doctor_vertical_group = auto()
    flow_diagram = auto()
    input_field = auto()
    input_field_vertical = auto()
    input_select = auto()
    input_select_vertical = auto()
    install_help = auto()
    internet_links = auto()
    last_clicked = auto()
    log_views = auto()
    navigate_button = auto()
    navigate_buttons_vertical = auto()
    operate_button = auto()
    operate_buttons_horizontal = auto()
    operate_info = auto()
    operate_screen = auto()
    pad_bottom = auto()
    screen_base = auto()
    single_button_vertical = auto()
    switch_horizontal = auto()
    switch_label = auto()
    switches_vertical = auto()
    tab_button = auto()
    tab_buttons_horizontal = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    tree_widget = auto()


class TreeName(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()


class UnwantedDirs(StrEnum):
    __pycache__ = "__pycache__"
    bin = "bin"
    cache = "cache"
    Cache = "Cache"
    CMakeFiles = "CMakeFiles"
    Crash_Reports = "Crash Reports"
    DerivedData = "DerivedData"
    Desktop = "Desktop"
    Documents = "Documents"
    dot_build = ".build"
    dot_bundle = ".bundle"
    dot_cache = ".cache"
    dot_dart_tool = ".dart_tool"
    dot_DS_Store = ".DS_Store"
    dot_git = ".git"
    dot_ipynb_checkpoints = ".ipynb_checkpoints"
    dot_mozilla = ".mozilla"
    dot_mypy_cache = ".mypy_cache"
    dot_parcel_cache = ".parcel_cache"
    dot_pytest_cache = ".pytest_cache"
    dot_ssh = ".ssh"
    dot_Trash = ".Trash"
    dot_venv = ".venv"
    Downloads = "Downloads"
    extensions = "extensions"
    go_build = "go-build"
    Music = "Music"
    node_modules = "node_modules"
    Pictures = "Pictures"
    Public = "Public"
    Recent = "Recent"
    temp = "temp"
    Temp = "Temp"
    Templates = "Templates"
    tmp = "tmp"
    trash = "trash"
    Trash = "Trash"
    Videos = "Videos"


class UnwantedFiles(StrEnum):
    AppImage = ".AppImage"
    bak = ".bak"
    cache = ".cache"
    coverage = ".coverage"
    doc = ".doc"
    docx = ".docx"
    egg_info = ".egg-info"
    gz = ".gz"
    kdbx = ".kdbx"
    lock = ".lock"
    pdf = ".pdf"
    pid = ".pid"
    ppt = ".ppt"
    pptx = ".pptx"
    rar = ".rar"
    swp = ".swp"
    tar = ".tar"
    temp = ".temp"
    tgz = ".tgz"
    tmp = ".tmp"
    xls = ".xls"
    xlsx = ".xlsx"
    zip = ".zip"


class ViewName(StrEnum):
    contents_view = auto()
    debug_log_view = auto()
    diff_view = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    init_purge_view = auto()
    app_log_view = auto()
    output_log_view = auto()
    cat_config = auto()
    config_ignored = auto()
    template_data = auto()
    diagram = auto()


SPLASH = """\
 _______________________________ ___________________._
|       |   |   |    ___|___    |    '    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".replace(
    "===", "=\u200b=\u200b="
).splitlines()


# provisional diagrams until dynamically created
FLOW = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │                   │                   │                   │
       │     Add Tab       │    autoCommit     │     git push      │
       │   Re-Add Tab      │──────────────────>│──────────────────>│
       │──────────────────>│                   │                   │
       │                   │                autopush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
       │     Apply Tab     │     chezmoi init & chezmoi git pull   │
       │<──────────────────│<──────────────────────────────────────│
       │                   │                   │                   │
       │     Diff View     │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │                   │
       │                   │                   │                   │
       │                   │    chezmoi init & chezmoi git pull    │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │        chezmoi init --one-shot & chezmoi init --apply     │
       │<──────────────────────────────────────────────────────────│
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │ target state │    │ source state │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""
