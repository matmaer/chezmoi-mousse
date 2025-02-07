"""Module to run chezmoi commands with subprocess."""

import subprocess

from chezmoi_mousse import CHEZMOI, COMMANDS


class ChezmoiCommands:
    # TODO: check what happens if chezmoi is run in different directories
    # subprocess.run doesnt have a cwd argument, Popen does
    # could impact the data shown to act on in the operate mode of the TUI
    chezmoi_base_command = [
        "chezmoi",
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
        "--config=/home/mm/.config/chezmoi/chezmoi.toml",
    ]

    def _run(self, chezmoi_args: list) -> dict:
        try:
            chezmoi_args in COMMANDS
        except ValueError:
            raise ValueError(f"Command {chezmoi_args} not in COMMANDS")

        full_command_list = self.chezmoi_base_command + chezmoi_args
        verb = chezmoi_args[0]
        CHEZMOI[verb]["full_command"] = " ".join(full_command_list)
        try:
            returned = subprocess.run(
                full_command_list,
                capture_output=True,
                encoding="utf-8",
                shell=False,
                timeout=2,
            )
            CHEZMOI[verb]["output"] = returned.stdout
            return CHEZMOI[verb]

        except subprocess.CalledProcessError as e:
            # chezmoi can be used without config file
            if chezmoi_args[0] == "cat-config" and returned.returncode == 1:
                # store stderr instead of stdout
                CHEZMOI[verb]["output"] = returned.stderr
                return CHEZMOI[verb]

            # all other cases, raise the error
            raise subprocess.CalledProcessError from e

    def run(self, chezmoi_args: str, refresh: bool = False) -> dict:

        try:
            chezmoi_args in COMMANDS
        except ValueError:
            raise ValueError(f"Command {chezmoi_args} not in COMMANDS")

        chezmoi_arg_list = chezmoi_args.split()
        verb = chezmoi_arg_list[0]

        if refresh or CHEZMOI[verb]["output"] == "":
            return self._run(chezmoi_arg_list)
        return CHEZMOI[verb]
