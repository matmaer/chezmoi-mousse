import os
import shutil
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from ._app_ids import AppIds
from ._str_enums import TabLabel

__all__ = ["CustomAppAttribute"]


class CustomEnvVars(NamedTuple):
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


class CanvasIds(NamedTuple):
    add = AppIds(TabLabel.add)
    apply = AppIds(TabLabel.apply)
    config = AppIds(TabLabel.config)
    debug = AppIds(TabLabel.debug)
    logs = AppIds(TabLabel.logs)
    re_add = AppIds(TabLabel.re_add)


@dataclass(frozen=True)
class CustomAppAttribute:

    custom_env_vars = CustomEnvVars()
    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    stacktrace_path: Path = Path(__file__).parent / "stacktrace.log"
    canvas_ids: CanvasIds = CanvasIds()

    def __post_init__(self) -> None:
        if self.stacktrace_path.exists():
            self.stacktrace_path.unlink()

    def save_stacktrace(self):
        with Path.open(self.stacktrace_path, "a") as f:
            traceback.print_exc(file=f)
