@echo off
REM 6a pytest: reads the test specification, report in 07_results__reports\6a_pytest
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if exist 07_results__reports\6a_pytest rmdir /s /q 07_results__reports\6a_pytest
python 02_read_the_spec__spec_loader\update_spec_document.py
python -m pytest 06_run_the_tests__test_runners\6a_pytest --junitxml=07_results__reports\6a_pytest\junit.xml --html=07_results__reports\6a_pytest\report.html --self-contained-html
