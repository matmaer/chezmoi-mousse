from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Label, Link, Switch

from chezmoi_mousse import (
    CMD,
    AppType,
    BorderTitle,
    FlatBtnLabel,
    LinkBtn,
    OpBtnEnum,
    OpBtnLabel,
    ScreenName,
    SwitchEnum,
    TabLabel,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds


__all__ = [
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "TabButtons",
    "OpButton",
    "OperateButtons",
    "SwitchWithLabel",
    "SwitchSlider",
]


class FlatButton(Button):
    def __init__(self, ids: "AppIds", *, btn_enum: FlatBtnLabel) -> None:
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=ids.flat_button_id(btn=btn_enum),
            label=btn_enum,
            variant="primary",
        )


class FlatLink(Link):
    def __init__(self, link_enum: LinkBtn) -> None:
        super().__init__(text=link_enum.link_text, url=link_enum.link_url)
        self.link_enum = link_enum

    def on_mount(self) -> None:
        if self.link_enum == LinkBtn.chezmoi_guess:
            self.add_class(Tcss.guess_link)


class FlatButtonsVertical(Vertical):

    def __init__(self, ids: "AppIds", *, buttons: tuple[FlatBtnLabel, ...]) -> None:
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.buttons: tuple[FlatBtnLabel, ...] = buttons

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            yield FlatButton(self.ids, btn_enum=btn_enum)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatButton.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatButton.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class OpButton(Button, AppType):

    def __init__(
        self, *, btn_id: str, btn_enum: OpBtnEnum | OpBtnLabel, app_ids: "AppIds"
    ) -> None:
        label = btn_enum.label if isinstance(btn_enum, OpBtnEnum) else btn_enum.value
        super().__init__(classes=Tcss.operate_button, id=btn_id, label=label)
        self.btn_enum: OpBtnEnum | OpBtnLabel = btn_enum
        self.btn_id: str = btn_id
        self.app_ids: AppIds = app_ids
        if label in (
            OpBtnLabel.destroy_review,
            OpBtnLabel.forget_review,
            OpBtnLabel.add_review,
        ):
            self.disabled = True
        elif label in (
            OpBtnLabel.add_run,
            OpBtnLabel.apply_run,
            OpBtnLabel.re_add_run,
            OpBtnLabel.forget_run,
            OpBtnLabel.destroy_run,
            OpBtnLabel.cancel,
            OpBtnLabel.reload,
        ):
            self.display = False


class OperateButtons(HorizontalGroup):
    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.operate_buttons)
        self.ids = ids

    def compose(self) -> ComposeResult:
        for btn_id, btn_enum in self.ids.op_btn_map.items():
            yield OpButton(btn_id=btn_id, btn_enum=btn_enum, app_ids=self.ids)

    def on_mount(self) -> None:
        if (
            self.ids.canvas_name == TabLabel.debug
            or self.ids.canvas_name == ScreenName.init
        ):
            # we never toggle display on these tabs
            return
        self.cancel_btn = self.query_one(self.ids.op_btn.cancel_q, OpButton)
        self.reload_btn = self.query_one(self.ids.op_btn.reload_q, OpButton)
        # disable apply review button if no_status_paths is true
        if self.ids.canvas_name == TabLabel.apply:
            self.query_one(self.ids.op_btn.apply_review_q, OpButton).disabled = bool(
                CMD.cache.no_status_paths
            )
        elif self.ids.canvas_name == TabLabel.re_add:
            self.query_one(self.ids.op_btn.re_add_review_q, OpButton).disabled = bool(
                CMD.cache.no_status_paths
            )
        all_buttons: list[OpButton] = [
            b for b in self.query_children().results() if isinstance(b, OpButton)
        ]
        self.run_buttons = [b for b in all_buttons if b.id in self.ids.run_btn_ids]
        self.review_buttons = [
            b for b in all_buttons if b.id in self.ids.review_btn_ids
        ]

    def set_path_arg(self, path: "Path") -> None:
        for btn_enum in self.ids.op_btn_map.values():
            if isinstance(btn_enum, OpBtnEnum):
                btn_enum.path_arg = path

    @on(OpButton.Pressed)
    def update_operate_button_display(self, event: OpButton.Pressed) -> None:
        if not isinstance(event.button, OpButton):
            # allows for type hinting to work and we only toggle display for OpButton
            return

        if (
            self.ids.canvas_name in (TabLabel.debug, ScreenName.init)
            or event.button.label == OpBtnLabel.refresh_tree
        ):
            # we don't need any display toggling in those contexts for now
            return

        if event.button.id in (self.ids.op_btn.cancel, self.ids.op_btn.reload):
            self.cancel_btn.display = False
            self.reload_btn.display = False
            for btn in self.run_buttons:
                btn.display = False
            for btn in self.review_buttons:
                btn.display = True

        elif event.button.id in self.ids.review_btn_ids:
            self.cancel_btn.display = True
            for btn in self.review_buttons:
                btn.display = False
            for btn in self.run_buttons:
                btn.disabled = False
            run_btn_enum = OpBtnEnum.review_to_run(OpBtnLabel(str(event.button.label)))
            # now lookup the button widget in self.run_buttons with the
            # corresponding enum
            btn_widget: OpButton = next(
                b for b in self.run_buttons if b.btn_enum == run_btn_enum
            )
            btn_widget.display = True

        elif event.button.id in self.ids.run_btn_ids:
            self.cancel_btn.display = False
            self.reload_btn.display = True
            event.button.disabled = True


class SwitchWithLabel(HorizontalGroup):

    def __init__(self, ids: "AppIds", *, switch_enum: "SwitchEnum") -> None:
        super().__init__()
        self.switch_enum = switch_enum
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Switch(id=self.ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class SwitchSlider(VerticalGroup):
    def __init__(self, ids: "AppIds") -> None:
        super().__init__(classes="-visible")
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            self.switches = (SwitchEnum.unchanged, SwitchEnum.expand_all)
        else:  # for the AddTab
            self.switches = (SwitchEnum.unmanaged_dirs, SwitchEnum.unwanted)
        self.ids = ids

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            yield SwitchWithLabel(self.ids, switch_enum=switch_enum)

    def on_mount(self) -> None:
        self.query_children(HorizontalGroup).last().styles.padding = 0


class TabButtons(Horizontal):
    def __init__(self, buttons: tuple[TabLabel, ...]):
        super().__init__()
        self.buttons = buttons

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield Button(label=btn_enum, classes=Tcss.tab_button)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_tab_btn)
        self.border_subtitle = BorderTitle.dest_dir.value

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
        if event.button.label == TabLabel.tree:
            self.border_subtitle = BorderTitle.dest_dir
        elif event.button.label == TabLabel.list:
            self.border_subtitle = BorderTitle.list_tree
