from __future__ import annotations

import sys
import tempfile
import traceback
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

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

    @staticmethod
    def is_immutable_object(any_object: object) -> bool:
        return bool(hash(any_object))


class ClassInstanceTracker:
    def __init__(self) -> None:
        self.counts: dict[str, int] = defaultdict(int)
        # Ensure project_dir is fully resolved once
        self.project_dir: Path = Path(__file__).resolve().parent.parent.parent
        self._path_cache: dict[str, bool] = {}
        self._is_profiling: bool = False

    def _profile(self, frame: types.FrameType, event: str, _: object) -> None:
        # Re-entrancy guard: stop recursion while processing an event
        if self._is_profiling or event != "call":
            return

        code = frame.f_code

        if code.co_name == "__init__":
            self._is_profiling = True
            try:
                filename = code.co_filename

                # Fast Path: Check cached path decision
                if filename not in self._path_cache:
                    filepath = Path(filename).resolve()
                    try:
                        self._path_cache[filename] = filepath.is_relative_to(
                            self.project_dir
                        )
                    except ValueError:
                        self._path_cache[filename] = False

                # Only proceed if the file belongs to your project
                if self._path_cache[filename]:
                    self_obj = frame.f_locals.get("self")
                    if self_obj is not None and not isinstance(
                        self_obj, ClassInstanceTracker
                    ):
                        cls_name = type(self_obj).__qualname__
                        self.counts[cls_name] += 1
            finally:
                self._is_profiling = False

    def start(self) -> None:
        """Starts monitoring class instantiations (only if in debug mode)."""
        if __debug__:
            sys.setprofile(self._profile)

    def stop(self) -> None:
        """Stops monitoring."""
        if __debug__:
            sys.setprofile(None)

    def get_counts(self) -> dict[str, int]:
        """Returns a copy of the current class instantiation counts."""
        return dict(self.counts)
