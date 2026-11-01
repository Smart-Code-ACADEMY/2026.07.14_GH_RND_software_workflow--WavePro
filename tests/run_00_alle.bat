@echo off
REM Alle drei Werkzeuge nacheinander, danach Vergleich in reports\00_vergleich.html
cd /d "%~dp0"
call run_01_pytest.bat
call run_02_robot.bat
call run_03_pywinauto.bat
python 09_gemeinsam\vergleiche_ergebnisse.py
echo.
echo Vergleich: reports\00_vergleich.html
start "" "reports\00_vergleich.html"
