from enum import Enum, StrEnum, auto

__all__ = [
    "BindingAction",
    "BindingDescription",
    "Chars",
    "ChezmoiGitArgs",
    "ColorVar",
    "ContainerName",
    "FlatBtnLabel",
    "GlobalArgs",
    "StaticString",
    "LoadingLabel",
    "LogString",
    "OpBtnLabel",
    "OpInfoString",
    "NotifyMsg",
    "PathFilters",
    "PathKind",
    "PwMgrInfo",
    "ReadCmd",
    "RichLogName",
    "SectionLabel",
    "StatusCode",
    "SwitchLabel",
    "TabLabel",
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


class ColorVar(StrEnum):
    bogus = "#FFFF00"
    dimmed = "foreground-darken-3"
    info = "foreground-darken-1"
    ready = "accent-darken-2"
    text = "text"
    text_error = "text-error"
    text_error_dark = "text-error-darken-3"
    text_primary = "text-primary"
    text_secondary = "text-secondary"
    text_success = "text-success"
    text_warning = "text-warning"


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


class LoadingLabel(StrEnum):
    loading = "Loading"  # the initial label
    log_cmd_results = "Logging command results"
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
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    removed_managed = "New managed paths"

    @property
    def end(self) -> str:
        return "-" * len(self)


class NotifyMsg(StrEnum):
    add_tab_tree_reloaded = "Add tab directory tree reloaded."
    no_managed_changes = "No managed or status paths changed."


class OpBtnLabel(StrEnum):
    add_dry_run = BindingDescription.add_dry_run
    remove_dry_run = BindingDescription.remove_dry_run
    add_review = "Review Add Path"
    add_run = "Run Chezmoi Add"
    apply_review = "Review Apply Path"
    apply_run = "Run Chezmoi Apply"
    cancel = "Cancel"
    close = "Close"
    create_diffs = "Create Diffs"
    create_paths = "Create Test Paths"
    destroy_review = "Review Destroy Path"
    destroy_run = "Run Chezmoi Destroy"
    forget_review = "Review Forget Path"
    forget_run = "Run Chezmoi Forget"
    list_test_paths = "List Test Paths"
    log_memory = "Log Memory Usage"
    not_set = "Not Set"
    re_add_review = "Review Re-Add Path"
    re_add_run = "Run Chezmoi Re-Add"
    refresh_trees = "Refresh Trees"
    reload = "Reload"
    remove_paths = "Remove Test Paths"

    @classmethod
    def dry_run_set(cls) -> frozenset["OpBtnLabel"]:
        return frozenset({OpBtnLabel.add_dry_run, OpBtnLabel.remove_dry_run})

    @classmethod
    def exit_modal_set(cls) -> frozenset["OpBtnLabel"]:
        return frozenset({OpBtnLabel.cancel, OpBtnLabel.close, OpBtnLabel.reload})

    @classmethod
    def review_btn_set(cls) -> frozenset["OpBtnLabel"]:
        return frozenset(
            {
                OpBtnLabel.add_review,
                OpBtnLabel.apply_review,
                OpBtnLabel.destroy_review,
                OpBtnLabel.forget_review,
                OpBtnLabel.re_add_review,
            }
        )

    @classmethod
    def run_btn_set(cls) -> frozenset["OpBtnLabel"]:
        return frozenset(
            {
                OpBtnLabel.add_run,
                OpBtnLabel.apply_run,
                OpBtnLabel.destroy_run,
                OpBtnLabel.forget_run,
                OpBtnLabel.re_add_run,
            }
        )

    # classmethod which maps each review button to its corresponding run button
    @classmethod
    def _review_to_run_map(cls) -> dict["OpBtnLabel", "OpBtnLabel"]:
        return {
            cls.add_review: cls.add_run,
            cls.apply_review: cls.apply_run,
            cls.re_add_review: cls.re_add_run,
            cls.destroy_review: cls.destroy_run,
            cls.forget_review: cls.forget_run,
        }

    @property
    def review_to_run(self) -> "OpBtnLabel":
        return self._review_to_run_map()[self]

    @property
    def normalized_label(self) -> str:
        return (
            self.value.replace(" ", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
        ).lower()


class OpInfoString(StrEnum):
    add_path_info = (
        f"[${ColorVar.dimmed}]Add new targets to the source state. If adding a "
        "directory, it will be recursed in.[/]"
    )
    add_subtitle = f" local path {Chars.right_arrow} chezmoi repo "
    apply_path_info = (
        f"[${ColorVar.dimmed}]Chezmoi will ensure that the path is in the target "
        "state. The command will run without prompting.\n"
        "For targets modified since chezmoi last wrote it. If adding a "
        "directory, it will be recursed in.[/]"
    )
    apply_subtitle = f" chezmoi repo {Chars.right_arrow} path on disk "
    auto_add = (
        f"[${ColorVar.text_success}]{Chars.check_mark} Chezmoi 'autoadd' is enabled: "
        "paths will be added to the chezmoi repository."
        f"{Chars.check_mark}[/]"
    )
    auto_commit = (
        f"[${ColorVar.text_warning}]{Chars.warning_sign} Chezmoi 'autocommit' is "
        "enabled: paths will be committed to the chezmoi repository "
        f"{Chars.warning_sign}[/]"
    )
    auto_push = (
        f"[${ColorVar.text_error}]{Chars.warning_sign} Chezmoi 'autopush' is enabled: "
        "the updated chezmoi repository will be pushed to the remote (origin) "
        f"{Chars.warning_sign}[/]"
    )
    destroy_path_info = (
        f"[${ColorVar.text_error}]Permanently remove the path from disk and chezmoi.\n"
        "MAKE SURE YOU HAVE A BACKUP![/]"
    )
    destroy_subtitle = (
        f"[${ColorVar.text_error}]{Chars.x_mark} delete on disk and in chezmoi repo "
        f"[${ColorVar.text_error}]{Chars.x_mark}[/]"
    )
    dry_run_notice = (
        "Ready to run command with --dry-run flag, no changes will be made to the "
        "chezmoi repository, the paths below will be unaffected."
    )
    forget_path_info = (
        f"[${ColorVar.dimmed}] Remove from the source state, i.e. stop managing them "
        "[/]"
    )
    forget_subtitle = f" leave on disk {Chars.right_arrow} chezmoi repo {Chars.x_mark} "
    live_run_notice = (
        f"[${ColorVar.text_warning}]{Chars.warning_sign} Ready to run command live! "
        f"The paths below will be affected {Chars.warning_sign}[/]"
    )
    ready_to_run_title = " ready to run "
    run_completed_title = " command completed "
    re_add_path_info = (
        f"[${ColorVar.dimmed}]Re-add modified files in the target state, preserving "
        "any encrypted_ attributes. chezmoi will not overwrite templates, and "
        "all entries that are not files are ignored. If adding a directory, it"
        " will be recursed in.[/]"
    )
    re_add_subtitle = f" path on disk {Chars.right_arrow} overwrite chezmoi repo "


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


class PathKind(StrEnum):
    EXISTS_FALSE = auto()
    man_dir_access_denied = auto()
    man_dir_not_exists = auto()
    SYMLINK = auto()
    UNHANDLED = auto()
    unman_dir_access_denied = auto()
    UNMANAGED = auto()


class PwMgrInfo(StrEnum):
    confusing = (
        "Check your package manager which implementation is used as there are"
        " confusingly similar named packages."
    )
    fully_open_source = (
        "Fully open source and auditable worldwide. No third party trust"
        " required. But beware of your supply chain: package manager, certificate"
        " authority, maintainers reputation, etc."
    )
    info_warning = (
        f"[${ColorVar.text_warning}]{Chars.warning_sign} The additional info is "
        "provided but may not be up-to-date or correct. Please contribute to improve "
        f"this.{Chars.warning_sign}[/]"
    )
    not_documented = "Not yet documented in chezmoi mousse."
    not_open_source = (
        "Not open source, cannot be audited but it's ok if you trust this third"
        " party to handle your secrets securely and cannot access them."
    )
    source_available = (
        "The code is publicly available. No third party trust required. But"
        " beware of your supply chain: package manager, certificate authority,"
        " maintainers reputation and so on."
    )


class RichLogName(StrEnum):
    app_logger = auto()
    cmd_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    memory_usage_logger = auto()


class SectionLabel(StrEnum):
    added_managed_paths = "Added managed paths"
    cat_config_output = "Cat Config Output"
    changed_paths = "Changed Paths"
    changed_status_paths = "Changed status paths"
    chezmoi_cat_output = "Chezmoi Cat output"
    command_outputs = "Command Output"
    debug_log = " Debug Log "
    dest_dir = "Destination Directory"
    dest_dir_diff = "This is the root of the chezmoi repository and never has a status"
    diagram = "Chezmoi Diagram"
    doctor_output = "Doctor Output"
    dom_nodes = " DOM Nodes "
    full_cmd = "Full Command"
    ignored_output = "Ignored Output"
    managed_dir = "Managed Directory"
    managed_file = "Managed File"
    managed_no_status = "The path is managed but has no status for this context"
    memory_usage = " Memory Usage "
    n_dir = "Managed directory which contains nested status paths"
    no_managed_paths = "No managed paths yet"
    no_status_paths = "No paths with a status"
    not_set = "Not Set"
    password_managers = "Password Manager Information"
    paths_with_status = "Paths with Status"
    project_description = "Project Description"
    project_link = "Project Link"
    pw_mgr_additional_info = "Additional Info"
    read_file_output = "Read file from disk output"
    removed_managed_paths = "Removed managed paths"
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"
    template_data_output = "Chezmoi Data Output"
    test_paths = " Test Paths "
    unmanaged_dir = "Unmanaged Directory"
    unmanaged_file = "Unmanaged File"


class StaticString(StrEnum):
    click_path_with_status = "<- click a path with a status to see its diff"
    click_file_for_contents = "<- Click a file path to see its contents"


class StatusCode(StrEnum):
    Added = "A"
    Deleted = "D"
    Modified = "M"
    Run = "R"
    Space = " "

    # Fake status code for internal use in the ManagedTree, not returned by chezmoi
    # Used to create the color and to determine if the dir should be displayed or not.
    N_DIR = auto()


class SwitchLabel(StrEnum):
    # Apply and ReAdd Tab
    show_unchanged = "Show unchanged paths"
    show_unmanaged = "Show unmanaged children"
    expand_all = "Expand all dirs"

    # Add Tab
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

    @classmethod  # TODO: avoid class methods in Enum classes
    def main_tabs(cls) -> tuple["TabLabel", ...]:
        return (cls.apply, cls.re_add, cls.add, cls.logs, cls.config, cls.debug)


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


##############################################
# Enums for the chezmoi command construction #
##############################################s


class ChezmoiGitArgs(Enum):
    # args for 'chezmoi git'
    option_terminator = "--"  # option terminator
    global_args = ("--no-pager", "--no-advice")
    default_args = (option_terminator,) + global_args
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
    git_log = default_args + ("log",) + git_log_args
    git_remote = default_args + ("remote", verbose)


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
    git_log = ("git",) + ChezmoiGitArgs.git_log.value
    git_remote = ("git",) + ChezmoiGitArgs.git_remote.value
    ignored = ("ignored",)
    managed_dirs = ("managed", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    managed_files = ("managed", VerbArgs.path_style_absolute, VerbArgs.include_files)
    source_path = ("source-path",)
    status_dirs = ("status", VerbArgs.path_style_absolute, VerbArgs.include_dirs)
    status_files = ("status", VerbArgs.path_style_absolute, VerbArgs.include_files)
    template_data = ("data", VerbArgs.format_json)

    @classmethod
    def splash_only_commands(cls) -> tuple["ReadCmd", ...]:
        # TODO: create function to re-run the loading screen
        return (cls.cat_config, cls.doctor, cls.git_remote, cls.ignored)

    @classmethod
    def json_parsable_commands(cls) -> tuple["ReadCmd", ...]:
        return (cls.dump_config, cls.template_data)

    @classmethod
    def managed_commands(cls) -> tuple["ReadCmd", ...]:
        return (cls.managed_dirs, cls.managed_files, cls.status_dirs, cls.status_files)

    @classmethod
    def grouped_commands_count(cls) -> int:
        return len(
            cls.json_parsable_commands()
            + cls.managed_commands()
            + cls.splash_only_commands()
        )


class WriteCmd(Enum):
    add = ("add",)
    apply = ("apply",)
    destroy = ("destroy",)
    forget = ("forget",)
    re_add = ("re-add",)
