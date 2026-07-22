from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.str_enums import StatusCode, TabLabel
    from chezmoi_mousse.textual_app import ChezmoiGui

    type ParsedJson = dict[str, Any]
    type StatusDict = dict[Path, StatusCode]

    __all__ = (
        "AppIds",
        "ChezmoiGui",
        "ParsedJson",
        "StatusCode",
        "StatusDict",
        "TabLabel",
    )
