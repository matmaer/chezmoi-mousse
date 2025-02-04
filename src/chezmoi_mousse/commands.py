""" Module to run chezmoi commands with subprocess."""

import subprocess

from chezmoi_mousse import CHEZMOI


class ChezmoiCommands:
    # TODO: check what happens chezmoi doesn't know what the destination dir
    # Note the cmd is not defined the subprocess call
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
        full_command_list = self.chezmoi_base_command + chezmoi_args
        verb = chezmoi_args[0]
        CHEZMOI[verb]["full_command"] = " ".join(full_command_list)
        try:
            call_result = subprocess.run(
                full_command_list,
                capture_output=True,
                encoding="utf-8",
                shell=False,
                timeout=2,
            )
            CHEZMOI[verb]["output"] = call_result.stdout
            return CHEZMOI[verb]
        except subprocess.CalledProcessError as e:
            # chezmoi can be used without config file
            if chezmoi_args[0] == "cat-config" and call_result.returncode == 1:
                # store stderr instead of stdout
                CHEZMOI[verb]["output"] = call_result.stderr
                return CHEZMOI[verb]
            raise subprocess.CalledProcessError from e

    def run(self, chezmoi_args: str, refresh: bool = False) -> dict:

        chezmoi_arg_list = chezmoi_args.split()
        verb = chezmoi_arg_list[0]

        # safety check because working programmatically created dict
        try:
            chezmoi_args == CHEZMOI[verb]["command"]
        except ValueError as e:
            raise ValueError(f"'{chezmoi_args}': unknown command") from e
        except KeyError as e:
            raise KeyError(f"'{verb}': unknown command") from e

        if refresh:
            return self._run(chezmoi_arg_list)
        return CHEZMOI[verb]
