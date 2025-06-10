[![Pylint](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

terminal user interface for [chezmoi](https://github.com/twpayne/chezmoi), pretty print its environment and starting operations from the relevant visualized components. Built with [textual](https://github.com/Textualize/textual) and [rich](https://github.com/Textualize/rich), see [Textualize](https://www.textualize.io/).

## Run the App

Requirements:
- [Python 3.13](https://www.python.org/)
- [Textual](https://textual.textualize.io/)

```shell
git clone
cd your/dir/chezmoi-mousse/src
python -m chezmoi_mousse
```

## Supported commands

- [ ] `chezmoi add`
- [ ] `chezmoi apply`
- [ ] `chezmoi destroy`
- [ ] `chezmoi forget`
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


## Supported features

- [ ] file encryption
- [ ] import files from archives
- [ ] password manager
- [ ] scripts
- [ ] templates
- [x] filemode
- [x] read commands


## Packaging

- [x] Vindows
  - [x] unpackaged
  - [ ] executable
- [x] Apple
  - [x] unpackaged
  - [ ] executable
- [x] Linux
  - [x] unpackaged
  - [ ] executable
- [ ] https://github.com/actions/attest-build-provenance