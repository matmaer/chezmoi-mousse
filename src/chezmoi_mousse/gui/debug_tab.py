import random
from enum import StrEnum
from pathlib import Path

from faker import Faker
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Button, ContentSwitcher, RichLog, Static
from tomlkit import document, dumps, table  # type: ignore[import-untyped]

from chezmoi_mousse import IDS, AppType, FlatBtn, Tcss

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
    # HOME = str(Path.home())
    TEST_DIR = str(Path.home() / "_test_dir")
    SUB_DIR = str(Path.home() / "_test_dir" / "_test_sub_dir")
    DIR_STATUS_TEST = str(Path.home() / "_test_dir" / "_test_dir_status")


class Files(StrEnum):
    TOML = "_test_file.toml"
    TRICKY_UTF8 = "_test_file_tricky_utf8.txt"
    LARGE = "_test_file_large.txt"
    BINARY = "_test_file_binary.bin"

    @classmethod
    def files_in_home(cls) -> list[Path]:
        return [Path.home() / cls.TOML, Path.home() / cls.LARGE]


class DebugBtnLabels(StrEnum):
    toggle_diffs = "Toggle Diffs"
    reset_paths = "(Re)Create Test Paths"
    remove_paths = "Remove Test Paths"


class DebugTab(Horizontal, AppType):
    def __init__(self):
        super().__init__()
        self.test_manager = TestPathManager()

    def compose(self) -> ComposeResult:

        yield FlatButtonsVertical(
            ids=IDS.debug,
            buttons=(
                FlatBtn.debug_test_paths,
                FlatBtn.debug_log,
                FlatBtn.debug_dom_nodes,
            ),
        )
        with ContentSwitcher(
            id=IDS.debug.switcher.debug_tab, initial=IDS.debug.view.test_paths
        ):
            yield Vertical(
                Static(id=IDS.debug.static.debug_test_paths),
                HorizontalGroup(
                    Button(
                        classes=Tcss.operate_button,
                        label=DebugBtnLabels.reset_paths,
                    ),
                    Button(
                        classes=Tcss.operate_button,
                        label=DebugBtnLabels.remove_paths,
                    ),
                    Button(
                        classes=Tcss.operate_button,
                        label=DebugBtnLabels.toggle_diffs,
                    ),
                    classes=Tcss.operate_button_group,
                ),
                id=IDS.debug.view.test_paths,
                classes=Tcss.border_title_top,
            )
            yield DebugLog(ids=IDS.debug)
            yield RichLog(
                id=IDS.debug.logger.dom_nodes,
                auto_scroll=False,
                highlight=True,
                classes=Tcss.border_title_top,
            )

    def on_mount(self) -> None:
        self.test_paths_static = self.query_one(
            IDS.debug.static.debug_test_paths_q, Static
        )
        self.test_paths_static.update(
            self.test_manager.list_existing_test_paths()
        )
        self.debug_test_path_view = self.query_one(
            IDS.debug.view.test_paths_q, Vertical
        )
        self.debug_test_path_view.border_title = " Test Paths "
        self.debug_log = self.query_one(IDS.debug.logger.debug_q, DebugLog)
        self.debug_log.add_class(Tcss.border_title_top)
        self.debug_log.border_title = " Debug Log "
        self.dom_node_logger = self.query_one(
            IDS.debug.logger.dom_nodes_q, RichLog
        )
        self.dom_node_logger.border_title = " DOM Nodes "
        self.switcher = self.query_one(
            IDS.debug.switcher.debug_tab_q, ContentSwitcher
        )

        self.app.call_later(self.log_dom_nodes)

    def log_dom_nodes(self) -> None:
        dom_items = [
            item
            for item in self.app.walk_children(with_self=True, method="depth")
        ]
        self.dom_node_logger.write(f"DOMNode count: {len(dom_items)}\n")
        nodes_with_id = [item for item in dom_items if item.id is not None]
        nodes_without_id = [item for item in dom_items if item.id is None]
        for item in sorted(nodes_with_id, key=str):
            self.dom_node_logger.write(f"{item}")
        for item in sorted(nodes_without_id, key=str):
            self.dom_node_logger.write(f"{item}")

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == IDS.debug.flat_btn.debug_log:
            self.switcher.current = IDS.debug.logger.debug
        elif event.button.id == IDS.debug.flat_btn.debug_test_paths:
            self.switcher.current = IDS.debug.view.test_paths
        elif event.button.id == IDS.debug.flat_btn.debug_dom_nodes:
            self.switcher.current = IDS.debug.logger.dom_nodes

    @on(Button.Pressed)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == DebugBtnLabels.toggle_diffs:
            result = self.test_manager.create_file_diffs()
            self.test_paths_static.update(result)
        elif event.button.label == DebugBtnLabels.reset_paths:
            result = self.test_manager.reset_test_paths()
            self.test_paths_static.update(result)
        elif event.button.label == DebugBtnLabels.remove_paths:
            result = self.test_manager.remove_test_paths()
            self.test_paths_static.update(result)


