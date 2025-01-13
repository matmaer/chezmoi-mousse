"""
Module that wraps chezmoi and git commands.
Bare minimum output curation which needed for any widget.
"""

import json
import subprocess
import tomllib
from textual.app import ComposeResult
from textual.widgets import Log


class CommandLog(Log):
    def __init__(self):
        super().__init__(
            highlight=True,
            max_lines=1000,
        )

    def compose(self) -> ComposeResult:
        yield Log()


class ChezmoiCommands:
    def __init__(self):
        self.chezmoi = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ]
        self.command_log = CommandLog()

    def _run(self, command: list) -> subprocess.CompletedProcess:
        # removed check=True, not all non-zero exit codes are show stoppers
        result = subprocess.run(
            self.chezmoi + command,
            capture_output=True,
            encoding="utf-8",
            shell=False,  # avoid shell injection, safer
            timeout=1,  # 1 second, the minimum
        )
        if result.returncode == 0:
            return result
        # chezmoi can be used without config file
        if command[0] == "cat-config" and result.returncode == 1:
            return result
        else:  # as if check=True was used, quits the app with an error
            raise subprocess.CalledProcessError

    def _log(self, to_write="default") -> None:
        self.command_log.write_line(to_write)

    def data(self) -> dict:
        result = json.loads(self._run(["data", "--format=json"]).stdout)["chezmoi"]
        del result["args"]
        return result

    def dump_config(self) -> dict:
        return json.loads(self._run(["dump-config", "--format=json"]).stdout)

    def cat_config(self) -> dict:
        result = self._run(["cat-config"]).stdout
        return tomllib.loads(result)

    def managed(self) -> list:
        command = ["managed", "--path-style=absolute"]
        return self._run(command).stdout.splitlines()

    def doctor(self) -> list:
        return self._run(["doctor"]).stdout.splitlines()

    def status(self) -> list:
        return self._run(["status"]).stdout.splitlines()
