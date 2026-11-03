import math
import random
import shutil
import stat
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from rich.markup import escape

from chezmoi_mousse import path_funcs
from chezmoi_mousse.debug import test_path_funcs as gen_path
from chezmoi_mousse.str_enums import ColorVar, PathFilters

__all__ = ["TestPaths"]

HOME_DIR = Path.home()
TXT: str = ".txt"
BIN: str = ".bin"
SMALL = 10 * 1024
MEDIUM = 50 * 1024
LARGE = 500 * 1024
HUGE = 2500 * 1024


@dataclass
class _TestDirPaths:
    _base_test: Path = field(default=gen_path.dir_path(HOME_DIR, None, depth=0))
    _base_depth: int = field(default_factory=int)
    _single_child_depth: int = field(default_factory=int)
    un_wanted_name: str = PathFilters.UNWANTED_DIRS.value[0].replace("_test_dir_", "")
    home_un_wanted_dir: Path = field(
        default=gen_path.dir_path(HOME_DIR, un_wanted_name, depth=0)
    )
    large_diff: Path = field(
        default=gen_path.dir_path(HOME_DIR, "large_diffs", depth=0)
    )
    paths: list[Path] = field(default_factory=list[Path])

    def __post_init__(self) -> None:
        self._base_depth = len(self._base_test.parts)
        self._single_child_depth = self._base_depth + 3
        self.paths.append(self.large_diff)
        self.paths.append(self._base_test)
        self.paths.append(self.home_un_wanted_dir)
        self.paths.extend(self._generate_dynamic_dir_names())
        self.paths = path_funcs.sort_paths(self.paths)

    def _generate_dynamic_dir_names(self) -> list[Path]:
        generated_paths: list[Path] = []
        current_base: Path = self._base_test
        start_depth = self._base_depth - len(HOME_DIR.parts)
        for depth_idx in range(start_depth, start_depth + 6):
            nested_path = gen_path.dir_path(current_base, None, depth=depth_idx)
            unwanted_path = gen_path.dir_path(
                current_base, self.un_wanted_name, depth=depth_idx
            )
            # The single child dir has no siblings and only one nested dir.
            if self._single_child_depth in (
                len(nested_path.parts),
                len(current_base.parts),
            ):
                generated_paths.append(nested_path)
                current_base = nested_path
                continue
            if depth_idx % 2 != 0:
                generated_paths.extend([unwanted_path, nested_path])
                current_base = nested_path
                continue
            sibling = gen_path.dir_path(
                current_base, None, depth=depth_idx, sibling=True
            )
            generated_paths.extend([nested_path, sibling])
            current_base = nested_path
        return generated_paths

    @cached_property
    def test_dirs(self) -> list[Path]:
        return [
            p
            for p in self.paths
            if p != self.home_un_wanted_dir and p != self.large_diff
        ]

    @cached_property
    def dirs_for_normal_diff_files(self) -> list[Path]:
        return [
            p
            for p in self.paths
            if p != self.large_diff
            and not self.un_wanted_name in str(p)
            and len(p.parts) != self._single_child_depth
        ]

    @cached_property
    def dirs_for_normal_bin_files(self) -> list[Path]:
        return [p for p in self.paths if "sibling" in p.name]

    @cached_property
    def nested_un_wanted_dirs(self) -> list[Path]:
        return [
            p
            for p in self.paths
            if self.un_wanted_name in str(p) and p.is_relative_to(self._base_test)
        ]


