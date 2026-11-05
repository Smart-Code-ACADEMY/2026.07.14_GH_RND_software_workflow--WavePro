"""STEP 02 – READ AND CHECK THE SPECIFICATION  (spec loader)

1. Makes the step files 03–05 loadable (see MODULE_PATTERNS below).
2. Reads 01_what_to_test__test_specification/test_cases.yaml and checks it
   BEFORE the EXE is started: unknown step name, wrong number of values,
   duplicate ID, missing field, test case without a check, broken YAML.
3. Applies the test selection from step 07 (WAVEPRO_TESTS, or the selection window).

Used by all three tools (6a pytest, 6b Robot Framework, 6c pywinauto only).
Every tool imports THIS file first.
"""
from __future__ import annotations

import importlib.abc
import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

TESTS_DIR = Path(__file__).resolve().parents[1]


def find_step_file(pattern: str) -> Path:
    """The one file in tests/ that matches `pattern`, e.g. "05_*/*__session.py".

    Files are found by their step number and their professional name at the
    END of the file name. The descriptive part in front can be renamed freely."""
    matches = sorted(TESTS_DIR.glob(pattern))
    if len(matches) != 1:
        found = "none" if not matches else ", ".join(m.name for m in matches)
        raise ImportError(f"Expected exactly one file matching '{pattern}' in {TESTS_DIR}, "
                          f"found: {found}. Keep the step number in the folder name and the "
                          f"professional name at the end of the file name.")
    return matches[0]


SPEC_FILE = find_step_file("01_*/test_cases.yaml")

# ── Which file is which module? ─────────────────────────────────────────
# The file names are long and readable for people and may contain "-" or
# spaces. Python cannot `import` such names, so each file gets a short module
# name. The file is found by: step-number folder + professional name at the
# end. Example: 04_*/*_app_driver.py → commands-to-interact-your-app_app_driver.py
MODULE_PATTERNS = {
    "keyword_library":    "03_*/*__keyword_library.py",
    "app_driver":         "04_*/*_app_driver.py",
    "command_log":        "04_*/*_command_log.py",
    "profile_guard":      "05_*/*__profile_guard.py",
    "temp_music_library": "05_*/*__temp_music_library.py",
    "session":            "05_*/*__session.py",
}


class _StepFileFinder(importlib.abc.MetaPathFinder):
    """Lets `import app_driver` load 04_…/commands-to-interact-your-app_app_driver.py."""

    def find_spec(self, name, path=None, target=None):
        pattern = MODULE_PATTERNS.get(name)
        if pattern is None:
            return None
        return importlib.util.spec_from_file_location(name, find_step_file(pattern))


