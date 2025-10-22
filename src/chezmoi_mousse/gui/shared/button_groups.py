from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button

from chezmoi_mousse import AreaName, NavBtn, OperateBtn, TabBtn, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


__all__ = ["NavButtonsVertical", "OperateBtnHorizontal", "TabBtnHorizontal"]


class ButtonsHorizontalBase(HorizontalGroup):

    def __init__(
        self,
        *,
        ids: "CanvasIds",
        buttons: tuple[TabBtn, ...] | tuple[OperateBtn, ...],
        area: AreaName,
    ) -> None:
        self.buttons = buttons
        self.area: AreaName = area
        self.ids: "CanvasIds" = ids
        super().__init__(id=self.ids.buttons_horizontal_id(area=self.area))

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.ids.button_id(btn=button_enum),
                )


class NavButtonsVertical(VerticalGroup):

    def __init__(
        self, *, ids: "CanvasIds", buttons: tuple[NavBtn, ...]
    ) -> None:
        self.buttons: tuple[NavBtn, ...] = buttons
        self.ids: "CanvasIds" = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield Button(
                label=button_enum.value,
                variant="primary",
                flat=True,
                classes=Tcss.nav_button.name,
                id=self.ids.button_id(btn=button_enum),
            )


class OperateBtnHorizontal(ButtonsHorizontalBase):
    def __init__(self, *, ids: "CanvasIds", buttons: tuple[OperateBtn, ...]):
        super().__init__(ids=ids, buttons=buttons, area=AreaName.bottom)

    def on_mount(self) -> None:
        for btn in self.query(Button):
            btn.add_class(Tcss.operate_button.name)


class TabBtnHorizontal(ButtonsHorizontalBase):
    def __init__(
        self, *, ids: "CanvasIds", buttons: tuple[TabBtn, ...], area: AreaName
    ):
        super().__init__(ids=ids, buttons=buttons, area=area)

    def on_mount(self) -> None:
        buttons = self.query(Button)
        for btn in buttons:
            btn.add_class(Tcss.tab_button.name)
        buttons[0].add_class(Tcss.last_clicked.name)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked.name)
        event.button.add_class(Tcss.last_clicked.name)
