from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gui.textual_app import ChezmoiGUI

__all__ = ["AppState"]


class AppState:
    """Centralized app state accessible from anywhere."""

    _changes_enabled: bool = False
    _app: "ChezmoiGUI | None" = None  # Reference to the app instance

    @classmethod
    def set_app(cls, app: "ChezmoiGUI") -> None:
        cls._app = app

    @classmethod
    def changes_enabled(cls) -> bool:
        return cls._changes_enabled

    @classmethod
    def set_changes_enabled(cls, value: bool) -> None:
        cls._changes_enabled = value
        # Notify the app to update its reactive attribute
        if cls._app is not None:
            cls._app.changes_enabled = value
