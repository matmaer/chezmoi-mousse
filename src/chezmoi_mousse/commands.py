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
            # keys for verbs: underscore vs hyphen so DRY
            "verbs": {
                "doctor": ["doctor"],
                "dump_config": ["dump-config", "--format=json"],
                "data": ["data", "--format=json"],
                "cat_config": ["cat-config"],
                "ignored": ["ignored"],
                "managed": ["managed"],
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
        empty_cmd_dict = dict.fromkeys(self.words.keys(), {})
        # add a key for each verb for each command
        for key in empty_cmd_dict:
            empty_cmd_dict[key] = dict.fromkeys(
                self.words[key]["verbs"].keys(), ""
                )
        return empty_cmd_dict

    # property to retrieve all the verbs for calling subprocess.run()
    @property
    def full_command(self):
        full_command = self.empty_cmd_dict
        for cmd, items in self.words.items():
            base_words = items["base"]
            for verb, verb_words in items["verbs"].items():
                full_command[cmd][verb] = base_words + verb_words
                # full_command[cmd][verb] = "no output yet"
        return full_command

    # method to generate a dictionary "template"
    # Another time for creating the dict full_command to be used by subprocess.run()
    def create_output_dict(self):
        return copy.deepcopy(self.empty_cmd_dict)  # Create a deep copy of the template


OUTPUT = Components().create_output_dict()


def run(command: str, verb: str, refresh: bool = False) -> str:
    command_to_run = Components().full_command[command][verb]
    if refresh:
        result = subprocess.run(
            command_to_run,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        OUTPUT[command][verb] = result.stdout
    # return OUTPUT[command][verb]
    return f"Command: {command} {verb} has been run"
