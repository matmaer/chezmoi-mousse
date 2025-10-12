# from enum import StrEnum

# from textual import on
# from textual.app import ComposeResult
# from textual.containers import HorizontalGroup, Vertical
# from textual.screen import Screen
# from textual.validation import URL
# from textual.widgets import (
#     Button,
#     ContentSwitcher,
#     Input,
#     Label,
#     Select,
#     Static,
# )

# from chezmoi_mousse import (
#     AreaName,
#     ChangeCmd,
#     Id,
#     NavBtn,
#     OperateBtn,
#     CanvasIds,
#     Tcss,
#     ViewName,
# )
# from chezmoi_mousse.gui import AppType
# from chezmoi_mousse.gui.button_groups import (
#     NavButtonsVertical,
#     OperateBtnHorizontal,
# )


# class Strings(StrEnum):
#     screen_id = "init_screen"


# class InitTab(Screen[None], AppType):

#     def __init__(self) -> None:
#         super().__init__(id=Strings.screen_id)
#         self.repo_url: str | None = None

#     def compose(self) -> ComposeResult:
#         yield NavButtonsVertical(
#             canvas_ids=Id.init,
#             buttons=(NavBtn.new_repo, NavBtn.clone_repo, NavBtn.purge_repo),
#         )
#         yield InitTabSwitcher(canvas_ids=Id.init)

#     @on(Input.Submitted)
#     def log_invalid_reasons(self, event: Input.Submitted) -> None:
#         if (
#             event.validation_result is not None
#             and not event.validation_result.is_valid
#         ):
#             text_lines: str = "\n".join(
#                 event.validation_result.failure_descriptions
#             )
#             self.app.notify(text_lines, severity="error")

#     @on(Button.Pressed, Tcss.nav_button.value)
#     def switch_content(self, event: Button.Pressed) -> None:
#         event.stop()
#         switcher = self.query_exactly_one(InitTabSwitcher)
#         if event.button.id == Id.init.button_id(btn=NavBtn.new_repo):
#             switcher.current = Id.init.view_id(view=ViewName.init_new_view)
#         elif event.button.id == Id.init.button_id(btn=NavBtn.clone_repo):
#             switcher.current = Id.init.view_id(view=ViewName.init_clone_view)

#     @on(Button.Pressed, Tcss.operate_button.value)
#     def handle_operation_button(self, event: Button.Pressed) -> None:
#         event.stop()
#         if event.button.id == Id.init.button_id(btn=OperateBtn.clone_repo):
#             self.app.chezmoi.perform(ChangeCmd.init, self.repo_url)
#             self.query_one(
#                 Id.init.button_id("#", btn=OperateBtn.clone_repo), Button
#             ).disabled = True
#         elif event.button.id == Id.init.button_id(btn=OperateBtn.new_repo):
#             self.app.chezmoi.perform(ChangeCmd.init)
#             self.query_one(
#                 Id.init.button_id("#", btn=OperateBtn.new_repo), Button
#             ).disabled = True
#         elif event.button.id == Id.init.button_id(btn=OperateBtn.purge_repo):
#             self.app.chezmoi.perform(ChangeCmd.purge)
#             self.query_one(
#                 Id.init.button_id("#", btn=OperateBtn.purge_repo), Button
#             ).disabled = True


# class InitTabSwitcher(ContentSwitcher):

#     def __init__(self, canvas_ids: CanvasIds):
#         self.canvas_ids = canvas_ids
#         super().__init__(
#             id=self.canvas_ids.content_switcher_id(area=AreaName.right),
#             initial=self.canvas_ids.view_id(view=ViewName.init_new_view),
#             classes=Tcss.nav_content_switcher.name,
#         )

#     def compose(self) -> ComposeResult:
#         # New Repo Content
#         yield Vertical(
#             Label(
#                 "Initialize new chezmoi git repository",
#                 classes=Tcss.section_label.name,
#             ),
#             Input(placeholder="Enter config file path"),
#             OperateBtnHorizontal(
#                 canvas_ids=self.canvas_ids, buttons=(OperateBtn.new_repo,)
#             ),
#             id=self.canvas_ids.view_id(view=ViewName.init_new_view),
#         )
#         # Clone Repo Content
#         yield Vertical(
#             Label(
#                 "Clone existing chezmoi git repository",
#                 classes=Tcss.section_label.name,
#             ),
#             # TODO: implement guess feature from chezmoi
#             # TODO: add selection for https(with PAT token) or ssh
#             HorizontalGroup(
#                 Vertical(
#                     Select[str].from_values(
#                         ["https", "ssh"],
#                         classes=Tcss.input_select.name,
#                         value="https",
#                         allow_blank=False,
#                         type_to_search=False,
#                     ),
#                     classes=Tcss.input_select_vertical.name,
#                 ),
#                 Vertical(
#                     Input(
#                         placeholder="Enter repository URL",
#                         validate_on=["submitted"],
#                         validators=URL(),
#                         classes=Tcss.input_field.name,
#                     ),
#                     classes=Tcss.input_field_vertical.name,
#                 ),
#             ),
#             OperateBtnHorizontal(
#                 canvas_ids=self.canvas_ids, buttons=(OperateBtn.clone_repo,)
#             ),
#             id=self.canvas_ids.view_id(view=ViewName.init_clone_view),
#         )
#         # Purge chezmoi repo
#         yield Vertical(
#             Label(
#                 "Purge current chezmoi git repository",
#                 classes=Tcss.section_label.name,
#             ),
#             Static(
#                 "Remove chezmoi's configuration, state, and source directory, but leave the target state intact."
#             ),
#             OperateBtnHorizontal(
#                 canvas_ids=self.canvas_ids, buttons=(OperateBtn.purge_repo,)
#             ),
#             id=self.canvas_ids.view_id(view=ViewName.init_purge_view),
#         )
