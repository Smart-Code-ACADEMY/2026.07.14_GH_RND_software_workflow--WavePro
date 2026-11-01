@echo off
REM Fuehrt die 10 Testfaelle mit pytest + pywinauto aus.
cd /d "%~dp0"
python -m pytest pytest_suite --junitxml=reports\pytest_junit.xml --html=reports\pytest_report.html --self-contained-html
