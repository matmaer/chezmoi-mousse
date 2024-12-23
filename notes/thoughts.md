# Reflexions to shape the UI

## Principles

Most importantly:

- Prevent accidental errors that overwrite in the opposite way of the desired direction. You could forget if the edit was done with Chezmoi edit, an external edit, or a diff resulting from a pull from the remote repo. These diffs are correctly displayed by Chezmoi in different "added" or "removed" lines in the diffs but are prone to be overlooked when not paying attention.
- Your own badly implemented template to manage the differences for your user between machines, can also cause mistakes when looking at the diffs that subsequently are misinterpreted by the user (I have experience).
- This is the only way Chezmoi can implement these popular and advanced features, but some additional assistance is the perfect job for a TUI using Textal features for visualization and live user interaction, while being pretty and intuitive at the same time.

Also important:

- the TUI only supports interactive usage with Chezmoi and does not apply in any way to scripted usage
- the TUI is aimed at existing users that are familiar Chezmoi approach, and just look for additional some convenience. These users are not lazy, but responsible.
- Any chezmoi features for interactive usage are enhanced with visual context.
- Just 3 vertical containers are implemented, toggling the left or right sidebars or both, by the user, if desired.
- Aim for real time visualization updates whenever possible instead of leaning on a refresh button.

Security and safety to protect the user:

- use Richlog for all output returned by the shell
- use shell=false and check=true for subprocess calls
- operate git with a python module that includes additional safety nets
- always ask for confirmation for write operations with a default "no" and rather short timeouts that default to no
- prevent running the TUI as root. Chezmoi is designed to be used in the user's home directory, and by a single person's accounts on different machines.
- inform the user to first close open editors and save pending changes, if any

## MVP stage focus
- use subprocess and not interact with go api from python
- run git operations with a python package as it will probably be easier than subprocess calls anyway
- don't offer editing with dotfiles `chezmoi edit`or an external editor, just the operations after editing a file.
- the MVP requires the user to be an existing Chezmoi user, not cover the initial Chezmoi setup, migrations or similar "non-daily-operation" tasks.
- guide the user to take care of an initial install and config which, as it renders the MVP TUI useless. For example:
    - no chezmoi executable found
    - no existing chezmoi repository is found
    - no chezmoi toml configs found
- limit features as much as possible, at the same time aiming to be bug free, and only add features or any other changes before the working MVP is published publicly.

## Layout

- Left sidebar with buttons for TUI related tasks
    Maybe consider adding tabs if just a few buttons would waste screen estate in a top to bottom sidebar
- Right sidebar with RichLog
- Center content containing the diagrams to offer the visualization, with "inline buttons" to run a task


### Button Sidebar

Buttons on the left, that can be toggled away when operationg from the visualization, or richlog output is more important from the user's judgement in a given scenario.  Buttons could include:
- help button
- config status button (not the git status or Chezmoi status) A kind of pre-flight checklists to keep both the user and the app on the same page, as to what the TUI app will operate on.
- show config files that are diverging from the optional template (check if this can be integrated in the diagram visualization.)
  show diffs before applying the template with Chezmoi init, maybe create two screens or more screens for the Center content
- button to show managed files, maybe in collapsible list and  offer additional access to diffs, outside of the diagram visualization
- button to manually refresh the visuals if something was has changed outside of the TUI

## Center content

Visalization based on the diagrams offered by Chezmoi help.
These are mermaid diagrams converted to text after minor editing so
they can be converted to text with PlantUml

- contains the visualisation diagram
- supports actions with "inline buttons" that trigger an operation
- status icons based on git status, like they can be shown in a prompt,
    to check if existing python modules can help to avoid reinventing the wheel.
- show diffs between areas in RichLog
- diagrams with dynamically colored lines and arrows, for example:
    - red for a diff between local files and any other layer
    - orange for a diff between staging and local repo
    - yellow for diff between local repo and remote repo
    - green for no diff anywhere
    - potentially taking other git status into account where diffs are not that useful
- group files in collapsible if list too long
- clearly highlight the diff what's left and right so it doesn't depend on how the file was edited with "chezmoi edit",
    directly, by a template or changed by local software when using this software or which perspective you are looking from.
- "inline" buttons to launch the operations with borderless buttons, just a different color, bold, underline, italic or a combination.
   buttons with border are three lines high which would cause the diagram to become too large
- keep the format of the diagram in line with the Chezmoi docs as the user probably is already familiar with these, or could be confused when consulting the chezmoi docs in the future.


## Sections:

### RichLog Sidebar

- can be toggled on the right if a visual diff or other chezmoi output is temporarily not needed
- pop open if any output is send to Richlog.
- displays diffs
- displays chezmoi status output, replacing abbreviations with the full word.
    This is ueseful for differences where a text diff is not really applicable, like file mode changes.
- displays the current configuration at startup or when consulted at a later stage
- display staging area status with a focus on what's dirty
- display ahead or behind info between the user's local and remote chezmoi dotfiles repo


**notes to process**

think aubot integrating in tui, considering pre-flight checklist
    R->>H: chezmoi init or apply (--apply) (--one-shot) <dotfiles-repo-url>
    H->>L: chezmoi init

To be included in backend, but probably not the visualization although offer launching?
    W->>W: chezmoi edit (without file) or merge <file>
    W->>H: chezmoi edit (--apply) (--watch) with or without file

