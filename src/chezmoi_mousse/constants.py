from enum import StrEnum, auto


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


class DoctorCollapsibles(StrEnum):
    cat_config = "chezmoi cat-config (contents of config-file)"
    diagram = "chezmoi diagram (how operations are applied)"
    doctor = "chezmoi doctor output (diagnostic information)"
    doctor_ignored = "chezmoi ignored (git ignore in source-dir)"
    doctor_template_data = "chezmoi template-data (contents of template-file)"
    pw_mgr_info = "supported password managers (link and description)"

    @property
    def qid(self) -> str:
        return f"#{self.name}"


class IoVerbs(StrEnum):
    doctor = "doctor"
    managed = "managed"
    status = "status"


class Location(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class ModalIdStr(StrEnum):
    invalid_input_modal = auto()
    maximized_modal = auto()
    maximized_vertical = auto()
    modal_contents_view = auto()
    modal_diff_view = auto()
    modal_git_log_view = auto()
    operate_collapsible = auto()
    operate_info = auto()
    operate_log = auto()
    operate_modal = auto()
    operate_vertical = auto()

    @property
    def qid(self) -> str:
        return f"#{self.name}"


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


class TabStr(StrEnum):
    add_tab = auto()
    apply_tab = auto()
    doctor_tab = auto()
    init_tab = auto()
    log_tab = auto()
    re_add_tab = auto()


class TcssStr(StrEnum):
    border_title_bottom = auto()
    border_title_top = auto()
    content_switcher_left = auto()
    content_switcher_right = auto()
    content_view = auto()
    diff_view = auto()
    dir_tree_widget = auto()
    doctor_collapsible = auto()
    doctor_table = auto()
    doctor_vertical = auto()
    flow_diagram = auto()
    input_field = auto()
    input_field_vertical = auto()
    input_select = auto()
    input_select_vertical = auto()
    last_clicked = auto()
    modal_base = auto()
    operate_button = auto()
    operate_log = auto()
    operate_top_path = auto()
    pad_bottom = auto()
    single_button_vertical = auto()
    switch_horizontal = auto()
    switch_label = auto()
    switches_vertical = auto()
    tab_button = auto()
    tab_buttons_horizontal = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    tree_widget = auto()


class TreeStr(StrEnum):
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
    node_modules = "node_modules"
    Pictures = "Pictures"
    Public = "Public"
    Recent = "Recent"
    temp = "temp"
    Temp = "Temp"
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


class ViewStr(StrEnum):
    contents_view = auto()
    diff_view = auto()
    doctor_table = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    init_purge_view = auto()


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
