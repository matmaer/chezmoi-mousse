from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher, Label, Static

from chezmoi_mousse import AreaName, NavBtn, Tcss, ViewName

from .shared.button_groups import NavButtonsVertical
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["HelpTab"]


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
            id=self.ids.content_switcher_id(area=AreaName.right),
            initial=self.ids.view_id(view=ViewName.apply_help_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:

        yield Vertical(
            Label("Apply Tab Help", classes=Tcss.section_label.name),
            Static("Instructions for using the Apply Tab will go here."),
            id=self.ids.view_id(view=ViewName.apply_help_view),
        )
        yield Vertical(
            Label("Re-Add Tab Help", classes=Tcss.section_label.name),
            Static("Instructions for using the Re-Add Tab will go here."),
            id=self.ids.view_id(view=ViewName.re_add_help_view),
        )
        yield Vertical(
            Label("Add Tab Help", classes=Tcss.section_label.name),
            Static("Instructions for using the Add Tab will go here."),
            id=self.ids.view_id(view=ViewName.add_help_view),
        )
        yield Vertical(
            Label("chezmoi diagram", classes=Tcss.section_label.name),
            Static(self.FLOW_DIAGRAM, classes=Tcss.flow_diagram.name),
            id=self.ids.view_id(view=ViewName.diagram_view),
        )


class HelpTab(TabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        yield NavButtonsVertical(
            ids=self.ids,
            buttons=(
                NavBtn.apply_help,
                NavBtn.re_add_help,
                NavBtn.add_help,
                NavBtn.diagram,
            ),
        )
        yield HelpTabSwitcher(ids=self.ids)

    @on(Button.Pressed, Tcss.nav_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(HelpTabSwitcher)
        if event.button.id == self.ids.button_id(btn=NavBtn.apply_help):
            switcher.current = self.ids.view_id(view=ViewName.apply_help_view)
        elif event.button.id == self.ids.button_id(btn=NavBtn.re_add_help):
            switcher.current = self.ids.view_id(view=ViewName.re_add_help_view)
        elif event.button.id == self.ids.button_id(btn=NavBtn.add_help):
            switcher.current = self.ids.view_id(view=ViewName.add_help_view)
        elif event.button.id == self.ids.button_id(btn=NavBtn.diagram):
            switcher.current = self.ids.view_id(view=ViewName.diagram_view)
