from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical
from textual.widgets import Button, Label, Link, Switch

from chezmoi_mousse import (
    AppType,
    FlatBtn,
    LinkBtn,
    OpBtnEnum,
    ScreenName,
    TabBtn,
    TabName,
    Tcss,
)

from ._messages import OperateButtonMsg

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, Switches


__all__ = [
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "LogsTabButtons",
    "OperateButtons",
    "SwitchWithLabel",
    "TreeTabButtons",
    "ViewTabButtons",
]


class SwitchWithLabel(HorizontalGroup):

    def __init__(self, *, ids: "AppIds", switch_enum: "Switches") -> None:
        self.ids = ids
        self.switch_enum = switch_enum
        super().__init__(
            id=self.ids.switch_horizontal_id(switch=self.switch_enum)
        )

    def compose(self) -> ComposeResult:
        yield Switch(id=self.ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class FlatButton(Button):
    def __init__(self, *, ids: "AppIds", button_enum: FlatBtn) -> None:
        self.ids = ids
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=self.ids.flat_button_id(btn=button_enum),
            label=button_enum,
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
        for button_enum in self.buttons:
            yield FlatButton(ids=self.ids, button_enum=button_enum)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class OperateButton(Button, AppType):

    def __init__(
        self,
        *,
        ids: "AppIds",
        button_label: str,
        button_enum: OpBtnEnum,
        disabled_default: bool,
    ) -> None:
        self.ids = ids
        self.btn_id = self.ids.operate_button_id(btn=button_enum)
        self.btn_qid = self.ids.operate_button_id("#", btn=button_enum)
        self.button_enum = button_enum
        self.disabled_default = disabled_default
        super().__init__(
            classes=Tcss.operate_button,
            disabled=disabled_default,
            id=self.btn_id,
            label=button_label,
        )
        self.button_enum = button_enum

    def on_mount(self) -> None:
        self.display = False

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        operate_button_message = OperateButtonMsg(
            btn_enum=self.button_enum,
            btn_qid=self.btn_qid,
            canvas_name=self.ids.canvas_name,
            label=str(self.label),
            tab_qid=self.ids.tab_qid,
        )
        self.post_message(operate_button_message)


class OperateButtons(HorizontalGroup):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.container.operate_buttons)

    def compose(self) -> ComposeResult:
        if self.ids.canvas_name == TabName.add:
            yield OperateButton(
                button_label=OpBtnEnum.add_file.label,
                button_enum=OpBtnEnum.add_file,
                ids=self.ids,
                disabled_default=True,  # on startup in dest dir
            )
            yield OperateButton(
                button_label=OpBtnEnum.add_dir.label,
                button_enum=OpBtnEnum.add_dir,
                ids=self.ids,
                disabled_default=True,  # on startup in dest dir
            )

        if self.ids.canvas_name == TabName.apply:
            yield OperateButton(
                button_label=OpBtnEnum.apply_path.label,
                button_enum=OpBtnEnum.apply_path,
                ids=self.ids,
                disabled_default=True,  # on startup in dest dir
            )
        if self.ids.canvas_name == TabName.re_add:
            yield OperateButton(
                button_label=OpBtnEnum.re_add_path.label,
                button_enum=OpBtnEnum.re_add_path,
                ids=self.ids,
                disabled_default=True,  # on startup in dest dir
            )
        if self.ids.canvas_name in (TabName.apply, TabName.re_add):
            yield OperateButton(
                button_label=OpBtnEnum.forget_path.label,
                button_enum=OpBtnEnum.forget_path,
                ids=self.ids,
                disabled_default=True,  # on startup in dest dir
            )
            yield OperateButton(
                button_label=OpBtnEnum.destroy_path.label,
                button_enum=OpBtnEnum.destroy_path,
                ids=self.ids,
                disabled_default=True,  # on startup in dest dir
            )
        if self.ids.canvas_name == ScreenName.init:
            yield OperateButton(
                button_label=OpBtnEnum.init_new.label,
                button_enum=OpBtnEnum.init_new,
                ids=self.ids,
                disabled_default=False,  # after pushing InitScreen
            )
            yield OperateButton(
                button_label=OpBtnEnum.init_clone.label,
                button_enum=OpBtnEnum.init_clone,
                ids=self.ids,
                disabled_default=True,  # after pushing InitScreen, no repo arg yet
            )
        yield OperateButton(
            button_label=OpBtnEnum.operate_exit.label,
            button_enum=OpBtnEnum.operate_exit,
            ids=self.ids,
            disabled_default=False,  # always enabled when displayed
        )


class TabButtonsBase(Horizontal):
    def __init__(
        self, *, ids: "AppIds", buttons: tuple[TabBtn, ...], container_id: str
    ):
        self.ids = ids
        self.buttons = buttons
        self.container_id = container_id

        super().__init__(id=self.container_id)

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield Button(
                    label=button_enum,
                    id=self.ids.tab_button_id(btn=button_enum),
                    classes=Tcss.tab_button,
                )

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_tab_btn)

    @on(Button.Pressed)
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
        if self.app.dev_mode is True:
            self.tab_buttons += (TabBtn.debug_log,)
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
        self.view_tab_buttons = (
            TabBtn.diff,
            TabBtn.contents,
            TabBtn.git_log_path,
        )
        super().__init__(
            ids=self.ids,
            buttons=self.view_tab_buttons,
            container_id=self.ids.switcher.view_buttons,
        )
