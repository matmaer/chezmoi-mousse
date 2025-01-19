# MIT License

# Copyright (c) 2021 Will McGugan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from __future__ import annotations

import inspect

from rich.syntax import Syntax

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen, Screen
from textual.widgets import Static


class CodeScreen(ModalScreen):
    DEFAULT_CSS = """
    CodeScreen {
        #code {
            border: heavy $accent;
            margin: 2 4;
            scrollbar-gutter: stable;
            Static {
                width: auto;
            }
        }
    }
    """
    BINDINGS = [("escape", "dismiss", "Dismiss")]

    def __init__(self, title: str, code: str) -> None:
        super().__init__()
        self.code = code
        self.title = title

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="code"):
            yield Static(
                Syntax(
                    self.code, lexer="python", indent_guides=True, line_numbers=True
                ),
                expand=True,
            )

    def on_mount(self):
        code_widget = self.query_one("#code")
        code_widget.border_title = self.title
        code_widget.border_subtitle = "Escape to close"


class PageScreen(Screen):
    BINDINGS = [
        Binding(
            key="c",
            action="show_code",
            description="Code",
            tooltip="Show the code used to generate this screen",
        ),
    ]

    @work(thread=True)
    def get_code(self, source_file: str) -> str | None:
        """Read code from disk, or return `None` on error."""
        try:
            with open(source_file, "rt", encoding="utf-8") as file_:
                return file_.read()
        except Exception:
            return None

    async def action_show_code(self):
        source_file = inspect.getsourcefile(self.__class__)
        if source_file is None:
            self.notify(
                "Could not get the code for this page",
                title="Show code",
                severity="error",
            )
            return

        code = await self.get_code(source_file).wait()
        if code is None:
            self.notify(
                "Could not get the code for this page",
                title="Show code",
                severity="error",
            )
        else:
            self.app.push_screen(CodeScreen("Code for this page", code))
