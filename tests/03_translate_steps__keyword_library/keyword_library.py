"""STEP 03 – TRANSLATE STEPS INTO ACTIONS  (keyword library)

Every step name used in 01_what_to_test__test_specification/test_cases.yaml
is translated HERE into a Python function. Each function calls the real
commands of step 04 (app_driver.py).

All three tools (6a pytest, 6b Robot Framework, 6c pywinauto only) use this
one dictionary – so a step behaves identically in every tool.

Add a new step: write a function and put @step("Step Name") above it.
Name contains "Should" → CHECK (expected result), otherwise → ACTION.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from app_driver import WaveProApp


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


def _check(condition: bool, message: str) -> None:
    if not condition:
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


# ═══════════════════════════ CHECKS ════════════════════════════════════
@step("Window Title Should Start With")
def _(c, text):
    title = c.app.window_title()
    _check(title.startswith(text), f"Window title is '{title}'")


@step("Startup Time Should Be Below Seconds")
def _(c, seconds):
    t = c.app.startup_seconds
    _check(t < float(seconds), f"Startup took {t:.1f} s")


@step("Text Should Be Visible")
def _(c, text):
    _check(c.app.text_exists(text), f"Text not found: '{text}'")


@step("Button Should Exist")
def _(c, name):
    _check(c.app.button_exists(name), f"Button not found: '{name}'")


@step("Table Should Contain")
def _(c, text):
    _check(c.app.cell_exists(text), f"Table cell not found: '{text}'")


@step("Row Should Be Shown")
def _(c, text):
    _check(c.app.is_row_shown(text), f"Row is hidden: '{text}'")


@step("Row Should Be Hidden")
def _(c, text):
    _check(not c.app.is_row_shown(text), f"Row is still shown: '{text}'")


@step("Row Should Be In View")
def _(c, text):
    _check(c.app.is_row_in_view(text), f"Row is not in the visible area: '{text}'")


@step("Row Should Not Be In View")
def _(c, text):
    _check(not c.app.is_row_in_view(text), f"Row is in the visible area: '{text}'")


@step("Search Box Should Contain")
def _(c, text):
    value = c.app.search_value()
    _check(value == text, f"Search box contains '{value}', expected '{text}'")


@step("Dialog Should Appear")
def _(c, dialog_title):
    _check(c.app.wait_for_dialog(dialog_title), f"Dialog did not appear: '{dialog_title}'")


@step("Dialog Should Be Closed")
def _(c, dialog_title):
    _check(c.app.wait_dialog_closed(dialog_title), f"Dialog is still open: '{dialog_title}'")


@step("File Should Exist")
def _(c, relative_path, starts_with):
    file = c.app.library / relative_path
    _check(file.is_file(), f"File not found: {relative_path}")
    content = file.read_text(encoding="utf-8")
    _check(content.startswith(starts_with),
           f"Content of {relative_path} is '{content[:40]}'")


@step("Number Of Text Files Should Be Unchanged")
def _(c):
    now = len(c.app.library_files("**/*.txt"))
    before = c.memory.get("txt_count")
    _check(before is not None, "'Remember Number Of Text Files' was not run before")
    _check(now == before, f"Before {before}, now {now} .txt files")


@step("Row Should Be Blue In All Columns")
def _(c, text):
    ratios = c.app.row_blue_ratios(text)
    _check(len(ratios) >= 8, f"Only {len(ratios)} columns found")
    _check(all(r >= 0.5 for r in ratios),
           f"Not blue everywhere (share per column): {[round(r, 2) for r in ratios]}")


@step("Row Should Not Be Blue")
def _(c, text):
    ratios = c.app.row_blue_ratios(text)
    _check(all(r < 0.1 for r in ratios),
           f"Row is blue (share per column): {[round(r, 2) for r in ratios]}")


@step("Window Should Fit On Screen")
def _(c):
    window, screen = c.app.window_rect(), c.app.screen_rect()
    _check(screen.contains(window, tolerance=10),
           f"Window {window} is larger than the screen {screen}")


@step("Button Should Be Inside Window")
def _(c, name):
    _check(c.app.window_rect().contains(c.app.button_rect(name)),
           f"'{name}' is outside the window")


@step("Button Should Be On Screen")
def _(c, name):
    _check(c.app.screen_rect().contains(c.app.button_rect(name)),
           f"'{name}' is outside the screen")


@step("Window Should Be Maximized")
def _(c):
    _check(c.app.is_maximized(), "Window is not maximized")


@step("Window Should Not Be Maximized")
def _(c):
    _check(not c.app.is_maximized(), "Window is still maximized")
