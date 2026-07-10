import asyncio
import sys
from enum import StrEnum

from ._custom_app_attr import CustomAppAttribute
from .debug._pilot_mode import test_app_with_pilot
from .textual_app import ChezmoiGUI

__all__ = ["run_app"]


class NoRunInfo(StrEnum):
    _CHEZMOI_FOUND = "'chezmoi' command found: "
    _GIT_FOUND = "'git' command found: "
    CHEZMOI_NOT_FOUND = "'chezmoi' command not found, see https://chezmoi.io/install/"
    FEEDBACK = "Feedback welcome! https://github.com/matmaer/chezmoi-mousse/discussions"
    GIT_NOT_FOUND = "'git' command not found, see https://git-scm.com/install/"
    IN_SUBSHELL = "You are in a 'chezmoi subshell', exit the subshell to run the app."
    NOT_IN_SUBSHELL = "Not in a 'chezmoi subshell' detected."
    NO_APP_RUN = "Please check:"
    PRETEND_FAIL = "Pretending the app cannot run."
    NO_PRETEND_FAIL = "Not pretending that the app cannot run."

    @classmethod
    def git_found(cls, which: str) -> str:
        return cls._GIT_FOUND + which

    @classmethod
    def chezmoi_found(cls, which: str) -> str:
        return cls._CHEZMOI_FOUND + which


def _will_not_run_message(attr: "CustomAppAttribute") -> str | None:
    error_info: list[str] = []
    start_info: list[str] = []
    if attr.git_bin is None:
        error_info.append(NoRunInfo.GIT_NOT_FOUND)
    else:
        start_info.append(NoRunInfo.git_found(attr.git_bin))

    if attr.chezmoi_bin is None:
        error_info.append(NoRunInfo.CHEZMOI_NOT_FOUND)
    else:
        start_info.append(NoRunInfo.chezmoi_found(attr.chezmoi_bin))

    if attr.custom_env_vars.chezmoi_subshell:
        error_info.append(NoRunInfo.IN_SUBSHELL)
    else:
        start_info.append(NoRunInfo.NOT_IN_SUBSHELL)

    if attr.custom_env_vars.pretend_fail:
        error_info.append(NoRunInfo.PRETEND_FAIL)
    else:
        start_info.append(NoRunInfo.NO_PRETEND_FAIL)
    lines: list[str] = []
    if error_info or attr.custom_env_vars.pretend_fail:
        lines.append(NoRunInfo.NO_APP_RUN)
        lines.extend(error_info)
    if attr.custom_env_vars.pretend_fail:
        lines.extend(start_info)
    if len(lines) > 0:
        return "\n".join(lines) + "\n" + NoRunInfo.FEEDBACK
    return None


def run_app():

    custom_app_attr = CustomAppAttribute()

    wil_not_run_msg = _will_not_run_message(custom_app_attr)

    if wil_not_run_msg is not None:
        sys.exit(wil_not_run_msg)

    try:
        app = ChezmoiGUI(custom_app_attr=custom_app_attr)
    except Exception:
        custom_app_attr.save_stacktrace()
        raise

    try:
        if custom_app_attr.custom_env_vars.pilot_mode:
            asyncio.run(test_app_with_pilot(app))
        else:
            app.run()
    except Exception:
        custom_app_attr.save_stacktrace()
        raise


if __name__ == "__main__":
    run_app()
