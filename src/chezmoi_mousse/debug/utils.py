import tempfile
import traceback
from pathlib import Path

__all__ = ["DebugUtils"]


class DebugUtils:
    @staticmethod
    def clear_stacktrace() -> None:
        path = Path(tempfile.gettempdir()) / "chezmoi_gui_stacktrace.log"
        path.unlink(missing_ok=True)
        with path.open("w") as f:
            f.write("")

    @staticmethod
    def save_stacktrace() -> None:
        path = Path(tempfile.gettempdir()) / "chezmoi_gui_stacktrace.log"
        if not path.exists():
            path.touch()
        with path.open("a") as f:
            traceback.print_exc(file=f)
