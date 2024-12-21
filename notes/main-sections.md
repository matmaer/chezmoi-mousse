# interface layout

## Page 1: visualize current state

Visualisation including with buttons to launch related git and chezmoi commands.
- Main visualization and modus operandi
- Ability to verify one specific file its status
- Local repo (staging and diffs for anything not staged or committed yet)
- diffs? otherwise modal embedded decide to show Separate Diff window

## Page 2: Status, or "detected configuration"

The goal is to align with the user, on what the TUI will help operating on

**Locally found executables**

- Chezmoi executable path and version
- Git executable path and version
- Shell executable path and version, for example bash, zhs or fish. (Relevant for the subprocess calls, require minimum versions and shell type, that passed all testing)

**Chezmoi Config**
- EDITOR value because spawning with subprocess
- display relevant environment variables
- display chezmoi.toml and the contents
- display active templates
- display a list of managed files
- highlight any active automation for add/commit/push etc

**Git**
- short symbol based git status like you can have in a prompt
- display git config output
- local user level .ssh/config to push/pull from the remote
- local repo path and it's status
- configured remotes for the local chezmoi repo
- display some basic stats from git logs

## Page 3: Options

Text characters choices:
  O Pure ascii
  O Extended assci
  O Pretty unicode

Tooltips
  O show
  O don't show

## Page 4: History and logs

- git log and relevant journal entries

## Page 5: Help

- help page, maybe populated with info from the tooltips
- help with in regards to missing characters or font issues
