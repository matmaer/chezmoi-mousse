from __future__ import annotations

from enum import Enum, StrEnum, auto
from functools import cache, cached_property
from typing import Self

__all__ = [
    "BindingAction",
    "BindingDescription",
    "BtnLabel",
    "Chars",
    "ChezmoiStatusCode",
    "ColorVar",
    "ContainerName",
    "GlobalArgs",
    "InfoKind",
    "LabelStr",
    "LogStr",
    "PathFilters",
    "ProblemChars",
    "ReactiveVar",
    "ReadCmd",
    "RichLogName",
    "Tcss",
    "WriteCmd",
]


class BindingAction(StrEnum):
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider = auto()


class BindingDescription(StrEnum):
    # Tab bindings
    hide_filters = "Hide filters"
    # Shared bindings
    maximize = "Maximize"
    minimize = "Minimize"
    show_filters = "Show filters"
    enable_live_run = "Enable live run"
    switch_to_dry_run = "Switch to dry run"


class BtnLabel(StrEnum):
    # Main tabs
    add = "Add"
    apply = "Apply"
    config = "Config"
    debug = "Debug"
    logs = "Logs"
    re_add = "Re-Add"

    # Gen 2 main tabs
    managed_tree = "Managed Tree"
    danger_zone = "Danger Zone"

    # Managed Tree operation buttons
    chezmoi_add = "chezmoi add"
    chezmoi_apply = "chezmoi apply"
    chezmoi_re_add = "chezmoi re-add"

    # Danger Zone operation buttons
    chezmoi_forget = "chezmoi forget"
    chezmoi_destroy = "chezmoi destroy"

    # Tab buttons for content switcher within a main tab
    app_log = "Application"
    cmd_log = "Chezmoi-Commands"
    contents = "Contents"
    diff = "Diff"
    git_log = "Git-Log"

    # Flat button labels
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    env_vars = "Env Vars"
    ignored = "Ignored"
    template_data = "Template Data"
    test_paths = "Test Paths"

    # Triggers chezmoi command labels
    add_review = "Review Add Path"
    add_run = "Run Chezmoi Add"
    apply_review = "Review Apply Path"
    apply_run = "Run Chezmoi Apply"
    forget_review = "Review Forget Path"
    forget_run = "Run Chezmoi Forget"
    destroy_review = "Review Destroy Path"
    destroy_run = "Run Chezmoi Destroy"
    re_add_review = "Review Re-Add Path"
    re_add_run = "Run Chezmoi Re-Add"
    refresh_trees = "Refresh Trees"
    reload = "Reload"

    # Debug tab buttons
    create_diffs = "Create Diffs"
    create_paths = "Create Test Paths"
    list_test_paths = "List Test Paths"
    log_memory = "Log Memory Usage"
    remove_paths = "Remove Test Paths"

    # Other
    cancel = "Cancel"

    @property
    def pane_id(self) -> str:
        return f"{self.name}_pane_id"


class Chars(StrEnum):
    burger = "\u2261"  # IDENTICAL TO
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE

    # Used by Tree and DirectoryTree subclasses, simply adds a space to the triangle
    tree_collapsed = f"{right_triangle} "
    tree_expanded = f"{down_triangle} "


class ColorVar(StrEnum):
    bogus = "#FFFF00"
    accent_darken_2 = "accent-darken-2"
    dimmed = "foreground-darken-3"
    info = "foreground-darken-1"
    success = "success"
    text = "text"
    text_block = "foreground-darken-1"
    text_error = "text-error"
    text_error_dark = "text-error-darken-3"
    text_primary = "text-primary"
    text_secondary = "text-secondary"
    text_success = "text-success"
    text_warning = "text-warning"
    warning = "warning"


class ContainerName(StrEnum):
    cat_config = auto()
    contents = auto()
    cmd_log = auto()
    debug_log = auto()
    diagram = auto()
    diff = auto()
    doctor = auto()
    dom_nodes = auto()
    env_vars = auto()
    flat_buttons = auto()
    git_ignored = auto()
    git_log = auto()
    left_side = auto()
    middle = auto()
    right_side = auto()
    operate_buttons = auto()
    template_data = auto()
    test_paths_view = auto()

    @property
    def container_id(self) -> str:
        return f"{self}_id"