@dataclass
class _TestFileData:
    small_name: str = gen_path.file_name("small", TXT)
    small: str = gen_path.initial_text(SMALL)
    _medium_name: str = gen_path.file_name("medium", TXT)
    _medium: str = gen_path.initial_text(MEDIUM)
    large_name: str = gen_path.file_name("large", TXT)
    large: str = gen_path.initial_text(LARGE)

    _huge_name: str = gen_path.file_name("huge", TXT)
    _huge: str = gen_path.initial_text(HUGE)
    _tricky_utf8_name: str = gen_path.file_name("tricky_utf8", TXT)
    _tricky_utf8: str = gen_path.tricky_utf8_text()
    un_wanted_name: str = PathFilters.UN_WANTED_TEST_FILE.value
    un_wanted: str = gen_path.initial_text(SMALL)

    _control_chars_name: str = gen_path.file_name("control_chars", BIN)
    _control_chars: bytes = gen_path.control_chars_bytes(SMALL)
    _high_entropy_name: str = gen_path.file_name("high_entropy", BIN)
    _high_entropy: bytes = gen_path.high_entropy_bytes(SMALL)
    _invalid_utf8_name: str = gen_path.file_name("invalid_utf8", BIN)
    _invalid_utf8: bytes = gen_path.invalid_utf8_bytes(SMALL)
    _null_bytes_name: str = gen_path.file_name("null_bytes", BIN)
    _null_bytes: bytes = gen_path.null_bytes(SMALL)
    _printable_ascii_name: str = gen_path.file_name("printable_ascii", BIN)
    _printable_ascii: bytes = gen_path.printable_ascii_bytes(SMALL)
    _utf16_interleaved_name: str = gen_path.file_name("utf16_interleaved", BIN)
    _utf16_interleaved: bytes = gen_path.utf16_interleaved_bytes(SMALL)

    _file_name_map: dict[str, str | bytes] = field(
        default_factory=dict[str, str | bytes]
    )

    def __post_init__(self) -> None:
        self._file_name_map[self._tricky_utf8_name] = self._tricky_utf8
        self._file_name_map[self.un_wanted_name] = self.un_wanted
        self._file_name_map[self._invalid_utf8_name] = self._invalid_utf8
        self._file_name_map[self._control_chars_name] = self._control_chars
        self._file_name_map[self._high_entropy_name] = self._high_entropy
        self._file_name_map[self._null_bytes_name] = self._null_bytes
        self._file_name_map[self._printable_ascii_name] = self._printable_ascii
        self._file_name_map[self._utf16_interleaved_name] = self._utf16_interleaved
        self._file_name_map[self.small_name] = self.small
        self._file_name_map[self._medium_name] = self._medium
        self._file_name_map[self.large_name] = self.large
        self._file_name_map[self._huge_name] = self._huge

    @cached_property
    def un_wanted_files(self) -> dict[str, str | bytes]:
        un_wanted_names = [
            self._huge_name,
            self.un_wanted_name,
            self._invalid_utf8_name,
        ]
        return {k: v for k, v in self._file_name_map.items() if k in un_wanted_names}

    @cached_property
    def normal_diff_files(self) -> dict[str, str]:
        diff_names = [self._medium_name, self.small_name]
        return {
            k: v
            for k, v in self._file_name_map.items()
            if k in diff_names and isinstance(v, str)
        }

    @cached_property
    def normal_bin_files(self) -> dict[str, bytes]:
        bin_names = [
            fn
            for fn in self._file_name_map
            if fn.endswith(BIN) and fn != self._invalid_utf8_name
        ]
        return {
            k: v
            for k, v in self._file_name_map.items()
            if k in bin_names and isinstance(v, bytes)
        }


