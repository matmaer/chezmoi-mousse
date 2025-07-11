[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)](https://www.python.org/downloads/release/python-3110/)
[![Framework: Textual](https://img.shields.io/badge/framework-Textual-5967FF?logo=python)](https://www.textualize.io/)
[![Pylint](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-blueviolet)](https://github.com/astral-sh/ruff)


Graphical user interface in the terminal for [chezmoi](https://github.com/twpayne/chezmoi). Built with [textual](https://github.com/Textualize/textual).

## Current Use Case

- [Chezmoi](https://www.chezmoi.io/) is installed
- Existing local `chezmoi` repository on disk (`chezmoi init` is not implemented)
- [Python 3.11+](https://www.python.org/) is installed
  (including [Textual](https://textual.textualize.io/) or run with [UV](https://docs.astral.sh/uv/getting-started/installation/))
- Can be safely tested as no write operations are enabled by default.

## Available Chezmoi commands

> enable write operations by setting an env var MOUSSE_ENABLE_CHANGES=1

### Write Operations

- [x] `chezmoi add` file
- [x] `chezmoi apply` file
- [x] `chezmoi re-add` file
- [ ] `chezmoi add` directory
- [ ] `chezmoi apply` directory
- [ ] `chezmoi re-add` directory
- [ ] `chezmoi destroy`
- [ ] `chezmoi forget`
- [ ] `chezmoi init`

### Read Operations

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
