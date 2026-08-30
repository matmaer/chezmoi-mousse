from __future__ import annotations

import inspect
import os
import tracemalloc
from typing import TYPE_CHECKING

from rich.markup import escape
from textual import on, work
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
)
from textual.widgets import (
    Button,
    ContentSwitcher,
    Label,
    RichLog,
    Static,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.actionables import (
    FlatButtonsVertical,
)
from chezmoi_mousse.gui.common.loggers import RichLoggers
from chezmoi_mousse.str_enums import (
    BtnLabel,
    ColorVar,
    LogString,
    SectionLabel,
    Tcss,
)

from .test_paths import TestPaths

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["DebugTab"]


class DebugLog(RichLoggers):
    def __init__(self) -> None:
        super().__init__(markup=True, max_lines=10000, wrap=True)

    def on_mount(self) -> None:
        self.write_ready(LogString.debug_log_initialized)
        if tracemalloc.is_tracing():
            self.write_warning(LogString.tracing)
        else:
            self.write_error(LogString.not_tracing)

    def write_text_block(self, message: str) -> None:
        color = self.app.theme_variables[ColorVar.text_block.value]
        escaped_lines = [
            f"[{color}]{escape(line)}[/]"
            for line in message.splitlines()
            if line.strip() != ""
        ]
        self.write("  \n".join(escaped_lines))

    def write_info(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.info))

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
            try:
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
            except Exception:
                return "unknown"

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


class DebugTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    class TestPathsView(Static): ...

    MiB = 1024 * 1024
    INTERVAL = 2

    _previous_rss: float = 0.0

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        super().__init__(id=BtnLabel.debug.pane_id, title=BtnLabel.debug)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                app_ids=store.debug_ids,
                labels=(
                    BtnLabel.test_paths,
                    BtnLabel.debug_log,
                    BtnLabel.dom_nodes,
                    BtnLabel.env_vars,
                ),
            )
            with ContentSwitcher(initial=store.debug_ids.container.test_paths_view):
                yield Vertical(
                    Label(SectionLabel.test_paths, classes=Tcss.main_section_label),
                    DebugTab.TestPathsView(classes=Tcss.info),
                    id=store.debug_ids.container.test_paths_view,
                )
                yield Vertical(
                    Label(SectionLabel.debug_log, classes=Tcss.main_section_label),
                    DebugLog(),
                    id=store.debug_ids.container.debug_log,
                )
                yield Vertical(
                    Label(SectionLabel.dom_nodes, classes=Tcss.main_section_label),
                    RichLog(
                        id=store.debug_ids.richlog.dom_nodes,
                        highlight=True,
                        auto_scroll=False,
                    ),
                    id=store.debug_ids.container.dom_nodes,
                )
                yield Vertical(
                    Label(SectionLabel.env_vars, classes=Tcss.main_section_label),
                    RichLog(
                        id=store.debug_ids.richlog.env_vars,
                        highlight=True,
                        auto_scroll=False,
                    ),
                    id=store.debug_ids.container.env_vars,
                )
        with HorizontalGroup(
            id=store.debug_ids.container.operate_buttons, classes=Tcss.op_btn_group
        ):
            yield Button(
                classes=Tcss.operate_button,
                id=store.debug_ids.op_btn.log_memory,
                label=BtnLabel.log_memory,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=store.debug_ids.op_btn.list_test_paths,
                label=BtnLabel.list_test_paths,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=store.debug_ids.op_btn.create_diffs,
                label=BtnLabel.create_diffs,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=store.debug_ids.op_btn.create_paths,
                label=BtnLabel.create_paths,
            )
            yield Button(
                classes=Tcss.operate_button,
                id=store.debug_ids.op_btn.remove_paths,
                label=BtnLabel.remove_paths,
            )

    def on_mount(self) -> None:

        self.test_paths = TestPaths()
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.test_paths_view = self.query_one(
            store.debug_ids.container.test_paths_view_q
        )
        self.test_paths_static = self.query_exactly_one(DebugTab.TestPathsView)
        self.debug_log = self.query_exactly_one(DebugLog)
        self.dom_node_logger = self.query_one(
            store.debug_ids.richlog.dom_nodes_q, RichLog
        )
        self.env_var_logger = self.query_one(
            store.debug_ids.richlog.env_vars_q, RichLog
        )
        self.mem_log_op_btn = self.query_one(
            store.debug_ids.op_btn.log_memory_q, Button
        )
        self.mem_log_op_btn.disabled = True
        self.list_test_paths_op_btn = self.query_one(
            store.debug_ids.op_btn.list_test_paths_q, Button
        )
        self.create_diffs_op_btn = self.query_one(
            store.debug_ids.op_btn.create_diffs_q, Button
        )
        self.create_paths_op_btn = self.query_one(
            store.debug_ids.op_btn.create_paths_q, Button
        )
        self.remove_paths_op_btn = self.query_one(
            store.debug_ids.op_btn.remove_paths_q, Button
        )
        self.test_paths_op_btns = [
            self.list_test_paths_op_btn,
            self.create_diffs_op_btn,
            self.create_paths_op_btn,
            self.remove_paths_op_btn,
        ]
        self._list_existing_test_paths()
        self._log_env_vars()
        self.app.call_later(self._log_dom_nodes)
        self.set_interval(self.INTERVAL, lambda: self._write_to_debug_log(auto=True))

    def _list_existing_test_paths(self) -> None:
        path_lines = "\n".join(
            str(p) for p in self.test_paths.get_existing_test_paths()
        )
        result = (
            path_lines
            if path_lines
            else f"[${ColorVar.text_warning} bold]No test paths exist.[/]"
        )
        self.test_paths_static.update(result)

    def _write_to_debug_log(self, auto: bool = False) -> None:
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()

        rss = current_bytes / self.MiB  # Active Python heap allocations
        vms = peak_bytes / self.MiB  # Peak heap size recorded during tracing

        pc2_increase = rss > self._previous_rss * 1.02
        pc2_decrease = rss < self._previous_rss * 0.98
        pc2_change = pc2_increase or pc2_decrease
        self._previous_rss = rss
        if pc2_increase:
            color = "cyan bold"
        elif pc2_decrease:
            color = "green bold"
        elif not pc2_change:
            color = ColorVar.text_secondary
        else:
            color = ColorVar.bogus

        rss_str = f"{rss:5.2f} MiB current heap"
        vms_str = f"{vms:5.2f} MiB peak"

        now_prefix = "Current memory usage log:"
        auto_prefix = "Auto log 2 percent delta:"
        prefix = auto_prefix if auto else now_prefix

        if (pc2_change and auto) or not auto:
            self.debug_log.write(f"[{color}]{prefix} {rss_str} | {vms_str}[/]")

    @work
    async def _log_dom_nodes(self) -> None:
        # App dom nodes
        app_nodes = list(self.app.walk_children())
        self.dom_node_logger.write(f"self.app DOMNode count: {len(app_nodes)}\n")
        app_nodes_with_id = [item for item in app_nodes if item.id is not None]
        app_nodes_without_id = [item for item in app_nodes if item.id is None]
        self.dom_node_logger.write(f"DOMNodes with id: {len(app_nodes_with_id)}")
        for item in sorted(app_nodes_with_id, key=str):
            self.dom_node_logger.write(f"{item}")
        self.dom_node_logger.write(
            f"\nDOMNodes without id: {len(app_nodes_without_id)}"
        )
        for item in sorted(app_nodes_without_id, key=str):
            self.dom_node_logger.write(f"{item}")
        # Screen dom nodes
        screen_nodes = list(self.screen.walk_children())
        self.dom_node_logger.write(
            f"\nself.screen DOMNode count: {len(screen_nodes)}\n"
        )
        screen_nodes_with_id = [item for item in screen_nodes if item.id is not None]
        screen_nodes_without_id = [item for item in screen_nodes if item.id is None]
        self.dom_node_logger.write(f"DOMNodes with id: {len(screen_nodes_with_id)}")
        for item in sorted(screen_nodes_with_id, key=str):
            self.dom_node_logger.write(f"{item}")
        self.dom_node_logger.write(
            f"\nDOMNodes without id: {len(screen_nodes_without_id)}"
        )
        for item in sorted(screen_nodes_without_id, key=str):
            self.dom_node_logger.write(f"{item}")

    @work
    async def _log_env_vars(self) -> None:
        self.env_var_logger.write("\n".join(f"{k}: {v}" for k, v in os.environ.items()))

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == BtnLabel.debug_log:
            self.mem_log_op_btn.disabled = False
            self.switcher.current = store.debug_ids.container.debug_log
        else:
            self.mem_log_op_btn.disabled = True
            for btn in self.test_paths_op_btns:
                btn.display = True
        if event.button.label == BtnLabel.test_paths:
            self.switcher.current = self.test_paths_view.id
        elif event.button.label == BtnLabel.debug_log:
            self.switcher.current = store.debug_ids.container.debug_log
        elif event.button.label == BtnLabel.dom_nodes:
            self.switcher.current = store.debug_ids.container.dom_nodes
        elif event.button.label == BtnLabel.env_vars:
            self.switcher.current = store.debug_ids.container.env_vars

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == BtnLabel.log_memory.value:
            self._write_to_debug_log(auto=False)
            return
        result: str | list[str] = ""
        if event.button.label == BtnLabel.list_test_paths:
            self._list_existing_test_paths()
            return
        if event.button.label == BtnLabel.create_diffs:
            result = self.test_paths.create_diffs()
        elif event.button.label == BtnLabel.create_paths:
            result = self.test_paths.create_paths_on_disk()
        elif event.button.label == BtnLabel.remove_paths:
            result = self.test_paths.remove_test_paths()
        # TODO: self.app.cmattr.update_attributes(ReadCmd.managed_status_commands())
        if isinstance(result, str):
            self.test_paths_static.update(result)
        else:
            self.test_paths_static.update("\n".join(result))
