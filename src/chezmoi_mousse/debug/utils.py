from __future__ import annotations

import sys
import tempfile
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

__all__ = ["DebugUtils"]


class DebugUtils:
    def _new_log_path(self, out_dir: Path) -> Path:
        return out_dir / f"{datetime.now().strftime('%Y%m%d_%Hh_%Mm_%Ss')}.log"

    def _handle_existing_log_file(self, out_dir: Path, to_write: str) -> bool:
        all_log_files = [p for p in out_dir.glob("*.log") if p.is_file()]
        log_files = [p for p in all_log_files if not p.name.startswith("backup_")]
        log_files = sorted(log_files, key=lambda p: p.name, reverse=True)
        if not log_files:
            return False

        log_file = log_files[0]
        with log_file.open("r") as f:
            old_contents = f.read().strip()
        if old_contents == to_write:
            log_file.rename(self._new_log_path(out_dir))
            return True  # Renamed existing log in-place: signal no new write is needed

        log_file.rename(log_file.with_name(f"backup_{log_file.name}"))
        # clean up old backups, keeping only the five most recent ones
        backups = sorted(out_dir.glob("backup_*"), key=lambda p: p.name, reverse=True)
        for old_backup in backups[5:]:
            old_backup.unlink(missing_ok=True)
        return False

    def save_stacktrace(self) -> None:
        try:
            out_dir = Path(tempfile.gettempdir()) / "chezmoi_mousse_stacktraces"
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return

        to_write = traceback.format_exc().strip()

        if self._handle_existing_log_file(out_dir, to_write):
            # True if we did a rename because the exception is identical
            return

        new_log_path = self._new_log_path(out_dir)
        with new_log_path.open("w") as f:
            f.write(to_write)

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
