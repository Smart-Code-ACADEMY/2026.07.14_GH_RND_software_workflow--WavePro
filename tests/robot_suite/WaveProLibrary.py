"""Robot-Framework-Bibliothek für Wave Pro.

Sie definiert KEINE eigenen Testschritte. Sie gibt Robot einfach alle
Schritte aus common/schritte.py weiter (Robot "Dynamic Library API").
Dazu kommen nur die 4 Vorbereitungs-/Aufräum-Schritte.
"""
import sys
from pathlib import Path

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.schritte import SCHRITTE, Kontext, finde_schritt  # noqa: E402
from common.wavepro import (  # noqa: E402
    REPORTS_DIR, ProfileGuard, WaveProApp, create_test_library, find_exe,
    remove_test_library)

_VORBEREITUNG = {
    "Sichere Benutzerprofil": "_profil_sichern",
    "Stelle Benutzerprofil Wieder Her": "_profil_wiederherstellen",
    "Starte Wave Pro Mit Testbibliothek": "_app_starten",
    "Schliesse Wave Pro": "_app_schliessen",
}


class WaveProLibrary:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self._guard = ProfileGuard()
        self._kontext = None
        self._bibliothek = None

    # ---------- Robot Dynamic Library API ------------------------------
    def get_keyword_names(self):
        return list(_VORBEREITUNG) + [s.name for s in SCHRITTE.values()]

    def get_keyword_arguments(self, name):
        if name in _VORBEREITUNG:
            return []
        n = finde_schritt(name).anzahl_werte
        return [f"wert{i + 1}" for i in range(n)]

    def get_keyword_documentation(self, name):
        if name in _VORBEREITUNG:
            return "Vorbereitung / Aufräumen (nicht Teil der Spezifikation)."
        art = "Prüfung" if finde_schritt(name).ist_pruefung else "Aktion"
        return f"{art} aus common/schritte.py"

    def run_keyword(self, name, args, kwargs=None):
        if name in _VORBEREITUNG:
            return getattr(self, _VORBEREITUNG[name])()
        if self._kontext is None:
            raise RuntimeError("Wave Pro wurde nicht gestartet.")
        result = finde_schritt(name).funktion(self._kontext, *args)
        shot = self._kontext.gemerkt.pop("screenshot", None)
        if shot is not None:
            logger.info(f'<img src="{Path(shot).as_uri()}" width="800">', html=True)
        return result

    # ---------- Vorbereitung / Aufräumen -------------------------------
    def _profil_sichern(self):
        self._guard.backup()

    def _profil_wiederherstellen(self):
        self._guard.restore()

    def _app_starten(self):
        self._bibliothek = create_test_library()
        self._guard.prepare_for_test(self._bibliothek)
        app = WaveProApp(find_exe(), self._bibliothek)
        self._kontext = Kontext(app)
        app.start()

    def _app_schliessen(self):
        app = self._kontext.app if self._kontext else None
        try:
            if (BuiltIn().get_variable_value("${TEST STATUS}") == "FAIL"
                    and app is not None and app.win is not None):
                name = BuiltIn().get_variable_value("${TEST NAME}", "test")
                datei = "".join(c if c.isalnum() else "_" for c in name) + ".png"
                shot = app.screenshot(REPORTS_DIR / "robot_failures" / datei)
                logger.info(f'<img src="{shot.as_uri()}" width="800">', html=True)
        except Exception:
            pass
        finally:
            if app is not None:
                app.close()
            if self._bibliothek is not None:
                self._guard.forget_library_cache(self._bibliothek)
                remove_test_library(self._bibliothek)
            self._kontext = None
            self._bibliothek = None
