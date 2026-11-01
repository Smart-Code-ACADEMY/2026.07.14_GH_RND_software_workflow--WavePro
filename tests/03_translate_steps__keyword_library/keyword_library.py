"""STEP 03 – TRANSLATE STEPS INTO ACTIONS  (keyword library)

Every step name used in 01_what_to_test__test_specification/test_cases.yaml
is translated HERE into a Python function. Each function calls the real
commands of step 04 (app_driver.py).

All three tools (6a pytest, 6b Robot Framework, 6c pywinauto only) run steps
through `execute_step(...)` below – so a step behaves identically everywhere
and is logged identically (step header + every command + every comparison).

Add a new step: write a function and put @step("Step Name") above it.
Name contains "Should" → CHECK (expected result), otherwise → ACTION.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from app_driver import WaveProApp
from command_log import LOG


@dataclass
class Context:
    """What a step needs: the running app, the report folder, a small memory."""
    app: WaveProApp
    report_dir: Optional[Path] = None
    memory: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Keyword:
    name: str
    function: Callable
    value_count: int

    @property
    def is_check(self) -> bool:
        return "should" in self.name.lower()


KEYWORDS: Dict[str, Keyword] = {}


def _key(name: str) -> str:
    """Like Robot Framework: upper/lower case and spaces do not matter."""
    return "".join(name.lower().split())


def step(name: str):
    def register(fn):
        count = len(inspect.signature(fn).parameters) - 1     # without "c"
        KEYWORDS[_key(name)] = Keyword(name, fn, count)
        return fn
    return register


def find_keyword(name: str) -> Keyword:
    keyword = KEYWORDS.get(_key(name))
    if keyword is None:
        raise KeyError(f"Unknown step: '{name}'")
    return keyword


def readable(name: str, values) -> str:
    if not values:
        return name
    return name + " " + ", ".join(f"“{v}”" for v in values)


def execute_step(context: Context, name: str, values) -> object:
    """Run ONE step of the specification – used by all three tools."""
    keyword = find_keyword(name)
    LOG.step(readable(keyword.name, values), keyword.is_check)
    return keyword.function(context, *values)


def _check(ok: bool, expression: str, explanation: str, message: str) -> None:
    """Log the comparison, then fail with `message` if it is not true."""
    LOG.check(expression, explanation, bool(ok))
    if not ok:
        raise AssertionError(message)


# ═══════════════════════════ ACTIONS ═══════════════════════════════════
@step("Click Button")
def _(c, name):
    c.app.click_button(name)


@step("Type In Search Box")
def _(c, text):
    c.app.type_search(text)


@step("Type In Dialog")
def _(c, dialog_title, text):
    c.app.dialog_type(dialog_title, text)


@step("Click In Dialog")
def _(c, dialog_title, button):
    c.app.dialog_click(dialog_title, button)


@step("Press Ctrl+E Plus")
def _(c, letter):
    c.app.press_ctrl_e_plus(letter)


@step("Press Escape")
def _(c):
    c.app.press_escape()


@step("Scroll With Mouse Wheel")
def _(c, notches):
    c.app.wheel_scroll_table(int(notches))


@step("Click Row")
def _(c, text):
    c.app.click_row(text)


@step("Save Screenshot")
def _(c, file_name):
    folder = (c.report_dir or Path.cwd()) / "screenshots"
    c.memory["screenshot"] = c.app.screenshot(folder / file_name)


@step("Resize Window")
def _(c, width, height):
    c.app.resize_window(int(width), int(height))


@step("Maximize Window")
def _(c):
    c.app.maximize()


@step("Restore Window")
def _(c):
    c.app.restore()


@step("Remember Number Of Text Files")
def _(c):
    c.memory["txt_count"] = len(c.app.library_files("**/*.txt"))
    LOG.command(f"memory['txt_count'] = {c.memory['txt_count']}",
                "Remember the number for a later comparison")


# ═══════════════════════════ CHECKS ════════════════════════════════════
@step("Window Title Should Start With")
def _(c, text):
    title = c.app.window_title()
    _check(title.startswith(text), f"{title!r}.startswith({text!r})",
           "Does the window title start with the expected text?",
           f"Window title is '{title}'")


@step("Startup Time Should Be Below Seconds")
def _(c, seconds):
    t = c.app.startup_seconds
    _check(t < float(seconds), f"{t:.1f} < {float(seconds)}",
           "Was the start faster than the limit?", f"Startup took {t:.1f} s")


@step("Text Should Be Visible")
def _(c, text):
    found = c.app.text_exists(text)
    _check(found, f"text_exists({text!r}) == True", "Is the text on the screen?",
           f"Text not found: '{text}'")


@step("Button Should Exist")
def _(c, name):
    found = c.app.button_exists(name)
    _check(found, f"button_exists({name!r}) == True", "Is the button in the window?",
           f"Button not found: '{name}'")


@step("Table Should Contain")
def _(c, text):
    found = c.app.cell_exists(text)
    _check(found, f"cell_exists({text!r}) == True", "Is the text somewhere in the table?",
           f"Table cell not found: '{text}'")


@step("Row Should Be Shown")
def _(c, text):
    shown = c.app.is_row_shown(text)
    _check(shown, f"is_row_shown({text!r}) == True", "Is the row shown (not filtered out)?",
           f"Row is hidden: '{text}'")


@step("Row Should Be Hidden")
def _(c, text):
    shown = c.app.is_row_shown(text)
    _check(not shown, f"is_row_shown({text!r}) == False", "Is the row filtered out?",
           f"Row is still shown: '{text}'")


@step("Row Should Be In View")
def _(c, text):
    in_view = c.app.is_row_in_view(text)
    _check(in_view, f"is_row_in_view({text!r}) == True",
           "Is the row inside the visible part of the table?",
           f"Row is not in the visible area: '{text}'")


@step("Row Should Not Be In View")
def _(c, text):
    in_view = c.app.is_row_in_view(text)
    _check(not in_view, f"is_row_in_view({text!r}) == False",
           "Is the row outside the visible part (scrolled away)?",
           f"Row is in the visible area: '{text}'")


@step("Search Box Should Contain")
def _(c, text):
    value = c.app.search_value()
    _check(value == text, f"{value!r} == {text!r}",
           "Is the text in the search box the expected one?",
           f"Search box contains '{value}', expected '{text}'")


@step("Dialog Should Appear")
def _(c, dialog_title):
    open_ = c.app.wait_for_dialog(dialog_title)
    _check(open_, f"dialog {dialog_title!r} is open", "Did the dialog appear?",
           f"Dialog did not appear: '{dialog_title}'")


@step("Dialog Should Be Closed")
def _(c, dialog_title):
    closed = c.app.wait_dialog_closed(dialog_title)
    _check(closed, f"dialog {dialog_title!r} is closed", "Did the dialog close?",
           f"Dialog is still open: '{dialog_title}'")


@step("File Should Exist")
def _(c, relative_path, starts_with):
    file = c.app.library / relative_path
    exists = file.is_file()
    _check(exists, f"Path({str(file)!r}).is_file() == True",
           "Does the file exist on the disk?", f"File not found: {relative_path}")
    content = file.read_text(encoding="utf-8")
    _check(content.startswith(starts_with), f"{content[:40]!r}.startswith({starts_with!r})",
           "Does the file contain the expected text?",
           f"Content of {relative_path} is '{content[:40]}'")


@step("Number Of Text Files Should Be Unchanged")
def _(c):
    now = len(c.app.library_files("**/*.txt"))
    before = c.memory.get("txt_count")
    _check(before is not None, "memory['txt_count'] is set",
           "Was the number remembered before?",
           "'Remember Number Of Text Files' was not run before")
    _check(now == before, f"{now} == {before}", "Same number of .txt files as before?",
           f"Before {before}, now {now} .txt files")


@step("Row Should Be Blue In All Columns")
def _(c, text):
    ratios = [round(r, 2) for r in c.app.row_blue_ratios(text)]
    _check(len(ratios) >= 8, f"{len(ratios)} >= 8", "Were all 8 columns found?",
           f"Only {len(ratios)} columns found")
    _check(all(r >= 0.5 for r in ratios), f"all(r >= 0.5 for r in {ratios})",
           "Is every column at least half blue?",
           f"Not blue everywhere (share per column): {ratios}")


@step("Row Should Not Be Blue")
def _(c, text):
    ratios = [round(r, 2) for r in c.app.row_blue_ratios(text)]
    _check(all(r < 0.1 for r in ratios), f"all(r < 0.1 for r in {ratios})",
           "Is the row NOT blue (not selected)?",
           f"Row is blue (share per column): {ratios}")


@step("Window Should Fit On Screen")
def _(c):
    window, screen = c.app.window_rect(), c.app.screen_rect()
    _check(screen.contains(window, tolerance=10), f"screen {screen} contains window {window}",
           "Does the whole window fit on the screen?",
           f"Window {window} is larger than the screen {screen}")


@step("Button Should Be Inside Window")
def _(c, name):
    window, button = c.app.window_rect(), c.app.button_rect(name)
    _check(window.contains(button), f"window {window} contains button {button}",
           f"Is '{name}' fully inside the window?", f"'{name}' is outside the window")


@step("Button Should Be On Screen")
def _(c, name):
    screen, button = c.app.screen_rect(), c.app.button_rect(name)
    _check(screen.contains(button), f"screen {screen} contains button {button}",
           f"Is '{name}' fully on the screen?", f"'{name}' is outside the screen")


@step("Window Should Be Maximized")
def _(c):
    maximized = c.app.is_maximized()
    _check(maximized, f"is_maximized() == True", "Is the window maximized?",
           "Window is not maximized")


@step("Window Should Not Be Maximized")
def _(c):
    maximized = c.app.is_maximized()
    _check(not maximized, f"is_maximized() == False", "Is the window back to normal size?",
           "Window is still maximized")
