import asyncio

from ._app_ids import CanvasIds
from ._app_state import AppState
from .debug._pilot_mode import test_app_with_pilot
from .textual_app import ChezmoiGUI

__all__ = ["run_app"]


def run_app():

    pre_run_logic = AppState()
    ids = CanvasIds()

    try:
        app = ChezmoiGUI(pre_run_logic=pre_run_logic, ids=ids)
    except Exception:
        pre_run_logic.save_stacktrace()
        raise

    try:
        if pre_run_logic.pilot_mode:
            asyncio.run(test_app_with_pilot(app))
        else:
            app.run()
    except Exception:
        pre_run_logic.save_stacktrace()
        raise


if __name__ == "__main__":
    run_app()
