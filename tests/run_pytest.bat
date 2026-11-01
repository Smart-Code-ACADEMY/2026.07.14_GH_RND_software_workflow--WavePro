@echo off
REM pytest liest spec\testfaelle.yaml und fuehrt alle Testfaelle aus.
cd /d "%~dp0"
python tools\erzeuge_uebersicht.py
python -m pytest pytest_suite --junitxml=reports\pytest_junit.xml --html=reports\pytest_report.html --self-contained-html
