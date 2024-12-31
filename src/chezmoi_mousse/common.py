""" Command base classes and helper functions """

import json
import subprocess


def run_chezmoi(params: list) -> subprocess.CompletedProcess:
    """run a chezmoi command with the given parameters"""
    global_params = [
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    result = subprocess.run(
        ["chezmoi"] + global_params + params,
        capture_output=True,
        check=True,  # raise an exception if exit code is not 0
        encoding="utf-8",
        shell=False,  # avoid shell injection, safer
        timeout=1,  # can be increased at a later stage
    )
    return result


class ChezmoiContext:
    """
    Retrieved Chezmoi context form the local system.  "Context" includes local
    chezmoi configuration and other system specific local context.
    Initialized when starting the app. An optional refresh parameter that will
    only re-run the the commands needed for the requested context.
    """

    def __init__(self, refresh: bool = False) -> None:
        self.refresh = refresh
        self.context_item = None
        self.config = self.get_config()
        self.data = self.get_data()

    def get_config(self) -> dict:
        """Refresh the output of the `chezmoi dump-config` command"""
        return json.loads(run_chezmoi(["dump-config"]).stdout)

    def get_data(self) -> dict:
        """Refresh the output of the `chezmoi data` command"""
        return json.loads(run_chezmoi(["data"]).stdout)

    def get_source_dir(self) -> str:
        if self.refresh:
            self.config = self.get_config()
        return self.config["sourceDir"]

    def get_destination_dir(self) -> str:
        if self.refresh:
            self.config = self.get_config()
        return self.config["destDir"]

    def get_chezmoi_managed(self) -> list:
        chezmoi_arguments = [
            "managed",
            "--exclude=dirs",
            "--path-style=absolute",
        ]
        return run_chezmoi(chezmoi_arguments).stdout.splitlines()
