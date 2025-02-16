from dataclasses import dataclass
import shutil
import subprocess
import copy


@dataclass(frozen=True)
class Components:

    words = {
        "chezmoi": {
            "base": [
                shutil.which("chezmoi"),
                "--no-pager",
                "--color=false",
                "--no-tty",
                "--progress=false",
            ],
            "verbs": {
                "doctor": ["doctor"],
                "dump_config": ["dump-config", "--format=json"],
                "data": ["data", "--format=json"],
                "cat_config": ["cat-config"],
                "ignored": ["ignored"],
                "managed": ["managed",  "--path-style=absolute"],
                "status": ["status", "--parent-dirs"],
                "unmanaged": ["unmanaged", "--path-style=absolute"],
            },
        },
        "git": {
            "base": [
                shutil.which("git"),
                "--no-advice",
                "--no-pager",
            ],
            "verbs": {
                "log": ["log", "--oneline"],
                "status": ["status"],
            },
        },
    }

    @property
    def empty_cmd_dict(self):
        # a key for each global command
        empty_cmd_dict = {key: {} for key in self.words}
        # add a key for each verb for each command
        for key in empty_cmd_dict:
            empty_cmd_dict[key] = {verb: "" for verb in self.words[key]["verbs"].keys()}
        return copy.deepcopy(empty_cmd_dict)

    # property to retrieve all the verbs for calling subprocess.run()
    @property
    def full_command(self):
        full_command = self.empty_cmd_dict
        for cmd, items in self.words.items():
            base_words = items["base"]
            for verb, verb_words in items["verbs"].items():
                full_command[cmd][verb] = base_words + verb_words
        return full_command

OUTPUT = Components().empty_cmd_dict

@dataclass(frozen=True)
class CommandIO(Components):

    def get_command_output(self, command: str, verb: str) -> str:
        return OUTPUT[command][verb]

    def set_command_output(self, command: str, verb: str, output: str):
        OUTPUT[command][verb] = output

    def get_output(self, command: str, verb: str, refresh: bool = False) -> str:
        command_to_run = Components().full_command[command][verb]
        if refresh or not self.get_command_output(command, verb):
            result = subprocess.run(
                command_to_run,
                capture_output=True,
                check=True,  # raises exception for any non-zero return code
                shell=False,  # mitigates shell injection risk
                text=True,  # returns stdout as str instead of bytes
                timeout=2,
            )
            self.set_command_output(command, verb, result.stdout)
        return self.get_command_output(command, verb)


def run(command: str, verb: str, refresh: bool = False) -> str:
    return CommandIO().get_output(command, verb, refresh)
