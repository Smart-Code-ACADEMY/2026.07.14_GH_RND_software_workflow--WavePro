"""STEP 04 – REAL COMMANDS  (app driver, pywinauto)

The functions of step 03 call the methods of this class. Here are the real
commands: start the EXE, find window/buttons/cells, click, type, press keys,
scroll, wait, take screenshots, measure pixels.

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

# ── Constants ───────────────────────────────────────────────────────────
TESTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = TESTS_DIR.parent

WINDOW_TITLE_START = "Wave Pro - Music Studio"
TITLE_RE = r"^Wave Pro - Music Studio.*"
SONG_COUNT = 60          # number of songs in the temporary test library

VK_CONTROL, VK_ESCAPE = 0x11, 0x1B
KEYEVENTF_KEYUP = 0x0002
SW_MAXIMIZE, SW_RESTORE = 3, 9


# ── Helpers ──────────────────────────────────────────────────────────
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
               interval: float = 0.25) -> bool:
    """Repeat `condition()` until it is True or the timeout passes."""
    end = time.monotonic() + timeout
    while True:
        try:
            if condition():
                return True
        except Exception:
            pass
        if time.monotonic() >= end:
            return False
        time.sleep(interval)


def blue_ratio(image) -> float:
    """Share of 'blue' pixels (selection colour) in a PIL image, 0.0 – 1.0."""
    data = image.convert("RGB").tobytes()      # r,g,b,r,g,b,…
    total = len(data) // 3
    if total == 0:
        return 0.0
    blue = sum(1 for i in range(0, total * 3, 3)
               if data[i + 2] > data[i] + 40 and data[i + 2] > 90)
    return blue / total


# ── Find the EXE ──────────────────────────────────────────────────────────
def find_exe() -> Path:
    """Find the Wave Pro EXE.

    Order: environment variable WAVEPRO_EXE → folder publish/ → project
    root. With several candidates, the one with 'wave' in its name wins."""
    env = os.environ.get("WAVEPRO_EXE", "").strip().strip('"')
    if env:
        p = Path(env)
        if p.is_file():
            return p.resolve()
        raise FileNotFoundError(f"WAVEPRO_EXE does not point to a file: {p}")

    for folder, pattern in ((PROJECT_DIR / "publish", "**/*.exe"),
                            (PROJECT_DIR, "*.exe")):
        if not folder.is_dir():
            continue
        found = sorted(folder.glob(pattern))
        wave_named = [p for p in found if "wave" in p.name.lower()]
        if len(wave_named) == 1:
            return wave_named[0].resolve()
        if len(wave_named) > 1:
            raise RuntimeError(
                "Several Wave Pro EXE files found – please set WAVEPRO_EXE:\n  "
                + "\n  ".join(map(str, wave_named)))
        if len(found) == 1:
            return found[0].resolve()
    raise FileNotFoundError(
        "No Wave Pro EXE found (publish/ or project root). "
        "Tip: set WAVEPRO_EXE=C:\\path\\WavePro.exe")


# ── The app driver ───────────────────────────────────────────────────
def _make_dpi_aware() -> None:
    """Exact pixel coordinates even with Windows scaling (125 %, 150 % …)."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _button_regex(name: str) -> str:
    # Some buttons have a symbol in front ("▶  Play Filtered", "⤓ End").
    return rf"^(?:.*\s)?{re.escape(name)}$"


