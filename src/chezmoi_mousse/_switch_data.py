from dataclasses import dataclass
from enum import Enum, StrEnum

__all__ = ["Switches"]


class SwitchLabel(StrEnum):
    expand_all = "Expand all dirs"
    unchanged = "Show unchanged files"
    unmanaged_dirs = "Show unmanaged dirs"
    unwanted = "Show unwanted paths"


@dataclass(frozen=True, slots=True)
class SwitchData:
    label: str
    enabled_tooltip: str
    disabled_tooltip: str | None


class Switches(Enum):

    expand_all = SwitchData(
        label=SwitchLabel.expand_all,
        enabled_tooltip='Expand all managed directories. Showing unchanged depending on the "show unchanged files" switch.',
        disabled_tooltip="Switch to Tree to enable this switch.",
    )
    unchanged = SwitchData(
        label=SwitchLabel.unchanged,
        enabled_tooltip="Include files unchanged files which are not found in the 'chezmoi status' output.",
        disabled_tooltip=None,
    )
    unmanaged_dirs = SwitchData(
        label=SwitchLabel.unmanaged_dirs,
        enabled_tooltip="The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
        disabled_tooltip=None,
    )
    unwanted = SwitchData(
        label=SwitchLabel.unwanted,
        enabled_tooltip="Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
        disabled_tooltip=None,
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip

    @property
    def disabled_tooltip(self) -> str | None:
        return self.value.disabled_tooltip
