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
- [ ] Implement fist startup loading screen
  - [x] show the chezmoi commands run to load all data
  - [x] create animated ascii art font on the loading screen
  - [ ] implement pre-flight checks with feedback what to do if failed
- [ ] Create widget to show subprocess shell IO when using the TUI

### Inspect chezmoi environment widgets

- [x] `chezmoi data`
- [x] `chezmoi doctor`
- [x] `chezmoi config-dump`
- [x] `chezmoi ignored`
- [x] `chezmoi cat-config` for toml format
- [ ] `git config` for the local chezmoi repository
- [ ] `git status` between local and remote chezmoi repository
- ...

### Operate chezmoi widgets

- [ ] interactive chezmoi status
  - [ ] chezmoi re-add
  - [ ] chezmoi apply
  - [ ] autopush option switch
  - [ ] autcommit option switch
  - ...
- [ ] interactive chezmoi managed/unmanaged tab
  - [x] `chezmoi managed` file tree
  - [ ] `chezmoi unmanaged` toggle to add muted entries to the managed tree
  - [ ] `chezmoi add`
  - [ ] `chezmoi forget`
  - [ ] `chezmoi destroy`
  - ...
- [ ] interactive chezmoi diagram

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



