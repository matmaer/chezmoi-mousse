# chezmoi-mousse
TUI for ChezMoi with a wink to the mouse.

This repository is for testing a terminal user interface for [chezmoi](https://github.com/twpayne/chezmoi).

Roadmap

- app startup
    - check if chezmoi is available
    - check if there is a current chezmoi config file
- app buttons
    - generate chezmoi config
    - show files tracked by chezmoi
    - update personal chezmoi dotfiles repo (locally and remotely)
    - edit dotfiles, and follow up subsequent workflow actions
    - update local dotfile from local or remote personal chezmoi repo


Possible thanks to [Textual](https://github.com/Textualize/textual) and [Python](https://www.python.org/).

Current `pacman -Qi chezmoi` output:

```text
Name            : chezmoi
Version         : 2.52.4
Description     : Manage your dotfiles across multiple machines
Architecture    : x86_64
URL             : https://www.chezmoi.io/
Licenses        : MIT
Depends On      : glibc
```