"""STEP 06b – Robot Framework: parser that reads the test specification.

Robot Framework does not understand YAML test cases by itself. This parser
builds a Robot test suite from test_cases.yaml: one Robot test per test
case, one Robot step per YAML step.

Call (see run_6b_robot_framework.bat):
    python -m robot --parser 06_run_the_tests__test_runners/6b_robot_framework/convert_yaml_to_robot_tests__yaml_parser.py
                    01_what_to_test__test_specification/test_cases.yaml
"""
import sys
from pathlib import Path

from robot.running import TestSuite
from robot.utils import escape

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

from spec_loader import load_selected_test_cases, selection_text  # noqa: E402

EXTENSION = ".yaml"
# IMPORTANT: as_posix() = path with "/". With Windows "\" Robot would read the
# characters as escapes ("\t" = tab) and not find the library.
LIBRARY = sorted(Path(__file__).parent.glob("*__robot_keywords.py"))[0].as_posix()


def parse(source: Path, defaults=None) -> TestSuite:
    cases = load_selected_test_cases(Path(source))   # step-07 selection applied
    suite = TestSuite(name="Wave Pro Test Specification", source=source,
                      doc=f"Generated automatically from {Path(source).name}")
    suite.metadata["Test selection (step 07)"] = selection_text()
    suite.resource.imports.library(LIBRARY)
    suite.setup.config(name="Begin Session")
    suite.teardown.config(name="End Session")

    for case in cases:
        test = suite.tests.create(
            name=case.name,
            doc=f"Principle: {case.principle}. {case.goal}",
            tags=[case.id, case.principle])
        test.setup.config(name="Start Test")
        test.teardown.config(name="End Test")
        for call in case.steps:
            # escape(): texts such as "${…}" or "\" stay exactly as written.
            test.body.create_keyword(
                name=call.name,
                args=[escape(v) if v else "${EMPTY}" for v in call.values])
    return suite
