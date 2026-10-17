from __future__ import annotations

import asyncio
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from chezmoi_mousse import asyncio_process_exec as proc

if TYPE_CHECKING:
    from pathlib import Path

# Prints the index path it was given and leaves a lock file behind like git would
SCRIPT_SHOWING_INDEX = (
    "import os;"
    "idx = os.environ['GIT_INDEX_FILE'];"
    "open(idx + '.lock', 'w').close();"
    "print(idx)"
)


def run_isolated(tmp_path: Path, script: str, timeout: float = 15) -> str:
    """Runs the script with an isolated index and returns what it printed."""
    real_index = tmp_path / "real_index"
    real_index.write_text("index content")
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()

    with (
        mock.patch.object(proc, "_get_chezmoi_cmd", return_value=sys.executable),
        mock.patch.object(proc, "_GLOBAL_TIMEOUT", timeout),
        mock.patch.object(
            proc.store, "cfg", SimpleNamespace(git_index=real_index), create=True
        ),
        mock.patch.object(tempfile, "tempdir", str(temp_dir)),
    ):
        std_out, _, _ = asyncio.run(
            proc.create_subprocess_exec_result(("-c", script), use_isolated_index=True)
        )
    return std_out


def leftovers(tmp_path: Path) -> list[Path]:
    return list((tmp_path / "tmp").iterdir())


def test_isolated_index_is_a_copy_and_cleaned_up(tmp_path: Path) -> None:
    std_out = run_isolated(tmp_path, SCRIPT_SHOWING_INDEX)

    assert std_out != str(tmp_path / "real_index")
    assert (tmp_path / "real_index").read_text() == "index content"
    assert leftovers(tmp_path) == []


def test_isolated_index_is_cleaned_up_after_a_timeout(tmp_path: Path) -> None:
    script = SCRIPT_SHOWING_INDEX + ";import time; time.sleep(30)"

    with pytest.raises(subprocess.TimeoutExpired):
        run_isolated(tmp_path, script, timeout=1)

    assert leftovers(tmp_path) == []
