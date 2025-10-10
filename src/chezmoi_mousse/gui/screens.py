from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click
from textual.screen import Screen

from chezmoi_mousse import Id, PaneBtn, TabIds, Tcss, ViewName
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.rich_logs import ContentsView, DiffView
from chezmoi_mousse.gui.widgets import GitLogView

__all__ = ["Maximized"]


class ScreensBase(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape", action="esc_dismiss", description="close", show=False
        )
    ]

    def __init__(self, *, screen_id: str) -> None:
        self.screen_id = screen_id
        super().__init__(id=self.screen_id, classes=Tcss.screen_base.name)

    def on_click(self, event: Click) -> None:
        event.stop()
        if (
            event.chain == 2
            and self.screen_id == Id.maximized_screen.screen_id
        ):
            self.dismiss()

    def action_esc_dismiss(self) -> None:
        if self.screen_id in [
            Id.maximized_screen.screen_id,
            Id.operate_screen.screen_id,
        ]:
            self.dismiss()
        elif self.screen_id == Id.install_help_screen.screen_id:
            self.app.exit()


class Maximized(ScreensBase):

    def __init__(
        self, *, id_to_maximize: str | None, path: Path | None, tab_ids: TabIds
    ) -> None:
        self.id_to_maximize = id_to_maximize
        self.path = path
        self.tab_ids = tab_ids
        self.reverse: bool = (
            False if self.tab_ids.tab_name == PaneBtn.apply_tab.name else True
        )
        super().__init__(screen_id=Id.maximized_screen.screen_id)

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.contents_view
            ):
                yield ContentsView(tab_ids=Id.maximized_screen)
            elif self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.diff_view
            ):
                yield DiffView(
                    init_ids=Id.maximized_screen, reverse=self.reverse
                )
            elif self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.git_log_view
            ):
                yield GitLogView(tab_ids=Id.maximized_screen)

    def on_mount(self) -> None:
        self.add_class(Tcss.border_title_top.name)
        self.border_subtitle = self.border_subtitle = (
            Id.maximized_screen.border_subtitle()
        )
        if self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.contents_view
        ):
            if self.path is not None:
                self.query_one(
                    Id.maximized_screen.view_id(
                        "#", view=ViewName.contents_view
                    ),
                    ContentsView,
                ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.diff_view
        ):
            if self.path is not None:
                self.query_one(
                    Id.maximized_screen.view_id("#", view=ViewName.diff_view),
                    DiffView,
                ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.git_log_view
        ):
            if self.path is not None:
                self.query_one(
                    Id.maximized_screen.view_id(
                        "#", view=ViewName.git_log_view
                    ),
                    GitLogView,
                ).path = self.path

        if self.path == self.app.destDir:
            self.border_title = f" {self.app.destDir} "
        elif self.path is not None:
            self.border_title = f" {self.path.relative_to(self.app.destDir)} "
