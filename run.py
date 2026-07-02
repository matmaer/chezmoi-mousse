import sys
from pathlib import Path

# Add the src folder to python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from chezmoi_mousse.main import run_app  # pyright: ignore[reportMissingTypeStubs]

if __name__ == "__main__":
    run_app()
