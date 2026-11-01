"""Wörterbuch aller erlaubten Testschritte.

Jeder Schritt-Name aus 00_spezifikation/testfaelle.yaml wird HIER in eine echte Aktion
übersetzt. pytest, Robot Framework und der reine pywinauto-Lauf benutzen dieses
Wörterbuch – ein Schritt funktioniert also in allen drei Werkzeugen identisch.

Neuen Schritt hinzufügen:  Funktion schreiben + @schritt("Name") darüber.
Name mit "Sollte"  → Prüfung (erwartetes Ergebnis), sonst → Aktion.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Callable, Dict

from pathlib import Path

from wavepro import REPORTS_DIR, WaveProApp


@dataclass
class Kontext:
    """Was ein Schritt braucht: die laufende App + ein kleines Gedächtnis."""
    app: WaveProApp
    bericht_ordner: Path = REPORTS_DIR
    gemerkt: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Schritt:
    name: str
    funktion: Callable
    anzahl_werte: int

    @property
    def ist_pruefung(self) -> bool:
        return "sollte" in self.name.lower()


SCHRITTE: Dict[str, Schritt] = {}


def _schluessel(name: str) -> str:
    """Wie Robot: Groß/Kleinschreibung und Leerzeichen sind egal."""
    return "".join(name.lower().split())


def schritt(name: str):
    def registrieren(fn):
        n = len(inspect.signature(fn).parameters) - 1   # ohne "k"
        SCHRITTE[_schluessel(name)] = Schritt(name, fn, n)
        return fn
    return registrieren


def finde_schritt(name: str) -> Schritt:
    s = SCHRITTE.get(_schluessel(name))
    if s is None:
        raise KeyError(f"Unbekannter Schritt: '{name}'")
    return s


def _pruefe(bedingung: bool, meldung: str) -> None:
    if not bedingung:
        raise AssertionError(meldung)


# ════════════════════════ AKTIONEN ════════════════════════════════════
@schritt("Klicke Button")
def _(k, name):
    k.app.click_button(name)


@schritt("Tippe In Suchfeld")
def _(k, text):
    k.app.type_search(text)


@schritt("Tippe In Dialog")
def _(k, titel, text):
    k.app.dialog_type(titel, text)


@schritt("Klicke Im Dialog")
def _(k, titel, button):
    k.app.dialog_click(titel, button)


@schritt("Druecke Strg+E Plus")
def _(k, buchstabe):
    k.app.press_ctrl_e_plus(buchstabe)


@schritt("Druecke Escape")
def _(k):
    k.app.press_escape()


@schritt("Scrolle Mit Mausrad")
def _(k, raster):
    k.app.wheel_scroll_table(int(raster))


@schritt("Klicke Zeile")
def _(k, text):
    k.app.click_row(text)


@schritt("Speichere Screenshot")
def _(k, dateiname):
    k.gemerkt["screenshot"] = k.app.screenshot(k.bericht_ordner / "screenshots" / dateiname)


@schritt("Aendere Fenstergroesse")
def _(k, breite, hoehe):
    k.app.resize_window(int(breite), int(hoehe))


@schritt("Maximiere Fenster")
def _(k):
    k.app.maximize()


@schritt("Stelle Fenster Wieder Her")
def _(k):
    k.app.restore()


@schritt("Merke Anzahl Textdateien")
def _(k):
    k.gemerkt["txt"] = len(k.app.library_files("**/*.txt"))


# ════════════════════════ PRÜFUNGEN ═══════════════════════════════════
@schritt("Fenstertitel Sollte Beginnen Mit")
def _(k, text):
    titel = k.app.window_title()
    _pruefe(titel.startswith(text), f"Titel ist '{titel}'")


@schritt("Startzeit Sollte Unter Sekunden Liegen")
def _(k, sekunden):
    t = k.app.startup_seconds
    _pruefe(t < float(sekunden), f"Start dauerte {t:.1f} s")


@schritt("Text Sollte Sichtbar Sein")
def _(k, text):
    _pruefe(k.app.text_exists(text), f"Text fehlt: '{text}'")


@schritt("Button Sollte Existieren")
def _(k, name):
    _pruefe(k.app.button_exists(name), f"Button fehlt: '{name}'")


@schritt("Tabelle Sollte Enthalten")
def _(k, text):
    _pruefe(k.app.cell_exists(text), f"Tabellenzelle fehlt: '{text}'")


@schritt("Zeile Sollte Angezeigt Werden")
def _(k, text):
    _pruefe(k.app.is_row_shown(text), f"Zeile ist ausgeblendet: '{text}'")


@schritt("Zeile Sollte Ausgeblendet Sein")
def _(k, text):
    _pruefe(not k.app.is_row_shown(text), f"Zeile ist noch sichtbar: '{text}'")


@schritt("Zeile Sollte Im Sichtbaren Bereich Sein")
def _(k, text):
    _pruefe(k.app.is_row_in_view(text), f"Zeile nicht im sichtbaren Bereich: '{text}'")


@schritt("Zeile Sollte Nicht Im Sichtbaren Bereich Sein")
def _(k, text):
    _pruefe(not k.app.is_row_in_view(text), f"Zeile ist im sichtbaren Bereich: '{text}'")


@schritt("Suchfeld Sollte Enthalten")
def _(k, text):
    wert = k.app.search_value()
    _pruefe(wert == text, f"Suchfeld enthält '{wert}', erwartet '{text}'")


@schritt("Dialog Sollte Erscheinen")
def _(k, titel):
    _pruefe(k.app.wait_for_dialog(titel), f"Dialog erscheint nicht: '{titel}'")


@schritt("Dialog Sollte Geschlossen Sein")
def _(k, titel):
    _pruefe(k.app.wait_dialog_closed(titel), f"Dialog ist noch offen: '{titel}'")


@schritt("Datei Sollte Existieren")
def _(k, pfad, beginnt_mit):
    datei = k.app.library / pfad
    _pruefe(datei.is_file(), f"Datei fehlt: {pfad}")
    inhalt = datei.read_text(encoding="utf-8")
    _pruefe(inhalt.startswith(beginnt_mit), f"Inhalt von {pfad} ist '{inhalt[:40]}'")


@schritt("Anzahl Textdateien Sollte Unveraendert Sein")
def _(k):
    jetzt = len(k.app.library_files("**/*.txt"))
    vorher = k.gemerkt.get("txt")
    _pruefe(vorher is not None, "Vorher wurde nicht 'Merke Anzahl Textdateien' ausgeführt")
    _pruefe(jetzt == vorher, f"Vorher {vorher}, jetzt {jetzt} .txt-Dateien")


@schritt("Zeile Sollte In Allen Spalten Blau Sein")
def _(k, text):
    anteile = k.app.row_blue_ratios(text)
    _pruefe(len(anteile) >= 8, f"Nur {len(anteile)} Spalten gefunden")
    _pruefe(all(a >= 0.5 for a in anteile),
            f"Nicht überall blau (Anteil je Spalte): {[round(a, 2) for a in anteile]}")


@schritt("Zeile Sollte Nicht Blau Sein")
def _(k, text):
    anteile = k.app.row_blue_ratios(text)
    _pruefe(all(a < 0.1 for a in anteile),
            f"Zeile ist blau (Anteil je Spalte): {[round(a, 2) for a in anteile]}")


@schritt("Fenster Sollte Auf Den Bildschirm Passen")
def _(k):
    fenster, schirm = k.app.window_rect(), k.app.screen_rect()
    _pruefe(schirm.contains(fenster, tolerance=10),
            f"Fenster {fenster} ist größer als der Bildschirm {schirm}")


@schritt("Button Sollte Im Fenster Liegen")
def _(k, name):
    _pruefe(k.app.window_rect().contains(k.app.button_rect(name)),
            f"'{name}' liegt außerhalb des Fensters")


@schritt("Button Sollte Auf Dem Bildschirm Liegen")
def _(k, name):
    _pruefe(k.app.screen_rect().contains(k.app.button_rect(name)),
            f"'{name}' liegt außerhalb des Bildschirms")


@schritt("Fenster Sollte Maximiert Sein")
def _(k):
    _pruefe(k.app.is_maximized(), "Fenster ist nicht maximiert")


@schritt("Fenster Sollte Nicht Maximiert Sein")
def _(k):
    _pruefe(not k.app.is_maximized(), "Fenster ist noch maximiert")