class WaveProApp:
    """Starts, operates and inspects the Wave Pro EXE (one instance per test)."""

    def __init__(self, exe: Path, library: Path):
        self.exe = Path(exe)
        self.library = Path(library)
        self.proc: Optional[subprocess.Popen] = None
        self.win_spec = None      # pywinauto WindowSpecification
        self.win = None           # pywinauto Wrapper
        self.startup_seconds: Optional[float] = None
        self._desktop = None

    # ---------- Start / stop -------------------------------------------
    def start(self, timeout: float = 60.0) -> None:
        _make_dpi_aware()
        from pywinauto import Desktop
        self._desktop = Desktop(backend="uia")
        if self._desktop.window(title_re=TITLE_RE).exists(timeout=1):
            raise RuntimeError("Wave Pro is already running. Please close it first.")

        t0 = time.monotonic()
        self.proc = subprocess.Popen([str(self.exe)], cwd=str(self.exe.parent))
        self.win_spec = self._desktop.window(title_re=TITLE_RE)
        self.win_spec.wait("visible", timeout=timeout)
        self.win = self.win_spec.wrapper_object()
        self.startup_seconds = time.monotonic() - t0

        if not self.wait_for_text(f"{SONG_COUNT} songs", timeout=timeout):
            raise TimeoutError("The test library was not loaded completely.")
        self.win.set_focus()

    def close(self) -> None:
        try:
            if self.win is not None:
                self.win.close()
        except Exception:
            pass
        if self.proc is not None:
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"],
                               capture_output=True)
        # PyInstaller "onefile": the window belongs to a child process.
        if self._desktop is not None and self._desktop.window(
                title_re=TITLE_RE).exists(timeout=2):
            subprocess.run(["taskkill", "/IM", self.exe.name, "/T", "/F"],
                           capture_output=True)
        self.win = None

    # ---------- Window ------------------------------------------------
    def window_title(self) -> str:
        return self.win.window_text()

    def window_rect(self) -> Rect:
        return Rect.from_pywinauto(self.win.rectangle())

    def screen_rect(self) -> Rect:
        m = ctypes.windll.user32.GetSystemMetrics
        x, y = m(76), m(77)                   # virtual screen (all monitors)
        return Rect(x, y, x + m(78), y + m(79))

    def resize_window(self, width: int, height: int) -> None:
        hwnd = self.win.handle
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        ctypes.windll.user32.MoveWindow(hwnd, 40, 40, width, height, True)
        time.sleep(1.0)

    def maximize(self) -> None:
        ctypes.windll.user32.ShowWindow(self.win.handle, SW_MAXIMIZE)
        time.sleep(1.0)

    def restore(self) -> None:
        ctypes.windll.user32.ShowWindow(self.win.handle, SW_RESTORE)
        time.sleep(1.0)

    def is_maximized(self) -> bool:
        return bool(ctypes.windll.user32.IsZoomed(self.win.handle))

    # ---------- Texts & buttons ----------------------------------------
    def text_exists(self, text: str) -> bool:
        return self.win_spec.child_window(
            title=text, control_type="Text").exists(timeout=0)

    def wait_for_text(self, text: str, timeout: float = 10.0) -> bool:
        return wait_until(lambda: self.text_exists(text), timeout)

    def _button(self, name: str):
        return self.win_spec.child_window(
            title_re=_button_regex(name), control_type="Button")

    def button_exists(self, name: str) -> bool:
        return self._button(name).exists(timeout=2)

    def button_rect(self, name: str) -> Rect:
        return Rect.from_pywinauto(self._button(name).wrapper_object().rectangle())

    def click_button(self, name: str) -> None:
        self.win.set_focus()
        self._button(name).wrapper_object().click_input()
        time.sleep(0.4)

    # ---------- Search box -----------------------------------------------
    def _search_box(self):
        # The only text input in the main window (it has no name of its own).
        return self.win_spec.child_window(control_type="Edit", found_index=0)

    def type_search(self, text: str) -> None:
        box = self._search_box().wrapper_object()
        box.click_input()
        box.type_keys(text, with_spaces=True, set_foreground=True)
        time.sleep(0.5)

    def search_value(self) -> str:
        box = self._search_box().wrapper_object()
        for read in (lambda: box.get_value(),
                     lambda: box.iface_text.DocumentRange.GetText(-1),
                     lambda: box.legacy_properties().get("Value", "")):
            try:
                value = read()
                if value is not None:
                    return str(value)
            except Exception:
                continue
        return ""

    # ---------- Table ------------------------------------------------
    def _table(self):
        for ct in ("Table", "DataGrid"):
            spec = self.win_spec.child_window(control_type=ct)
            if spec.exists(timeout=0):
                return spec
        raise LookupError("Song table not found.")

    def table_rect(self) -> Rect:
        return Rect.from_pywinauto(self._table().wrapper_object().rectangle())

    def _cell(self, text: str):
        # Windows: Qt only reports rows currently visible on screen.
        # Rows scrolled away or hidden by a filter are missing here.
        return self._table().child_window(title=text, visible_only=False)

    def cell_rect(self, text: str) -> Optional[Rect]:
        """Position of the cell in the CURRENTLY visible area, otherwise None."""
        spec = self._cell(text)
        if not spec.exists(timeout=0):
            return None
        return Rect.from_pywinauto(spec.wrapper_object().rectangle())

    def _visible_cell_names(self) -> tuple:
        """Names of the currently visible cells (used to detect the list end)."""
        return tuple(c.window_text() for c in self._table().wrapper_object().children())

    def cell_exists(self, text: str) -> bool:
        """Is the text anywhere in the table? Scrolls through the whole list
        if needed, then back to the top."""
        if wait_until(lambda: self.cell_rect(text) is not None, timeout=2):
            return True
        try:
            self.scroll_table_to_top()
            previous = None
            for _ in range(200):
                if self.cell_rect(text) is not None:
                    return True
                current = self._visible_cell_names()
                if current == previous:                   # end of list reached
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
        self.win.set_focus()
        table = self._table().wrapper_object()
        # coords=(None, None) → centre of the table (pywinauto uses relative coords).
        table.wheel_mouse_input(wheel_dist=notches)
        time.sleep(0.6)

    def click_row(self, text: str) -> None:
        self.win.set_focus()
        self._cell(text).wrapper_object().click_input()
        self._park_mouse()

    def _park_mouse(self) -> None:
        """Move the mouse away from the table (no tooltips/hover in screenshots)."""
        from pywinauto import mouse
        w = self.window_rect()
        mouse.move(coords=(w.left + 60, w.top + 45))
        time.sleep(0.5)

    def _row_cells(self, text: str) -> List[Rect]:
        anchor = self.cell_rect(text)
        if anchor is None or anchor.is_empty:
            raise LookupError(f"Row '{text}' is not visible.")
        cells = []
        for child in self._table().wrapper_object().children():
            r = Rect.from_pywinauto(child.rectangle())
            if (r.top == anchor.top and r.height == anchor.height
                    and r.left >= anchor.left and not r.is_empty):
                cells.append(r)
        return sorted(cells, key=lambda c: c.left)

    def row_blue_ratios(self, text: str) -> List[float]:
        """For each column of the row: share of blue pixels (selection colour)."""
        from PIL import ImageGrab
        ratios = []
        for c in self._row_cells(text):
            box = (c.left + 3, c.top + 3, c.right - 3, c.bottom - 3)
            ratios.append(blue_ratio(ImageGrab.grab(bbox=box, all_screens=True)))
        return ratios

    def screenshot(self, path: Path) -> Path:
        from PIL import ImageGrab
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        w = self.window_rect()
        ImageGrab.grab(bbox=(w.left, w.top, w.right, w.bottom),
                       all_screens=True).save(path)
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
                found = findwindows.find_elements(
                    title=title, backend="uia", visible_only=True, **extra)
            except Exception:
                found = []
            for elem in found:
                if elem.handle:
                    return self._desktop.window(handle=elem.handle)
        return None

    def wait_for_dialog(self, title: str, timeout: float = 10.0) -> bool:
        return wait_until(lambda: self._find_dialog(title) is not None, timeout)

    def wait_dialog_closed(self, title: str, timeout: float = 10.0) -> bool:
        return wait_until(lambda: self._find_dialog(title) is None, timeout)

    def dialog_type(self, title: str, text: str) -> None:
        dlg = self._find_dialog(title)
        box = dlg.child_window(control_type="Edit", found_index=0).wrapper_object()
        box.click_input()
        box.type_keys(text, with_spaces=True, set_foreground=True)
        time.sleep(0.3)

    def dialog_click(self, title: str, button: str) -> None:
        dlg = self._find_dialog(title)
        dlg.child_window(title=button, control_type="Button").wrapper_object().click_input()
        time.sleep(0.4)

    # ---------- Keyboard -----------------------------------------------
    @staticmethod
    def _key(vk: int, up: bool = False) -> None:
        ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP if up else 0, 0)
        time.sleep(0.06)

    def press_ctrl_e_plus(self, letter: str) -> None:
        """Wave Pro shortcut: hold Ctrl + E, then tap a letter."""
        self.win.set_focus()
        vk = ord(letter.upper())
        for k in (VK_CONTROL, ord("E")):
            self._key(k)
        self._key(vk)
        self._key(vk, up=True)
        for k in (ord("E"), VK_CONTROL):
            self._key(k, up=True)
        time.sleep(0.4)

    def press_escape(self) -> None:
        self._key(VK_ESCAPE)
        self._key(VK_ESCAPE, up=True)
        time.sleep(0.4)

    # ---------- Files in the test library --------------------------
    def library_files(self, pattern: str = "**/*") -> List[Path]:
        return sorted(p for p in self.library.glob(pattern) if p.is_file())
