@echo off
REM Runs all three tools (6a, 6b, 6c) with ONE test selection, then compares the results.
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
REM Delete all previous reports first, so you never read results of an earlier run.
for %%d in (6a_pytest 6b_robot_framework 6c_pywinauto_only) do if exist 08_results__reports\%%d rmdir /s /q 08_results__reports\%%d
if exist 08_results__reports\00_comparison_of_all_tools.html del 08_results__reports\00_comparison_of_all_tools.html
REM Step 07: choose the test cases ONCE; the choice is written to a temporary file.
set "WAVEPRO_SELECTION_FILE=%TEMP%\wavepro_test_selection_%RANDOM%.txt"
python 07_choose_tests__test_selection\choose_which_tests_to_run__test_selection_popup.py --out "%WAVEPRO_SELECTION_FILE%"
if errorlevel 1 (echo No tests run. & del "%WAVEPRO_SELECTION_FILE%" >nul 2>&1 & exit /b 1)
set /p WAVEPRO_TESTS=<"%WAVEPRO_SELECTION_FILE%"
del "%WAVEPRO_SELECTION_FILE%" >nul 2>&1
echo Test selection: %WAVEPRO_TESTS%
set WAVEPRO_FROM_ALL_TOOLS=1
call run_6a_pytest.bat
call run_6b_robot_framework.bat
call run_6c_pywinauto_only.bat
python 08_results__reports\compare_and_combine_existing_reports.py
echo.
echo Comparison: 08_results__reports\00_comparison_of_all_tools.html
start "" "08_results__reports\00_comparison_of_all_tools.html"
