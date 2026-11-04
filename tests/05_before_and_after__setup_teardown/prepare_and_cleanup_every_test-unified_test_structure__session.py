"""STEP 05 – BEFORE AND AFTER: the test session (setup and teardown)

Written ONCE, used by all three tools (6a pytest, 6b Robot, 6c pywinauto):

    begin()         once before all tests:  is YOUR Wave Pro closed? (must be),
                                            report folder, back up your data
    start_test()    before every test:      CLEAN STATE (no Wave Pro left open,
                                            no key held down), fresh temporary
                                            library, fresh settings, start the
                                            EXE, wait until "60 songs" is loaded
    end_test()      after every test:       screenshot if failed, close the EXE,
                                            release all keys, delete the library

EVERY TEST IS INDEPENDENT: it gets its own library, its own settings, its own
Wave Pro process and its own memory. Nothing from an earlier test – passed or
failed – can reach it. So any single test, any selection or all tests can run
in any combination and give the same result.
    end()           once after all tests:   restore your data exactly,
                                            save the command log (step 08)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import app_driver
import profile_guard
import temp_music_library
from command_log import LOG
from keyword_library import Context

TESTS_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = TESTS_DIR / "08_results__reports"


def safe_name(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text)


class TestSession:
    __test__ = False          # tell pytest: this is not a test class

    def __init__(self, report_dir: Path):
        self.report_dir = Path(report_dir)
        self.guard = profile_guard.ProfileGuard()
        self.context: Optional[Context] = None
        self._library: Optional[Path] = None

    def begin(self) -> None:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        LOG.phase("Session start (step 05)", "Back up your real Wave Pro data before any test")
        if app_driver.wave_pro_window_open():
            raise RuntimeError(
                "Wave Pro is open. Please close Wave Pro, then start the tests again. "
                "(Nothing was changed – your data was not touched.)")
        self.guard.backup()

    def start_test(self, case_id: str, title: str) -> Context:
        LOG.begin_test(case_id, title)
        LOG.phase("Setup (step 05)", "Clean state, fresh test data, start Wave Pro")
        app_driver.release_all_keys()
        if app_driver.wave_pro_window_open():          # left over by an earlier test
            app_driver.force_close_wave_pro(app_driver.find_exe().name)
        self._library = temp_music_library.create_test_library()
        self.guard.prepare_for_test(self._library)
        app = app_driver.WaveProApp(app_driver.find_exe(), self._library)
        self.context = Context(app, report_dir=self.report_dir)
        app.start()
        LOG.phase("Test steps (from test_cases.yaml)", "Now the steps of the specification run")
        return self.context

    def end_test(self, case_id: str, failed: bool, message: str = "") -> Optional[Path]:
        """Returns the path of the failure screenshot (or None)."""
        LOG.phase("Teardown (step 05)", "Close Wave Pro and delete the test data")
        app = self.context.app if self.context else None
        screenshot = None
        try:
            if failed and app is not None and app.win is not None:
                screenshot = app.screenshot(
                    self.report_dir / "failure_screenshots" / f"{safe_name(case_id)}.png")
        except Exception:
            screenshot = None
        finally:
            if app is not None:
                app.close()
            try:
                app_driver.release_all_keys()
            except Exception:
                pass
            if self._library is not None:
                self.guard.forget_library_cache(self._library)
                temp_music_library.remove_test_library(self._library)
            self.context = None
            self._library = None
            LOG.end_test("FAIL" if failed else "PASS", message)
        return screenshot

    def end(self) -> None:
        LOG.phase("Session end (step 05)", "Restore your real Wave Pro data")
        try:
            self.guard.restore()
        finally:
            LOG.save(self.report_dir)
