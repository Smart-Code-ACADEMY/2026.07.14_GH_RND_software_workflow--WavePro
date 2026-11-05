# Test Specification – Wave Pro (Windows EXE)

| | |
|---|---|
| **Test object** | Wave Pro – Music Studio, EXE from `publish/` |
| **Test cases** | **`test_cases.yaml`** (this folder) – the only source. All three tools read it directly. |
| **This document** | Explains the setup, the tools and the limits. The table in section 3 is generated from `test_cases.yaml`. |

---

## 1. The path from test case to report

Every folder number is one step, in the order the test actually runs:

| Step | Folder | Plain words | Professional term |
|---|---|---|---|
| **01** | `01_what_to_test__test_specification` | *What* is tested | Test specification |
| **02** | `02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader` | Read the YAML specification, check it and convert it into Python data | Spec loader / validator |
| **03** | `03_map_text_to_function__keyword_library` | Map each step text of the YAML to its Python function | Keyword library (test steps) |
| **04** | `04_real_commands__app_driver` | The real commands: click, type, press keys, scroll, wait – each one logged | App driver (pywinauto) + command log |
| **05** | `05_before_and_after__setup_teardown` | Prepare before, clean up after, protect your data | Setup / teardown |
| **06** | `06_run_the_tests__test_runners` | Run with 6a pytest, 6b Robot Framework, 6c pywinauto only | Test runners |
| **07** | `07_choose_tests__test_selection` | Choose which test cases run (popup, can be saved) | Test selection |
| **08** | `08_results__reports` | Results of every tool, the command logs and the comparison | Reports |

Example – one line of the specification on its way through the steps:

```
01  test_cases.yaml       "Type In Search Box: Song 07"
02  yaml-to-dictionary-converting__spec_loader.py        checks: step name exists, one value given
03  map_testcase_text_with_right_function_and_run_test_steps__keyword_library.py    @step("Type In Search Box") → c.app.type_search("Song 07")
04  commands-to-interact-your-app_app_driver.py         find the Edit field → click_input() → type_keys("Song 07") → wait 0.5 s
05  definitions-of_begin-start_test-end_test- end_prepare-and-cleanup-every-test-as-unified-test-structure__session.py            (before: start the EXE with test data · after: close and clean up)
06  pytest / Robot / pywinauto only run it
07  report: PASS or FAIL with the failing step
```

All three tools share steps 02–05, so they **must** give the same results and run the
same commands. `08_results__reports/00_comparison_of_all_tools.html` proves both after every run.

**Command log:** every executed command is written – live in the terminal and in
`08_results__reports/<tool>/command_log.html` – one line each: left the exact command with its
result, right what it does in plain words. Every check shows the comparison it made
(e.g. `check: 'Song 07' == 'Song 07' -> OK`).

---

## 2. The tools

| No. | Tool | What it shows | Report |
|---|---|---|---|
| **6a** | **pytest** + pywinauto | Test framework for developers | `08_results__reports/6a_pytest/report.html`, `command_log.html` |
| **6b** | **Robot Framework** + pywinauto | Step-by-step log, good for teams and customers | `08_results__reports/6b_robot_framework/log.html`, `command_log.html` |
| **6c** | **pywinauto only** | No test framework: a small Python program runs the specification | `08_results__reports/6c_pywinauto_only/report.html`, `command_log.html` |

Not suitable: **Playwright** and **Selenium** – they only control web pages in a browser, not a Windows EXE.

---

## 3. The test cases (generated from `test_cases.yaml`)

Before **every** test case (step 05): a fresh temporary library (60 silent WAV files `Artist NN - Song NN` in `Pop/` and `Rock/`, empty folder `To-Do/`), start the EXE, wait until “60 songs” is loaded. After it: close the EXE, delete the temporary library.

