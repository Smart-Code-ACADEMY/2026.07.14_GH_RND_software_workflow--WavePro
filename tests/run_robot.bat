@echo off
REM Fuehrt dieselben 10 Testfaelle mit Robot Framework + pywinauto aus.
cd /d "%~dp0"
python -m robot --outputdir reports\robot robot_suite
