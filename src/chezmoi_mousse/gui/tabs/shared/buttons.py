from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Link

from chezmoi_mousse import (
    ContainerName,
    FlatBtn,
    LinkBtn,
    OperateBtn,
    TabBtn,
    Tcss,
)

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds


__all__ = [
    "FlatButton",
    "FlatLink",
    "FlatButtonsVertical",
    "OperateButtons",
    "TabBtnHorizontal",
]


class FlatButton(Button):
    def __init__(self, *, ids: "CanvasIds", button_enum: FlatBtn) -> None:
        self.ids = ids
        super().__init__(
            classes=Tcss.flat_button.name,
            flat=True,
            id=self.ids.button_id(btn=button_enum),
            label=button_enum.value,
            variant="primary",
        )


class FlatLink(Link):
    def __init__(self, *, ids: "CanvasIds", link_enum: LinkBtn) -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.button_id(btn=link_enum),
            text=link_enum.link_text,
            url=link_enum.link_url,
            classes=Tcss.flat_link.name,
        )


class OperateButton(Button):
    def __init__(self, *, ids: "CanvasIds", button_enum: OperateBtn) -> None:
        self.ids = ids
        self.button_enum = button_enum
        super().__init__(
            classes=Tcss.operate_button.name,
            disabled=True,
            id=self.ids.button_id(btn=self.button_enum),
            label=self.button_enum.label(),
            tooltip=self.button_enum.initial_tooltip,
        )


class OperateButtonVertical(Vertical):

    def __init__(self, *, ids: "CanvasIds", button_enum: OperateBtn) -> None:
        self.ids = ids
        self.button_enum = button_enum
        super().__init__(classes=Tcss.single_button_vertical.name)

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=self.button_enum)


class FlatButtonsVertical(VerticalGroup):

    def __init__(
        self, *, ids: "CanvasIds", buttons: tuple[FlatBtn, ...]
    ) -> None:
        self.buttons: tuple[FlatBtn, ...] = buttons
        self.ids: "CanvasIds" = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield FlatButton(ids=self.ids, button_enum=button_enum)


class OperateButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", buttons: tuple[OperateBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(
            id=self.ids.container_id(name=ContainerName.operate_btn_group)
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield OperateButtonVertical(ids=self.ids, button_enum=button_enum)


class TabBtnHorizontal(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", buttons: tuple[TabBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(
            id=self.ids.container_id(name=ContainerName.switcher_btn_group)
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.ids.button_id(btn=button_enum),
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
