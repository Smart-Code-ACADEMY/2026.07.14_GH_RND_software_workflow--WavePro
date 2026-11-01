# Tests für Wave Pro (EXE)

Testfälle stehen an EINER Stelle: **`00_spezifikation/testfaelle.yaml`**.
Drei Werkzeuge lesen diese Datei und müssen dasselbe Ergebnis liefern.

## Schnellstart (Windows)

1. **Wave Pro schließen.**
2. Einmalig im Projektordner: `pip install -r tests\requirements-tests.txt`
3. `tests\run_00_alle.bat` starten. Maus und Tastatur ca. 15 Min. nicht benutzen.
4. Am Ende öffnet sich **`tests\reports\00_vergleich.html`**: alle drei Werkzeuge nebeneinander.

Ein einzelnes Werkzeug: `run_01_pytest.bat`, `run_02_robot.bat` oder `run_03_pywinauto.bat`.
Andere EXE als in `publish\`: `set WAVEPRO_EXE=C:\Pfad\WavePro.exe`

## Ordner (nummeriert = Reihenfolge)

```
tests/
├── 00_spezifikation/
│   ├── testfaelle.yaml         ★ zentrale Testspezifikation – nur hier Tests ändern
│   └── TESTSPEZIFIKATION.md    Begleitdokument; Testfall-Tabelle wird automatisch erzeugt
├── 01_pytest/                  Werkzeug 1: pytest liest die YAML
├── 02_robot/                   Werkzeug 2: Robot Framework liest die YAML
├── 03_pywinauto/               Werkzeug 3: pywinauto pur, ohne Testframework
├── 09_gemeinsam/               Code, den alle drei teilen
│   ├── wavepro.py              Motor: pywinauto-Befehle + Schutz deiner Daten
│   ├── schritte.py             Schritt-Name → Aktion / Prüfung
│   ├── sitzung.py              Vorbereitung + Aufräumen
│   ├── spec.py                 liest + prüft die YAML
│   ├── erzeuge_uebersicht.py   schreibt die Tabelle ins Dokument
│   └── vergleiche_ergebnisse.py erstellt reports/00_vergleich.html
├── reports/                    (wird erzeugt)
│   ├── 00_vergleich.html       alle drei Werkzeuge nebeneinander
│   ├── 01_pytest/              report.html, junit.xml, screenshots/, fehler_screenshots/
│   ├── 02_robot/               report.html, log.html, output.xml, screenshots/, …
│   └── 03_pywinauto/           bericht.html, ergebnis.json, screenshots/, …
├── run_00_alle.bat  run_01_pytest.bat  run_02_robot.bat  run_03_pywinauto.bat
└── requirements-tests.txt
```

## Testfall ändern

`00_spezifikation\testfaelle.yaml` bearbeiten (erlaubte Schritte: `09_gemeinsam\schritte.py`)
und einen Lauf starten. Tippfehler werden sofort gemeldet.

## Sicherheit

- Nur eine temporäre Testbibliothek wird benutzt; deine Musik wird nie berührt.
- Einstellungen, Historie und offene Aufgaben werden gesichert und wiederhergestellt.
- Bricht ein Lauf ab, stellt der nächste Lauf die Sicherung automatisch wieder her.
