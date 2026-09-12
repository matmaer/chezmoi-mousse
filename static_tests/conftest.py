from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest
from static_tests._ast_nodes import NodeDb

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any

    from _pytest.reports import TestReport


type IssueList = list[tuple[str, ...]]
type CheckFunction = Callable[[NodeDb], IssueList]
type CheckRunner = Callable[[CheckFunction], None]


@pytest.fixture(scope="session", autouse=True)  # pyright: ignore[reportUnknownMemberType]
def node_db() -> NodeDb:
    return NodeDb()


def format_fails(items: IssueList) -> str:
    """Groups N-column tuples by their last column, sorts each group by column 0,
    and formats remaining columns into aligned string blocks.
    """
    # Group items by the last element (free text info)
    groups: dict[str, IssueList] = defaultdict(list)
    for row in items:
        info = row[-1]
        data_cols = row[:-1]  # Exclude the info column
        groups[info].append(data_cols)

    # Determine max column widths for the data columns across ALL items
    all_data_rows = [row for row_list in groups.values() for row in row_list]
    num_data_cols = max(len(row) for row in all_data_rows) if all_data_rows else 0

    max_widths = [
        max(len(row[col_idx]) if col_idx < len(row) else 0 for row in all_data_rows)
        for col_idx in range(num_data_cols)
    ]

    # Create padded lines grouped by last column (info)
    formatted_output: list[str] = []
    for info, rows in groups.items():
        formatted_output.append(f"\n___ {info} ___\n")
        for row in sorted(rows):
            formatted_parts: list[str] = []
            for col_idx, text in enumerate(row):
                width = max_widths[col_idx]
                formatted_parts.append(f"{text:<{width}}")
            formatted_line = "-  " + "  ".join(formatted_parts)
            formatted_output.append(formatted_line)

    return "\n".join(formatted_output)


# --- Check Runner Fixture ---
@pytest.fixture  # pyright: ignore[reportUnknownMemberType]
def run_check(node_db: NodeDb) -> CheckRunner:
    """_test_func: formats issues from any def test_func_ and calls pytest.fail()"""

    def _test_func(test_func: CheckFunction) -> None:
        issues = test_func(node_db)
        if issues:
            formatted = format_fails(issues)
            report = f"{len(issues)} issue(s) found:\n" + formatted
            pytest.fail(report)

    return _test_func


# --- Burndown Tracking Hooks ---

total_issues_count: int = 0


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport() -> Generator[None, Any]:
    """Intercepts test failure reports and tallies individual static issue lines."""
    global total_issues_count
    outcome = yield
    report: TestReport = outcome.get_result()

    if report.when == "call" and report.failed:
        longrepr_str = str(report.longrepr)
        issue_count = sum(
            1 for line in longrepr_str.splitlines() if line.strip().startswith("- ")
        )
        total_issues_count += issue_count


def pytest_unconfigure(config: pytest.Config) -> None:
    """Executes during session teardown after all terminal summary reporters finish."""
    if total_issues_count > 0:
        terminalreporter = config.pluginmanager.get_plugin("terminalreporter")
        if terminalreporter is not None:
            terminalreporter.write_line("")
            terminalreporter.write_sep(
                "=",
                f"STATIC ANALYSIS: {total_issues_count} ISSUE(S) REMAINING",
                red=True,
                bold=True,
            )
            terminalreporter.write_line("")
