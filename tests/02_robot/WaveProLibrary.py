"""02 Robot Framework – Bibliothek.

Definiert KEINE eigenen Testschritte. Sie gibt Robot alle Schritte aus
09_gemeinsam/schritte.py weiter (Robot "Dynamic Library API") und nutzt für
Vorbereitung/Aufräumen dieselbe Sitzung wie pytest und pywinauto.
"""
import sys
from pathlib import Path

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "09_gemeinsam"))

from schritte import SCHRITTE, finde_schritt  # noqa: E402
from sitzung import Sitzung  # noqa: E402
from wavepro import REPORTS_DIR  # noqa: E402

BERICHT = REPORTS_DIR / "02_robot"

_SITZUNG_SCHRITTE = {
    "Beginne Sitzung": "_beginne",
    "Beende Sitzung": "_beende",
    "Starte Test": "_starte_test",
    "Beende Test": "_beende_test",
}


def _bild(pfad: Path) -> None:
    logger.info(f'<img src="{Path(pfad).as_uri()}" width="800">', html=True)


class WaveProLibrary:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self._sitzung = Sitzung(BERICHT)

    # ---------- Robot Dynamic Library API ------------------------------
    def get_keyword_names(self):
        return list(_SITZUNG_SCHRITTE) + [s.name for s in SCHRITTE.values()]

    def get_keyword_arguments(self, name):
        if name in _SITZUNG_SCHRITTE:
            return []
        return [f"wert{i + 1}" for i in range(finde_schritt(name).anzahl_werte)]

    def get_keyword_documentation(self, name):
        if name in _SITZUNG_SCHRITTE:
            return "Vorbereitung / Aufräumen aus 09_gemeinsam/sitzung.py."
        art = "Prüfung" if finde_schritt(name).ist_pruefung else "Aktion"
        return f"{art} aus 09_gemeinsam/schritte.py"

    def run_keyword(self, name, args, kwargs=None):
        if name in _SITZUNG_SCHRITTE:
            return getattr(self, _SITZUNG_SCHRITTE[name])()
        kontext = self._sitzung.kontext
        if kontext is None:
            raise RuntimeError("Wave Pro wurde nicht gestartet.")
        ergebnis = finde_schritt(name).funktion(kontext, *args)
        screenshot = kontext.gemerkt.pop("screenshot", None)
        if screenshot is not None:
            _bild(screenshot)
        return ergebnis

    # ---------- Sitzung --------------------------------------------------
    def _beginne(self):
        self._sitzung.beginne()

    def _beende(self):
        self._sitzung.beende()

    def _starte_test(self):
        self._sitzung.starte_test()

    def _beende_test(self):
        bi = BuiltIn()
        name = bi.get_variable_value("${TEST NAME}", "test").split(" ")[0]
        fehler = bi.get_variable_value("${TEST STATUS}") != "PASS"
        screenshot = self._sitzung.beende_test(name, fehler)
        if screenshot is not None:
            _bild(screenshot)
