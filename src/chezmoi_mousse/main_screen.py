from collections.abc import Iterable
from pathlib import Path

from rich.text import Text

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Center,
    Horizontal,
    VerticalGroup,
    VerticalScroll,
)
from textual.content import Content
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
    Switch,
    TabbedContent,
    Tree,
)

from chezmoi_mousse.ascii_art import FLOW
from chezmoi_mousse.common import Tools, chezmoi


class Doctor(Widget):

    class GitLog(DataTable):

        def __init__(self) -> None:
            super().__init__(id="gitlog", cursor_type="row")

        def on_mount(self) -> None:
            self.add_columns("COMMIT", "MESSAGE")
            for line in chezmoi.git_log.std_out.splitlines():
                columns = line.split(";")
                self.add_row(*columns)

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=line-too-long
        self.doctor_cmd_map = {
            "age-command": {
                "description": "A simple, modern and secure file encryption tool",
                "link": "https://github.com/FiloSottile/age",
            },
            "bitwarden-command": {
                "description": "Bitwarden Password Manager",
                "link": "https://github.com/bitwarden/cli",
            },
            "bitwarden-secrets-command": {
                "description": "Bitwarden Secrets Manager CLI for managing secrets securely.",
                "link": "https://github.com/bitwarden/bitwarden-secrets",
            },
            "doppler-command": {
                "description": "The Doppler CLI for managing secrets, configs, and environment variables.",
                "link": "https://github.com/DopplerHQ/cli",
            },
            "gopass-command": {
                "description": "The slightly more awesome standard unix password manager for teams.",
                "link": "https://github.com/gopasspw/gopass",
            },
            "keeper-command": {
                "description": "An interface to Keeper® Password Manager",
                "link": "https://github.com/Keeper-Security/Commander",
            },
            "keepassxc-command": {
                "description": "Cross-platform community-driven port of Keepass password manager",
                "link": "https://keepassxc.org/",
            },
            "lpass-command": {
                "description": "Old LastPass CLI for accessing your LastPass vault.",
                "link": "https://github.com/lastpass/lastpass-cli",
            },
            "pass-command": {
                "description": "Stores, retrieves, generates, and synchronizes passwords securely",
                "link": "https://www.passwordstore.org/",
            },
            "pinentry-command": {
                "description": "Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
                "link": "https://gnupg.org/related_software/pinentry/",
            },
            "rbw-command": {
                "description": "Unofficial Bitwarden CLI",
                "link": "https://git.tozt.net/rbw",
            },
            "vault-command": {
                "description": "A tool for managing secrets",
                "link": "https://vaultproject.io/",
            },
        }

    def compose(self) -> ComposeResult:
        yield DataTable(id="doctortable", show_cursor=False)
        with VerticalScroll(can_focus=False):
            yield Collapsible(
                ListView(id="cmdnotfound"), title="Commands Not Found"
            )
            yield Collapsible(
                Pretty(chezmoi.get_config_dump), title="chezmoi dump-config"
            )
            yield Collapsible(
                Pretty(chezmoi.template_data_dict),
                title="chezmoi data (template data)",
            )
            yield Collapsible(
                self.GitLog(), title="chezmoi git log (last 20 commits)"
            )
            yield Collapsible(
                Pretty(chezmoi.cat_config.std_out.splitlines()),
                title="chezmoi cat-config (contents of config-file)",
            )
            yield Collapsible(
                Pretty(chezmoi.ignored.std_out.splitlines()),
                title="chezmoi ignored (git ignore in source-dir)",
            )

    def on_mount(self) -> None:

        list_view = self.query_exactly_one("#cmdnotfound", ListView)
        table = self.query_exactly_one("#doctortable", DataTable)
        doctor_rows = chezmoi.doctor.std_out.splitlines()
        table.add_columns(*doctor_rows[0].split())

        for line in doctor_rows[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "ok":
                row = [
                    Text(cell_text, style=f"{self.app.current_theme.success}")
                    for cell_text in row
                ]
            elif row[0] == "warning":
                row = [
                    Text(cell_text, style=f"{self.app.current_theme.warning}")
                    for cell_text in row
                ]
            elif row[0] == "error":
                row = [
                    Text(cell_text, style=f"{self.app.current_theme.error}")
                    for cell_text in row
                ]
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(cell_text, style=f"{self.app.current_theme.warning}")
                    for cell_text in row
                ]
            elif row[0] == "info" and "not found in $PATH" in row[2]:
                if row[1] in self.doctor_cmd_map:
                    list_view.append(
                        ListItem(
                            Link(
                                row[1], url=self.doctor_cmd_map[row[1]]["link"]
                            ),
                            Static(self.doctor_cmd_map[row[1]]["description"]),
                        )
                    )
                    continue
                list_view.append(
                    ListItem(
                        # color accent as that's how links are styled by default
                        Static(f"[$accent]{row[1]}[/]", markup=True),
                        Static(
                            "Not Found in $PATH, no description available in TUI."
                        ),
                    )
                )
                continue
            else:
                row = [Text(cell_text) for cell_text in row]
            table.add_row(*row)


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

        if self.apply:
            changes = chezmoi.get_apply_changes
        else:
            changes = chezmoi.get_add_changes

        for code, path in changes:
            status: str = self.status_info["code name"][code]
            rel_path = str(path.relative_to(chezmoi.dest_dir))

            colored_diffs: list[Label] = []
            for line in chezmoi.get_cm_diff(str(path), self.apply):
                if line.startswith("- "):
                    colored_diffs.append(Label(line, variant="error"))
                elif line.startswith("+ "):
                    colored_diffs.append(Label(line, variant="success"))
                elif line.startswith("  "):
                    colored_diffs.append(Label(line, classes="muted"))
            colored_diffs.append(Label())
            self.status_items.append(
                Collapsible(*colored_diffs, title=f"{status} {rel_path}")
            )
        self.refresh(recompose=True)


