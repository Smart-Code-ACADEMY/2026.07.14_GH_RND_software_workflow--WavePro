"""STEP 06a – pytest runs the test specification.

There is NO single test case written here. pytest reads
01_what_to_test__test_specification/test_cases.yaml and creates one test
per entry (name = ID, e.g. "TC-04"). New test case = edit the YAML only.
"""
import pytest

from spec_loader import load_selected_test_cases, run_test_case

# all test cases of the YAML – or only those chosen in the step-07 popup
TEST_CASES = load_selected_test_cases()


@pytest.mark.parametrize("case", TEST_CASES, ids=[c.id for c in TEST_CASES])
def test_from_specification(case, context):
    run_test_case(context, case)
