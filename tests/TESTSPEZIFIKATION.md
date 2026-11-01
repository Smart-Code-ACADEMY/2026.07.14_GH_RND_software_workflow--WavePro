# Testspezifikation – Wave Pro (Windows-EXE)

| | |
|---|---|
| **Testobjekt** | Wave Pro – Music Studio, EXE aus `publish/` |
| **Version der Spezifikation** | 1.0 – 01.11.2026 |
| **Ziel** | Mit 10 kurzen, **sehr unterschiedlichen** Testfällen zeigen, was an der EXE automatisch testbar ist – und was nicht. |
| **Automatisiert mit** | pywinauto (steuert die EXE) + pytest **und** Robot Framework (dieselben 10 Tests, zum Vergleich) |

---

## 1. Welche Werkzeuge passen zur EXE?

| Werkzeug | Für Wave Pro? | Warum |
|---|---|---|
| **pywinauto** | ✅ ja – der „Motor“ | Bedient Windows-Programme: Fenster, Buttons, Texte, Tabellen, Maus, Tastatur. |
| **pytest** | ✅ ja | Schreibt und startet Tests in Python. Gut für Entwickler. |
| **Robot Framework** | ✅ ja | Dieselben Tests als lesbare Sätze („Klicke Button“). Gut für Teams und Fachleute. |
| **Playwright** | ❌ nein | Nur für Webseiten im Browser. Wave Pro ist kein Browser-Programm. → Für deine Next.js-Website. |
| **Selenium** | ❌ nein | Ebenfalls nur Browser. |

> **Merksatz:** pywinauto *bedient* die App. pytest oder Robot *organisieren* die Tests und schreiben den Bericht.

---

## 2. Testumgebung und Testdaten

- **PC:** Windows 10/11, Python 3.11. Wave Pro muss **geschlossen** sein.
- **Während des Laufs (ca. 5 Min.):** Maus und Tastatur **nicht** benutzen – die Tests bewegen die echte Maus.
- **Testdaten:** Jeder Test erzeugt eine eigene, temporäre Musikbibliothek in `%TEMP%`:
  60 stille WAV-Dateien `Artist 01 - Song 01.wav` … `Artist 60 - Song 60.wav` in den Ordnern `Pop/`, `Rock/` und dem leeren Ordner `To-Do/`.
- **Schutz deiner Daten:**
  - Deine echte Musik wird **nie** geöffnet.
  - Deine Wave-Pro-Einstellungen, die Änderungshistorie und offene Aufgaben werden **vorher gesichert und danach exakt wiederhergestellt** – auch nach einem Absturz beim nächsten Lauf.

---

## 3. Die 10 Testfälle

Jeder Testfall prüft ein **anderes Prinzip**. Jeder Test startet die App frisch.

| ID | Prinzip | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| **TC-01** | Start / Fenster | EXE starten | Hauptfenster erscheint in < 30 s, Titel beginnt mit „Wave Pro - Music Studio“ |
| **TC-02** | Texte lesen | – | „60 songs“, „Nothing is playing“ sowie die Buttons „Play Filtered“, „Reset filters“ und „+ To-Do“ sind vorhanden |
| **TC-03** | Daten in Tabelle | – | Die Tabelle enthält „Artist 01“, „Song 01“ und „Artist 60“; die erste Zeile ist sichtbar |
| **TC-04** | Text eingeben | „Song 07“ ins Suchfeld tippen | Suchfeld = „Song 07“; Song 07 sichtbar, Song 08 ausgeblendet |
| **TC-05** | Button klicken | Suchen wie TC-04, dann „Reset filters“ klicken | Suchfeld leer, Song 08 wieder sichtbar |
| **TC-06** | Dialog + Datei | „+ To-Do“ → Name „TC06 Testlied“ → „Create To-Do“ | Dialog schließt; die Datei `To-Do/TC06 Testlied.txt` existiert **auf der Festplatte**; Zeile erscheint in der Tabelle |
| **TC-07** | Tastatur-Kürzel | Strg+E halten + T, dann Esc | To-Do-Dialog öffnet sich und schließt; **keine** neue Datei (Abbrechen erzeugt nichts) |
| **TC-08** | Scrollen | „⤓ End“, „⤒ Top“, Mausrad nach unten | Letzte bzw. erste Zeile liegt im sichtbaren Bereich; nach dem Mausrad ist die erste Zeile weggescrollt |
| **TC-09** | Visuell (Pixel) | Zeile 2 anklicken, Screenshot | **Jede** Spalte der Zeile ist ≥ 50 % blau; eine andere Zeile ist < 10 % blau |
| **TC-10** | Fenstergröße | Start, dann 900×600, dann maximieren, dann wiederherstellen | Startfenster passt auf den Bildschirm; die Buttons bleiben im Fenster bzw. auf dem Bildschirm |

