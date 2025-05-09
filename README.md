terminal user interface for [chezmoi](https://github.com/twpayne/chezmoi), pretty print its environment and starting operations from the relevant visualized components. Built with [textual](https://github.com/Textualize/textual) and [rich](https://github.com/Textualize/rich), see [Textualize](https://www.textualize.io/).

The name of the repository chezmoi-mousse is a wink to the mouse.
The project is in its very early stages, see roadmap below.

## Run app

The app is not packaged yet, can be run as a module with python and `textual`.

## Roadmap

### General
- [x] Create text based version of the `mermaid` diagrams offered by `chezmoi`.
- [x] Implement first startup loading screen
  - [x] show the chezmoi commands run to load all data
  - [x] create animated ascii art font on the loading screen
  - [ ] implement pre-flight checks with feedback what to do if failed
    - [ ] handle chezmoi init recommendation when config was changed
- [ ] Create widget to show subprocess shell IO when using the TUI
- [ ] Spaced-out/compact content toggling

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
- [x] `chezmoi add`
- [ ] `chezmoi apply`
- [ ] `chezmoi re-add`
- [ ] `chezmoi forget`
- [ ] `chezmoi destroy`
- ...

### Chezmoi features

- [ ] autopush option switch
- [ ] autcommit option switch
- [x] support for regular files
- [ ] support for chezmoi templates

### Development overhead

- [x] Setup development environment
  - [x] Develop in rootless container which includes the chezmoi command
  - [x] Create vscode workspace with integrated `textual-dev` tooling
  - [x] Test relevant vscode extensions
  - [x] Setup linting
  - [x] Setup formatting
  - [x] Setup `pre-commit` hooks.
  - [ ] Setup pytest
  - [ ] Setup profiling
  - [ ] Packaging
    - [x] Manage project venvs with `uv`
  - [ ] Release pipeline
    - [x] Implement basic `pytest` testing
    - [ ] Coverage


## General goals

- leverage `textual` features for concise and rich visualizations
- made for existing chezmoi users
- only support interactive operations
- rich visualization of state
- improve understanding of chezmoi by using the TUI
- make subprocess calls as safe as possible
- "loading" screen for initial app startup and pre-flight checks
- operate screen to operate chezmoi
