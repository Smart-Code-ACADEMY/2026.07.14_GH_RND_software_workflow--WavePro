@echo off
REM 6c pywinauto only: reads the test specification, report in 07_results__reports\6c_pywinauto_only
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if exist 07_results__reports\6c_pywinauto_only rmdir /s /q 07_results__reports\6c_pywinauto_only
python 02_read_the_spec__spec_loader\update_spec_document.py
python 06_run_the_tests__test_runners\6c_pywinauto_only\run_specification.py
