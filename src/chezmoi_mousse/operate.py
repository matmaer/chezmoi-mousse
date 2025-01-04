""" Chezmoi Operations """

import json
import subprocess
import tomllib


class ChezmoiCommands:

    def _run(self, params: list) -> subprocess.CompletedProcess:
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

    def data(self) -> dict:
        chezmoi_arguments = ["data", "--format=json"]
        return json.loads(self._run(chezmoi_arguments).stdout)

    def dump_config(self) -> dict:
        chezmoi_arguments = ["dump-config", "--format=json"]
        return json.loads(self._run(chezmoi_arguments).stdout)

    def cat_config(self) -> dict:
        return tomllib.loads(self._run(["cat-config"]).stdout)

    def managed(self) -> list:
        command = ["managed", "--path-style=absolute"]
        managed = self._run(command).stdout.splitlines()
        return managed

    def doctor(self) -> list:
        return self._run(["doctor"]).stdout.splitlines()

    def status(self) -> list:
        return self._run(["status"]).stdout.splitlines()
