from __future__ import annotations

import asyncio
import json
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse import store
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.named_tuples import DumpConfigKeys
from chezmoi_mousse.str_enums import ColorVar, ReadCmd, SplashLogStr, WriteCmd

from .common.ascii_constants import SPLASH_ASCII
from .common.messages import CommandResultMsg

if TYPE_CHECKING:
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = ["SplashScreen"]

SPLASH_WIDTH = len(max(SPLASH_ASCII, key=len))
LOG_MSG_WIDTH = SPLASH_WIDTH - 4


def _create_fade_line_styles() -> deque[Style]:
    start_color = "#0178D4"
    end_color = "#F187FB"
    fade: list[str] = [start_color] * 10
    gradient = Gradient.from_colors(start_color, end_color, quality=5)
    fade.extend([color.hex for color in gradient.colors])
    gradient.colors.reverse()
    fade.extend([color.hex for color in gradient.colors])
    fade_line_styles = deque(
        [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
    )
    return fade_line_styles


FADE_LINE_STYLES: deque[Style] = _create_fade_line_styles()


class AnimatedFade(Static):
    def on_mount(self) -> None:
        self.step_count = 0
        self.styles.height = len(SPLASH_ASCII)
        self.styles.width = SPLASH_WIDTH
        self.fade_timer = self.set_interval(
            name="refresh_self",
            interval=0.05,
            callback=self._rotate_and_refresh,
            pause=True,
        )

    def _rotate_and_refresh(self) -> None:
        FADE_LINE_STYLES.rotate()
        self.step_count += 1
        self.refresh()

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH_ASCII[y], style=FADE_LINE_STYLES[y])])


class SplashScreen(Screen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    log_message: reactive[str | None] = reactive(None, init=False)

    def _forward_event(self, event: events.Event) -> None:
        if isinstance(
            event,
            (
                events.AppBlur,
                events.AppFocus,
                events.CursorPosition,
                events.Enter,
                events.InputEvent,
                events.Leave,
                events.MouseEvent,
                events.Paste,
                events.Resize,
                events.TextSelected,
            ),
        ):
            return
        super()._forward_event(event)

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(markup=True))

    def on_mount(self) -> None:
        self.chezmoi_repo_found = False
        self.pre_mount_cmd_results: list[CommandResult] = []
        self.color_map: dict[SplashLogStr | int, str] = {
            SplashLogStr.checked: self.app.theme_variables[ColorVar.text_warning],
            SplashLogStr.failed: self.app.theme_variables[ColorVar.text_error],
            SplashLogStr.reports: self.app.theme_variables[ColorVar.accent_darken_2],
            SplashLogStr.parsed: self.app.theme_variables[ColorVar.text_success],
            SplashLogStr.success: self.app.theme_variables[ColorVar.text_primary],
        }
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.height = (
            len(ReadCmd.post_dump_config_commands())
            + len(ReadCmd.post_operation_commands())
            + 9
        )
        self.splash_log.styles.width = LOG_MSG_WIDTH
        self.animated_fade = self.query_exactly_one(AnimatedFade)
        self.animated_fade.fade_timer.resume()

    def _write_log_msg(
        self, *, prefix: SplashLogStr | str, suffix: SplashLogStr
    ) -> None:
        padding = LOG_MSG_WIDTH - len(prefix) - len(suffix.padded) - 4
        color = self.color_map[suffix]
        msg = f"[{color}]{prefix} {'.' * padding} {suffix.padded}[/{color}]"
        self.splash_log.write(msg)

    async def _splash_run_pre_mount_cmd(self, cmd: ReadCmd) -> None:
        cr: CommandResult = await Commands.exec_read_cmd(cmd, path_arg=None)
        self.pre_mount_cmd_results.append(cr)

        prefix = cr.pretty_cmd
        suffix = SplashLogStr.success if cr.returncode == 0 else SplashLogStr.checked
        self._write_log_msg(prefix=prefix, suffix=suffix)

        if cmd is ReadCmd.dump_config:
            parsed_std_out = json.loads(cr.std_out)
            store.cfg = DumpConfigKeys(
                dest_dir_path=Path(parsed_std_out["destDir"]),
                auto_add_bool=parsed_std_out["git"]["autoadd"],
                auto_commit_bool=parsed_std_out["git"]["autocommit"],
                auto_push_bool=parsed_std_out["git"]["autopush"],
            )
            store.add_path = store.cfg.dest_dir_path
            store.apply_path = store.cfg.dest_dir_path
            store.re_add_path = store.cfg.dest_dir_path
            self._write_log_msg(
                prefix=SplashLogStr.parse_dump_config, suffix=SplashLogStr.reports
            )
        elif cmd is ReadCmd.git_remote:
            if cr.returncode == 0:
                self.chezmoi_repo_found = True
                self._write_log_msg(
                    prefix=SplashLogStr.repo_found, suffix=SplashLogStr.reports
                )
            else:
                self._write_log_msg(
                    prefix=SplashLogStr.repo_not_found, suffix=SplashLogStr.reports
                )

        elif cmd is ReadCmd.git_log:
            if cr.returncode == 0:
                self._write_log_msg(
                    prefix=SplashLogStr.has_git_commits, suffix=SplashLogStr.reports
                )
            else:
                self._write_log_msg(
                    prefix=SplashLogStr.has_no_git_commits, suffix=SplashLogStr.reports
                )

    async def _splash_run_post_mount_cmd(self, cmd: ReadCmd) -> None:
        cr: CommandResult = await Commands.exec_read_cmd(cmd, path_arg=None)
        self.app.post_message(CommandResultMsg(cr))

        prefix = cr.pretty_cmd
        suffix = SplashLogStr.success if cr.returncode == 0 else SplashLogStr.checked
        self._write_log_msg(prefix=prefix, suffix=suffix)

        if cmd is ReadCmd.dump_config:
            parsed_std_out = json.loads(cr.std_out)
            store.cfg = DumpConfigKeys(
                dest_dir_path=Path(parsed_std_out["destDir"]),
                auto_add_bool=parsed_std_out["git"]["autoadd"],
                auto_commit_bool=parsed_std_out["git"]["autocommit"],
                auto_push_bool=parsed_std_out["git"]["autopush"],
            )
            store.add_path = store.cfg.dest_dir_path
            store.apply_path = store.cfg.dest_dir_path
            store.re_add_path = store.cfg.dest_dir_path
            self._write_log_msg(
                prefix=SplashLogStr.parse_dump_config, suffix=SplashLogStr.reports
            )
        elif cmd is ReadCmd.git_remote:
            if cr.returncode == 0:
                self.chezmoi_repo_found = True
                self._write_log_msg(
                    prefix=SplashLogStr.repo_found, suffix=SplashLogStr.reports
                )
            else:
                self._write_log_msg(
                    prefix=SplashLogStr.repo_not_found, suffix=SplashLogStr.reports
                )

        elif cmd is ReadCmd.git_log:
            if cr.returncode == 0:
                self._write_log_msg(
                    prefix=SplashLogStr.has_git_commits, suffix=SplashLogStr.reports
                )
            else:
                self._write_log_msg(
                    prefix=SplashLogStr.has_no_git_commits, suffix=SplashLogStr.reports
                )

    async def _splash_run_chezmoi_init(self) -> None:
        cr = await Commands.run_write_cmd(WriteCmd.init, path_arg=None)
        suffix = SplashLogStr.success if cr.returncode == 0 else SplashLogStr.failed
        self._write_log_msg(prefix=cr.pretty_cmd, suffix=suffix)
        if self.chezmoi_repo_found:
            self._write_log_msg(
                prefix=SplashLogStr.repo_created, suffix=SplashLogStr.reports
            )
        else:
            self._write_log_msg(
                prefix=SplashLogStr.repo_init, suffix=SplashLogStr.reports
            )

    async def run_init_tasks(self) -> None:
        await self._splash_run_pre_mount_cmd(ReadCmd.git_remote)
        await self._splash_run_chezmoi_init()
        await self._splash_run_pre_mount_cmd(ReadCmd.dump_config)

    async def run_post_init_tasks(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for cmd in ReadCmd.post_dump_config_commands():
                tg.create_task(self._splash_run_post_mount_cmd(cmd))

        async with asyncio.TaskGroup() as tg:
            for cmd in ReadCmd.post_operation_commands():
                tg.create_task(self._splash_run_post_mount_cmd(cmd))

    async def dismiss_after_fade_loop(self) -> None:
        while (
            self.animated_fade.step_count < 20
            or self.animated_fade.step_count % 20 != 0
        ):
            await asyncio.sleep(0.03)
        self.dismiss()
