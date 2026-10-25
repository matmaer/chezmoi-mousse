import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from rich.markup import escape

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import ColorVar, ProblemChars, TestDir, TestFile

__all__ = ["TestPaths"]

HOME_DIR = Path.home()


@dataclass
class _TestFileContents:
    _initial_small: str = ""
    _initial_medium: str = ""
    _initial_large: str = ""
    _initial_huge: str = ""

    _diff_small: str = ""
    _diff_medium: str = ""
    _diff_large: str = ""

    _tricky_utf8: str = ""
    binary_file_data_map: dict[str, bytes] = field(default_factory=dict[str, bytes])

    _words: list[str] = field(default_factory=list[str])

    def __post_init__(self) -> None:
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
        self.binary_file_data_map = self._generate_binary_data_map()

        self._diff_small = self._initial_small.replace("lorem", "LOREM")
        self._diff_medium = self._initial_medium.replace("lorem", "LOREM")
        self._diff_large = self._initial_large.replace("lorem", "LOREM")

    @property
    def initial_map(self) -> dict[str, str | bytes]:
        file_name_map = {
            TestFile.small_file: self._initial_small,
            TestFile.small_file_1: self._initial_small,
            TestFile.small_file_2: self._initial_small,
            TestFile.small_file_3: self._initial_small,
            TestFile.medium_file: self._initial_medium,
            TestFile.large_file: self._initial_large,
            TestFile.huge_file: self._initial_huge,
            TestFile.tricky_utf8_file: self._tricky_utf8,
            TestFile.wanted_file: self._initial_small,
        }
        return file_name_map | self.binary_file_data_map

    @property
    def old_diff_map(self) -> dict[str, str]:
        return {
            TestFile.small_file: self._initial_small,
            TestFile.small_file_1: self._initial_small,
            TestFile.small_file_2: self._initial_small,
            TestFile.small_file_3: self._initial_small,
            TestFile.medium_file: self._initial_medium,
            TestFile.large_file: self._initial_large,
        }

    @property
    def new_diff_map(self) -> dict[str, str]:
        return {
            TestFile.small_file: self._diff_small,
            TestFile.small_file_1: self._diff_small,
            TestFile.small_file_2: self._diff_small,
            TestFile.small_file_3: self._diff_small,
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

    def _generate_binary_data_map(self) -> dict[str, bytes]:
        size = 10000

        rng = random.Random(42)
        printable = bytes(range(32, 127)) + b"\n\r\t"

        null_data = bytearray(size)
        null_data[rng.randrange(size)] = rng.randrange(1, 256)

        utf16_interleaved = bytearray(size)
        for offset in range(0, size, 2):
            utf16_interleaved[offset] = rng.randrange(65, 91)

        bin_kinds = {
            "null_bytes": bytes(null_data),
            "high_entropy": rng.randbytes(size),
            "control_chars": bytes(rng.randrange(1, 32) for _ in range(size)),
            "invalid_utf8": bytes(rng.randrange(128, 256) for _ in range(size)),
            "printable_ascii": bytes(rng.choice(printable) for _ in range(size)),
            "utf16_interleaved": bytes(utf16_interleaved),
        }
        return {f"_test_file_{key}.bin": value for key, value in bin_kinds.items()}


@dataclass
class _FullPaths:
    binary_file_names: tuple[str, ...]

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

    def dir_paths(self, exists: bool | None = None) -> list[Path]:
        paths = [getattr(self, attr) for attr in dir(self) if attr.endswith("_dir")]
        sorted_paths = path_funcs.sort_paths(paths)
        if exists is True:
            return [path for path in sorted_paths if path.exists()]
        elif exists is False:
            return [path for path in sorted_paths if not path.exists()]
        return sorted_paths

    def file_paths(self, exists: bool | None = None) -> list[Path]:
        fixed_paths = [
            getattr(self, attr) for attr in dir(self) if attr.endswith("_file")
        ]
        fixed_paths.extend(
            self.l1_special_dir / name for name in self.binary_file_names
        )
        file_names = (
            TestFile.small_file,
            TestFile.small_file_1,
            TestFile.small_file_2,
            TestFile.small_file_3,
            TestFile.medium_file,
            TestFile.wanted_file,
            *self.binary_file_names,
        )
        variable_paths = [
            directory / name
            for directory in self.dir_paths()
            if directory != self.l1_special_dir
            for name in file_names
        ]
        sorted_paths = path_funcs.sort_paths(fixed_paths + variable_paths)
        if exists is True:
            return [path for path in sorted_paths if path.exists()]
        elif exists is False:
            return [path for path in sorted_paths if not path.exists()]
        return sorted_paths

    @property
    def files_for_diff(self) -> list[Path]:
        return [
            path
            for path in self.file_paths(exists=True)
            if path.name
            in (
                TestFile.small_file,
                TestFile.small_file_1,
                TestFile.small_file_2,
                TestFile.small_file_3,
                TestFile.medium_file,
                TestFile.large_file,
            )
        ]

    def all_paths(self, exists: bool | None = None) -> list[Path]:
        return self.dir_paths(exists) + self.file_paths(exists)


class TestPaths:
    def __init__(self) -> None:
        self.file_contents = _TestFileContents()
        self.full_paths = _FullPaths(
            binary_file_names=tuple(self.file_contents.binary_file_data_map)
        )

    def report_test_paths(self) -> str:
        """Report existing test leaves and collapse missing directory trees to /**."""
        lines: list[str] = []
        existing = self.full_paths.all_paths(exists=True)
        parents = {parent for path in existing for parent in path.parents}
        existing = [path for path in existing if path not in parents]
        if existing:
            lines.append(f"[${ColorVar.text_success}]Existing:[/]")
            lines.extend(escape(str(path)) for path in existing)

        missing = self.full_paths.all_paths(exists=False)
        if missing:
            top_level = path_funcs.get_common_top_level(missing)
            directories = set(self.full_paths.dir_paths())
            lines.append(f"[${ColorVar.text_warning}]Missing:[/]")
            lines.extend(
                escape(str(path / "**" if path in directories else path))
                for path in missing
                if path in top_level
            )
        return "\n".join(lines)

    def reset_paths(self) -> str:
        # TODO: phase out button
        return self.create_diffs()

    def remove_test_paths(self) -> str:
        existing = self.full_paths.all_paths(exists=True)
        if not existing:
            return f"[${ColorVar.text_warning}]No test paths exist.[/]"

        for path in path_funcs.get_common_top_level(existing):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

        removed = [escape(str(path)) for path in path_funcs.sort_paths(existing)]
        return "\n".join([f"[${ColorVar.text_success}]Removed paths:[/]", *removed])

    def create_diffs(self) -> str:
        """Bias ordinary directories 15% toward empty, then eligible ones 15%
        toward containing just one subdirectory.
        """
        directories = set(self.full_paths.dir_paths())
        files = set(self.full_paths.file_paths())
        existing = set(self.full_paths.all_paths(exists=True))
        special_dir = self.full_paths.l1_special_dir
        special_paths = {special_dir} | {
            path for path in files if path.parent == special_dir
        }
        binary_paths = {
            path
            for path in files - special_paths
            if path.name in self.full_paths.binary_file_names
        }
        # about 10% of binary paths eligible each run
        selected_binary_paths = set(
            random.sample(
                path_funcs.sort_paths(binary_paths), k=int(len(binary_paths) * 0.10)
            )
        )
        available_files = files - binary_paths | selected_binary_paths
        home_files = {self.full_paths.l0_small_file, self.full_paths.l0_medium_file}
        home_toggle = random.choice(sorted(home_files))
        # bias ordinary directories 15% toward empty, then eligible ones 15% toward
        # containing just one subdirectory.
        empty_dirs = {
            directory
            for directory in path_funcs.sort_paths(directories - {special_dir})
            if random.random() < 0.15
        }

        candidates = path_funcs.sort_paths(
            path
            for path in existing - special_paths - {home_toggle}
            if empty_dirs.isdisjoint(path.parents)
            and (path in directories or path in available_files)
        )
        if self.full_paths.l1_large_file in existing:
            candidates.append(self.full_paths.l1_large_file)
        # keep about half of the paths
        preserved_count = len(candidates) // 2
        preserved = set(random.sample(candidates, k=preserved_count))
        required_dirs = (preserved & directories) | {
            parent
            for path in preserved
            for parent in path.parents
            if parent in directories
        }
        target: set[Path] = special_paths | preserved | required_dirs

        ordered_dirs = sorted(
            directories - {special_dir}, key=lambda path: (len(path.parts), path)
        )
        for directory in ordered_dirs:
            if not empty_dirs.isdisjoint(directory.parents):
                continue
            if directory.parent != HOME_DIR and directory.parent not in target:
                continue
            if directory not in required_dirs and not random.choice((True, False)):
                continue
            target.add(directory)
            if directory in empty_dirs:
                continue
            children = path_funcs.sort_paths(
                [path for path in available_files if path.parent == directory]
            )
            target.update(random.sample(children, k=random.randint(0, len(children))))

        target.update(home_files & existing)
        if not existing:
            target.update(home_files)
        if home_toggle in existing:
            target.discard(home_toggle)
        else:
            target.add(home_toggle)

        for directory in ordered_dirs:
            if directory not in target or directory in empty_dirs:
                continue
            subdirs = path_funcs.sort_paths(
                path for path in directories if path.parent == directory
            )
            if not subdirs:
                continue
            if random.random() >= 0.15:
                continue
            child = random.choice(subdirs)
            target = {
                path
                for path in target
                if not path.is_relative_to(directory)
                or path == directory
                or path.is_relative_to(child)
            }
            target.add(child)

        removed = existing - target
        for path in path_funcs.get_common_top_level(removed):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

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
            (set(self.full_paths.files_for_diff) & existing) - preserved - {home_toggle}
        )
        modified = (
            random.sample(eligible, k=random.randint(1, len(eligible)))
            if eligible
            else []
        )
        for path in modified:
            contents = (
                new_diff[path.name]
                if path.read_text(encoding="utf-8") == old_diff[path.name]
                else old_diff[path.name]
            )
            path.write_text(contents, encoding="utf-8")

        lines: list[str] = []
        for label, paths in (
            ("Created paths", created),
            ("Removed paths", removed),
            ("Modified files", modified),
        ):
            if paths:
                lines.append(f"[${ColorVar.text_warning}]{label}:[/]")
                lines.extend(escape(str(path)) for path in path_funcs.sort_paths(paths))
        return "\n".join(lines)
