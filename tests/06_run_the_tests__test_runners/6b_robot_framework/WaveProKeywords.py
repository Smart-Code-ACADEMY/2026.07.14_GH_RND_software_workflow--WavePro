"""STEP 06b – Robot Framework: keyword library.

Defines NO steps of its own. It hands all steps of step 03
(keyword_library.py) to Robot ("Dynamic Library API") and uses the same
session (step 05) as pytest and pywinauto only.
"""
import sys
from pathlib import Path

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

TESTS = Path(__file__).resolve().parents[2]
for folder in sorted(TESTS.glob("0[2-5]_*")):
    sys.path.insert(0, str(folder))

from keyword_library import KEYWORDS, find_keyword  # noqa: E402
from session import REPORTS_DIR, TestSession  # noqa: E402

REPORT_DIR = REPORTS_DIR / "6b_robot_framework"

_SESSION_KEYWORDS = {
    "Begin Session": "_begin",
    "End Session": "_end",
    "Start Test": "_start_test",
    "End Test": "_end_test",
}


def _log_image(path: Path) -> None:
    logger.info(f'<img src="{Path(path).as_uri()}" width="800">', html=True)


class WaveProKeywords:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self._session = TestSession(REPORT_DIR)

    # ---------- Robot Dynamic Library API ------------------------------
    def get_keyword_names(self):
        return list(_SESSION_KEYWORDS) + [k.name for k in KEYWORDS.values()]

    def get_keyword_arguments(self, name):
        if name in _SESSION_KEYWORDS:
            return []
        return [f"value{i + 1}" for i in range(find_keyword(name).value_count)]

    def get_keyword_documentation(self, name):
        if name in _SESSION_KEYWORDS:
            return "Setup / teardown from step 05 (session.py)."
        kind = "Check" if find_keyword(name).is_check else "Action"
        return f"{kind} from step 03 (keyword_library.py)"

    def run_keyword(self, name, args, kwargs=None):
        if name in _SESSION_KEYWORDS:
            return getattr(self, _SESSION_KEYWORDS[name])()
        context = self._session.context
        if context is None:
            raise RuntimeError("Wave Pro was not started.")
        result = find_keyword(name).function(context, *args)
        screenshot = context.memory.pop("screenshot", None)
        if screenshot is not None:
            _log_image(screenshot)
        return result

    # ---------- Session --------------------------------------------------
    def _begin(self):
        self._session.begin()

    def _end(self):
        self._session.end()

    def _start_test(self):
        self._session.start_test()

    def _end_test(self):
        builtin = BuiltIn()
        name = builtin.get_variable_value("${TEST NAME}", "test").split(" ")[0]
        failed = builtin.get_variable_value("${TEST STATUS}") != "PASS"
        screenshot = self._session.end_test(name, failed)
        if screenshot is not None:
            _log_image(screenshot)