@dataclass
class _AllTestPaths:
    files = _TestFileData()
    dirs = _TestDirPaths()
    file_paths: dict[Path, str | bytes] = field(default_factory=dict[Path, str | bytes])

    def __post_init__(self) -> None:
        self.file_paths[HOME_DIR / self.files.small_name] = self.files.small
        self.file_paths[HOME_DIR / self.files.un_wanted_name] = self.files.un_wanted
        dirs_for_normal_diff_files = self.dirs.dirs_for_normal_diff_files
        for path in self.dirs.paths:
            if path == self.dirs.home_un_wanted_dir:
                self.file_paths.update(self._get_normal_bin_paths(path))
            if (
                path == self.dirs.home_un_wanted_dir
                or path in self.dirs.nested_un_wanted_dirs
            ):
                self.file_paths.update(self._get_un_wanted_paths(path))
            if path in dirs_for_normal_diff_files:
                self.file_paths.update(self._get_normal_diff_paths(path))
            if path in self.dirs.dirs_for_normal_bin_files:
                self.file_paths.update(self._random_bin_path(path))
            if path == self.dirs.large_diff:
                self.file_paths.update({path / self.files.large_name: self.files.large})
        self.file_paths = path_funcs.sort_path_dict(self.file_paths)

    def _get_normal_bin_paths(self, base_dir: Path) -> dict[Path, str | bytes]:
        return {
            base_dir / file_name: file_content
            for file_name, file_content in self.files.normal_bin_files.items()
        }

    def _get_un_wanted_paths(self, base_dir: Path) -> dict[Path, str | bytes]:
        return {
            base_dir / file_name: file_content
            for file_name, file_content in self.files.un_wanted_files.items()
        }

    def _get_normal_diff_paths(self, base_dir: Path) -> dict[Path, str | bytes]:
        return {
            base_dir / file_name: file_content
            for file_name, file_content in self.files.normal_diff_files.items()
        }

    @property
    def existing_dirs(self) -> set[Path]:
        return {path for path in self.dirs.paths if path.exists()}

    @property
    def missing_dirs(self) -> set[Path]:
        return {path for path in self.dirs.paths if not path.exists()}

    @property
    def existing_files(self) -> set[Path]:
        return {path for path in self.file_paths if path.exists()}

    @property
    def missing_files(self) -> set[Path]:
        return {path for path in self.file_paths if not path.exists()}

    @property
    def files_for_diff(self) -> set[Path]:
        return {
            p
            for p in self.file_paths
            if p.suffix == TXT and p.name not in self.files.un_wanted_files
        }

    def get_random_dir_to_delete(self) -> Path | None:
        existing_dirs = list(self.existing_dirs)
        eligible = [d for d in existing_dirs if d in self.dirs.test_dirs]
        if not eligible:
            return None
        return random.choice(eligible)

    def get_random_dir_to_create(self) -> Path | None:
        missing_dirs = self.missing_dirs
        eligible = [d for d in missing_dirs if d in self.dirs.test_dirs]
        if not eligible:
            return None
        return random.choice(eligible)

    def _random_bin_path(self, dir_path: Path) -> dict[Path, bytes]:
        # Seed with the dir path so each dir gets the same file on every run.
        name = random.Random(str(dir_path)).choice(list(self.files.normal_bin_files))
        return {dir_path / name: self.files.normal_bin_files[name]}

    def get_random_files_to_delete(self, target: float) -> list[Path] | None:
        existing_files = list(self.existing_files)
        eligible = [
            f
            for f in existing_files
            if f.parent == HOME_DIR or f.parent in self.dirs.test_dirs
        ]
        if not eligible:
            return None
        k = self._random_file_count(target)
        return random.sample(eligible, k=min(k, len(eligible)))

    def get_random_files_to_create(self, target: float) -> list[Path]:
        missing_files = self.missing_files
        existing_dirs = self.existing_dirs
        eligible = [
            f
            for f in missing_files
            if f.parent in existing_dirs or f.parent == HOME_DIR
        ]
        k = self._random_file_count(target)
        return random.sample(eligible, k=min(k, len(eligible)))

    def _random_file_count(self, target: float) -> int:
        # Change a random 15-30% (for target 0.7) of all files per call, so the
        # share of existing files swings around the target.
        max_count = math.floor(len(self.file_paths) * (1 - target))
        return random.randint(max(1, math.ceil(max_count / 2)), max(1, max_count))


