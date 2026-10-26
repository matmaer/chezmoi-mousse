import random
import shutil
import stat
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from rich.markup import escape

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import ColorVar, ProblemChars, TestDir, TestFile

__all__ = ["TestPaths"]

HOME_DIR = Path.home()


class _TestFileContents:
    def __init__(self) -> None:
        self.bin_file_size: int = 10000
        self.rng = random.Random(42)
        self._words = [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
        ]
        self._initial_small = self._generate_initial_text(TestFile.small_file)
        self._initial_medium = self._generate_initial_text(TestFile.medium_file)
        self._initial_large = self._generate_initial_text(TestFile.large_file)
        self._initial_huge = self._generate_initial_text(TestFile.huge_file)
        self._tricky_utf8 = self._generate_tricky_utf8_text()

        self._diff_small = self._initial_small.replace("lorem", "LOREM")
        self._diff_medium = self._initial_medium.replace("lorem", "LOREM")
        self._diff_large = self._initial_large.replace("lorem", "LOREM")

        self._control_chars_file = self._get_control_chars_bytes()
        self._high_entropy_file = self._get_high_entropy_bytes()
        self._invalid_utf8_file = self._get_invalid_utf8_bytes()
        self._null_bytes_file = self._get_null_bytes()
        self._printable_ascii_file = self._get_printable_ascii_bytes()
        self._utf16_interleaved_file = self._get_utf16_interleaved_bytes()

    @property
    def initial_map(self) -> dict[str, str | bytes]:
        file_name_map: dict[str, str | bytes] = {
            TestFile.small_file: self._initial_small,
            TestFile.small_1_file: self._initial_small,
            TestFile.small_2_file: self._initial_small,
            TestFile.small_3_file: self._initial_small,
            TestFile.medium_file: self._initial_medium,
            TestFile.large_file: self._initial_large,
            TestFile.huge_file: self._initial_huge,
            TestFile.tricky_utf8_file: self._tricky_utf8,
            TestFile.wanted_file: self._initial_small,
            TestFile.control_chars_file: self._control_chars_file,
            TestFile.high_entropy_file: self._high_entropy_file,
            TestFile.invalid_utf8_file: self._invalid_utf8_file,
            TestFile.null_bytes_file: self._null_bytes_file,
            TestFile.printable_ascii_file: self._printable_ascii_file,
            TestFile.utf16_interleaved_file: self._utf16_interleaved_file,
        }
        return file_name_map

    @property
    def old_diff_map(self) -> dict[str, str]:
        return {
            TestFile.small_file: self._initial_small,
            TestFile.small_1_file: self._initial_small,
            TestFile.small_2_file: self._initial_small,
            TestFile.small_3_file: self._initial_small,
            TestFile.medium_file: self._initial_medium,
            TestFile.large_file: self._initial_large,
        }

    @property
    def new_diff_map(self) -> dict[str, str]:
        return {
            TestFile.small_file: self._diff_small,
            TestFile.small_1_file: self._diff_small,
            TestFile.small_2_file: self._diff_small,
            TestFile.small_3_file: self._diff_small,
            TestFile.medium_file: self._diff_medium,
            TestFile.large_file: self._diff_large,
        }

    def _generate_initial_text(self, file_name: str) -> str:
        str_to_kb_map: dict[str, int] = {
            TestFile.small_file: 10,
            TestFile.medium_file: 50,
            TestFile.large_file: 500,
            TestFile.huge_file: 2000,
        }
        target_bytes: int = str_to_kb_map[file_name] * 1024
        rng = random.Random(target_bytes)

        paragraphs: list[str] = []
        current_bytes: int = 0

        while current_bytes < target_bytes:
            word_count: int = rng.randint(20, 60)
            paragraphs.append(
                " ".join(rng.choices(self._words, k=word_count)) + ".\n\n"
            )
            current_bytes += len(paragraphs[-1])

        return "".join(paragraphs)

    def _generate_tricky_utf8_text(self) -> str:
        rng = random.Random(42)
        parts: list[str] = []
        parts.append(" ".join(self._words))
        parts.append(
            "".join(rng.choice("!@#$%^&*()[]{};:,.<>/?\\\"'") for _ in range(60))
        )
        parts.append("".join(chr(rng.randint(0x0600, 0x06FF)) for _ in range(30)))
        parts.append("".join(chr(rng.randint(0x4E00, 0x9FFF)) for _ in range(30)))
        # emoji sequences and variation selectors
        parts.append("🙂🚀🔥" * 10 + ProblemChars.VARSEL)
        # combining sequences
        parts.append(
            "e"
            + ProblemChars.COMBINING
            + "a"
            + ProblemChars.COMBINING
            + "o"
            + ProblemChars.COMBINING
        )
        parts.append(
            ProblemChars.BIDI_RLO
            + self._words[2]
            + ProblemChars.BIDI_PDF
            + ProblemChars.ZWS
            + self._words[3]
        )
        return "".join(parts)

    def _get_control_chars_bytes(self) -> bytes:
        return bytes(self.rng.randrange(1, 32) for _ in range(self.bin_file_size))

    def _get_high_entropy_bytes(self) -> bytes:
        return self.rng.randbytes(self.bin_file_size)

    def _get_invalid_utf8_bytes(self) -> bytes:
        return bytes(self.rng.randrange(128, 256) for _ in range(self.bin_file_size))

    def _get_null_bytes(self) -> bytes:
        null_data = bytearray(self.bin_file_size)
        null_data[self.rng.randrange(self.bin_file_size)] = self.rng.randrange(1, 256)
        return bytes(null_data)

    def _get_printable_ascii_bytes(self) -> bytes:
        printable = bytes(range(32, 127)) + b"\n\r\t"
        return bytes(self.rng.choice(printable) for _ in range(self.bin_file_size))

    def _get_utf16_interleaved_bytes(self) -> bytes:
        utf16_interleaved = bytearray(self.bin_file_size)
        for offset in range(0, self.bin_file_size, 2):
            utf16_interleaved[offset] = self.rng.randrange(65, 91)
        return bytes(utf16_interleaved)


