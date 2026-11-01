"""pytest-Anbindung an die gemeinsame Sitzung (09_gemeinsam/sitzung.py).

Hier steht keine eigene Logik – nur die Verbindung von pytest zu
Vorbereitung und Aufräumen, die alle drei Werkzeuge teilen.
"""
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "09_gemeinsam"))

from sitzung import Sitzung  # noqa: E402
from wavepro import REPORTS_DIR  # noqa: E402

BERICHT = REPORTS_DIR / "01_pytest"


@pytest.fixture(scope="session")
def sitzung():
    s = Sitzung(BERICHT)
    s.beginne()
    yield s
    s.beende()


@pytest.fixture
def kontext(sitzung, request):
    try:
        yield sitzung.starte_test()
    finally:
        rep = getattr(request.node, "rep_call", None)
        fehler = rep is None or rep.failed
        sitzung.beende_test(request.node.callspec.id if hasattr(request.node, "callspec")
                            else request.node.name, fehler)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Merkt sich das Ergebnis, damit bei Fehlern ein Screenshot entsteht."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
