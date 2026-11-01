@echo off
REM 03 pywinauto pur: liest 00_spezifikation\testfaelle.yaml, Bericht in reports\03_pywinauto
cd /d "%~dp0"
if exist reports\03_pywinauto rmdir /s /q reports\03_pywinauto
python 09_gemeinsam\erzeuge_uebersicht.py
python 03_pywinauto\run_spezifikation.py
