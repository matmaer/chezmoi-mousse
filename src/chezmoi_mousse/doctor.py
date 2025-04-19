from rich.text import Text
from textual.app import ComposeResult

from textual.containers import VerticalScroll

from textual.widget import Widget
from textual.widgets import (
    Collapsible,
    DataTable,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
)

from chezmoi_mousse.chezmoi import chezmoi


class GitLog(DataTable):

    def __init__(self) -> None:
        super().__init__(id="gitlog", cursor_type="row")

    def on_mount(self) -> None:
        self.add_columns("COMMIT", "MESSAGE")
        for line in chezmoi.git_log.list_out:
            columns = line.split(";")
            self.add_row(*columns)


class Doctor(Widget):

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
                ListView(id="cmdnotfound"),
                title="Commands Not Found",
                classes="collapsible-defaults",
            )
            yield Collapsible(
                Pretty(chezmoi.dump_config.dict_out),
                title="chezmoi dump-config",
                classes="collapsible-defaults",
            )
            yield Collapsible(
                Pretty(chezmoi.template_data.dict_out),
                title="chezmoi data (template data)",
                classes="collapsible-defaults",
            )
            yield Collapsible(
                GitLog(),
                title="chezmoi git log (last 20 commits)",
                classes="collapsible-defaults",
            )
            yield Collapsible(
                Pretty(chezmoi.cat_config.list_out),
                title="chezmoi cat-config (contents of config-file)",
                classes="collapsible-defaults",
            )
            yield Collapsible(
                Pretty(chezmoi.ignored.list_out),
                title="chezmoi ignored (git ignore in source-dir)",
                classes="collapsible-defaults",
            )

    def on_mount(self) -> None:

        styles = {
            "ok": f"{self.app.current_theme.success}",
            "warning": f"{self.app.current_theme.warning}",
            "error": f"{self.app.current_theme.error}",
            "info": f"{self.app.current_theme.foreground}",
        }

        list_view = self.query_exactly_one("#cmdnotfound", ListView)
        table = self.query_exactly_one("#doctortable", DataTable)
        doctor_rows = chezmoi.doctor.list_out
        table.add_columns(*doctor_rows[0].split())

        for line in doctor_rows[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                if row[1] in self.doctor_cmd_map:
                    list_view.append(
                        ListItem(
                            Link(
                                row[1], url=self.doctor_cmd_map[row[1]]["link"]
                            ),
                            Static(self.doctor_cmd_map[row[1]]["description"]),
                        )
                    )
                elif row[1] not in self.doctor_cmd_map:
                    list_view.append(
                        ListItem(
                            # color accent as that's how links are styled by default
                            Static(f"[$accent-muted]{row[1]}[/]", markup=True),
                            Label(
                                "Not Found in $PATH, no description available in TUI."
                            ),
                        )
                    )
            elif row[0] == "ok" or row[0] == "warning" or row[0] == "error":
                row = [
                    Text(cell_text, style=f"{styles[row[0]]}")
                    for cell_text in row
                ]
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(cell_text, style=f"{self.app.current_theme.warning}")
                    for cell_text in row
                ]
            else:
                row = [Text(cell_text) for cell_text in row]
            table.add_row(*row)
