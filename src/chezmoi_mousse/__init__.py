import json
import sys
from pathlib import Path
from subprocess import run

from .id_typing import ParsedJson

chezmoi_config: ParsedJson


BASE_CMD = ("chezmoi", "--no-pager", "--color=off", "--no-tty", "--mode=file")


try:
    chezmoi_config: ParsedJson = json.loads(
        run(
            BASE_CMD + ("dump-config", "--format=json"),
            capture_output=True,
            text=True,
        ).stdout
    )
except Exception as e:
    print(f"Failed run chezmoi dump-config: {e}", file=sys.stderr)
    sys.exit(1)


class ChezmoiConfig:
    def __init__(self, config: ParsedJson):
        self.destDir: Path = Path(config["destDir"])
        self.sourceDir: Path = Path(config["sourceDir"])
        self.autoadd: bool = config["git"]["autoadd"]
        self.autocommit: bool = config["git"]["autocommit"]
        self.autopush: bool = config["git"]["autopush"]
        self.interactive: bool = config["interactive"]
        self.mode: str = config["mode"]
        self.tempDir: str = config["tempDir"]


try:
    CM_CFG = ChezmoiConfig(chezmoi_config)
    if CM_CFG.mode != "file":
        print(f"Currently only file mode is supported, got {CM_CFG.mode}")
        sys.exit(1)
except Exception as e:
    print(f"Failed to create ChezmoiConfig: {e}", file=sys.stderr)
    sys.exit(1)
