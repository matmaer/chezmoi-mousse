from dataclasses import dataclass
from pathlib import Path

from ._str_enum_names import PathKind
from ._str_enums import StatusCode

type PathNodeDict = dict[Path, PathNode]
type PathNodeList = list[PathNode]

__all__ = ["ChezmoiPathNodes"]


@dataclass(slots=True)
class PathNode:
    found: bool
    # Chezmoi status codes processed: A, D, M, or a space
    # Additional "node status" codes: X (no status but managed)
    path_kind: PathKind
    status_pair: tuple[StatusCode, StatusCode]


class ChezmoiPathNodes:
    def __init__(self, path_nodes: PathNodeDict = {}) -> None:
        self.path_nodes: PathNodeDict = path_nodes
        self.changed_node_paths: PathNodeDict = {}
        self.removed_nodes: PathNodeDict = {}

    @property
    def dirs(self) -> PathNodeDict:
        return {
            path: node
            for path, node in self.path_nodes.items()
            if node.path_kind == PathKind.DIR
        }

    @property
    def files(self) -> PathNodeDict:
        return {
            path: node
            for path, node in self.path_nodes.items()
            if node.path_kind == PathKind.FILE
        }

    @property
    def status_dirs(self) -> PathNodeDict:
        return {
            path: node
            for path, node in self.path_nodes.items()
            if node.path_kind == PathKind.DIR
            and node.status_pair != (StatusCode.dir_no_status, StatusCode.dir_no_status)
        }

    @property
    def status_files(self) -> PathNodeDict:
        return {
            path: node
            for path, node in self.path_nodes.items()
            if node.path_kind == PathKind.FILE
            and node.status_pair
            != (StatusCode.file_no_status, StatusCode.file_no_status)
        }

    @property
    def no_status_dirs(self) -> PathNodeDict:
        return {
            path: node
            for path, node in self.path_nodes.items()
            if node.path_kind == PathKind.DIR
            and node.status_pair == (StatusCode.dir_no_status, StatusCode.dir_no_status)
        }

    @property
    def no_status_files(self) -> PathNodeDict:
        return {
            path: node
            for path, node in self.path_nodes.items()
            if node.path_kind == PathKind.FILE
            and node.status_pair
            == (StatusCode.file_no_status, StatusCode.file_no_status)
        }

    def _create_path_node(
        self,
        parsed_path: Path,
        *,
        path_kind: PathKind,
        status_pair: tuple[StatusCode, StatusCode],
    ) -> PathNode:
        new_node = PathNode(
            # path=parsed_path,
            path_kind=path_kind,
            found=parsed_path.exists(),
            status_pair=status_pair,
        )
        if parsed_path in self.path_nodes.keys():
            existing_node = self.path_nodes[parsed_path]
            # changed
            if new_node != existing_node:
                self.changed_node_paths[parsed_path] = new_node
        elif parsed_path not in self.path_nodes.keys():
            # new node
            self.changed_node_paths[parsed_path] = new_node
        return new_node

    def create_file_nodes(
        self, *, managed_files: str, status_files: str
    ) -> PathNodeDict:
        file_node_dict: PathNodeDict = {}
        file_node_list: PathNodeList = []
        # Parse status files
        for line in status_files.splitlines():
            file_path = Path(line[3:])
            file_node_list.append(
                self._create_path_node(
                    file_path,
                    path_kind=PathKind.FILE,
                    status_pair=(StatusCode(line[0]), StatusCode(line[1])),
                )
            )
            file_node_dict[file_path] = self._create_path_node(
                file_path,
                path_kind=PathKind.FILE,
                status_pair=(StatusCode(line[0]), StatusCode(line[1])),
            )
        # Parse managed files without status
        for line in managed_files.splitlines():
            if Path(line) in file_node_dict.keys():
                # Avoid overwriting parsed files with status as they also appear in
                # the managed files command output.
                continue
            file_node_dict[Path(line)] = self._create_path_node(
                Path(line),
                path_kind=PathKind.FILE,
                status_pair=StatusCode.file_no_status_pair(),
            )
        return dict(sorted(file_node_dict.items()))

    def create_dir_nodes(
        self, *, managed_dirs: str, status_dirs: str, file_node_dict: PathNodeDict
    ) -> PathNodeDict:
        dir_node_dict: PathNodeDict = {}
        # Parse status dirs
        for line in status_dirs.splitlines():
            # No check for existing entries as we didn't process any dirs yet.
            dir_path = Path(line[3:])
            dir_node_dict[dir_path] = self._create_path_node(
                dir_path,
                path_kind=PathKind.DIR,
                status_pair=(StatusCode(line[0]), StatusCode(line[1])),
            )
        # Parse managed dirs without status
        no_status_pairs = {
            StatusCode.file_no_status_pair(),
            StatusCode.dir_no_status_pair(),
        }
        for line in managed_dirs.splitlines():
            # First determine if the directory has any files or directories, no matter
            # how deeply nested with a status.
            dir_path = Path(line)
            has_status_descendants = any(
                dir_path in path.parents
                and path_node.status_pair not in no_status_pairs
                for path, path_node in list(dir_node_dict.items())
                + list(file_node_dict.items())
            )
            if has_status_descendants and dir_path not in dir_node_dict:
                dir_node_dict[dir_path] = self._create_path_node(
                    dir_path,
                    path_kind=PathKind.DIR,
                    status_pair=StatusCode.dir_with_status_children_pair(),
                )
        # Remaining managed dirs not yet in dir_node_dict, get a no-status status pair.
        for line in managed_dirs.splitlines():
            dir_path = Path(line)
            if dir_path in dir_node_dict.keys():
                # Avoid overwriting parsed dirs with status or status_parent as they
                # also appear in the managed dirs command output.
                continue
            dir_node_dict[dir_path] = self._create_path_node(
                dir_path,
                path_kind=PathKind.DIR,
                status_pair=StatusCode.dir_no_status_pair(),
            )
        return dir_node_dict

    def update_path_dict(
        self,
        *,
        managed_dirs: str,
        managed_files: str,
        status_dirs: str,
        status_files: str,
    ) -> None:
        self.changed_node_paths.clear()
        # Parse status files and managed files
        file_node_dict = self.create_file_nodes(
            managed_files=managed_files, status_files=status_files
        )
        # Parse status dirs and managed dirs
        dir_node_dict = self.create_dir_nodes(
            managed_dirs=managed_dirs,
            status_dirs=status_dirs,
            file_node_dict=file_node_dict,
        )
        self.path_nodes = {**dir_node_dict, **file_node_dict}

    def managed_paths_in(self, dir_path: Path, recursive: bool = False) -> PathNodeDict:
        if recursive:
            return {
                path: self.path_nodes[path]
                for path in self.path_nodes.keys()
                if dir_path in path.parents
            }
        return {
            path: self.path_nodes[path]
            for path in self.path_nodes.keys()
            if path.parent == dir_path
        }

    def status_paths_in(self, dir_path: Path, recursive: bool = False) -> PathNodeDict:
        # Return all paths with a status in the provided directory, recursively or not.
        managed_children = self.managed_paths_in(dir_path, recursive)
        no_status_pairs = {
            StatusCode.file_no_status_pair(),
            StatusCode.dir_no_status_pair(),
        }
        return {
            path: path_node
            for path, path_node in managed_children.items()
            if path_node.status_pair not in no_status_pairs
        }

    def paths_without_status_in(
        self, dir_path: Path, recursive: bool = False
    ) -> PathNodeDict:
        # Used when toggling the "show unchanged" switch for the Tree widgets.
        managed_children = self.managed_paths_in(dir_path, recursive)
        no_status_pairs = {
            StatusCode.file_no_status_pair(),
            StatusCode.dir_no_status_pair(),
        }
        return {
            path: path_node
            for path, path_node in managed_children.items()
            if path_node.status_pair in no_status_pairs
        }

    def has_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any status path is a descendant of the
        # provided directory.
        no_status_pairs = {
            StatusCode.file_no_status_pair(),
            StatusCode.dir_no_status_pair(),
        }
        return any(
            dir_path in path.parents
            for path, node_data in self.path_nodes.items()
            if node_data.status_pair not in no_status_pairs
        )

    def list_status_paths_in(
        self, dir_path: Path, recursive: bool = True
    ) -> PathNodeDict:
        # When operating on a directory, we may want to list all status paths
        # that are descendants of that directory as most chezmoi commands have the
        # default --recursive flag.
        no_status_pairs = {
            StatusCode.file_no_status_pair(),
            StatusCode.dir_no_status_pair(),
        }
        if recursive:
            return {
                path: path_node
                for path, path_node in self.path_nodes.items()
                if dir_path in path.parents
                and path_node.status_pair not in no_status_pairs
            }
        return {
            path: path_node
            for path, path_node in self.path_nodes.items()
            if path.parent == dir_path and path_node.status_pair not in no_status_pairs
        }
