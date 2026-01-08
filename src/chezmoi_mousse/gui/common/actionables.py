from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Label, Link, Switch

from chezmoi_mousse import (
    IDS,
    AppType,
    FlatBtn,
    LinkBtn,
    OpBtnEnum,
    OpBtnLabels,
    ScreenName,
    Switches,
    TabBtn,
    TabName,
    Tcss,
)

from .messages import CloseButtonMsg, OperateButtonMsg

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, Switches


__all__ = [
    "CloseButton",
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "LogsTabButtons",
    "OpButton",
    "OperateButtons",
    "SwitchWithLabel",
    "SwitchSlider",
    "TreeTabButtons",
    "ViewTabButtons",
]


class CloseButton(Button, AppType):
    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(
            id=ids.close, classes=Tcss.operate_button, label=OpBtnLabels.cancel
        )
        self.ids = ids

    def on_mount(self) -> None:
        self.display = False
        if self.ids.close == IDS.init.close:
            self.label = OpBtnLabels.exit_app
            self.display = True

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_pressed(self, event: Button.Pressed) -> None:
        if not isinstance(event.button, CloseButton):
            raise TypeError("event.button is not a CloseButton")
        event.stop()  # We post our own message.
        if event.button.label == OpBtnLabels.exit_app:
            self.app.exit()
            return
        self.post_message(CloseButtonMsg(button=event.button, ids=self.ids))


class FlatButton(Button):
    def __init__(self, *, ids: "AppIds", btn_enum: FlatBtn) -> None:
        self.ids = ids
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=self.ids.flat_button_id(btn=btn_enum),
            label=btn_enum,
            variant="primary",
        )


class FlatLink(Link):
    def __init__(self, *, ids: "AppIds", link_enum: LinkBtn) -> None:
        self.ids = ids

        super().__init__(
            id=self.ids.link_button_id(btn=link_enum),
            text=link_enum.link_text,
            url=link_enum.link_url,
        )
        self.link_enum = link_enum

    def on_mount(self) -> None:
        if self.link_enum == LinkBtn.chezmoi_guess:
            self.add_class(Tcss.guess_link)


class FlatButtonsVertical(Vertical):

    def __init__(self, *, ids: "AppIds", buttons: tuple[FlatBtn, ...]) -> None:
        self.buttons: tuple[FlatBtn, ...] = buttons
        self.ids = ids
        super().__init__(
            id=self.ids.container.left_side, classes=Tcss.tab_left_vertical
        )

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            yield FlatButton(ids=self.ids, btn_enum=btn_enum)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatButton.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatButton.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class OpButton(Button, AppType):

    def __init__(self, *, btn_id: str, btn_enum: OpBtnEnum) -> None:
        super().__init__(classes=Tcss.operate_button, id=btn_id, label=btn_enum.label)
        self.btn_enum = btn_enum


