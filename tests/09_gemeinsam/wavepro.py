"""
Motor: steuert die Wave-Pro-EXE mit pywinauto – für ALLE drei Werkzeuge.

01_pytest, 02_robot und 03_pywinauto benutzen genau diese Klasse.
Dadurch führen alle Werkzeuge identische Befehle aus.

Technik: pywinauto mit "uia"-Backend (Windows UI Automation).
Wave Pro ist eine Qt-Anwendung; Qt meldet Fenster, Buttons, Texte und
Tabellenzellen an Windows UI Automation. pywinauto liest diese Angaben.

SICHERHEIT (höchste Priorität):
  * Die Tests benutzen NIE deine echte Musik. Jeder Test erzeugt eine
    eigene, temporäre Testbibliothek (60 stille WAV-Dateien) in %TEMP%.
  * Deine Wave-Pro-Einstellungen (Registry), deine Änderungshistorie
    (changelog.csv) und offene Aufgaben (pending_queue.json) werden vor dem
    Testlauf gesichert und danach exakt wiederhergestellt.
  * Gelöscht wird nur, was die Tests selbst erzeugt haben – geprüft über
    Name, Ort und eine Markierungsdatei.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

# ── Feste Werte ─────────────────────────────────────────────────────────
TESTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = TESTS_DIR.parent
REPORTS_DIR = TESTS_DIR / "reports"

WINDOW_TITLE_START = "Wave Pro - Music Studio"
TITLE_RE = r"^Wave Pro - Music Studio.*"
REG_KEY = r"HKCU\Software\WavePro\Wave Pro - Music Studio"
GUARDED_FILES = ("pending_queue.json", "changelog.csv")

SONG_COUNT = 60                       # Anzahl Testlieder
LIB_PREFIX = "wavepro_testlib_"       # Name der temporären Testbibliothek
LIB_MARKER = ".wavepro_test_library"  # Markierung: "von Tests erzeugt"

VK_CONTROL, VK_ESCAPE = 0x11, 0x1B
KEYEVENTF_KEYUP = 0x0002
SW_MAXIMIZE, SW_RESTORE = 3, 9


# ── Hilfstypen ──────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Rect:
    """Bildschirm-Rechteck in Pixeln."""
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
    """Wiederholt `condition()` bis True oder Zeitlimit. Gibt Ergebnis zurück."""
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
    """Anteil 'blauer' Pixel (Auswahlfarbe) in einem PIL-Bild, 0.0 – 1.0."""
    data = image.convert("RGB").tobytes()      # r,g,b,r,g,b,…
    total = len(data) // 3
    if total == 0:
        return 0.0
    blue = sum(1 for i in range(0, total * 3, 3)
               if data[i + 2] > data[i] + 40 and data[i + 2] > 90)
    return blue / total


# ── EXE finden ──────────────────────────────────────────────────────────
def find_exe() -> Path:
    """Sucht die Wave-Pro-EXE.

    Reihenfolge: Umgebungsvariable WAVEPRO_EXE → Ordner publish/ →
    Projektwurzel. Bei mehreren Kandidaten gewinnt der Name mit 'wave'."""
    env = os.environ.get("WAVEPRO_EXE", "").strip().strip('"')
    if env:
        p = Path(env)
        if p.is_file():
            return p.resolve()
        raise FileNotFoundError(f"WAVEPRO_EXE zeigt auf keine Datei: {p}")

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
                "Mehrere Wave-Pro-EXE gefunden – bitte WAVEPRO_EXE setzen:\n  "
                + "\n  ".join(map(str, wave_named)))
        if len(found) == 1:
            return found[0].resolve()
    raise FileNotFoundError(
        "Keine Wave-Pro-EXE gefunden (publish/ oder Projektwurzel). "
        "Tipp: set WAVEPRO_EXE=C:\\Pfad\\WavePro.exe")


# ── Testbibliothek (temporäre Musikordner) ──────────────────────────────
def song_title(i: int) -> str:
    return f"Artist {i:02d} - Song {i:02d}"


def create_test_library(count: int = SONG_COUNT) -> Path:
    """Erzeugt <TEMP>/wavepro_testlib_xxx mit Pop/, Rock/, To-Do/.

    Ungerade Nummern → Pop, gerade → Rock. Jede Datei: 0,5 s Stille (WAV)."""
    root = Path(tempfile.mkdtemp(prefix=LIB_PREFIX)).resolve()
    (root / LIB_MARKER).write_text(
        "Von den Wave-Pro-Tests erzeugt. Darf gelöscht werden.\n",
        encoding="utf-8")
    for cat in ("Pop", "Rock", "To-Do"):
        (root / cat).mkdir()
    for i in range(1, count + 1):
        cat = "Pop" if i % 2 else "Rock"
        with wave.open(str(root / cat / f"{song_title(i)}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(8000)
            w.writeframes(b"\x00\x00" * 4000)
    return root


def remove_test_library(root: Path) -> None:
    """Löscht NUR eine von uns erzeugte Testbibliothek (3-fach geprüft)."""
    root = Path(root).resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if not (root.name.startswith(LIB_PREFIX)
            and root.parent == temp
            and (root / LIB_MARKER).is_file()):
        raise RuntimeError(f"Sicherheitsstopp: {root} ist keine Testbibliothek.")
    shutil.rmtree(root, ignore_errors=True)


# ── Schutz deines echten Wave-Pro-Profils ───────────────────────────────
def _reg(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["reg", *args], capture_output=True, text=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProfileGuard:
    """Sichert und restauriert Einstellungen + Historie des echten Benutzers.

    Ablauf: backup() einmal vor allen Tests → prepare_for_test() vor jedem
    Test → restore() einmal nach allen Tests.
    Regel: Es wird erst etwas verändert, wenn die Sicherung vollständig
    und geprüft ist (Datei COMPLETE). Stürzt ein Lauf ab, stellt der
    nächste Lauf zuerst die alte Sicherung wieder her."""

    def __init__(self, backup_dir: Optional[Path] = None,
                 appdata_dir: Optional[Path] = None):
        self.backup_dir = Path(backup_dir or TESTS_DIR / ".profile_backup")
        self.appdata_dir = Path(appdata_dir or (
            Path(os.environ.get("APPDATA", Path.home()))
            / "WavePro" / "Wave Pro - Music Studio"))

    @property
    def _complete(self) -> Path:
        return self.backup_dir / "COMPLETE"

    def backup(self) -> None:
        if self._complete.is_file():          # früherer Lauf abgebrochen
            self.restore()
        elif self.backup_dir.exists():        # Sicherung unvollständig:
            shutil.rmtree(self.backup_dir)    # Originale wurden nie berührt
        self.backup_dir.mkdir(parents=True)

        had_key = _reg("query", REG_KEY).returncode == 0
        if had_key:
            reg_file = self.backup_dir / "settings.reg"
            r = _reg("export", REG_KEY, str(reg_file), "/y")
            if r.returncode != 0 or not reg_file.is_file():
                raise RuntimeError(f"Registry-Sicherung fehlgeschlagen: {r.stderr}")

        saved = []
        for name in GUARDED_FILES:
            src = self.appdata_dir / name
            if src.is_file():
                dst = self.backup_dir / name
                shutil.copy2(src, dst)
                if _sha256(src) != _sha256(dst):
                    raise RuntimeError(f"Sicherung von {name} ist fehlerhaft.")
                saved.append(name)

        self._complete.write_text(
            json.dumps({"had_key": had_key, "files": saved}), encoding="utf-8")

    def prepare_for_test(self, library: Path) -> None:
        """Sauberer Start: leere Einstellungen, nur die Testbibliothek."""
        if not self._complete.is_file():
            raise RuntimeError("Sicherheitsstopp: keine vollständige Sicherung.")
        _reg("delete", REG_KEY, "/f")
        r = _reg("add", REG_KEY, "/v", "root_path", "/t", "REG_SZ",
                 "/d", str(Path(library).resolve()), "/f")
        if r.returncode != 0:
            raise RuntimeError(f"Registry-Eintrag fehlgeschlagen: {r.stderr}")
        queue = self.appdata_dir / "pending_queue.json"
        if queue.is_file():   # Original liegt geprüft in der Sicherung
            queue.unlink()

    def forget_library_cache(self, library: Path) -> None:
        """Entfernt die Cache-Datei, die Wave Pro für die Testbibliothek anlegt."""
        h = hashlib.md5(str(Path(library).resolve()).encode()).hexdigest()
        cache = self.appdata_dir / f"music_library_cache_{h}.json"
        if cache.is_file():
            cache.unlink()

    def restore(self) -> None:
        if not self._complete.is_file():
            return
        info = json.loads(self._complete.read_text(encoding="utf-8"))
        _reg("delete", REG_KEY, "/f")
        if info["had_key"]:
            r = _reg("import", str(self.backup_dir / "settings.reg"))
            if r.returncode != 0:
                raise RuntimeError(
                    f"Registry-Wiederherstellung fehlgeschlagen: {r.stderr}\n"
                    f"Sicherung bleibt erhalten in: {self.backup_dir}")
        for name in GUARDED_FILES:
            dst = self.appdata_dir / name
            if name in info["files"]:
                self.appdata_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.backup_dir / name, dst)
            elif dst.is_file():       # gab es vorher nicht → vom Test erzeugt
                dst.unlink()
        shutil.rmtree(self.backup_dir)


# ── Die App-Steuerung ───────────────────────────────────────────────────
def _make_dpi_aware() -> None:
    """Pixelgenaue Koordinaten auch bei Windows-Skalierung (125 %, 150 % …)."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _button_regex(name: str) -> str:
    # Buttons haben teils Symbole davor ("▶  Play Filtered", "⤓ End").
    return rf"^(?:.*\s)?{re.escape(name)}$"


