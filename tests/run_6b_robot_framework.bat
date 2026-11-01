@echo off
REM 6b Robot Framework: reads the test specification, report in 07_results__reports\6b_robot_framework
cd /d "%~dp0"
if exist 07_results__reports\6b_robot_framework rmdir /s /q 07_results__reports\6b_robot_framework
python 02_read_the_spec__spec_loader\update_spec_document.py
python -m robot --parser 06_run_the_tests__test_runners\6b_robot_framework\yaml_parser.py --outputdir 07_results__reports\6b_robot_framework 01_what_to_test__test_specification\test_cases.yaml
