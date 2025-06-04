[![Pylint](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

terminal user interface for [chezmoi](https://github.com/twpayne/chezmoi), pretty print its environment and starting operations from the relevant visualized components. Built with [textual](https://github.com/Textualize/textual) and [rich](https://github.com/Textualize/rich), see [Textualize](https://www.textualize.io/).

The name of the repository chezmoi-mousse is a wink to the mouse.
The project is in its very early stages, see roadmap below.

## Run app

The app is not packaged yet, can be run as a module with python and `textual`.

## General goals for a first release

- support chezmoi add, re-add and apply commands
- support interactive operations for regular files
- use `textual` features for rich visualization
- keep app as safe as possible to avoid user mistakes with visualizations
- have no support for system interaction other than through chezmoi

## Roadmap

### Chezmoi commands

- [x] `chezmoi data`
- [x] `chezmoi doctor`
- [x] `chezmoi config-dump`
- [x] `chezmoi ignored`
- [x] `chezmoi cat-config`
- [x] `chezmoi managed`
- [x] `chezmoi unmanaged`
- [x] `chezmoi diff`
- [x] `chezmoi status`
- [x] `chezmoi git log`
- [x] `chezmoi cat`
- [x] `chezmoi source-dir`
- [ ] `chezmoi add`
- [ ] `chezmoi apply`
- [ ] `chezmoi re-add`


### Todo notes

- [ ] implement pre-flight checks before app can load with feedback in an  inline textual app
- [x] Implement first startup loading screen
  - [x] create animated ascii art font on the loading screen
- [x] Create widget to show subprocess shell IO as it happens
  - [x] log the chezmoi commands which ran ran to load all data
- [ ] handle chezmoi init recommendation when config was changed
- [ ] Check https://github.com/actions/attest-build-provenance