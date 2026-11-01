"""Schreibt die Testfall-Tabelle in TESTSPEZIFIKATION.md – aus der YAML-Datei.

Der Abschnitt zwischen den Markierungen AUTO-START und AUTO-ENDE wird
komplett neu erzeugt. So zeigt das Dokument immer genau das, was die
Werkzeuge ausführen. Nicht von Hand bearbeiten – stattdessen
spec/testfaelle.yaml ändern.

    python tools/erzeuge_uebersicht.py           → Tabelle aktualisieren
    python tools/erzeuge_uebersicht.py --check   → nur prüfen (Fehler, wenn veraltet)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.spec import SPEC_DATEI, lade_spezifikation  # noqa: E402
from common.wavepro import TESTS_DIR  # noqa: E402

DOKUMENT = TESTS_DIR / "TESTSPEZIFIKATION.md"
START = "<!-- AUTO-START: aus spec/testfaelle.yaml erzeugt – nicht von Hand ändern -->"
ENDE = "<!-- AUTO-ENDE -->"


def _zelle(text: str) -> str:
    return text.replace("|", "\\|")


def tabelle() -> str:
    zeilen = [
        "| ID | Prinzip | Aktionen (was der Test tut) | Erwartetes Ergebnis (was geprüft wird) |",
        "|---|---|---|---|",
    ]
    for fall in lade_spezifikation():
        aktionen, pruefungen = [], []
        for nr, s in enumerate(fall.schritte, start=1):
            (pruefungen if s.ist_pruefung else aktionen).append(f"{nr}. {_zelle(s.lesbar())}")
        zeilen.append(
            f"| **{fall.id}** {_zelle(fall.titel)} | {_zelle(fall.prinzip)} "
            f"| {'<br>'.join(aktionen) or '–'} | {'<br>'.join(pruefungen)} |")
    return "\n".join(zeilen)


def neuer_inhalt(alt: str) -> str:
    if START not in alt or ENDE not in alt:
        raise SystemExit(f"Markierungen fehlen in {DOKUMENT.name}.")
    vorne, rest = alt.split(START, 1)
    _, hinten = rest.split(ENDE, 1)
    return f"{vorne}{START}\n{tabelle()}\n{ENDE}{hinten}"


def main() -> int:
    alt = DOKUMENT.read_text(encoding="utf-8")
    neu = neuer_inhalt(alt)
    if "--check" in sys.argv:
        if neu != alt:
            print("VERALTET: bitte 'python tools/erzeuge_uebersicht.py' ausführen.")
            return 1
        print("OK: TESTSPEZIFIKATION.md passt zu", SPEC_DATEI.name)
        return 0
    DOKUMENT.write_text(neu, encoding="utf-8")
    print(f"Aktualisiert: {DOKUMENT.name} ({SPEC_DATEI.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
