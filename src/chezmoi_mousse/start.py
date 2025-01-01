"""
Provisional file containing the greeter.
Could be implemented as a splash screen or Richlog greeter.
"""

from chezmoi_mousse.blocks import GREETER


def write_greeter(self):
    # show the greeter after startup
    greeter = GREETER.split("\n")
    top_gradient = [
        "#439CFB",
        "#6698FB",
        "#8994FB",
        "#AB8FFB",
        "#CE8BFB",
        "#F187FB",
        "#F187FB",
    ]
    reverse = top_gradient.copy()
    gradient = top_gradient + reverse.reverse()
    for line, color in zip(greeter, gradient):
        self.rlog(f"[{color}]{line}[/]")
