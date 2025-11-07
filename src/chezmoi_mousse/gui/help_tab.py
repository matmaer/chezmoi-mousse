from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher, Static

from chezmoi_mousse import ContainerName, FlatBtn, Tcss, ViewName

from .shared.buttons import NavButtonsVertical
from .shared.section_headers import SectionLabel
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["HelpTab"]


class Strings(StrEnum):
    add_help = "Add Tab Help"
    apply_help = "Apply Tab Help"
    chezmoi_diagram = "chezmoi diagram"
    re_add_help = "Re-Add Tab Help"

    @property
    def placeholder(self) -> str:
        return f"{self.value} will go here."


class ApplyTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        return super().__init__(
            id=self.ids.view_id(view=ViewName.apply_help_view)
        )

    def compose(self) -> ComposeResult:
        yield SectionLabel(Strings.apply_help)
        yield Static(Strings.apply_help.placeholder)


class ReAddTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        return super().__init__(
            id=self.ids.view_id(view=ViewName.re_add_help_view)
        )

    def compose(self) -> ComposeResult:
        yield SectionLabel(Strings.re_add_help)
        yield Static(Strings.re_add_help.placeholder)


class AddTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        return super().__init__(
            id=self.ids.view_id(view=ViewName.add_help_view)
        )

    def compose(self) -> ComposeResult:
        yield SectionLabel(Strings.add_help)
        yield Static(Strings.add_help.placeholder)


class HelpTabSwitcher(ContentSwitcher):

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

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.content_switcher_id(name=ContainerName.help_switcher),
            initial=self.ids.view_id(view=ViewName.apply_help_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:

        yield ApplyTabHelp(ids=self.ids)
        yield ReAddTabHelp(ids=self.ids)
        yield AddTabHelp(ids=self.ids)
        yield Vertical(
            SectionLabel(Strings.chezmoi_diagram),
            Static(self.FLOW_DIAGRAM, classes=Tcss.flow_diagram.name),
            id=self.ids.view_id(view=ViewName.diagram_view),
        )


class HelpTab(TabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

        # Content Switcher IDs
        self.content_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.help_switcher
        )
        self.content_switcher_qid = self.ids.content_switcher_id(
            "#", name=ContainerName.help_switcher
        )
        # View IDs
        self.apply_help_view_id = self.ids.view_id(
            view=ViewName.apply_help_view
        )
        self.re_add_help_view_id = self.ids.view_id(
            view=ViewName.re_add_help_view
        )
        self.add_help_view_id = self.ids.view_id(view=ViewName.add_help_view)
        self.diagram_view_id = self.ids.view_id(view=ViewName.diagram_view)
        # Button IDs
        self.apply_help_btn_id = self.ids.button_id(btn=FlatBtn.apply_help)
        self.re_add_help_btn_id = self.ids.button_id(btn=FlatBtn.re_add_help)
        self.add_help_btn_id = self.ids.button_id(btn=FlatBtn.add_help)
        self.diagram_btn_id = self.ids.button_id(btn=FlatBtn.diagram)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(name=ContainerName.left_side),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield NavButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.apply_help,
                    FlatBtn.re_add_help,
                    FlatBtn.add_help,
                    FlatBtn.diagram,
                ),
            )
        yield HelpTabSwitcher(ids=self.ids)

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(self.content_switcher_qid, HelpTabSwitcher)
        if event.button.id == self.apply_help_btn_id:
            switcher.current = self.apply_help_view_id
        elif event.button.id == self.re_add_help_btn_id:
            switcher.current = self.re_add_help_view_id
        elif event.button.id == self.add_help_btn_id:
            switcher.current = self.add_help_view_id
        elif event.button.id == self.diagram_btn_id:
            switcher.current = self.diagram_view_id
