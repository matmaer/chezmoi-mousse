from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button

from chezmoi_mousse import ContainerName, FlatBtn, OperateBtn, TabBtn, Tcss

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds


__all__ = [
    "AddOpButtons",
    "AddOpScreenButtons",
    "ApplyOpButtons",
    "ApplyOpScreenButtons",
    "FlatButton",
    "NavButtonsVertical",
    "OperateBtnHorizontal",
    "OperateButton",
    "ReAddOpButtons",
    "ReAddOpScreenButtons",
    "TabBtnHorizontal",
]


class FlatButton(Button):
    def __init__(self, *, ids: "CanvasIds", button_enum: FlatBtn) -> None:
        self.ids = ids
        super().__init__(
            label=button_enum.value,
            variant="primary",
            flat=True,
            classes=Tcss.flat_button.name,
            id=self.ids.button_id(btn=button_enum),
        )


class OperateButton(Vertical):

    def __init__(self, *, ids: "CanvasIds", button_enum: OperateBtn) -> None:
        self.ids = ids
        self.button_enum = button_enum
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(classes=Tcss.single_button_vertical.name):
            yield Button(
                label=self.button_enum.initial_label,
                id=self.ids.button_id(btn=self.button_enum),
                classes=Tcss.operate_button.name,
                disabled=True,
                tooltip=self.button_enum.initial_tooltip,
            )


class NavButtonsVertical(VerticalGroup):

    def __init__(
        self, *, ids: "CanvasIds", buttons: tuple[FlatBtn, ...]
    ) -> None:
        self.buttons: tuple[FlatBtn, ...] = buttons
        self.ids: "CanvasIds" = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield FlatButton(ids=self.ids, button_enum=button_enum)


class OperateBtnHorizontal(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", buttons: tuple[OperateBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield OperateButton(ids=self.ids, button_enum=button_enum)


class ApplyOpButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.apply_path)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.forget_path)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.destroy_path)


class ApplyOpScreenButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", operate_button: OperateBtn):
        self.ids = ids
        self.operate_button = operate_button
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=self.operate_button)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.exit_button)


class ReAddOpButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.re_add_path)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.forget_path)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.destroy_path)


class ReAddOpScreenButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", operate_button: OperateBtn):
        self.ids = ids
        self.operate_button = operate_button
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=self.operate_button)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.exit_button)


class AddOpButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.add_dir)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.add_file)


class AddOpScreenButtons(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", operate_button: OperateBtn):
        self.ids = ids
        self.operate_button = operate_button
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.operate_btn_group),
            classes=Tcss.operate_btn_horizontal.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateButton(ids=self.ids, button_enum=self.operate_button)
        yield OperateButton(ids=self.ids, button_enum=OperateBtn.exit_button)


class TabBtnHorizontal(HorizontalGroup):
    def __init__(self, *, ids: "CanvasIds", buttons: tuple[TabBtn, ...]):
        self.ids = ids
        self.buttons = buttons
        super().__init__(
            id=self.ids.buttons_group_id(name=ContainerName.switcher_btn_group)
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