class OperateButtons(HorizontalGroup):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.container.operate_buttons, classes=Tcss.operate_button_group
        )

    def compose(self) -> ComposeResult:
        if self.ids.canvas_name == TabName.add:
            yield OpButton(btn_id=self.ids.op_btn.add, btn_enum=OpBtnEnum.add)

        if self.ids.canvas_name == TabName.apply:
            yield OpButton(btn_id=self.ids.op_btn.apply, btn_enum=OpBtnEnum.apply)
        if self.ids.canvas_name == TabName.re_add:
            yield OpButton(btn_id=self.ids.op_btn.re_add, btn_enum=OpBtnEnum.re_add)
        if self.ids.canvas_name in (TabName.apply, TabName.re_add):
            yield OpButton(btn_id=self.ids.op_btn.forget, btn_enum=OpBtnEnum.forget)
            yield OpButton(btn_id=self.ids.op_btn.destroy, btn_enum=OpBtnEnum.destroy)
        if self.ids.canvas_name == ScreenName.init:
            yield OpButton(btn_id=self.ids.op_btn.init, btn_enum=OpBtnEnum.init)
        yield CloseButton(ids=self.ids)

    @on(OpButton.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: OpButton.Pressed) -> None:
        event.stop()  # We post our own message.
        if not isinstance(event.button, OpButton):
            raise TypeError("event.button is not an OpButton")
        pressed_label = str(event.button.label)
        self.post_message(
            OperateButtonMsg(
                button=event.button, ids=self.ids, pressed_label=pressed_label
            )
        )

        if event.button.label == OpBtnLabels.init_review:
            event.button.label = OpBtnLabels.init_run

        elif event.button.label == OpBtnLabels.add_review:
            event.button.label = OpBtnLabels.add_run

        elif event.button.label == OpBtnLabels.apply_review:
            self.query_one(self.ids.op_btn.forget_q).display = False
            self.query_one(self.ids.op_btn.destroy_q).display = False
            event.button.label = OpBtnLabels.apply_run

        elif event.button.label == OpBtnLabels.destroy_review:
            self.query_one(self.ids.op_btn.forget_q).display = False
            if self.ids.canvas_name == TabName.apply:
                self.query_one(self.ids.op_btn.apply_q).display = False
            elif self.ids.canvas_name == TabName.re_add:
                self.query_one(self.ids.op_btn.re_add_q).display = False
            event.button.label = OpBtnLabels.destroy_run

        elif event.button.label == OpBtnLabels.forget_review:
            self.query_one(self.ids.op_btn.destroy_q).display = False
            if self.ids.canvas_name == TabName.apply:
                self.query_one(self.ids.op_btn.apply_q).display = False
            elif self.ids.canvas_name == TabName.re_add:
                self.query_one(self.ids.op_btn.re_add_q).display = False
            event.button.label = OpBtnLabels.forget_run

        elif event.button.label == OpBtnLabels.re_add_review:
            self.query_one(self.ids.op_btn.forget_q).display = False
            self.query_one(self.ids.op_btn.destroy_q).display = False
            event.button.label = OpBtnLabels.re_add_run


class SwitchWithLabel(HorizontalGroup):

    def __init__(self, *, ids: "AppIds", switch_enum: "Switches") -> None:
        self.ids = ids
        self.switch_enum = switch_enum
        super().__init__(id=self.ids.switch_horizontal_id(switch=self.switch_enum))

    def compose(self) -> ComposeResult:
        yield Switch(id=self.ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class SwitchSlider(VerticalGroup):
    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.switch_slider)
        if self.ids.canvas_name in (TabName.apply, TabName.re_add):
            self.switches = (Switches.unchanged, Switches.expand_all)
        else:  # for the AddTab
            self.switches = (Switches.unmanaged_dirs, Switches.unwanted)

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            yield SwitchWithLabel(ids=self.ids, switch_enum=switch_enum)

    def on_mount(self) -> None:
        self.query(HorizontalGroup).last().styles.padding = 0


class TabButtonsBase(Horizontal):
    def __init__(
        self, *, ids: "AppIds", buttons: tuple[TabBtn, ...], container_id: str
    ):
        super().__init__(id=container_id)
        self.ids = ids
        self.buttons = buttons

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield Button(
                    label=btn_enum,
                    id=self.ids.tab_button_id(btn=btn_enum),
                    classes=Tcss.tab_button,
                )

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_tab_btn)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)


class LogsTabButtons(TabButtonsBase, AppType):
    def __init__(self, *, ids: "AppIds"):
        self.ids = ids
        self.tab_buttons = (
            TabBtn.app_log,
            TabBtn.read_log,
            TabBtn.operate_log,
            TabBtn.git_log_global,
        )
        super().__init__(
            ids=self.ids,
            buttons=self.tab_buttons,
            container_id=self.ids.switcher.logs_tab_buttons,
        )


class TreeTabButtons(TabButtonsBase):
    def __init__(self, *, ids: "AppIds"):
        self.ids = ids
        self.tree_tab_buttons = (TabBtn.tree, TabBtn.list)
        super().__init__(
            ids=self.ids,
            buttons=self.tree_tab_buttons,
            container_id=self.ids.switcher.tree_buttons,
        )


class ViewTabButtons(TabButtonsBase):
    def __init__(self, *, ids: "AppIds"):
        self.ids = ids
        self.view_tab_buttons = (TabBtn.diff, TabBtn.contents, TabBtn.git_log_path)
        super().__init__(
            ids=self.ids,
            buttons=self.view_tab_buttons,
            container_id=self.ids.switcher.view_buttons,
        )
