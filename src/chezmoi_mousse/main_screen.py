from collections.abc import Iterable
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll, VerticalGroup
from textual.reactive import reactive
from textual.screen import Screen

from textual.widget import Widget
from textual.widgets import (
    Checkbox,
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
    TabbedContent,
    Tree,
)

from chezmoi_mousse.common import FLOW, chezmoi, status_info, Tooling


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.border_title = "outputs-from-chezmoi-commands"

    def compose(self) -> ComposeResult:

        yield VerticalScroll(
            Static("test"),
        )


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
        yield DataTable(id="doctortable", cursor_type="row")
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

        list_view = self.query_one("#cmdnotfound", ListView)
        table = self.query_one("#doctortable", DataTable)
        table.add_columns(*chezmoi.get_doctor_rows[0].split())

        for line in chezmoi.get_doctor_rows[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "ok":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.success}")
                    for cell in row
                ]
            elif row[0] == "warning":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.warning}")
                    for cell in row
                ]
            elif row[0] == "error":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.error}")
                    for cell in row
                ]
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.warning}")
                    for cell in row
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
                row = [Text(str(cell)) for cell in row]
            table.add_row(*row)


class ChezmoiStatus(VerticalScroll):

    class DiffViewer(Collapsible):
        def __init__(self, diff_title: str, diff_text: Static) -> None:
            super().__init__(
                diff_text,
                collapsed=True,
                title=diff_title,
            )

    def __init__(self, apply: bool) -> None:
        # if true, adds apply status to the list, otherwise "re-add" status
        self.apply = apply
        self.status_items: list[Collapsible] = []
        self.dest_dir = Path(chezmoi.get_config_dump["destDir"])
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalGroup(
            *self.status_items,
            # collapsed=False,
            # id="statusitems",
            # title=f"status in destDir {chezmoi.get_config_dump['destDir']}",
        )
        # yield ListView(id="statuslist")

    def on_mount(self) -> None:

        if self.apply:
            changes = chezmoi.get_apply_changes
        else:
            changes = chezmoi.get_add_changes

        for code, path in changes:
            status: str = status_info["code name"][code]
            rel_path = str(path.relative_to(self.dest_dir))

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
            label=f"{chezmoi.get_config_dump['destDir']}",
        )

    def on_mount(self) -> None:
        dest_dir_path = Path(chezmoi.get_config_dump["destDir"])
        dir_paths = set(p for p in chezmoi.get_managed_paths if p.is_dir())
        file_paths = set(p for p in chezmoi.get_managed_paths if p.is_file())

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir_path:
                parent = self.root
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            for file in [f for f in file_paths if f.parent == dir_path]:
                parent.add_leaf(str(file.parts[-1]), file)
            sub_dirs = [d for d in dir_paths if d.parent == dir_path]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir_path)
        self.root.collapse_all()
        self.root.expand()
        for dirs in self.root.children:
            dirs.expand()


class AddDirTree(Widget):

    class FilteredTree(DirectoryTree):  # pylint: disable=too-many-ancestors

        only_managed_dirs = reactive(True)

        def __init__(self) -> None:
            super().__init__(
                path=chezmoi.get_config_dump["destDir"],
                id="moussetree",
            )

        def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
            all_paths = Tooling.filter_unwanted_paths(list(paths))
            paths_to_show: list[Path] = []
            if self.only_managed_dirs:
                unique_parents = {f.parent for f in chezmoi.get_managed_paths}
                for p in all_paths:
                    if (
                        p.is_dir()
                        and p in unique_parents
                        and p in chezmoi.get_managed_paths
                    ):
                        paths_to_show.append(p)
                    elif p.is_file() and p not in chezmoi.get_managed_paths:
                        paths_to_show.append(p)
                return sorted(paths_to_show)
            return [p for p in all_paths if p not in chezmoi.get_managed_files]

    def compose(self) -> ComposeResult:
        yield Checkbox(
            "show only unmanaged files in directories which already contain managed files",
            id="adddirtreecheckbox",
            classes="tree-checkbox",
            value=True,
        )
        yield self.FilteredTree()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        dir_tree = self.query_one(self.FilteredTree)
        dir_tree.only_managed_dirs = event.value
        dir_tree.reload()


class MainScreen(Screen):

    BINDINGS = [
        Binding("i, I", "toggle_slidebar", "Toggle Inspect"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        yield SlideBar()
        with TabbedContent(
            "Apply",
            "Re-Add",
            "Add",
            "Doctor",
            "Diagram",
        ):
            yield VerticalScroll(ChezmoiStatus(True), ManagedTree())
            yield VerticalScroll(ChezmoiStatus(False), ManagedTree())
            yield VerticalScroll(AddDirTree())
            yield VerticalScroll(Doctor())
            yield Static(FLOW, id="diagram")
        yield Footer()

    # Underscore to ignore return value from screen.dismiss()
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.query_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
