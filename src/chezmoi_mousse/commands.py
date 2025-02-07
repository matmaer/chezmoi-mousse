"""Module to run chezmoi commands with subprocess."""

import subprocess
from chezmoi_mousse import CHEZMOI, ChezmoiOutput


class ChezmoiCommand:

    @staticmethod
    def run(chezmoi_args: str, refresh: bool = False) -> ChezmoiOutput:
        base_command = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
            "--config=/home/mm/.config/chezmoi/chezmoi.toml",
        ]

        chezmoi_arg_list = chezmoi_args.split()
        verb = chezmoi_arg_list[0].replace("-", "_")

        try:
            command_data = getattr(CHEZMOI, verb)
        except AttributeError:
            raise KeyError(f"Chezmoi verb '{verb}' is not found in CHEZMOI")

        full_command_list = base_command + chezmoi_arg_list
        command_data.full_command = " ".join(full_command_list)

        if refresh or command_data.output == "":
            try:
                call_output = subprocess.run(
                    full_command_list,
                    capture_output=True,
                    encoding="utf-8",
                    shell=False,
                    timeout=2,
                )
                command_data.output = call_output.stdout
                return command_data

            except subprocess.CalledProcessError:
                if verb == "cat_config" and call_output.returncode == 1:
                    command_data.output = call_output.stderr
                    return command_data

        return command_data