@dataclass
class _FullPaths:
    l1_special_dir: Path = HOME_DIR / TestDir.special_dir
    l1_dir: Path = HOME_DIR / "_test_dir"
    l2_dir: Path = l1_dir / "_test_dir_level_1"
    l2_sibling_dir: Path = l1_dir / "_test_dir_level_1_sibling"
    l2_un_wanted_dir: Path = l1_dir / TestDir.un_wanted_dir
    l2_wanted_dir: Path = l1_dir / TestDir.wanted_dir
    l3_dir: Path = l2_dir / "_test_dir_level_2"
    l4_dir: Path = l3_dir / "_test_dir_level_3"
    l4_sibling_dir: Path = l3_dir / "_test_dir_level_3_sibling"

    l0_medium_file: Path = HOME_DIR / TestFile.medium_file
    l0_small_file: Path = HOME_DIR / TestFile.small_file
    l1_large_file: Path = l1_special_dir / TestFile.large_file
    l1_huge_file: Path = l1_special_dir / TestFile.huge_file
    l1_tricky_utf8_file: Path = l1_special_dir / TestFile.tricky_utf8_file

    @cached_property
    def all_dir_paths(self) -> set[Path]:
        return {getattr(self, attr) for attr in dir(self) if attr.endswith("_dir")}

    @property
    def _existing_dirs(self) -> set[Path]:
        return {path for path in self.all_dir_paths if path.exists()}

    @property
    def _missing_dirs(self) -> set[Path]:
        return {path for path in self.all_dir_paths if not path.exists()}

    @cached_property
    def all_file_paths(self) -> set[Path]:
        paths = [getattr(self, attr) for attr in dir(self) if attr.endswith("_file")]
        paths.extend(self.l1_special_dir / name for name in TestFile.bin_files())
        file_names = (
            (TestFile.diff_files() - {Path(TestFile.large_file)})
            | {Path(TestFile.wanted_file)}
            | TestFile.bin_files()
        )
        variable_paths = [
            directory / name
            for directory in self.all_dir_paths
            if directory != self.l1_special_dir
            for name in file_names
        ]
        return set(paths + variable_paths)

    @property
    def _existing_files(self) -> set[Path]:
        return {path for path in self.all_file_paths if path.exists()}

    @property
    def _missing_files(self) -> set[Path]:
        return {path for path in self.all_file_paths if not path.exists()}

    @property
    def existing_paths(self) -> set[Path]:
        return self._existing_dirs | self._existing_files

    @property
    def missing_paths(self) -> set[Path]:
        return self._missing_dirs | self._missing_files

    @property
    def files_for_diff(self) -> set[Path]:
        return {
            path
            for path in self._existing_files
            if Path(path.name) in TestFile.diff_files()
        }


