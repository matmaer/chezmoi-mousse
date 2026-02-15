from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._chezmoi_command import WriteCmd
    from .gui.textual_app import ChezmoiGUI

type ParsedJson = dict[str, "Any"]

__all__ = ["AppType", "InitCloneData", "ParsedJson"]


class AppType:
    app: ChezmoiGUI


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool
