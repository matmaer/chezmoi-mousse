from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import Container, ScrollableContainer
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import CMD, AppType, ReadCmd, Tcss

from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["ContentsView"]


class ContentsView(Container, AppType):

    class ContentStr(StrEnum):
        cannot_decode = "Path cannot be decoded as UTF-8:"
        empty_or_only_whitespace = "File is empty or contains only whitespace."
        permission_denied = "Permission denied to read file"
        read_error = "Error reading path"
        truncated = "\n--- File content truncated to"

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents)
        self.mounted: dict[Path, str] = {}
        self.current_path: Path | None = None

    def hide_all_containers(self) -> None:
        for container in self.query_children(ScrollableContainer):
            container.display = False

    def _create_managed_dir_container(self, dir_path: Path) -> ScrollableContainer:
        widgets: list[Static | Label] = []
        if dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination Directory", classes=Tcss.main_section_label)
            )
        else:
            widgets.append(Label("Managed directory", classes=Tcss.main_section_label))
        widgets.append(Label(str(dir_path), classes=Tcss.sub_section_label))
        widgets.append(
            Static("<- Click a file to see its contents.", classes=Tcss.added)
        )
        return ScrollableContainer(*widgets, id=self.app.path_to_id(dir_path))

    def _create_file_container(self, file_path: Path) -> ScrollableContainer:
        widgets: list[Label | Static] = []

        def _handle_exception(
            exception: PermissionError | UnicodeDecodeError | OSError,
        ) -> str:
            if isinstance(exception, PermissionError):
                return f"{ContentsView.ContentStr.permission_denied} for {file_path}"
            elif isinstance(exception, UnicodeDecodeError):
                return f"{ContentsView.ContentStr.cannot_decode} for {file_path}"
            else:
                return f"{ContentsView.ContentStr.read_error} for {file_path}"

        def _read_file(file_path: Path) -> str:
            if not file_path.exists():
                cmd_result = CMD.run_cmd.read(ReadCmd.cat, path_arg=file_path)
                self.post_message(LogCmdResultMsg(cmd_result))
                return cmd_result.std_out
            try:
                truncate_size: int = 1024 * 1024  # 1Mib
                file_size = file_path.stat().st_size
                with Path.open(file_path, encoding="utf-8") as f:
                    f_contents = f.read(truncate_size)
                if f_contents.strip() == "":
                    file_contents = ContentsView.ContentStr.empty_or_only_whitespace
                elif file_size > truncate_size:
                    file_contents = (
                        f_contents + f"\n--- {ContentsView.ContentStr.truncated} "
                        f"{truncate_size / 1024} KiB ---"
                    )
                else:
                    file_contents = (
                        "Nothing to read." if f_contents == "" else f_contents
                    )
                return file_contents

            except (UnicodeDecodeError, PermissionError, OSError) as e:
                return _handle_exception(e)

        file_contents = _read_file(file_path)
        text_obj = Text(file_contents)
        ReprHighlighter().highlight(text_obj)
        widgets.append(Static(text_obj))
        return ScrollableContainer(*widgets, id=self.app.path_to_id(file_path))

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.hide_all_containers()
        sc_id = self.app.path_to_id(show_path)
        sc_id_q = self.app.path_to_qid(show_path)
        try:
            container = self.query_one(sc_id_q, ScrollableContainer)
            container.display = True
        except NoMatches:
            if show_path in CMD.cache.sets.managed_dirs_plus_dest_dir:
                container = self._create_managed_dir_container(show_path)
            else:
                container = self._create_file_container(show_path)
            self.mount(container)
            self.mounted[show_path] = sc_id
        self.current_path = show_path
