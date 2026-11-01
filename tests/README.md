# Tests für Wave Pro (EXE)

Was die Tests prüfen und warum: **[TESTSPEZIFIKATION.md](TESTSPEZIFIKATION.md)**

## Schnellstart (Windows)

1. **Wave Pro schließen.**
2. Einmalig installieren (im Projektordner):
   ```bat
   pip install -r tests\requirements-tests.txt
   ```
3. Starten – dabei Maus und Tastatur ca. 5 Minuten nicht benutzen:
   ```bat
   tests\run_all.bat
   ```
4. Ergebnisse öffnen:
   - `tests\reports\pytest_report.html`
   - `tests\reports\robot\report.html`

Die EXE wird automatisch in `publish\` gesucht. Eine andere EXE wählst du so:
`set WAVEPRO_EXE=C:\Pfad\zu\WavePro.exe`

## Ordner

```
tests/
├── TESTSPEZIFIKATION.md   ← die 10 Testfälle: was ist testbar, was nicht
├── README.md              ← diese Anleitung
├── requirements-tests.txt ← pywinauto, pytest, Robot Framework, Pillow
├── run_pytest.bat / run_robot.bat / run_all.bat
├── common/wavepro.py      ← steuert die EXE (pywinauto) + Schutz deiner Daten
├── pytest_suite/          ← die 10 Tests mit pytest
├── robot_suite/           ← dieselben 10 Tests mit Robot Framework
└── reports/               ← Berichte und Screenshots (werden erzeugt)
```

## Sicherheit

- Die Tests arbeiten nur mit einer **temporären Testbibliothek** (60 stille WAV-Dateien).
  Deine Musik wird nie berührt.
- Deine Wave-Pro-Einstellungen, die Historie und offene Aufgaben werden vorher gesichert und
  danach wiederhergestellt.
- Bricht ein Lauf ab, stellt der **nächste** Lauf die Sicherung aus
  `tests\.profile_backup\` automatisch wieder her.