class TestPaths:
    def __init__(self) -> None:
        self.paths = _AllTestPaths()
        self.no_existing_msg = f"[${ColorVar.text_warning}]No test paths exist[/]"
        self.no_missing_msg = f"[${ColorVar.text_warning}]All test paths exist[/]"

    def _get_file_lines(self, dir_path: Path, files: set[Path]) -> list[str]:
        children = {path for path in files if path.parent == dir_path}
        return [escape(str(path)) for path in path_funcs.sort_paths(children)]

    def _report_existing_paths(self, dirs: set[Path], files: set[Path]) -> list[str]:
        lines: list[str] = []
        lines.extend(self._get_file_lines(HOME_DIR, files))
        for path in path_funcs.sort_paths(dirs):
            lines.append(f"[${ColorVar.text_primary}]{escape(str(path))}[/]")
            lines.extend(self._get_file_lines(path, files))
        return lines

    def _report_missing_paths(self, dirs: set[Path], files: set[Path]) -> list[str]:
        lines: list[str] = []
        parent_dirs = {path.parent for path in files}
        for path in path_funcs.sort_paths(dirs | parent_dirs):
            if path in dirs:
                lines.append(f"[${ColorVar.text_primary}]{escape(str(path))}[/]")
            lines.extend(self._get_file_lines(path, files))
        return lines

    def report_test_paths(self) -> str:
        lines: list[str] = []
        existing_dirs = self.paths.existing_dirs
        existing_files = self.paths.existing_files
        if not (existing_dirs | existing_files):
            lines.append(self.no_existing_msg)
        else:
            lines.append(f"[${ColorVar.text_success}]Existing test paths:[/]")
            lines.extend(self._report_existing_paths(existing_dirs, existing_files))
        missing_dirs = self.paths.missing_dirs
        missing_files = self.paths.missing_files
        if not (missing_dirs | missing_files):
            lines.append(self.no_missing_msg)
        else:
            lines.append(f"[${ColorVar.text_success}]Missing test paths:[/]")
            lines.extend(self._report_missing_paths(missing_dirs, missing_files))
        return "\n".join(lines)

    def create_missing_test_paths(self) -> str:
        lines: list[str] = []
        missing_dirs_before = self.paths.missing_dirs
        missing_files_before = self.paths.missing_files
        if not (missing_dirs_before | missing_files_before):
            return f"[${ColorVar.text_warning}]All test paths already exist[/]"
        all_test_dirs = self.paths.dirs.paths
        for path in all_test_dirs:
            path.mkdir(parents=True, exist_ok=True)
        for path in missing_files_before:
            self._write_file(path, self.paths.file_paths[path])
        missing_dirs_after = self.paths.missing_dirs
        missing_files_after = self.paths.missing_files
        created_dirs = missing_dirs_before - missing_dirs_after
        created_files = missing_files_before - missing_files_after
        if not (created_dirs | created_files):
            return f"[${ColorVar.text_warning}]No test paths were created[/]"
        lines.append(f"[${ColorVar.text_success}]Created test paths:[/]")
        # Use _report_missing_paths so created files whose parent dir already
        # existed are reported too.
        lines.extend(self._report_missing_paths(created_dirs, created_files))
        return "\n".join(lines)

    def remove_existing_test_paths(self) -> str:
        lines: list[str] = []
        existing_dirs_before = self.paths.existing_dirs
        existing_files_before = self.paths.existing_files
        if not (existing_dirs_before | existing_files_before):
            return self.no_existing_msg
        top_level = path_funcs.get_common_top_level(dir_paths=existing_dirs_before)
        for path in top_level:
            assert path != HOME_DIR
            shutil.rmtree(path)
        for path in self.paths.existing_files:
            path.unlink()
        existing_dirs = self.paths.existing_dirs
        existing_files = self.paths.existing_files
        if existing_dirs | existing_files:
            lines.append(f"[${ColorVar.text_warning}]Some paths were not removed![/]")
            lines.extend(self._report_existing_paths(existing_dirs, existing_files))
        removed_dirs = existing_dirs_before - existing_dirs
        removed_files = existing_files_before - existing_files
        if not (removed_dirs | removed_files):
            lines.append(f"[${ColorVar.text_error}]No paths were removed[/]")
        else:
            lines.append(f"[${ColorVar.text_success}]Removed paths:[/]")
            lines.extend(self._report_missing_paths(removed_dirs, removed_files))
        return "\n".join(lines)

    def _write_file(self, path: Path, contents: str | bytes) -> None:
        if isinstance(contents, bytes):
            path.write_bytes(contents)
        else:
            path.write_text(contents, encoding="utf-8")

    def _add_remove_random_dir(
        self, existing: set[Path], missing: set[Path]
    ) -> list[str]:
        lines: list[str] = []
        removed: set[Path] = set()
        added: set[Path] = set()
        reduce = len(existing) / (len(existing) + len(missing)) > 0.7
        if reduce:
            dir_to_delete = self.paths.get_random_dir_to_delete()
            if dir_to_delete:
                shutil.rmtree(dir_to_delete)
                removed = existing - self.paths.existing_dirs
        else:
            dir_to_create = self.paths.get_random_dir_to_create()
            if dir_to_create:
                dir_to_create.mkdir(parents=True)
            added = missing - self.paths.missing_dirs
        if not added and not removed:
            lines.append(
                f"[${ColorVar.text_warning}]No directories were added or removed[/]"
            )
            return lines
        if added:
            lines.append(f"[${ColorVar.text_success}]Added directories:[/]")
            lines.extend(escape(str(p)) for p in path_funcs.sort_paths(added))
        elif removed:
            lines.append(f"[${ColorVar.text_success}]Removed directories:[/]")
            lines.extend(escape(str(p)) for p in path_funcs.sort_paths(removed))
        return lines

    def _add_remove_random_files(
        self, existing: set[Path], missing: set[Path]
    ) -> list[str]:
        lines: list[str] = []
        removed: set[Path] = set()
        added: set[Path] = set()
        should_exist_ratio = 0.7
        reduce = len(existing) / (len(existing) + len(missing)) > should_exist_ratio
        if reduce:
            files_to_delete = self.paths.get_random_files_to_delete(should_exist_ratio)
            if files_to_delete:
                for f in files_to_delete:
                    f.unlink(missing_ok=True)
                removed = set(files_to_delete)
        else:
            file_to_create = self.paths.get_random_files_to_create(should_exist_ratio)
            if file_to_create:
                for f in file_to_create:
                    self._write_file(f, self.paths.file_paths[f])
                added = set(file_to_create)
        if not added and not removed:
            lines.append(f"[${ColorVar.text_warning}]No files were added or removed[/]")
            return lines
        if added:
            lines.append(f"[${ColorVar.text_success}]Added files:[/]")
            lines.extend(escape(str(p)) for p in path_funcs.sort_paths(added))
        if removed:
            lines.append(f"[${ColorVar.text_success}]Removed files:[/]")
            lines.extend(escape(str(p)) for p in path_funcs.sort_paths(removed))
        return lines

    def _toggle_file_diffs(self) -> list[str]:
        lines: list[str] = []
        all_files_for_diff = self.paths.files_for_diff
        eligible_files = [p for p in all_files_for_diff if p.exists()]
        if not eligible_files:
            return [f"[${ColorVar.text_warning}]No existing files without a status[/]"]
        desired_k = int(len(eligible_files) / 2)
        if desired_k <= 0:
            return [f"[${ColorVar.text_warning}]Not enough eligible files to toggle[/]"]
        paths_to_toggle = random.sample(eligible_files, k=desired_k)
        for path in paths_to_toggle:
            current_content = path.read_text(encoding="utf-8")
            if "LOREM" in current_content:
                current_content = current_content.replace("LOREM", "lorem")
            elif "lorem" in current_content:
                current_content = current_content.replace("lorem", "LOREM")
            path.write_text(current_content, encoding="utf-8")
        lines.append(f"[${ColorVar.text_success}]Toggled files:[/]")
        lines.extend(escape(str(p)) for p in path_funcs.sort_paths(paths_to_toggle))
        return lines

    def _change_random_dir_permission(self, existing_dirs: set[Path]) -> str:
        eligible = [d for d in self.paths.dirs.test_dirs if d in existing_dirs]
        if not eligible:
            return f"[${ColorVar.text_warning}]No eligible dirs to create a diff for[/]"
        directory = random.choice(eligible)
        mode = stat.S_IMODE(directory.stat().st_mode)
        directory.chmod(0o750 if mode == 0o755 else 0o755)
        dir_str = escape(str(directory))
        return f"[${ColorVar.text_success}]Changed permission for {dir_str}[/]"

    def create_diffs(self) -> str:
        lines: list[str] = []
        existing_dirs = self.paths.existing_dirs
        missing_dirs = self.paths.missing_dirs
        lines.extend(self._add_remove_random_dir(existing_dirs, missing_dirs))
        existing_files = self.paths.existing_files
        missing_files = self.paths.missing_files
        lines.extend(self._add_remove_random_files(existing_files, missing_files))
        lines.extend(self._toggle_file_diffs())
        lines.append(self._change_random_dir_permission(self.paths.existing_dirs))
        return "\n".join(lines)
