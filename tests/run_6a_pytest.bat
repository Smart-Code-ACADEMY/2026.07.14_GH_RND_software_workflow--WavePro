@echo off
REM 6a pytest: runs the chosen test cases, report in 08_results__reports\6a_pytest
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
REM Delete the previous report first, so you never read results of an earlier run.
if exist 08_results__reports\6a_pytest rmdir /s /q 08_results__reports\6a_pytest
REM Step 07: the test-selection window opens when the tool starts.
REM (Started by run_6_all_tools.bat: the choice made there is used.)
if not defined WAVEPRO_FROM_ALL_TOOLS set "WAVEPRO_TESTS="
python 02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader\update_makrdown_test_spec_document.py
python -m pytest 06_run_the_tests__test_runners\6a_pytest --junitxml=08_results__reports\6a_pytest\junit.xml --html=08_results__reports\6a_pytest\report.html --self-contained-html
