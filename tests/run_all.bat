@echo off
REM Beide Werkzeuge nacheinander (Vergleich).
cd /d "%~dp0"
call run_pytest.bat
call run_robot.bat
echo.
echo Ergebnisse: reports\pytest_report.html  und  reports\robot\report.html
