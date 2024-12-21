# interface layout

## Page 1: visualize current state

Visualisation including with buttons to launch related git and chezmoi commands.
- Main visualization and modus operandi
- Ability to verify one specific file its status
- Local repo (staging and diffs for anything not staged or committed yet)
- diffs? otherwise modal embedded decide to show Separate Diff window

## Page 2: Status, or "detected configuration"

The goal is to align with the user, on what the TUI will help operating on.
Similar to a dashboard that uncludes colors to indicate individual component status.

**Locally found executables**

- Chezmoi executable path and version
- Git executable path and version
- Shell executable path and version, for example bash, zhs or fish. (Relevant for the subprocess calls, require minimum versions and shell type, that passed all testing)
- check if remotes dns gets resolved and replies to a ping

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

**TUI options**
- pretty print TUI options, stored in a toml file, like if editing is enabled, spawned from the TUI

## Page 3: Options

Can be edited directly in the toml file where the options are stored, so reread config on every operation, which is peanuts anyway.

Text characters choices:
  O Pure ascii
  O Extended assci
  O Pretty unicode

Tooltips
  O show
  O don't show
  ( option to disable as they will be quite verbose to quickly get going but should be self-explanatory)

Editing
  O disable spawning editor and as such edit outside of the TUI's awareness
    if set, this would alert the user of the refresh button on the "status" page 2.
  O enable spawning and editor based on what EDITOR contains, just like chezmoi offers on the cli

Git
  O enable periodic fetch without pulling to keep the git repository status visuals up to date
  O disable and fetch and/or pull manually

Theme
  O textual theme 1
  O textual theme 2
  O textual theme 3
  etc.

## Page 4: History and logs

- git log
- app usage log with additional info seen by git
- chezmoi logs

## Page 5: Help

- help page, maybe populated with info from the tooltips
- help with in regards to missing characters or font issues
