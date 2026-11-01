# Tests für Wave Pro (EXE)

**Testfälle stehen an EINER Stelle: [`spec/testfaelle.yaml`](spec/testfaelle.yaml).**
pytest und Robot Framework lesen diese Datei direkt und führen sie aus.
Rahmen, Werkzeuge und Grenzen: [TESTSPEZIFIKATION.md](TESTSPEZIFIKATION.md)

## Schnellstart (Windows)

1. **Wave Pro schließen.**
2. Einmalig im Projektordner: `pip install -r tests\requirements-tests.txt`
3. `tests\run_all.bat` starten. Dabei ca. 5 Min. Maus und Tastatur nicht benutzen.
4. Berichte öffnen:
   - `tests\reports\pytest_report.html`
   - `tests\reports\robot\report.html`

Andere EXE als in `publish\` testen: `set WAVEPRO_EXE=C:\Pfad\WavePro.exe`

## Testfall ändern oder hinzufügen

1. `spec\testfaelle.yaml` bearbeiten – erlaubte Schritte stehen in `common\schritte.py`.
2. Die Tests starten. Tippfehler werden sofort gemeldet. Die Tabelle in
   `TESTSPEZIFIKATION.md` aktualisiert sich automatisch.

## Ordner

```
tests/
├── spec/testfaelle.yaml        ★ die zentrale Testspezifikation (einzige Quelle)
├── TESTSPEZIFIKATION.md        Begleitdokument; Tabelle wird aus der YAML erzeugt
├── common/
│   ├── spec.py                 liest + prüft die YAML
│   ├── schritte.py             Schritt-Name → Aktion/Prüfung
│   └── wavepro.py              pywinauto steuert die EXE + Schutz deiner Daten
├── pytest_suite/               pytest liest die YAML
├── robot_suite/                Robot Framework liest die YAML
├── tools/erzeuge_uebersicht.py schreibt die Tabelle ins Dokument
├── run_pytest.bat / run_robot.bat / run_all.bat
├── requirements-tests.txt
└── reports/                    Berichte und Screenshots (werden erzeugt)
```

## Sicherheit

- Gearbeitet wird nur mit einer temporären Testbibliothek. Deine Musik wird nie berührt.
- Deine Einstellungen, die Historie und offene Aufgaben werden gesichert und
  danach wiederhergestellt.
- Bricht ein Lauf ab, stellt der nächste Lauf die Sicherung automatisch wieder her.
