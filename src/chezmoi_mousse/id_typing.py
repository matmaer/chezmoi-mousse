from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Any

from chezmoi_mousse.constants import Chars, Location, TabStr, TreeStr, ViewStr

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
    refresh_doctor_data = "Re-run 'chezmoi doctor' command (refresh data)"


@dataclass(frozen=True)
class SwitchData:
    label: str
    tooltip: str


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


@dataclass
class PwMgrData:
    doctor_check: str
    description: str
    link: str
    doctor_message: str | None = None


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
    def __init__(self, tab_name: TabStr) -> None:
        self.log_id = f"{tab_name}_log"
        self.log_qid = f"#{self.log_id}"
        self.switches_slider_id = f"{tab_name}_switches_slider"
        self.switches_slider_qid = f"#{self.switches_slider_id}"
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

    def switch_horizontal_id(
        self, switch_enum: Switches, location: Location
    ) -> str:
        return (
            f"{self.tab_name}_{switch_enum.name}_switch_horizontal_{location}"
        )

    def switch_horizontal_qid(
        self, switch_enum: Switches, location: Location
    ) -> str:
        return f"#{self.switch_horizontal_id(switch_enum, location)}"

    def switch_id(self, switch_enum: Switches) -> str:
        return f"{self.tab_name}_{switch_enum.name}_switch"

    def switch_qid(self, switch_enum: Switches) -> str:
        return f"#{self.switch_id(switch_enum)}"

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