if not any(isinstance(f, _StepFileFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _StepFileFinder())

from keyword_library import Context, execute_step, find_keyword, readable  # noqa: E402


class SpecificationError(Exception):
    pass


@dataclass(frozen=True)
class StepCall:
    name: str          # exactly as written in the YAML file
    values: tuple      # always texts (like in Robot Framework)

    @property
    def is_check(self) -> bool:
        return find_keyword(self.name).is_check

    def readable(self) -> str:
        return readable(self.name, self.values)


@dataclass(frozen=True)
class TestCase:
    __test__ = False          # tell pytest: this is not a test class
    id: str
    title: str
    principle: str
    goal: str
    steps: tuple

    @property
    def name(self) -> str:
        return f"{self.id} {self.title}"


def _values(raw) -> tuple:
    if raw is None:
        return ()
    if isinstance(raw, list):
        return tuple("" if v is None else str(v) for v in raw)
    return (str(raw),)


def load_specification(file: Path = SPEC_FILE) -> List[TestCase]:
    try:
        data = yaml.safe_load(Path(file).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SpecificationError(f"{file}: YAML error: {e}") from e

    if not isinstance(data, dict) or not isinstance(data.get("test_cases"), list):
        raise SpecificationError(f"{file}: list 'test_cases' is missing.")

    cases, ids = [], set()
    for number, raw in enumerate(data["test_cases"], start=1):
        where = f"{Path(file).name}, test case no. {number}"
        if not isinstance(raw, dict):
            raise SpecificationError(f"{where}: must be an entry with id/title/steps.")
        for field_name in ("id", "title", "principle", "steps"):
            if not raw.get(field_name):
                raise SpecificationError(f"{where}: field '{field_name}' is missing.")
        case_id = str(raw["id"])
        if case_id in ids:
            raise SpecificationError(f"{where}: ID {case_id} is used twice.")
        ids.add(case_id)

        steps = []
        for step_no, s in enumerate(raw["steps"], start=1):
            place = f"{case_id}, step {step_no}"
            if not (isinstance(s, dict) and len(s) == 1):
                raise SpecificationError(f"{place}: expected format 'Step Name: value'.")
            name, raw_value = next(iter(s.items()))
            try:
                keyword = find_keyword(str(name))
            except KeyError as e:
                raise SpecificationError(f"{place}: {e.args[0]}") from None
            values = _values(raw_value)
            if len(values) != keyword.value_count:
                raise SpecificationError(
                    f"{place}: '{name}' needs {keyword.value_count} value(s), "
                    f"got {len(values)}.")
            steps.append(StepCall(str(name), values))

        if not any(s.is_check for s in steps):
            raise SpecificationError(f"{case_id}: has no check ('… Should …').")

        cases.append(TestCase(case_id, str(raw["title"]), str(raw["principle"]),
                              str(raw.get("goal", "")), tuple(steps)))
    return cases


def run_test_case(context: Context, case: TestCase) -> None:
    """Run all steps in order (each logged); a failure message names the step."""
    for number, call in enumerate(case.steps, start=1):
        try:
            execute_step(context, call.name, call.values)
        except AssertionError as e:
            raise AssertionError(
                f"{case.id} – step {number}: {call.readable()}\n  → {e}") from None


# ── Test selection (step 07) ────────────────────────────────────────────
class SelectionCancelled(Exception):
    """The user pressed Cancel in the test-selection window."""


def _ask_user() -> List[str]:
    """Open the step-07 selection window in this process; returns the chosen IDs."""
    file = find_step_file("07_*/*__test_selection_popup.py")
    spec = importlib.util.spec_from_file_location("test_selection_popup", file)
    popup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(popup)
    ids = popup.ask_user()
    if not ids:
        raise SelectionCancelled("Cancelled in the test-selection window – no tests run.")
    return ids


def load_selected_test_cases(file: Path = SPEC_FILE, ask: bool = True) -> List[TestCase]:
    """The test cases of this run.

    WAVEPRO_TESTS="TC-08"         → only TC-08 (set by run_6_all_tools.bat)
    WAVEPRO_TESTS="ALL"           → all test cases, no window
    WAVEPRO_TESTS not set, ask    → the selection window opens (never silently all)
    WAVEPRO_TESTS not set, no ask → all test cases (used by the comparison page)"""
    cases = load_specification(file)
    raw = os.environ.get("WAVEPRO_TESTS", "").strip()
    if not raw:
        if not ask:
            return cases
        raw = ",".join(_ask_user())
        os.environ["WAVEPRO_TESTS"] = raw      # the same choice for the rest of this run
    if raw.upper() == "ALL":
        return cases
    wanted = [x.strip() for x in raw.split(",") if x.strip()]
    unknown = [w for w in wanted if w not in {c.id for c in cases}]
    if unknown:
        raise SpecificationError(f"Selected test cases not in the specification: {unknown}")
    return [c for c in cases if c.id in wanted]


def selection_text() -> str:
    """The selection of this run in words – shown at the top of every report."""
    total = len(load_specification())
    raw = os.environ.get("WAVEPRO_TESTS", "").strip()
    if not raw or raw.upper() == "ALL":
        return f"all {total} test cases"
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    return f"{', '.join(ids)} ({len(ids)} of {total} test cases)"
