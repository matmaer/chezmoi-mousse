import random
from enum import StrEnum
from pathlib import Path

from faker import Faker
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup
from textual.widgets import Button, ContentSwitcher, Static
from tomlkit import document, dumps, table  # type: ignore[import-untyped]

from chezmoi_mousse import IDS, FlatBtn, Tcss

from .common.actionables import FlatButtonsVertical
from .common.loggers import DebugLog

__all__ = ["DebugTab"]

fake = Faker()


class ProblemChars(StrEnum):
    BIDI_PDF = "\u202c"
    BIDI_RLO = "\u202e"
    COMBINING = "\u0301"
    VARSEL = "\ufe0f"
    ZWJ = "\u200d"
    ZWS = "\u200b"


class Dirs(StrEnum):
    HOME = str(Path.home())
    TEST_DIR = str(Path.home() / "_test_path")
    SUB_DIR = str(Path.home() / "_test_path" / "_test_sub_dir")


class FileNames(StrEnum):
    TOML = "_test_file.toml"
    TRICKY_UTF8 = "_test_file_tricky_utf8.txt"
    LARGE = "_test_file_large.txt"
    BINARY = "_test_file_binary.bin"


class DebugBtnLabels(StrEnum):
    toggle_diffs = "Toggle Diffs"
    create_paths = "Create Test Paths"
    remove_paths = "Remove Test Paths"


class DebugTabSwitcher(ContentSwitcher):
    def __init__(self):
        super().__init__(
            id=IDS.debug.switcher.debug_tab,
            initial=IDS.debug.static.debug_test_paths,
        )

    def compose(self) -> ComposeResult:
        yield Static(id=IDS.debug.static.debug_test_paths)
        yield DebugLog(ids=IDS.debug)

    def on_mount(self) -> None:
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        self.test_paths_static.add_class(Tcss.border_title_top)
        self.test_paths_static.border_title = " Test Paths "
        self.debug_log = self.query_one(IDS.debug.logger.debug_q, DebugLog)
        self.debug_log.add_class(Tcss.border_title_top)
        self.debug_log.border_title = " Debug Log "


class DebugTab(Horizontal):
    def __init__(self):
        super().__init__()
        self.test_manager = TestPathManager()

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            ids=IDS.debug,
            buttons=(FlatBtn.debug_test_paths, FlatBtn.debug_log),
        )
        yield DebugTabSwitcher()
        yield HorizontalGroup(
            Button(
                classes=Tcss.operate_button, label=DebugBtnLabels.create_paths
            ),
            Button(
                classes=Tcss.operate_button, label=DebugBtnLabels.remove_paths
            ),
            Button(
                classes=Tcss.operate_button, label=DebugBtnLabels.toggle_diffs
            ),
            classes=Tcss.operate_button_group,
        )

    def on_mount(self) -> None:
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        self.test_paths_static.update(self.test_manager.existing_test_paths())

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            IDS.debug.switcher.debug_tab_q, DebugTabSwitcher
        )
        if event.button.id == IDS.debug.flat_btn.debug_log:
            switcher.current = IDS.debug.logger.debug
        elif event.button.id == IDS.debug.flat_btn.debug_test_paths:
            switcher.current = IDS.debug.static.debug_test_paths

    @on(Button.Pressed)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == DebugBtnLabels.toggle_diffs:
            result = self.test_manager.create_file_diffs()
            self.test_paths_static.update(result)
        elif event.button.label == DebugBtnLabels.create_paths:
            result = self.test_manager.create_test_paths()
            self.test_paths_static.update(result)
        elif event.button.label == DebugBtnLabels.remove_paths:
            result = self.test_manager.remove_test_paths()
            self.test_paths_static.update(result)


