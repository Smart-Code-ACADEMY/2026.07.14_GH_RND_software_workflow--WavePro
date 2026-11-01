@echo off
REM 02 Robot Framework: liest 00_spezifikation\testfaelle.yaml, Bericht in reports\02_robot
cd /d "%~dp0"
if exist reports\02_robot rmdir /s /q reports\02_robot
python 09_gemeinsam\erzeuge_uebersicht.py
python -m robot --parser 02_robot\yaml_parser.py --outputdir reports\02_robot 00_spezifikation\testfaelle.yaml
