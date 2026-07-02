import asyncio

from chezmoi_mousse._pilot_mode import test_app_with_pilot
from chezmoi_mousse._pre_run_logic import PreRunLogic
from chezmoi_mousse.textual_app import ChezmoiGUI


def run_app():

    pre_run_logic = PreRunLogic()

    try:
        app = ChezmoiGUI(pre_run_logic=pre_run_logic)
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
