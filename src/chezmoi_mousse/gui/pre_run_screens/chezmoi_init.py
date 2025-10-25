"""Not implemented yet, just recycled code snippets."""

from shared.button_groups import NavButtonsVertical, OperateBtnHorizontal
from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import Button, ContentSwitcher, Input, Label, Select

from chezmoi_mousse import (
    AppType,
    AreaName,
    Canvas,
    CanvasIds,
    ChangeCmd,
    Id,
    NavBtn,
    OperateBtn,
    Tcss,
    ViewName,
)


class InitTabSwitcher(ContentSwitcher):

    def __init__(self, ids: CanvasIds):
        self.ids = ids
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.right),
            initial=self.ids.view_id(view=ViewName.init_new_repo_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:
        # New Repo Content
        yield Vertical(
            Label(
                "Initialize new chezmoi git repository",
                classes=Tcss.section_label.name,
            ),
            Input(placeholder="Enter config file path"),
            OperateBtnHorizontal(
                ids=self.ids, buttons=(OperateBtn.init_new_repo,)
            ),
            id=self.ids.view_id(view=ViewName.init_new_repo_view),
        )
        # Clone Repo Content
        yield Vertical(
            Label(
                "Clone existing chezmoi git repository",
                classes=Tcss.section_label.name,
            ),
            # TODO: add selection for https(with PAT token) or ssh
            HorizontalGroup(
                Vertical(
                    Select[str].from_values(
                        ["https", "ssh"],
                        # classes=Tcss.input_select.name,
                        value="https",
                        allow_blank=False,
                        type_to_search=False,
                    ),
                    # classes=Tcss.input_select_vertical.name,
                ),
                Vertical(
                    Input(
                        placeholder="Enter repository URL",
                        validate_on=["submitted"],
                        validators=URL(),
                        # classes=Tcss.input_field.name,
                    ),
                    # classes=Tcss.input_field_vertical.name,
                ),
            ),
            OperateBtnHorizontal(
                ids=self.ids, buttons=(OperateBtn.clone_chezmoi_repo,)
            ),
            id=self.ids.view_id(view=ViewName.clone_existing_repo_view),
        )


class InitScreen(Screen[None], AppType):

    def __init__(self) -> None:
        self.ids = Id.chezmoi_init
        super().__init__(id=Canvas.chezmoi_init, classes=Tcss.screen_base.name)
        self.repo_url: str | None = None

    def compose(self) -> ComposeResult:
        yield NavButtonsVertical(
            ids=self.ids,
            buttons=(NavBtn.init_new_repo, NavBtn.clone_existing_repo),
        )
        yield InitTabSwitcher(ids=self.ids)

    @on(Input.Submitted)
    def log_invalid_reasons(self, event: Input.Submitted) -> None:
        if (
            event.validation_result is not None
            and not event.validation_result.is_valid
        ):
            text_lines: str = "\n".join(
                event.validation_result.failure_descriptions
            )
            self.app.notify(text_lines, severity="error")
        else:
            self.repo_url = event.value

    @on(Button.Pressed, Tcss.nav_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(InitTabSwitcher)
        if event.button.id == self.ids.button_id(btn=NavBtn.init_new_repo):
            switcher.current = self.ids.view_id(
                view=ViewName.init_new_repo_view
            )
        elif event.button.id == self.ids.button_id(
            btn=NavBtn.clone_existing_repo
        ):
            switcher.current = self.ids.view_id(
                view=ViewName.clone_existing_repo_view
            )

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operation_button(self, event: Button.Pressed) -> None:
        event.stop()
        if (
            event.button.id
            == self.ids.button_id(btn=OperateBtn.clone_chezmoi_repo)
            and self.repo_url is not None
        ):
            self.app.chezmoi.perform(ChangeCmd.init, repo_url=self.repo_url)
            self.query_one(
                self.ids.button_id("#", btn=OperateBtn.clone_chezmoi_repo),
                Button,
            ).disabled = True
        elif event.button.id == self.ids.button_id(
            btn=OperateBtn.init_new_repo
        ):
            self.app.chezmoi.perform(ChangeCmd.init)
            self.query_one(
                self.ids.button_id("#", btn=OperateBtn.init_new_repo), Button
            ).disabled = True
