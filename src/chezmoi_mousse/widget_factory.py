# We need 3 factories which each should accept a CommandResults object.
# content: list[Label | Static | TextArea]
# diff: list[Label | Static]
# git_log: DataTable[str]

from dataclasses import dataclass
from pathlib import Path

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.widgets import DataTable, Label, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from ._chezmoi_command import ReadCmd
from ._str_enum_names import PathKind, Tcss
from ._str_enums import StatusCode
from ._type_checking import AppType

__all__ = ["GitLogTable"]


@dataclass(slots=True)
class PathWidgets:
    label_str: str
    contents: list[Static] | TextArea
    diff_apply: list[Static]
    diff_reverse: list[Static]
    git_log: DataTable[str]


class PathNode(AppType):

    def __init__(
        self, path: Path, path_kind: PathKind, status_code: StatusCode
    ) -> None:
        self.status_code = status_code
        self.path = path
        self.path_kind = path_kind
        self.path_widgets: PathWidgets = self.create_widgets()

    def create_widgets(self):
        if self.path_kind == PathKind.FILE:
            path_contents = self.create_file_content_widgets()
        else:
            path_contents = self.create_dir_content_widgets()

        return PathWidgets(
            label_str=self.path.name,  # to be constructed based status_code and exists
            contents=path_contents,
            diff_apply=self.create_diff_statics(reverse=False),
            diff_reverse=self.create_diff_statics(reverse=True),
            git_log=GitLogTable(self.path),
        )

    def create_diff_statics(self, reverse: bool) -> list[Static]:
        # green: "+", "new"
        # red: "-", "old", "deleted"
        # orange: "changed"
        # dimmed: " ", "index"
        static_list: list[Static] = []
        diff_result = (
            (self.app.cmd.read(ReadCmd.diff, path_arg=self.path))
            if reverse is False
            else (self.app.cmd.read(ReadCmd.diff_reverse, path_arg=self.path))
        )
        for line in diff_result.completed_process.stdout.splitlines():
            if line.startswith(("+", "new")):
                static_list.append(Static(line, classes=Tcss.added))
            elif line.startswith(("-", "old", "deleted")):
                static_list.append(Static(line, classes=Tcss.removed))
            else:
                static_list.append(Static(line, classes=Tcss.unchanged))
        return static_list

    # textual.textualize.io/widgets/text_area/#textual.widgets.text_area.BUILTIN_LANGUAGES
    def create_file_content_widgets(self) -> TextArea | list[Static]:
        BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}
        LANGUAGE_MAP = BUILTIN_MAP | {
            ".cfg": BUILTIN_MAP["toml"],
            ".ini": BUILTIN_MAP["toml"],
            ".sh": BUILTIN_MAP["bash"],
            ".yml": BUILTIN_MAP["yaml"],
            ".zsh": BUILTIN_MAP["bash"],
        }
        text_content = self.app.cmd.read(
            ReadCmd.cat, path_arg=self.path
        ).completed_process.stdout
        language = LANGUAGE_MAP.get(self.path.suffix.lower())
        if language is not None:
            return TextArea(text=text_content, language=language)
        else:
            rich_highlighter = ReprHighlighter()
            static_list: list[Static] = []
            for line in text_content.splitlines():
                text_obj = Text(line)
                rich_highlighter.highlight(text_obj)
                static_list.append(Static(text_obj))
            return static_list

    def create_dir_content_widgets(self) -> list[Label | Static]:
        return [
            Label("no label implemented"),
            Static(f"no static implemented for {self.path}"),
        ]


class GitLogTable(DataTable[str], AppType):
    """Contains a datatable, for a given path its ConnandResult object."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        path_arg = None if path == self.app.dest_dir else path
        self.row_color = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        self.lines = self.app.cmd.read(
            ReadCmd.cat, path_arg=path_arg
        ).completed_process.stdout.splitlines()
        self.populate_datatable()

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: list[str] = [f"[{style}]{cell_text}[/{style}]" for cell_text in columns]
        self.add_row(*row)

    def populate_datatable(self) -> None:
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
        for line in self.lines:
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, self.row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, self.row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, self.row_color["error"])
            else:
                self.add_row(*columns)
