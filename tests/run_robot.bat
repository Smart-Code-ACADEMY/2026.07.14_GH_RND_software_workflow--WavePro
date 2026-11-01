@echo off
REM Robot Framework liest spec\testfaelle.yaml (ueber robot_suite\yaml_parser.py).
cd /d "%~dp0"
python tools\erzeuge_uebersicht.py
python -m robot --parser robot_suite\yaml_parser.py --outputdir reports\robot spec\testfaelle.yaml
