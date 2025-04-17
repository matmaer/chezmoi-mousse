from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    VerticalGroup,
    VerticalScroll,
)
from textual.content import Content
from textual.lazy import Lazy
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Collapsible,
    DirectoryTree,
    Footer,
    Header,
    Label,
    Static,
    Switch,
    TabbedContent,
    Tree,
)

from chezmoi_mousse.constants import FLOW
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.doctor import Doctor
import chezmoi_mousse.factory as factory


class ChezmoiStatus(VerticalScroll):

    # Chezmoi status command output reference:
    # https://www.chezmoi.io/reference/commands/status/
    status_info = {
        "code name": {
            "space": "No change",
            "A": "Added",
            "D": "Deleted",
            "M": "Modified",
            "R": "Modified Script",
        },
        "re add change": {
            "space": "no changes for repository",
            "A": "add to repository",
            "D": "mark as deleted in repository",
            "M": "modify in repository",
            "R": "not applicable for repository",
        },
        "apply change": {
            "space": "no changes for filesystem",
            "A": "create on filesystem",
            "D": "delete from filesystem",
            "M": "modify on filesystem",
            "R": "modify script on filesystem",
        },
    }

    def __init__(self, apply: bool) -> None:
        # if true, adds apply status to the list, otherwise "re-add" status
        self.apply = apply
        self.status_items: list[Collapsible] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalGroup(*self.status_items)

    def on_mount(self) -> None:

        changes: list[tuple[str, Path]] = chezmoi.get_status(
            apply=self.apply, files=True, dirs=False
        )

        for status_code, path in changes:
            status: str = self.status_info["code name"][status_code]

            rel_path = str(path.relative_to(chezmoi.config["destDir"]))

            self.status_items.append(
                Collapsible(
                    factory.colored_diff(chezmoi.diff(str(path), self.apply)),
                    title=f"{status} {rel_path}",
                    classes="collapsible-defaults",
                )
            )
        self.refresh(recompose=True)


class ManagedTree(Tree):

    def __init__(self, apply: bool) -> None:
        self.apply = apply
        super().__init__(
            label=str(chezmoi.config["destDir"]), id="managed_tree"
        )

    def on_mount(self) -> None:

        dest_dir_path = Path(chezmoi.config["destDir"])

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir_path:
                parent = self.root
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [
                f for f in chezmoi.managed_f_paths if f.parent == dir_path
            ]
            for file in files:
                parent.add_leaf(str(file.parts[-1]))
            sub_dirs = [
                d for d in chezmoi.managed_d_paths if d.parent == dir_path
            ]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir_path)
        self.root.expand()


# pylint: disable=too-many-ancestors
class FilteredAddDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(True, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = set(chezmoi.managed_d_paths)
        managed_files = set(chezmoi.managed_f_paths)

        # Switches: Red - Green (default)
        if not self.include_unmanaged_dirs and self.filter_unwanted:
            return [
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent == Path(chezmoi.config["destDir"])
                    )
                    and not chezmoi.is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not chezmoi.is_unwanted_path(p)
                    and p in managed_dirs
                )
            ]
        # Switches: Red - Red
        if not self.include_unmanaged_dirs and not self.filter_unwanted:
            return [
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent == Path(chezmoi.config["destDir"])
                    )
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            ]
        # Switches: Green - Green
        if self.include_unmanaged_dirs and self.filter_unwanted:
            return [
                p
                for p in paths
                if p not in managed_files and not chezmoi.is_unwanted_path(p)
            ]
        # Switches: Green - Red , this means the following is true:
        # "self.include_unmanaged_dirs and not self.filter_unwanted"
        return [
            p
            for p in paths
            if p.is_dir() or (p.is_file() and p not in managed_files)
        ]


class AddDirTree(Widget):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "add_path", "Add Path"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield FilteredAddDirTree(
                chezmoi.config["destDir"], id="adddirtree", classes="dir-tree"
            )

    def on_mount(self) -> None:
        self.query_one(FilteredAddDirTree).root.label = (
            f"{chezmoi.config["destDir"]} (destDir)"
        )

    def action_add_path(self) -> None:
        cursor_node = self.query_exactly_one(FilteredAddDirTree).cursor_node
        self.app.push_screen(ChezmoiAdd(cursor_node.data.path))  # type: ignore[reportOptionalMemberAccess] # pylint: disable:line-too-long


