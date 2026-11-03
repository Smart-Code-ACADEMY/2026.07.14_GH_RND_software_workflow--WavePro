# Wave Pro – automated tests

The folders are numbered in the order a test run happens:
**01 what to test → 02 read → 03 translate → 04 real commands → 05 before/after → 06 run → 07 choose tests → 08 results.**

Test cases are defined in ONE place: **`01_what_to_test__test_specification/test_cases.yaml`**.
Three tools read that file and must give the same results.

## Quick start (Windows)

1. **Close Wave Pro.**
2. Once, in the project folder: `pip install -r tests\requirements-tests.txt`
3. Start `tests\run_6_all_tools.bat` (or one tool: `run_6a_pytest.bat`, `run_6b_robot_framework.bat`,
   `run_6c_pywinauto_only.bat`).
4. **A window opens (step 07): choose the test cases** and click *Run selected tests*.
5. Do not use mouse and keyboard while the tests run (all 10 tests, all tools: about 15 minutes).
6. Results: `tests\08_results__reports\` – `run_6_all_tools.bat` opens
   `00_comparison_of_all_tools.html` at the end.

A different EXE than in `publish\`: `set WAVEPRO_EXE=C:\path\WavePro.exe`

## Step 07 – choosing the test cases

- The window opens **once** per start. `run_6_all_tools.bat` asks once and runs the same choice with all three tools.
- It preselects your **saved selection** – or **all** test cases if nothing is saved.
- Tick **"Save this selection for next time"** to keep your choice
  (stored in `07_choose_tests__test_selection/saved_test_selection.json`).
  Without ticking it, the choice is used only for this run.
- **"Forget saved selection"** deletes the saved choice → all test cases are preselected again.
- **Cancel** (or Esc) stops the start file; nothing runs.
- Without a display, a short text menu appears instead of the window.

## Folders and files

```
tests/
├── 01_what_to_test__test_specification/
│   ├── test_cases.yaml                     ★ the test cases – edit tests only here
│   └── test_specification.md               explanation; its table is generated from the YAML
├── 02_read_the_spec__spec_loader/
│   ├── spec_loader.py                      reads + checks the YAML, loads the files of steps 03–05,
│   │                                       applies the step-07 selection (MODULE_FILES = file table)
│   └── update_makrdown_test_spec_document.py   writes the table into test_specification.md
├── 03_translate_steps__keyword_library/
│   └── connect_testcase_with_right_function_and_run_test_steps__keyword_library.py
│                                           step name → Python function (actions and checks)
├── 04_real_commands__app_driver/
│   ├── commands-to-interact-your-app_app_driver.py        pywinauto: start, click, type, keys, scroll…
│   └── write-down-every-executed-command_command_log.py   logs every command + explanation + file:line
├── 05_before_and_after__setup_teardown/
│   ├── backup_and_restore_user_data-and-settings__profile_guard.py   protects your Wave Pro data
│   ├── generate_and_delete_test_data__temp_music_library.py         60 silent WAV test files
│   └── prepare_and_cleanup_every_test-unified_test_structure__session.py   before/after every test
├── 06_run_the_tests__test_runners/
│   ├── 6a_pytest/            conftest.py, pytest.ini, run_yaml_test_cases_with_pytest.py
│   ├── 6b_robot_framework/   convert_yaml_to_robot_tests__yaml_parser.py,
│   │                         run_shared_steps_with_robot__robot_keywords.py
│   └── 6c_pywinauto_only/    run_yaml_tests_with_pywinauto__run_specification.py
├── 07_choose_tests__test_selection/
│   ├── choose_which_tests_to_run__test_selection_popup.py   the selection window
│   └── saved_test_selection.json            (created when you save a selection)
├── 08_results__reports/
│   ├── compare_and_combine_existing_reports.py   creates 00_comparison_of_all_tools.html
│   └── 00_comparison_of_all_tools.html, 6a_pytest/, 6b_robot_framework/, 6c_pywinauto_only/  (generated)
├── run_6_all_tools.bat   run_6a_pytest.bat   run_6b_robot_framework.bat   run_6c_pywinauto_only.bat
└── requirements-tests.txt
```

**Renaming a file in 03–05?** Change its entry in `MODULE_FILES` in `spec_loader.py` (one place).
File names may contain `-`, because these files are loaded by their path.

## Command log – every command, step by step

While the tests run, **every executed command** is printed in the terminal, one per line:
the command exactly as executed (with its result) | what it does in plain words | [file:line].
The same lines are saved for every tool in `08_results__reports/<tool>/command_log.html`
(also `.txt` and `.json`) and appear inside pytest's `report.html` and Robot's `log.html`.
The last HTML column **"Executed in (file:line)"** shows the exact source line.
Zoomed in? Use **← →** to scroll sideways (Shift + ← → = faster).
`00_comparison_of_all_tools.html` also checks that all three tools ran the **same commands**.

## Change or add a test case

Edit `01_…/test_cases.yaml` (allowed step names: the file in `03_…`) and start a run.
Spelling mistakes in step names are reported before anything starts.

## Safety

- Only a temporary test library is used; your music is never touched.
- Settings, change history and unfinished tasks are backed up and restored.
- If a run is interrupted, the next run restores the backup automatically.
