# We need 3 factories which each should accept a CommandResults object.
# content: list[Label | Static | TextArea]
# diff: list[Label | Static]
# git_log: DataTable[str]

from dataclasses import dataclass
from pathlib import Path

# from rich.highlighter import ReprHighlighter
# from rich.text import Text
from textual.widgets import DataTable, Static, TextArea

from ._chezmoi_command import CommandResult, ReadCmd
from ._str_enum_names import TabName
from ._str_enums import StatusCode
from ._type_checking import AppType

# from textual.widgets.text_area import BUILTIN_LANGUAGES


__all__ = ["DirNodeDict"]


@dataclass(slots=True)
class PathData:
    contents: list[Static] | TextArea
    diff: list[Static]
    git_log: DataTable[str]
    label: str
    status: StatusCode


type FileNodeDict = dict[Path, PathData]


@dataclass(slots=True)
class DirData:
    files: FileNodeDict
    widgets: PathData


class DirNodeDict(AppType):

    dest_dir: Path

    def __init__(
        self,
        git_log_cmd_result: CommandResult,
        managed_dirs_cmd_result: CommandResult,
        managed_files_cmd_result: CommandResult,
        status_dirs_cmd_result: CommandResult,
        status_files_cmd_result: CommandResult,
        tab_name: TabName,
    ) -> None:
        self.git_log = git_log_cmd_result
        self.managed_dirs = managed_dirs_cmd_result
        self.managed_files = managed_files_cmd_result
        self.status_dirs = status_dirs_cmd_result
        self.status_files = status_files_cmd_result
        self.tab_name = tab_name
        # dir_path: Path, dir_files: list[Path], status_pair: tuple[str, str]
        # self.path_widgets: PathData = self.create_widgets()
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["warning-darken-2"],
            StatusCode.X: self.app.theme_variables["foreground-darken-3"],
        }
        self.dir_with_status_children_color = self.app.theme_variables["text-secondary"]

    # def create_dir_widgets(self):

    #     path_contents = self.create_dir_content_widgets()
    #     label_str = (self.path.name,)  # to be constructed based status_code and exists
    #     contents = (path_contents,)
    #     diff_apply = (self.create_diff_statics(reverse=False),)
    #     diff_reverse = (self.create_diff_statics(reverse=True),)
    #     git_log = (GitLogTable(self.path),)
    #     status_apply = (StatusCode(self.status_pair[0]),)
    #     status_other = (StatusCode(self.status_pair[1]),)

    # def create_file_widgets(self):
    #     path_contents = self.create_dir_content_widgets()
    #     label_str = (self.path.name,)  # to be constructed based status_code and exists
    #     contents = (path_contents,)
    #     diff_apply = (self.create_diff_statics(reverse=False),)
    #     diff_reverse = (self.create_diff_statics(reverse=True),)
    #     git_log = (GitLogTable(self.path),)
    #     status_apply = (StatusCode(self.status_pair[0]),)
    #     status_other = (StatusCode(self.status_pair[1]),)

    # def create_label_string(self) -> None:
    #     if self.path.exists():
    #         italic = " italic" if not self.path.exists() else ""
    #         color = self.node_colors[tree_node.data.status]
    #         node_label = f"[{color}" f"{italic}]{tree_node.data.path.name}[/]"
    #         if tree_node.data.path_kind == PathKind.FILE:
    #             tree_node.add_leaf(label=node_label, data=tree_node.data)
    #         else:
    #             tree_node.add(label=node_label, data=tree_node.data)

    # def create_diff_statics(self, reverse: bool) -> list[Static]:
    #     # green: "+", "new"
    #     # red: "-", "old", "deleted"
    #     # orange: "changed"
    #     # dimmed: " ", "index"
    #     static_list: list[Static] = []
    #     diff_result = (
    #         (self.app.cmd.read(ReadCmd.diff, path_arg=self.path))
    #         if reverse is False
    #         else (self.app.cmd.read(ReadCmd.diff_reverse, path_arg=self.path))
    #     )
    #     for line in diff_result.completed_process.stdout.splitlines():
    #         if line.startswith(("+", "new")):
    #             static_list.append(Static(line, classes=Tcss.added))
    #         elif line.startswith(("-", "old", "deleted")):
    #             static_list.append(Static(line, classes=Tcss.removed))
    #         else:
    #             static_list.append(Static(line, classes=Tcss.unchanged))
    #     return static_list

    # # textual.textualize.io/widgets/text_area/#textual.widgets.text_area.BUILTIN_LANGUAGES
    # def create_file_content_widgets(self) -> TextArea | list[Static]:
    #     BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}
    #     LANGUAGE_MAP = BUILTIN_MAP | {
    #         ".cfg": BUILTIN_MAP["toml"],
    #         ".ini": BUILTIN_MAP["toml"],
    #         ".sh": BUILTIN_MAP["bash"],
    #         ".yml": BUILTIN_MAP["yaml"],
    #         ".zsh": BUILTIN_MAP["bash"],
    #     }
    #     text_content = self.app.cmd.read(
    #         ReadCmd.cat, path_arg=self.path
    #     ).completed_process.stdout
    #     language = LANGUAGE_MAP.get(self.path.suffix.lower())
    #     if language is not None:
    #         return TextArea(text=text_content, language=language)
    #     else:
    #         rich_highlighter = ReprHighlighter()
    #         static_list: list[Static] = []
    #         for line in text_content.splitlines():
    #             text_obj = Text(line)
    #             rich_highlighter.highlight(text_obj)
    #             static_list.append(Static(text_obj))
    #         return static_list

    # def create_dir_content_widgets(self) -> list[Label | Static]:
    #     return [
    #         Label("no label implemented"),
    #         Static(f"no static implemented for {self.path}"),
    #     ]


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
