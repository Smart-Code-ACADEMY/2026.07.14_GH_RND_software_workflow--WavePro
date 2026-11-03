@echo off
REM 6a pytest: reads the test specification, report in 08_results__reports\6a_pytest
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
REM Step 07: choose the test cases (only once - skipped when called from run_6_all_tools.bat)
if not defined WAVEPRO_SELECTION_DONE (
    for /f "usebackq delims=" %%i in (`python 07_choose_tests__test_selection\choose_which_tests_to_run__test_selection_popup.py`) do set "WAVEPRO_TESTS=%%i"
)
if "%WAVEPRO_TESTS%"=="CANCEL" exit /b 1
if "%WAVEPRO_TESTS%"=="" (echo Test selection failed - see the message above. & exit /b 1)
if exist 08_results__reports\6a_pytest rmdir /s /q 08_results__reports\6a_pytest
python 02_read_the_spec__spec_loader\update_makrdown_test_spec_document.py
python -m pytest 06_run_the_tests__test_runners\6a_pytest --junitxml=08_results__reports\6a_pytest\junit.xml --html=08_results__reports\6a_pytest\report.html --self-contained-html