class InfoKind(Enum):
    # Kind of info mainly
    contents_view_file = auto()
    dest_dir_contents = auto()


class LabelStr(StrEnum):
    # Managed Tree and Danger Zone tab
    middle = "Middle Section"
    right_side = "Right Side Section"

    # Apply and ReAdd Tab
    show_unchanged = "Show unchanged paths"
    show_unmanaged = "Show unmanaged children"
    expand_all = "Expand all dirs"

    # Add Tab
    show_managed = "Show managed paths"
    show_unwanted = "Show unwanted paths"

    # Changed paths
    # added_managed_paths = "Added managed paths" # noqa: ERA001
    # changed_paths = "Changed Paths" # noqa: ERA001
    # changed_status_paths = "Changed status paths" # noqa: ERA001
    # removed_managed_paths = "Removed managed paths" # noqa: ERA001

    # Other
    cat_config_output = "Cat Config Output"
    chezmoi_cat_output = "Chezmoi Cat output"
    # command_outputs = "Command Output"  # noqa: ERA001
    debug_log = "Debug Log"
    dest_dir = "Destination Directory"
    dest_dir_diff = "This is the root of the chezmoi repository and never has a status"
    diagram = "Chezmoi Diagram"
    doctor_output = "Doctor Output"
    dom_nodes = "DOM Nodes"
    env_vars = "Environment Variables"
    full_cmd = "Full Command"
    ignored_output = "Ignored Output"
    managed_dir = "Managed Directory"
    managed_file = "Managed File"
    managed_no_status = "The path is managed but has no status for this context"
    n_dir = "Managed directory which contains nested status paths"
    no_managed_paths = "No managed paths yet"
    no_status_paths = "No paths with a status"
    not_set = "Not Set"
    read_file_output = "Read file from disk output"
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"
    template_data_output = "Chezmoi Data Output"
    test_paths = " Test Paths "
    unmanaged_dir = "Unmanaged Directory"
    unmanaged_file = "Unmanaged File"


class LogStr(StrEnum):
    # added_managed = "New managed paths" # noqa: ERA001
    app_log_initialized = "Application log initialized"
    # changed_status = "New managed paths" # noqa: ERA001
    debug_log_initialized = "Debug log initialized"
    debug_tab_enabled = "Debug tab enabled"
    doctor_errors_found = "See the Config tab for errors"
    doctor_failed_found = "See the Config tab for failed checks"
    doctor_minor_issues_found = "Doctor issues are probably safe to ignore"
    doctor_no_issue_found = "No warnings, failed or error entries reported"
    doctor_not_set_found = "See the Config tab for commands not set"
    doctor_section = "Chezmoi doctor output"
    doctor_warnings_found = "See the Config tab for warnings"
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    not_tracing = "tracemalloc is not tracing but the Debug tab is active"
    # removed_managed = "New managed paths" # noqa: ERA001
    tracing = "tracemalloc is tracing"

    @property
    def end(self) -> str:
        return "-" * len(self)

    # Splash log strings, prefixes
    check_chezmoi_repo = "check chezmoi repository"
    parse_dump_config = "parse chezmoi dump-config"

    # Splash log strings, suffixes
    absent = auto()
    checked = auto()
    parsed = auto()
    present = auto()
    reports = auto()
    skipped = auto()
    success = auto()

    @classmethod
    @cache
    def _splash_suffixes(cls) -> frozenset[Self]:
        return frozenset(
            (
                cls[cls.absent],
                cls[cls.checked],
                cls[cls.parsed],
                cls[cls.present],
                cls[cls.reports],
                cls[cls.skipped],
                cls[cls.success],
            )
        )

    @property
    def padded_suffix(self) -> str:
        if self not in self._splash_suffixes():
            raise ValueError(f"{self} is not a splash log suffix")
        # Add padding for splash log suffixes
        max_length = max(len(str(suffix)) for suffix in self._splash_suffixes())
        # return the string with spaces on the left
        return str(self).rjust(max_length)