class ManagedTree(Tree):

    def __init__(self, apply: bool) -> None:
        self.apply = apply
        super().__init__(label=str(chezmoi.dest_dir), id="managed_tree")

    def on_mount(self) -> None:
        dest_dir_path = Path(chezmoi.get_config_dump["destDir"])
        file_paths = chezmoi.get_managed_files

        if self.apply:
            dir_paths = chezmoi.get_managed_parents
        else:
            status_paths = [t[1] for t in chezmoi.get_add_changes]
            dir_paths = {path for path in status_paths if path.is_dir()}

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir_path:
                parent = self.root
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [f for f in file_paths if f.parent == dir_path]
            for file in files:
                parent.add_leaf(str(file.parts[-1]), file)
            sub_dirs = [d for d in dir_paths if d.parent == dir_path]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir_path)
        self.root.expand()


class AddDirTree(Widget):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "add_file", "Add Path"),
    ]

    # pylint: disable=too-many-ancestors
    class FilteredAddDirTree(DirectoryTree):

        include_unmanaged = reactive(False)
        include_junk = reactive(False)

        def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
            # Do not include any junk paths
            # Include unmanaged files if they are part of a directory which
            # already has managed files in chezmoi.get_managed_paths.
            if not self.include_unmanaged and not self.include_junk:
                paths_to_show: list[Path] = []
                for p in Tools.filter_junk(list(paths)):
                    if p.is_dir() and p in chezmoi.get_managed_parents:
                        paths_to_show.append(p)
                    elif (
                        p.is_file() and p.parent in chezmoi.get_managed_parents
                    ):
                        paths_to_show.append(p)
                return paths_to_show
            # Do not include any junk paths
            # Include any unmanaged path in the destDir
            if self.include_unmanaged and not self.include_junk:
                return Tools.filter_junk(list(paths))
            # Include any unmanaged path in the destDir,
            # even if they are considered junk paths.
            if not self.include_unmanaged and self.include_junk:
                paths_to_show: list[Path] = []
                for p in list(paths):
                    if p.is_dir() and p in chezmoi.get_managed_parents:
                        paths_to_show.append(p)
                    elif (
                        p.is_file() and p.parent in chezmoi.get_managed_parents
                    ):
                        paths_to_show.append(p)
                return paths_to_show
            # Both switches "on": include all files in the destDir path
            return list(paths)

    def compose(self) -> ComposeResult:
        if chezmoi.autoadd_enabled:
            yield Static(
                # pylint: disable=line-too-long
                Content.from_markup(
                    '[$warning italic]"autoadd" is enabled: changes will be added to the source state after any change.[/]\n'
                )
            )
        yield self.FilteredAddDirTree(chezmoi.dest_dir, id="adddirtree")

    def action_add_file(self) -> None:
        self.app.push_screen(AddFileModal())