class TestPaths:
    def __init__(self) -> None:
        self.file_contents = _TestFileContents()
        self.paths = _FullPaths()

    def report_test_paths(self) -> str:
        """Report existing test leaves and collapse missing directory trees to /**."""
        lines: list[str] = []
        existing = path_funcs.sort_paths(self.paths.existing_paths)
        parents = {parent for path in existing for parent in path.parents}
        existing = [path for path in existing if path not in parents]
        if existing:
            lines.append(f"[${ColorVar.text_success}]Existing:[/]")
            lines.extend(escape(str(path)) for path in existing)

        missing = self.paths.missing_paths
        if missing:
            directories = self.paths.all_dir_paths
            top_level = path_funcs.get_common_top_level(dir_paths=missing & directories)
            lines.append(f"[${ColorVar.text_warning}]All Other Possible Test Paths:[/]")
            lines.extend(
                escape(str(path / "**" if path in directories else path))
                for path in path_funcs.sort_paths(missing)
                if path in top_level
                or (path not in directories and top_level.isdisjoint(path.parents))
            )
        return "\n".join(lines)

    def remove_test_paths(self) -> str:
        existing = self.paths.existing_paths
        if not existing:
            return f"[${ColorVar.text_warning}]No test paths exist.[/]"

        top_level = path_funcs.get_common_top_level(
            dir_paths=existing & self.paths.all_dir_paths
        )
        for path in existing & self.paths.all_file_paths:
            path.unlink()
        for path in top_level:
            shutil.rmtree(path)

        removed = [escape(str(path)) for path in path_funcs.sort_paths(existing)]
        return "\n".join([f"[${ColorVar.text_success}]Removed paths:[/]", *removed])

    def create_diffs(self) -> str:
        """Choose directory shapes before preserving paths and filling the tree.

        Ordinary directories have a 5% empty bias, then eligible ones have a
        5% single-child bias. Preservation only considers compatible paths.
        Compatible directories have an 80% inclusion chance, plus required parents.
        Compatible existing files have a 90% survival chance, missing files a
        12% creation chance, and surviving diff-capable files a 70% toggle chance.
        One directory also toggles permissions between 0755 and 0750 each run.
        """
        directories = self.paths.all_dir_paths
        files = self.paths.all_file_paths
        existing = self.paths.existing_paths
        special_dir = self.paths.l1_special_dir
        special_paths = {special_dir} | {
            path for path in files if path.parent == special_dir
        }
        binary_paths = {
            path
            for path in files - special_paths
            if Path(path.name) in TestFile.bin_files()
        }
        # about 10% of binary paths eligible each run
        selected_binary_paths = set(
            random.sample(
                path_funcs.sort_paths(binary_paths), k=int(len(binary_paths) * 0.10)
            )
        )
        available_files = files - binary_paths | selected_binary_paths
        home_files = {self.paths.l0_small_file, self.paths.l0_medium_file}
        home_toggle = random.choice(sorted(home_files))
        ordered_dirs = sorted(
            directories - {special_dir}, key=lambda path: (len(path.parts), path)
        )
        allowed_dirs: set[Path] = {special_dir}
        empty_dirs: set[Path] = set()
        single_children: dict[Path, Path] = {}
        for directory in ordered_dirs:
            parent = directory.parent
            if parent != HOME_DIR and parent not in allowed_dirs:
                continue
            if parent in empty_dirs:
                continue
            if parent in single_children and single_children[parent] != directory:
                continue
            allowed_dirs.add(directory)
            if random.random() < 0.05:
                empty_dirs.add(directory)
                continue
            subdirs = path_funcs.sort_paths(
                path for path in directories if path.parent == directory
            )
            if subdirs and random.random() < 0.05:
                single_children[directory] = random.choice(subdirs)

        available_files = {
            path
            for path in available_files
            if path.parent == HOME_DIR
            or (
                path.parent in allowed_dirs
                and path.parent not in empty_dirs
                and path.parent not in single_children
            )
        }

        candidates = path_funcs.sort_paths(
            path
            for path in existing - special_paths - {home_toggle}
            if path in allowed_dirs or path in available_files
        )
        candidate_files = [path for path in candidates if path in files]
        selected_dirs = {
            path
            for path in ordered_dirs
            if path in allowed_dirs and random.random() < 0.80
        }
        preserved_files = {path for path in candidate_files if random.random() < 0.90}
        required_dirs = selected_dirs | {
            parent
            for path in selected_dirs | preserved_files
            for parent in path.parents
            if parent in directories
        }
        target: set[Path] = special_paths | preserved_files | required_dirs

        for directory in ordered_dirs:
            if directory not in allowed_dirs:
                continue
            if directory.parent != HOME_DIR and directory.parent not in target:
                continue
            if (
                directory not in required_dirs
                and single_children.get(directory.parent) != directory
            ):
                continue
            target.add(directory)
            if directory in empty_dirs:
                continue
            children = path_funcs.sort_paths(
                [
                    path
                    for path in available_files - existing
                    if path.parent == directory
                ]
            )
            target.update(path for path in children if random.random() < 0.12)

        target.update(home_files & existing)
        if not existing:
            target.update(home_files)
        if home_toggle in existing:
            target.discard(home_toggle)
        else:
            target.add(home_toggle)

        removed = existing - target
        top_level = path_funcs.get_common_top_level(dir_paths=removed & directories)
        for path in removed & files:
            path.unlink()
        for path in top_level:
            shutil.rmtree(path)

        created = target - existing
        for directory in sorted(
            target & directories, key=lambda path: (len(path.parts), path)
        ):
            directory.mkdir(parents=True, exist_ok=True)

        initial = self.file_contents.initial_map
        old_diff = self.file_contents.old_diff_map
        new_diff = self.file_contents.new_diff_map
        for path in path_funcs.sort_paths(created & files):
            contents = initial[path.name]
            if path.name in new_diff:
                contents = random.choice((contents, new_diff[path.name]))
            if isinstance(contents, bytes):
                path.write_bytes(contents)
            else:
                path.write_text(contents, encoding="utf-8")

        eligible = path_funcs.sort_paths(
            (self.paths.files_for_diff & existing) - {home_toggle}
        )
        modified = [path for path in eligible if random.random() < 0.70]
        for path in modified:
            contents = (
                new_diff[path.name]
                if path.read_text(encoding="utf-8") == old_diff[path.name]
                else old_diff[path.name]
            )
            path.write_text(contents, encoding="utf-8")

        surviving_dirs = target & directories & existing
        directory = random.choice(
            path_funcs.sort_paths(surviving_dirs or (target & directories))
        )
        mode = stat.S_IMODE(directory.stat().st_mode)
        directory.chmod(0o750 if mode == 0o755 else 0o755)

        lines: list[str] = []
        for label, paths in (
            ("Created paths", created),
            ("Removed paths", removed),
            ("Modified files", modified),
            ("Modified directories", [directory]),
        ):
            if paths:
                lines.append(f"[${ColorVar.text_warning}]{label}:[/]")
                lines.extend(escape(str(path)) for path in path_funcs.sort_paths(paths))
        return "\n".join(lines)
