"""STEP 06b – Robot Framework: keyword library.

Defines NO steps of its own. It hands all steps of step 03
(map_testcase_text_with_right_function_and_run_test_steps__keyword_library.py) to Robot ("Dynamic Library API") and uses the same
session (step 05) as pytest and pywinauto only.
"""
import sys
from pathlib import Path

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

TESTS = Path(__file__).resolve().parents[2]
# First: load step 02 (the spec loader). It is found by its step number and its
# professional name at the end, so the descriptive part of the name can change.
if "spec_loader" not in sys.modules:
    import importlib.util
    _found = sorted(TESTS.glob("02_*/*__spec_loader.py"))
    if len(_found) != 1:
        raise ImportError(f"Expected one file 02_*/*__spec_loader.py in {TESTS}, found {len(_found)}")
    _spec = importlib.util.spec_from_file_location("spec_loader", _found[0])
    sys.modules["spec_loader"] = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(sys.modules["spec_loader"])
import spec_loader  # noqa: E402,F401  – makes the files of steps 03–05 loadable

from command_log import LOG  # noqa: E402
from keyword_library import KEYWORDS, execute_step, find_keyword  # noqa: E402
from session import REPORTS_DIR, TestSession  # noqa: E402

REPORT_DIR = REPORTS_DIR / "6b_robot_framework"

_SESSION_KEYWORDS = {
    "Begin Session": "_begin",
    "End Session": "_end",
    "Start Test": "_start_test",
    "End Test": "_end_test",
}


def _log_image(path: Path) -> None:
    logger.info(f'<img src="{Path(path).resolve().as_uri()}" width="800">', html=True)


def _to_robot_log(entry: dict) -> None:
    """Every command line also appears in Robot's log.html (under its keyword)."""
    text = entry["command"] + (f"  -> {entry['result']}" if entry["result"] else "")
    logger.info(f"{text}\n    = {entry['explanation']}")


class WaveProKeywords:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self._session = TestSession(REPORT_DIR)
        LOG.listeners.append(_to_robot_log)

    # ---------- Robot Dynamic Library API ------------------------------
    def get_keyword_names(self):
        return list(_SESSION_KEYWORDS) + [k.name for k in KEYWORDS.values()]

    def get_keyword_arguments(self, name):
        if name in _SESSION_KEYWORDS:
            return []
        return [f"value{i + 1}" for i in range(find_keyword(name).value_count)]

    def get_keyword_documentation(self, name):
        if name in _SESSION_KEYWORDS:
            return "Setup / teardown from step 05 (definitions-of_begin-start_test-end_test- end_prepare-and-cleanup-every-test-as-unified-test-structure__session.py)."
        kind = "Check" if find_keyword(name).is_check else "Action"
        return f"{kind} from step 03 (map_testcase_text_with_right_function_and_run_test_steps__keyword_library.py)"

    def run_keyword(self, name, args, kwargs=None):
        if name in _SESSION_KEYWORDS:
            return getattr(self, _SESSION_KEYWORDS[name])()
        context = self._session.context
        if context is None:
            raise RuntimeError("Wave Pro was not started.")
        result = execute_step(context, name, args)
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
        full_name = BuiltIn().get_variable_value("${TEST NAME}", "test")
        case_id, _, title = full_name.partition(" ")
        self._session.start_test(case_id, title)

    def _end_test(self):
        builtin = BuiltIn()
        name = builtin.get_variable_value("${TEST NAME}", "test").split(" ")[0]
        failed = builtin.get_variable_value("${TEST STATUS}") != "PASS"
        message = builtin.get_variable_value("${TEST MESSAGE}", "")
        screenshot = self._session.end_test(name, failed, message if failed else "")
        if screenshot is not None:
            _log_image(screenshot)


# Robot Framework uses the class that has the same name as the file
# (whatever the file is called).
globals()[Path(__file__).stem] = WaveProKeywords
