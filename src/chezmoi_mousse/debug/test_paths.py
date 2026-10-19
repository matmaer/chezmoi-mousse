import os
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path

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
    _binary_file_data_map: dict[str, bytes] = field(default_factory=dict[str, bytes])

    _words: frozenset[str] = frozenset(
        [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
        ]
    )

    def __post_init__(self) -> None:

        self._initial_small = self._generate_initial_text(TestFile.small_file)
        self._initial_medium = self._generate_initial_text(TestFile.medium_file)
        self._initial_large = self._generate_initial_text(TestFile.large_file)
        self._initial_huge = self._generate_initial_text(TestFile.huge_file)
        self._tricky_utf8 = self._generate_tricky_utf8_text()
        self._binary_file_data_map = self._generate_binary_data_map()

        self._diff_small = self._initial_small.replace("lorem", "LOREM")
        self._diff_medium = self._initial_medium.replace("lorem", "LOREM")
        self._diff_large = self._initial_large.replace("lorem", "LOREM")

    @property
    def initial_map(self) -> dict[str, str | bytes]:
        file_name_map = {
            TestFile.small_file.value: self._initial_small,
            TestFile.medium_file.value: self._initial_medium,
            TestFile.large_file.value: self._initial_large,
            TestFile.huge_file.value: self._initial_huge,
            TestFile.tricky_utf8_file.value: self._tricky_utf8,
        }
        return file_name_map | self._binary_file_data_map

    @property
    def old_diff_map(self) -> dict[str, str]:
        return {
            TestFile.small_file.value: self._initial_small,
            TestFile.medium_file.value: self._initial_medium,
            TestFile.large_file.value: self._initial_large,
        }

    @property
    def new_diff_map(self) -> dict[str, str]:
        return {
            TestFile.small_file.value: self._diff_small,
            TestFile.medium_file.value: self._diff_medium,
            TestFile.large_file.value: self._diff_large,
        }

    def _generate_initial_text(self, file_name: str) -> str:
        str_to_kb_map: dict[str, int] = {
            TestFile.small_file.value: 10,
            TestFile.medium_file.value: 100,
            TestFile.large_file.value: 1000,
            TestFile.huge_file.value: 3000,
        }
        target_bytes: int = str_to_kb_map[file_name] * 1024
        random.seed(target_bytes)

        paragraphs: list[str] = []
        current_bytes: int = 0

        while current_bytes < target_bytes:
            word_count: int = random.randint(20, 60)
            paragraphs.append(
                " ".join(random.choices(list(self._words), k=word_count)) + ".\n\n"
            )
            current_bytes += len(paragraphs[-1])

        return "".join(paragraphs)

    def _generate_tricky_utf8_text(self) -> str:
        parts: list[str] = []
        parts.append(" ".join(list(self._words)))
        parts.append(
            "".join(random.choice("!@#$%^&*()[]{};:,.<>/?\\\"'") for _ in range(60))
        )
        parts.append("".join(chr(random.randint(0x0600, 0x06FF)) for _ in range(30)))
        parts.append("".join(chr(random.randint(0x4E00, 0x9FFF)) for _ in range(30)))
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
            + list(self._words)[2]
            + ProblemChars.BIDI_PDF
            + ProblemChars.ZWS
            + list(self._words)[3]
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
    file_contents: _TestFileContents
    _initial_diff_state: bool = True

    l1_man_dir: Path = HOME_DIR / TestDir.managed_dir
    l1_special_dir: Path = HOME_DIR / TestDir.special_dir
    l1_un_wanted_dir: Path = HOME_DIR / TestDir.un_wanted_dir
    l1_wanted_dir: Path = HOME_DIR / TestDir.wanted_dir

    l2_empty_dir: Path = HOME_DIR / TestDir.managed_dir / TestDir.empty_dir
    l2_man_dir: Path = HOME_DIR / TestDir.managed_dir / TestDir.managed_dir.nested_l1
    l2_wanted_dir: Path = HOME_DIR / TestDir.managed_dir / TestDir.wanted_dir.nested_l1
    l2_un_wanted_dir: Path = l1_man_dir / TestDir.un_wanted_dir
    l2_wanted_dir: Path = l1_man_dir / TestDir.wanted_dir
    l3e_man_dir: Path = l2_empty_dir / TestDir.managed_dir
    l3e_wanted_dir: Path = l2_empty_dir / TestDir.wanted_dir
    l3e_un_wanted_dir: Path = l2_empty_dir / TestDir.un_wanted_dir

    l0_medium_file: Path = HOME_DIR / TestFile.medium_file
    l0_small_file: Path = HOME_DIR / TestFile.small_file
    l1_huge_file: Path = l1_special_dir / TestFile.huge_file
    l1_tricky_utf8_file: Path = l1_special_dir / TestFile.tricky_utf8_file

    l1_medium_file: Path = l1_man_dir / TestFile.medium_file
    l1_un_wanted_file: Path = l1_man_dir / TestFile.un_wanted_file
    l1_medium_file: Path = l1_man_dir / TestFile.medium_file
    l1_small_file: Path = l1_man_dir / TestFile.small_file
    l1_large_file: Path = l1_man_dir / TestFile.large_file
    l2_medium_file: Path = l2_man_dir / TestFile.medium_file
    l2_medium_file: Path = l2_man_dir / TestFile.medium_file
    l2_wanted_file: Path = l2_man_dir / TestFile.wanted_file
    l3e_medium_file: Path = l3e_man_dir / TestFile.medium_file
    l3e_small_file: Path = l3e_man_dir / TestFile.small_file
    l3e_un_wanted_file: Path = l3e_man_dir / TestFile.un_wanted_file

    def __post_init__(self) -> None:
        self.file_contents = _TestFileContents()

    @property
    def dir_paths(self) -> list[Path]:
        return [getattr(self, attr) for attr in dir(self) if attr.endswith("_dir")]

    @property
    def file_paths(self) -> list[Path]:
        return [getattr(self, attr) for attr in dir(self) if attr.endswith("_file")]

    @property
    def files_for_diff(self) -> list[Path]:
        return [
            path
            for path in self.file_paths
            if path.name
            in (TestFile.small_file, TestFile.medium_file, TestFile.large_file)
        ]

    @property
    def all_paths(self) -> list[Path]:
        return self.dir_paths + self.file_paths

    def get_for_diff_contents(self, paths: list[Path]) -> dict[Path, str]:
        result: dict[Path, str] = {}
        self._initial_diff_state = not self._initial_diff_state
        for path in paths:
            if path not in self.files_for_diff:
                continue
            elif self._initial_diff_state:
                result[path] = self.file_contents.old_diff_map[path.name]
            else:
                result[path] = self.file_contents.new_diff_map[path.name]
        return result


