"""STEP 06a – pytest: connection to the shared session (step 05).

No own logic here – only the link from pytest to the setup and teardown
that all three tools share.
"""
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[2]
for folder in sorted(TESTS.glob("0[2-5]_*")):
    sys.path.insert(0, str(folder))

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
    try:
        yield session.start_test()
    finally:
        report = getattr(request.node, "rep_call", None)
        failed = report is None or report.failed
        name = request.node.callspec.id if hasattr(request.node, "callspec") else request.node.name
        session.end_test(name, failed)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Remember the result, so that a screenshot is taken on failure."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
