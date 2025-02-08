"""Module to run chezmoi commands with subprocess."""

import subprocess
import json
from chezmoi_mousse import CommandData


class ChezmoiCommand:

    @classmethod
    def run(cls, command_data: CommandData, refresh: bool = False) -> CommandData:
        full_command = command_data.base_cmd + command_data.verb_cmd

        if refresh or command_data.stdout == "":
            try:
                call_output = subprocess.run(
                    full_command,
                    capture_output=True,
                    check=True,
                    encoding="utf-8",
                    shell=False,
                    timeout=2,
                )
                command_data.stdout = call_output.stdout
            except subprocess.CalledProcessError:
                if (
                    command_data.verb_cmd[0] == "cat-config"
                    and call_output.returncode == 1
                ):
                    command_data.stdout = call_output.stderr
            try:
                command_data.pyout = json.loads(command_data.stdout)
            except json.JSONDecodeError:
                command_data.pyout = command_data.stdout.splitlines()
            except AttributeError:
                command_data.pyout = command_data.stdout.strip()
        return command_data
