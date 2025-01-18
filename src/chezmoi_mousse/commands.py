"""
Module that wraps chezmoi and git commands.
Bare minimum output curation which needed for any widget.
"""

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
        # removed check=True, not all non-zero exit codes are show stoppers
        result = subprocess.run(
            self.chezmoi + command,
            capture_output=True,
            encoding="utf-8",
            shell=False,
            timeout=2,  # temporary for development, should be one
        )
        if result.returncode == 0:
            return result.stdout
        # chezmoi can be used without config file
        if command[0] == "cat-config" and result.returncode == 1:
            return result.stderr
        else:  # as if check=True was used, quits the app with an error
            raise subprocess.CalledProcessError

    def data(self) -> dict:
        result = json.loads(self._run(["data", "--format=json"]))["chezmoi"]
        del result["args"]
        return result

    def dump_config(self) -> dict:
        return json.loads(self._run(["dump-config", "--format=json"]))

    def cat_config(self) -> dict:
        result = self._run(["cat-config"])
        try:
            return tomllib.loads(result)
        except tomllib.TOMLDecodeError:
            return result.strip()

    def managed(self) -> list:
        command = ["managed", "--path-style=absolute"]
        return self._run(command).splitlines()

    def doctor(self) -> list:
        return self._run(["doctor"]).splitlines()

    def status(self) -> list:
        return self._run(["status"]).splitlines()
