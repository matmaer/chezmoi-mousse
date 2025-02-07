"""Module to run chezmoi commands with subprocess."""

import subprocess

from chezmoi_mousse import CHEZMOI





class ChezmoiCommands:




    @staticmethod
    def run(chezmoi_args: str, refresh: bool = False) -> dict:



        base_command = [
            # which("chezmoi"),
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
            "--config=/home/mm/.config/chezmoi/chezmoi.toml",
        ]

        chezmoi_arg_list = chezmoi_args.split()
        verb = chezmoi_arg_list[0]

        try:
            verb in CHEZMOI
        except KeyError:
            raise KeyError(f"Chezmoi verb '{verb} is not found in CHEZMOI")

        full_command_list = base_command + chezmoi_arg_list
        print(full_command_list)

        CHEZMOI[verb]["full_command"] = " ".join(full_command_list)
        if refresh or CHEZMOI[verb]["output"] == "":
            try:
                print(full_command_list)
                call_output = subprocess.run(
                    full_command_list,
                    capture_output=True,
                    encoding="utf-8",
                    shell=False,
                    timeout=2,
                )
                CHEZMOI[verb]["output"] = call_output.stdout
                return CHEZMOI[verb]

            except subprocess.CalledProcessError:
                # chezmoi can be used without config file
                if verb == "cat-config" and call_output.returncode == 1:
                    # store stderr instead of stdout
                    CHEZMOI[verb]["output"] = call_output.stderr
                    return CHEZMOI[verb]
        return CHEZMOI[verb]