"""STEP 02 – READ AND CHECK THE SPECIFICATION  (spec loader)

Reads 01_what_to_test__test_specification/test_cases.yaml and checks it
BEFORE the EXE is started: unknown step name, wrong number of values,
duplicate ID, missing field, test case without a check, broken YAML.

Used by all three tools (6a pytest, 6b Robot Framework, 6c pywinauto only).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

from keyword_library import Context, find_keyword

TESTS_DIR = Path(__file__).resolve().parents[1]
SPEC_FILE = TESTS_DIR / "01_what_to_test__test_specification" / "test_cases.yaml"


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
        if not self.values:
            return self.name
        return self.name + " " + ", ".join(f"“{v}”" for v in self.values)


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


def run_step(context: Context, call: StepCall) -> None:
    find_keyword(call.name).function(context, *call.values)


def run_test_case(context: Context, case: TestCase) -> None:
    """Run all steps in order; a failure message names the step."""
    for number, call in enumerate(case.steps, start=1):
        try:
            run_step(context, call)
        except AssertionError as e:
            raise AssertionError(
                f"{case.id} – step {number}: {call.readable()}\n  → {e}") from None
