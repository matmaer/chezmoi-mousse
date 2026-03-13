import random
import shutil
from dataclasses import dataclass, fields
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
    TRICKY_UTF8 = "_test_file_tricky_utf8.txt"

    @property
    def all_toml_file_names(self) -> list[str]:
        return [self.TEST_FILE_1, self.TEST_FILE_2, self.TEST_FILE_3]

    @property
    def toml_file_without_diff(self) -> list[str]:
        return [self.TEST_FILE_2]

    @property
    def toml_files_for_diffs(self) -> list[str]:
        return [self.TEST_FILE_1, self.TEST_FILE_3]


@dataclass(frozen=True, slots=True, kw_only=True)
class AllTestPaths:
    home_dir: Path = Path.home()
    test_dir: Path = home_dir / "_test_dir"

    # dir names
    _empty_dir: Path = test_dir / "_test_empty_dir"
    dir_with_status: Path = test_dir / "_test_dir_with_status"
    nested_dirs_1: Path = test_dir / "_test_sub_dir_1" / "_test_nested_dir"
    _nested_dir_without_status_files_in: Path = test_dir / "_test_sub_dir_2"
    _nested_dir_with_status_files_in: Path = (
        _nested_dir_without_status_files_in / "_test_nested_dir"
    )

    # file names
    file_names = PileNames()

    @property
    def all_dirs_to_create(self) -> list[Path]:
        # to create the dirs with parents True
        return sorted(
            {
                self.dir_with_status,
                self._empty_dir,
                self.nested_dirs_1,
                self._nested_dir_with_status_files_in,
            }
        )

    @property
    def _dirs_with_toml_files(self) -> list[Path]:
        return sorted(
            {self.home_dir}
            | {
                getattr(self, field.name)
                for field in fields(self)
                if field.name != "_empty_dir"
            }
        )

    @property
    def toml_files_to_create(self) -> list[Path]:
        to_create: set[Path] = set()
        for file_name in self.file_names.all_toml_file_names:
            for dir in self._dirs_with_toml_files:
                if dir != self._nested_dir_without_status_files_in:
                    to_create.add(dir / file_name)
        for file_name in self.file_names.toml_file_without_diff:
            to_create.add(self._nested_dir_without_status_files_in / file_name)
        return sorted(to_create)

    @property
    def toml_files_to_delete(self) -> list[Path]:
        to_delete: set[Path] = set()
        for file_name in self.toml_files_to_create:
            if file_name.name == self.file_names.TEST_FILE_3:
                to_delete.add(self._nested_dir_without_status_files_in / file_name)
        return sorted(to_delete)

    @property
    def toml_files_for_diff(self) -> list[Path]:
        to_diff: set[Path] = set()
        for file_name in self.file_names.toml_files_for_diffs:
            for dir in self._dirs_with_toml_files:
                if dir in [self._nested_dir_without_status_files_in, self._empty_dir]:
                    continue
                to_diff.add(dir / file_name)
        return sorted(to_diff)

    @property
    def large_file_path(self) -> Path:
        return self.test_dir / self.file_names.LARGE

    @property
    def binary_file_path(self) -> Path:
        return self.test_dir / self.file_names.BINARY

    @property
    def tricky_utf8_file_path(self) -> Path:
        return self.test_dir / self.file_names.TRICKY_UTF8

    @property
    def all_test_paths(self) -> list[Path]:
        return sorted(
            set(self.all_dirs_to_create)
            | set(self.toml_files_to_create)
            | {self.large_file_path, self.binary_file_path, self.tricky_utf8_file_path}
        )


