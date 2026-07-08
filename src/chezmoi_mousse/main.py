import asyncio

from ._app_ids import CanvasIds
from ._custom_app_attr import CustomAppAttribute
from .debug._pilot_mode import test_app_with_pilot
from .textual_app import ChezmoiGUI

__all__ = ["run_app"]


def run_app():

    custom_app_attr = CustomAppAttribute()
    ids = CanvasIds()

    try:
        app = ChezmoiGUI(custom_app_attr=custom_app_attr, ids=ids)
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
