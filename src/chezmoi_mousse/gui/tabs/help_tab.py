from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
)
from textual.widgets import Button, ContentSwitcher, Label, Static

from chezmoi_mousse import IDS, FlatBtn, LinkBtn, OpBtnLabels, Switches, Tcss
from chezmoi_mousse.shared import FlatButtonsVertical, FlatLink

__all__ = ["HelpTab"]

# provisional diagrams until dynamically created
FLOW_DIAGRAM = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │                   │                   │                   │
       │     Add Tab       │    autoCommit     │     git push      │
       │   Re-Add Tab      │──────────────────>│──────────────────>│
       │──────────────────>│                   │                   │
       │                   │                autopush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
       │     Apply Tab     │     chezmoi init & chezmoi git pull   │
       │<──────────────────│<──────────────────────────────────────│
       │                   │                   │                   │
       │     Diff View     │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │                   │
       │                   │                   │                   │
       │                   │    chezmoi init & chezmoi git pull    │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │        chezmoi init --one-shot & chezmoi init --apply     │
       │<──────────────────────────────────────────────────────────│
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────────────────┴───────┐    ┌──────┴───────┐
│ destination  │    │    target state / source state   │    │  git remote  │
└──────────────┘    └──────────────────────────────────┘    └──────────────┘
"""


class HelpStrings(StrEnum):
    chezmoi_diagram = "Chezmoi Diagram"
    available_filters = "Available Filters"
    available_buttons = "Available Buttons"
    # Add tab
    add_tab_help = "Add Tab Help"
    unmanaged_dirs_filter = f"{Switches.unmanaged_dirs.label} Filter"
    unwanted_filter = f"{Switches.unwanted.label} Filter"
    # Apply tab
    apply_tab_help = "Apply Tab Help"
    apply_dir_button = f"{OpBtnLabels.apply_review} Button"
    apply_file_button = f"{OpBtnLabels.apply_run} Button"
    # Re-Add tab
    re_add_tab_help = "Re-Add Tab Help"
    re_add_dir_button = f"{OpBtnLabels.re_add_review} Button"
    re_add_file_button = f"{OpBtnLabels.re_add_run} Button"
    # Common filters for Apply and Re-Add tabs
    expand_all_filter = f"{Switches.expand_all.label} Filter"
    unchanged_filter = f"{Switches.unchanged.label} Filter"


class SharedBtnHelp(VerticalGroup):

    def compose(self) -> ComposeResult:
        yield FlatLink(ids=IDS.help, link_enum=LinkBtn.chezmoi_forget)
        yield Label(
            HelpStrings.available_buttons, classes=Tcss.sub_section_label
        )
        yield FlatLink(ids=IDS.help, link_enum=LinkBtn.chezmoi_destroy)
        yield Label(
            HelpStrings.available_buttons, classes=Tcss.sub_section_label
        )


class SharedFiltersHelp(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Label(
            HelpStrings.available_filters, classes=Tcss.flat_section_label
        )
        yield Label(
            HelpStrings.unchanged_filter, classes=Tcss.sub_section_label
        )
        yield Static(Switches.unchanged.enabled_tooltip)
        yield Label(
            HelpStrings.expand_all_filter, classes=Tcss.sub_section_label
        )
        yield Static(Switches.expand_all.enabled_tooltip)


class ApplyTabHelp(Vertical):
    def __init__(self) -> None:
        super().__init__(id=IDS.help.view.apply_help)

    def compose(self) -> ComposeResult:
        yield Label(
            HelpStrings.apply_tab_help, classes=Tcss.main_section_label
        )
        with ScrollableContainer():
            yield SharedFiltersHelp()
            yield FlatLink(ids=IDS.help, link_enum=LinkBtn.chezmoi_apply)
            yield Label(
                HelpStrings.available_buttons, classes=Tcss.sub_section_label
            )
            yield Static(HelpStrings.apply_file_button)
            yield Static(HelpStrings.apply_dir_button)
            yield SharedBtnHelp()


class ReAddTabHelp(Vertical):

    def __init__(self) -> None:
        super().__init__(id=IDS.help.view.re_add_help)

    def compose(self) -> ComposeResult:
        yield Label(
            HelpStrings.re_add_tab_help, classes=Tcss.main_section_label
        )
        with ScrollableContainer():
            yield SharedFiltersHelp()
            yield FlatLink(ids=IDS.help, link_enum=LinkBtn.chezmoi_re_add)
            yield Label(
                HelpStrings.available_buttons, classes=Tcss.sub_section_label
            )
            yield Static(HelpStrings.re_add_file_button)
            yield Static(HelpStrings.re_add_dir_button)
            yield SharedBtnHelp()


class AddTabHelp(Vertical):

    def __init__(self) -> None:
        super().__init__(id=IDS.help.view.add_help)

    def compose(self) -> ComposeResult:
        yield Label(HelpStrings.add_tab_help, classes=Tcss.main_section_label)

        with ScrollableContainer():
            yield Label(
                HelpStrings.available_filters, classes=Tcss.flat_section_label
            )
            yield Label(
                HelpStrings.unmanaged_dirs_filter,
                classes=Tcss.sub_section_label,
            )
            yield Static(Switches.unmanaged_dirs.enabled_tooltip)
            yield Label(
                HelpStrings.unwanted_filter, classes=Tcss.sub_section_label
            )
            yield Static(Switches.unwanted.enabled_tooltip)
            yield FlatLink(ids=IDS.help, link_enum=LinkBtn.chezmoi_add)
            yield Label(
                HelpStrings.available_buttons, classes=Tcss.sub_section_label
            )


class ChezmoiDiagram(Vertical):

    def __init__(self) -> None:
        super().__init__(id=IDS.help.view.diagram)

    def compose(self) -> ComposeResult:
        yield Label(
            HelpStrings.chezmoi_diagram, classes=Tcss.main_section_label
        )
        yield ScrollableContainer(
            Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram)
        )


class HelpTab(Horizontal):

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            ids=IDS.help,
            buttons=(
                FlatBtn.apply_help,
                FlatBtn.re_add_help,
                FlatBtn.add_help,
                FlatBtn.diagram,
            ),
        )
        with ContentSwitcher(
            id=IDS.help.switcher.help_tab, initial=IDS.help.view.apply_help
        ):
            yield ApplyTabHelp()
            yield ReAddTabHelp()
            yield AddTabHelp()
            yield ChezmoiDiagram()

    def on_mount(self) -> None:
        self.switcher = self.query_one(
            IDS.help.switcher.help_tab_q, ContentSwitcher
        )

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == IDS.help.flat_btn.apply_help:
            self.switcher.current = IDS.help.view.apply_help
        elif event.button.id == IDS.help.flat_btn.re_add_help:
            self.switcher.current = IDS.help.view.re_add_help
        elif event.button.id == IDS.help.flat_btn.add_help:
            self.switcher.current = IDS.help.view.add_help
        elif event.button.id == IDS.help.flat_btn.diagram:
            self.switcher.current = IDS.help.view.diagram
