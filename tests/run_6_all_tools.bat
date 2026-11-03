@echo off
REM Runs all three tools (6a, 6b, 6c) with ONE test selection, then compares the results.
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
set WAVEPRO_SELECTION_DONE=1
call run_6a_pytest.bat
call run_6b_robot_framework.bat
call run_6c_pywinauto_only.bat
python 08_results__reports\compare_and_combine_existing_reports.py
echo.
echo Comparison: 08_results__reports\00_comparison_of_all_tools.html
start "" "08_results__reports\00_comparison_of_all_tools.html"