class ChezmoiAdd(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss", "dismiss modal screen", show=False)
    ]

    def __init__(self, path_to_add: Path) -> None:
        self.path_to_add = path_to_add
        self.files_to_add: list[Path] = []
        self.add_path_items: list[Collapsible] = []
        self.add_label = "- Add File -"
        self.auto_warning = ""
        super().__init__(id="addfilemodal")

    def compose(self) -> ComposeResult:
        with Container(id="addfilemodalcontainer", classes="operationmodal"):
            if chezmoi.autocommit_enabled:
                yield Static(
                    Content.from_markup(
                        f"[$warning italic]{self.auto_warning}[/]"
                    ),
                    classes="autowarning",
                )
            yield VerticalGroup(*self.add_path_items)
            yield Horizontal(
                Button(self.add_label, id="addfile"),
                Button("- Cancel -", id="canceladding"),
            )

    def on_mount(self) -> None:
        # pylint: disable=line-too-long
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            self.auto_warning = '"Auto Commit" is enabled: added file(s) will also be committed.'
        elif chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            self.auto_warning = '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed the remote.'
        collapse = True
        self.files_to_add: list[Path] = []
        if self.path_to_add.is_file():
            self.files_to_add: list[Path] = [self.path_to_add]
            collapse = False
        elif self.path_to_add.is_dir():
            self.files_to_add = chezmoi.unmanaged_in_d(self.path_to_add)
        if len(self.files_to_add) == 0:
            # pylint: disable=line-too-long
            self.notify(
                f"The selected directory does not contain unmanaged files to add.\nDirectory: {self.path_to_add}."
            )
            self.dismiss()
        elif len(self.files_to_add) > 1:
            self.add_label = "- Add Files -"

        for f in self.files_to_add:
            self.add_path_items.append(
                Collapsible(
                    factory.rich_file_content(f),
                    collapsed=collapse,
                    title=str(str(f)),
                    classes="collapsible-defaults",
                )
            )
        self.refresh(recompose=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "addfile":
            for f in self.files_to_add:
                chezmoi.add(f)
                self.notify(f"Added {f} to chezmoi.")
            self.screen.dismiss()
        elif event.button.id == "canceladding":
            self.notify("No files were added.")
            self.screen.dismiss()


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=line-too-long
        self.border_title = "filters "
        self.unmanaged_tooltip = "Enable to include all un-managed files, even if they live in an un-managed directory. Disable to only show un-managed files in directories which already contain managed files (the default). The purpose is to easily spot new un-managed files in already managed directories. (in both cases, only the un-managed files are shown)"
        self.junk_tooltip = 'Filter out files and directories considered as "unwanted" for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories.  You can disable this, for example if you want to add files to your chezmoi repository which are in a directory named "cache".'

    def compose(self) -> ComposeResult:

        with Horizontal(classes="filter-container"):
            yield Switch(
                value=False, id="includeunmanaged", classes="filter-switch"
            )
            yield Label(
                "Include unmanaged directories",
                id="unmanagedlabel",
                classes="filter-label",
            )
            yield Label(
                "(?)", id="unmanagedtooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.unmanaged_tooltip)

        with Horizontal(classes="filter-container"):
            yield Switch(value=True, id="filterjunk", classes="filter-switch")
            yield Label(
                "Filter unwanted paths", id="unwanted", classes="filter-label"
            )
            yield Label(
                "(?)", id="junktooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.junk_tooltip)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.screen.query_exactly_one(FilteredAddDirTree)
        if event.switch.id == "includeunmanaged":
            add_dir_tree.include_unmanaged_dirs = event.value
            add_dir_tree.reload()
        elif event.switch.id == "filterjunk":
            add_dir_tree.filter_unwanted = event.value
            add_dir_tree.reload()


class MainScreen(Screen):

    BINDINGS = [Binding("f", "toggle_slidebar", "Filters")]

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")

        with TabbedContent("Apply", "Re-Add", "Add", "Doctor", "Diagram"):
            yield VerticalScroll(
                Lazy(ChezmoiStatus(apply=True)),
                ManagedTree(apply=True),
                can_focus=False,
            )
            yield VerticalScroll(
                Lazy(ChezmoiStatus(apply=False)),
                ManagedTree(apply=False),
                can_focus=False,
            )
            yield VerticalScroll(AddDirTree(), can_focus=False)
            yield VerticalScroll(Doctor(), id="doctor", can_focus=False)
            yield VerticalScroll(Static(FLOW, id="diagram"))
        yield SlideBar()
        yield Footer()

    def action_toggle_slidebar(self):
        self.screen.query_exactly_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.screen.query_exactly_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