class PathFilters(Enum):
    # TODO: create an ALWAYS_IGNORE category to realistically implement things like
    # os.walk, os.scandir, pathlib.iterdir and watchdog features to avoid elaborate
    # exception handling, useless work, and keeping things as lean as possible

    UNWANTED_DIRS = (
        ".build",
        ".bundle",
        ".dart_tool",
        ".DS_Store",
        ".env",
        ".ipynb_checkpoints",
        ".mozilla",
        ".Trash",
        ".venv",
        "bin",
        "CMakeFiles",
        "Crash Reports",
        "DerivedData",
        "Desktop",
        "Documents",
        "Downloads",
        "extensions",
        "go-build",
        "Music",
        "node_modules",
        "Pictures",
        "Public",
        "Recent",
        "temp",
        "Temp",
        "Templates",
        "tmp",
        "trash",
        "Trash",
        "Videos",
    )

    KEY_FILE_NAMES = (
        # As we don't support adding encrypted files yet, we are excluding them.
        # Common private key file names across platforms
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "id_ecdsa_sk",  # FIDO/U2F ECDSA
        "id_ed25519_sk",  # FIDO/U2F Ed25519
        "identity",  # Legacy RSA1
        # Age encryption tool
        "age-key.txt",
        "keys.txt",  # common age key file name
        # Generic private key naming conventions
        "private_key",
        "privatekey",
        "priv_key",
        "privkey",
        # Terraform / cloud provider credentials
        "terraform.tfvars",  # often contains secrets
        "credentials",  # AWS credentials file pattern
        # Kubernetes
        "kubeconfig",
        # Wireguard
        "wg0.conf",  # contains PrivateKey
        "privatekey",
    )

    KEY_FILE_EXTENSIONS = (
        # Common private key file extensions
        # PuTTY private key files
        ".ppk",
        # GPG / PGP private key exports
        ".gpg",
        ".pgp",
        ".asc",
        # SSL/TLS private keys
        ".key",
        ".p12",
        ".pfx",
        # Generic private key naming conventions
        ".pem",
    )

    UNWANTED_FILE_SUFFIXES = (
        ".7z",
        ".AppImage",
        ".bak",
        ".bin",
        ".coverage",
        ".doc",
        ".docx",
        ".egg-info",
        ".exe",
        ".gif",
        ".gz",
        ".img",
        ".iso",
        ".jar",
        ".jpeg",
        ".jpg",
        ".kdbx",
        ".lock",
        ".pdf",
        ".pid",
        ".png",
        ".ppk",
        ".ppt",
        ".pptx",
        ".rar",
        ".swp",
        ".tar",
        ".temp",
        ".tgz",
        ".tmp",
        ".xls",
        ".xlsx",
        ".zip",
    )


class ProblemChars(StrEnum):
    BIDI_PDF = "\u202c"
    BIDI_RLO = "\u202e"
    COMBINING = "\u0301"
    VARSEL = "\ufe0f"
    ZWJ = "\u200d"
    ZWS = "\u200b"


class ReactiveVar(StrEnum):
    cmd_result = auto()
    template_data = auto()


class RichLogName(StrEnum):
    app_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    env_var_logger = auto()
    memory_usage_logger = auto()


class ChezmoiStatusCode(StrEnum):
    Added = "A"
    Deleted = "D"
    Modified = "M"
    Run = "R"
    Space = " "

    # Fake status code for internal use in the ManagedTree, not returned by chezmoi
    # Used to create the color and to determine if the dir should be displayed or not.
    N_DIR = auto()


class StatusPairs(StrEnum):
    # Standard file state pairs
    M_S = "M "  # Modified locally in target
    S_M = " M"  # Modified in source repo
    M_M = "MM"  # Modified in both target and source

    D_S = "D "  # Deleted locally in target (apply will recreate)
    S_D = " D"  # Deleted in source repo (apply will delete target)
    D_A = "DA"  # Previously managed entry deleted, recreate from source
    M_A = "MA"  # Modified locally, target state creates entry

    A_S = "A "  # Target entry created locally (unmanaged/new)
    S_A = " A"  # Target entry added in source repo

    # Script execution pair
    S_R = " R"  # Script target will run on apply


