import json
import subprocess
import tomllib
from dataclasses import dataclass, field

import yaml
# from textual import work
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Header,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import FLOW_DIAGRAM, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen


@dataclass
class InputOutput:
    long_command: list[str] = field(default_factory=list)
    std_out: str = "initial std_out value"

    @property
    def py_out(self):
        failures = {}
        std_out = self.std_out.strip()
        if std_out == "":
            return "std_out is an empty string"
        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            failures["json"] = "std_out json.JSONDecodeError"
        try:
            return tomllib.loads(std_out)
        except tomllib.TOMLDecodeError:
            failures["toml"] = "std_out tomllib.TOMLDecodeError"
        try:
            return yaml.safe_load(std_out)
        except yaml.YAMLError:
            failures["yaml"] = "std_out yaml.YAMLError"
        if std_out.count("\n") > 0:
            return std_out.splitlines()
        return std_out

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def _subprocess_run(self):
        """Runs the subprocess call and sets std_out."""
        result = subprocess.run(
            self.long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.std_out = result.stdout

    def update(self):
        """Re-run the subprocess call, don't return anything."""
        self._subprocess_run()

    def updated_std_out(self):
        """Re-run subprocess call and return std_out."""
        self._subprocess_run()
        return self.std_out

    def updated_py_out(self):
        """Re-run subprocess call and return py_out."""
        self._subprocess_run()
        return self.py_out


class Chezmoi:

    cat_config: InputOutput = None
    data: InputOutput = None
    doctor: InputOutput = None
    dump_config: InputOutput = None
    git_log: InputOutput = None
    git_status: InputOutput = None
    ignored: InputOutput = None
    managed: InputOutput = None
    status: InputOutput = None
    unmanaged: InputOutput = None

    def __init__(self):
        self.base = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ]
        self.subs = {
            "cat_config": ["cat-config"],
            "data": ["data", "--format=json"],
            "doctor": ["doctor"],
            "dump_config": ["dump-config", "--format=json"],
            "git_log": ["git", "log", "--", "--oneline"],
            "git_status": ["git", "status"],
            "ignored": ["ignored"],
            "managed": ["managed", "--path-style=absolute"],
            "status": ["status", "--parent-dirs"],
            "unmanaged": ["unmanaged", "--path-style=absolute"],
        }

        for arg_id, sub_cmd in self.subs.items():
            setattr(self, arg_id, InputOutput(self.base + sub_cmd))

    @property
    def arg_ids(self):
        """Return the list of arg_ids."""
        return list(self.subs.keys())


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    def __init__(self) -> None:
        super().__init__()
        self.chezmoi = Chezmoi()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            "Unmanaged",
            "Diagram",
            # "Doctor",
            "Dump-Config",
            # "Chezmoi-Status",
            # "Managed-Files",
            # "Template-Data",
            # "Cat-Config",
            # "Git-Log",
            # "Ignored",
            # "Git-Status",
        ):
            yield Pretty(self.app.chezmoi.unmanaged.py_out)
            yield Static(FLOW_DIAGRAM, id="diagram")
            # yield ChezmoiDoctor(self.app.chezmoi.doctor.py_out)
            yield Static(self.app.chezmoi.dump_config.py_out)
            # yield ChezmoiStatus(self.app.chezmoi.status.py_out)
            # yield ManagedFiles(self.app.chezmoi.managed.py_out)
            # yield Pretty(self.app.chezmoi.data.py_out)
            # yield Pretty(self.app.chezmoi.cat_config.py_out)
            # yield Pretty(self.app.chezmoi.git_log.py_out)
            # yield Pretty(self.app.chezmoi.ignored.py_out)
            # yield Pretty(self.app.chezmoi.status.py_out)

        yield Footer()

    def on_mount(self) -> None:

        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading")
