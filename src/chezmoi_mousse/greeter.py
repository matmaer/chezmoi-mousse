"""
Provisional file containing the greeter.
Could be implemented as a splash screen or Richlog greeter.
"""

GREETER_PART_1 = """
 ██████╗██╗  ██╗███████╗███████╗███╗   ███╗ ██████╗ ██╗
██╔════╝██║  ██║██╔════╝╚══███╔╝████╗ ████║██╔═══██╗██║
██║     ███████║█████╗    ███╔╝ ██╔████╔██║██║   ██║██║
██║     ██╔══██║██╔══╝   ███╔╝  ██║╚██╔╝██║██║   ██║██║
╚██████╗██║  ██║███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝
 """
GREETER_PART_2 = """
 ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗
 ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔════╝
 ██╔████╔██║██║   ██║██║   ██║███████╗███████╗█████╗
 ██║╚██╔╝██║██║   ██║██║   ██║╚════██║╚════██║██╔══╝
 ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████║███████╗
 ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
"""


def write_greeter(self):
    # show the greeter after startup
    top_lines = GREETER_PART_1.split("\n")
    bottom_lines = GREETER_PART_2.split("\n")
    gradient = [
        "#439CFB",
        "#6698FB",
        "#8994FB",
        "#AB8FFB",
        "#CE8BFB",
        "#F187FB",
        "#F187FB",
    ]
    for line, color in zip(top_lines, gradient):
        self.rlog(f"[{color}]{line}[/]")
    gradient.reverse()
    for line, color in zip(bottom_lines, gradient):
        self.rlog(f"[{color}]{line}[/]")
    self.rlog(" ")
