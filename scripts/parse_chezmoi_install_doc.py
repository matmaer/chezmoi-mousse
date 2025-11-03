# TODO has to run when building the package

import json
import urllib.request
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

OUTPUT_DIR = Path("src", "chezmoi_mousse", "gui", "screens")
OUTPUT_FILE = Path.joinpath(OUTPUT_DIR, "chezmoi_install_commands.json")


class TemplateStr(StrEnum):
    """Strings to process the install help and latest chezmoi release."""

    cross_platform = (
        "chezmoi is available in many cross-platform package managers"
    )
    chezmoi_install_doc_url = "https://raw.githubusercontent.com/twpayne/chezmoi/refs/heads/master/assets/chezmoi.io/docs/install.md.tmpl"
    chezmoi_latest_release_url = (
        "https://api.github.com/repos/twpayne/chezmoi/releases/latest"
    )
    more_packages = "For more packages, see"
    os_install = (
        "Install chezmoi with your package manager with a single command"
    )
    version_tag = "{{ $version }}"


def get_install_help() -> str:
    req = urllib.request.Request(
        TemplateStr.chezmoi_install_doc_url,
        headers={"User-Agent": "python-urllib"},
    )
    with urllib.request.urlopen(req, timeout=2) as response:
        return response.read().decode("utf-8")


def get_latest_chezmoi_ver() -> str:
    with urllib.request.urlopen(
        TemplateStr.chezmoi_latest_release_url
    ) as response:
        data = json.load(response)
        return data.get("tag_name")


def pre_process_file() -> list[str]:
    latest_version = get_latest_chezmoi_ver()
    content_list = get_install_help().splitlines()
    # Remove empty lines and code fences
    content_list = [
        line
        for line in content_list
        if line.strip() and not line.strip().startswith("```")
    ]
    # Replace template strings
    replacements: list[tuple[str, str]] = [
        (TemplateStr.version_tag, latest_version),
        ('"', ""),
        ("=== ", ""),
    ]
    for old, new in replacements:
        content_list = [line.replace(old, new) for line in content_list]
    # Strip head and tail
    first_idx = next(
        (
            i
            for i, line in enumerate(content_list)
            if line.startswith(TemplateStr.os_install)
        )
    )
    last_idx = next(
        (
            i
            for i, line in enumerate(content_list)
            if line.startswith(TemplateStr.more_packages)
        )
    )
    content_list = content_list[first_idx:last_idx]
    # Split OS-specific and cross-platform commands
    split_idx = next(
        (
            i
            for i, line in enumerate(content_list)
            if line.startswith(TemplateStr.cross_platform)
        )
    )
    # Generate result
    result = content_list[1:split_idx]  # OS-specific commands
    result.append("Cross-Platform")  # Add a header and indent cross-platform
    result.extend(f"    {line}" for line in content_list[split_idx + 1 :])
    freebsd_idx = next(
        (i for i, line in enumerate(result) if line.startswith("FreeBSD"))
    )
    # insert a list item before FreeBSD
    result.insert(freebsd_idx, "Unix-like systems")
    # increase indent for the next four lines (FreeBSD and OpenIndiana commands)
    for i in range(freebsd_idx + 1, freebsd_idx + 5):
        result[i] = f"    {result[i]}"
    return result


class Node(TypedDict):
    text: str
    indent: int
    children: list["Node"]


type Value = str | dict[str, "Value"]


def parse_indented_text(lines: list[str]) -> dict[str, Value]:
    root_node: Node = {"text": "", "indent": -1, "children": []}
    stack: list[Node] = [root_node]

    # construct tree
    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        # Pop nodes with greater or equal indentation
        while stack and indent <= stack[-1]["indent"]:
            stack.pop()
        # Add new node
        node: Node = {"text": line.strip(), "indent": indent, "children": []}
        stack[-1]["children"].append(
            node
        )  # will modify the root_node variable
        stack.append(node)

    # collapse tree into nested dictionary
    def collapse(node: Node) -> Value:
        # a node without children is the text of the command
        if not node["children"]:
            return node["text"]
        # Single child becomes its value for a nested structure
        if len(node["children"]) == 1:
            return collapse(node["children"][0])
        # Multiple children become a dictionary
        return {child["text"]: collapse(child) for child in node["children"]}

    # return final nested dict
    return {child["text"]: collapse(child) for child in root_node["children"]}


if __name__ == "__main__":
    all_lines: list[str] = pre_process_file()
    data = parse_indented_text(all_lines)
    OUTPUT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
