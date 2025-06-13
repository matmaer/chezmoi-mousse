[![Pylint](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

Graphical user interface in the terminal for [chezmoi](https://github.com/twpayne/chezmoi). Built with [textual](https://github.com/Textualize/textual).

## Install

- [Python](https://www.python.org/)
- [Textual](https://textual.textualize.io/)
- [Chezmoi](https://www.chezmoi.io/)

## Chezmoi commands

- [ ] `chezmoi add`
- [ ] `chezmoi apply`
- [ ] `chezmoi destroy`
- [ ] `chezmoi forget`
- [ ] `chezmoi init`
- [ ] `chezmoi re-add`
- [x] `chezmoi cat-config`
- [x] `chezmoi cat`
- [x] `chezmoi config-dump`
- [x] `chezmoi data`
- [x] `chezmoi diff`
- [x] `chezmoi doctor`
- [x] `chezmoi git log`
- [x] `chezmoi ignored`
- [x] `chezmoi managed`
- [x] `chezmoi source-dir`
- [x] `chezmoi status`
- [x] `chezmoi unmanaged`


### implemented features

- [ ] file encryption
- [ ] import files from archives
- [ ] password manager
- [ ] scripts
- [ ] templates
- [x] filemode
- [x] read commands

## Start

Feedback is welcome before the app is packaged and supports changing state, it's very safe to test currently.

Required: `chezmoi` command available and existing `chezmoi` repository.

Clone this repository and cd into the `src` directory of the cloned repository.

Then run `python -m chezmoi_mousse`

If you don't have `textual` installed but the `uv` command is available:
`uv run --with textual -m chezmoi_mousse`

(Don't run the app in a `chezmoi cd` invoked shell, it doesn't do anything bad as the app only performs read-only operations but it will crash.)

- [x] python -m chezmoi_mousse (Python 3.13 with `textual` installed)
- [x] uv run --with textual -m chezmoi_mousse
- [x] Windows
  - [ ] app store
  - [ ] single executable
  - [x] unpackaged
- [x] Apple
  - [ ] app store
  - [ ] single executable
  - [x] unpackaged
- [x] Linux
  - [ ] single executable
  - [ ] AppImage
  - [ ] flatpak
  - [ ] snap
  - [x] unpackaged
