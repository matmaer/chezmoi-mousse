from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button

from chezmoi_mousse import AreaName, NavBtn, OperateBtn, TabBtn, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


__all__ = ["NavButtonsVertical", "OperateBtnHorizontal", "TabBtnHorizontal"]


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


class OperateBtnHorizontal(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", buttons: tuple[OperateBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(
            id=self.ids.buttons_horizontal_id(area=AreaName.bottom),
            classes=Tcss.operate_button_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.ids.button_id(btn=button_enum),
                    classes=Tcss.operate_button.name,
                )

    def on_mount(self) -> None:
        buttons = self.query(Button)
        for button in buttons:
            if button.id in (
                self.ids.button_id(btn=OperateBtn.add_dir),
                self.ids.button_id(btn=OperateBtn.apply_dir),
                self.ids.button_id(btn=OperateBtn.destroy_dir),
                self.ids.button_id(btn=OperateBtn.destroy_file),
                self.ids.button_id(btn=OperateBtn.forget_file),
                self.ids.button_id(btn=OperateBtn.forget_dir),
                self.ids.button_id(btn=OperateBtn.re_add_dir),
            ):
                button.tooltip = "Not yet implemented."
                button.disabled = True


class TabBtnHorizontal(HorizontalGroup):
    def __init__(
        self, *, ids: "CanvasIds", buttons: tuple[TabBtn, ...], area: AreaName
    ):
        self.ids = ids
        self.buttons = buttons
        self.area = area
        super().__init__(id=self.ids.buttons_horizontal_id(area=self.area))

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
