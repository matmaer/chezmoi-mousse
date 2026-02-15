from __future__ import annotations

from dataclasses import dataclass

from ._chezmoi_command import WriteCmd

__all__ = ["InitCloneData"]


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool
