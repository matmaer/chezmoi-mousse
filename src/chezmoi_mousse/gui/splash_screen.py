from __future__ import annotations

import asyncio
import json
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual import events, work
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.gui.common.ascii_constants import SPLASH_ASCII
from chezmoi_mousse.named_tuples import DumpConfigKeys
from chezmoi_mousse.str_enums import ColorVar, LogStr, ReadCmd, WriteCmd

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

    async def on_mount(self) -> None:
        self.repo_existed = True
        self.pre_mount_cmd_results: list[CommandResult] = []
        self.color_map: dict[LogStr | int, str] = {
            LogStr.absent: self.app.theme_variables[ColorVar.text_error],
            LogStr.present: self.app.theme_variables[ColorVar.success],
            LogStr.checked: self.app.theme_variables[ColorVar.warning],
            LogStr.reports: self.app.theme_variables[ColorVar.accent_darken_2],
            LogStr.parsed: self.app.theme_variables[ColorVar.success],
            LogStr.success: self.app.theme_variables[ColorVar.text_primary],
        }
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.height = 18
        self.splash_log.styles.width = LOG_MSG_WIDTH
        self.animated_fade = self.query_exactly_one(AnimatedFade)
        await self.wait_for_refresh()
        self.animated_fade.fade_timer.resume()

    async def _write_log_msg(self, *, prefix: LogStr | str, suffix: LogStr) -> None:
        dots_count = LOG_MSG_WIDTH - len(prefix) - len(suffix.padded_suffix) - 4
        dots = "." * dots_count
        color = self.color_map[suffix]
        msg = f"[{color}]{prefix} {dots} {suffix.padded_suffix}[/{color}]"
        self.splash_log.write(msg)

    async def splash_run_chezmoi(self, cmd: ReadCmd | WriteCmd) -> int:
        if self.repo_existed is False and cmd in (ReadCmd.git_remote, ReadCmd.git_log):
            prefix = tchezmoi.pretty_cmd(cmd, None)
            suffix = LogStr.skipped
            await self._write_log_msg(prefix=prefix, suffix=suffix)
        cr: CommandResult = await tchezmoi.exec_chezmoi_cmd(self.app, cmd, None).wait()
        prefix = cr.pretty_cmd
        if store.pre_mount is True:
            self.pre_mount_cmd_results.append(cr)

        suffix = LogStr.success if cr.returncode == 0 else LogStr.checked
        await self._write_log_msg(prefix=prefix, suffix=suffix)
        if cr.returncode is None:
            return -1
        return cr.returncode

    async def _parse_and_store_config(self) -> None:
        # Set store.cfg variable
        cr = self.pre_mount_cmd_results[-1]  # result form chezmoi dump-config
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
        await self._write_log_msg(prefix=LogStr.parse_dump_config, suffix=LogStr.parsed)

    async def run_initial_command_sequence(self) -> None:

        # check if repo exists
        rc = await self.splash_run_chezmoi(ReadCmd.git_dir)
        suffix = LogStr.present if rc == 0 else LogStr.absent
        await self._write_log_msg(prefix=LogStr.check_chezmoi_repo, suffix=suffix)
        self.repo_existed = bool(rc == 0)
        if not self.repo_existed:
            # TODO: show modal for chezmoi init
            self.notify("No existing chezmoi repository found.")
            self.notify("chezmoi init not yet implemented in this case...")
            self.notify("App will exit...", severity="warning")
            await asyncio.sleep(3)
            self.app.exit()

        # run chezmoi init to update config
        rc = await self.splash_run_chezmoi(WriteCmd.init)
        if rc != 0:
            # TODO: handle error when chezmoi init to update config fails, could happen
            # after the user updated the template files
            self.notify(
                "Error: Failed to run chezmoi init to update config, run chezmoi init "
                "manually in the terminal to check for issues.",
                severity="error",
            )
            self.notify("App will exit...", severity="warning")
            await asyncio.sleep(3)
            self.app.exit()
        await self.splash_run_chezmoi(ReadCmd.dump_config)

        # parse and store config
        await self._parse_and_store_config()

        store.pre_mount = False

    @work(group="managed_commands")
    async def run_managed_commands(self) -> None:
        for cmd in ReadCmd.managed_commands():
            await self.splash_run_chezmoi(cmd)

    async def dismiss_after_fade_loop(self) -> None:
        while (
            self.animated_fade.step_count < 20
            or self.animated_fade.step_count % 20 != 0
        ):
            await asyncio.sleep(0.03)
        self.dismiss()
