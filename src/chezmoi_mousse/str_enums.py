from enum import Enum, StrEnum, auto
from functools import cached_property
from typing import Self

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
    "ReactiveVar",
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

    # Run chezmoi command buttons
    chezmoi_add = "chezmoi add"
    chezmoi_apply = "chezmoi apply"
    chezmoi_re_add = "chezmoi re-add"
    chezmoi_forget = "chezmoi forget"
    chezmoi_destroy = "chezmoi destroy"

    # Tab buttons for content switcher within a main tab
    app_log = "Application"
    cmd_log = "Chezmoi-Commands"

    # Flat button labels
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    env_vars = "Env Vars"
    git_config = "Git Config"
    ignored = "Ignored"
    template_data = "Template Data"
    test_paths = "Test Paths"

    # Triggers chezmoi command labels
    refresh_trees = "Refresh Trees"
    reload = "Reload"

    # Debug tab buttons
    colors = "Colors"
    create_diffs = "Create Diffs"
    create_paths = "Create Test Paths"
    list_test_paths = "List Test Paths"
    log_memory = "Log Memory Usage"
    remove_paths = "Remove Test Paths"

    # Other
    cancel = "Cancel"
    close = "Close"

    @property
    def pane_id(self) -> str:
        return f"{self.name}_pane_id"


class Chars(StrEnum):
    burger = "\u2261"  # IDENTICAL TO
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE
    radio_button = "\u2b24"  # MEDIUM BLACK CIRCLE


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

    @property
    def btn_label(self) -> str:
        return f"{self.name.replace('_', '-')}"

    @property
    def prompt_item(self) -> str:
        return f"{self.name.replace('_', '-')}"

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
    diff = auto()
    diff_reverse = auto()
    doctor = auto()
    dom_nodes = auto()
    env_vars = auto()
    flat_buttons = auto()
    git_config = auto()
    git_ignored = auto()
    git_log = auto()
    left_side = auto()
    middle = auto()
    prompt_buttons = auto()
    right_side = auto()
    operate_buttons = auto()
    template_data = auto()
    test_paths_view = auto()

    @property
    def container_id(self) -> str:
        return f"{self}_id"


class LabelStr(StrEnum):
    # Config tab
    doctor_output = "Doctor Output"
    cat_config_output = "Cat Config Output"
    ignored_output = "Ignored Output"
    template_data_output = "Chezmoi Data Output"
    chezmoi_git_config = "Chezmoi Git Config"
    diagram = "Chezmoi Diagram"

    # Debug tab
    test_paths = " Test Paths "
    debug_log = "Debug Log"
    dom_nodes = "DOM Nodes"
    env_vars = "Environment Variables"
    colors = "Colors from ColorVar StrEnum class"

    # Operate tab MainSectionLabel text
    dest_dir = "Destination Directory"
    un_man_file = "Un-managed File"
    un_man_dir = "Un-managed Directory"
    un_wanted_dir = f"{un_man_dir} (matches un-wanted)"
    un_wanted_file = f"{un_man_file} (matches un-wanted)"

    _has_no_status = "has no status"
    _has_status = "has a status"
    _nested_sp = "nested status paths"

    real_status_dir = f"Managed Directory ({_has_status})"
    man_d_no_nested_status = f"Managed Directory ({_has_no_status}, has {_nested_sp})"
    man_dir_no_status = f"Managed Directory ({_has_no_status})"
    space_file = f"Managed File ({_has_no_status})"
    status_file = f"Managed File ({_has_status})"

    # Operate tab FlatSectionLabel
    read_file_output = "Read file from disk output"
    select_path_contents = "<- Select a file path to view its contents."
    select_path_diff = "<- Select a path with a status to view its diff."
    select_path_git_log = "<- Select a managed path to see the chezmoi git log."
    no_git_log = "No git log available for this path."

    # Operate tab radio buttons
    radio_contents = "Contents View"
    radio_diff = "Diff View"
    radio_diff_reverse = "Diff Reverse View"
    radio_git_log = "Git Log View"

    # Operate tab Switch labels
    expand_managed = "Expand Managed"
    show_unchanged = "Show Unchanged"
    show_unmanaged = "Show Unmanaged"
    show_unwanted = "Show Unwanted"

    # Operate tab PathInfo labels
    # directories
    d_is_managed = "Directory is managed"
    d_un_wanted = "Directory matches un-wanted filter"
    d_exists = "Directory exists on disk"
    d_has_status = "Directory has a status"
    d_has_nested_status = "Directory has nested status paths"
    d_has_nested_managed = "Directory has nested managed paths"
    # files
    f_is_managed = "File is managed"
    f_has_status = "File has a status"
    f_exists = "File exists on disk"
    f_un_wanted = "File matches un-wanted filter"

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
    node_data = auto()


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

    DA = "DA"  # Target deleted locally; apply will create/restore target file.
    DD = "DD"  # NOTE: probably impossible status pair
    DM = "DM"  # Target deleted locally; apply will create target from source.
    DS = "DS"  # Target deleted locally; no target apply action required.

    MA = "MA"  # Target modified without chezmoi edit; apply treats path as addition.
    MD = "MD"  # Target modified without chezmoi edit; apply deletes target per rules.
    MM = "MM"  # Target modified without chezmoi edit; apply will modify target.
    MS = "MS"  # Target modified without chezmoi edit; no target apply action required.

    SA = "SA"  # Applied target missing; apply will create/restore target file.
    SD = "SD"  # Applied target clean; apply will delete target per source rules.
    SM = "SM"  # Applied target clean; apply will modify target from source updates.

    @cached_property
    def pretty_cmd(self) -> str:
        return f"chezmoi {self.value[0]}"


