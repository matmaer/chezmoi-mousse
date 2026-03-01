import random
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import tomlkit
from faker import Faker

__all__ = ["TestPaths"]

FAKER = Faker()


class ProblemChars(StrEnum):
    BIDI_PDF = "\u202c"
    BIDI_RLO = "\u202e"
    COMBINING = "\u0301"
    VARSEL = "\ufe0f"
    ZWJ = "\u200d"
    ZWS = "\u200b"


@dataclass(frozen=True, slots=True, kw_only=True)
class PileNames:
    BINARY = "_test_file_binary.bin"
    LARGE = "_test_file_large.txt"
    TEST_FILE_1 = "_test_file_1.toml"
    TEST_FILE_2 = "_test_file_2.toml"
    TEST_FILE_3 = "_test_file_3.toml"
    TEST_FILE_4 = "_test_file_4.toml"
    TRICKY_UTF8 = "_test_file_tricky_utf8.txt"

    @property
    def all_toml_file_names(self) -> list[str]:
        return [self.TEST_FILE_1, self.TEST_FILE_2, self.TEST_FILE_3, self.TEST_FILE_4]

    @property
    def toml_files_for_diffs(self) -> list[str]:
        return [self.TEST_FILE_1, self.TEST_FILE_3]


@dataclass(frozen=True, slots=True, kw_only=True)
class AllTestPaths:
    DEST_DIR: Path
    # dir names
    DIR_WITH_STATUS = "_test_dir_with_status"
    EMPTY = "_test_empty_dir"
    SUB_DIR = "_test_sub_dir"
    WITH_NESTED_STATUS_CHILDREN = "_test_with_status_children"
    WITH_SPECIAL_FILES = "_test_special_files"
    WITHOUT_STATUS_CHILDREN = "_test_with_status_children"

    # file names
    file_names = PileNames()

    @property
    def _dir_with_special_files(self) -> Path:
        return self.DEST_DIR / self.WITH_SPECIAL_FILES

    @property
    def _dir_with_nested_dir_with_status_children(self) -> Path:
        return self.DEST_DIR / self.WITH_NESTED_STATUS_CHILDREN

    @property
    def _dir_with_status(self) -> Path:
        return self.DEST_DIR / self.DIR_WITH_STATUS

    @property
    def _dir_without_status_children(self) -> Path:
        return self._dir_with_nested_dir_with_status_children / self.SUB_DIR

    @property
    def _empty_dir_path(self) -> Path:
        return self.DEST_DIR / self.EMPTY

    @property
    def _nested_dir_with_status_paths(self) -> Path:
        return self.DEST_DIR / self.WITH_NESTED_STATUS_CHILDREN / self.SUB_DIR

    @property
    def _sub_dir_path(self) -> Path:
        return self.DEST_DIR / self.SUB_DIR

    @property
    def all_dirs_to_create(self) -> list[Path]:
        # to create the dirs with parents True
        return [
            self._dir_with_special_files,
            self._dir_with_status,
            self._dir_without_status_children,
            self._empty_dir_path,
            self._nested_dir_with_status_paths,
            self._sub_dir_path,
        ]

    @property
    def _dirs_with_toml_files(self) -> list[Path]:
        return [
            self._dir_with_status,
            self._dir_without_status_children,
            self._nested_dir_with_status_paths,
            self._sub_dir_path,
            self.DEST_DIR,
        ]

    @property
    def toml_files_to_create(self) -> list[Path]:
        to_create: list[Path] = []
        for file_name in self.file_names.all_toml_file_names:
            for dir in self._dirs_with_toml_files:
                to_create.append(dir / file_name)
        return to_create

    @property
    def toml_files_for_diff(self) -> list[Path]:
        to_diff: list[Path] = []
        dirs_to_exclude = [
            self._dir_with_nested_dir_with_status_children,
            self._dir_with_special_files,
            self._dir_without_status_children,
            self._empty_dir_path,
            self._nested_dir_with_status_paths,
        ]
        for file_name in self.file_names.toml_files_for_diffs:
            for dir in self._dirs_with_toml_files:
                if dir in dirs_to_exclude:
                    continue
                to_diff.append(dir / file_name)
        return to_diff

    @property
    def large_file_path(self) -> Path:
        return self.DEST_DIR / self.WITH_SPECIAL_FILES / self.file_names.LARGE

    @property
    def binary_file_path(self) -> Path:
        return self.DEST_DIR / self.WITH_SPECIAL_FILES / self.file_names.BINARY

    @property
    def tricky_utf8_file_path(self) -> Path:
        return self.DEST_DIR / self.WITH_SPECIAL_FILES / self.file_names.TRICKY_UTF8

    @property
    def all_test_paths(self) -> list[Path]:
        return sorted(
            self.all_dirs_to_create
            + self.toml_files_to_create
            + [self.large_file_path, self.binary_file_path, self.tricky_utf8_file_path]
        )


