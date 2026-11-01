"""Vorbereitung und Aufräumen – EINMAL geschrieben, von allen drei Werkzeugen benutzt.

    beginne()       einmal vor allen Tests:  Profil sichern, Berichtsordner anlegen
    starte_test()   vor jedem Test:          Testbibliothek anlegen, EXE starten,
                                             warten bis "60 songs" geladen ist
    beende_test()   nach jedem Test:         bei Fehler Screenshot, EXE schließen,
                                             Testdaten löschen
    beende()        einmal nach allen Tests: Profil exakt wiederherstellen

Weil 01_pytest, 02_robot und 03_pywinauto genau diese Klasse benutzen,
laufen Vorbereitung und Aufräumen in allen Werkzeugen identisch.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import wavepro as wp
from schritte import Kontext


def sicherer_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text)


class Sitzung:
    def __init__(self, bericht_ordner: Path):
        self.bericht_ordner = Path(bericht_ordner)
        self.guard = wp.ProfileGuard()
        self.kontext: Optional[Kontext] = None
        self._bibliothek: Optional[Path] = None

    def beginne(self) -> None:
        self.bericht_ordner.mkdir(parents=True, exist_ok=True)
        self.guard.backup()

    def starte_test(self) -> Kontext:
        self._bibliothek = wp.create_test_library()
        self.guard.prepare_for_test(self._bibliothek)
        app = wp.WaveProApp(wp.find_exe(), self._bibliothek)
        self.kontext = Kontext(app, bericht_ordner=self.bericht_ordner)
        app.start()
        return self.kontext

    def beende_test(self, name: str, fehlgeschlagen: bool) -> Optional[Path]:
        """Gibt den Pfad des Fehler-Screenshots zurück (oder None)."""
        app = self.kontext.app if self.kontext else None
        screenshot = None
        try:
            if fehlgeschlagen and app is not None and app.win is not None:
                screenshot = app.screenshot(
                    self.bericht_ordner / "fehler_screenshots" / f"{sicherer_name(name)}.png")
        except Exception:
            screenshot = None
        finally:
            if app is not None:
                app.close()
            if self._bibliothek is not None:
                self.guard.forget_library_cache(self._bibliothek)
                wp.remove_test_library(self._bibliothek)
            self.kontext = None
            self._bibliothek = None
        return screenshot

    def beende(self) -> None:
        self.guard.restore()
