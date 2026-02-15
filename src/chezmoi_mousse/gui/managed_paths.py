from dataclasses import dataclass
from pathlib import Path

from textual.containers import ScrollableContainer

from chezmoi_mousse import StatusCode, TabName

from .common.contents import ContentWidgetDict, DirContents, FileContents

__all__ = ["PathDict"]


@dataclass(slots=True)
class DirWidgets:
    contents: ScrollableContainer


type DirWidgetDict = dict[Path, DirWidgets]


@dataclass(slots=True)
class DirNode:
    label: str
    widgets: DirWidgets
    status_files: dict[Path, StatusCode]
    x_files: dict[Path, StatusCode]
    # True if the dir has status_files or if any subdir or file has a status other than
    # X, no matter how deeply nested
    has_status_paths: bool = False
    # True if the dir has x_files or if any subdir or file has a status with status X,
    # no matter how deeply nested
    has_x_paths: bool = False


type DirNodeDict = dict[Path, DirNode]


type StatusPath = dict[Path, StatusCode]


class PathDict:
    def __init__(
        self,
        dest_dir: Path,
        theme_variables: dict[str, str],
        managed_dirs: list[Path],
        managed_files: list[Path],
        apply_dir_status: dict[Path, StatusCode],
        apply_file_status: dict[Path, StatusCode],
        re_add_dir_status: dict[Path, StatusCode],
        re_add_file_status: dict[Path, StatusCode],
    ) -> None:
        self.dest_dir = dest_dir
        self.theme_variables = theme_variables
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.theme_variables["text-success"],
            StatusCode.Deleted: self.theme_variables["text-error"],
            StatusCode.Modified: self.theme_variables["text-warning"],
            StatusCode.No_Change: self.theme_variables["warning-darken-2"],
            StatusCode.Run: self.theme_variables["error"],
            StatusCode.X: self.theme_variables["text-secondary"],
        }
        self.managed_dirs: list[Path] = [self.dest_dir] + managed_dirs
        self.managed_files: list[Path] = managed_files
        self.status_dirs: list[Path] = list(apply_dir_status.keys())
        self.status_files: list[Path] = list(apply_file_status.keys())
        self.x_dirs: list[Path] = []
        self.x_files: list[Path] = []
        self.apply_dir_status: StatusPath = apply_dir_status
        self.apply_file_status: StatusPath = apply_file_status
        self.re_add_dir_status: StatusPath = re_add_dir_status
        self.re_add_file_status: StatusPath = re_add_file_status
        # Compute x_dirs and x_files
        for path in self.managed_dirs:
            if path not in self.status_dirs:
                self.x_dirs.append(path)
        for path in self.managed_files:
            if path not in self.status_files:
                self.x_files.append(path)
        self.contents_dict: ContentWidgetDict = {}
        self._update_contents_dict()
        self.content_widgets: ContentWidgetDict = {}
        self._update_content_widgets()
        self.apply_dir_widgets: DirWidgetDict = {}
        self.re_add_dir_widgets: DirWidgetDict = {}
        self.create_managed_dir_node_widgets()
        self.apply_dir_node_dict: DirNodeDict = {}
        self.re_add_dir_node_dict: DirNodeDict = {}
        self.create_dir_node_dict()

    def _update_contents_dict(self):
        for path in self.managed_files:
            self.contents_dict[path] = FileContents(file_path=path).widget
        for path in self.managed_dirs:
            has_status_paths = self.has_status_paths_in(path)
            has_x_paths = self.has_x_paths_in(path)
            self.contents_dict[path] = DirContents(
                dir_path=path,
                has_status_paths=has_status_paths,
                has_x_paths=has_x_paths,
                dest_dir=self.dest_dir,
            ).widget

    def _update_content_widgets(self):
        for path in self.managed_files:
            self.content_widgets[path] = FileContents(file_path=path).widget
        for path in self.managed_dirs:
            self.content_widgets[path] = DirContents(
                dest_dir=self.dest_dir,
                has_status_paths=self.has_status_paths_in(path),
                has_x_paths=self.has_x_paths_in(path),
                dir_path=path,
            ).widget

    def create_label(self, path: Path, tab_name: TabName) -> str:
        italic = " italic" if not path.exists() else ""
        apply_color = self.node_colors.get(
            self.apply_file_status.get(path, StatusCode.X)
        )
        if tab_name == TabName.apply:
            apply_color = self.node_colors.get(
                self.apply_file_status.get(path, StatusCode.X)
            )
            return f"[{apply_color}" f"{italic}]{path.name}[/]"
        elif tab_name == TabName.re_add:
            re_add_color = self.node_colors.get(
                self.re_add_file_status.get(path, StatusCode.X)
            )
            return f"[{re_add_color}" f"{italic}]{path.name}[/]"
        else:
            raise ValueError(f"Unhandled tab name: {tab_name}")

    def has_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any path with a status other than X, is a descendant of the
        # provided directory.
        return any(path.is_relative_to(dir_path) for path in self.status_files) or any(
            path.is_relative_to(dir_path) for path in self.status_dirs
        )

    def has_x_paths_in(self, dir_path: Path) -> bool:
        # Return True if any managed path is a descendant of the
        # provided directory containing paths with status X.
        return any(path.is_relative_to(dir_path) for path in self.x_files) or any(
            path.is_relative_to(dir_path) for path in self.x_dirs
        )

    def create_managed_dir_node_widgets(self):
        for dir_path in self.managed_dirs:
            has_status_paths = self.has_status_paths_in(dir_path)
            has_x_paths = self.has_x_paths_in(dir_path)
            dir_content_widgets = DirContents(
                dir_path=dir_path,
                has_status_paths=has_status_paths,
                has_x_paths=has_x_paths,
                dest_dir=self.dest_dir,
            )
            self.apply_dir_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container
            )
            self.re_add_dir_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container
            )

    def create_dir_node_dict(self):
        for dir_path, dir_widgets in self.apply_dir_widgets.items():
            status_files: dict[Path, StatusCode] = {
                path: status
                for path, status in self.apply_file_status.items()
                if path.parent == dir_path
            }
            x_files: dict[Path, StatusCode] = {
                path: status
                for path, status in self.apply_file_status.items()
                if path.parent == dir_path
            }
            self.apply_dir_node_dict[dir_path] = DirNode(
                label=self.create_label(dir_path, TabName.apply),
                widgets=dir_widgets,
                status_files=status_files,
                x_files=x_files,
                has_status_paths=self.has_status_paths_in(dir_path),
                has_x_paths=self.has_x_paths_in(dir_path),
            )
        for dir_path, dir_widgets in self.re_add_dir_widgets.items():
            status_files: dict[Path, StatusCode] = {
                path: status
                for path, status in self.re_add_file_status.items()
                if path.parent == dir_path
            }
            x_files: dict[Path, StatusCode] = {
                path: status
                for path, status in self.re_add_file_status.items()
                if path.parent == dir_path
            }
            self.re_add_dir_node_dict[dir_path] = DirNode(
                label=self.create_label(dir_path, TabName.re_add),
                widgets=dir_widgets,
                status_files=status_files,
                x_files=x_files,
                has_status_paths=self.has_status_paths_in(dir_path),
                has_x_paths=self.has_x_paths_in(dir_path),
            )
