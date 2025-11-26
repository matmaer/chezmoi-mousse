from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Link

from chezmoi_mousse import (
    AppType,
    FlatBtn,
    LinkBtn,
    OperateBtn,
    ScreenName,
    TabBtn,
    Tcss,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds


__all__ = [
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "LogsTabButtons",
    "OperateButtons",
    "TreeTabButtons",
    "ViewTabButtons",
]


class FlatButton(Button):
    def __init__(self, *, ids: "AppIds", button_enum: FlatBtn) -> None:
        self.ids = ids
        super().__init__(
            classes=Tcss.flat_button.name,
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
            classes=Tcss.flat_link.name,
        )


class FlatButtonsVertical(Vertical):

    def __init__(self, *, ids: "AppIds", buttons: tuple[FlatBtn, ...]) -> None:
        self.buttons: tuple[FlatBtn, ...] = buttons
        self.ids = ids
        super().__init__(
            id=self.ids.container.left_side,
            classes=Tcss.tab_left_vertical.name,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield FlatButton(ids=self.ids, button_enum=button_enum)

    def on_mount(self) -> None:
        first_button = self.query_one(
            self.ids.flat_button_id("#", btn=self.buttons[0])
        )
        first_button.add_class(Tcss.last_clicked_flat_btn.name)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_flat_btn.name)
        event.button.add_class(Tcss.last_clicked_flat_btn.name)


class OperateButton(Button):
    def __init__(self, *, ids: "AppIds", button_enum: OperateBtn) -> None:
        self.ids = ids
        self.button_enum = button_enum
        if self.ids.screen_name in (ScreenName.init, ScreenName.operate):
            should_disable = False
        else:
            should_disable = True
        super().__init__(
            classes=Tcss.operate_button.name,
            disabled=should_disable,
            id=self.ids.operate_button_id(btn=self.button_enum),
            label=self.button_enum.initial_label,
            tooltip=self.button_enum.initial_tooltip,
        )


class OperateButtons(Horizontal):
    def __init__(self, *, ids: "AppIds", buttons: tuple[OperateBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(id=self.ids.container.operate_buttons)

    def on_mount(self) -> None:
        for button_enum in self.buttons:
            self.mount(
                Vertical(OperateButton(ids=self.ids, button_enum=button_enum))
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
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum,
                    id=self.ids.tab_button_id(btn=button_enum),
                    classes=Tcss.tab_button.name,
                )

    def on_mount(self) -> None:
        first_button = self.query_one(
            self.ids.tab_button_id("#", btn=self.buttons[0])
        )
        first_button.add_class(Tcss.last_clicked_tab_btn.name)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_tab_btn.name)
        event.button.add_class(Tcss.last_clicked_tab_btn.name)


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
