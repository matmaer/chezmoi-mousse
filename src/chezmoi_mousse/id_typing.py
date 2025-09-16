"""Contains type aliases, dataclasses, enums and the TabIds and Id class to
enable setting widget id's without hardcoded strings or generated the id
dynamically."""

from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chezmoi_mousse.constants import (
    Area,
    Chars,
    OperateBtn,
    ScreenName,
    TabBtn,
    TabName,
    TreeName,
    ViewName,
)

if TYPE_CHECKING:
    from chezmoi_mousse.gui import ChezmoiGUI

type Mro = tuple[type, ...]
type OperateButtons = tuple[OperateBtn, ...]
type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]
type TabButtons = tuple[TabBtn, ...]


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


##############################
# dataclass decorated classes:


@dataclass
class NodeData:
    found: bool
    path: Path
    status: str


@dataclass
class OperateData:
    path: Path | None = None
    operation_executed: bool = False
    tab_name: TabName | None = None
    found: bool | None = None
    button_name: OperateBtn | None = None
    is_file: bool | None = None


@dataclass
class PwMgrData:
    doctor_check: str
    description: str
    link: str
    doctor_message: str | None = None


@dataclass(frozen=True)
class SplashIds:
    animated_fade = "animated_fade"
    loading_screen = "loading_screen"
    splash_log = "splash_log"


@dataclass(frozen=True)
class SwitchData:
    label: str
    tooltip: str


###############
# Enum classes:


class OperateHelp(Enum):
    add = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
    apply = "[$text-primary]Local file (target state) in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    # TODO from chezmoi help: If you want to remove all traces of chezmoi from your system use purge instead. If you want chezmoi to stop managing the file use forget instead.
    # ---> create links for this to the other tabs
    changes_mode_disabled = (
        "Changes mode disabled, operations will dry-run only"
    )
    changes_mode_enabled = "Changes mode enabled, operations will run."
    destroy = (
        "[$text-primary]Remove target from the source state, the destination directory, and the state.[/]",
        "[$text-error]The destroy command permanently removes files both from your home directory and chezmoi's source directory, make sure you have a backup![/]",
    )
    diff_color = (
        "[$text-success]+ green lines will be added[/]",
        "[$text-error]- red lines will be removed[/]",
        f"[dim]{Chars.bullet} dimmed lines for context[/]",
    )
    # TODO chezmoi forget help: "Targets must have entries in the source state. They cannot be externals."
    # -> disable forget button in that case
    forget = "[$text-primary]Remove targets from the source state, i.e. stop managing them.[/]"
    re_add = (
        "[$text-primary]Overwrite the source state with current local file[/]"
    )


class Switches(Enum):
    clone_and_apply = SwitchData(
        "init and apply", ("run chezmoi init with --apply flag.")
    )
    expand_all = SwitchData(
        "expand all dirs",
        (
            "Expand all managed directories. Depending on the unchanged "
            "switch."
        ),
    )
    guess_url = SwitchData(
        "chezmoi guess", ("Submit with `chezmoi --guess-repo-url`.")
    )
    unchanged = SwitchData(
        "show unchanged files",
        (
            "Include files unchanged files which are not found in the "
            "'chezmoi status' output."
        ),
    )
    unmanaged_dirs = SwitchData(
        "show unmanaged dirs",
        (
            "The default (disabled), only shows directories which already "
            "contain managed files. This allows spotting new unmanaged files "
            "in already managed directories. Enable to show all directories "
            "which contain unmanaged files."
        ),
    )
    unwanted = SwitchData(
        "show unwanted paths",
        (
            "Include files and directories considered as 'unwanted' for a "
            "dotfile manager. These include cache, temporary, trash (recycle "
            "bin) and other similar files or directories. For example enable "
            "this to add files to your chezmoi repository which are in a "
            "directory named '.cache'."
        ),
    )


