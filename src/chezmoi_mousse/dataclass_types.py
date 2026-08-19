from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.str_enums import WriteCmd

__all__ = ("ReviewBtnData", "RunBtnData")


@dataclass(slots=True)
class ReviewBtnData:
    ids: AppIds
    btn_id: str
    btn_qid: str
    write_cmd: WriteCmd
    op_info_string: str
    op_info_subtitle: str
    path_arg: Path | None = None


@dataclass(slots=True)
class RunBtnData:
    btn_id: str
    btn_qid: str
