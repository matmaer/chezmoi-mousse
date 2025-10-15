"""Contains all RichLog widgets.

These classes
- inherit directly from built in textual widgets
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't call any query methods
- don't import from main_tabs.py, gui.py or containers.py modules
- don't have key bindings
"""

from datetime import datetime
from subprocess import CompletedProcess
from typing import TYPE_CHECKING

from rich.markup import escape
from rich.text import Text
from textual.reactive import reactive
from textual.widgets import RichLog

from chezmoi_mousse import (
    ActiveCanvas,
    Canvas,
    Chars,
    GlobalCmd,
    ReadCmd,
    Tcss,
    VerbArgs,
    ViewName,
)
from chezmoi_mousse.gui import AppType

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CanvasIds

__all__ = [
    "AppLog",
    "ContentsView",
    "DebugLog",
    "DiffView",
    "LogUtils",
    "OutputLog",
]


class LogUtils:
    @staticmethod
    def pretty_cmd_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return "chezmoi " + " ".join(
            [
                _
                for _ in command[1:]
                if _
                not in GlobalCmd.default_args.value
                + filter_git_log_args
                + [
                    VerbArgs.format_json.value,
                    VerbArgs.path_style_absolute.value,
                ]
            ]
        )


class ContentsView(RichLog, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        # self.first_render: bool = True
        super().__init__(
            id=self.ids.view_id(view=ViewName.contents_view),
            auto_scroll=False,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            highlight=True,
            classes=Tcss.border_title_top.name,
        )
        self.click_colored_file = Text(
            "Click a colored file in the tree to see the contents.",
            style="dim",
        )

    def on_mount(self) -> None:
        self._write_destDir_info()

    def _write_destDir_info(self) -> None:
        self.write('This is the destination directory "chezmoi destDir"\n')
        self.write(self.click_colored_file)

    def watch_path(self) -> None:
        assert self.path is not None
        self.border_title = f" {self.path} "
        self.clear()
        truncated_message = ""
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated_message = (
                    "\n\n--- File content truncated to 150 KiB ---\n"
                )
                self.app.app_log.warning(
                    f"File {self.path} is larger than 150 KiB, truncating output."
                )
        except PermissionError as e:
            self.write(e.strerror)
            self.app.app_log.error(f"Permission denied to read {self.path}")
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if not file_content.strip():
                    message = "File is empty or contains only whitespace"
                    self.write(message)
                else:
                    self.write(file_content + truncated_message)

        except UnicodeDecodeError:
            self.write(f"{self.path} cannot be decoded as UTF-8.")
            return

        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.path in self.app.chezmoi.managed_dirs:
                self.write(f"Managed directory: {self.path}")
                return
            if self.path in self.app.chezmoi.managed_files:
                cat_output = self.app.chezmoi.read(ReadCmd.cat, self.path)
                if cat_output == "":
                    self.write(
                        Text("File contains only whitespace", style="dim")
                    )
                else:
                    self.write(cat_output.splitlines())
                return

        except IsADirectoryError:
            if self.path in self.app.chezmoi.managed_dirs:
                self.write(f"Managed directory: {self.path}")
            else:
                self.write(f"Unmanaged directory: {self.path}")

        except OSError as error:
            self.write(Text(f"Error reading {self.path}: {error}"))
            if self.app.chezmoi.app_log is not None:
                self.app.chezmoi.app_log.error(
                    f"Error reading {self.path}: {error}"
                )


class DiffView(RichLog, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds", reverse: bool) -> None:
        self.ids = ids
        self.reverse = reverse
        self.destDir: "Path | None" = None
        self.active_canvas: ActiveCanvas | None = None
        self.diff_read_cmd: ReadCmd = (
            ReadCmd.diff_reverse if self.reverse else ReadCmd.diff
        )
        self.pretty_diff_cmd = LogUtils.pretty_cmd_str(
            self.diff_read_cmd.value
        )
        self.active_canvas = Canvas.re_add if self.reverse else Canvas.apply
        super().__init__(
            id=self.ids.view_id(view=ViewName.diff_view),
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            classes=Tcss.border_title_top.name,
        )
        self.click_colored_file = Text(
            f"Click a colored file in the tree to see the output from {self.pretty_diff_cmd}",
            style="dim",
        )

    def on_mount(self) -> None:
        self.write('This is the destination directory "chezmoi destDir"\n')
        self.write(self.click_colored_file)

    def _write_dir_info(self) -> None:
        self.write(f"Managed directory {self.path}\n")
        self.write(self.click_colored_file)

    def _write_unchanged_file_info(self) -> None:
        self.write(
            f'No diff available for "{self.path}", the file is unchanged.'
        )
        self.write(self.click_colored_file)

    def watch_path(self) -> None:
        if self.path is None or self.path == self.destDir:
            return
        self.border_title = f" {self.path} "
        self.clear()
        # write lines for an unchanged file or directory except when we are in
        # either the ApplyTab or ReAddTab
        if (
            self.active_canvas is not None
            and self.path in self.app.chezmoi.managed_dirs
        ):
            self._write_dir_info()
            return

        # create the diff view for a changed file
        diff_output: list[str] = []
        diff_output = self.app.chezmoi.read(
            self.diff_read_cmd, self.path
        ).splitlines()

        diff_lines: list[str] = [
            line
            for line in diff_output
            if line.strip() != ""
            and (
                line[0] in "+- "
                or line.startswith("old mode")
                or line.startswith("new mode")
            )
            and not line.startswith(("+++", "---"))
        ]
        if not diff_lines:
            self._write_unchanged_file_info()
            return

        for line in diff_lines.copy():
            line = line.rstrip("\n")  # each write call contains a newline
            if line.startswith("old mode") or line.startswith("new mode"):
                self.write("Permissions/mode will be changed:")
                self.write(f" {Chars.bullet} {line}")
                # remove the line from diff_lines
                diff_lines.remove(line)

        self.write(f'Output from "{self.pretty_diff_cmd} {self.path}":\n')
        for line in diff_lines:
            if line.startswith("-"):
                self.write(Text(line, self.app.theme_variables["text-error"]))
            elif line.startswith("+"):
                self.write(
                    Text(line, self.app.theme_variables["text-success"])
                )


class CommandLogBase(RichLog, AppType):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def _log_command(self, command: list[str]) -> None:
        trimmed_cmd = LogUtils.pretty_cmd_str(command)
        time = self._log_time()
        color = self.app.theme_variables["primary-lighten-3"]
        log_line = f"{time} [{color}]{trimmed_cmd}[/]"
        self.write(log_line)

    def ready_to_run(self, message: str) -> None:
        color = self.app.theme_variables["accent-darken-3"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def info(self, message: str) -> None:
        color = self.app.theme_variables["text-secondary"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def success(self, message: str) -> None:
        color = self.app.theme_variables["text-success"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def warning(self, message: str) -> None:
        lines = message.splitlines()
        color = self.app.theme_variables["text-warning"]
        for line in [line for line in lines if line.strip() != ""]:
            escaped_line = escape(line)
            self.write(f"{self._log_time()} [{color}]{escaped_line}[/]")

    def error(self, message: str) -> None:
        color = self.app.theme_variables["text-error"]
        time = self._log_time()
        self.write(f"{time} [{color}]{message}[/]")

    def dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        lines: list[str] = message.splitlines()
        color = self.app.theme_variables["text-disabled"]
        for line in lines:
            if line.strip() != "":
                escaped_line = escape(line)
                self.write(f"[{color}]{escaped_line}[/]")


class AppLog(CommandLogBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.app_log_view),
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views.name,
        )
        self.succes_no_output = f"{Chars.check_mark} Success, no output"
        self.success_with_output = (
            f"{Chars.check_mark} success, output processed in UI"
        )

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
        self._log_command(completed_process.args)
        if completed_process.returncode == 0:
            if completed_process.stdout == "":
                self.success(self.succes_no_output)
            else:
                self.success(self.success_with_output)
        else:
            self.error(
                f"{Chars.x_mark} Command failed with exit code {completed_process.returncode}, stderr logged to Output log"
            )


class DebugLog(CommandLogBase, AppType):

    type Mro = tuple[type, ...]

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.debug_log_view),
            markup=True,
            max_lines=10000,
            wrap=True,
            classes=Tcss.log_views.name,
        )

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
        self._log_command(completed_process.args)
        self.dimmed(f"{dir(completed_process)}")

    def mro(self, mro: Mro) -> None:
        color = self.app.theme_variables["accent-darken-2"]
        self.write(f"{self._log_time()} [{color}]Method Resolution Order:[/]")

        exclude = {
            "typing.Generic",
            "builtins.object",
            "textual.dom.DOMNode",
            "textual.message_pump.MessagePump",
            "chezmoi_mousse.id_typing.AppType",
        }

        pretty_mro = " -> ".join(
            f"{qname}\n"
            for cls in mro
            if not any(
                e in (qname := f"{cls.__module__}.{cls.__qualname__}")
                for e in exclude
            )
        )
        self.dimmed(pretty_mro)

    def list_attr(self, obj: object) -> None:
        members = [attr for attr in dir(obj) if not attr.startswith("_")]
        self.ready_to_run(f"{obj.__class__.__name__} attributes:")
        self.dimmed(", ".join(members))


class OutputLog(CommandLogBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.output_log_view),
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views.name,
        )

    def _trim_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )

    def completed_process(
        self, completed_process: CompletedProcess[str], trimmed: bool = True
    ) -> None:
        if trimmed:
            completed_process.stdout = self._trim_stdout(
                completed_process.stdout
            )
            completed_process.stderr = self._trim_stdout(
                completed_process.stderr
            )
        self._log_command(completed_process.args)
        if completed_process.returncode == 0:
            self.success("success, stdout:")
            if completed_process.stdout == "":
                self.dimmed("No output on stdout")
            else:
                self.dimmed(completed_process.stdout)
        else:
            self.error("failed, stderr:")
            self.dimmed(f"{completed_process.stderr}")