@dataclass(slots=True, kw_only=True)
class TestPaths:
    all_paths: AllTestPaths = AllTestPaths()

    def _create_dir_paths(self) -> list[str]:
        created_dirs: set[str] = set()
        for dir in self.all_paths.all_dirs_to_create:
            if not dir.exists():
                dir.mkdir(parents=True)
                created_dirs.add(str(dir))
        return sorted(created_dirs)

    def _create_binary_file(self) -> list[str]:
        file_path = self.all_paths.binary_file_path
        if file_path.exists():
            return []
        content = FAKER.binary(length=2048)
        with Path.open(file_path, "wb") as f:
            f.write(content)
        return [str(file_path)]

    def _create_large_file(self) -> list[str]:
        file_path = self.all_paths.large_file_path
        if file_path.exists():
            return []
        content = FAKER.text(max_nb_chars=700000)
        with Path.open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return [str(file_path)]

    def _create_tricky_utf8_file(self) -> list[str]:
        file_path = self.all_paths.tricky_utf8_file_path
        if file_path.exists():
            return []
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
        with Path.open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        return [str(file_path)]

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

        created_files: set[str] = set()
        for file in self.all_paths.toml_files_to_create:
            if file.exists():
                continue
            # to avoid creating the file when we deleted nested_dirs_1
            elif file.parent.exists():
                with Path.open(file, "w", encoding="utf-8") as f:
                    f.write(get_fake_toml_string())
                created_files.add(str(file))
        return sorted(created_files)

    def create_paths_on_disk(self) -> list[str]:
        created_paths: set[str] = set()
        created_paths.update(self._create_dir_paths())
        created_paths.update(self._create_binary_file())
        created_paths.update(self._create_large_file())
        created_paths.update(self._create_tricky_utf8_file())
        created_paths.update(self._create_toml_files())
        if not created_paths:
            return [
                (
                    "[$text-warning]No test paths were created because they already "
                    "exist.[/]"
                )
            ] + [f"[dim]{p}[/]" for p in self.list_existing_test_paths()]
        return ["[$text-primary bold]Created paths:[/]\n"] + sorted(created_paths)

    def list_existing_test_paths(self) -> list[Path]:
        existing_paths = [p for p in self.all_paths.all_test_paths if p.exists()]
        return sorted(existing_paths)

    def remove_test_paths(self) -> str:
        existing_paths = self.list_existing_test_paths()
        removed_paths: set[str] = set()
        if not existing_paths:
            return "[$text-warning bold]No test paths to remove.[/]\n"
        paths_in_test_dir = self.all_paths.test_dir.rglob("*")
        removed_paths.update([f"[$text-error]{p}[/]" for p in paths_in_test_dir])
        shutil.rmtree(self.all_paths.test_dir)
        for file_path in [
            p
            for p in self.all_paths.home_dir.iterdir()
            if p.name.startswith("_test_file_") and p.name.endswith(".toml")
        ]:
            file_path.unlink()
            removed_paths.add(f"[$text-error]{file_path}[/]")

        return "[$text-primary bold]Removed paths:[/]\n" + "\n".join(
            sorted(removed_paths)
        )

    def create_diffs(self) -> str:
        if not self.list_existing_test_paths():
            return "[$text-warning bold]No test paths exist to modify.[/]"
        modified: set[str] = set()

        # Modify LARGE file
        large_file_path = self.all_paths.large_file_path
        if large_file_path.exists():
            with Path.open(large_file_path, "w", encoding="utf-8") as f:
                modified_content = (
                    large_file_path.read_text(encoding="utf-8")
                    .replace("the", "")
                    .replace("o", "O")
                )
                f.write(modified_content)
            modified.add(f"[$text-warning]{large_file_path}[/]")

        # Modify TOML files
        for file in self.all_paths.toml_files_for_diff:
            if file.exists():
                if file in self.all_paths.toml_files_to_delete:
                    file.unlink()
                    modified.add(f"[$text-error]{file}[/]")
                    continue
                modified_content = (
                    file.read_text(encoding="utf-8")
                    .replace("title", "new_title")
                    .replace("true", "false")
                )
                with Path.open(file, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                modified.add(f"[$text-warning]{file}[/]")

        # Toggle between 0o750 and 0o755 for the dir with status
        dir_with_status = self.all_paths.dir_with_status
        if dir_with_status.exists():
            current_permissions = dir_with_status.stat().st_mode
            if current_permissions == 0o750:
                dir_with_status.chmod(0o755)
            else:
                dir_with_status.chmod(0o750)
            modified.add(f"[$text-warning]{dir_with_status}[/]")

        # Delete or create the self.nested_dirs_1
        nested_dirs_1 = self.all_paths.nested_dirs_1
        if nested_dirs_1.exists():
            shutil.rmtree(nested_dirs_1)
            modified.add(f"[$text-error]{nested_dirs_1}[/]")
        else:
            nested_dirs_1.mkdir(parents=True)
            modified.add(f"[$text-success]{nested_dirs_1}[/]")

        return "[$text-primary bold]Modified paths:[/]\n" + "\n".join(sorted(modified))
