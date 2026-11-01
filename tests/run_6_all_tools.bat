@echo off
REM Runs all three tools (6a, 6b, 6c) one after another, then compares the results.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
call run_6a_pytest.bat
call run_6b_robot_framework.bat
call run_6c_pywinauto_only.bat
python 07_results__reports\compare_results.py
echo.
echo Comparison: 07_results__reports\00_comparison_of_all_tools.html
start "" "07_results__reports\00_comparison_of_all_tools.html"
