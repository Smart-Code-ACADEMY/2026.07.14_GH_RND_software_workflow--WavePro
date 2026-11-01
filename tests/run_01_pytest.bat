@echo off
REM 01 pytest: liest 00_spezifikation\testfaelle.yaml, Bericht in reports\01_pytest
cd /d "%~dp0"
if exist reports\01_pytest rmdir /s /q reports\01_pytest
python 09_gemeinsam\erzeuge_uebersicht.py
python -m pytest 01_pytest --junitxml=reports\01_pytest\junit.xml --html=reports\01_pytest\report.html --self-contained-html
