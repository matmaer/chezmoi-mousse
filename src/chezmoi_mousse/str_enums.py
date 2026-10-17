from enum import Enum, StrEnum, auto
from functools import cached_property

__all__ = [
    "BindingAction",
    "BindingDescription",
    "BtnLabel",
    "Chars",
    "ChezmoiPrompts",
    "ColorVar",
    "ContainerName",
    "LabelStr",
    "LogStr",
    "PathFilters",
    "ProblemChars",
    "ReadCmd",
    "RichLogName",
    "StatusCode",
    "Tcss",
    "TreeName",
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
    enable_live_run = "Enable live run"
    switch_to_dry_run = "Switch to dry run"


class BtnLabel(StrEnum):
    # Main tabs
    operate = "Operate"
    config = "Config"
    logs = "Logs"
    debug = "Debug"

    # Tab buttons for content switcher within a main tab
    app_log = "Application"
    cmd_log = "Chezmoi-Commands"

    # Flat button labels
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    dump_config = "Config Dump"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    env_vars = "Env Vars"
    ignored = "Ignored"
    template_data = "Template Data"
    test_paths = "Test Paths"

    # Debug tab buttons
    colors = "Colors"
    create_diffs = "Create Diffs"
    create_paths = "Create Test Paths"
    list_test_paths = "List Test Paths"
    log_memory = "Log Memory Usage"
    remove_paths = "Remove Test Paths"

    # Run chezmoi command buttons
    chezmoi_add = "chezmoi add"
    chezmoi_apply = "chezmoi apply"
    chezmoi_re_add = "chezmoi re-add"
    chezmoi_forget = "chezmoi forget"
    chezmoi_destroy = "chezmoi destroy"
    # Operate modal
    cancel = "Cancel"
    close = "Close"

    @property
    def pane_id(self) -> str:
        return f"{self.name}_pane_id"

    @property
    def run_label(self) -> str:  # Operate modal
        if not self.name.startswith("chezmoi_"):
            raise AttributeError(f"run_label not available for {self}")
        return f"Run interactive {self.value}"

    @property
    def dry_cmd(self) -> "ReadCmd":  # Operate modal
        if not self.name.startswith("chezmoi_"):
            raise AttributeError(f"run_label not available for {self}")
        map = {
            BtnLabel.chezmoi_add: ReadCmd.dry_add,
            BtnLabel.chezmoi_apply: ReadCmd.dry_apply,
            BtnLabel.chezmoi_re_add: ReadCmd.dry_re_add,
            BtnLabel.chezmoi_forget: ReadCmd.dry_forget,
            BtnLabel.chezmoi_destroy: ReadCmd.dry_destroy,
        }
        return map[self]


class Chars(StrEnum):
    bullet = "\u2022"  # BULLET
    burger = "\u2261"  # IDENTICAL TO
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    radio_button = "\u2b24"  # MEDIUM BLACK CIRCLE
    refresh = "\u21bb"  # CLOCKWISE OPEN CIRCLE ARROW
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE


class ChezmoiPrompts(Enum):
    # each member its name corresponds to a chezmoi prompt item and the member its value
    # corresponds to the value we send to the chezmoi process
    all = "a"
    diff = "d"
    edit = "e"
    get = "g"
    no = "n"
    no_to_all = "N"
    quit = "q"
    save = "s"
    yes = "y"

    @cached_property
    def prompt_item(self) -> str:
        return self.name.replace("_", "-")

    @property
    def reply(self) -> str:
        return self.value


class ColorVar(StrEnum):
    error_muted = "error-muted"

    text = "text"
    foreground_darken_2 = "foreground-darken-2"
    foreground_darken_3 = "foreground-darken-3"
    secondary = "secondary"

    text_accent = "text-accent"
    accent_darken_3 = "accent-darken-3"

    error = "error"
    text_error = "text-error"

    text_primary = "text-primary"
    primary_darken_1 = "primary-darken-1"

    success = "success"
    text_success = "text-success"

    warning = "warning"
    text_warning = "text-warning"
    warning_lighten_3 = "warning-lighten-3"


class ContainerName(StrEnum):
    cat_config = auto()
    color_vars = auto()
    contents = auto()
    cmd_log = auto()
    debug_log = auto()
    diagram = auto()
    dump_config = auto()
    diff = auto()
    diff_reverse = auto()
    doctor = auto()
    dom_nodes = auto()
    env_vars = auto()
    flat_buttons = auto()
    git_ignored = auto()
    git_log = auto()
    left_side = auto()
    prompt_buttons = auto()
    operate_buttons = auto()
    template_data = auto()
    test_paths_view = auto()


class LabelStr(StrEnum):
    # Config tab
    cat_config_output = "Cat Config Output"
    diagram = "Chezmoi Diagram"
    doctor_output = "Doctor Output"
    dump_config_output = "Dump Config Output"
    ignored_output = "Ignored Output"
    template_data_output = "Chezmoi Data Output"

    # Debug tab
    test_paths = " Test Paths "
    debug_log = "Debug Log"
    dom_nodes = "DOM Nodes"
    env_vars = "Environment Variables"
    colors = "Colors from ColorVar StrEnum class"

    # Operate tab MainSectionLabel text
    dest_dir = "Destination Directory"
    managed_dir = "Managed Directory"
    managed_file = "Managed File"
    un_man_file = "Un-managed File"
    un_man_dir = "Un-managed Directory"

    # Operate tab PathInfo labels
    has_nested_status = "Has nested status paths"
    has_nested_managed = "Has nested managed paths"
    has_nested_un_man = "Has nested un-managed paths"
    path_exists = "Exists on disk"
    path_has_status = "Has a status"
    path_un_wanted = "Matches un-wanted filter"

    # Operate tab FlatSectionLabel
    read_file_output = "Read file from disk output"
    select_file_path = "<- Select a file path to view its contents."
    select_status_path = "<- Select a path with a status to view its diff."
    select_git_log_path = "<- Select a managed path to see the chezmoi git log."

    # Operate tab radio buttons
    radio_contents = "Contents View"
    radio_diff = "Diff View"
    radio_diff_reverse = "Diff Reverse View"
    radio_git_log = "Git Log View"
    radio_path_view = "Path Info"

    # Operate tab Switch labels
    expand_managed = "Expand Managed"
    show_unchanged = "Show Unchanged"
    show_unmanaged = "Show Unmanaged"
    show_unwanted = "Show Unwanted"

    # other
    context = "Context"
    not_set = "Not Set"

    # CommandResult collapsible sections
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"

    # Changed paths
    # added_managed_paths = "Added managed paths" # noqa: ERA001
    # changed_paths = "Changed Paths" # noqa: ERA001
    # changed_status_paths = "Changed status paths" # noqa: ERA001
    # removed_managed_paths = "Removed managed paths" # noqa: ERA001


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

    # Splash log strings, suffixes
    checked = auto()
    decoded = auto()
    missing = auto()
    present = auto()
    reports = auto()
    # skipped = auto() # noqa: ERA001
    success = auto()
    trigger = auto()

    # splash log string suffixes and pretty verb args
    on_managed_dirs = "on managed dirs"
    on_managed_files = "on managed files"


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


class RichLogName(StrEnum):
    app_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    env_var_logger = auto()
    memory_usage_logger = auto()


class StatusCode(StrEnum):
    """
    Status pairs used for coloring and parsing, the comments are potentially not 100%
    correct and are corrected when new, uncounted for scenarios emerge or when it's
    plain wrong.
    """

    # Possible chezmoi status codes in a column
    A = auto()
    D = auto()
    M = auto()
    R = auto()
    S = "\x20"  # single space

    # --- Status Pairs ---
    # TODO: We currently completely skip any status R, so currently omitted here
    # NOTE: The first column can only contain M, D or a space, so not applicable

    # Target deleted locally; apply will create/restore target file.
    # Is a no-op when running chezmoi re-add
    DA = "DA"
    DD = "DD"  # NOTE: probably impossible status pair
    DM = "DM"  # Target deleted locally; apply will create target from source.
    DS = "D\x20"  # Target deleted locally; no target apply action required.

    MA = "MA"  # Target modified outside chezmoi; apply treats path as addition.
    MD = "MD"  # Target modified outside chezmoi; apply deletes target per rules.
    MM = "MM"  # Target modified outside chezmoi; apply will modify target.
    MS = "M\x20"  # Target modified outside chezmoi; no target apply action required.

    SA = "\x20A"  # Applied target missing; apply will create/restore target file.
    SD = "\x20D"  # Applied target clean; apply will delete target per source rules.
    SM = "\x20M"  # Applied target clean; apply will modify target from source updates.


class Tcss(StrEnum):
    # Operation tabs
    operate_pane = auto()
    dest_dir_button = auto()
    switch_with_label = auto()
    switches_vert_group = auto()

    # Other
    added = auto()
    cmd_output = auto()
    context = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    full_cmd = auto()
    info = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    live_run_color = auto()
    op_btn_group = auto()
    operate_button = auto()
    prompt_btn_group = auto()
    prompt_button = auto()
    refresh_button = auto()
    removed = auto()
    single_button_vertical = auto()
    splash_log = auto()
    tab_button = auto()
    tree_header = auto()
    true_label = auto()
    false_label = auto()


class TreeName(StrEnum):
    """
    iu: include unchanged
    xpd: expanded

    status trees: never include unchanged
    managed trees: always include unchanged
    """

    # the status trees include managed paths with a status or meta status
    managed_sp = auto()  # base dict data
    managed_sp_xpd = auto()
    # the man trees includes all managed paths, with or without a status or meta status
    managed_amp = auto()  # base dict data
    managed_amp_xpd = auto()
    # trees including unmanaged paths without unwanted paths
    wanted_plus_amp = auto()  # base dict data
    wanted_plus_amp_xpd = auto()
    wanted_plus_sp = auto()  # base dict data
    wanted_plus_sp_xpd = auto()
    # trees including any unmanaged path, including unwanted paths
    un_wanted_plus_amp = auto()  # base dict data
    un_wanted_plus_amp_xpd = auto()
    un_wanted_plus_sp = auto()  # base dict data
    un_wanted_plus_sp_xpd = auto()

    @property
    def is_xpd_tree(self) -> bool:
        return self.name.endswith("_xpd")

    @property
    def is_managed_tree(self) -> bool:
        return self.name.startswith("managed_")

    @property
    def is_wanted_tree(self) -> bool:
        return self.name.startswith("wanted_")


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
        "--format=%ar%x1f%cn%x1f%B%x00",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    )
    git_dir = (_option_terminator, *global_args, "rev-parse", "--git-dir")
    git_log = (_option_terminator, *global_args, "log", *git_log_args)
    git_remote = (_option_terminator, *global_args, "remote", verbose)