class WaveProApp:
    """Startet, bedient und prüft die Wave-Pro-EXE (eine Instanz pro Test)."""

    def __init__(self, exe: Path, library: Path):
        self.exe = Path(exe)
        self.library = Path(library)
        self.proc: Optional[subprocess.Popen] = None
        self.win_spec = None      # pywinauto WindowSpecification
        self.win = None           # pywinauto Wrapper
        self.startup_seconds: Optional[float] = None
        self._desktop = None

    # ---------- Start / Ende -------------------------------------------
    def start(self, timeout: float = 60.0) -> None:
        _make_dpi_aware()
        from pywinauto import Desktop
        self._desktop = Desktop(backend="uia")
        if self._desktop.window(title_re=TITLE_RE).exists(timeout=1):
            raise RuntimeError("Wave Pro läuft bereits. Bitte zuerst schließen.")

        t0 = time.monotonic()
        self.proc = subprocess.Popen([str(self.exe)], cwd=str(self.exe.parent))
        self.win_spec = self._desktop.window(title_re=TITLE_RE)
        self.win_spec.wait("visible", timeout=timeout)
        self.win = self.win_spec.wrapper_object()
        self.startup_seconds = time.monotonic() - t0

        if not self.wait_for_text(f"{SONG_COUNT} songs", timeout=timeout):
            raise TimeoutError("Testbibliothek wurde nicht vollständig geladen.")
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
        # PyInstaller-"onefile": Fenster gehört einem Kindprozess.
        if self._desktop is not None and self._desktop.window(
                title_re=TITLE_RE).exists(timeout=2):
            subprocess.run(["taskkill", "/IM", self.exe.name, "/T", "/F"],
                           capture_output=True)
        self.win = None

    # ---------- Fenster ------------------------------------------------
    def window_title(self) -> str:
        return self.win.window_text()

    def window_rect(self) -> Rect:
        return Rect.from_pywinauto(self.win.rectangle())

    def screen_rect(self) -> Rect:
        m = ctypes.windll.user32.GetSystemMetrics
        x, y = m(76), m(77)                   # virtueller Bildschirm
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

    # ---------- Texte & Buttons ----------------------------------------
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

    # ---------- Suchfeld -----------------------------------------------
    def _search_box(self):
        # Einziges Texteingabefeld im Hauptfenster (hat keinen eigenen Namen).
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

    # ---------- Tabelle ------------------------------------------------
    def _table(self):
        for ct in ("Table", "DataGrid"):
            spec = self.win_spec.child_window(control_type=ct)
            if spec.exists(timeout=0):
                return spec
        raise LookupError("Songtabelle nicht gefunden.")

    def table_rect(self) -> Rect:
        return Rect.from_pywinauto(self._table().wrapper_object().rectangle())

    def _cell(self, text: str):
        # Achtung Windows: Qt meldet nur Zeilen, die gerade auf dem Bildschirm
        # zu sehen sind. Weggescrollte oder weggefilterte Zeilen fehlen hier.
        return self._table().child_window(title=text, visible_only=False)

    def cell_rect(self, text: str) -> Optional[Rect]:
        """Position der Zelle im JETZT sichtbaren Bereich, sonst None."""
        spec = self._cell(text)
        if not spec.exists(timeout=0):
            return None
        return Rect.from_pywinauto(spec.wrapper_object().rectangle())

    def _visible_cell_names(self) -> tuple:
        """Namen der gerade sichtbaren Zellen (erkennt das Listenende)."""
        return tuple(c.window_text() for c in self._table().wrapper_object().children())

    def cell_exists(self, text: str) -> bool:
        """Steht der Text irgendwo in der Tabelle? Scrollt dafür durch die
        ganze Liste und danach wieder nach oben."""
        if wait_until(lambda: self.cell_rect(text) is not None, timeout=2):
            return True
        try:
            self.scroll_table_to_top()
            previous = None
            for _ in range(200):
                if self.cell_rect(text) is not None:
                    return True
                current = self._visible_cell_names()
                if current == previous:                   # Ende erreicht
                    return False
                previous = current
                self.wheel_scroll_table(-3)               # 3 Raster nach unten
            return False
        finally:
            self.scroll_table_to_top()                    # zurück nach oben

    def scroll_table_to_top(self) -> None:
        """In kleinen Schritten nach oben, bis sich nichts mehr bewegt.
        (Ein einzelnes Mausrad-Ereignis scrollt höchstens eine Seite.)"""
        previous = None
        for _ in range(200):
            current = self._visible_cell_names()
            if current == previous:
                return
            previous = current
            self.wheel_scroll_table(+5)

    def is_row_shown(self, text: str) -> bool:
        """Zeile nicht weggefiltert (ausgeblendete Zeilen haben Fläche 0)."""
        r = self.cell_rect(text)
        return r is not None and not r.is_empty

    def is_row_in_view(self, text: str) -> bool:
        """Zeile liegt im sichtbaren Bereich der Tabelle (nicht weggescrollt)."""
        r = self.cell_rect(text)
        return r is not None and not r.is_empty and self.table_rect().contains(r)

    def wheel_scroll_table(self, notches: int) -> None:
        """Mausrad über der Tabelle; negative Zahl = nach unten."""
        self.win.set_focus()
        table = self._table().wrapper_object()
        # coords=(None, None) → Mitte der Tabelle (pywinauto rechnet relativ).
        table.wheel_mouse_input(wheel_dist=notches)
        time.sleep(0.6)

    def click_row(self, text: str) -> None:
        self.win.set_focus()
        self._cell(text).wrapper_object().click_input()
        self._park_mouse()

    def _park_mouse(self) -> None:
        """Maus weg von der Tabelle (keine Tooltips/Hover im Screenshot)."""
        from pywinauto import mouse
        w = self.window_rect()
        mouse.move(coords=(w.left + 60, w.top + 45))
        time.sleep(0.5)

    def _row_cells(self, text: str) -> List[Rect]:
        anchor = self.cell_rect(text)
        if anchor is None or anchor.is_empty:
            raise LookupError(f"Zeile '{text}' ist nicht sichtbar.")
        cells = []
        for child in self._table().wrapper_object().children():
            r = Rect.from_pywinauto(child.rectangle())
            if (r.top == anchor.top and r.height == anchor.height
                    and r.left >= anchor.left and not r.is_empty):
                cells.append(r)
        return sorted(cells, key=lambda c: c.left)

    def row_blue_ratios(self, text: str) -> List[float]:
        """Für jede Spalte der Zeile: Anteil blauer Pixel (Auswahlfarbe)."""
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

    # ---------- Dialoge ------------------------------------------------
    def _find_dialog(self, title: str):
        """Sucht einen SICHTBAREN Dialog. (exists() würde auch versteckte
        finden – Qt versteckt geschlossene Dialoge nur, statt sie zu löschen.)"""
        from pywinauto import findwindows
        searches = (
            dict(top_level_only=True),                       # eigenes Fenster
            dict(top_level_only=False, control_type="Window",  # unter Hauptfenster
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

    # ---------- Tastatur -----------------------------------------------
    @staticmethod
    def _key(vk: int, up: bool = False) -> None:
        ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP if up else 0, 0)
        time.sleep(0.06)

    def press_ctrl_e_plus(self, letter: str) -> None:
        """Wave-Pro-Kürzel: Strg + E gedrückt halten, dann Buchstabe tippen."""
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

    # ---------- Dateien in der Testbibliothek --------------------------
    def library_files(self, pattern: str = "**/*") -> List[Path]:
        return sorted(p for p in self.library.glob(pattern) if p.is_file())