class Tcss(StrEnum):
    # Operation tabs
    operate_pane = auto()
    operations_left = auto()
    operations_middle = auto()
    operations_right = auto()
    dest_dir_button = auto()
    managed_tree = auto()
    switch_with_label = auto()
    switches_vert_group = auto()

    # Other
    added = auto()
    changed = auto()
    cmd_output = auto()
    context = auto()
    flat_button = auto()
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
    unhandled = auto()


class TreeName(StrEnum):
    """
    iu: include unchanged
    xpd: expanded

    status trees: never include unchanged
    managed trees: always include unchanged
    """

    # the status trees include managed paths with a status or meta status
    managed_only_sp = auto()  # base dict data
    managed_only_sp_xpd = auto()
    # the man trees includes all managed paths, with or without a status or meta status
    managed_all_mp = auto()  # base dict data
    managed_all_mp_xpd = auto()
    # trees including unmanaged paths without unwanted paths
    un_man_plus_sp = auto()  # base dict data
    un_man_plus_sp_xpd = auto()
    un_man_plus_amp = auto()  # base dict data
    un_man_plus_amp_xpd = auto()
    # trees including any unmanaged path, including unwanted paths
    un_wanted_plus_sp = auto()  # base dict data
    un_wanted_plus_sp_xpd = auto()
    un_wanted_plus_amp = auto()  # base dict data
    un_wanted_plus_amp_xpd = auto()

    @classmethod
    def managed_trees(cls) -> tuple[Self, ...]:
        return (
            cls(cls.managed_only_sp_xpd),
            cls(cls.managed_only_sp),
            cls(cls.managed_all_mp),
            cls(cls.managed_all_mp_xpd),
        )


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
    dry_run_arg = "--dry-run=true"
    verbose_arg = "--verbose"

    @property
    def dry_run(self) -> tuple[str, ...]:
        return (
            *self.global_defaults.value,
            self.dry_run_arg.value,
            self.verbose_arg.value,
        )