**Wo im Code?** `pytest_suite/test_wavepro.py` (Funktion `test_tc01_…`) und `robot_suite/wavepro.robot` (Test „TC-01 …“).

---

## 4. Was ist automatisch testbar – und was nicht?

| Funktion | Testbar? | Begründung |
|---|---|---|
| Fenster, Titel, Texte, Buttons | ✅ | Qt meldet Name und Typ an Windows (UI Automation). |
| Suchfeld, Dialoge, Tastenkürzel | ✅ | Echte Tastatur- und Mauseingaben. |
| Tabelleninhalt, Filtern, Scrollen | ✅ | Jede Zelle hat einen Namen und eine Position auf dem Bildschirm. |
| Dateien auf der Festplatte (To-Do) | ✅ | Python prüft die Datei direkt. |
| Farben und Layout | ◐ teilweise | Nur über Pixel-Messung (TC-09). Kann von Bildschirm, Skalierung oder HDR abhängen. |
| **Schloss-Buttons, Kategorie-Auswahl, Sterne und 🗑 in den Tabellenzeilen** | ◐ teilweise | Qt meldet diese Bedienelemente **nicht** an Windows. Sie sind nur per Klick auf eine berechnete Position erreichbar – das ist fragil. *Lösung später: im App-Code gezielte Test-Namen ergänzen.* |
| Kurze Hinweise (Toasts, 1,5–3 s) | ◐ teilweise | Möglich, aber zeitkritisch → unzuverlässig. |
| Ton ist wirklich hörbar | ❌ | Ein Test kann nicht „hören“. Prüfbar ist nur, dass die Anzeige auf „Wiedergabe“ wechselt. |
| VU-Meter-Animation | ❌ | Bewegte Grafik ohne feste Werte. |
| Globale Hotkeys, während eine andere App aktiv ist | ❌ | Hängt von Systemrechten und der App im Vordergrund ab. |

---

## 5. Vergleich: gleiche Tests, zwei Werkzeuge

| | pytest | Robot Framework |
|---|---|---|
| Testfall sieht aus wie | Python-Code (`assert …`) | Deutsche Sätze (`Klicke Button  Reset filters`) |
| Gut für | Entwickler | Tester, Fachabteilung, Kunden |
| Bericht | `reports/pytest_report.html` | `reports/robot/report.html` + `log.html` (Schritt für Schritt) |
| Schritte auf Windows | identisch – beide nutzen `common/wavepro.py` | identisch |
| Screenshot bei Fehler | `reports/pytest_failures/` | `reports/robot_failures/` + im Log |

---

## 6. Ausführen

```bat
pip install -r tests\requirements-tests.txt
tests\run_pytest.bat      &REM nur pytest
tests\run_robot.bat       &REM nur Robot Framework
tests\run_all.bat         &REM beide (Vergleich)
```

Bestanden = grün im Bericht. Bei einem Fehler: Screenshot und Meldung im Bericht.

---

## 7. Grenzen und bisherige Befunde

- **Prüfung vor der Auslieferung:** Alle 10 Tests liefen mit pytest **und** Robot Framework unverändert gegen die echte App. Statt Windows war das Linux mit Qts Barrierefreiheits-Daten – das sind dieselben Daten, die pywinauto unter Windows liest.
  - Ergebnis: 10/10 grün mit beiden Werkzeugen.
  - Gegenprobe: Absichtlich eingebaute Fehler (Suche defekt, Auswahlfarbe falsch, Datei im falschen Ordner) wurden jeweils vom richtigen Test gefunden.
  - **Der erste Lauf auf deinem Windows-PC ist die endgültige Abnahme.**
- **Befund TC-10:** Ist der Bildschirm schmaler als ca. 1320 Pixel, z. B. ein Laptop mit 1920 px Breite und 150 % Windows-Skalierung, öffnet sich Wave Pro breiter als der Bildschirm (Mindestbreite 1316 px). TC-10 meldet das dann als **Fehler** – gewollt, denn es ist ein echtes Problem für Nutzer.
- **TC-09** misst Farben am Bildschirm. Wenn Windows eine Farbanpassung nutzt (z. B. Nachtmodus oder HDR), kann der Test fälschlich fehlschlagen → für den Lauf ausschalten.
