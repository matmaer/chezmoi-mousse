import random
import shutil
import stat
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
            TestFile.small_file.value: self._initial_small,
            TestFile.medium_file.value: self._initial_medium,
            TestFile.large_file.value: self._initial_large,
            TestFile.huge_file.value: self._initial_huge,
            TestFile.tricky_utf8_file.value: self._tricky_utf8,
            TestFile.wanted_file.value: self._initial_small,
            TestFile.un_wanted_file.value: self._initial_small,
        }
        return file_name_map | self.binary_file_data_map

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
            TestFile.medium_file.value: 50,
            TestFile.large_file.value: 500,
            TestFile.huge_file.value: 2000,
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
    file_contents: _TestFileContents = field(default_factory=_TestFileContents)

    l1_man_dir: Path = HOME_DIR / TestDir.managed_dir
    l1_special_dir: Path = HOME_DIR / TestDir.special_dir
    l1_un_wanted_dir: Path = HOME_DIR / TestDir.un_wanted_dir
    l1_wanted_dir: Path = HOME_DIR / TestDir.wanted_dir

    l2_empty_dir: Path = HOME_DIR / TestDir.managed_dir / TestDir.empty_dir
    l2_man_dir: Path = HOME_DIR / TestDir.managed_dir / TestDir.managed_dir.nested_l1
    l2_un_wanted_dir: Path = l1_man_dir / TestDir.un_wanted_dir
    l2_wanted_dir: Path = l1_man_dir / TestDir.wanted_dir
    l3e_man_dir: Path = l2_man_dir / TestDir.managed_dir
    l3e_wanted_dir: Path = l2_man_dir / TestDir.wanted_dir

    l0_medium_file: Path = HOME_DIR / TestFile.medium_file
    l0_small_file: Path = HOME_DIR / TestFile.small_file
    l1_large_file: Path = l1_special_dir / TestFile.large_file
    l1_huge_file: Path = l1_special_dir / TestFile.huge_file
    l1_tricky_utf8_file: Path = l1_special_dir / TestFile.tricky_utf8_file

    l1_un_wanted_file: Path = l1_man_dir / TestFile.un_wanted_file
    l1_small_file: Path = l1_man_dir / TestFile.small_file
    l1_medium_file: Path = l1_man_dir / TestFile.medium_file
    l2_small_file: Path = l2_man_dir / TestFile.small_file
    l2_medium_file: Path = l2_man_dir / TestFile.medium_file
    l2_wanted_file: Path = l2_man_dir / TestFile.wanted_file
    l3e_small_file: Path = l3e_man_dir / TestFile.small_file
    l3e_medium_file: Path = l3e_man_dir / TestFile.medium_file
    l3e_un_wanted_file: Path = l3e_man_dir / TestFile.un_wanted_file

    def dir_paths(self, exists: bool | None = None) -> list[Path]:
        paths = [getattr(self, attr) for attr in dir(self) if attr.endswith("_dir")]
        sorted_paths = path_funcs.sort_paths(paths)
        if exists is True:
            return [path for path in sorted_paths if path.exists()]
        elif exists is False:
            return [path for path in sorted_paths if not path.exists()]
        return sorted_paths

    def file_paths(self, exists: bool | None = None) -> list[Path]:
        text_paths = [
            getattr(self, attr) for attr in dir(self) if attr.endswith("_file")
        ]
        binary_paths = [
            self.l1_special_dir / f_name
            for f_name in self.file_contents.binary_file_data_map
        ]
        sorted_paths = path_funcs.sort_paths(text_paths + binary_paths)
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
            in (TestFile.small_file, TestFile.medium_file, TestFile.large_file)
        ]

    def all_paths(self, exists: bool | None = None) -> list[Path]:
        return self.dir_paths(exists) + self.file_paths(exists)


class TestPaths:
    def __init__(self) -> None:
        self.full_paths = _FullPaths()

    def report_test_paths(self) -> str:
        lines: list[str] = []
        existing = self.full_paths.all_paths(exists=True)
        if existing:
            lines.append(f"[${ColorVar.text_success}]Existing:[/]")
            lines.extend(escape(str(path)) for path in existing)

        missing = self.full_paths.all_paths(exists=False)
        if missing:
            lines.append(f"[${ColorVar.text_warning}]Missing:[/]")
            lines.extend(escape(str(path)) for path in missing)
        return "\n".join(line for line in lines)

    def reset_paths(self) -> str:
        existing_before = set(self.full_paths.all_paths(exists=True))
        for dir_path in self.full_paths.dir_paths():
            dir_path.mkdir(parents=True, exist_ok=True)
            dir_path.chmod(0o755)
        for file_path in self.full_paths.file_paths():
            file_contents = self.full_paths.file_contents.initial_map[file_path.name]
            if isinstance(file_contents, bytes):
                file_path.write_bytes(file_contents)
            else:
                file_path.write_text(file_contents, encoding="utf-8")

        existing_after = set(self.full_paths.all_paths(exists=True))
        created = path_funcs.sort_paths(existing_after - existing_before)
        updated = path_funcs.sort_paths(existing_before & existing_after)
        lines: list[str] = []
        if created:
            lines.append(f"[${ColorVar.text_success}]Created missing paths:[/]")
            lines.extend(escape(str(path)) for path in created)
        if updated:
            lines.append(f"[${ColorVar.text_warning}]Updated existing paths:[/]")
            lines.extend(escape(str(path)) for path in updated)
        return "\n".join(lines)

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
        lines: list[str] = []
        dir_path = self.full_paths.l2_man_dir
        dir_exists = dir_path.is_dir()
        files = self.full_paths.files_for_diff
        if not dir_exists and not files:
            return f"[${ColorVar.text_warning}]No test paths exist to modify.[/]"

        initial = self.full_paths.file_contents.old_diff_map
        modified = self.full_paths.file_contents.new_diff_map
        restore_initial = any(
            path.read_text(encoding="utf-8") != initial[path.name] for path in files
        ) or (dir_exists and stat.S_IMODE(dir_path.stat().st_mode) != 0o755)

        if dir_exists:
            lines.append(f"[${ColorVar.text_warning}]Modified status dir:[/]")
            dir_path.chmod(0o755 if restore_initial else 0o750)
            lines.append(f"{escape(str(dir_path))}")
        else:
            lines.append(
                f"[${ColorVar.text_warning}]Dir to modify does not exist: {dir_path}[/]"
            )

        contents = initial if restore_initial else modified
        if files:
            lines.append(f"[${ColorVar.text_warning}]Modified files:[/]")
        for path in files:
            path.write_text(contents[path.name], encoding="utf-8")
            lines.append(f"{escape(str(path))}")
        return "\n".join(lines)
