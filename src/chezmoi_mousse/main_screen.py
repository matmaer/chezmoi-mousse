from collections.abc import Iterable
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, VerticalGroup, Grid, Horizontal
from textual.content import Content
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen

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

from chezmoi_mousse.common import chezmoi, Tools
from chezmoi_mousse.ascii_art import FLOW


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
        with VerticalScroll():
            yield Collapsible(
                ListView(id="cmdnotfound"),
                title="Commands Not Found",
            )
            yield Collapsible(
                Pretty(chezmoi.get_config_dump),
                title="chezmoi dump-config",
            )
            yield Collapsible(
                Pretty(chezmoi.get_template_data),
                title="chezmoi data (template data)",
            )
            yield Collapsible(
                self.GitLog(),
                title="chezmoi git log (last 20 commits)",
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
        table.add_columns(*chezmoi.get_doctor_rows[0].split())

        for line in chezmoi.get_doctor_rows[1:]:
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
                                row[1],
                                url=self.doctor_cmd_map[row[1]]["link"],
                            ),
                            Static(self.doctor_cmd_map[row[1]]["description"]),
                        ),
                    )
                    continue
                list_view.append(
                    ListItem(
                        # color accent as that's how links are styled by default
                        Static(f"[$accent]{row[1]}[/]", markup=True),
                        Static(
                            "Not Found in $PATH, no description available in TUI."
                        ),
                    ),
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

    def __init__(self) -> None:
        super().__init__(
            label=f"{chezmoi.dest_dir}",
            id="managedtree",
        )

    def on_mount(self) -> None:
        dir_paths = set(p for p in chezmoi.get_managed_paths if p.is_dir())
        file_paths = set(p for p in chezmoi.get_managed_paths if p.is_file())

        def recurse_paths(parent, dir_path):
            if dir_path == chezmoi.dest_dir:
                parent = self.root
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            for file in [f for f in file_paths if f.parent == dir_path]:
                leaf_label = f"{str(file.parts[-1])}"
                parent.add_leaf(leaf_label, file)
            sub_dirs = [d for d in dir_paths if d.parent == dir_path]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, chezmoi.dest_dir)
        self.root.collapse_all()
        self.root.expand()


class AddDirTree(DirectoryTree):  # pylint: disable=too-many-ancestors

    def __init__(self) -> None:
        super().__init__(
            path=chezmoi.dest_dir,
            id="adddirtree",
            classes="dir-tree",
        )

    include_unmanaged = reactive(False)
    include_junk = reactive(False)
    paths_to_show: list[Path] = []

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        # case 1: default, do not include unmanaged dirs or trash paths
        if self.include_unmanaged is False and self.include_junk is False:
            clean_paths = Tools.filter_junk(list(paths))
            paths_to_show: list[Path] = []
            for p in clean_paths:
                if p.is_dir() and p in chezmoi.get_managed_parents:
                    paths_to_show.append(p)
                elif p.is_file() and p not in chezmoi.get_managed_paths:
                    paths_to_show.append(p)
            return sorted(paths_to_show)
        # case 2: include unmanaged dirs but not jusk
        if self.include_unmanaged is True and self.include_junk is False:
            return Tools.filter_junk(list(paths))
        # case 3: dont' include unmanaged dirs but include managed trash dirs
        if self.include_unmanaged is True and self.include_junk is True:
            paths_to_show: list[Path] = []
            for p in chezmoi.get_managed_paths:
                if p.is_dir() and p in chezmoi.get_managed_parents:
                    paths_to_show.append(p)
                elif p.is_file():
                    paths_to_show.append(p)
            return sorted(paths_to_show)
        # case 4: both switches "on" or True: include everything
        return paths


class AddTabDirTree(Widget):

    def compose(self) -> ComposeResult:
        if chezmoi.autoadd_enabled:
            yield Static(
                # pylint: disable=line-too-long
                Content.from_markup(
                    "[$warning italic]Git autoadd is enabled, so files will be added automatically.[/]\n"
                )
            )
        yield AddDirTree()


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=line-too-long
        self.border_title = "filters "
        self.unmanaged_tooltip = "Enable to Include all un-managed files, even if they live in an un-managed directory. Disable to only show un-managed files in directories which already contain managed files (the default). The purpose is to easily spot new un-managed files in already managed directories. (in both cases, only the un-managed files are shown)"
        self.junk_tooltip = 'Show files and directories considered as "junk" for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories.  You can disable this, for example if you want to add files to your chezmoi repository which are in a directory named "cache".'

    def compose(self) -> ComposeResult:

        with Horizontal(classes="filter-container"):
            yield Switch(
                value=False,
                id="includeunmanaged",
                classes="filter-switch",
            )
            yield Label(
                id="unmanagedlabel",
                classes="filter-label",
            )
            yield Label(
                "(?)", id="unmanagedtooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.unmanaged_tooltip)

        with Horizontal(classes="filter-container"):
            yield Switch(
                value=False,
                id="includejunk",
                classes="filter-switch",
            )
            yield Label(
                "no text set",
                id="junklabel",
                classes="filter-label",
            )
            yield Label(
                "(?)", id="junktooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.junk_tooltip)

    @on(Switch.Changed, "#includeunmanaged")
    def show_unmanaged_dirs(self, event: Switch.Changed) -> None:
        self.screen.query_exactly_one(AddDirTree).include_unmanaged = (
            event.value
        )
        self.screen.query_exactly_one(AddDirTree).reload()

    @on(Switch.Changed, "#includejunk")
    def include_junk(self, event: Switch.Changed) -> None:
        self.screen.query_exactly_one(AddDirTree).include_junk = event.value
        self.screen.query_exactly_one(AddDirTree).reload()

    def on_mount(self) -> None:
        switch_labels = {
            "#unmanagedlabel": "Include unmanaged directories",
            "#junklabel": "Include junk paths",
        }
        for label_id, label_text in switch_labels.items():
            self.screen.query_exactly_one(label_id, Label).update(label_text)


class AddFileModal(ModalScreen):

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Add file to chezmoi managed files?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class MainScreen(Screen):

    BINDINGS = [
        Binding("i, I", "toggle_slidebar", "Toggle Inspect"),
        Binding("q", "request_quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        yield SlideBar()
        with TabbedContent(
            "Add",
            "Apply",
            "Re-Add",
            "Doctor",
            "Diagram",
        ):
            yield VerticalScroll(AddTabDirTree())
            yield VerticalScroll(ChezmoiStatus(True), ManagedTree())
            yield VerticalScroll(ChezmoiStatus(False), ManagedTree())
            yield VerticalScroll(Doctor())
            yield Static(FLOW, id="diagram")
        yield Footer()

    def action_request_quit(self) -> None:
        """Action to display the quit dialog."""
        self.app.push_screen(AddFileModal())

    # Underscore to ignore return value from screen.dismiss()
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.screen.query_exactly_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.screen.query_exactly_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
