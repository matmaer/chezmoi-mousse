from dataclasses import dataclass, fields
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Any

type Buttons = OperateButtons | TabButtons
type CmdWords = tuple[str, ...]
type Mro = tuple[type, ...]
type OperateButtons = tuple[OperateBtn, ...]
type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]
type TabButtons = tuple[TabBtn, ...]


# needed by both widgets.py and overrides.py
@dataclass
class NodeData:
    found: bool
    path: Path
    status: str


class UnwantedDirs(StrEnum):
    __pycache__ = "__pycache__"
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
    bin = "bin"
    cache = "cache"
    Cache = "Cache"
    CMakeFiles = "CMakeFiles"
    Crash_Reports = "Crash Reports"
    DerivedData = "DerivedData"
    Desktop = "Desktop"
    Documents = "Documents"
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


class TabStr(StrEnum):
    add_tab = auto()
    apply_tab = auto()
    doctor_tab = auto()
    init_tab = auto()
    log_tab = auto()
    re_add_tab = auto()


class ViewStr(StrEnum):
    contents_view = auto()
    diff_view = auto()
    doctor_table = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    init_purge_view = auto()


class Location(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class TreeStr(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()


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
    filter_horizontal = auto()
    filter_label = auto()
    filters_vertical = auto()
    flow_diagram = auto()
    invalid_input = auto()
    last_clicked = auto()
    modal_base = auto()
    operate_button = auto()
    operate_log = auto()
    operate_top_path = auto()
    pad_bottom = auto()
    single_button_vertical = auto()
    tab_button = auto()
    tab_buttons_horizontal = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    tree_widget = auto()


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


class IoVerbs(Enum):
    doctor = "doctor"
    managed = "managed"
    status = "status"


class ReadVerbs(Enum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
    diff = "diff"
    git = "git"
    ignored = "ignored"
    source_path = "source-path"


class OperateVerbs(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    purge = "purge"
    re_add = "re-add"


class Chars(Enum):
    add_file_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    apply_file_info_border = f"local \u2190{'\u2014' * 3} chezmoi"  # '\N{LEFTWARDS ARROW}', '\N{EM DASH}'
    bullet = "\u2022"  # '\N{BULLET}'
    burger = "\u2261"  # '\N{IDENTICAL TO}'
    check_mark = "\u2714"  # '\N{HEAVY CHECK MARK}'
    # gear = "\u2699"  # '\N{GEAR}'
    lower_3_8ths_block = "\u2583"  # "\N{LOWER THREE EIGHTHS BLOCK}"
    re_add = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'


class InfoBorderTitles(Enum):
    apply_file = Chars.apply_file_info_border.value
    re_add_file = Chars.add_file_info_border.value
    add_file = Chars.add_file_info_border.value
    forget_file = " forget file "
    destroy_file = " destroy file "


class OperateHelp(Enum):
    add = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
    apply = "[$text-primary]Local file (target state) in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign.value} Auto commit is enabled: files will also be committed.{Chars.warning_sign.value}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign.value} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign.value}[/]"
    # TODO from chezmoi help: If you want to remove all traces of chezmoi from your system use purge instead. If you want chezmoi to stop managing the file use forget instead.
    # ---> create links for this to the other tabs
    changes_mode_disabled = (
        "Changes mode disabled, operations will dry-run only"
    )
    changes_mode_enabled = "Changes mode enabled, operations will run."
    destroy = (
        "[$text-primary]Remove target from the source state, the destination directory, and the state.[/]",
        "[$text-error]The destroy command permanently removes files both from your home directory and chezmoi's source directory.[/]",
        "[$text-error]Only run chezmoi destroy if you have a separate backup of your home directory and your source directory.[/]",
    )
    diff_color = (
        "[$text-success]+ green lines will be added[/]",
        "[$text-error]- red lines will be removed[/]",
        f"[dim]{Chars.bullet.value} dimmed lines for context[/]",
    )
    # TODO chezmoi forget help: "Targets must have entries in the source state. They cannot be externals."
    # -> disable forget button in that case
    forget = "[$text-primary]Remove targets from the source state, i.e. stop managing them.[/]"
    re_add = (
        "[$text-primary]Overwrite  will be updated with current local file[/]"
    )


class TabBtn(Enum):
    # Tab buttons for content switcher within a main tab
    clone_repo = "Clone"
    contents = "Contents"
    diff = "Diff"
    git_log = "Git-Log"
    list = "List"
    new_repo = "New"
    purge_repo = "Purge"
    tree = "Tree"


class OperateBtn(Enum):
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


@dataclass(frozen=True)
class FilterData:
    label: str
    tooltip: str


class Switches(Enum):
    clone_and_apply = FilterData(
        "init and apply", ("run chezmoi init with --apply flag.")
    )
    expand_all = FilterData(
        "expand all dirs",
        (
            "Expand all managed directories. Depending on the unchanged "
            "switch."
        ),
    )
    guess_url = FilterData(
        "chezmoi guess", ("Submit with `chezmoi --guess-repo-url`.")
    )
    unchanged = FilterData(
        "show unchanged files",
        (
            "Include files unchanged files which are not found in the "
            "'chezmoi status' output."
        ),
    )
    unmanaged_dirs = FilterData(
        "show unmanaged dirs",
        (
            "The default (disabled), only shows directories which already "
            "contain managed files. This allows spotting new unmanaged files "
            "in already managed directories. Enable to show all directories "
            "which contain unmanaged files."
        ),
    )
    unwanted = FilterData(
        "show unwanted paths",
        (
            "Include files and directories considered as 'unwanted' for a "
            "dotfile manager. These include cache, temporary, trash (recycle "
            "bin) and other similar files or directories. For example enable "
            "this to add files to your chezmoi repository which are in a "
            "directory named '.cache'."
        ),
    )


class DoctorEnum(Enum):
    cat_config = "chezmoi cat-config (contents of config-file)"
    commands_not_found = (
        "chezmoi supported commands not found (ignore if not needed)"
    )
    diagram = "chezmoi diagram (how operations are applied)"
    doctor = "chezmoi doctor output (diagnostic information)"
    doctor_ignored = "chezmoi ignored (git ignore in source-dir)"
    doctor_template_data = "chezmoi template-data (contents of template-file)"

    @property
    def qid(self) -> str:
        return f"#{self.name}"


class TabIds:
    def __init__(self, tab_name: TabStr) -> None:
        self.filter_slider_id = f"{tab_name}_filter_slider"
        self.filter_slider_qid = f"#{self.filter_slider_id}"
        self.tab_main_horizontal_id = f"{tab_name}_main_horizontal"
        self.tab_name: TabStr = tab_name
        self.tab_pane_id = f"{tab_name}_pane"
        self.tab_pane_qid = f"#{self.tab_pane_id}"

    def button_id(self, btn_enum: OperateBtn | TabBtn) -> str:
        suffix = "_op_btn" if isinstance(btn_enum, OperateBtn) else "_tab_btn"
        return f"{self.tab_name}_{btn_enum.name}{suffix}"

    def button_qid(self, btn_enum: OperateBtn | TabBtn) -> str:
        return f"#{self.button_id(btn_enum)}"

    def buttons_horizontal_id(self, location: Location) -> str:
        return f"{self.tab_name}_{location}_horizontal"

    def buttons_horizontal_qid(self, location: Location) -> str:
        return f"#{self.buttons_horizontal_id(location)}"

    def button_vertical_id(self, btn_enum: OperateBtn | TabBtn) -> str:
        return f"{self.tab_name}_{btn_enum.name}_vertical"

    def content_switcher_id(self, side: Location) -> str:
        return f"{self.tab_name}_{side}_content_switcher"

    def content_switcher_qid(self, side: Location) -> str:
        return f"#{self.content_switcher_id(side)}"

    def filter_horizontal_id(
        self, filter_enum: Switches, location: Location
    ) -> str:
        return (
            f"{self.tab_name}_{filter_enum.name}_filter_horizontal_{location}"
        )

    def filter_horizontal_qid(
        self, filter_enum: Switches, location: Location
    ) -> str:
        return f"#{self.filter_horizontal_id(filter_enum, location)}"

    def switch_id(self, filter_enum: Switches) -> str:
        return f"{self.tab_name}_{filter_enum.name}_switch"

    def switch_qid(self, filter_enum: Switches) -> str:
        return f"#{self.switch_id(filter_enum)}"

    def tab_vertical_id(self, side: Location) -> str:
        return f"{self.tab_name}_{side}_vertical"

    def tab_vertical_qid(self, side: Location) -> str:
        return f"#{self.tab_vertical_id(side)}"

    def tree_id(self, tree: TreeStr) -> str:
        return f"{self.tab_name}_{tree}"

    def tree_qid(self, tree: TreeStr) -> str:
        return f"#{self.tree_id(tree)}"

    def view_id(self, view: ViewStr) -> str:
        return f"{self.tab_name}_{view}"

    def view_qid(self, view: ViewStr) -> str:
        return f"#{self.view_id(view)}"


@dataclass(frozen=True)
class Id:
    add: TabIds = TabIds(TabStr.add_tab)
    apply: TabIds = TabIds(TabStr.apply_tab)
    doctor: TabIds = TabIds(TabStr.doctor_tab)
    init: TabIds = TabIds(TabStr.init_tab)
    log: TabIds = TabIds(TabStr.log_tab)
    re_add: TabIds = TabIds(TabStr.re_add_tab)

    _pane_id_map: dict[str, TabIds] | None = None

    @classmethod
    def get_tab_ids_from_pane_id(cls, pane_id: str) -> TabIds:

        if cls._pane_id_map is None:
            cls._pane_id_map = {}
            for field in fields(cls):
                field_value = getattr(cls, field.name)
                if isinstance(field_value, TabIds):
                    cls._pane_id_map[field_value.tab_pane_id] = field_value

        if pane_id in cls._pane_id_map:
            return cls._pane_id_map[pane_id]
        raise ValueError(f"No TabIds found for pane_id: {pane_id}")
