import json
import subprocess
import tomllib


class Utils:

    @staticmethod
    def get_label(long_command: list[str]) -> str:
        return " ".join([w for w in long_command if not w.startswith("-")])

    @staticmethod
    def get_arg_id(long_command: list[str]) -> str:
        all_args = long_command[1:]
        verbs = [w for w in all_args if not w.startswith("-")]
        return "_".join([w.replace("-", "_") for w in verbs])

    @staticmethod
    def parse_std_out(std_out) -> str | list | dict:
        failures = {}
        std_out = std_out.strip()
        if std_out == "":
            return "std_out is an empty string nothing to decode"
        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            failures["json"] = "std_out json.JSONDecodeError"
            try:
                return tomllib.loads(std_out)
            except tomllib.TOMLDecodeError:
                failures["toml"] = "std_out tomllib.TOMLDecodeError"
                # check how many "\n" newlines are found in the output
                if std_out.count("\n") > 0:
                    return std_out.splitlines()
        # should not be returned, just gives feedback in the tui
        return failures

    @staticmethod
    def subprocess_run(long_command):
        result = subprocess.run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        return result.stdout
