from dataclasses import dataclass, field
import json
import subprocess
import tomllib

@dataclass
class ChezmoiIO:
    input: str = field(default_factory=str)
    stdout: str = field(default_factory=str)
    stderr: str = field(default_factory=str)


@dataclass
class ChezmoiOutput(ChezmoiIO):
    data: ChezmoiIO = field(default_factory=ChezmoiIO)
    dump_config: ChezmoiIO = field(default_factory=ChezmoiIO)
    cat_config: ChezmoiIO = field(default_factory=ChezmoiIO)
    doctor: ChezmoiIO = field(default_factory=ChezmoiIO)
    ignored: ChezmoiIO = field(default_factory=ChezmoiIO)
    managed: ChezmoiIO = field(default_factory=ChezmoiIO)
    status: ChezmoiIO = field(default_factory=ChezmoiIO)

chezmoi_io = ChezmoiOutput()


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

    def _run(self, command: list) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                self.chezmoi_base_command + command,
                capture_output=True,
                encoding="utf-8",
                shell=False,
                timeout=1,
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

    def umanaged(self) -> list:
        command = ["managed", "--path-style=absolute"]
        return self._run(command).splitlines()

    def managed(self) -> list:
        command = ["managed", "--path-style=absolute"]
        return self._run(command).splitlines()

    def status(self) -> list:
        return self._run(["status"]).splitlines()

chezmoi = ChezmoiCommands()