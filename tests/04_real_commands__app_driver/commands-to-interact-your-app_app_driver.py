"""STEP 04 – REAL COMMANDS  (app driver, pywinauto)

The functions of step 03 call the methods of this class. Here are the real
commands: start the EXE, find window/buttons/cells, click, type, press keys,
scroll, wait, take screenshots, measure pixels.

EVERY real command runs through `call(...)` from write-down-every-executed-command_command_log.py, so it is
written to the terminal and the reports – left the exact command, right a
plain-English explanation.

Technique: pywinauto with the "uia" backend (Windows UI Automation).
Wave Pro is a Qt application; Qt reports windows, buttons, texts and table
cells to Windows UI Automation, and pywinauto reads them.

Windows detail: Qt only reports table rows that are currently visible on
screen. Rows scrolled out of view or hidden by a filter are not reported.
"""
from __future__ import annotations

import ctypes
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from command_log import LOG, call

# ── Constants ───────────────────────────────────────────────────────────
TESTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = TESTS_DIR.parent

WINDOW_TITLE_START = "Wave Pro - Music Studio"
TITLE_RE = r"^Wave Pro - Music Studio.*"
SONG_COUNT = 60          # number of songs in the temporary test library

VK_SHIFT, VK_CONTROL, VK_MENU, VK_ESCAPE = 0x10, 0x11, 0x12, 0x1B
KEYEVENTF_KEYUP = 0x0002
SW_SHOW, SW_MAXIMIZE, SW_RESTORE = 5, 3, 9
KEY_NAMES = {VK_SHIFT: "Shift", VK_CONTROL: "Ctrl", VK_MENU: "Alt", VK_ESCAPE: "Esc"}


# ── Helpers ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Rect:
    """Screen rectangle in pixels."""
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def is_empty(self) -> bool:
        return self.width <= 0 or self.height <= 0

    def contains(self, other: "Rect", tolerance: int = 2) -> bool:
        return (other.left >= self.left - tolerance
                and other.top >= self.top - tolerance
                and other.right <= self.right + tolerance
                and other.bottom <= self.bottom + tolerance)

    @classmethod
    def from_pywinauto(cls, r) -> "Rect":
        return cls(int(r.left), int(r.top), int(r.right), int(r.bottom))


def wait_until(condition: Callable[[], bool], timeout: float = 10.0,
               interval: float = 0.25, code: str = "", what: str = "") -> bool:
    """Repeat `condition()` until it is True or the timeout passes.

    With `code`/`what` the whole loop is logged as ONE line (with the number
    of tries); the commands inside the loop are not logged one by one."""
    start, tries, result = time.monotonic(), 0, False
    with LOG.quiet():
        while True:
            tries += 1
            try:
                if condition():
                    result = True
                    break
            except Exception:
                pass
            if time.monotonic() - start >= timeout:
                break
            time.sleep(interval)
    if code:
        seconds = time.monotonic() - start
        LOG.command(f"wait_until(lambda: {code}, timeout={timeout}, interval={interval})",
                    f"Repeat every {interval} s until {what} (at most {timeout} s)",
                    f"{result} after {tries} tries ({seconds:.1f} s)")
    return result


def blue_ratio(image) -> float:
    """Share of 'blue' pixels (selection colour) in a PIL image, 0.0 – 1.0."""
    data = image.convert("RGB").tobytes()      # r,g,b,r,g,b,…
    total = len(data) // 3
    if total == 0:
        return 0.0
    blue = sum(1 for i in range(0, total * 3, 3)
               if data[i + 2] > data[i] + 40 and data[i + 2] > 90)
    return blue / total


