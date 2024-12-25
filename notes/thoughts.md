# Reflexions to shape the UI

## Principles

Most importantly:

- Chezmoi features for interactive usage are enhanced with visual context. Offer additional assistance for convenience and safety, using Textual and Rich to build the TUI.
- Prevent accidental errors that "update" (overwrite) files in the opposite way of what was wanted. Reasons this could happen:
    - Overlook if edits were made with Chezmoi edit, an external edit by yourself or an application writing a change to their config files.
    - In the local cli, overlooking the cwd
    - Using both git diff and chezmoi diff commands without consistency.
- Prevent data loss with template related user mistakes.
- Prevent data loss by keeping the remote repository up to date.

Also important:

- the TUI only supports interactive usage with Chezmoi and does not apply in any way to scripted usage
- the TUI is aimed at existing users that are familiar Chezmoi approach.
- Aim for real time visualization updates whenever possible instead of leaning on a refresh button.
- Improve visualization based on the chezmoi docs and diagrams, by including the terminology explained in the "concepts" page.

Additional security and safety:

- use Richlog for all output returned by the shell
- use shell=false and check=true for subprocess calls
- operate git with a python module that includes additional safety nets
- always ask for confirmation for write operations, default "no" and rather short timeouts that default to no
- prevent running the TUI as root
- inform the user to first close open editors and save pending changes, if any
- if no remote is detected, advise adding and taking a backup before using the TUI

## MVP stage focus
- include only the "read only" chezmoi commands
- no support for editing files or chezmoi features that change files
- use subprocess and no Python-Go-Python interaction

## Layout

- 3 vertical containers, toggling the left or right sidebars or both
- Sidebar toggling with bindings or mouse
- Left sidebar with buttons
- Right sidebar with RichLog
- Center content with the visualization

Maybe consider adding tabs if scope of the TUI benefits from it.

### Button Sidebar

Buttons could include:

- help button
- config status button (not the git status or Chezmoi status) to check what the TUI sees and affects.
- button to show managed files, maybe in collapsible list and offer additional access to diffs, outside of the diagram visualization
- button to manually refresh the visuals if something was has changed outside of the TUI

### Center Visualisation

Visalization based on the diagrams offered by Chezmoi help.

- supports actions with "inline buttons" that trigger an operation
- status icons based on git status (ahead, behind, dirty etc)
- diagrams with dynamically colored lines and arrows, for example:
    - red for a diff between local files and any other layer
    - orange for a diff between staging and local repo
    - yellow for diff between local repo and remote repo
    - green for no diff anywhere
    - potentially taking other git status into account where diffs are not that useful
- managed files
- keep the format of the diagram in line with the Chezmoi docs

### RichLog Sidebar

- pop open if any output is send to Richlog
- to display anything requested by the user
- avoids displaying info already included in the center visualization

### notes to process

think aubot integrating in tui, considering pre-flight checklist
    R->>H: chezmoi init or apply (--apply) (--one-shot) <dotfiles-repo-url>
    H->>L: chezmoi init

To be included in backend, but probably not the visualization although offer launching?
    W->>W: chezmoi edit (without file) or merge <file>
    W->>H: chezmoi edit (--apply) (--watch) with or without file




┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘

destination         Target state
directory           desired state
                    of dest dir


(target is file
dir or symlink in
destination dir)

destination state:
**current** state of
all targets in
dest dir

                source state:
                declares
                **desired state**
                for home dir
                including templates
                for machine specific
                data.
                **contains only**
                **files and dirs**
                contains **attributes**
                like executable_
                dot_, private_
                                    source directory
                                    stores the source state
                                    ~/.local/share/chezmoi

Target state
**desired** state
of dest dir
**computed** from
 - source state
 - config file
 - destination state

                The working tree is
                the git working tree.
                Normally it is the
                same as the source
                directory, but can
                be a parent of the
                source directory.
                also includes **symbolic**
                links scripts and targets
                to **remove**


The config file contains machine-specific data. By default it is ~/.config/chezmoi/chezmoi.toml.

chezmoi status
space: no change

first column: difference between last state **written by chezmoi**
              A: was created
              M: was modified
              D: was deleted

second column: difference between the actual state and the target state
               effect of running **chezmoi apply**
               A will be created
               M will be modified
               D will be deleted
               R script will be run

#### Read only operations:

**cat**                  Print the target contents of a file, script, or symlink
**cat-config**           Print the configuration file
**data**                 Print the template data
**diff**                Print the diff between the target state and the destination state
**doctor**               Check your system for potential problems
**dump**                 Generate a dump of the target state
    --format json|yaml
**dump-config**          Dump the configuration values
**git**                  Run git in the source directory
**help**                 Print help about a command
**ignored**              Print ignored targets
**license**              Print license
**managed**              List the managed entries in the destination directory
**source-path**          Print the source path of a target
**state dump**
**status**               Show the status of targets
**target-path**          Print the target path of a source path
**unmanaged**            List the unmanaged files in the destination directory
**verify**               Exit with success if the destination state matches the target state, fail otherwise

#### Write operations

add                  Add an existing file, directory, or symlink to the source state
age                  Interact with age
apply                Update the destination directory to match the target state
archive              Generate a tar archive of the target state
cd                   Launch a shell in the source directory
chattr               Change the attributes of a target in the source state
completion           Generate shell completion code
decrypt              Decrypt file or standard input
destroy              Permanently delete an entry from the source state, the destination directory, and the
edit                 Edit the source state of a target
edit-config          Edit the configuration file
edit-config-template Edit the configuration file template
encrypt              Encrypt file or standard input
execute-template     Execute the given template(s)
forget               Remove a target from the source state
generate             Generate a file for use with chezmoi
import               Import an archive into the source state
init                 Setup the source directory and update the destination directory to match the target state
merge                Perform a three-way merge between the destination state, the source state, and the target state
merge-all            Perform a three-way merge for each modified file
purge                Purge chezmoi's configuration and data
re-add               Re-add modified files
secret               Interact with a secret manager
update               Pull and apply any changes
**verify**               Exit with success if the destination state matches the target state, fail otherwise