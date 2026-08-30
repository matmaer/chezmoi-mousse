from enum import Enum, StrEnum, auto
from typing import Self

__all__ = [
    "BindingAction",
    "BindingDescription",
    "BtnLabel",
    "Chars",
    "ChezmoiGitArgs",
    "ColorVar",
    "ContainerName",
    "GlobalArgs",
    "InfoKind",
    "LoadingLabel",
    "LogString",
    "OpInfoString",
    "PathFilters",
    "PathKind",
    "ReactiveVar",
    "ReadCmd",
    "RichLogName",
    "SectionLabel",
    "StatusCode",
    "SplashLogStr",
    "SwitchLabel",
    "Tcss",
    "VerbArgs",
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
    # Placeholder
    not_set = "Not Set"

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
    close = "Close"
    enable_live_run = "Enable live run"
    switch_to_dry_run = "Switch to dry run"

    @property
    def pane_id(self) -> str:
        return f"{self}_pane_id"

    @classmethod
    def debug_tab_btn_set(cls) -> frozenset["BtnLabel"]:
        return frozenset(
            {
                BtnLabel.create_diffs,
                BtnLabel.create_paths,
                BtnLabel.list_test_paths,
                BtnLabel.log_memory,
                BtnLabel.remove_paths,
            }
        )

    @classmethod
    def dry_run_set(cls) -> frozenset["BtnLabel"]:
        return frozenset({BtnLabel.enable_live_run, BtnLabel.switch_to_dry_run})

    @classmethod
    def exit_modal_set(cls) -> frozenset["BtnLabel"]:
        return frozenset({BtnLabel.cancel, BtnLabel.close, BtnLabel.reload})

    @classmethod
    def main_tabs_set(cls) -> frozenset["BtnLabel"]:
        return frozenset(
            {
                BtnLabel.add,
                BtnLabel.apply,
                BtnLabel.config,
                BtnLabel.debug,
                BtnLabel.logs,
                BtnLabel.re_add,
            }
        )

    @classmethod
    def run_btn_set(cls) -> frozenset["BtnLabel"]:
        return frozenset(
            {
                BtnLabel.add_run,
                BtnLabel.apply_run,
                BtnLabel.destroy_run,
                BtnLabel.forget_run,
                BtnLabel.re_add_run,
            }
        )

    # classmethod which maps each review button to its corresponding run button
    @classmethod
    def _review_to_run_map(cls) -> dict["BtnLabel", "BtnLabel"]:
        return {
            cls.add_review: cls.add_run,
            cls.apply_review: cls.apply_run,
            cls.re_add_review: cls.re_add_run,
            cls.destroy_review: cls.destroy_run,
            cls.forget_review: cls.forget_run,
        }

    @property
    def review_to_run(self) -> "BtnLabel":
        return self._review_to_run_map()[self]


class Chars(StrEnum):
    burger = "\u2261"  # IDENTICAL TO
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_arrow = f"{'\u2014' * 3}\u2192"  # EM DASH, RIGHTWARDS ARROW
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE
    # warning_sign = "\u26a0"  # WARNING SIGN # noqa: ERA001
    x_mark = "\u2716"  # HEAVY MULTIPLICATION X
    bullet = "\u2022"  # BULLET # noqa: ERA001
    # check_mark = "\u2714"  # HEAVY CHECK MARK # noqa: ERA001
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


class ColorVar(StrEnum):
    bogus = "#FFFF00"
    dimmed = "foreground-darken-3"
    info = "foreground-darken-1"
    accent_darken_2 = "accent-darken-2"
    text = "text"
    text_accent = "text-accent"
    text_block = "foreground-darken-1"
    text_error = "text-error"
    text_error_dark = "text-error-darken-3"
    text_primary = "text-primary"
    text_secondary = "text-secondary"
    text_success = "text-success"
    text_warning = "text-warning"


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
    git_ignored = auto()
    git_log = auto()
    left_side = auto()
    operate_buttons = auto()
    right_side = auto()
    template_data = auto()
    test_paths_view = auto()

    @property
    def container_id(self) -> str:
        return f"{self}_id"


class LoadingLabel(StrEnum):
    loading = "Loading"  # the initial label
    get_affected_paths = "Getting affected paths"
    purge_cache = "Purge cached data"
    update_trees = "Update Managed Trees"
    reload_dir_tree = "Reloading Add tab directory tree"


class LogString(StrEnum):
    added_managed = "New managed paths"
    app_log_initialized = "Application log initialized"
    changed_status = "New managed paths"
    debug_log_initialized = "Debug log initialized"
    debug_tab_enabled = "Debug tab enabled"
    doctor_errors_found = "See the Config tab for errors"
    doctor_failed_found = "See the Config tab for failed checks"
    doctor_minor_issues_found = "Doctor issues are probably safe to ignore"
    doctor_no_issue_found = "No warnings, failed or error entries reported"
    doctor_not_set_found = "See the Config tab for commands not set"
    doctor_section = "Chezmoi doctor output"
    doctor_warnings_found = "See the Config tab for warnings"
    env_vars = "Environment variables"
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    not_tracing = "tracemalloc is not tracing but the Debug tab is active"
    removed_managed = "New managed paths"
    tracing = "tracemalloc is tracing"

    @property
    def end(self) -> str:
        return "-" * len(self)


class InfoKind(Enum):
    # Kind of info mainly
    contents_view_file = auto()
    dest_dir_diff = auto()
    dest_dir_contents = auto()
    unmanaged_diff = auto()
    unmanaged_git_log = auto()


class OpInfoString(StrEnum):
    add_path_info = (
        f"[${ColorVar.info}]{Chars.bullet} Add new targets to the source state[/]"
    )
    add_subtitle = f"local path {Chars.right_arrow} chezmoi repo"
    apply_path_info = (
        f"[${ColorVar.info}]{Chars.bullet} Chezmoi will ensure that the path is in the "
        "target state. The command will run without prompting. For targets modified "
        "since chezmoi last wrote it[/]"
    )
    apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
    auto_add = (
        f"{Chars.bullet} [${ColorVar.text_warning}]Chezmoi 'autoadd' is enabled: "
        "paths will be added to the chezmoi repository[/]"
    )
    auto_commit = (
        f"{Chars.bullet} [${ColorVar.text_warning}]Chezmoi 'autocommit' is "
        "enabled: paths will be committed to the chezmoi repository[/]"
    )
    auto_push = (
        f"{Chars.bullet} [${ColorVar.text_warning}]Chezmoi 'autopush' is enabled: "
        "the updated chezmoi repository will be pushed to the remote (origin)[/]"
    )
    auto_settings_not_applicable = (
        f"{Chars.bullet} [dim]Apply btn_label: chezmoi autoadd, autocommit and "
        "autopush not applicable[/]"
    )
    destroy_path_info = (
        f"{Chars.bullet} [${ColorVar.text_error}]Permanently remove the path from disk "
        "and chezmoi.\n"
        "MAKE SURE YOU HAVE A BACKUP![/]"
    )
    destroy_subtitle = (
        f"[${ColorVar.text_error}]{Chars.x_mark}delete on disk and in chezmoi repo"
        f"[${ColorVar.text_error}]{Chars.x_mark}[/]"
    )
    dry_run_notice = (
        f"{Chars.bullet} [${ColorVar.text_secondary}]--dry-run flag is active, no "
        "changes will be made to the chezmoi repository[/]"
    )
    forget_path_info = (
        f"{Chars.bullet} [${ColorVar.info}]Remove from the source state, i.e. stop "
        "managing them[/]"
    )
    forget_subtitle = f"leave on disk {Chars.right_arrow} chezmoi repo {Chars.x_mark}"
    live_run_notice = (
        f"{Chars.bullet} [${ColorVar.text_warning}]Command will run live! The paths "
        "below will be affected![/]"
    )
    re_add_path_info = (
        f"{Chars.bullet} [${ColorVar.info}]Re-add modified files in the target state, "
        "preserving any encrypted_ attributes. chezmoi will not overwrite templates, "
        "and all entries that are not files are ignored[/]"
    )
    re_add_subtitle = f"path on disk {Chars.right_arrow} overwrite chezmoi repo"


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


class PathKind(StrEnum):
    EXISTS_FALSE = auto()
    man_dir_access_denied = auto()
    man_dir_not_exists = auto()
    SYMLINK = auto()
    UNHANDLED = auto()
    unman_dir_access_denied = auto()
    UNMANAGED = auto()


class ReactiveVar(StrEnum):
    cmd_result = auto()


class RichLogName(StrEnum):
    app_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    env_var_logger = auto()
    memory_usage_logger = auto()


class SectionLabel(StrEnum):
    added_managed_paths = "Added managed paths"
    affected_paths = "Paths affected by the command"
    cat_config_output = "Cat Config Output"
    changed_paths = "Changed Paths"
    changed_status_paths = "Changed status paths"
    chezmoi_cat_output = "Chezmoi Cat output"
    command_outputs = "Command Output"
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
    paths_with_status = "Paths with Status"
    read_file_output = "Read file from disk output"
    removed_managed_paths = "Removed managed paths"
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"
    template_data_output = "Chezmoi Data Output"
    test_paths = " Test Paths "
    unmanaged_dir = "Unmanaged Directory"
    unmanaged_file = "Unmanaged File"


class SplashStr(StrEnum):
    completed = auto()
    found_repo = "create new chezmoi repo"
    exit_one = auto()
    exit_other = auto()
    exit_zero = auto()
    found_existing_repo = "chezmoi repository exists"
    reported = auto()


class StatusCode(StrEnum):
    Added = "A"
    Deleted = "D"
    Modified = "M"
    Run = "R"
    Space = " "

    # Fake status code for internal use in the ManagedTree, not returned by chezmoi
    # Used to create the color and to determine if the dir should be displayed or not.
    N_DIR = auto()


class SplashLogStr(StrEnum):
    # Splash log strings, prefixes
    has_git_commits = "chezmoi repo has commits"
    has_no_git_commits = "chezmoi repo has no commits"
    parse_dump_config = "parse dump-config"
    repo_created = "chezmoi repo created"
    repo_found = "chezmoi repo found"
    repo_not_found = "chezmoi repo not found"

    # Splash log strings, suffixes
    checked = auto()  # for non-problematic non-exit 0 chezmoi commands
    failed = auto()  # problematic non-exit 0 chezmoi commands, failed non chezmoi
    reports = auto()  # other
    parsed = auto()
    success = auto()  # successful commands

    @classmethod
    def _suffixes(cls) -> frozenset[Self]:
        return frozenset(
            (
                cls[cls.checked],
                cls[cls.failed],
                cls[cls.reports],
                cls[cls.parsed],
                cls[cls.success],
            )
        )

    @property
    def padded(self) -> str:
        if self not in self._suffixes():
            raise ValueError(f"{self} is not a splash log suffix")
        # Add padding for splash log suffixes
        max_length = max(len(str(suffix)) for suffix in self._suffixes())
        # return the string with spaces on the left
        return str(self).rjust(max_length)


class SwitchLabel(StrEnum):
    # Apply and ReAdd Tab
    show_unchanged = "Show unchanged paths"
    show_unmanaged = "Show unmanaged children"
    expand_all = "Expand all dirs"

    # Add Tab
    show_managed = "Show managed paths"
    show_unwanted = "Show unwanted paths"


class Tcss(StrEnum):
    add_tab_contents_view = auto()
    added = auto()
    changed = auto()
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
    live_run_color = auto()
    main_section_label = auto()
    managed_tree = auto()
    operate_button = auto()
    op_btn_group = auto()
    operate_info = auto()
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


##############################################
# Enums for the chezmoi command construction #
##############################################


class ChezmoiGitArgs(Enum):
    option_terminator = "--"
    global_args = ("--no-pager", "--no-advice")
    default_args = (option_terminator,) + global_args
    # _dry_run = "--dry-run" # noqa: ERA001
    git_log_args = (
        "--date-order",
        "--format=%ar%x1f%cn%x1f%s%x00",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    )
    git_log = default_args + ("log",) + git_log_args
    git_remote = default_args + ("remote", "--verbose")
    check_exists = default_args + ("rev-parse", "--git-dir")
    check_has_commits = default_args + ("rev-parse", "--verify", "HEAD")


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
    verbose = "--verbose=true"


class VerbArgs(StrEnum):
    format_json = "--format=json"
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadCmd(Enum):
    cat = ("cat",)
    cat_config = ("cat-config",)
    diff = ("diff",)
    diff_reverse = ("diff", VerbArgs.reverse)
    doctor = ("doctor",)
    dump_config = ("dump-config", VerbArgs.format_json)
    git_commit_check = ("git",) + ChezmoiGitArgs.check_has_commits.value
    git_log = ("git",) + ChezmoiGitArgs.git_log.value
    git_remote = ("git",) + ChezmoiGitArgs.git_remote.value
    git_repo_check = ("git",) + ChezmoiGitArgs.check_exists.value
    ignored = ("ignored",)
    managed_dirs = ("managed", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    managed_files = ("managed", VerbArgs.path_style_absolute, VerbArgs.include_files)
    source_path = ("source-path",)
    status_dirs = ("status", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    status_files = ("status", VerbArgs.path_style_absolute, VerbArgs.include_files)
    template_data = ("data", VerbArgs.format_json)

    @classmethod
    def managed_commands(cls) -> tuple["ReadCmd", ...]:
        return (cls.managed_dirs, cls.managed_files, cls.status_dirs, cls.status_files)


class WriteCmd(Enum):
    init = ("init",)
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)

    @classmethod
    def get_write_cmd(cls, op_btn_label: BtnLabel) -> "WriteCmd":
        mapping = {
            BtnLabel.add_run: cls.add,
            BtnLabel.apply_run: cls.apply,
            BtnLabel.destroy_run: cls.destroy,
            BtnLabel.forget_run: cls.forget,
            BtnLabel.re_add_run: cls.re_add,
        }
        return mapping[op_btn_label]
