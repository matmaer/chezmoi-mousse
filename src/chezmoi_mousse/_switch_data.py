from dataclasses import dataclass
from enum import Enum, StrEnum

__all__ = ["Switches"]


class SwitchNameLabel(StrEnum):
    expand_all = "Expand all dirs"
    unchanged = "Show unchanged files"
    unmanaged_dirs = "Show unmanaged dirs"
    unwanted = "Show unwanted paths"


@dataclass(frozen=True, slots=True)
class SwitchData:
    label: str
    switch_name: str
    enabled_tooltip: str
    disabled_tooltip: str | None


class Switches(Enum):

    expand_all = SwitchData(
        label=SwitchNameLabel.expand_all,
        switch_name=SwitchNameLabel.expand_all.name,
        enabled_tooltip='Expand all managed directories. Showing unchanged depending on the "show unchanged files" switch.',
        disabled_tooltip="Switch to Tree to enable this switch.",
    )
    unchanged = SwitchData(
        label=SwitchNameLabel.unchanged,
        switch_name=SwitchNameLabel.unchanged.name,
        enabled_tooltip="Include files unchanged files which are not found in the 'chezmoi status' output.",
        disabled_tooltip=None,
    )
    unmanaged_dirs = SwitchData(
        label=SwitchNameLabel.unmanaged_dirs,
        switch_name=SwitchNameLabel.unmanaged_dirs.name,
        enabled_tooltip="The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
        disabled_tooltip=None,
    )
    unwanted = SwitchData(
        label=SwitchNameLabel.unwanted,
        switch_name=SwitchNameLabel.unwanted.name,
        enabled_tooltip="Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
        disabled_tooltip=None,
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def switch_name(self) -> str:
        return self.value.switch_name

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip

    @property
    def disabled_tooltip(self) -> str | None:
        return self.value.disabled_tooltip