@dataclass(slots=True, kw_only=True)
class TestPaths:
    all_paths: AllTestPaths = AllTestPaths(DEST_DIR=Path.home())

    def _create_dir_paths(self) -> list[str]:
        created_dirs: list[str] = []
        for dir in self.all_paths.all_dirs_to_create:
            if not dir.exists():
                dir.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(dir))
        return created_dirs

    def _create_binary_file(self) -> str:
        file = self.all_paths.binary_file_path
        content = FAKER.binary(length=2048)
        with open(file, "wb") as f:
            f.write(content)
        return str(file)

    def _create_large_file(self) -> str:
        content = FAKER.text(max_nb_chars=700000)
        with open(self.all_paths.large_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(self.all_paths.large_file_path)

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
        with open(self.all_paths.tricky_utf8_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        return str(self.all_paths.tricky_utf8_file_path)

    def _create_toml_files(self) -> list[str]:
        def get_fake_toml_string() -> str:
            doc = tomlkit.document()
            doc["title"] = FAKER.sentence(nb_words=6)
            doc["version"] = FAKER.pyfloat(left_digits=1, right_digits=2, positive=True)
            doc["debug"] = FAKER.boolean()
            doc["hosts"] = [FAKER.hostname() for _ in range(10)]
            doc["ports"] = [FAKER.port_number() for _ in range(10)]
            some_table = tomlkit.table()
            some_table["id"] = FAKER.uuid4()
            some_table["date"] = FAKER.date_time().isoformat()
            some_table["text"] = FAKER.paragraph(nb_sentences=12)
            doc["some_table"] = some_table
            return doc.as_string()

        created_files: list[str] = []
        for file in self.all_paths.toml_files_to_create:
            if file.exists():
                file.unlink()
            with open(file, "w", encoding="utf-8") as f:
                f.write(get_fake_toml_string())
            created_files.append(str(file))
        return created_files

    def create_paths_on_disk(self) -> list[str]:
        created_paths = self._create_dir_paths()
        created_paths.append(self._create_binary_file())
        created_paths.append(self._create_large_file())
        created_paths.append(self._create_tricky_utf8_file())
        created_paths.extend(self._create_toml_files())
        return created_paths

    def list_existing_test_paths(self) -> str | list[Path]:
        existing_paths = [p for p in self.all_paths.all_test_paths if p.exists()]
        if not existing_paths:
            return "[$text-warning]No test paths exist on disk.[/]"
        return existing_paths

    def remove_test_paths(self) -> str:
        removed_paths: list[str] = []
        # Remove files first
        existing_paths = self.list_existing_test_paths()
        if isinstance(existing_paths, str):
            return existing_paths
        for path in existing_paths:
            if path.is_file():
                path.unlink()
                removed_paths.append(str(path))
        # Then remove directories
        for dir_path in sorted(self.all_paths.all_dirs_to_create, reverse=True):
            if dir_path.exists():
                dir_path.rmdir()
                removed_paths.append(str(dir_path))
        if not removed_paths:
            return "[$text-warning]No test paths to remove.[/]"
        removed_paths.sort()
        removed_path_strings = "\n".join([str(p) for p in removed_paths])
        return "[$text-success]Removed paths:[/]\n" + removed_path_strings

    def create_file_diffs(self) -> str:
        if not self.list_existing_test_paths():
            return "[$text-warning]No test paths exist to modify.[/]"
        modified: list[str] = []

        # Modify LARGE file
        large_file_path = self.all_paths.large_file_path
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
        for file in self.all_paths.toml_files_for_diff:
            if file.exists():
                modified_content = (
                    file.read_text(encoding="utf-8")
                    .replace("title", "new_title")
                    .replace("true", "false")
                )
                with open(file, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                modified.append(str(file))

        modified.append(self._create_binary_file())
        modified.append(self._create_large_file())
        modified.append(self._create_tricky_utf8_file())

        return "[$text-primary]Modified paths:[/]\n" + "\n".join(modified)
