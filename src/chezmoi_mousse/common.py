""" Command base classes and helper functions """

import json
import subprocess


def _run(params: list) -> subprocess.CompletedProcess:
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


class ChezmoiCommands:
    def data(self) -> dict:
        chezmoi_arguments = ["data", "--format=json"]
        return json.loads(_run(chezmoi_arguments).stdout)

    def dump_config(self) -> dict:
        chezmoi_arguments = ["dump-config", "--format=json"]
        return json.loads(_run(chezmoi_arguments).stdout)

    def cat_config(self) -> str:
        return _run(["cat-config"]).stdout

    def managed(self) -> dict:
        # initialize the the dictionary to return
        managed = dict.fromkeys(["dirs", "files", "symlinks"], [])
        # chezmoi managed
        # note: "--path-style=relative": relative to the destination dir
        common_args = ["managed", "--path-style=relative"]
        dir_args = common_args + ["--include=dirs"]
        file_args = common_args + ["--include=files"]
        symlink_args = common_args + ["--include=symlinks"]

        managed["dirs"] = _run(dir_args).stdout.splitlines()
        managed["files"] = _run(file_args).stdout.splitlines()
        managed["symlinks"] = _run(symlink_args).stdout.splitlines()

        return managed

    def doctor(self) -> list:
        return _run(["doctor"]).stdout.splitlines()

    def status(self) -> list:
        return _run(["status"]).stdout.splitlines()


# class ChezmoiContext:
#     """
#     Handle system specific local context which doesn't change at any point
#     while using the TUI. Initialized when starting the app.
#     """
