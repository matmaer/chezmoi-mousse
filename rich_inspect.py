import sys
from rich import inspect

if __name__ == "__main__":
    selected_text = sys.argv[1]
    exec(inspect(f"{selected_text})"))
