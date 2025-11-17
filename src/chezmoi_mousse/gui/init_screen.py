from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import Button, ContentSwitcher, Footer, Input

from chezmoi_mousse import (
    AppType,
    ContainerName,
    DataTableName,
    FlatBtn,
    SplashData,
    Tcss,
)
from chezmoi_mousse.shared import (
    CatConfigView,
    DoctorTableView,
    FlatButtonsVertical,
    ReactiveHeader,
    SectionLabel,
    TemplateDataView,
)

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitCloneRepo(Vertical, AppType):

    def __init__(self, *, ids: "CanvasIds") -> None:
        super().__init__(id=ids.views.new_repo)
        self.repo_url: str = ""

    def compose(self) -> ComposeResult:
        yield SectionLabel("Initialize New Chezmoi Repository")
        yield Input(
            placeholder="Enter repository URL",
            validate_on=["submitted"],
            validators=URL(),
        )

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
            self.app.notify(f"Will submit repository URL: {self.repo_url}")


class InitSwitcher(ContentSwitcher):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container_id(name=ContainerName.init_screen_switcher),
            initial=self.ids.views.new_repo,
        )
        self.splash_data = splash_data
        self.doctor_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield InitCloneRepo(ids=self.ids)
        yield DoctorTableView(ids=self.ids)
        yield CatConfigView(ids=self.ids)
        yield TemplateDataView(ids=self.ids)

    def on_mount(self) -> None:
        doctor_view = self.query_one(self.ids.views.doctor_q, DoctorTableView)
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        cat_config = self.query_one(self.ids.views.cat_config_q, CatConfigView)
        cat_config.mount_cat_config_output(self.splash_data.cat_config)
        template_data_view = self.query_one(
            self.ids.views.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.splash_data.template_data
        )


class InitScreen(Screen[None], AppType):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        super().__init__()
        self.ids = ids
        self.tab_vertical_id = ids.tab_vertical_id(
            name=ContainerName.left_side
        )
        self.splash_data = splash_data

    def compose(self) -> ComposeResult:
        yield ReactiveHeader(self.app.init_screen_ids)
        with Horizontal(id=self.ids.canvas_container_id):
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.init_new_repo,
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.template_data,
                ),
            )
            yield InitSwitcher(ids=self.ids, splash_data=self.splash_data)
        yield Footer()

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            self.ids.container_id(
                "#", name=ContainerName.init_screen_switcher
            ),
            ContentSwitcher,
        )
        if event.button.id == self.ids.views.new_repo_btn:
            switcher.current = self.ids.views.new_repo
        elif event.button.id == self.ids.views.doctor_btn:
            switcher.current = self.ids.views.doctor
        elif event.button.id == self.ids.views.cat_config_btn:
            switcher.current = self.ids.views.cat_config
        elif event.button.id == self.ids.views.template_data_btn:
            switcher.current = self.ids.views.template_data
