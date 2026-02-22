import random
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from faker import Faker
from tomlkit import document, dumps, table  # type: ignore[import-untyped]

__all__ = ["TestPaths"]

FAKER = Faker()


class ProblemChars(StrEnum):
    BIDI_PDF = "\u202c"
    BIDI_RLO = "\u202e"
    COMBINING = "\u0301"
    VARSEL = "\ufe0f"
    ZWJ = "\u200d"
    ZWS = "\u200b"


@dataclass(frozen=True, slots=True)
class Files:
    BINARY = "_test_file_binary.bin"
    LARGE = "_test_file_large.txt"
    TOML_APPLY_A = "_test_file_apply_a.toml"
    TOML_APPLY_D = "_test_file_apply_d.toml"
    TOML_APPLY_M = "_test_file_apply_m.toml"
    TOML_APPLY_S = "_test_file_apply_space.toml"
    TOML_RE_ADD_A = "_test_file_re_add_a.toml"
    TOML_RE_ADD_D = "_test_file_re_add_d.toml"
    TOML_RE_ADD_M = "_test_file_re_add_m.toml"
    TOML_RE_ADD_S = "_test_file_re_add_space.toml"
    TRICKY_UTF8 = "_test_file_tricky_utf8.txt"
    UNCHANGED_1 = "_test_file_unchanged_1.toml"
    UNCHANGED_2 = "_test_file_unchanged_2.toml"
    UNCHANGED_3 = "_test_file_unchanged_3.toml"


@dataclass(frozen=True, slots=True, kw_only=True)
class DirNames:
    HOME = "_test_home"
    EMPTY = "_test_empty_dir"
    WITH_STATUS = "_test_dir_with_status"
    WITH_STATUS_CHILDREN = "_test_dir_with_status_children"
    SUB_DIR = "_test_sub_dir"
    TEST_DIR = "_test_dir"
    UNCHANGED = "_test_dir_unchanged"
    CHANGED = "_test_dir_changed"