class _GlobalArgs(Enum):
    _global_defaults = (
        "--color=off",
        "--keep-going=false",
        "--mode=file",
        "--no-pager=true",
        "--progress=false",
        "--use-builtin-diff=true",
        "--use-builtin-git=true",
        "--no-tty=true",
    )
    _force_true = "--force=true"
    _force_false = "--force=false"
    _interactive_false = "--interactive=false"
    _interactive_true = "--interactive=true"
    non_interactive = (
        *_global_defaults,
        _interactive_false,
        _force_true,
    )
    # --no-tty=true makes chezmoi prompt over stdin/stdout instead of /dev/tty
    interactive = (
        *_global_defaults,
        _interactive_true,
        _force_false,
    )
    dry_run_arg = "--dry-run=true"
    verbose_arg = "--verbose"


class _VerbArgs(StrEnum):
    format_json = "--format=json"
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    prompt = "--prompt=true"
    reverse = "--reverse"


class _WriteVerb(StrEnum):
    init = "init"
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    re_add = "re-add"


class ReadCmd(Enum):
    cat = (
        *_GlobalArgs.non_interactive.value,
        "cat",
    )
    cat_config = (
        *_GlobalArgs.non_interactive.value,
        "cat-config",
    )
    diff = (
        *_GlobalArgs.non_interactive.value,
        "diff",
    )
    diff_reverse = (
        *_GlobalArgs.non_interactive.value,
        "diff",
        _VerbArgs.reverse.value,
    )
    doctor = (
        *_GlobalArgs.non_interactive.value,
        "doctor",
    )
    dump_config = (
        *_GlobalArgs.non_interactive.value,
        "dump-config",
        _VerbArgs.format_json.value,
    )
    git_dir = (
        *_GlobalArgs.non_interactive.value,
        "git",
        *_ChezmoiGitArgs.git_dir.value,
    )
    git_log = (
        *_GlobalArgs.non_interactive.value,
        "git",
        *_ChezmoiGitArgs.git_log.value,
    )
    git_remote = (
        *_GlobalArgs.non_interactive.value,
        "git",
        *_ChezmoiGitArgs.git_remote.value,
    )
    ignored = (
        *_GlobalArgs.non_interactive.value,
        "ignored",
    )
    managed_dirs = (
        *_GlobalArgs.non_interactive.value,
        "managed",
        _VerbArgs.path_style_absolute.value,
        _VerbArgs.include_dirs.value,
    )
    managed_files = (
        *_GlobalArgs.non_interactive.value,
        "managed",
        _VerbArgs.path_style_absolute.value,
        _VerbArgs.include_files.value,
    )
    source_path = (
        *_GlobalArgs.non_interactive.value,
        "source-path",
    )
    status_dirs = (
        *_GlobalArgs.non_interactive.value,
        "status",
        _VerbArgs.path_style_absolute.value,
        _VerbArgs.include_dirs.value,
    )
    status_files = (
        *_GlobalArgs.non_interactive.value,
        "status",
        _VerbArgs.path_style_absolute.value,
        _VerbArgs.include_files.value,
    )
    unmanaged_dirs = (
        *_GlobalArgs.non_interactive.value,
        "unmanaged",
        _VerbArgs.path_style_absolute.value,
        _VerbArgs.include_dirs.value,
    )
    unmanaged_files = (
        *_GlobalArgs.non_interactive.value,
        "unmanaged",
        _VerbArgs.path_style_absolute.value,
        _VerbArgs.include_files.value,
    )
    template_data = (
        *_GlobalArgs.non_interactive.value,
        "data",
        _VerbArgs.format_json.value,
    )

    dry_add = (
        *_GlobalArgs.non_interactive.value,
        _GlobalArgs.dry_run_arg.value,
        _GlobalArgs.verbose_arg.value,
        _WriteVerb.add.value,
    )
    dry_apply = (
        *_GlobalArgs.non_interactive.value,
        _GlobalArgs.dry_run_arg.value,
        _GlobalArgs.verbose_arg.value,
        _WriteVerb.apply.value,
    )
    dry_destroy = (
        *_GlobalArgs.non_interactive.value,
        _GlobalArgs.dry_run_arg.value,
        _GlobalArgs.verbose_arg.value,
        _WriteVerb.destroy.value,
    )
    dry_forget = (
        *_GlobalArgs.non_interactive.value,
        _GlobalArgs.dry_run_arg.value,
        _GlobalArgs.verbose_arg.value,
        _WriteVerb.forget.value,
    )
    dry_re_add = (
        *_GlobalArgs.non_interactive.value,
        _GlobalArgs.dry_run_arg.value,
        _GlobalArgs.verbose_arg.value,
        _WriteVerb.re_add.value,
    )

    @cached_property
    def pretty_cmd(self) -> str:
        ugly_args: tuple[str, ...] = (
            *_GlobalArgs.non_interactive.value,
            *_ChezmoiGitArgs.global_args.value,
            *_ChezmoiGitArgs.git_log_args.value,
            _ChezmoiGitArgs.verbose.value,
            *(
                _VerbArgs.format_json.value,
                _VerbArgs.path_style_absolute.value,
            ),
        )
        verb_str = " ".join(a for a in self.value if a not in ugly_args)
        if "git" in verb_str and verb_str.count("--") == 1:
            # remove the option terminator
            verb_str = verb_str.replace(" --", "")
        return f"chezmoi {verb_str}"

    @cached_property
    def pretty_splash_cmd(self) -> str:
        return self.pretty_cmd.replace("--include=", "")

    @property
    def write_btn_label(self) -> BtnLabel:
        map = {
            ReadCmd.dry_add: BtnLabel.chezmoi_add,
            ReadCmd.dry_apply: BtnLabel.chezmoi_apply,
            ReadCmd.dry_destroy: BtnLabel.chezmoi_destroy,
            ReadCmd.dry_forget: BtnLabel.chezmoi_forget,
            ReadCmd.dry_re_add: BtnLabel.chezmoi_re_add,
        }
        return map[self]

    @property
    def write_cmd(self) -> "WriteCmd":
        map = {
            ReadCmd.dry_add: WriteCmd.add,
            ReadCmd.dry_apply: WriteCmd.apply,
            ReadCmd.dry_destroy: WriteCmd.destroy,
            ReadCmd.dry_forget: WriteCmd.forget,
            ReadCmd.dry_re_add: WriteCmd.re_add,
        }
        return map[self]