class AddFileModal(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss", "dismiss modal screen", show=False)
    ]

    def __init__(self, file_name: str = ""):
        self.file_name = file_name
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Center(
            Static("file add modal"),
            Horizontal(
                Button("Add", id="addfile"), Button("Cancel", id="cancel")
            ),
            id="addfilemodal",
            classes="operationmodal",
        )

    def on_mount(self):
        add_file_modal = self.query_one("#addfilemodal")
        add_file_modal.border_title = self.title
        add_file_modal.border_subtitle = "Escape to cancel"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "addfile":
            self.screen.dismiss()
        if event.button.id == "re_add_file":
            self.screen.dismiss()
        elif event.button.id == "cancel":
            self.screen.dismiss()
            self.notify("no write operation performed")


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=line-too-long
        self.border_title = "filters "
        self.unmanaged_tooltip = "Enable to include all un-managed files, even if they live in an un-managed directory. Disable to only show un-managed files in directories which already contain managed files (the default). The purpose is to easily spot new un-managed files in already managed directories. (in both cases, only the un-managed files are shown)"
        self.junk_tooltip = 'Show files and directories considered as "junk" for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories.  You can disable this, for example if you want to add files to your chezmoi repository which are in a directory named "cache".'

    def compose(self) -> ComposeResult:

        with Horizontal(classes="filter-container"):
            yield Switch(
                value=False, id="includeunmanaged", classes="filter-switch"
            )
            yield Label(id="unmanagedlabel", classes="filter-label")
            yield Label(
                "(?)", id="unmanagedtooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.unmanaged_tooltip)

        with Horizontal(classes="filter-container"):
            yield Switch(
                value=False, id="includejunk", classes="filter-switch"
            )
            yield Label("no text set", id="junklabel", classes="filter-label")
            yield Label(
                "(?)", id="junktooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.junk_tooltip)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.screen.query_exactly_one(
            AddDirTree.FilteredAddDirTree
        )
        if event.switch.id == "includeunmanaged":
            add_dir_tree.include_unmanaged = event.value
            add_dir_tree.reload()
        elif event.switch.id == "includejunk":
            add_dir_tree.include_junk = event.value
            add_dir_tree.reload()

    def on_mount(self) -> None:
        switch_labels = {
            "#unmanagedlabel": "Include unmanaged directories",
            "#junklabel": "Include junk paths",
        }
        for label_id, label_text in switch_labels.items():
            self.screen.query_exactly_one(label_id, Label).update(label_text)


class MainScreen(Screen):

    BINDINGS = [Binding("f", "toggle_slidebar", "Filters")]

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")

        with TabbedContent("Apply", "Re-Add", "Add", "Doctor", "Diagram"):
            yield VerticalScroll(
                ChezmoiStatus(apply=True),
                ManagedTree(apply=True),
                can_focus=False,
            )
            yield VerticalScroll(
                ChezmoiStatus(apply=False),
                ManagedTree(apply=False),
                can_focus=False,
            )
            yield VerticalScroll(AddDirTree(), can_focus=False)
            yield VerticalScroll(Doctor(), id="doctor", can_focus=False)
            yield Static(FLOW, id="diagram")
        yield SlideBar()
        yield Footer()

    def action_toggle_slidebar(self):
        self.screen.query_exactly_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.screen.query_exactly_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