@dataclass(slots=True, kw_only=True)
class TestPaths:
    files: Files = Files()
    dir_names: DirNames = DirNames()
    home_dir: Path = Path.home() / dir_names.HOME
    test_dir: Path = home_dir / dir_names.TEST_DIR
    status_children_dir: Path = (
        test_dir / dir_names.WITH_STATUS_CHILDREN / dir_names.SUB_DIR
    )
    binary_file_path: Path = test_dir / files.BINARY
    large_file_path: Path = test_dir / files.LARGE
    tricky_utf8_file_path: Path = test_dir / files.TRICKY_UTF8
    dir_paths: set[Path] = field(default_factory=lambda: set())
    file_paths: set[Path] = field(default_factory=lambda: set())

    @property
    def changed_file_names(self) -> list[str]:
        return [
            self.files.TOML_APPLY_A,
            self.files.TOML_APPLY_D,
            self.files.TOML_APPLY_M,
            self.files.TOML_APPLY_S,
            self.files.TOML_RE_ADD_A,
            self.files.TOML_RE_ADD_D,
            self.files.TOML_RE_ADD_M,
            self.files.TOML_RE_ADD_S,
        ]

    @property
    def unchanged_file_names(self) -> list[str]:
        return [self.files.UNCHANGED_1, self.files.UNCHANGED_2, self.files.UNCHANGED_3]

    @property
    def test_dir_paths(self) -> list[Path]:
        return [
            self.home_dir,
            self.home_dir / self.dir_names.UNCHANGED,
            self.test_dir,
            self.test_dir / self.dir_names.UNCHANGED,
            self.test_dir / self.dir_names.CHANGED,
            self.test_dir / self.dir_names.EMPTY,
            self.test_dir / self.dir_names.WITH_STATUS_CHILDREN,
            self.test_dir
            / self.dir_names.WITH_STATUS_CHILDREN
            / self.dir_names.SUB_DIR,
        ]

    @property
    def all_existing_paths(self) -> list[Path]:
        paths = sorted(self.dir_paths | self.file_paths)
        return [p for p in paths if p.exists()]

    def remove_all_paths_on_disk(self) -> None:
        for file in self.file_paths:
            if file.exists():
                file.unlink()
        for dir in self.dir_paths:
            if dir.exists():
                dir.rmdir()

    def populate_test_paths(self) -> None:
        for dir in self.test_dir_paths:
            self.dir_paths.add(dir)
        self.file_paths.add(self.binary_file_path)
        self.file_paths.add(self.large_file_path)
        self.file_paths.add(self.tricky_utf8_file_path)
        for file in self.unchanged_file_names:
            for dir in self.dir_paths:
                if (
                    dir.name in (self.dir_names.HOME, self.dir_names.UNCHANGED)
                    or dir == self.test_dir / self.dir_names.WITH_STATUS_CHILDREN
                ):
                    self.file_paths.add(dir / file)
        for file in self.changed_file_names:
            for dir in self.dir_paths:
                if dir == self.status_children_dir or dir == self.home_dir:
                    self.file_paths.add(dir / file)

    def create_paths_on_disk(self) -> list[str]:
        created_paths: list[str] = []
        for dir in self.dir_paths:
            dir.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(dir))
        created_paths.append(self._create_tricky_utf8_file())
        created_paths.append(self._create_large_file())
        created_paths.append(self._create_binary_file())
        for file in self.file_paths:
            if file.exists() or file.parent.name == self.dir_names.EMPTY:
                continue
            if file.name.endswith(".toml"):
                content = self._get_fake_toml_document()
                with open(file, "w", encoding="utf-8") as f:
                    f.write(content)
                created_paths.append(str(file))
        return created_paths

    def _get_fake_toml_document(self):
        doc = document()
        doc["title"] = FAKER.sentence(nb_words=6)
        doc["version"] = FAKER.pyfloat(left_digits=1, right_digits=2, positive=True)
        doc["debug"] = FAKER.boolean()
        doc["hosts"] = [FAKER.hostname() for _ in range(10)]
        doc["ports"] = [FAKER.port_number() for _ in range(10)]
        some_table = table()
        some_table["id"] = FAKER.uuid4()
        some_table["date"] = FAKER.date_time().isoformat()
        some_table["text"] = FAKER.paragraph(nb_sentences=12)
        doc["some_table"] = some_table
        return dumps(doc)

    def _create_binary_file(self) -> str:
        file = self.binary_file_path
        content = FAKER.binary(length=2048)
        with open(file, "wb") as f:
            f.write(content)
        return str(file)

    def _create_large_file(self) -> str:
        file = self.large_file_path
        content = FAKER.text(max_nb_chars=700000)
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
        return str(file)

    def _create_tricky_utf8_file(self) -> str:
        parts: list[str] = []
        parts.append(FAKER.sentence(nb_words=6))
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
            + FAKER.word()
            + " .ext"
            + ProblemChars.BIDI_PDF
            + ProblemChars.ZWS
            + FAKER.word()
        )
        parts.append("A" + ProblemChars.ZWJ + "B" + ProblemChars.ZWJ + "C")
        with open(self.tricky_utf8_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        return str(self.tricky_utf8_file_path)

    def list_existing_test_paths(self) -> str | None:
        existing_paths = [str(p) for p in self.all_existing_paths if p.exists()]
        if not existing_paths:
            return None
        return "[$text-success]Existing paths:[/]\n" + "\n".join(existing_paths)

    def remove_test_paths(self) -> str:
        removed_paths: list[str] = []
        # Remove files first
        for path in self.all_existing_paths:
            if path.exists() and path.is_file():
                path.unlink()
                removed_paths.append(str(path))
        # Then remove directories
        for dir in reversed(sorted(self.dir_paths)):
            dir_path = Path(dir)
            if dir_path.exists():
                dir_path.rmdir()
                removed_paths.append(str(dir_path))
        if not removed_paths:
            return "[$text-warning]No test paths to remove.[/]"
        return "[$text-success]All test paths removed.[/]"

    def create_file_diffs(self) -> str:
        if not self.list_existing_test_paths():
            return "[$text-warning]No test paths exist to modify.[/]"
        modified: list[str] = []

        # Modify LARGE file
        large_file_path = self.large_file_path
        if large_file_path.exists():
            with open(large_file_path, "w", encoding="utf-8") as f:
                modified_content = (
                    large_file_path.read_text(encoding="utf-8")
                    .replace("the", "")
                    .replace("o", "O")
                )
                f.write(modified_content)
            modified.append(str(large_file_path))

        # Modify TOML files
        for file in self.file_paths:
            if file.exists() and file.name not in self.unchanged_file_names:
                modified_content = (
                    file.read_text(encoding="utf-8")
                    .replace("title", "new_title")
                    .replace("true", "false")
                )
                with open(file, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                modified.append(str(file))
        return "[$text-primary]Modified paths:[/]\n" + "\n".join(modified)

    def __post_init__(self):
        self.populate_test_paths()
