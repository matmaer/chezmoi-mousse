# ruff: noqa: F401 F403
# type: ignore  # noqa: PGH003

import ast
import asyncio
import json
import os
import shutil
import sys
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum, StrEnum, auto
from functools import cache, cached_property
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING, ClassVar, NamedTuple

from rich import inspect, print
from rich.pretty import install as install_pretty
from rich.traceback import install as install_traceback
from scripts.common_textual_imports import *

from chezmoi_mousse.str_enums import *

terminal_size = shutil.get_terminal_size()

install_traceback(width=terminal_size.columns - 4)

# Pretty print an object automatically in the REPL, when you just type its name.
install_pretty(max_string=180)


# Shortcuts methods for different Inspect params of objects in the REPL

# default=False help    Show full help text rather than just first paragraph
# default=False methods Enable inspection of callables
# default=True  docs    Also render doc strings
# default=False private Show private attributes
# default=True  value   Pretty print value of object


def methspect(to_inspect: object) -> None:
    inspect(to_inspect, methods=True, help=True, dunder=False)


def minspect(to_inspect: object) -> None:
    # Minimal inspection: show methods, hide docs and don't pretty print recursively
    inspect(to_inspect, methods=True, docs=False)


def _get_cwd() -> Path:
    return Path.cwd()


def cwd() -> None:
    print(Path.cwd())


def ls() -> None:
    cwd = _get_cwd()
    # split the results into directories and files
    dir_count = 0
    file_count = 0
    max_items = 20
    dirs: set[str] = set()
    files: set[str] = set()
    for item in cwd.iterdir():
        if item.is_dir():
            dirs.add(str(item))
            dir_count += 1
            if dir_count > max_items:
                dirs.add("...")
                break
        else:
            files.add(str(item))
            file_count += 1
            if file_count > max_items:
                files.add("...")
                break
    print({"dirs": sorted(dirs), "files": sorted(files)})


def dirpub(some_object: object) -> None:
    print([name for name in dir(some_object) if not name.startswith("_")])
