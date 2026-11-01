"""STEP 06a – pytest: connection to the shared session (step 05).

No own logic here – only the link from pytest to the setup and teardown
that all three tools share, plus the command table in report.html.
"""
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[2]
for folder in sorted(TESTS.glob("0[2-5]_*")):
    sys.path.insert(0, str(folder))

from command_log import LOG, html_table, inline_style  # noqa: E402
from session import REPORTS_DIR, TestSession  # noqa: E402

REPORT_DIR = REPORTS_DIR / "6a_pytest"


@pytest.fixture(scope="session")
def session():
    s = TestSession(REPORT_DIR)
    s.begin()
    yield s
    s.end()


@pytest.fixture
def context(session, request):
    case = request.node.callspec.params["case"]
    try:
        yield session.start_test(case.id, case.title)
    finally:
        report = getattr(request.node, "rep_call", None)
        failed = report is None or report.failed
        message = ""
        if report is not None and report.failed:
            crash = getattr(report.longrepr, "reprcrash", None)
            message = crash.message if crash else str(report.longrepr)
        session.end_test(case.id, failed, message)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Remember the result (screenshot on failure) and add the command log
    of this test case to report.html."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    # After teardown the log of this test is complete. pytest-html shows the
    # "call" row (or "setup" if setup failed) and builds the report only after
    # teardown – so the full table is attached to that row now.
    if report.when == "teardown" and hasattr(item, "callspec"):
        case = item.callspec.params.get("case")
        target = getattr(item, "rep_call", None) or getattr(item, "rep_setup", None)
        if case is not None and target is not None:
            try:
                from pytest_html import extras
                table = inline_style() + html_table(LOG.entries_for(case.id))
                target.extras = getattr(target, "extras", []) + [extras.html(table)]
            except ImportError:
                pass
