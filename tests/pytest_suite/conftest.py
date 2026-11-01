"""pytest-Vorbereitung: Profil sichern, Testbibliothek anlegen, App starten.

Für jeden Test: neue Testbibliothek + frisch gestartete App
→ Testfälle sind unabhängig voneinander.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.wavepro import (  # noqa: E402
    REPORTS_DIR, ProfileGuard, WaveProApp, create_test_library, find_exe,
    remove_test_library)


@pytest.fixture(scope="session")
def exe_path() -> Path:
    return find_exe()


@pytest.fixture(scope="session")
def profile_guard():
    guard = ProfileGuard()
    guard.backup()          # einmal vor allen Tests
    yield guard
    guard.restore()         # einmal nach allen Tests


@pytest.fixture
def wavepro(exe_path, profile_guard, request):
    library = create_test_library()
    profile_guard.prepare_for_test(library)
    app = WaveProApp(exe_path, library)
    try:
        app.start()
        yield app
    finally:
        rep = getattr(request.node, "rep_call", None)
        if rep is not None and rep.failed and app.win is not None:
            try:
                app.screenshot(REPORTS_DIR / "pytest_failures" / f"{request.node.name}.png")
            except Exception:
                pass
        app.close()
        profile_guard.forget_library_cache(library)
        remove_test_library(library)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Merkt sich das Testergebnis, damit bei Fehlern ein Screenshot entsteht."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
