import os

from textual.app import ComposeResult
from textual.widgets import DataTable, Tree, Label, Static

from chezmoi_mousse.common import chezmoi


class ChezmoiDoctor(Static):

    # pylint: disable=line-too-long
    command_info = {
        "age": {
            "Description": "A simple, modern and secure file encryption tool",
            "URL": "https://github.com/FiloSottile/age",
        },
        "gopass": {
            "Description": "The slightly more awesome standard unix password manager for teams.",
            "URL": "https://github.com/gopasspw/gopass",
        },
        "pass": {
            "Description": "Stores, retrieves, generates, and synchronizes passwords securely",
            "URL": "https://www.passwordstore.org/",
        },
        "rbw": {
            "Description": "Unofficial Bitwarden CLI",
            "URL": "https://git.tozt.net/rbw",
        },
        "vault": {
            "Description": "A tool for managing secrets",
            "URL": "https://vaultproject.io/",
        },
        "pinentry": {
            "Description": "Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
            "URL": "https://gnupg.org/related_software/pinentry/",
        },
        "keepassxc": {
            "Description": "Cross-platform community-driven port of Keepass password manager",
            "URL": "https://keepassxc.org/",
        },
    }


    def compose(self) -> ComposeResult:
        yield DataTable(
            id="main_table",
            cursor_type="row",
        )
        yield Label(
            "Local commands skipped because not in Path:",
        )
        yield DataTable(
            id="second_table",
            cursor_type="row",
        )

    def on_mount(self) -> None:

        doctor = chezmoi.doctor.updated_py_out()

        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")

        header_row = doctor.pop(0).split()

        main_table.add_columns(*header_row)
        second_table.add_columns("COMMAND", "DESCRIPTION", "URL")

        for row in [row.split(maxsplit=2) for row in doctor]:
            if row[0] == "info" and "not found in $PATH" in row[2]:
                # check if the command exists in the command_info dict
                command = row[2].split()[0]
                if command in self.command_info:
                    row = [
                        command,
                        self.command_info[command]["Description"],
                        self.command_info[command]["URL"],
                    ]
                else:
                    row = [
                        command,
                        "Not found in $PATH",
                        "...",
                    ]
                second_table.add_row(*row)
            else:
                if row[0] == "ok":
                    row = [f"[#3fc94d]{cell}[/]" for cell in row]
                elif row[0] == "warning":
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                elif row[0] == "error":
                    row = [f"[red]{cell}[/]" for cell in row]
                elif row[0] == "info" and row[2] == "not set":
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                else:
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                main_table.add_row(*row)


class ChezmoiStatus(Static):
    # Chezmoi status command output reference:
    # https://www.chezmoi.io/reference/commands/status/

    status_table = {
        " ": {
            "Status": "No change",
            "Re_Add_Change": "No change",
            "Apply_Change": "No change",
        },
        "A": {
            "Status": "Added",
            "Re_Add_Change": "Entry was created",
            "Apply_Change": "Entry will be created",
        },
        "D": {
            "Status": "Deleted",
            "Re_Add_Change": "Entry was deleted",
            "Apply_Change": "Entry will be deleted",
        },
        "M": {
            "Status": "Modified",
            "Re_Add_Change": "Entry was modified",
            "Apply_Change": "Entry will be modified",
        },
        "R": {
            "Status": "Run",
            "Re_Add_Change": "Not applicable",
            "Apply_Change": "Entry will be run",
        },
    }

    def __init__(self, status_py_out: list):
        super().__init__()
        self.status_py_out = status_py_out

    def compose(self) -> ComposeResult:
        yield Label("Chezmoi Apply Status")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status")
        yield DataTable(id="re_add_table")

    def on_mount(self):

        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in self.status_py_out:
            path = line[3:]

            apply_status = self.status_table[line[0]]["Status"]
            apply_change = self.status_table[line[0]]["Apply_Change"]

            re_add_status = self.status_table[line[1]]["Status"]
            re_add_change = self.status_table[line[1]]["Re_Add_Change"]

            apply_table.add_row(*[apply_status, path, apply_change])
            re_add_table.add_row(*[re_add_status, path, re_add_change])


class ManagedFiles(Static):

    def compose(self) -> ComposeResult:
        yield Tree(id="managed_tree", label="destDir")

    

    def build_tree(self, paths):
        json_tree = {}
        for path in paths:
            parts = path.split(os.sep)
            current_level = json_tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
        return json_tree

    # def on_mount(self) -> None:
    #     managed_files = chezmoi.managed.updated_py_out()
    #     tree = self.query_one("#managed_tree")
    #     json_tree = self.build_tree(managed_files)

        # Loop over the generated json_tree object
        # Add leafs and nested leafs to the tree widget

    # def add_leafs(self, tree, json_tree, parent_node=None):
    #     for key, value in json_tree.items():
    #         node = tree.add(parent_node, key) if parent_node else tree.add(key)
    #         if isinstance(value, dict):
    #             self.add_leafs(tree, value, node)

    # def on_mount(self) -> None:
    #     managed_files = chezmoi.managed.updated_py_out()
    #     tree = self.query_one("#managed_tree")
    #     json_tree = self.build_tree(managed_files)

    #     # Add leafs and nested leafs to the tree widget
    #     self.add_leafs(tree, json_tree)

        # ...existing code...

    def add_leafs(self, tree, json_tree, parent_node=None):
        for key, value in json_tree.items():
            node = parent_node.add(key) if parent_node else tree.root.add(key)
            if isinstance(value, dict):
                self.add_leafs(tree, value, node)

    def on_mount(self) -> None:
        managed_files = chezmoi.managed.updated_py_out()
        tree = self.query_one("#managed_tree")
        json_tree = self.build_tree(managed_files)

        # Add leafs and nested leafs to the tree widget
        self.add_leafs(tree, json_tree)