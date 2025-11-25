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
    TabBtn,
    TabName,
    Tcss,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds


__all__ = [
    "FlatButton",
    "FlatLink",
    "FlatButtonsVertical",
    "LogsTabButtons",
    "OperateButtons",
    "TabButtons",
]


class FlatButton(Button):
    def __init__(self, *, ids: "AppIds", button_enum: FlatBtn) -> None:
        self.ids = ids
        super().__init__(
            classes=Tcss.flat_button.name,
            flat=True,
            id=self.ids.flat_button_id(btn=button_enum),
            label=button_enum.value,
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


class OperateButton(Button):
    def __init__(self, *, ids: "AppIds", button_enum: OperateBtn) -> None:
        self.ids = ids
        self.button_enum = button_enum
        super().__init__(
            classes=Tcss.operate_button.name,
            disabled=True,
            id=self.ids.operate_button_id(btn=self.button_enum),
            label=self.button_enum.label(),
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
    def __init__(self, *, ids: "AppIds", buttons: tuple[TabBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        if self.ids.tab_name == TabName.logs:
            self.container_ids = self.ids.switcher.logs_tab_buttons
        super().__init__(id=self.ids.switcher.switcher_buttons)

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.ids.tab_button_id(btn=button_enum),
                    classes=Tcss.tab_button.name,
                )

    def on_mount(self) -> None:
        buttons = self.query(Button)
        buttons[0].add_class(Tcss.last_clicked.name)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked.name)
        event.button.add_class(Tcss.last_clicked.name)


class TabButtons(Horizontal):
    def __init__(self, *, ids: "AppIds", buttons: tuple[TabBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(id=self.ids.switcher.switcher_buttons)

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.ids.tab_button_id(btn=button_enum),
                    classes=Tcss.tab_button.name,
                )

    def on_mount(self) -> None:
        buttons = self.query(Button)
        buttons[0].add_class(Tcss.last_clicked.name)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked.name)
        event.button.add_class(Tcss.last_clicked.name)


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
        super().__init__(ids=ids, buttons=self.tab_buttons)
