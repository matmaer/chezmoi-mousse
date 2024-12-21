# Reflexions to shape the UI

## Principles

- the tool only supports enhancing interactive usage and does not apply in any to scripted usage
- all chezmoi features for interactive usage are enhanced with context eliminating abbreviations an making it a bit more verbose
- don't offer editing but launch the editor from the shell with $ $EDITOR <file>
- button to manually refresh the visuals if something was edited outside of the TUI
- operate after guiding the user to get started of no existing implementation is found
- the focus is on convenience for an existing user, who does understand how chezmoi works, maybe fend out later if it looks safe
- don't proceed if the user doesn't have the needed executables, repository and/or remote
- the tool is not meant to eliminate any cli experience to purely use chezmoi with a gui
- the goal is convvenience and transparency for existing users by visualizing all aspects
- security:
    - only allow the chezmoi command to be run
    - always ask for confirmation for write operations with a timeouts
    - maybe support some kind of "undo" for low hanging "undo fruit"
    - use subprocess without full shell commands but a list instead
    - short timeouts
    - pre-flight checklists to avoid onboarding users with any chezmoi experience, like the existence of an existing chezmoi repo
    - highlight where to find the subprocess calls in the source code, show and help with transparency to make the user feel comfortable

## Visualization element thoughts

> not complete as properly defined elements are integrated in main-sections.md

- access to diffs between areas, maybe with colored arrows: red for a diff between local files and any other layer, orange for a diff between staging and local repo, yellow for diff between local repo and remote repo
green for no diff anywhere
- group files in collapsible if list too long
- visualising in the diff what's left and what's right
- if diffs: button or another way to apply, add or re-add
- show diffs between templata and local files to run init again and show what the template will change
- make the staging area look a bitt different it's closely related the local repo and cannot be separated as if it's an independent area (although it kind of is, however you cannot push or pull with a dirty work tree)
- visualize not only diffs, but cover all possibilities like Deleted-Added
- urge the user to first close open editors and save pending changes
- let the user decide on edit with or without chezmoi, as it's often a mix anyway, and focus on the desired diffs and add/apply or commit, without accidental errors that overwrite in the opposite way of the desired way.

## Screens:

### Main Visualization

- support for add, apply, re-add, commit, pull (without apply), forget, destroy
- status icons based on git status, like can be shown in a prompt, python scripts exist without a doubt, use dependencies if possible to reduce the time to a first release.
- Local repo (staging and diffs for anything not staged or committed yet)
- diffs? otherwise modal embedded decide to show Separate Diff window

### related guidance streens

make any change interactive with a clear non abbreviated visual status

clearly warning what exactly will happen, as just checking the status with abbreviations is error prone, especially for the target audience who are not looking for automation but visual interaction to help their judgement

**notes to process**

think aubot integrating in tui, considering pre-flight checklist
    R->>H: chezmoi init or apply (--apply) (--one-shot) <dotfiles-repo-url>
    H->>L: chezmoi init

To be included in backend, but probably not the visualization although offer launching?
    W->>W: chezmoi edit (without file) or merge <file>
    W->>H: chezmoi edit (--apply) (--watch) with or without file

- pull, pull and push, if no other action is required in another section to keep things safe when a more verbose interaction is warranted
- staging area status with a focus on dirty or not
