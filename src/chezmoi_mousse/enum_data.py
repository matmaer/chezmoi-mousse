from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from chezmoi_mousse.named_tuples import PwMgrData, SwitchData
from chezmoi_mousse.str_enums import (
    OpBtnLabel,
    OpInfoString,
    PwMgrInfo,
    SwitchLabel,
    WriteCmd,
)

__all__ = ["OpBtnEnum", "PwMgrEnum", "SwitchEnum"]


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd
    op_info_string: str
    op_info_title: str
    op_info_subtitle: str | None = None
    path_arg: "Path | None" = None


class OpBtnEnum(Enum):
    add_review = OpBtnData(
        label=OpBtnLabel.add_review,
        write_cmd=WriteCmd.add,
        op_info_string=OpInfoString.add_path_info,
        op_info_subtitle=OpInfoString.add_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    add_run = OpBtnData(
        label=OpBtnLabel.add_run,
        write_cmd=WriteCmd.add,
        op_info_string=OpInfoString.add_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    apply_review = OpBtnData(
        label=OpBtnLabel.apply_review,
        write_cmd=WriteCmd.apply,
        op_info_string=OpInfoString.apply_path_info,
        op_info_subtitle=OpInfoString.apply_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    apply_run = OpBtnData(
        label=OpBtnLabel.apply_run,
        write_cmd=WriteCmd.apply,
        op_info_string=OpInfoString.apply_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    destroy_review = OpBtnData(
        label=OpBtnLabel.destroy_review,
        write_cmd=WriteCmd.destroy,
        op_info_string=OpInfoString.destroy_path_info,
        op_info_subtitle=OpInfoString.destroy_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    destroy_run = OpBtnData(
        label=OpBtnLabel.destroy_run,
        write_cmd=WriteCmd.destroy,
        op_info_string=OpInfoString.destroy_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    forget_review = OpBtnData(
        label=OpBtnLabel.forget_review,
        write_cmd=WriteCmd.forget,
        op_info_string=OpInfoString.forget_path_info,
        op_info_subtitle=OpInfoString.forget_subtitle,
        op_info_title=OpInfoString.ready_to_run,
        path_arg=None,
    )
    forget_run = OpBtnData(
        label=OpBtnLabel.forget_run,
        write_cmd=WriteCmd.forget,
        op_info_string=OpInfoString.forget_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    re_add_review = OpBtnData(
        label=OpBtnLabel.re_add_review,
        write_cmd=WriteCmd.re_add,
        op_info_string=OpInfoString.re_add_path_info,
        op_info_subtitle=OpInfoString.re_add_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    re_add_run = OpBtnData(
        label=OpBtnLabel.re_add_run,
        write_cmd=WriteCmd.re_add,
        op_info_string=OpInfoString.re_add_path_info,
        op_info_title=OpInfoString.run_completed,
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def write_cmd(self) -> WriteCmd:
        return self.value.write_cmd

    @property
    def op_info_string(self) -> str:
        return self.value.op_info_string

    @property
    def op_info_subtitle(self) -> str | None:
        return self.value.op_info_subtitle

    @property
    def op_info_title(self) -> str:
        return self.value.op_info_title

    @property
    def path_arg(self) -> "Path | None":
        return self.value.path_arg

    @path_arg.setter
    def path_arg(self, value: "Path | None") -> None:
        self.value.path_arg = value

    @classmethod
    def review_to_run(cls, btn_label: OpBtnLabel) -> "OpBtnEnum":
        _mapping = {
            OpBtnLabel.add_review: cls.add_run,
            OpBtnLabel.apply_review: cls.apply_run,
            OpBtnLabel.destroy_review: cls.destroy_run,
            OpBtnLabel.forget_review: cls.forget_run,
            OpBtnLabel.re_add_review: cls.re_add_run,
        }
        return _mapping[btn_label]

    @classmethod
    def review_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls.add_review,
            cls.apply_review,
            cls.destroy_review,
            cls.forget_review,
            cls.re_add_review,
        }

    @classmethod
    def run_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls.add_run,
            cls.apply_run,
            cls.destroy_run,
            cls.forget_run,
            cls.re_add_run,
        }


class PwMgrEnum(Enum):
    age_command = PwMgrData(
        doctor_check="age-command",
        description="A simple, modern and secure file encryption tool.",
        link="https://github.com/FiloSottile/age",
        info=PwMgrInfo.fully_open_source,
    )
    bitwarden_command = PwMgrData(
        doctor_check="bitwarden-command",
        description="Bitwarden Password Manager",
        link="https://github.com/bitwarden",
        info=PwMgrInfo.source_available,
    )
    bitwarden_secrets_command = PwMgrData(
        doctor_check="bitwarden-secrets-command",
        description="Bitwarden Secrets Manager CLI for managing secrets securely.",
        link="https://github.com/bitwarden",
        info=PwMgrInfo.fully_open_source,
    )
    dashlane_command = PwMgrData(
        doctor_check="dashlane-command",
        description=(
            "Simple and secure access to all your online accounts. At work,"
            " home, and everywhere in between."
        ),
        link="https://github.com/dashlane",
        info=PwMgrInfo.not_open_source,
    )
    doppler_command = PwMgrData(
        doctor_check="doppler-command",
        description=(
            "Doppler is the multi-cloud SecretOps Platform developers and"
            " security teams trust to provide secrets management at enterprise scale."
        ),
        link="https://github.com/dopplerhq",
        info=PwMgrInfo.not_open_source,
    )
    gopass_command = PwMgrData(
        doctor_check="gopass-command",
        description=(
            "The slightly more awesome standard unix password manager for teams."
        ),
        link="https://github.com/gopasspw/gopass",
        info=PwMgrInfo.fully_open_source,
    )
    keeper_command = PwMgrData(
        doctor_check="keeper-command",
        description="An interface to Keeper Password Manager",
        link="https://github.com/Keeper-Security/Commander",
        info=PwMgrInfo.not_open_source,
    )
    keepassxc_command = PwMgrData(
        doctor_check="keepassxc-command",
        description=(
            "Cross-platform community-driven port of Keepass password manager."
        ),
        link="https://keepassxc.org/",
        info=PwMgrInfo.fully_open_source,
    )
    lastpass_command = PwMgrData(
        doctor_check="lastpass-command",
        description="Old LastPass CLI for accessing your LastPass vault.",
        link="https://https://github.com/lastpass",
        info=PwMgrInfo.not_open_source,
    )
    one_password_command = PwMgrData(
        doctor_check="one-password-command",
        description="Secure all sign-ins to every application from any device.",
        link="https://github.com/1Password/for-open-source",
        info=PwMgrInfo.not_open_source,
    )
    pass_command = PwMgrData(
        doctor_check="pass-command",
        description=(
            "Stores, retrieves, generates, and synchronizes passwords securely."
        ),
        link="https://www.passwordstore.org/",
        info=PwMgrInfo.confusing,
    )
    passhole_command = PwMgrData(
        doctor_check="passhole-command",
        description="A secure hole for your passwords (KeePass CLI).",
        link="https://github.com/Evidlo/passhole",
        info=PwMgrInfo.not_open_source,
    )
    pinentry_command = PwMgrData(
        doctor_check="pinentry-command",
        description=(
            "Collection of simple PIN or passphrase entry dialogs which utilize"
            " the Assuan protocol."
        ),
        link="https://gnupg.org/related_software/pinentry/",
        info=PwMgrInfo.fully_open_source,
    )
    rbw_command = PwMgrData(
        doctor_check="rbw-command",
        description="Unofficial Bitwarden.",
        link="https://git.tozt.net/rbw",
        info=PwMgrInfo.not_documented,
    )
    vault_command = PwMgrData(
        doctor_check="vault-command",
        description="A tool for managing secrets.",
        link="https://vaultproject.io/",
        info=PwMgrInfo.not_documented,
    )


class SwitchEnum(Enum):
    # Apply and Re-Add tab
    show_unchanged = SwitchData(
        label=SwitchLabel.show_unchanged,
        enabled_tooltip=(
            "Include unchanged paths, which are not found in the 'chezmoi status' "
            "output."
        ),
    )
    show_unmanaged = SwitchData(
        label=SwitchLabel.show_unmanaged,
        enabled_tooltip=("If enabled, also show unmanaged children."),
    )
    expand_all = SwitchData(
        label=SwitchLabel.expand_all, enabled_tooltip=("Expand all directories.")
    )

    # Add Tab

    show_managed = SwitchData(
        label=SwitchLabel.show_managed,
        enabled_tooltip=("If enabled, also show already managed paths."),
    )
    show_unwanted = SwitchData(
        label=SwitchLabel.show_unwanted,
        enabled_tooltip=(
            "Include files and directories considered as 'unwanted' for a dotfile "
            "manager. These include cache, temporary, trash (recycle bin) and other "
            "similar files or directories."
        ),
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip
