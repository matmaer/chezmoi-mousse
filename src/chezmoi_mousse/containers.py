"""Contains classes used as container components in main_tabs.py.

Rules:
- inherit from textual containers or is a ModalScreen
- are only reused in the main_tabs.py module
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.validation import URL
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Label,
    Pretty,
    Static,
    Switch,
)

from chezmoi_mousse import CM_CFG
from chezmoi_mousse.id_typing import (
    Buttons,
    Filters,
    Id,
    Location,
    TabIds,
    TcssStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.widgets import ExpandedTree, FlatTree, ManagedTree


class FilterSlider(VerticalGroup):

    def __init__(
        self, *, tab_ids: TabIds, filters: tuple[Filters, Filters]
    ) -> None:
        self.filters = filters
        super().__init__(
            id=tab_ids.filter_slider_id, classes=TcssStr.filters_vertical
        )
        self.tab_ids = tab_ids

    def compose(self) -> ComposeResult:
        for filter_enum in self.filters:
            with HorizontalGroup(
                id=self.tab_ids.filter_horizontal_id(
                    filter_enum, Location.top
                ),
                classes=TcssStr.filter_horizontal,
            ):
                yield Switch(
                    id=self.tab_ids.switch_id(filter_enum), value=False
                )
                yield Label(
                    filter_enum.value.label, classes=TcssStr.filter_label
                ).with_tooltip(tooltip=filter_enum.value.tooltip)

    def on_mount(self) -> None:
        # add padding to the top filter horizontal group
        self.query_one(
            self.tab_ids.filter_horizontal_qid(self.filters[0], Location.top),
            HorizontalGroup,
        ).add_class(TcssStr.pad_bottom)


class ButtonsHorizontal(HorizontalGroup):

    def __init__(
        self,
        *,
        tab_ids: TabIds,
        buttons: tuple[Buttons, ...],
        location: Location,
    ) -> None:
        self.buttons = buttons
        self.location: Location = location
        self.tab_ids: TabIds = tab_ids
        super().__init__(
            id=tab_ids.buttons_horizontal_id(self.location),
            classes=TcssStr.tab_buttons_horizontal,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.tab_ids.button_vertical_id(button_enum),
                classes=TcssStr.single_button_vertical,
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.tab_ids.button_id(button_enum),
                )

    def on_mount(self) -> None:
        if self.location == Location.bottom:
            for button_enum in self.buttons:
                button = self.query_one(self.tab_ids.button_qid(button_enum))
                button.add_class(TcssStr.operate_button)
            return

        for button_enum in self.buttons:
            self.query_one(self.tab_ids.button_qid(button_enum)).add_class(
                TcssStr.tab_button
            )
            self.query_one(self.tab_ids.button_qid(self.buttons[0])).add_class(
                TcssStr.last_clicked
            )

    @on(Button.Pressed)
    def update_tab_btn_last_clicked(self, event: Button.Pressed) -> None:
        # tab buttons never on bottom, non-tab buttons, always on bottom
        if self.location == Location.bottom:
            return
        # update last_clicked class
        for button_enum in self.buttons:
            self.query_one(self.tab_ids.button_qid(button_enum)).remove_class(
                TcssStr.last_clicked
            )
        event.button.add_class(TcssStr.last_clicked)


class TreeContentSwitcher(ContentSwitcher):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(Location.left),
            initial=self.tab_ids.tree_id(TreeStr.managed_tree),
        )

    def on_mount(self) -> None:
        self.border_title = str(CM_CFG.destDir)
        self.add_class(TcssStr.content_switcher_left)
        self.add_class(TcssStr.top_border_title)

    def compose(self) -> ComposeResult:
        yield ManagedTree(tab_ids=self.tab_ids)
        yield FlatTree(tab_ids=self.tab_ids)
        yield ExpandedTree(tab_ids=self.tab_ids)


class InitNewRepo(Vertical):
    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        super().__init__(id=self.tab_ids.view_id(ViewStr.init_new_view))

    def compose(self) -> ComposeResult:
        yield Label("Init chezmoi from a remote Git repository")
        yield Input(
            placeholder="Enter repository URL",
            validate_on=["submitted"],
            validators=URL(),
        )
        yield Pretty([])

    @on(Input.Submitted)
    def show_invalid_reasons(self, event: Input.Submitted) -> None:
        # Updating the UI to show the reasons why validation failed
        if (
            event.validation_result is not None
            and not event.validation_result.is_valid
        ):
            self.query_one(Pretty).update(
                event.validation_result.failure_descriptions
            )
        else:
            self.query_one(Pretty).update([])


class InitCloneRepo(Vertical):
    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        super().__init__(id=self.tab_ids.view_id(ViewStr.init_clone_view))

    def compose(self) -> ComposeResult:
        yield Static(f"{self.tab_name} Init clone repo")
        yield ButtonsHorizontal(
            tab_ids=Id.init,
            buttons=(Buttons.clone_repo_btn, Buttons.clear_btn),
            location=Location.bottom,
        )


class InitPurgeRepo(Vertical):
    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        super().__init__(id=self.tab_ids.view_id(ViewStr.init_purge_view))

    def compose(self) -> ComposeResult:
        yield Static(f"{self.tab_name} Init purge repo")