class WriteCmd(Enum):
    init = (
        *_GlobalArgs.non_interactive.value,
        _WriteVerb.init.value,
    )
    add = (
        *_GlobalArgs.interactive.value,
        _WriteVerb.add.value,
        _VerbArgs.prompt.value,
    )
    apply = (
        *_GlobalArgs.interactive.value,
        _WriteVerb.apply.value,
    )
    destroy = (
        *_GlobalArgs.interactive.value,
        _WriteVerb.destroy.value,
    )
    forget = (
        *_GlobalArgs.interactive.value,
        _WriteVerb.forget.value,
    )
    re_add = (
        *_GlobalArgs.interactive.value,
        _WriteVerb.re_add.value,
    )

    @cached_property
    def pretty_cmd(self) -> str:
        ugly_args: tuple[str, ...] = (
            *_GlobalArgs.interactive.value,
            *_GlobalArgs.non_interactive.value,
        )
        verb_str = " ".join(a for a in self.value if a not in ugly_args)
        return f"chezmoi {verb_str}"

    @property
    def dry_cmd(self) -> ReadCmd:
        map = {
            WriteCmd.add: ReadCmd.dry_add,
            WriteCmd.apply: ReadCmd.dry_apply,
            WriteCmd.destroy: ReadCmd.dry_destroy,
            WriteCmd.forget: ReadCmd.dry_forget,
            WriteCmd.re_add: ReadCmd.dry_re_add,
        }
        return map[self]

    @property
    def write_btn_label(self) -> BtnLabel:
        map = {
            WriteCmd.add: BtnLabel.chezmoi_add,
            WriteCmd.apply: BtnLabel.chezmoi_apply,
            WriteCmd.destroy: BtnLabel.chezmoi_destroy,
            WriteCmd.forget: BtnLabel.chezmoi_forget,
            WriteCmd.re_add: BtnLabel.chezmoi_re_add,
        }
        return map[self]

    @property
    def write_run_label(self) -> str:
        map = {
            WriteCmd.add: BtnLabel.chezmoi_add.run_label,
            WriteCmd.apply: BtnLabel.chezmoi_apply.run_label,
            WriteCmd.destroy: BtnLabel.chezmoi_destroy.run_label,
            WriteCmd.forget: BtnLabel.chezmoi_forget.run_label,
            WriteCmd.re_add: BtnLabel.chezmoi_re_add.run_label,
        }
        return map[self]
