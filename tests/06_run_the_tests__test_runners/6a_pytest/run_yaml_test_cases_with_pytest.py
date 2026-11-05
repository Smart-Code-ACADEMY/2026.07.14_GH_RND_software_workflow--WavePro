"""STEP 06a – pytest runs the test specification.

There is NO single test case written here. pytest reads
01_what_to_test__test_specification/test_cases.yaml and creates one test
per entry (name = ID, e.g. "TC-04"). New test case = edit the YAML only.
"""
import pytest

from spec_loader import SelectionCancelled, load_selected_test_cases, run_test_case

# Only the test cases chosen in step 07 (WAVEPRO_TESTS, or the selection window
# opens now). Never silently all of them.
try:
    TEST_CASES = load_selected_test_cases()
except SelectionCancelled as cancelled:
    pytest.exit(str(cancelled), returncode=1)


@pytest.mark.parametrize("case", TEST_CASES, ids=[c.id for c in TEST_CASES])
def test_from_specification(case, context):
    run_test_case(context, case)
