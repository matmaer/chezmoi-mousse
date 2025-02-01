""" Module that wraps chezmoi commands."""

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
            "--config=/home/mm/.config/chezmoi/chezmoi.toml",
        ]

    def _run(self, command: list) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                self.chezmoi + command,
                capture_output=True,
                encoding="utf-8",
                shell=False,
                timeout=2,  # temporary for development, should be one
            )
        except FileNotFoundError:
            return "chezmoi not found"

        if result.returncode == 0:
            return result.stdout
        # chezmoi can be used without config file
        if command[0] == "cat-config" and result.returncode == 1:
            return result.stderr
        else:
            raise subprocess.CalledProcessError

    ####################
    # inspect commands #
    ####################

    def data(self) -> dict | str:
        result = self._run(["data", "--format=json"])
        try:
            result_dict = json.loads(result)
            if "args" in result_dict.keys():
                del result["args"]
            return result_dict["chezmoi"]
        except json.JSONDecodeError:
            return result.strip()

    def dump_config(self) -> dict | str:
        result = self._run(["dump-config", "--format=json"])
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result.strip()

    def cat_config(self) -> dict | str:
        result = self._run(["cat-config"])
        try:
            return tomllib.loads(result)
        except tomllib.TOMLDecodeError:
            return result.strip()

    def doctor(self) -> list:
        result = self._run(["doctor"]).splitlines()
        return result

    def ignored(self) -> list:
        return self._run(["ignored"]).splitlines()

    def managed(self) -> list:
        command = ["managed", "--path-style=absolute"]
        return self._run(command).splitlines()

    def status(self) -> list:
        return self._run(["status"]).splitlines()

    #########################################
    # commands to be implemented, if needed #
    #########################################

    def target_state_dump(self) -> dict | str:
        result = self._run(["dump"])
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result.strip()

    def state_dump(self) -> dict | str:
        result = self._run(["state", "dump", "--format=json"])
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result.strip()