<!-- AUTO-START: generated from test_cases.yaml – do not edit by hand -->
| ID | Principle | Actions (what the test does) | Expected result (what is checked) |
|---|---|---|---|
| **TC-01** Main window appears | Start / window | – | 1. Window Title Should Start With “Wave Pro - Music Studio”<br>2. Startup Time Should Be Below Seconds “30” |
| **TC-02** Labels are visible | Read texts | – | 1. Text Should Be Visible “60 songs”<br>2. Text Should Be Visible “Nothing is playing”<br>3. Button Should Exist “Play Filtered”<br>4. Button Should Exist “Reset filters”<br>5. Button Should Exist “+ To-Do” |
| **TC-03** Table shows the songs | Data in table | – | 1. Table Should Contain “Artist 01”<br>2. Table Should Contain “Song 01”<br>3. Table Should Contain “Artist 60”<br>4. Row Should Be In View “Artist 01” |
| **TC-04** Search filters the list | Type text | 1. Type In Search Box “Song 07” | 2. Search Box Should Contain “Song 07”<br>3. Row Should Be Shown “Song 07”<br>4. Row Should Be Hidden “Song 08” |
| **TC-05** Reset filters restores everything | Click a button | 1. Type In Search Box “Song 07”<br>3. Click Button “Reset filters” | 2. Row Should Be Hidden “Song 08”<br>4. Search Box Should Contain “”<br>5. Row Should Be Shown “Song 08” |
| **TC-06** To-Do creates a file | Dialog + file on disk | 1. Click Button “+ To-Do”<br>3. Type In Dialog “Add To-Do”, “TC06 Test Song”<br>4. Click In Dialog “Add To-Do”, “Create To-Do” | 2. Dialog Should Appear “Add To-Do”<br>5. Dialog Should Be Closed “Add To-Do”<br>6. File Should Exist “To-Do/TC06 Test Song.txt”, “To-Do: TC06 Test Song”<br>7. Table Should Contain “TC06 Test Song” |
| **TC-07** Shortcut opens dialog, Esc cancels | Keyboard shortcut | 1. Remember Number Of Text Files<br>2. Press Ctrl+E Plus “T”<br>4. Press Escape | 3. Dialog Should Appear “Add To-Do”<br>5. Dialog Should Be Closed “Add To-Do”<br>6. Number Of Text Files Should Be Unchanged |
| **TC-08** Scrolling with End, Top and mouse wheel | Scrolling | 2. Click Button “End”<br>5. Click Button “Top”<br>7. Scroll With Mouse Wheel “-10” | 1. Row Should Not Be In View “Artist 60”<br>3. Row Should Be In View “Artist 60”<br>4. Row Should Not Be In View “Artist 01”<br>6. Row Should Be In View “Artist 01”<br>8. Row Should Not Be In View “Artist 01” |
| **TC-09** Selection is blue in every column | Visual (pixels) | 1. Click Row “Artist 02”<br>2. Save Screenshot “tc09_selection.png” | 3. Row Should Be Blue In All Columns “Artist 02”<br>4. Row Should Not Be Blue “Artist 04” |
| **TC-10** Controls stay reachable | Window size | 2. Resize Window “900”, “600”<br>6. Maximize Window<br>11. Restore Window | 1. Window Should Fit On Screen<br>3. Button Should Be Inside Window “Reset filters”<br>4. Button Should Be Inside Window “End”<br>5. Button Should Be Inside Window “+ To-Do”<br>7. Window Should Be Maximized<br>8. Button Should Be On Screen “Reset filters”<br>9. Button Should Be On Screen “End”<br>10. Button Should Be On Screen “+ To-Do”<br>12. Window Should Not Be Maximized |
<!-- AUTO-END -->

---

## 4. What can be tested automatically – and what cannot?

| Feature | Testable? | Reason |
|---|---|---|
| Window, title, texts, buttons | ✅ | Qt reports name and type to Windows (UI Automation). |
| Search box, dialogs, keyboard shortcuts | ✅ | Real keyboard and mouse input. |
| Table content, filtering, scrolling | ✅ | Every visible text cell has a name and position. For rows scrolled out of view the test scrolls by itself. |
| Files on disk | ✅ | Python checks the file directly. |
| Colours and layout | ◐ | Only by measuring pixels (TC-09). Night light or HDR can interfere. |
| **Lock buttons, category drop-down, stars and 🗑 inside the table rows** | ◐ | Qt does **not** report these controls to Windows. Reachable only by clicking a calculated position – fragile. |
| Short notifications (toasts, 1.5–3 s) | ◐ | Possible, but timing-sensitive. |
| Sound is audible, VU meter animation | ❌ | A test cannot hear; moving graphics have no fixed values. |
| Global hotkeys while another app is active | ❌ | Depends on system rights and which app is in front. |

---

## 5. Test environment and protection of your data

- **PC:** Windows 10/11, Python 3.11. Wave Pro must be **closed**.
- **During the run:** do not use mouse and keyboard (all three tools: about 15 min).
- **Your data:**
  - Your real music is never touched.
  - Settings, change history and unfinished tasks are backed up before and restored exactly after the run – after a crash, at the start of the next run.

---

## 6. Limits and findings

- **Windows detail:** Qt only reports table rows that are visible on screen. “Table Should Contain” therefore scrolls through the list by itself and then back to the top.
- **TC-09** fails if the EXE was built before the selection colour fix.
- **TC-10** fails **on purpose** if the screen is narrower than about 1320 px (e.g. 1920 px at 150 % scaling) – Wave Pro is then wider than the screen, which is a real finding.