class Tcss(StrEnum):
    # Operation tabs
    operations_left = auto()
    operations_middle = auto()
    operations_right = auto()
    switch_group = auto()
    operate_pane = auto()

    # Both legacy and operation tabs
    dest_dir_tree_label = auto()
    main_section_label = auto()
    managed_tree = auto()

    # Other
    add_tab_contents_view = auto()
    added = auto()
    changed = auto()
    context = auto()
    directory_tree = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    full_cmd = auto()
    info = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    left_side_vertical = auto()
    live_run_color = auto()
    op_btn_group = auto()
    operate_button = auto()
    refresh_button = auto()
    removed = auto()
    single_button_vertical = auto()
    sub_section_label = auto()
    tab_button = auto()
    unhandled = auto()


##############################################
# Enums for the chezmoi command construction #
##############################################


class _ChezmoiGitArgs(Enum):
    _option_terminator = "--"
    global_args = ("--no-pager", "--no-advice")
    verbose = "--verbose"
    # _dry_run = "--dry-run" # noqa: ERA001
    git_log_args = (
        "--date-order",
        "--format=%ar%x1f%cn%x1f%s%x00",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    )
    git_dir = (_option_terminator, *global_args, "rev-parse", "--git-dir")
    git_log = (_option_terminator, *global_args, "log", *git_log_args)
    git_remote = (_option_terminator, *global_args, "remote", verbose)


class GlobalArgs(Enum):
    global_defaults = (
        "--color=off",
        "--force=true",
        "--interactive=false",
        "--keep-going=false",
        "--mode=file",
        "--no-pager=true",
        "--no-tty=true",
        "--progress=false",
        "--use-builtin-diff=true",
        "--use-builtin-git=true",
    )
    dry_run = "--dry-run=true"


class _VerbArgs(StrEnum):
    format_json = "--format=json"
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadCmd(Enum):
    cat = ("cat",)
    cat_config = ("cat-config",)
    diff = ("diff",)
    diff_reverse = ("diff", _VerbArgs.reverse)
    doctor = ("doctor",)
    dump_config = ("dump-config", _VerbArgs.format_json)
    git_dir = ("git", *_ChezmoiGitArgs.git_dir.value)
    git_log = ("git", *_ChezmoiGitArgs.git_log.value)
    git_remote = ("git", *_ChezmoiGitArgs.git_remote.value)
    ignored = ("ignored",)
    managed_dirs = ("managed", _VerbArgs.path_style_absolute, _VerbArgs.include_dirs)
    managed_files = ("managed", _VerbArgs.path_style_absolute, _VerbArgs.include_files)
    source_path = ("source-path",)
    status_dirs = ("status", _VerbArgs.path_style_absolute, _VerbArgs.include_dirs)
    status_files = ("status", _VerbArgs.path_style_absolute, _VerbArgs.include_files)
    template_data = ("data", _VerbArgs.format_json)

    @cached_property
    def pretty_cmd(self) -> str:
        ugly_args: tuple[str, ...] = (
            *_ChezmoiGitArgs.global_args.value,
            *_ChezmoiGitArgs.git_log_args.value,
            _ChezmoiGitArgs.verbose.value,
            *(
                _VerbArgs.format_json.value,
                _VerbArgs.path_style_absolute.value,
            ),
        )
        verb_str = " ".join(a for a in self.value if a not in ugly_args)
        return f"chezmoi {verb_str}"

    @classmethod
    @cache
    def splash_commands(cls) -> tuple[Self, ...]:
        return (
            cls(cls.doctor),
            cls(cls.cat_config),
            cls(cls.git_log),
            cls(cls.git_remote),
            cls(cls.ignored),
            cls(cls.template_data),
        )

    @classmethod
    @cache
    def managed_commands(cls) -> tuple[Self, ...]:
        return (
            cls(cls.managed_dirs),
            cls(cls.managed_files),
            cls(cls.status_dirs),
            cls(cls.status_files),
        )


class WriteCmd(Enum):
    init = ("init",)
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)

    @classmethod
    @cache
    def get_write_cmd(cls, op_btn_label: BtnLabel) -> Self:
        mapping: dict[BtnLabel, Self] = {
            BtnLabel.add_run: cls(cls.add),
            BtnLabel.apply_run: cls(cls.apply),
            BtnLabel.destroy_run: cls(cls.destroy),
            BtnLabel.forget_run: cls(cls.forget),
            BtnLabel.re_add_run: cls(cls.re_add),
        }
        return mapping[op_btn_label]

    @cached_property
    def pretty_cmd(self) -> str:
        return f"chezmoi {self.value[0]}"
