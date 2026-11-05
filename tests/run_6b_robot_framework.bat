@echo off
REM 6b Robot Framework: runs the chosen test cases, report in 08_results__reports\6b_robot_framework
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
REM Delete the previous report first, so you never read results of an earlier run.
if exist 08_results__reports\6b_robot_framework rmdir /s /q 08_results__reports\6b_robot_framework
REM Step 07: the test-selection window opens when the tool starts.
REM (Started by run_6_all_tools.bat: the choice made there is used.)
if not defined WAVEPRO_FROM_ALL_TOOLS set "WAVEPRO_TESTS="
python 02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader\update_makrdown_test_spec_document.py
python -m robot --parser 06_run_the_tests__test_runners\6b_robot_framework\convert_yaml_to_robot_tests__yaml_parser.py --outputdir 08_results__reports\6b_robot_framework 01_what_to_test__test_specification\test_cases.yaml