# ── Find the EXE ────────────────────────────────────────────────────────
def find_exe() -> Path:
    """Find the Wave Pro EXE.

    Order: environment variable WAVEPRO_EXE → folder publish/ → project
    root. With several candidates, the one with 'wave' in its name wins."""
    env = os.environ.get("WAVEPRO_EXE", "").strip().strip('"')
    if env:
        p = Path(env)
        if p.is_file():
            LOG.command(f"os.environ['WAVEPRO_EXE']", "Use the EXE named in the environment variable",
                        repr(str(p)))
            return p.resolve()
        raise FileNotFoundError(f"WAVEPRO_EXE does not point to a file: {p}")

    for folder, pattern in ((PROJECT_DIR / "publish", "**/*.exe"),
                            (PROJECT_DIR, "*.exe")):
        if not folder.is_dir():
            continue
        found = sorted(folder.glob(pattern))
        wave_named = [p for p in found if "wave" in p.name.lower()]
        chosen = None
        if len(wave_named) == 1:
            chosen = wave_named[0]
        elif len(wave_named) > 1:
            raise RuntimeError(
                "Several Wave Pro EXE files found – please set WAVEPRO_EXE:\n  "
                + "\n  ".join(map(str, wave_named)))
        elif len(found) == 1:
            chosen = found[0]
        if chosen is not None:
            LOG.command(f"Path({str(folder)!r}).glob({pattern!r})",
                        "Search the folder for the Wave Pro EXE", repr(chosen.name))
            return chosen.resolve()
    raise FileNotFoundError(
        "No Wave Pro EXE found (publish/ or project root). "
        "Tip: set WAVEPRO_EXE=C:\\path\\WavePro.exe")


# ── The app driver ──────────────────────────────────────────────────────
def _make_dpi_aware() -> None:
    """Exact pixel coordinates even with Windows scaling (125 %, 150 % …)."""
    try:
        call("shcore", ctypes.windll.shcore, "SetProcessDpiAwareness", 2,
             explain="Use real screen pixels, also with Windows scaling (125 %, 150 %)")
    except Exception:
        try:
            call("user32", ctypes.windll.user32, "SetProcessDPIAware",
                 explain="Use real screen pixels (older Windows)")
        except Exception:
            pass


def _button_regex(name: str) -> str:
    # Some buttons have a symbol in front ("▶  Play Filtered", "⤓ End").
    return rf"^(?:.*\s)?{re.escape(name)}$"


def _user32():
    return ctypes.windll.user32


def _sleep(seconds: float, why: str) -> None:
    call("time", time, "sleep", seconds, explain=f"Wait {seconds} s – {why}")


def _same_window(a, b) -> bool:
    try:
        return (int(a or 0) & 0xFFFFFFFF) == (int(b or 0) & 0xFFFFFFFF) and bool(a)
    except (TypeError, ValueError):
        return False


# ── Clean state between tests (used by step 05) ─────────────────────────
def wave_pro_window_open() -> bool:
    """Is any Wave Pro main window open right now?"""
    desktop = call("pywinauto", __import__("pywinauto"), "Desktop", backend="uia",
                   explain="Connect to Windows UI Automation (sees all windows)")
    spec = call("desktop", desktop, "window", title_re=TITLE_RE,
                explain="Describe the Wave Pro main window (by its title)")
    return bool(call("window", spec, "exists", timeout=1, explain="Is a Wave Pro window open?"))


def force_close_wave_pro(exe_name: str) -> None:
    """Close a Wave Pro left over by an earlier test (never the user's own –
    the session checks at its start that the user's Wave Pro is closed)."""
    call("subprocess", subprocess, "run", ["taskkill", "/IM", exe_name, "/T", "/F"],
         capture_output=True, explain="Force-quit a Wave Pro left over by an earlier test")
    if not wait_until(lambda: not wave_pro_window_open(), timeout=15,
                      code="not wave_pro_window_open()", what="no Wave Pro window is open"):
        raise RuntimeError("A Wave Pro window from an earlier test could not be closed.")


def release_all_keys() -> None:
    """Release keys a failed test might have left pressed (Ctrl, Shift, Alt, E, T)."""
    for vk in (VK_CONTROL, VK_SHIFT, VK_MENU, ord("E"), ord("T")):
        call("user32", _user32(), "keybd_event", vk, 0, KEYEVENTF_KEYUP, 0,
             explain=f"Make sure the key {KEY_NAMES.get(vk, chr(vk))} is not held down")


