from __future__ import annotations

import os
import zlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from pathlib import Path


class Utils:

    @staticmethod
    def path_to_id(p: Path) -> str:
        b = os.fsencode(os.fspath(p))  # safe, uses fs encoding + surrogateescape
        crc = zlib.crc32(b) & 0xFFFFFFFF  # 0xFFFFFFFF to ensure unsigned 32-bit integer
        return "p_" + str(crc)

    @staticmethod
    def path_to_qid(p: Path) -> str:
        return f"#{Utils.path_to_id(p)}"
