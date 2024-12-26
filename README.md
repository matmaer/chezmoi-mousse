Terminal user interface for [chezmoi](https://github.com/twpayne/chezmoi), visualizing its operations. Built with [Textual](https://github.com/Textualize/textual), the most complete, most user friendly and no surprise, most popular TUI app development framework.

The name of the repository chezmoi-mousse is a wink to the mouse.  The project is in its very early stages.

## Roadmap

- [x] Create repository, setup initial `uv` dev env with initial `pre-commit` hooks
- [x] Create text based version of the `mermaid` diagrams offered by `chezmoi`.
- [ ] Implement visualization of elements that only require read operations
  - [ ] Show local config for `chezmoi` including `git` config
  - [ ] Show `chezmoi status`, for targets, workspace and local repo
  - [ ] Show `git status`, local versus remote dotfiles repo
  - [ ] Show `chezmoi managed`
  - [ ] Show `chezmoi data`
  - [ ] Show `chezmoi diff` and `git diff`, by choosing on a diagram

- [ ] Setup `pytest`
- [ ] Use `uv` to `build` a package for distribution an a later phase
- [ ] Setup `pytest` and other elements to run locally
- [ ] Setup the complete pipeline including pushing to remote
- [ ] Implement `chezmoi` features that need write operations
- [ ] Setup pipelines for publishing, for example `pypi`.
- [ ] Implement remaining `chezmoi` features when all overheid is automated