class WaveProApp:
    """Starts, operates and inspects the Wave Pro EXE (one instance per test)."""

    def __init__(self, exe: Path, library: Path):
        self.exe = Path(exe)
        self.library = Path(library)
        self.proc: Optional[subprocess.Popen] = None
        self.win_spec = None      # pywinauto WindowSpecification
        self.win = None           # pywinauto wrapper
        self.startup_seconds: Optional[float] = None
        self._desktop = None
        self._table_spec = None   # the song table, remembered once found

    # ---------- Start / stop -------------------------------------------
    def start(self, timeout: float = 60.0) -> None:
        _make_dpi_aware()
        self._desktop = call("pywinauto", __import__("pywinauto"), "Desktop", backend="uia",
                             explain="Connect to Windows UI Automation (sees all windows)")
        old = call("desktop", self._desktop, "window", title_re=TITLE_RE,
                   explain="Describe the Wave Pro main window (by its title)")
        if call("window", old, "exists", timeout=1,
                explain="Is Wave Pro already open? (must not be)"):
            raise RuntimeError("Wave Pro is already running. Please close it first.")

        t0 = time.monotonic()
        self.proc = call("subprocess", subprocess, "Popen", [str(self.exe)],
                         cwd=str(self.exe.parent),
                         explain="START THE APPLICATION (Wave Pro EXE)")
        self.win_spec = call("desktop", self._desktop, "window", title_re=TITLE_RE,
                             explain="Describe the Wave Pro main window (by its title)")
        call("win_spec", self.win_spec, "wait", "visible", timeout=timeout,
             explain=f"Wait until the main window is visible (at most {timeout:.0f} s)")
        self.win = call("win_spec", self.win_spec, "wrapper_object",
                        explain="Get the main window as an object we can control")
        self.startup_seconds = time.monotonic() - t0
        LOG.command("time.monotonic() - t0", "Measure how long the start took",
                    f"{self.startup_seconds:.1f} s")

        if not self.wait_for_text(f"{SONG_COUNT} songs", timeout=timeout):
            raise TimeoutError("The test library was not loaded completely.")
        self.activate()

    # ---------- Bring a window to the front ----------------------------
    def activate(self) -> None:
        """Main window to the front – checked, not just hoped for."""
        call("win", self.win, "set_focus", explain="Ask Windows to give the main window the focus")
        self.bring_to_front(self.win.handle, "Wave Pro main window")

    def bring_to_front(self, hwnd: int, name: str) -> None:
        """Windows blocks programs from jumping in front ("foreground lock"),
        e.g. after the test-selection window closed. Then clicks and typing
        would land in another window. So: check which window is in front and,
        if needed, use the standard work-arounds – up to 5 tries."""
        user32 = _user32()
        if call("user32", user32, "IsIconic", hwnd, explain=f"Is the {name} minimized?"):
            call("user32", user32, "ShowWindow", hwnd, SW_RESTORE,
                 explain=f"Restore the minimized {name}")
        for attempt in range(1, 6):
            front = call("user32", user32, "GetForegroundWindow",
                         explain="Which window is in front (active) right now?")
            if _same_window(front, hwnd):
                LOG.check(f"GetForegroundWindow() == {name} (try {attempt})",
                          f"Is the {name} in front, so clicks and keys reach it?", True)
                return
            if attempt == 1:
                call("user32", user32, "SetForegroundWindow", hwnd,
                     explain=f"Bring the {name} to the front")
            elif attempt == 2:
                me = call("kernel32", ctypes.windll.kernel32, "GetCurrentThreadId",
                          explain="Our own thread (needed for the next command)")
                other = call("user32", user32, "GetWindowThreadProcessId", front, None,
                             explain="Thread of the window that is in front now")
                call("user32", user32, "AttachThreadInput", me, other, True,
                     explain="Share keyboard focus with the front window (allowed by Windows)")
                call("user32", user32, "SetForegroundWindow", hwnd,
                     explain=f"Bring the {name} to the front")
                call("user32", user32, "BringWindowToTop", hwnd,
                     explain=f"Put the {name} on top of all windows")
                call("user32", user32, "AttachThreadInput", me, other, False,
                     explain="Stop sharing keyboard focus again")
            else:
                call("user32", user32, "keybd_event", VK_MENU, 0, 0, 0,
                     explain="PRESS Alt (unlocks bringing a window to the front)")
                call("user32", user32, "SetForegroundWindow", hwnd,
                     explain=f"Bring the {name} to the front")
                call("user32", user32, "keybd_event", VK_MENU, 0, KEYEVENTF_KEYUP, 0,
                     explain="RELEASE Alt")
                call("user32", user32, "ShowWindow", hwnd, SW_SHOW,
                     explain=f"Show the {name}")
            _sleep(0.3, "let Windows switch the active window")
        LOG.check(f"GetForegroundWindow() == {name}",
                  f"Is the {name} in front, so clicks and keys reach it?", False)
        raise RuntimeError(f"The {name} could not be brought to the front – another window "
                           f"is in front. Clicks and typing would go to the wrong window.")

    def close(self) -> None:
        try:
            if self.win is not None:
                call("win", self.win, "close", explain="CLOSE THE APPLICATION (like clicking X)")
        except Exception:
            pass
        if self.proc is not None:
            try:
                call("proc", self.proc, "wait", timeout=20,
                     explain="Wait until the Wave Pro process has ended (at most 20 s)")
            except subprocess.TimeoutExpired:
                call("subprocess", subprocess, "run",
                     ["taskkill", "/PID", str(self.proc.pid), "/T", "/F"], capture_output=True,
                     explain="Force-quit Wave Pro (it did not close by itself)")
        # PyInstaller "onefile": the window belongs to a child process.
        if self._desktop is not None:
            leftover = call("desktop", self._desktop, "window", title_re=TITLE_RE,
                            explain="Describe the Wave Pro main window (by its title)")
            if call("window", leftover, "exists", timeout=2,
                    explain="Is a Wave Pro window still open?"):
                call("subprocess", subprocess, "run",
                     ["taskkill", "/IM", self.exe.name, "/T", "/F"], capture_output=True,
                     explain="Force-quit the remaining Wave Pro process")
        self.win = None

    # ---------- Window -------------------------------------------------
    def window_title(self) -> str:
        return call("win", self.win, "window_text", explain="Read the window title")

    def window_rect(self) -> Rect:
        return Rect.from_pywinauto(call("win", self.win, "rectangle",
                                        explain="Read position and size of the window"))

    def screen_rect(self) -> Rect:
        user32 = _user32()
        x = call("user32", user32, "GetSystemMetrics", 76, explain="Screen area: left edge (all monitors)")
        y = call("user32", user32, "GetSystemMetrics", 77, explain="Screen area: top edge")
        w = call("user32", user32, "GetSystemMetrics", 78, explain="Screen area: width")
        h = call("user32", user32, "GetSystemMetrics", 79, explain="Screen area: height")
        return Rect(x, y, x + w, y + h)

    def resize_window(self, width: int, height: int) -> None:
        user32 = _user32()
        call("user32", user32, "ShowWindow", self.win.handle, SW_RESTORE,
             explain="Make sure the window is not maximized")
        call("user32", user32, "MoveWindow", self.win.handle, 40, 40, width, height, True,
             explain=f"Move the window to (40, 40) and resize it to {width} x {height} pixels")
        _sleep(1.0, "let the layout adjust")

    def maximize(self) -> None:
        call("user32", _user32(), "ShowWindow", self.win.handle, SW_MAXIMIZE,
             explain="Maximize the window (full screen)")
        _sleep(1.0, "let the layout adjust")

    def restore(self) -> None:
        call("user32", _user32(), "ShowWindow", self.win.handle, SW_RESTORE,
             explain="Restore the window to normal size")
        _sleep(1.0, "let the layout adjust")

    def is_maximized(self) -> bool:
        return bool(call("user32", _user32(), "IsZoomed", self.win.handle,
                         explain="Ask Windows: is the window maximized?"))

    # ---------- Texts & buttons ----------------------------------------
    def text_exists(self, text: str) -> bool:
        spec = call("win_spec", self.win_spec, "child_window", title=text, control_type="Text",
                    explain=f"Describe a text label '{text}'")
        return call("label", spec, "exists", timeout=0,
                    explain=f"Is the text '{text}' in the window?")

    def wait_for_text(self, text: str, timeout: float = 10.0) -> bool:
        return wait_until(lambda: self.text_exists(text), timeout,
                          code=f"text_exists({text!r})", what=f"the text '{text}' is shown")

    def _button(self, name: str):
        return call("win_spec", self.win_spec, "child_window",
                    title_re=_button_regex(name), control_type="Button",
                    explain=f"Describe the button '{name}'")

    def button_exists(self, name: str) -> bool:
        return call("button", self._button(name), "exists", timeout=2,
                    explain=f"Is the button '{name}' in the window? (wait up to 2 s)")

    def button_rect(self, name: str) -> Rect:
        button = call("button", self._button(name), "wrapper_object",
                      explain=f"Find the button '{name}'")
        return Rect.from_pywinauto(call("button", button, "rectangle",
                                        explain=f"Read position and size of '{name}'"))

    def click_button(self, name: str) -> None:
        self.activate()
        button = call("button", self._button(name), "wrapper_object",
                      explain=f"Find the button '{name}'")
        call("button", button, "click_input",
             explain=f"CLICK the button '{name}' with the real mouse")
        _sleep(0.4, "let the app react to the click")

    # ---------- Search box ---------------------------------------------
    def _search_box(self):
        # The only text input in the main window (it has no name of its own).
        spec = call("win_spec", self.win_spec, "child_window", control_type="Edit", found_index=0,
                    explain="Describe the search box (the only text field in the window)")
        return call("search_box", spec, "wrapper_object", explain="Find the search box")

    def type_search(self, text: str) -> None:
        self.activate()
        box = self._search_box()
        call("search_box", box, "click_input", explain="Click into the search box")
        call("search_box", box, "type_keys", text, with_spaces=True, set_foreground=True,
             explain=f"TYPE the text '{text}' on the keyboard")
        _sleep(0.5, "let the list filter itself")

    def search_value(self) -> str:
        box = self._search_box()
        for owner, method, explain in (
                ("search_box", "get_value", "Read the text in the search box"),
                ("search_box.iface_text.DocumentRange", "GetText",
                 "Read the text in the search box (second way)"),
                ("search_box", "legacy_properties", "Read the text in the search box (third way)")):
            try:
                if method == "GetText":
                    value = call(owner, box.iface_text.DocumentRange, "GetText", -1, explain=explain)
                elif method == "legacy_properties":
                    value = call(owner, box, method, explain=explain).get("Value", "")
                else:
                    value = call(owner, box, method, explain=explain)
                if value is not None:
                    return str(value)
            except Exception:
                continue
        return ""

    # ---------- Table --------------------------------------------------
    def _table(self):
        if self._table_spec is not None:          # found before – the table never changes
            return self._table_spec
        for control_type in ("Table", "DataGrid"):
            spec = call("win_spec", self.win_spec, "child_window", control_type=control_type,
                        explain=f"Describe the song table (type {control_type})")
            if call("table", spec, "exists", timeout=0, explain="Is the song table there?"):
                self._table_spec = spec
                return spec
        raise LookupError("Song table not found.")

    def table_rect(self) -> Rect:
        table = call("table", self._table(), "wrapper_object", explain="Find the song table")
        return Rect.from_pywinauto(call("table", table, "rectangle",
                                        explain="Read position and size of the table"))

    def _cell(self, text: str):
        # Windows: Qt only reports rows currently visible on screen.
        # Rows scrolled away or hidden by a filter are missing here.
        return call("table", self._table(), "child_window", title=text, visible_only=False,
                    explain=f"Describe the table cell '{text}'")

    def cell_rect(self, text: str) -> Optional[Rect]:
        """Position of the cell in the CURRENTLY visible area, otherwise None."""
        spec = self._cell(text)
        if not call("cell", spec, "exists", timeout=0,
                    explain=f"Is the cell '{text}' visible right now?"):
            return None
        cell = call("cell", spec, "wrapper_object", explain=f"Find the cell '{text}'")
        return Rect.from_pywinauto(call("cell", cell, "rectangle",
                                        explain=f"Read position and size of '{text}'"))

    def _visible_cell_names(self) -> tuple:
        """Names of the currently visible cells (used to detect the list end)."""
        table = call("table", self._table(), "wrapper_object", explain="Find the song table")
        children = call("table", table, "children", explain="List all visible cells of the table")
        return tuple(c.window_text() for c in children)

    def cell_exists(self, text: str) -> bool:
        """Is the text anywhere in the table? Scrolls through the whole list
        if needed, then back to the top."""
        if wait_until(lambda: self.cell_rect(text) is not None, timeout=2,
                      code=f"cell_rect({text!r}) is not None",
                      what=f"the cell '{text}' is visible"):
            return True
        LOG.command("# not visible → scroll through the list", f"Look for '{text}' further down")
        try:
            self.scroll_table_to_top()
            previous = None
            for round_no in range(1, 201):
                LOG.command(f"# search round {round_no}", "Next part of the list")
                if self.cell_rect(text) is not None:
                    return True
                current = self._visible_cell_names()
                if current == previous:                   # end of list reached
                    LOG.command("current == previous", "The list did not move: end reached", "True")
                    return False
                previous = current
                self.wheel_scroll_table(-3)               # 3 notches down
            return False
        finally:
            self.scroll_table_to_top()                    # back to the top

    def scroll_table_to_top(self) -> None:
        """Scroll up in small steps until nothing moves any more.
        (One mouse-wheel event scrolls at most one page.)"""
        previous = None
        for _ in range(200):
            current = self._visible_cell_names()
            if current == previous:
                LOG.command("current == previous", "The list did not move: top reached", "True")
                return
            previous = current
            self.wheel_scroll_table(+5)

    def is_row_shown(self, text: str) -> bool:
        """Row is not hidden by a filter (hidden rows have no area)."""
        r = self.cell_rect(text)
        return r is not None and not r.is_empty

    def is_row_in_view(self, text: str) -> bool:
        """Row lies inside the visible area of the table (not scrolled away)."""
        r = self.cell_rect(text)
        return r is not None and not r.is_empty and self.table_rect().contains(r)

    def wheel_scroll_table(self, notches: int) -> None:
        """Mouse wheel over the table; negative number = down."""
        self.activate()
        table = call("table", self._table(), "wrapper_object", explain="Find the song table")
        # coords=(None, None) → centre of the table (pywinauto uses relative coords).
        call("table", table, "wheel_mouse_input", wheel_dist=notches,
             explain=f"SCROLL the mouse wheel {abs(notches)} notches "
                     f"{'down' if notches < 0 else 'up'} over the table")
        _sleep(0.6, "let the list scroll")

    def click_row(self, text: str) -> None:
        self.activate()
        cell = call("cell", self._cell(text), "wrapper_object", explain=f"Find the cell '{text}'")
        call("cell", cell, "click_input", explain=f"CLICK the row '{text}' (selects it)")
        self._park_mouse()

    def _park_mouse(self) -> None:
        """Move the mouse away from the table (no tooltips/hover in screenshots)."""
        from pywinauto import mouse
        w = self.window_rect()
        call("mouse", mouse, "move", coords=(w.left + 60, w.top + 45),
             explain="Move the mouse to the window header (away from the table)")
        _sleep(0.5, "let hover effects disappear")

    def _row_cells(self, text: str) -> List[Rect]:
        anchor = self.cell_rect(text)
        if anchor is None or anchor.is_empty:
            raise LookupError(f"Row '{text}' is not visible.")
        table = call("table", self._table(), "wrapper_object", explain="Find the song table")
        children = call("table", table, "children", explain="List all visible cells of the table")
        cells = []
        with LOG.quiet():
            for child in children:
                r = Rect.from_pywinauto(child.rectangle())
                if (r.top == anchor.top and r.height == anchor.height
                        and r.left >= anchor.left and not r.is_empty):
                    cells.append(r)
        LOG.command(f"[cell.rectangle() for cell in children if same row as '{text}']",
                    "Find all cells (columns) of this row", f"{len(cells)} columns")
        return sorted(cells, key=lambda c: c.left)

    def row_blue_ratios(self, text: str) -> List[float]:
        """For each column of the row: share of blue pixels (selection colour)."""
        from PIL import ImageGrab
        ratios = []
        for column, c in enumerate(self._row_cells(text), start=1):
            box = (c.left + 3, c.top + 3, c.right - 3, c.bottom - 3)
            image = call("ImageGrab", ImageGrab, "grab", bbox=box, all_screens=True,
                         explain=f"Take a picture of column {column} of row '{text}'")
            ratio = blue_ratio(image)
            LOG.command(f"blue_ratio(image)", f"Share of blue pixels in column {column}",
                        f"{ratio:.2f}")
            ratios.append(ratio)
        return ratios

    def screenshot(self, path: Path) -> Path:
        from PIL import ImageGrab
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        w = self.window_rect()
        image = call("ImageGrab", ImageGrab, "grab", bbox=(w.left, w.top, w.right, w.bottom),
                     all_screens=True, explain="Take a SCREENSHOT of the Wave Pro window")
        call("image", image, "save", path, explain=f"Save the screenshot as {path.name}")
        return path

    # ---------- Dialogs ------------------------------------------------
    def _find_dialog(self, title: str):
        """Find a VISIBLE dialog. (exists() would also find hidden ones –
        Qt only hides closed dialogs instead of deleting them.)"""
        from pywinauto import findwindows
        searches = (
            dict(top_level_only=True),                       # own top-level window
            dict(top_level_only=False, control_type="Window",  # below the main window
                 parent=self.win.element_info),
        )
        for extra in searches:
            try:
                found = call("findwindows", findwindows, "find_elements",
                             title=title, backend="uia", visible_only=True, **extra,
                             explain=f"Search for a visible dialog '{title}'")
            except Exception:
                found = []
            for elem in found:
                if elem.handle:
                    return call("desktop", self._desktop, "window", handle=elem.handle,
                                explain=f"Take the dialog '{title}' by its window handle")
        return None

    def wait_for_dialog(self, title: str, timeout: float = 10.0) -> bool:
        return wait_until(lambda: self._find_dialog(title) is not None, timeout,
                          code=f"find_dialog({title!r}) is not None",
                          what=f"the dialog '{title}' is open")

    def wait_dialog_closed(self, title: str, timeout: float = 10.0) -> bool:
        return wait_until(lambda: self._find_dialog(title) is None, timeout,
                          code=f"find_dialog({title!r}) is None",
                          what=f"the dialog '{title}' is closed")

    def _activate_dialog(self, title: str):
        dialog = self._find_dialog(title)
        if dialog is None:
            raise LookupError(f"The dialog '{title}' is not open.")
        self.bring_to_front(dialog.criteria[0]["handle"], f"dialog '{title}'")
        return dialog

    def dialog_type(self, title: str, text: str) -> None:
        dialog = self._activate_dialog(title)
        spec = call("dialog", dialog, "child_window", control_type="Edit", found_index=0,
                    explain=f"Describe the text field in '{title}'")
        box = call("dialog_field", spec, "wrapper_object", explain="Find the text field")
        call("dialog_field", box, "click_input", explain="Click into the text field")
        call("dialog_field", box, "type_keys", text, with_spaces=True, set_foreground=True,
             explain=f"TYPE the text '{text}' on the keyboard")
        _sleep(0.3, "let the dialog take the text")

    def dialog_click(self, title: str, button: str) -> None:
        dialog = self._activate_dialog(title)
        spec = call("dialog", dialog, "child_window", title=button, control_type="Button",
                    explain=f"Describe the button '{button}' in '{title}'")
        target = call("dialog_button", spec, "wrapper_object", explain=f"Find the button '{button}'")
        call("dialog_button", target, "click_input",
             explain=f"CLICK the button '{button}' with the real mouse")
        _sleep(0.4, "let the app react to the click")

    # ---------- Keyboard -----------------------------------------------
    @staticmethod
    def _key(vk: int, up: bool = False) -> None:
        name = KEY_NAMES.get(vk, chr(vk))
        call("user32", _user32(), "keybd_event", vk, 0, KEYEVENTF_KEYUP if up else 0, 0,
             explain=f"{'RELEASE' if up else 'PRESS'} the key {name}")
        time.sleep(0.06)

    def press_ctrl_e_plus(self, letter: str) -> None:
        """Wave Pro shortcut: hold Ctrl + E, then tap a letter."""
        self.activate()
        vk = ord(letter.upper())
        for k in (VK_CONTROL, ord("E")):
            self._key(k)
        self._key(vk)
        self._key(vk, up=True)
        for k in (ord("E"), VK_CONTROL):
            self._key(k, up=True)
        _sleep(0.4, "let the app react to the shortcut")

    def press_escape(self) -> None:
        self._key(VK_ESCAPE)
        self._key(VK_ESCAPE, up=True)
        _sleep(0.4, "let the app react to Esc")

    # ---------- Files in the test library ------------------------------
    def library_files(self, pattern: str = "**/*") -> List[Path]:
        files = sorted(p for p in self.library.glob(pattern) if p.is_file())
        LOG.command(f"library.glob({pattern!r})", "List the files in the test library",
                    f"{len(files)} files")
        return files