class TestPaths:
    def __init__(self) -> None:
        self.full_paths = _FullPaths(file_contents=_TestFileContents())

    def _get_existing_home_test_files(self) -> list[Path]:
        return [
            p for p in HOME_DIR.iterdir() if p.name.startswith("_test_") and p.is_file()
        ]

    def _get_existing_home_test_dirs(self) -> list[Path]:
        return [
            p for p in HOME_DIR.iterdir() if p.name.startswith("_test_") and p.is_dir()
        ]

    def _reset_paths(self) -> None:
        for dir_path in self.full_paths.dir_paths:
            dir_path.mkdir(parents=True, exist_ok=True)
        for file_path in self.full_paths.file_paths:
            file_contents = self.full_paths.file_contents.initial_map[file_path.name]
            if isinstance(file_contents, bytes):
                file_path.write_bytes(file_contents)
            else:
                file_path.write_text(file_contents, encoding="utf-8")

    def _get_existing_test_paths(self) -> list[Path]:
        matches: list[Path] = []
        matches.extend(self._get_existing_home_test_files())
        dir_paths = self._get_existing_home_test_dirs()
        for dir_path in dir_paths:
            for root, dirs, files in os.walk(dir_path):
                if len(Path(root).parts) > 7:
                    continue
                matches.extend(
                    Path(root) / name
                    for name in [*dirs, *files]
                    if name.startswith("_test_")
                )
        return matches

    def create_paths_on_disk(self) -> str:
        # record existing expected paths before creating anything
        existing_before = set(self._get_existing_test_paths())
        self._reset_paths()
        existing_after = set(self._get_existing_test_paths())

        # compute which expected paths now exist but didn't before
        created = {str(p) for p in (existing_after - existing_before)}
        nothing_created_msg = "No test paths created because they already exist."
        if not created:
            return f"[${ColorVar.text_warning}]{nothing_created_msg}"

        return "\n".join(
            f"[${ColorVar.text_success} bold]Created paths:[/]", *sorted(created)
        )

    def remove_test_paths(self) -> str:
        existing_paths = self._get_existing_test_paths()
        if not existing_paths:
            return f"[${ColorVar.text_warning} bold]No test paths to remove[/]"

        removed_entries = [
            f"[${ColorVar.text_error}]{p}[/]" for p in sorted(existing_paths)
        ]

        # Remove the test directory tree
        for path in self._get_existing_home_test_dirs():
            shutil.rmtree(path, ignore_errors=True)
        for path in self._get_existing_home_test_files():
            path.unlink()

        return "\n".join(
            f"[${ColorVar.foreground_darken_2} bold]Removed paths:[/]", *removed_entries
        )

    def existing_test_paths(self) -> str:
        paths: list[str] = [str(line) for line in self._get_existing_test_paths()]
        if not paths:
            return f"[${ColorVar.text_warning} bold]No test paths exist.[/]"
        return "\n".join(paths)

    def create_diffs(self) -> str:
        if not self._get_existing_test_paths():
            return f"[${ColorVar.text_warning} bold]No test paths exist to modify.[/]"

        modified: list[str] = []

        def toggle_dir_permissions(dir_path: Path) -> None:
            current_permissions = dir_path.stat().st_mode
            if current_permissions == 0o750:
                dir_path.chmod(0o755)
            else:
                dir_path.chmod(0o750)
            modified.append(f"[${ColorVar.text_warning}]{dir_path}[/]")

        def toggle_file_diffs() -> None:
            new_contents = self.full_paths.get_for_diff_contents(
                self.full_paths.file_paths
            )
            for path, content in new_contents.items():
                if path.is_file() and self.full_paths.files_for_diff:
                    path.write_text(content)
                modified.append(f"[${ColorVar.text_warning}]{path}[/]")

        toggle_dir_permissions(self.full_paths.l1_man_dir)
        toggle_file_diffs()
        return "\n".join(modified)
