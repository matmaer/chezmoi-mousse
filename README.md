terminal user interface for [chezmoi](https://github.com/twpayne/chezmoi), pretty print its environment and starting operations from the relevant visualized components. Built with [textual](https://github.com/Textualize/textual) and [rich](https://github.com/Textualize/rich), see [Textualize](https://www.textualize.io/).

The name of the repository chezmoi-mousse is a wink to the mouse.
The project is in its very early stages, see roadmap below.

## Run app

The app is not packaged yet.

To run:
- create a python venv and activate the venv
- `pip install textual` in the venv
- clone the repo
- change directory to the src directory in the repo
- run the app with `python -m chezmoi_mousse`

## Roadmap

### General
- [x] Create text based version of the `mermaid` diagrams offered by `chezmoi`.
- [x] Implement first startup loading screen
  - [x] show the chezmoi commands run to load all data
  - [x] create animated ascii art font on the loading screen
  - [ ] implement pre-flight checks with feedback what to do if failed
- [ ] Create widget to show subprocess shell IO when using the TUI

### Chezmoi commands

- [x] `chezmoi data`
- [x] `chezmoi doctor`
- [x] `chezmoi config-dump`
- [x] `chezmoi ignored`
- [x] `chezmoi cat-config` for toml format
- [x] `chezmoi managed` paths tree toggle
- [x] `chezmoi unmanaged` paths tree toggle
- [x] `chezmoi diff`
- [x] `chezmoi status`
- [x] `chezmoi git log`
- [x] `git config` for the local chezmoi repository
- [ ] `git status` between local and remote chezmoi repository
- ...

### Chezmoi features

  - [ ] autopush option switch
  - [ ] autcommit option switch

### Chezmoi write commands

  - [x] `chezmoi add`
  - [ ] `chezmoi apply`
  - [ ] `chezmoi re-add`
  - [ ] `chezmoi forget`
  - [ ] `chezmoi destroy`
  - ...

### Development overhead

- [x] Setup development environment
  - [x] Develop in rootless container which includes the chezmoi command
  - [x] Create vscode workspace with integrated `textual-dev` tooling
  - [x] Test relevant vscode extensions
  - [x] Setup linting
  - [x] Setup formatting
  - [x] Setup `pre-commit` hooks.

- CI/CD pipeline
  - [ ] Setup pytest
  - [ ] Packaging
    - ...
  - [ ] Distribution
    - ...
  - [ ] Release pipeline

## General goals

- leverage `textual` features for concise and rich visualizations
- made for existing chezmoi users
- only support interactive operations
- prevent accidental errors
- improve understanding of chezmoi by using the TUI
- make subprocess calls as safe as possible
- modus operandi
  - "loading" screen for initial app startup and pre-flight checks
  - operate screen to operate chezmoi
