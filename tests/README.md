# Wave Pro – automated tests

The folders are numbered in the order a test runs:
**01 what to test → 02 read → 03 translate → 04 real commands → 05 before/after → 06 run → 07 results.**

Test cases are defined in ONE place:
**`01_what_to_test__test_specification/test_cases.yaml`**.
Three tools read that file and must give the same results.

## Quick start (Windows)

1. **Close Wave Pro.**
2. Once, in the project folder: `pip install -r tests\requirements-tests.txt`
3. Start `tests\run_6_all_tools.bat`. Do not use mouse and keyboard for about 15 minutes.
4. At the end **`tests\07_results__reports\00_comparison_of_all_tools.html`** opens:
   all three tools side by side.

One tool only: `run_6a_pytest.bat`, `run_6b_robot_framework.bat` or `run_6c_pywinauto_only.bat`.
A different EXE than in `publish\`: `set WAVEPRO_EXE=C:\path\WavePro.exe`

## Folders

```
tests/
├── 01_what_to_test__test_specification/
│   ├── test_cases.yaml               ★ the test cases – edit tests only here
│   └── test_specification.md         explanation; its table is generated from the YAML
├── 02_read_the_spec__spec_loader/
│   ├── spec_loader.py                reads and checks test_cases.yaml
│   └── update_spec_document.py       writes the table into test_specification.md
├── 03_translate_steps__keyword_library/
│   └── keyword_library.py            step name → Python function (actions and checks)
├── 04_real_commands__app_driver/
│   ├── app_driver.py                 pywinauto: start, click, type, keys, scroll, wait, pixels
│   └── command_log.py                writes every executed command + a plain explanation
├── 05_before_and_after__setup_teardown/
│   ├── session.py                    before/after every test – shared by all tools
│   ├── temp_music_library.py         temporary test music (60 silent WAV files)
│   └── profile_backup.py             backs up and restores your Wave Pro data
├── 06_run_the_tests__test_runners/
│   ├── 6a_pytest/                    tool 1
│   ├── 6b_robot_framework/           tool 2
│   └── 6c_pywinauto_only/            tool 3 – no test framework
├── 07_results__reports/
│   ├── compare_results.py            creates 00_comparison_of_all_tools.html
│   ├── 00_comparison_of_all_tools.html   (generated)
│   ├── 6a_pytest/   6b_robot_framework/   6c_pywinauto_only/   (generated, each with command_log.html)
├── run_6_all_tools.bat   run_6a_pytest.bat   run_6b_robot_framework.bat   run_6c_pywinauto_only.bat
└── requirements-tests.txt
```

## Command log – every command, step by step

While the tests run, **every executed command** is printed in the terminal, one per line:
left the command exactly as executed (with its result), right what it does in plain words.

```
  STEP 1: Type In Search Box “Song 07”                                 | ACTION – does something in the app
      search_box.click_input()                                         | Click into the search box
      search_box.type_keys('Song 07', with_spaces=True, ...)           | TYPE the text 'Song 07' on the keyboard
      time.sleep(0.5)                                                  | Wait 0.5 s – let the list filter itself
  STEP 2: Search Box Should Contain “Song 07”                          | CHECK – compares with the expected result
      search_box.get_value()  -> 'Song 07'                             | Read the text in the search box
      check: 'Song 07' == 'Song 07'  -> OK                             | Is the text in the search box the expected one?
```

The same lines are saved for every tool in `07_results__reports/<tool>/command_log.html`
(also `.txt` and `.json`), and they appear inside pytest's `report.html` and Robot's `log.html`.
Polling loops ("check every 0.25 s until …") are one line with the number of tries.
`00_comparison_of_all_tools.html` also checks that all three tools ran the **same commands**.

## Change or add a test case

Edit `01_…/test_cases.yaml` (allowed step names: `03_…/keyword_library.py`) and start a run.
Spelling mistakes in step names are reported before anything starts.

## Safety

- Only a temporary test library is used; your music is never touched.
- Settings, change history and unfinished tasks are backed up and restored.
- If a run is interrupted, the next run restores the backup automatically.