class _VerbArgs(StrEnum):
    format_json = "--format=json"
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadCmd(Enum):
    cat = (
        *GlobalArgs.global_defaults.value,
        "cat",
    )
    cat_config = (
        *GlobalArgs.global_defaults.value,
        "cat-config",
    )
    diff = (
        *GlobalArgs.global_defaults.value,
        "diff",
    )
    diff_reverse = (*GlobalArgs.global_defaults.value, "diff", _VerbArgs.reverse)
    doctor = (
        *GlobalArgs.global_defaults.value,
        "doctor",
    )
    dump_config = (
        *GlobalArgs.global_defaults.value,
        "dump-config",
        _VerbArgs.format_json,
    )
    git_dir = (*GlobalArgs.global_defaults.value, "git", *_ChezmoiGitArgs.git_dir.value)
    git_log = (*GlobalArgs.global_defaults.value, "git", *_ChezmoiGitArgs.git_log.value)
    git_remote = (
        *GlobalArgs.global_defaults.value,
        "git",
        *_ChezmoiGitArgs.git_remote.value,
    )
    ignored = (
        *GlobalArgs.global_defaults.value,
        "ignored",
    )
    managed_dirs = (
        *GlobalArgs.global_defaults.value,
        "managed",
        _VerbArgs.path_style_absolute,
        _VerbArgs.include_dirs,
    )
    managed_files = (
        *GlobalArgs.global_defaults.value,
        "managed",
        _VerbArgs.path_style_absolute,
        _VerbArgs.include_files,
    )
    source_path = (
        *GlobalArgs.global_defaults.value,
        "source-path",
    )
    status_dirs = (
        *GlobalArgs.global_defaults.value,
        "status",
        _VerbArgs.path_style_absolute,
        _VerbArgs.include_dirs,
    )
    status_files = (
        *GlobalArgs.global_defaults.value,
        "status",
        _VerbArgs.path_style_absolute,
        _VerbArgs.include_files,
    )
    unmanaged_dirs = (
        *GlobalArgs.global_defaults.value,
        "unmanaged",
        _VerbArgs.path_style_absolute,
        _VerbArgs.include_dirs,
    )
    unmanaged_files = (
        *GlobalArgs.global_defaults.value,
        "unmanaged",
        _VerbArgs.path_style_absolute,
        _VerbArgs.include_files,
    )
    template_data = (*GlobalArgs.global_defaults.value, "data", _VerbArgs.format_json)

    @cached_property
    def pretty_cmd(self) -> str:
        ugly_args: tuple[str, ...] = (
            *GlobalArgs.global_defaults.value,
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


class WriteVerb(StrEnum):
    init = "init"
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    re_add = "re-add"


class WriteCmd(Enum):
    init = (
        *GlobalArgs.global_defaults.value,
        WriteVerb.init,
    )
    add = (
        *GlobalArgs.global_defaults.value,
        WriteVerb.add,
    )
    apply = (
        *GlobalArgs.global_defaults.value,
        WriteVerb.apply,
    )
    destroy = (
        *GlobalArgs.global_defaults.value,
        WriteVerb.destroy,
    )
    forget = (
        *GlobalArgs.global_defaults.value,
        WriteVerb.forget,
    )
    re_add = (
        *GlobalArgs.global_defaults.value,
        WriteVerb.re_add,
    )
    dry_init = (*GlobalArgs.global_defaults.dry_run, WriteVerb.init)
    dry_add = (*GlobalArgs.global_defaults.dry_run, WriteVerb.add)
    dry_apply = (*GlobalArgs.global_defaults.dry_run, WriteVerb.apply)
    dry_destroy = (*GlobalArgs.global_defaults.dry_run, WriteVerb.destroy)
    dry_forget = (*GlobalArgs.global_defaults.dry_run, WriteVerb.forget)
    dry_re_add = (*GlobalArgs.global_defaults.dry_run, WriteVerb.re_add)

    @cached_property
    def pretty_cmd(self) -> str:
        ugly_args: tuple[str, ...] = (*GlobalArgs.global_defaults.value,)
        verb_str = " ".join(a for a in self.value if a not in ugly_args)
        if "git" in verb_str and verb_str.count("--") == 1:
            # remove the option terminator
            verb_str = verb_str.replace(" --", "")
        return f"chezmoi {verb_str}"

    @classmethod
    def dry_cmds(cls) -> tuple[Self, ...]:
        return (
            cls(cls.dry_init),
            cls(cls.dry_add),
            cls(cls.dry_apply),
            cls(cls.dry_destroy),
            cls(cls.dry_forget),
            cls(cls.dry_re_add),
        )
