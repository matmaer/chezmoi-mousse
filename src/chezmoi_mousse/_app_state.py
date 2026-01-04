from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gui.textual_app import ChezmoiGUI

__all__ = ["AppState"]


class AppState:
    """Centralized app state accessible from anywhere."""

    _app: "ChezmoiGUI | None" = None  # Reference to the app instance
    _changes_enabled: bool = False

    @classmethod
    def set_app(cls, app: "ChezmoiGUI") -> None:
        cls._app = app

    @classmethod
    def get_app(cls) -> "ChezmoiGUI | None":
        return cls._app

    @classmethod
    def changes_enabled(cls) -> bool:
        return cls._changes_enabled

    @classmethod
    def set_changes_enabled(cls, value: bool) -> None:
        cls._changes_enabled = value
        if cls._app is not None:
            cls._app.changes_enabled = value
