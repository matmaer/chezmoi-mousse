"""Chezmoi operations: wrap commands, handle results."""

import json
import subprocess
import tomllib


class ChezmoiCommands:
    def __init__(self):
        self.chezmoi = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ]

    def _run(self, command: list) -> subprocess.CompletedProcess:
        result = subprocess.run(
            self.chezmoi + command,
            capture_output=True,
            check=True,  # raise an exception if exit code is not 0
            encoding="utf-8",
            shell=False,  # avoid shell injection, safer
            timeout=1,  # can be increased at a later stage
        )
        return result

    def data(self) -> dict:
        return json.loads(self._run(["data", "--format=json"]).stdout)

    def dump_config(self) -> dict:
        return json.loads(self._run(["dump-config", "--format=json"]).stdout)

    def cat_config(self) -> dict:
        return tomllib.loads(self._run(["cat-config"]).stdout)

    def managed(self) -> list:
        command = ["managed", "--path-style=absolute"]
        return self._run(command).stdout.splitlines()

    def doctor(self) -> list:
        return self._run(["doctor"]).stdout.splitlines()

    def status(self) -> list:
        return self._run(["status"]).stdout.splitlines()
