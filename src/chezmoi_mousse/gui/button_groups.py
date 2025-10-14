from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button

from chezmoi_mousse import (
    AreaName,
    CanvasIds,
    NavBtn,
    OperateBtn,
    TabBtn,
    Tcss,
)

__all__ = ["NavButtonsVertical", "OperateBtnHorizontal", "TabBtnHorizontal"]


class ButtonsHorizontalBase(HorizontalGroup):

    def __init__(
        self,
        *,
        canvas_ids: CanvasIds,
        buttons: tuple[TabBtn, ...] | tuple[OperateBtn, ...],
        area: AreaName,
    ) -> None:
        self.buttons = buttons
        self.area: AreaName = area
        self.canvas_ids: CanvasIds = canvas_ids
        super().__init__(id=self.canvas_ids.buttons_horizontal_id(self.area))

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.canvas_ids.button_id(btn=button_enum),
                )


class NavButtonsVertical(VerticalGroup):

    def __init__(
        self, *, canvas_ids: CanvasIds, buttons: tuple[NavBtn, ...]
    ) -> None:
        self.buttons: tuple[NavBtn, ...] = buttons
        self.canvas_ids: CanvasIds = canvas_ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield Button(
                label=button_enum.value,
                variant="primary",
                flat=True,
                classes=Tcss.nav_button.name,
                id=self.canvas_ids.button_id(btn=button_enum),
            )


class OperateBtnHorizontal(ButtonsHorizontalBase):
    def __init__(
        self, *, canvas_ids: CanvasIds, buttons: tuple[OperateBtn, ...]
    ):
        super().__init__(
            canvas_ids=canvas_ids, buttons=buttons, area=AreaName.bottom
        )

    def on_mount(self) -> None:
        for btn in self.query(Button):
            btn.add_class(Tcss.operate_button.name)
        for btn in self.query(Button):
            btn.disabled = True


class TabBtnHorizontal(ButtonsHorizontalBase):
    def __init__(
        self,
        *,
        canvas_ids: CanvasIds,
        buttons: tuple[TabBtn, ...],
        area: AreaName,
    ):
        super().__init__(canvas_ids=canvas_ids, buttons=buttons, area=area)

    def on_mount(self) -> None:
        self.query(Button).add_class(Tcss.tab_button.name)
        self.query_one(
            self.canvas_ids.button_id("#", btn=self.buttons[0])
        ).add_class(Tcss.last_clicked.name)
