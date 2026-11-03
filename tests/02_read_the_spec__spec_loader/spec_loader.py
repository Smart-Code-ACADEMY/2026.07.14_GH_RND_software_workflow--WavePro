"""STEP 02 – READ AND CHECK THE SPECIFICATION  (spec loader)

1. Makes the step files 03–05 loadable (see MODULE_FILES below).
2. Reads 01_what_to_test__test_specification/test_cases.yaml and checks it
   BEFORE the EXE is started: unknown step name, wrong number of values,
   duplicate ID, missing field, test case without a check, broken YAML.
3. Applies the test selection from step 07 (environment variable WAVEPRO_TESTS).

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
SPEC_FILE = TESTS_DIR / "01_what_to_test__test_specification" / "test_cases.yaml"

# ── Which file is which module? ─────────────────────────────────────────
# The file names are long and readable for people and may contain "-".
# Python cannot `import` such names, so every file gets a short module name
# here. Rename a file → change it here (one place).
MODULE_FILES = {
    "keyword_library":    "03_translate_steps__keyword_library/"
                          "connect_testcase_with_right_function_and_run_test_steps__keyword_library.py",
    "app_driver":         "04_real_commands__app_driver/commands-to-interact-your-app_app_driver.py",
    "command_log":        "04_real_commands__app_driver/write-down-every-executed-command_command_log.py",
    "profile_guard":      "05_before_and_after__setup_teardown/"
                          "backup_and_restore_user_data-and-settings__profile_guard.py",
    "temp_music_library": "05_before_and_after__setup_teardown/"
                          "generate_and_delete_test_data__temp_music_library.py",
    "session":            "05_before_and_after__setup_teardown/"
                          "prepare_and_cleanup_every_test-unified_test_structure__session.py",
}


class _StepFileFinder(importlib.abc.MetaPathFinder):
    """Lets `import app_driver` load 04_…/commands-to-interact-your-app_app_driver.py."""

    def find_spec(self, name, path=None, target=None):
        relative = MODULE_FILES.get(name)
        if relative is None:
            return None
        file = TESTS_DIR / relative
        if not file.is_file():
            raise ImportError(f"Module '{name}' expects the file {relative} – "
                              f"was it renamed? Update MODULE_FILES in spec_loader.py.")
        return importlib.util.spec_from_file_location(name, file)


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
def selected_ids() -> List[str]:
    """IDs chosen in the step-07 popup (WAVEPRO_TESTS="TC-01,TC-04"); empty = all."""
    raw = os.environ.get("WAVEPRO_TESTS", "").strip()
    return [x.strip() for x in raw.split(",") if x.strip()]


def load_selected_test_cases(file: Path = SPEC_FILE) -> List[TestCase]:
    """All test cases of the specification, filtered by the step-07 selection."""
    cases = load_specification(file)
    wanted = selected_ids()
    if not wanted:
        return cases
    unknown = [w for w in wanted if w not in {c.id for c in cases}]
    if unknown:
        raise SpecificationError(f"Selected test cases not in the specification: {unknown}")
    return [c for c in cases if c.id in wanted]
