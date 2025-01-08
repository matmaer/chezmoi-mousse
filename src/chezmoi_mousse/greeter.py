"""
Provisional file containing the greeter.
Could be implemented as a splash screen or Richlog greeter.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Grid
from textual.widgets import RichLog

SPLASH = """
 ██████╗██╗  ██╗███████╗███████╗███╗   ███╗ ██████╗ ██╗
██╔════╝██║  ██║██╔════╝╚══███╔╝████╗ ████║██╔═══██╗██║
██║     ███████║█████╗    ███╔╝ ██╔████╔██║██║   ██║██║
██║     ██╔══██║██╔══╝   ███╔╝  ██║╚██╔╝██║██║   ██║██║
╚██████╗██║  ██║███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝

 ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗
 ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔════╝
 ██╔████╔██║██║   ██║██║   ██║███████╗███████╗█████╗
 ██║╚██╔╝██║██║   ██║██║   ██║╚════██║╚════██║██╔══╝
 ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████║███████╗
 ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
"""
SPLASH = SPLASH.splitlines()[1:]


# 13 lines, index 0-12, 6 being the middle
# 56 columns, index 0-55, middle between 27 and 28
# 84 = 4 + 24 + 2 + 24 + 2 + 24 + 4
# 4 + 21 + 2 + 21 + 2 + 21 + 4 = 75
# --5---10---15---20---25---30---35---40---45---50---55---60---65-----|
# xxx|xxxxxxxxxxxxxxxxxxx|xxx|xxxxxxxxxxxxxxxxxxx|xxx|xxxxxxxxxxxxxxxxxxx|xxx|
# total is 77
# 77 - 56 = 21
# 10 left and 11 right
# .......|
# Inspect
# Operate
# Context


# GREETER = """
# #8  - - - - - - - - - -   / / / / / / / / / / /   - - - - - - - - - - 8#


# |-----------------|    |-----------------|    |-----------------|


#         ██████╗██╗  ██╗███████╗███████╗███╗   ███╗ ██████╗ ██╗
#        ██╔════╝██║  ██║██╔════╝╚══███╔╝████╗ ████║██╔═══██╗██║
#        ██║     ███████║█████╗    ███╔╝ ██╔████╔██║██║   ██║██║
#        ██║     ██╔══██║██╔══╝   ███╔╝  ██║╚██╔╝██║██║   ██║██║
#        ╚██████╗██║  ██║███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║
#         ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝

#         ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗
#         ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔════╝
#         ██╔████╔██║██║   ██║██║   ██║███████╗███████╗█████╗
#         ██║╚██╔╝██║██║   ██║██║   ██║╚════██║╚════██║██╔══╝
#         ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████║███████╗
#         ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝


# """

# GREETER = GREETER.splitlines()[1:-1]
# SHADES = "░▒▓█▓▒░"


# for line in GREETER:
#     print(len(line))


class GreeterScreens(Screen):
    # CSS_PATH = "tui.tcss"
    CSS = """
    Middle {
            background: black;
            border: heavy $accent;
            margin: 2 4;
            scrollbar-gutter: stable;
            Static {
                width: auto;
            }
    }
    """

    def __init__(self):
        super().__init__()
        self.fade = self.generate_fade_colors()
        self.splash = self.generate_splash_lines()

    def generate_fade_colors(self):
        high_fade = [
            "#439CFB",
            "#6698FB",
            "#8994FB",
            "#AB8FFB",
            "#CE8BFB",
            "#F187FB",
        ]
        low_fade = high_fade.copy()
        low_fade.reverse()
        full_fade = high_fade + ["#000000"] + low_fade
        return full_fade

    def generate_splash_lines(self):
        splash_lines = []
        for line, color in zip(SPLASH, self.fade):
            splash_lines.append(f"[{color}]{line}[/]")
        return splash_lines

    def rlog(self, to_print: str) -> None:
        richlog = self.query_one(RichLog)
        richlog.write(to_print)

    def compose(self) -> ComposeResult:
        with Grid():
            yield RichLog(wrap=False, markup=True)

    def on_mount(self) -> None:
        self.rlog("\n".join(self.splash))
        # self.rlog(self.css_tree)
