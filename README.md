[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?logo=python)](https://www.python.org/downloads/release/python-3120/)
[![Framework: Textual](https://img.shields.io/badge/framework-Textual-5967FF?logo=python)](https://www.textualize.io/)
[![Pylint](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-blueviolet)](https://github.com/astral-sh/ruff)


Graphical user interface in the terminal for [chezmoi](https://github.com/twpayne/chezmoi). Built with [textual](https://github.com/Textualize/textual).

## Current Use Case

- [Chezmoi](https://www.chezmoi.io/) is installed
- Existing local `chezmoi` repository on disk (`chezmoi init` is not implemented)
- [Python 3.12+](https://www.python.org/) is installed
  (including [Textual](https://textual.textualize.io/) or run with [UV](https://docs.astral.sh/uv/getting-started/installation/))
- Can be safely tested as no write operations are enabled by default.

## Available Chezmoi commands

> enable write operations by setting an env var MOUSSE_ENABLE_CHANGES=1

### Write Operations

- [x] `chezmoi add` file
- [x] `chezmoi apply` file
- [x] `chezmoi re-add` file
- [ ] `chezmoi add` directory
- [ ] `chezmoi add --encrypt` file
- [ ] `chezmoi apply` directory
- [ ] `chezmoi re-add` directory
- [x] `chezmoi destroy`
- [x] `chezmoi forget`
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

- [ ] import files from archives
- [ ] password manager
- [ ] scripts
- [ ] templates
- [x] filemode
- [x] read commands

## Start

> Don't run the python command in a `chezmoi cd` invoked shell, unless you want to test.

Required: `chezmoi` command available and existing `chezmoi` repository.

Clone repo and cd into the `src` directory of the cloned repo.

Then run `python -m chezmoi_mousse`

If you don't have `textual` installed but the `uv` command is available:
`uv run --with textual -m chezmoi_mousse`


- [x] python -m chezmoi_mousse (Python 3.13 with `textual` installed)
- [x] uv run --with textual -m chezmoi_mousse
- [x] Windows
  - [ ] app store
  - [ ] signed executable
  - [x] unpackaged
- [x] Apple
  - [ ] app store
  - [ ] signed executable
  - [x] unpackaged
- [x] Linux
  - [ ] AppImage
  - [ ] briefcase
  - [ ] flatpak
  - [ ] shared public key executable
  - [ ] snap
  - [x] unpackaged
