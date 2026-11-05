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

- **One tool** (`run_6a_pytest.bat`, `run_6b_robot_framework.bat`, `run_6c_pywinauto_only.bat`):
  the selection window opens when the tool starts. Only the ticked test cases run.
- **All tools** (`run_6_all_tools.bat`): the window opens **once**; all three tools run exactly that choice.
- **Started another way** (VS Code, command line): the window also opens – a run never silently uses
  all test cases. To skip the window: `set WAVEPRO_TESTS=TC-08` (or `TC-01,TC-04`, or `ALL`).
- The window preselects your **saved selection** – or **all** test cases if nothing is saved.
  Tick **"Save this selection for next time"** to keep your choice
  (stored in `07_choose_tests__test_selection/saved_test_selection.json`); otherwise it is used for this run only.
- **"Select all"** ticks every test case, **"Deselect all"** removes every tick with one click.
  **"Forget saved selection"** deletes the saved choice. **Cancel** (or Esc) stops the run; nothing is changed.
- Every report shows the selection at the top (**"Test selection (step 07): TC-08 (1 of 10 test cases)"**),
  and old reports are deleted before a run starts – so a report always belongs to the run you just made.

## Folders and files

```
tests/
├── 01_what_to_test__test_specification/
│   ├── test_cases.yaml                     ★ the test cases – edit tests only here
│   └── test_specification.md               explanation; its table is generated from the YAML
├── 02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader/
│   ├── yaml-to-dictionary-converting__spec_loader.py                      reads + checks the YAML, loads the files of steps 03–05,
│   │                                       applies the step-07 selection (MODULE_PATTERNS = file table)
│   └── update_makrdown_test_spec_document.py   writes the table into test_specification.md
├── 03_map_text_to_function__keyword_library/
│   └── map_testcase_text_with_right_function_and_run_test_steps__keyword_library.py
│                                           step name → Python function (actions and checks)
├── 04_real_commands__app_driver/
│   ├── commands-to-interact-your-app_app_driver.py        pywinauto: start, click, type, keys, scroll…
│   └── write-down-every-executed-command_command_log.py   logs every command + explanation + file:line
├── 05_before_and_after__setup_teardown/
│   ├── backup_and_restore_user_data-and-settings__profile_guard.py   protects your Wave Pro data
│   ├── generate_and_delete_test_data__temp_music_library.py         60 silent WAV test files
│   └── definitions-of_begin-start_test-end_test- end_prepare-and-cleanup-every-test-as-unified-test-structure__session.py   before/after every test
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

**Renaming files:** the descriptive part of a name can be changed freely. Files are found by their
step-number folder (`02_…`, `03_…`) and the professional name at the END of the file name
(`…__spec_loader.py`, `…__keyword_library.py`, `…_app_driver.py`, `…_command_log.py`,
`…__profile_guard.py`, `…__temp_music_library.py`, `…__session.py`, `…__test_selection_popup.py`,
`…__robot_keywords.py`, `…_with_pytest.py`). Keep those endings. Names may contain `-` and spaces.
The `.bat` files name their files directly – rename those paths there too.

## Every test case is independent

Any single test, any selection or all tests can run – in any combination – with the same result:

- **Own test data:** a fresh temporary music library for every test case (deleted afterwards).
- **Own settings:** Wave Pro's settings are reset to "test library only" before every test case.
- **Own app:** Wave Pro is started fresh for every test case and closed afterwards.
- **Clean state:** before every test case, a Wave Pro left open by an earlier (failed) test is
  closed, and Ctrl / Shift / Alt / E / T are released – nothing can carry over.
- **Wave Pro in front:** before every click and every typed text, the test checks that Wave Pro
  is the active window and brings it to the front if Windows put another window in front
  (e.g. after the selection window closed). If that is impossible, the test stops with a clear
  message instead of clicking into the wrong window.
- **Your own Wave Pro must be closed:** checked once at the very start, before anything changes.

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
