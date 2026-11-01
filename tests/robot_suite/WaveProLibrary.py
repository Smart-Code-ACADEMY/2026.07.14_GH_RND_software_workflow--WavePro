"""Robot-Framework-Schlüsselwörter für Wave Pro.

Dünne Schicht über common/wavepro.py – dieselbe Steuerung wie pytest.
Jede Methode mit @keyword wird in wavepro.robot als Schritt benutzt.
"""
import sys
from pathlib import Path

from robot.api import logger
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.wavepro import (  # noqa: E402
    REPORTS_DIR, ProfileGuard, WaveProApp, create_test_library, find_exe,
    remove_test_library)


@library(scope="SUITE", auto_keywords=False)
class WaveProLibrary:

    def __init__(self):
        self._guard = ProfileGuard()
        self._app = None
        self._library = None

    @property
    def app(self) -> WaveProApp:
        if self._app is None:
            raise RuntimeError("Wave Pro wurde nicht gestartet.")
        return self._app

    # ---------- Setup / Teardown ---------------------------------------
    @keyword("Sichere Benutzerprofil")
    def backup_profile(self):
        self._guard.backup()

    @keyword("Stelle Benutzerprofil Wieder Her")
    def restore_profile(self):
        self._guard.restore()

    @keyword("Starte Wave Pro Mit Testbibliothek")
    def start_app(self):
        self._library = create_test_library()
        self._guard.prepare_for_test(self._library)
        self._app = WaveProApp(find_exe(), self._library)
        self._app.start()

    @keyword("Schliesse Wave Pro")
    def close_app(self):
        try:
            status = BuiltIn().get_variable_value("${TEST STATUS}")
            if status == "FAIL" and self._app is not None and self._app.win is not None:
                name = BuiltIn().get_variable_value("${TEST NAME}", "test")
                safe = "".join(c if c.isalnum() else "_" for c in name)
                shot = self._app.screenshot(REPORTS_DIR / "robot_failures" / f"{safe}.png")
                logger.info(f'<img src="{shot.as_uri()}" width="800">', html=True)
        except Exception:
            pass
        finally:
            if self._app is not None:
                self._app.close()
            if self._library is not None:
                self._guard.forget_library_cache(self._library)
                remove_test_library(self._library)
            self._app = None
            self._library = None

    # ---------- Prüfungen ----------------------------------------------
    @keyword("Fenstertitel Sollte Beginnen Mit")
    def title_should_start_with(self, expected):
        title = self.app.window_title()
        if not title.startswith(expected):
            raise AssertionError(f"Titel ist '{title}'")

    @keyword("Startzeit Sollte Unter ${seconds} Sekunden Liegen")
    def startup_below(self, seconds):
        if not self.app.startup_seconds < float(seconds):
            raise AssertionError(f"Start dauerte {self.app.startup_seconds:.1f} s")

    @keyword("Text Sollte Sichtbar Sein")
    def text_visible(self, text):
        if not self.app.text_exists(text):
            raise AssertionError(f"Text fehlt: {text}")

    @keyword("Button Sollte Existieren")
    def button_exists(self, name):
        if not self.app.button_exists(name):
            raise AssertionError(f"Button fehlt: {name}")

    @keyword("Tabelle Sollte Enthalten")
    def table_contains(self, text):
        if not self.app.cell_exists(text):
            raise AssertionError(f"Tabellenzelle fehlt: {text}")

    @keyword("Zeile Sollte Angezeigt Werden")
    def row_shown(self, text):
        if not self.app.is_row_shown(text):
            raise AssertionError(f"Zeile ist ausgeblendet: {text}")

    @keyword("Zeile Sollte Ausgeblendet Sein")
    def row_hidden(self, text):
        if self.app.is_row_shown(text):
            raise AssertionError(f"Zeile ist noch sichtbar: {text}")

    @keyword("Zeile Sollte Im Sichtbaren Bereich Sein")
    def row_in_view(self, text):
        if not self.app.is_row_in_view(text):
            raise AssertionError(f"Zeile nicht im sichtbaren Bereich: {text}")

    @keyword("Zeile Sollte Nicht Im Sichtbaren Bereich Sein")
    def row_not_in_view(self, text):
        if self.app.is_row_in_view(text):
            raise AssertionError(f"Zeile ist im sichtbaren Bereich: {text}")

    @keyword("Suchfeld Sollte Enthalten")
    def search_should_be(self, expected):
        value = self.app.search_value()
        if value != expected:
            raise AssertionError(f"Suchfeld enthält '{value}', erwartet '{expected}'")

    @keyword("Dialog Sollte Erscheinen")
    def dialog_appears(self, title):
        if not self.app.wait_for_dialog(title):
            raise AssertionError(f"Dialog erscheint nicht: {title}")

    @keyword("Dialog Sollte Geschlossen Sein")
    def dialog_closed(self, title):
        if not self.app.wait_dialog_closed(title):
            raise AssertionError(f"Dialog ist noch offen: {title}")

    @keyword("Datei Sollte Existieren")
    def file_exists(self, relative_path, starts_with=""):
        p = self.app.library / relative_path
        if not p.is_file():
            raise AssertionError(f"Datei fehlt: {relative_path}")
        if starts_with and not p.read_text(encoding="utf-8").startswith(starts_with):
            raise AssertionError(f"Inhalt falsch in {relative_path}")

    @keyword("Zaehle Textdateien")
    def count_txt(self):
        return len(self.app.library_files("**/*.txt"))

    @keyword("Zeile Sollte In Allen Spalten Blau Sein")
    def row_blue(self, text):
        ratios = self.app.row_blue_ratios(text)
        if len(ratios) < 8 or not all(r >= 0.5 for r in ratios):
            raise AssertionError(f"Nicht überall blau: {ratios}")

    @keyword("Zeile Sollte Nicht Blau Sein")
    def row_not_blue(self, text):
        ratios = self.app.row_blue_ratios(text)
        if not all(r < 0.1 for r in ratios):
            raise AssertionError(f"Zeile ist blau: {ratios}")

    @keyword("Button Sollte Im Fenster Liegen")
    def button_in_window(self, name):
        if not self.app.window_rect().contains(self.app.button_rect(name)):
            raise AssertionError(f"{name} liegt außerhalb des Fensters")

    @keyword("Button Sollte Auf Dem Bildschirm Liegen")
    def button_on_screen(self, name):
        if not self.app.screen_rect().contains(self.app.button_rect(name)):
            raise AssertionError(f"{name} liegt außerhalb des Bildschirms")

    @keyword("Fenster Sollte Auf Den Bildschirm Passen")
    def window_fits_screen(self):
        win, screen = self.app.window_rect(), self.app.screen_rect()
        if not screen.contains(win, tolerance=10):
            raise AssertionError(f"Fenster {win} ist größer als Bildschirm {screen}")

    @keyword("Fenster Sollte Maximiert Sein")
    def is_max(self):
        if not self.app.is_maximized():
            raise AssertionError("Fenster ist nicht maximiert")

    @keyword("Fenster Sollte Nicht Maximiert Sein")
    def is_not_max(self):
        if self.app.is_maximized():
            raise AssertionError("Fenster ist noch maximiert")

    # ---------- Aktionen -----------------------------------------------
    @keyword("Klicke Button")
    def click_button(self, name):
        self.app.click_button(name)

    @keyword("Tippe In Suchfeld")
    def type_search(self, text):
        self.app.type_search(text)

    @keyword("Tippe In Dialog")
    def dialog_type(self, title, text):
        self.app.dialog_type(title, text)

    @keyword("Klicke Im Dialog")
    def dialog_click(self, title, button):
        self.app.dialog_click(title, button)

    @keyword("Druecke Strg+E+${letter}")
    def ctrl_e(self, letter):
        self.app.press_ctrl_e_plus(letter)

    @keyword("Druecke Escape")
    def escape(self):
        self.app.press_escape()

    @keyword("Scrolle Mit Mausrad")
    def wheel(self, notches):
        self.app.wheel_scroll_table(int(notches))

    @keyword("Klicke Zeile")
    def click_row(self, text):
        self.app.click_row(text)

    @keyword("Speichere Screenshot")
    def screenshot(self, name):
        shot = self.app.screenshot(REPORTS_DIR / "screenshots" / name)
        logger.info(f'<img src="{shot.as_uri()}" width="800">', html=True)

    @keyword("Aendere Fenstergroesse")
    def resize(self, width, height):
        self.app.resize_window(int(width), int(height))

    @keyword("Maximiere Fenster")
    def maximize(self):
        self.app.maximize()

    @keyword("Stelle Fenster Wieder Her")
    def restore_window(self):
        self.app.restore()
