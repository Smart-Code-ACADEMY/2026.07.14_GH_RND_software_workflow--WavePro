"""STEP 05 – BEFORE AND AFTER: the test session (setup and teardown)

Written ONCE, used by all three tools (6a pytest, 6b Robot, 6c pywinauto):

    begin()       once before all tests:  report folder, back up your data
    start_test()  before every test:      temporary library, start the EXE,
                                          wait until "60 songs" is loaded
    end_test()    after every test:       screenshot if failed, close the EXE,
                                          delete the temporary library
    end()         once after all tests:   restore your data exactly
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import app_driver
import profile_backup
import temp_music_library
from keyword_library import Context

TESTS_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = TESTS_DIR / "07_results__reports"


def safe_name(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text)


class TestSession:
    __test__ = False          # tell pytest: this is not a test class

    def __init__(self, report_dir: Path):
        self.report_dir = Path(report_dir)
        self.guard = profile_backup.ProfileGuard()
        self.context: Optional[Context] = None
        self._library: Optional[Path] = None

    def begin(self) -> None:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.guard.backup()

    def start_test(self) -> Context:
        self._library = temp_music_library.create_test_library()
        self.guard.prepare_for_test(self._library)
        app = app_driver.WaveProApp(app_driver.find_exe(), self._library)
        self.context = Context(app, report_dir=self.report_dir)
        app.start()
        return self.context

    def end_test(self, name: str, failed: bool) -> Optional[Path]:
        """Returns the path of the failure screenshot (or None)."""
        app = self.context.app if self.context else None
        screenshot = None
        try:
            if failed and app is not None and app.win is not None:
                screenshot = app.screenshot(
                    self.report_dir / "failure_screenshots" / f"{safe_name(name)}.png")
        except Exception:
            screenshot = None
        finally:
            if app is not None:
                app.close()
            if self._library is not None:
                self.guard.forget_library_cache(self._library)
                temp_music_library.remove_test_library(self._library)
            self.context = None
            self._library = None
        return screenshot

    def end(self) -> None:
        self.guard.restore()