class TestPathManager:
    def __init__(self):
        self.test_file_binary = fake.binary(length=2048)
        self.test_file_large = fake.text(max_nb_chars=700000)
        self.test_file_toml = self.fake_toml_file()
        self.test_file_tricky_utf8 = self.tricky_utf8_file()
        # Store originals for toggling
        self.original_large = self.test_file_large
        self.original_toml = self.test_file_toml
        self.difs_applied = False

    def fake_toml_file(self):
        doc = document()
        doc["title"] = fake.sentence(nb_words=6)
        doc["version"] = fake.pyfloat(
            left_digits=1, right_digits=2, positive=True
        )
        doc["debug"] = fake.boolean()
        doc["hosts"] = [fake.hostname() for _ in range(10)]
        doc["ports"] = [fake.port_number() for _ in range(10)]
        some_table = table()
        some_table["id"] = fake.uuid4()
        some_table["date"] = fake.date_time().isoformat()
        some_table["text"] = fake.paragraph(nb_sentences=12)
        doc["some_table"] = some_table
        return dumps(doc)

    def tricky_utf8_file(self):
        parts: list[str] = []
        parts.append(fake.sentence(nb_words=6))
        parts.append(
            "".join(
                random.choice("!@#$%^&*()[]{};:,.<>/?\\\"'") for _ in range(60)
            )
        )
        parts.append(
            "".join(chr(random.randint(0x0600, 0x06FF)) for _ in range(30))
        )
        parts.append(
            "".join(chr(random.randint(0x4E00, 0x9FFF)) for _ in range(30))
        )
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
            + fake.word()
            + " .ext"
            + ProblemChars.BIDI_PDF
            + ProblemChars.ZWS
            + fake.word()
        )
        parts.append("A" + ProblemChars.ZWJ + "B" + ProblemChars.ZWJ + "C")
        return "\n".join(parts)

    def create_test_paths(self) -> str:
        created_paths: list[str] = []
        for dir in Dirs:
            dir_path = Path(dir.value)
            dir_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(dir.value)
        file_dirs = [Dirs.TEST_DIR, Dirs.HOME, Dirs.SUB_DIR]
        for dir in file_dirs:
            for file_name in FileNames:
                content = ""
                mode = "w"
                if file_name == FileNames.TOML:
                    content = self.test_file_toml
                elif file_name == FileNames.LARGE:
                    content = self.test_file_large
                elif file_name == FileNames.TRICKY_UTF8:
                    content = self.test_file_tricky_utf8
                elif file_name == FileNames.BINARY:
                    content = self.test_file_binary
                    mode = "wb"
                file_path = Path(dir.value) / file_name.value
                with open(file_path, mode) as f:
                    f.write(content)
                created_paths.append(str(file_path))
        result = "Created paths:\n" + "\n".join(p for p in created_paths)
        return result

    def remove_test_paths(self) -> str:
        file_dirs = [Dirs.TEST_DIR, Dirs.HOME, Dirs.SUB_DIR]
        removed_paths: list[str] = []
        for dir in file_dirs:
            for file_name in FileNames:
                file_path = Path(dir.value) / file_name.value
                if file_path.exists():
                    file_path.unlink()
                    removed_paths.append(str(file_path))
        if Path(Dirs.SUB_DIR).exists():
            Path(Dirs.SUB_DIR).rmdir()
            removed_paths.append(Dirs.SUB_DIR)
        if Path(Dirs.TEST_DIR).exists():
            Path(Dirs.TEST_DIR).rmdir()
            removed_paths.append(Dirs.TEST_DIR)
        return self.existing_test_paths()

    def create_file_diffs(self) -> str:
        existing_paths = self.existing_test_paths()
        if "No test paths exist." in existing_paths:
            return "No test paths exist to apply diffs."
        updated_paths: list[Path] = []
        if not self.difs_applied:
            updated_paths.append(Path("Apply diffs to test files:"))
            self.test_file_large = self.test_file_large.replace(
                "the", ""
            ).replace("o", "O")
            self.test_file_toml = self.test_file_toml.replace(
                "title", "new_title"
            ).replace("true", "false")
            self.difs_applied = True
        else:
            updated_paths.append(Path("Revert diffs from test files:"))
            # Revert to originals
            self.test_file_large = self.original_large
            self.test_file_toml = self.original_toml
            self.difs_applied = False

        # Update the files
        file_dirs = [Dirs.TEST_DIR, Dirs.HOME, Dirs.SUB_DIR]
        for dir in file_dirs:
            # Update LARGE file
            large_path = Path(dir.value) / FileNames.LARGE.value
            try:
                with open(large_path, "w") as f:
                    f.write(self.test_file_large)
                updated_paths.append(large_path)
            except FileNotFoundError:
                continue
            # Update TOML file
            toml_path = Path(dir.value) / FileNames.TOML.value
            try:
                with open(toml_path, "w") as f:
                    f.write(self.test_file_toml)
                updated_paths.append(toml_path)
            except FileNotFoundError:
                continue
        return "\n".join(str(p) for p in updated_paths)

    def existing_test_paths(self) -> str:
        existing_paths: list[str] = []
        file_dirs = [Dirs.TEST_DIR, Dirs.HOME, Dirs.SUB_DIR]
        for dir in file_dirs:
            for file_name in FileNames:
                file_path = Path(dir.value) / file_name.value
                if file_path.exists():
                    existing_paths.append(str(file_path))
        existing = "\n".join(p for p in existing_paths)
        if len(existing) == 0:
            existing = "No test paths exist."
        return existing
