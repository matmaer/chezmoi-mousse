from enum import Enum, StrEnum, auto

__all__ = [
    "BindingAction",
    "BindingDescription",
    "Chars",
    "ContainerName",
    "FlatBtnLabel",
    "RichLogName",
    "LogString",
    "PathKind",
    "SectionLabel",
    "StatusCode",
    "SwitchLabel",
    "TabLabel",
    "Tcss",
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
    remove_dry_run = "Remove --dry-run"
    add_dry_run = "Add --dry-run"


class Chars(StrEnum):
    burger = "\u2261"  # IDENTICAL TO
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_arrow = f"{'\u2014' * 3}\u2192"  # EM DASH, RIGHTWARDS ARROW
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE
    warning_sign = "\u26a0"  # WARNING SIGN
    x_mark = "\u2716"  # HEAVY MULTIPLICATION X
    # bullet = "\u2022"  # BULLET # noqa: ERA001
    check_mark = "\u2714"  # HEAVY CHECK MARK
    # gear = "\u2699"  # GEAR # noqa: ERA001
    # heavy_line = "\u2501"  # Box Drawings Heavy Horizontal # noqa: ERA001
    # heavy_line_left = "\u2578"  # BOX DRAWINGS HEAVY LEFT  # noqa: ERA001
    # heavy_line_right = "\u257a"  # BOX DRAWINGS HEAVY RIGHT # noqa: ERA001
    # quadrant_lower_left = "\u2596"  # Quadrant Lower Left # noqa: ERA001
    # quadrant_lower_right = "\u2597"  # Quadrant Lower Rightbottom # noqa: ERA001
    # quadrant_upper_left = "\u2598"  # Quadrant Upper Left # noqa: ERA001
    # quadrant_upper_right = "\u259d"  # Quadrant Upper Right # noqa: ERA001

    # Used by Tree and DirectoryTree subclasses, simply adds a space to the triangle
    tree_collapsed = f"{right_triangle} "
    tree_expanded = f"{down_triangle} "


class ContainerName(StrEnum):
    cat_config = auto()
    contents = auto()
    debug_log = auto()
    diagram = auto()
    diff = auto()
    doctor = auto()
    dom_nodes = auto()
    git_ignored = auto()
    git_log = auto()
    left_side = auto()
    memory_usage = auto()
    operate_buttons = auto()
    pw_mgr_info = auto()
    right_side = auto()
    template_data = auto()
    test_paths_view = auto()


class FlatBtnLabel(StrEnum):
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    ignored = "Ignored"
    pw_mgr_info = "Password Managers"
    template_data = "Template Data"
    test_paths = "Test Paths"
    memory_usage = "Memory Usage"


class LogColor(StrEnum):
    error = "text-error"
    info = "text-primary"
    ready = "accent-darken-2"
    success = "text-success"
    warning = "text-warning"


class LogString(StrEnum):
    app_log_initialized = "Application log initialized"
    debug_log_initialized = "Debug log initialized"
    debug_tab_enabled = "Debug tab enabled"
    doctor_no_issue_found = "No warnings, failed or error entries reported"
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    using_chezmoi_bin = "Using chezmoi binary at:"


class PathKind(StrEnum):
    path_exists = auto()  # managed path which exists on file system
    path_not_exists = auto()  # managed path which does not exists on file system

    # these are managed dirs, have no status but have status descendants
    apply_n_dir = auto()  # column 1 in chezmoi status output
    re_add_n_dir = auto()  # column 2 in chezmoi status output

    # for unmanaged paths
    unmanaged = auto()
    unwanted = auto()

    # for any managed or unmanaged path
    symlink = auto()
    unknown = auto()


class PathFilters(Enum):

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


class RichLogName(StrEnum):
    app_logger = auto()
    cmd_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    memory_usage_logger = auto()


class SectionLabel(StrEnum):
    cat_config_output = "Cat Config Output"
    debug_log = " Debug Log "
    diagram = "Chezmoi Diagram"
    doctor_output = "Doctor Output"
    dom_nodes = " DOM Nodes "
    full_cmd = "Full Command"
    ignored_output = "Ignored Output"
    memory_usage = " Memory Usage "
    password_managers = "Password Manager Information"
    paths_with_status = "Paths with Status"
    project_description = "Project Description"
    project_link = "Project Link"
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"
    template_data_output = "Chezmoi Data Output"
    test_paths = " Test Paths "


class StatusCode(StrEnum):
    Added = "A"
    Deleted = "D"
    Modified = "M"
    Run = "R"
    Space = " "


class SwitchLabel(StrEnum):
    # Apply and ReAdd Tab
    show_unchanged = "Show unchanged paths"
    show_unmanaged_files = "Show unmanaged files"
    expand_all = "Expand all dirs"

    # Add Tab
    hide_unmanaged_dirs = "Hide unmanaged dirs"
    show_managed = "Show managed paths"
    show_unwanted = "Show unwanted paths"


class TabLabel(StrEnum):
    # Main tabs
    add = "Add"
    apply = "Apply"
    config = "Config"
    debug = "Debug"
    logs = "Logs"
    re_add = "Re-Add"
    # Tab buttons for content switcher within a main tab
    app_log = "Application"
    cmd_log = "Chezmoi-Commands"
    contents = "Contents"
    diff = "Diff"
    git_log = "Git-Log"

    @classmethod
    def main_tabs(cls) -> tuple["TabLabel", ...]:
        return (cls.apply, cls.re_add, cls.add, cls.logs, cls.config, cls.debug)


class Tcss(StrEnum):
    add_tab_contents_view = auto()
    added = auto()
    changed = auto()
    live_run_color = auto()
    context = auto()
    dest_dir_tree_label = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    full_cmd = auto()
    info = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    limited_label = auto()
    main_section_label = auto()
    managed_tree = auto()
    operate_button = auto()
    operate_info = auto()
    pw_mgr_group = auto()
    refresh_button = auto()
    removed = auto()
    single_button_vertical = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    unhandled = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"
