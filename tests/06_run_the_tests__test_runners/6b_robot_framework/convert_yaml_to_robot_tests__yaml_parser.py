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
for folder in sorted(TESTS.glob("0[2-5]_*")):
    sys.path.insert(0, str(folder))

from spec_loader import load_specification  # noqa: E402

EXTENSION = ".yaml"
# IMPORTANT: as_posix() = path with "/". With Windows "\" Robot would read the
# characters as escapes ("\t" = tab) and not find the library.
LIBRARY = Path(__file__).with_name("run_shared_steps_with_robot__robot_keywords.py").as_posix()


def parse(source: Path, defaults=None) -> TestSuite:
    cases = load_specification(Path(source))
    suite = TestSuite(name="Wave Pro Test Specification", source=source,
                      doc=f"Generated automatically from {Path(source).name}")
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
