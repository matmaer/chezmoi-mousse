import subprocess
from pathlib import Path

import pytest


def test_flake8_issues():
    result = subprocess.run(
        ["flake8", "src/"], capture_output=True, text=True, cwd=Path.cwd()
    )
    if result.returncode != 0:
        pytest.fail(f"Flake8 found issues:\n{result.stdout}\n{result.stderr}")
