from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Horizontal,
)
from textual.widgets import (
    Label,
    Switch,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.components import LeftSideVertical
from chezmoi_mousse.gui.common.managed_tree import ManagedTree
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Tcss,
)

from .common.actionables import (
    OperateBtnGroup,
    RefreshBtn,
    SwitchSlider,
)

if TYPE_CHECKING:
    from textual.app import ComposeResult

__all__ = ["DangerZoneTab", "ManagedTreeTab"]


class ManagedTreeTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.managed_tree.pane_id, title=BtnLabel.managed_tree)

    def compose(self) -> ComposeResult:
        with Horizontal(), LeftSideVertical(app_ids=store.man_tree_ids):
            yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
            yield ManagedTree(store.man_tree_ids)
            yield RefreshBtn(app_ids=store.man_tree_ids)
        yield OperateBtnGroup(
            app_ids=store.man_tree_ids,
            labels=(
                BtnLabel.chezmoi_add,
                BtnLabel.chezmoi_apply,
                BtnLabel.chezmoi_re_add,
            ),
        )
        yield SwitchSlider(app_ids=store.man_tree_ids)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        managed_tree = self.query_one(store.man_tree_ids.managed_tree_q, ManagedTree)
        if event.switch.id == store.man_tree_ids.switch.show_unchanged:
            managed_tree.show_unchanged = event.value
        elif event.switch.id == store.man_tree_ids.switch.show_unmanaged:
            managed_tree.show_unmanaged = event.value
        elif event.switch.id == store.man_tree_ids.switch.expand_all:
            managed_tree.expand_all = event.value


class DangerZoneTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.danger_zone.pane_id, title=BtnLabel.danger_zone)

    def compose(self) -> ComposeResult:
        with Horizontal(), LeftSideVertical(app_ids=store.danger_zone_ids):
            yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
            yield ManagedTree(store.danger_zone_ids)
            yield RefreshBtn(app_ids=store.danger_zone_ids)
        yield OperateBtnGroup(
            app_ids=store.danger_zone_ids,
            labels=(
                BtnLabel.forget_review,
                BtnLabel.destroy_review,
            ),
        )
        yield SwitchSlider(app_ids=store.danger_zone_ids)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        managed_tree = self.query_one(store.danger_zone_ids.managed_tree_q, ManagedTree)
        if event.switch.id == store.danger_zone_ids.switch.show_unchanged:
            managed_tree.show_unchanged = event.value
        elif event.switch.id == store.danger_zone_ids.switch.show_unmanaged:
            managed_tree.show_unmanaged = event.value
        elif event.switch.id == store.danger_zone_ids.switch.expand_all:
            managed_tree.expand_all = event.value
