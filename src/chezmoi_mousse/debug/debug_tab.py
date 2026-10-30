from __future__ import annotations

import inspect
import os
from datetime import datetime
from typing import TYPE_CHECKING

import psutil
from rich._inspect import Inspect
from rich.markup import escape
from textual import on, work
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, ContentSwitcher, RichLog, Static, TabPane

from chezmoi_mousse import store
from chezmoi_mousse.debug.test_paths import TestPaths
from chezmoi_mousse.gui.common.actionables import FlatButtonsVertical, OperateBtnGroup
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.str_enums import BtnLabel, ColorVar, LabelStr, LogStr, Tcss

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["DebugLog", "DebugTab"]


class _RichLogger(RichLog):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def _get_log_line(self, msg: str, color: ColorVar) -> str:
        log_time = f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"
        msg_color = self.app.theme_variables[color.value]
        return f"{log_time} [{msg_color}]{escape(msg)}[/]"

    def write_app_log_msg(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.secondary))

    def write_cmd(self, pretty_cmd: str, returncode: int) -> None:
        color = ColorVar.text_success if returncode == 0 else ColorVar.text_warning
        self.write(self._get_log_line(f"{pretty_cmd} (returncode {returncode})", color))

    def write_error(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.text_error))

    def write_ready(self, message: str) -> None:
        self.write(self._get_log_line(f"{message}", ColorVar.accent_darken_3))

    def write_success(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.text_success))

    def write_warning(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.text_warning))


class DebugLog(_RichLogger):
    def __init__(self) -> None:
        super().__init__(markup=True, max_lines=10000, wrap=True)

    def on_mount(self) -> None:
        self.write_ready(LogStr.debug_log_initialized)

    def write_text_block(self, message: str) -> None:
        color = self.app.theme_variables[ColorVar.foreground_darken_2]
        escaped_lines = [
            f"[{color}]{escape(line)}[/]"
            for line in message.splitlines()
            if line.strip() != ""
        ]
        self.write("  \n".join(escaped_lines))

    def write_info(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.foreground_darken_2))

    def write_inspect(self, some_object: object) -> None:
        inspector = Inspect(some_object, all=False, methods=True, private=True)
        self.write(inspector)

    def mro(self, mro: tuple[type, ...]) -> None:
        """Parameter mro accepts self.__class__.__mro__ or SomeClass.__mro__"""
        self.write_info("Method Resolution Order:")

        exclude = {
            "typing.Generic",
            "builtins.object",
            "textual.dom.DOMNode",
            "textual.message_pump.MessagePump",
        }

        pretty_mro = " -> ".join(
            f"{qname}\n"
            for cls in mro
            if not any(
                e in (qname := f"{cls.__module__}.{cls.__qualname__}") for e in exclude
            )
        )
        self.write_text_block(pretty_mro)

    def list_attr(
        self,
        obj: object,
        *,
        filter_text: str | None = None,
        show_method_sources: bool = False,
    ) -> None:
        members = [attr for attr in dir(obj) if not attr.startswith("_")]
        if filter_text is not None:
            members = [m for m in members if filter_text in m]

        if show_method_sources is True:
            for member_name in members:
                member = getattr(obj, member_name)
                if inspect.isroutine(member):
                    self.write_info(f"Source for method {member_name}:")
                    try:
                        source = inspect.getsource(member)
                        self.write_text_block(source)
                    except OSError as e:
                        self.write_error("Could not retrieve source")
                        self.write_text_block(f"{e}")

        def _type_for(name: str) -> str:
            val = getattr(obj, name)
            if inspect.isclass(val):
                return "class"
            if inspect.ismodule(val):
                return "module"
            if inspect.isroutine(val):
                if show_method_sources is True:
                    self.callable_source(val)
                return str(type(val).__name__)
            return str(type(val).__name__)

        members_with_types = [f"{m}: {_type_for(m)}" for m in members]
        self.write_info(f"{obj.__class__.__name__} attributes:")
        self.write_text_block("\n".join(members_with_types))

    def callable_source(self, callable: Callable[..., Any]) -> None:
        self.write_info(f"Function source for {callable.__name__}:")
        try:
            source = inspect.getsource(callable)
            self.write_text_block(source)
        except OSError as e:
            self.write_error("Could not retrieve source")
            self.write_text_block(f"{e}")


class TestPathsView(Static): ...


class ColorVarStatic(Static): ...


class DebugTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    MiB = 1024 * 1024

    process = psutil.Process(os.getpid())
    previous_rss = process.memory_info().rss / MiB
    peak_rss_mb = process.memory_info().rss / MiB
    current_rss_mb = process.memory_info().rss / MiB

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                app_ids=store.debug_ids,
                labels=(
                    BtnLabel.test_paths,
                    BtnLabel.debug_log,
                    BtnLabel.dom_nodes,
                    BtnLabel.env_vars,
                    BtnLabel.colors,
                ),
            )
            with ContentSwitcher(initial=store.debug_ids.container.test_paths_view):
                yield Vertical(
                    MainSectionLabel(LabelStr.test_paths),
                    ScrollableContainer(TestPathsView(classes=Tcss.info)),
                    id=store.debug_ids.container.test_paths_view,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.debug_log),
                    DebugLog(),
                    id=store.debug_ids.container.debug_log,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.dom_nodes),
                    RichLog(
                        id=store.debug_ids.richlog.dom_nodes,
                        highlight=True,
                        auto_scroll=False,
                    ),
                    id=store.debug_ids.container.dom_nodes,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.env_vars),
                    RichLog(
                        id=store.debug_ids.richlog.env_vars,
                        highlight=True,
                        auto_scroll=False,
                    ),
                    id=store.debug_ids.container.env_vars,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.colors),
                    ColorVarStatic(LabelStr.not_set, markup=True),
                    id=store.debug_ids.container.color_vars,
                )
        yield OperateBtnGroup(
            labels=(
                BtnLabel.create_diffs,
                BtnLabel.list_paths,
                BtnLabel.log_memory,
                BtnLabel.remove_paths,
                BtnLabel.start_auto_log,
                BtnLabel.stop_auto_log,
            )
        )

    def on_mount(self) -> None:

        self.test_paths = TestPaths()
        self.op_btn_group = self.query_exactly_one(OperateBtnGroup)
        self.op_buttons = self.op_btn_group.query_children(Button)
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.test_paths_static = self.query_exactly_one(TestPathsView)
        self.test_paths_static.update(self.test_paths.report_test_paths())
        self.debug_log = self.query_exactly_one(DebugLog)
        env_var_logger = self.query_one(store.debug_ids.richlog.env_vars_q, RichLog)
        env_var_logger.write("\n".join(f"{k}: {v}" for k, v in os.environ.items()))
        self.app.call_later(self._log_dom_nodes)
        self.auto_log_timer = self.set_interval(
            name="auto_log", interval=2, callback=self._log_mem_usage
        )
        self.auto_log = True
        self.debug_log.write_app_log_msg(f"{LogStr.auto_log}")
        self.debug_log.write_app_log_msg(
            f"Pre-init memory peak: {self.peak_rss_mb:5.2f} MiB"
        )
        self.app.call_later(self._log_colors)

    def _log_colors(self) -> None:
        self.color_var_static = self.query_exactly_one(ColorVarStatic)
        to_write: list[str] = []
        for color_var in ColorVar:
            color = self.app.theme_variables[color_var.value]
            to_write.append(f"[{color}]{color_var.name}:{color_var.value}[/]")
        self.color_var_static.update("\n".join(to_write))

    def _log_mem_usage(self, manual: bool = False) -> None:
        self.current_rss_mb = self.process.memory_info().rss / self.MiB
        # Check for >2% shift relative to previous reading
        auto_increase = self.current_rss_mb > self.previous_rss * 1.02
        auto_decrease = self.current_rss_mb < self.previous_rss * 0.98
        auto_new_peak = self.current_rss_mb > self.peak_rss_mb * 1.02
        new_peak = self.current_rss_mb > self.peak_rss_mb
        # Update peak RAM usage
        if new_peak:
            self.peak_rss_mb = self.current_rss_mb

        self.previous_rss = self.current_rss_mb

        rss_str = f"{self.current_rss_mb:5.2f} MiB"
        peak_str = f"{self.peak_rss_mb:5.2f} MiB"

        prefix = "Current memory usage:" if manual else "Auto log 2% delta:"

        if manual:
            self.debug_log.write_info(f"{prefix} {rss_str}")
            if new_peak:
                self.debug_log.write_info(f"New peak: {peak_str}")
        elif self.auto_log and auto_new_peak:
            self.debug_log.write_warning(f"New peak: {peak_str}")
        elif self.auto_log and auto_decrease:
            self.debug_log.write_success(f"{prefix} {rss_str}")
        elif self.auto_log and auto_increase:
            self.debug_log.write_warning(f"{prefix} {rss_str}")

    @work
    async def _log_dom_nodes(self) -> None:
        # App dom nodes
        dom_node_logger = self.query_one(store.debug_ids.richlog.dom_nodes_q, RichLog)
        app_nodes = list(self.app.walk_children())
        dom_node_logger.write(f"self.app DOMNode count: {len(app_nodes)}\n")
        app_nodes_with_id = [item for item in app_nodes if item.id is not None]
        app_nodes_without_id = [item for item in app_nodes if item.id is None]
        dom_node_logger.write(f"DOMNodes with id: {len(app_nodes_with_id)}")
        for item in sorted(app_nodes_with_id, key=str):
            dom_node_logger.write(f"{item}")
        dom_node_logger.write(f"\nDOMNodes without id: {len(app_nodes_without_id)}")
        for item in sorted(app_nodes_without_id, key=str):
            dom_node_logger.write(f"{item}")
        # Screen dom nodes
        screen_nodes = list(self.screen.walk_children())
        dom_node_logger.write(f"\nself.screen DOMNode count: {len(screen_nodes)}\n")
        screen_nodes_with_id = [item for item in screen_nodes if item.id is not None]
        screen_nodes_without_id = [item for item in screen_nodes if item.id is None]
        dom_node_logger.write(f"DOMNodes with id: {len(screen_nodes_with_id)}")
        for item in sorted(screen_nodes_with_id, key=str):
            dom_node_logger.write(f"{item}")
        dom_node_logger.write(f"\nDOMNodes without id: {len(screen_nodes_without_id)}")
        for item in sorted(screen_nodes_without_id, key=str):
            dom_node_logger.write(f"{item}")

    def start_auto_log(self) -> None:
        for btn in self.op_buttons:
            btn.disabled = btn.label == BtnLabel.start_auto_log
        self.debug_log.write_success(LogStr.auto_log_started)
        self.auto_log_timer.resume()
        self.auto_log = True

    def stop_auto_log(self) -> None:
        for btn in self.op_buttons:
            btn.disabled = btn.label in (BtnLabel.log_memory, BtnLabel.stop_auto_log)
        self.auto_log_timer.pause()
        self.auto_log = False
        self.debug_log.write_error(LogStr.auto_log_stopped)

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        if event.button.label not in (
            BtnLabel.colors,
            BtnLabel.debug_log,
            BtnLabel.dom_nodes,
            BtnLabel.env_vars,
            BtnLabel.test_paths,
            BtnLabel.start_auto_log,
            BtnLabel.stop_auto_log,
        ):
            return
        if event.button.label == BtnLabel.test_paths:
            for btn in self.op_buttons:
                btn.display = btn.label not in (
                    BtnLabel.log_memory,
                    BtnLabel.start_auto_log,
                    BtnLabel.stop_auto_log,
                )
            self.op_btn_group.display = True
            self.switcher.current = store.debug_ids.container.test_paths_view
        elif event.button.label == BtnLabel.dom_nodes:
            self.op_btn_group.display = False
            self.switcher.current = store.debug_ids.container.dom_nodes
        elif event.button.label == BtnLabel.env_vars:
            self.op_btn_group.display = False
            self.switcher.current = store.debug_ids.container.env_vars
        elif event.button.label == BtnLabel.colors:
            self.op_btn_group.display = False
            self.switcher.current = store.debug_ids.container.color_vars
        elif event.button.label == BtnLabel.debug_log:
            for btn in self.op_buttons:
                btn.display = btn.label in (
                    BtnLabel.log_memory,
                    BtnLabel.start_auto_log,
                    BtnLabel.stop_auto_log,
                )
            self.op_btn_group.display = True
            self.switcher.current = store.debug_ids.container.debug_log

    @on(Button.Pressed)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        if event.button.label == BtnLabel.log_memory:
            self._log_mem_usage(manual=True)
            return
        elif event.button.label == BtnLabel.start_auto_log:
            self.start_auto_log()
            return
        elif event.button.label == BtnLabel.stop_auto_log:
            self.stop_auto_log()
            return
        elif event.button.label == BtnLabel.list_paths:
            result = self.test_paths.report_test_paths()
        elif event.button.label == BtnLabel.create_diffs:
            result = self.test_paths.create_diffs()
        elif event.button.label == BtnLabel.remove_paths:
            result = self.test_paths.remove_test_paths()
        else:
            return
        event.stop()
        self.test_paths_static.update(result)
