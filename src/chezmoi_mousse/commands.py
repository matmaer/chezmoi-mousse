""" Module to run chezmoi commands with subprocess."""

import subprocess

from chezmoi_mousse import CHEZMOI, VERBS


class ChezmoiCommands:
    def __init__(self) -> None:
        self.chezmoi_base_command = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
            "--config=/home/mm/.config/chezmoi/chezmoi.toml",
        ]

    def _run(self, chezmoi_args: list) -> dict:
        subprocess_command = self.chezmoi_base_command + chezmoi_args
        verb = chezmoi_args[0]
        CHEZMOI[verb]["command"] = f"chezmoi {" ".join(chezmoi_args)}"
        try:
            call_result = subprocess.run(
                subprocess_command,
                capture_output=True,
                encoding="utf-8",
                shell=False,
                timeout=2,
            )
            CHEZMOI[verb]["output"] = call_result.stdout
            return CHEZMOI[verb]
        except subprocess.CalledProcessError:
            # chezmoi can be used without config file
            if chezmoi_args[0] == "cat-config" and call_result.returncode == 1:
                # store stderr instead of stdout
                CHEZMOI[verb]["output"] = call_result.stderr
                return CHEZMOI[verb]
            else:
                # raise every other non zero code, like check=true would do
                raise subprocess.CalledProcessError

    def run(self, chezmoi_args: str, refresh: bool = False) -> dict:
        chezmoi_args = chezmoi_args.split()
        verb = chezmoi_args[0]
        if verb not in VERBS:
            raise ValueError(f"'{verb}' not in VERBS")
        if refresh:
            return self._run(chezmoi_args)
        return CHEZMOI[verb]