class PwMgrInfo(Enum):
    age_command = PwMgrData(
        doctor_check="age-command",
        description="A simple, modern and secure file encryption tool",
        link="https://github.com/FiloSottile/age",
    )
    bitwarden_command = PwMgrData(
        doctor_check="bitwarden-command",
        description="Bitwarden Password Manager",
        link="https://github.com/bitwarden/cli",
    )
    bitwarden_secrets_command = PwMgrData(
        doctor_check="bitwarden-secrets-command",
        description="Bitwarden Secrets Manager CLI for managing secrets securely.",
        link="https://github.com/bitwarden/bitwarden-secrets",
    )
    doppler_command = PwMgrData(
        doctor_check="doppler-command",
        description="The Doppler CLI for managing secrets, configs, and environment variables.",
        link="https://github.com/DopplerHQ/cli",
    )
    gopass_command = PwMgrData(
        doctor_check="gopass-command",
        description="The slightly more awesome standard unix password manager for teams.",
        link="https://github.com/gopasspw/gopass",
    )
    keeper_command = PwMgrData(
        doctor_check="keeper-command",
        description="An interface to Keeper® Password Manager",
        link="https://github.com/Keeper-Security/Commander",
    )
    keepassxc_command = PwMgrData(
        doctor_check="keepassxc-command",
        description="Cross-platform community-driven port of Keepass password manager",
        link="https://keepassxc.org/",
    )
    lpass_command = PwMgrData(
        doctor_check="lpass-command",
        description="Old LastPass CLI for accessing your LastPass vault.",
        link="https://github.com/lastpass/lastpass-cli",
    )
    pass_command = PwMgrData(
        doctor_check="pass-command",
        description="Stores, retrieves, generates, and synchronizes passwords securely",
        link="https://www.passwordstore.org/",
    )
    pinentry_command = PwMgrData(
        doctor_check="pinentry-command",
        description="Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
        link="https://gnupg.org/related_software/pinentry/",
    )
    rbw_command = PwMgrData(
        doctor_check="rbw-command",
        description="Unofficial Bitwarden CLI",
        link="https://git.tozt.net/rbw",
    )
    vault_command = PwMgrData(
        doctor_check="vault-command",
        description="A tool for managing secrets",
        link="https://vaultproject.io/",
    )


class TabIds:
    def __init__(self, tab_name: TabName) -> None:
        self.switches_slider_id = f"{tab_name}_switches_slider"
        self.switches_slider_qid = f"#{self.switches_slider_id}"
        self.tab_container_id = f"{tab_name}_main_horizontal"
        self.tab_name: TabName = tab_name
        self.tab_pane_id = f"{tab_name}_pane"

    def button_id(self, qid: str = "", *, btn: OperateBtn | TabBtn) -> str:
        suffix = "_op_btn" if isinstance(btn, OperateBtn) else "_tab_btn"
        return f"{qid}{self.tab_name}_{btn.name}{suffix}"

    def buttons_horizontal_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_horizontal"

    def button_vertical_id(self, btn_enum: OperateBtn | TabBtn) -> str:
        return f"{self.tab_name}_{btn_enum.name}_vertical"

    def content_switcher_id(self, qid: str = "", *, area: Area) -> str:
        return f"{qid}{self.tab_name}_{area}_content_switcher"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.tab_name}_{switch.name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.tab_name}_{switch.name}_switch"

    def tab_vertical_id(self, qid: str = "", *, area: Area) -> str:
        return f"{qid}{self.tab_name}_{area}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.tab_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.tab_name}_{view}"


class ScreenIds:
    def __init__(self, screen_name: ScreenName) -> None:
        self.screen_name = screen_name
        self.screen_id = f"{screen_name}_id"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.screen_name}_{view}"


@dataclass(frozen=True)
class Id:
    add: TabIds = TabIds(TabName.add_tab)
    apply: TabIds = TabIds(TabName.apply_tab)
    doctor: TabIds = TabIds(TabName.doctor_tab)
    init: TabIds = TabIds(TabName.init_tab)
    logs: TabIds = TabIds(TabName.log_tab)
    re_add: TabIds = TabIds(TabName.re_add_tab)
    operate_screen: ScreenIds = ScreenIds(ScreenName.operate)
    maximized_screen: ScreenIds = ScreenIds(ScreenName.maximized)
    install_help_screen: ScreenIds = ScreenIds(ScreenName.install_help)
    splash_id = SplashIds()

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
