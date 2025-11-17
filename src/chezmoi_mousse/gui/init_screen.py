import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Input,
    Pretty,
    Static,
)

from chezmoi_mousse import (
    AppType,
    ContainerName,
    DataTableName,
    FlatBtn,
    SplashData,
    Tcss,
    ViewName,
)
from chezmoi_mousse.shared import (
    CatConfigOutput,
    DoctorTableView,
    FlatButtonsVertical,
    ReactiveHeader,
    TemplateDataOutput,
)

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitScreenIds(AppType):
    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids

    @property
    def new_repo_view_id(self) -> str:
        return self.ids.view_id(view=ViewName.init_new_repo_view)

    @property
    def new_repo_view_qid(self) -> str:
        return self.ids.view_id("#", view=ViewName.init_new_repo_view)

    @property
    def new_repo_btn_id(self) -> str:
        return self.ids.button_id(btn=FlatBtn.init_new_repo)

    @property
    def doctor_view_id(self) -> str:
        return self.ids.view_id(view=ViewName.doctor_view)

    @property
    def doctor_view_qid(self) -> str:
        return self.ids.view_id("#", view=ViewName.doctor_view)

    @property
    def doctor_btn_id(self) -> str:
        return self.ids.button_id(btn=FlatBtn.doctor)

    @property
    def cat_config_view_id(self) -> str:
        return self.ids.view_id(view=ViewName.cat_config_view)

    @property
    def cat_config_view_qid(self) -> str:
        return self.ids.view_id("#", view=ViewName.cat_config_view)

    @property
    def cat_config_btn_id(self) -> str:
        return self.ids.button_id(btn=FlatBtn.cat_config)

    @property
    def template_data_view_id(self) -> str:
        return self.ids.view_id(view=ViewName.template_data_view)

    @property
    def template_data_view_qid(self) -> str:
        return self.ids.view_id("#", view=ViewName.template_data_view)

    @property
    def template_data_btn_id(self) -> str:
        return self.ids.button_id(btn=FlatBtn.template_data)


class InitCloneRepo(Vertical, AppType):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.screen_ids = InitScreenIds(ids=ids)
        super().__init__(id=self.screen_ids.new_repo_view_id)
        self.repo_url: str = ""

    def compose(self) -> ComposeResult:
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
        self.screen_ids = InitScreenIds(ids=self.ids)
        super().__init__(
            id=self.ids.content_switcher_id(
                name=ContainerName.init_screen_switcher
            ),
            initial=self.screen_ids.new_repo_view_id,
        )
        self.splash_data = splash_data
        self.doctor_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield InitCloneRepo(ids=self.ids)
        yield DoctorTableView(ids=self.ids)
        yield CatConfigOutput(ids=self.ids)
        yield TemplateDataOutput(ids=self.ids)

    def on_mount(self) -> None:
        doctor_view = self.query_one(
            self.screen_ids.doctor_view_qid, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        cat_config = self.query_one(f"#{ViewName.cat_config_view}", Static)
        cat_config.update(self.splash_data.cat_config.std_out)
        template_cmd_output = self.splash_data.template_data.std_out
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(template_cmd_output)
        pretty_template_data.update(template_data_json)


class InitScreen(Screen[None], AppType):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        super().__init__()
        self.ids = ids
        self.tab_vertical_id = ids.tab_vertical_id(
            name=ContainerName.left_side
        )
        self.screen_ids = InitScreenIds(ids=self.ids)
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
            self.ids.content_switcher_id(
                "#", name=ContainerName.init_screen_switcher
            ),
            ContentSwitcher,
        )
        if event.button.id == self.screen_ids.new_repo_btn_id:
            switcher.current = self.screen_ids.new_repo_view_id
        elif event.button.id == self.screen_ids.doctor_btn_id:
            switcher.current = self.screen_ids.doctor_view_id
        elif event.button.id == self.screen_ids.cat_config_btn_id:
            switcher.current = self.screen_ids.cat_config_view_id
        elif event.button.id == self.screen_ids.template_data_btn_id:
            switcher.current = self.screen_ids.template_data_view_id
