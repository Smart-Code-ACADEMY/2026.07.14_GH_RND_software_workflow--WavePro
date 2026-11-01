"""Liest die zentrale Testspezifikation (spec/testfaelle.yaml) und prüft sie.

Wird von pytest UND Robot Framework benutzt. Fehler in der Spezifikation
(unbekannter Schritt, falsche Anzahl Werte, doppelte ID …) werden gemeldet,
BEVOR die EXE gestartet wird.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

from .schritte import Kontext, finde_schritt
from .wavepro import TESTS_DIR

SPEC_DATEI = TESTS_DIR / "spec" / "testfaelle.yaml"


class SpezifikationsFehler(Exception):
    pass


@dataclass(frozen=True)
class SchrittAufruf:
    name: str          # so wie in der YAML-Datei geschrieben
    werte: tuple       # immer Texte (wie in Robot Framework)

    @property
    def ist_pruefung(self) -> bool:
        return finde_schritt(self.name).ist_pruefung

    def lesbar(self) -> str:
        if not self.werte:
            return self.name
        return self.name + " " + ", ".join(f"„{w}“" for w in self.werte)


@dataclass(frozen=True)
class Testfall:
    id: str
    titel: str
    prinzip: str
    ziel: str
    schritte: tuple

    @property
    def name(self) -> str:
        return f"{self.id} {self.titel}"


def _werte(roh) -> tuple:
    if roh is None:
        return ()
    if isinstance(roh, list):
        return tuple("" if w is None else str(w) for w in roh)
    return (str(roh),)


def lade_spezifikation(datei: Path = SPEC_DATEI) -> List[Testfall]:
    try:
        daten = yaml.safe_load(Path(datei).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SpezifikationsFehler(f"{datei}: YAML-Fehler: {e}") from e

    if not isinstance(daten, dict) or not isinstance(daten.get("testfaelle"), list):
        raise SpezifikationsFehler(f"{datei}: Liste 'testfaelle' fehlt.")

    faelle, ids = [], set()
    for nr, roh in enumerate(daten["testfaelle"], start=1):
        wo = f"{Path(datei).name}, Testfall Nr. {nr}"
        if not isinstance(roh, dict):
            raise SpezifikationsFehler(f"{wo}: muss ein Eintrag mit id/titel/schritte sein.")
        for feld in ("id", "titel", "prinzip", "schritte"):
            if not roh.get(feld):
                raise SpezifikationsFehler(f"{wo}: Feld '{feld}' fehlt.")
        tid = str(roh["id"])
        if tid in ids:
            raise SpezifikationsFehler(f"{wo}: ID {tid} ist doppelt.")
        ids.add(tid)

        schritte = []
        for snr, s in enumerate(roh["schritte"], start=1):
            ort = f"{tid}, Schritt {snr}"
            if not (isinstance(s, dict) and len(s) == 1):
                raise SpezifikationsFehler(f"{ort}: Format 'Schritt-Name: Wert' erwartet.")
            name, roh_wert = next(iter(s.items()))
            try:
                definition = finde_schritt(str(name))
            except KeyError as e:
                raise SpezifikationsFehler(f"{ort}: {e.args[0]}") from None
            werte = _werte(roh_wert)
            if definition.anzahl_werte == 1 and roh_wert is not None and not werte:
                werte = ("",)
            if len(werte) != definition.anzahl_werte:
                raise SpezifikationsFehler(
                    f"{ort}: '{name}' braucht {definition.anzahl_werte} Wert(e), "
                    f"bekommt {len(werte)}.")
            schritte.append(SchrittAufruf(str(name), werte))

        if not any(s.ist_pruefung for s in schritte):
            raise SpezifikationsFehler(f"{tid}: hat keine Prüfung ('… Sollte …').")

        faelle.append(Testfall(tid, str(roh["titel"]), str(roh["prinzip"]),
                               str(roh.get("ziel", "")), tuple(schritte)))
    return faelle


def fuehre_schritt_aus(kontext: Kontext, aufruf: SchrittAufruf) -> None:
    finde_schritt(aufruf.name).funktion(kontext, *aufruf.werte)


def fuehre_testfall_aus(kontext: Kontext, fall: Testfall) -> None:
    """Für pytest: alle Schritte nacheinander; Fehlermeldung nennt den Schritt."""
    for nr, aufruf in enumerate(fall.schritte, start=1):
        try:
            fuehre_schritt_aus(kontext, aufruf)
        except AssertionError as e:
            raise AssertionError(
                f"{fall.id} – Schritt {nr}: {aufruf.lesbar()}\n  → {e}") from None