class TestPathManager:
    def __init__(self):
        self.test_file_binary = fake.binary(length=2048)
        self.large_file = fake.text(max_nb_chars=700000)
        self.toml_file = self._create_fake_toml_file()
        self.tricky_utf8_file = self._create_tricky_utf8_file()
        self.all_test_paths = self._all_test_paths()

    def _all_test_paths(self) -> list[Path]:
        paths: list[Path] = []
        # Home files
        paths.extend(Files.files_in_home())
        # Dirs
        for dir in Dirs:
            paths.append(Path(dir))
            paths.append(Path(dir) / Files.TOML)
            paths.append(Path(dir) / Files.LARGE)
            if dir == Dirs.TEST_DIR:
                paths.append(Path(dir) / Files.TRICKY_UTF8)
                paths.append(Path(dir) / Files.BINARY)
        return paths

    def _create_fake_toml_file(self):
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

    def _create_tricky_utf8_file(self):
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

    def list_existing_test_paths(self) -> str:
        existing_paths = [str(p) for p in self.all_test_paths if p.exists()]
        if not existing_paths:
            return "[$text-primary]No test paths exist.[/]"
        return "[$text-success]Existing paths:[/]\n" + "\n".join(
            existing_paths
        )

    def reset_test_paths(self) -> str:
        # If all paths exist, do nothing
        if all(p.exists() for p in self.all_test_paths):
            return "[$text-warning]All test paths already exist.[/]"
        created_paths: list[str] = []
        # Create directories
        for dir in Dirs:
            Path(dir).mkdir(parents=True, exist_ok=True)
            created_paths.append(dir)
        # Home files
        home_files: dict[Files, str] = {
            Files.TOML: self.toml_file,
            Files.LARGE: self.large_file,
        }
        for file_name, content in home_files.items():
            file_path = Path.home() / file_name
            with open(file_path, "w") as f:
                f.write(content)
            created_paths.append(str(file_path))
        # Dir files
        for dir in Dirs:
            dir_files: dict[str, str | bytes] = {
                Files.TOML: self.toml_file,
                Files.LARGE: self.large_file,
            }
            if dir == Dirs.TEST_DIR:
                dir_files[Files.TRICKY_UTF8] = self.tricky_utf8_file
                dir_files[Files.BINARY] = self.test_file_binary
            for file_name, content in dir_files.items():
                mode = "wb" if isinstance(content, bytes) else "w"
                file_path = Path(dir) / file_name
                with open(file_path, mode) as f:
                    f.write(content)
                created_paths.append(str(file_path))
        return "[$text-success](Re)Created paths:[/]\n" + "\n".join(
            created_paths
        )

    def remove_test_paths(self) -> str:
        removed_paths: list[str] = []
        # Remove files first
        for path in self.all_test_paths:
            if path.exists() and path.is_file():
                path.unlink()
                removed_paths.append(str(path))
        # Then remove directories
        for dir in reversed(Dirs):
            dir_path = Path(dir)
            if dir_path.exists():
                dir_path.rmdir()
                removed_paths.append(dir)
        if not removed_paths:
            return "[$text-warning]No test paths to remove.[/]"
        return "[$text-success]Removed paths:[/]\n" + "\n".join(removed_paths)

    def create_file_diffs(self) -> str:
        if "No test paths exist" in self.list_existing_test_paths():
            return "[$text-warning]No test paths exist to modify.[/]"
        modified: list[str] = []
        for dir in Dirs:
            # Modify LARGE file
            large_path = Path(dir) / Files.LARGE
            if large_path.exists():
                modified_content = self.large_file.replace("the", "").replace(
                    "o", "O"
                )
                with open(large_path, "w") as f:
                    f.write(modified_content)
                modified.append(str(large_path))
            # Modify TOML file
            toml_path = Path(dir) / Files.TOML
            if toml_path.exists():
                modified_content = self.toml_file.replace(
                    "title", "new_title"
                ).replace("true", "false")
                with open(toml_path, "w") as f:
                    f.write(modified_content)
                modified.append(str(toml_path))
        return "[$text-primary]Modified paths:[/]\n" + "\n".join(modified)
