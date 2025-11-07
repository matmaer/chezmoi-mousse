from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher, Static

from chezmoi_mousse import (
    ContainerName,
    FlatBtn,
    OperateBtn,
    Switches,
    Tcss,
    ViewName,
)

from .shared.buttons import NavButtonsVertical
from .shared.section_headers import SectionLabel, SectionSubLabel
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["HelpTab"]


class Strings(StrEnum):
    available_buttons = "Available Buttons"
    available_switches = "Available Switches"
    chezmoi_diagram = "chezmoi diagram"


class ButtonsHelp(Vertical):
    def __init__(self, button_info: list[tuple[str, str]]) -> None:
        super().__init__()

        self.button_info = button_info

    def compose(self) -> ComposeResult:
        yield SectionLabel(Strings.available_buttons)
        for label, tooltip in self.button_info:
            yield SectionSubLabel(label)
            yield Static(tooltip)


class SwitchesHelp(Vertical):
    def __init__(self, switches: list[Switches]) -> None:
        super().__init__()

        self.switches = switches

    def compose(self) -> ComposeResult:
        yield SectionLabel(Strings.available_switches)
        for switch in self.switches:
            yield SectionSubLabel(switch.label)
            yield Static(switch.enabled_tooltip)


class ApplyTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__(id=ids.view_id(view=ViewName.apply_help_view))

        self.op_buttons = [
            OperateBtn.apply_path,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ]
        self.op_dir_buttons_info: list[tuple[str, str]] = [
            (op_btn.dir_label, op_btn.dir_tooltip)
            for op_btn in self.op_buttons
        ]
        self.op_file_buttons_info: list[tuple[str, str]] = [
            (op_btn.file_label, op_btn.file_tooltip)
            for op_btn in self.op_buttons
        ]
        self.all_op_buttons_info = (
            self.op_dir_buttons_info + self.op_file_buttons_info
        )
        self.switches = [Switches.expand_all, Switches.unchanged]

    def compose(self) -> ComposeResult:
        yield ButtonsHelp(button_info=self.all_op_buttons_info)
        yield SwitchesHelp(switches=self.switches)


class ReAddTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__(id=ids.view_id(view=ViewName.re_add_help_view))

        self.op_buttons = [
            OperateBtn.re_add_path,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ]
        self.op_dir_buttons_info: list[tuple[str, str]] = [
            (op_btn.dir_label, op_btn.dir_tooltip)
            for op_btn in self.op_buttons
        ]
        self.op_file_buttons_info: list[tuple[str, str]] = [
            (op_btn.file_label, op_btn.file_tooltip)
            for op_btn in self.op_buttons
        ]
        self.all_op_buttons_info = (
            self.op_dir_buttons_info + self.op_file_buttons_info
        )
        self.switches = [Switches.expand_all, Switches.unchanged]

    def compose(self) -> ComposeResult:
        yield ButtonsHelp(button_info=self.all_op_buttons_info)
        yield SwitchesHelp(switches=self.switches)


class AddTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__(id=ids.view_id(view=ViewName.add_help_view))

        self.all_op_buttons_info: list[tuple[str, str]] = [
            (op_btn.initial_label, op_btn.enabled_tooltip)
            for op_btn in (OperateBtn.add_dir, OperateBtn.add_file)
        ]
        self.switches = [Switches.unmanaged_dirs, Switches.unwanted]

    def compose(self) -> ComposeResult:
        yield ButtonsHelp(button_info=self.all_op_buttons_info)
        yield SwitchesHelp(switches=self.switches)


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
