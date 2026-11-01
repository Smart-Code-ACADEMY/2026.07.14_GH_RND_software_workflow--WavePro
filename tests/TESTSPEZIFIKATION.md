# Testspezifikation – Wave Pro (Windows-EXE)

| | |
|---|---|
| **Testobjekt** | Wave Pro – Music Studio, EXE aus `publish/` |
| **Zentrale Testfälle** | **`spec/testfaelle.yaml`** – die einzige Quelle. pytest und Robot Framework lesen diese Datei direkt. |
| **Dieses Dokument** | Erklärt Rahmen, Werkzeuge und Grenzen. Die Tabelle in Abschnitt 3 wird automatisch aus der YAML-Datei erzeugt. |

---

## 1. So hängt alles zusammen

```
                spec/testfaelle.yaml      ← HIER werden Testfälle definiert (einzige Stelle)
                         │
                 common/spec.py           ← liest + prüft die YAML-Datei
          ┌──────────────┼───────────────────────────┐
          ▼              ▼                           ▼
   pytest_suite/   robot_suite/yaml_parser.py   tools/erzeuge_uebersicht.py
   (pytest)        (Robot Framework)            (Tabelle in diesem Dokument)
          └──────────────┬──────────────┘
                         ▼
               common/schritte.py         ← Schritt-Name → echte Aktion/Prüfung
                         ▼
               common/wavepro.py          ← pywinauto bedient die EXE
                         ▼
                   Wave Pro (EXE)
```

**Neuen Testfall anlegen oder ändern:** nur `spec/testfaelle.yaml` bearbeiten. Beide Werkzeuge und die Tabelle hier übernehmen das automatisch.

---

## 2. Werkzeuge – was passt zur EXE?

| Werkzeug | Für Wave Pro? | Aufgabe |
|---|---|---|
| **pywinauto** | ✅ | Bedient die EXE: Fenster, Buttons, Texte, Tabelle, Maus, Tastatur. |
| **pytest** | ✅ | Liest die Spezifikation und führt sie aus. Bericht für Entwickler. |
| **Robot Framework** | ✅ | Liest **dieselbe** Spezifikation und führt sie aus. Schritt-für-Schritt-Protokoll. |
| **Playwright / Selenium** | ❌ | Nur für Webseiten im Browser – nicht für eine Windows-EXE. |

---

## 3. Die Testfälle (automatisch aus `spec/testfaelle.yaml`)

Vor **jedem** Testfall: neue Testbibliothek (60 stille WAV-Dateien `Artist NN - Song NN` in `Pop/` und `Rock/`, leerer Ordner `To-Do/`) und frisch gestartete EXE. Danach wird die EXE geschlossen und die Testdaten werden gelöscht.

<!-- AUTO-START: aus spec/testfaelle.yaml erzeugt – nicht von Hand ändern -->
| ID | Prinzip | Aktionen (was der Test tut) | Erwartetes Ergebnis (was geprüft wird) |
|---|---|---|---|
| **TC-01** Hauptfenster erscheint | Start / Fenster | – | 1. Fenstertitel Sollte Beginnen Mit „Wave Pro - Music Studio“<br>2. Startzeit Sollte Unter Sekunden Liegen „30“ |
| **TC-02** Beschriftungen sind sichtbar | Texte lesen | – | 1. Text Sollte Sichtbar Sein „60 songs“<br>2. Text Sollte Sichtbar Sein „Nothing is playing“<br>3. Button Sollte Existieren „Play Filtered“<br>4. Button Sollte Existieren „Reset filters“<br>5. Button Sollte Existieren „+ To-Do“ |
| **TC-03** Tabelle zeigt die Lieder | Daten in Tabelle | – | 1. Tabelle Sollte Enthalten „Artist 01“<br>2. Tabelle Sollte Enthalten „Song 01“<br>3. Tabelle Sollte Enthalten „Artist 60“<br>4. Zeile Sollte Im Sichtbaren Bereich Sein „Artist 01“ |
| **TC-04** Suche filtert die Liste | Text eingeben | 1. Tippe In Suchfeld „Song 07“ | 2. Suchfeld Sollte Enthalten „Song 07“<br>3. Zeile Sollte Angezeigt Werden „Song 07“<br>4. Zeile Sollte Ausgeblendet Sein „Song 08“ |
| **TC-05** Reset filters setzt zurück | Button klicken | 1. Tippe In Suchfeld „Song 07“<br>3. Klicke Button „Reset filters“ | 2. Zeile Sollte Ausgeblendet Sein „Song 08“<br>4. Suchfeld Sollte Enthalten „“<br>5. Zeile Sollte Angezeigt Werden „Song 08“ |
| **TC-06** To-Do erzeugt eine Datei | Dialog + Datei auf Festplatte | 1. Klicke Button „+ To-Do“<br>3. Tippe In Dialog „Add To-Do“, „TC06 Testlied“<br>4. Klicke Im Dialog „Add To-Do“, „Create To-Do“ | 2. Dialog Sollte Erscheinen „Add To-Do“<br>5. Dialog Sollte Geschlossen Sein „Add To-Do“<br>6. Datei Sollte Existieren „To-Do/TC06 Testlied.txt“, „To-Do: TC06 Testlied“<br>7. Tabelle Sollte Enthalten „TC06 Testlied“ |
| **TC-07** Tastenkürzel öffnet Dialog, Esc bricht ab | Tastatur-Kürzel | 1. Merke Anzahl Textdateien<br>2. Druecke Strg+E Plus „T“<br>4. Druecke Escape | 3. Dialog Sollte Erscheinen „Add To-Do“<br>5. Dialog Sollte Geschlossen Sein „Add To-Do“<br>6. Anzahl Textdateien Sollte Unveraendert Sein |
| **TC-08** Scrollen mit End, Top und Mausrad | Scrollen | 2. Klicke Button „End“<br>5. Klicke Button „Top“<br>7. Scrolle Mit Mausrad „-10“ | 1. Zeile Sollte Nicht Im Sichtbaren Bereich Sein „Artist 60“<br>3. Zeile Sollte Im Sichtbaren Bereich Sein „Artist 60“<br>4. Zeile Sollte Nicht Im Sichtbaren Bereich Sein „Artist 01“<br>6. Zeile Sollte Im Sichtbaren Bereich Sein „Artist 01“<br>8. Zeile Sollte Nicht Im Sichtbaren Bereich Sein „Artist 01“ |
| **TC-09** Auswahl ist in jeder Spalte blau | Visuell (Pixel) | 1. Klicke Zeile „Artist 02“<br>2. Speichere Screenshot „tc09_auswahl.png“ | 3. Zeile Sollte In Allen Spalten Blau Sein „Artist 02“<br>4. Zeile Sollte Nicht Blau Sein „Artist 04“ |
| **TC-10** Bedienelemente bleiben erreichbar | Fenstergröße | 2. Aendere Fenstergroesse „900“, „600“<br>6. Maximiere Fenster<br>11. Stelle Fenster Wieder Her | 1. Fenster Sollte Auf Den Bildschirm Passen<br>3. Button Sollte Im Fenster Liegen „Reset filters“<br>4. Button Sollte Im Fenster Liegen „End“<br>5. Button Sollte Im Fenster Liegen „+ To-Do“<br>7. Fenster Sollte Maximiert Sein<br>8. Button Sollte Auf Dem Bildschirm Liegen „Reset filters“<br>9. Button Sollte Auf Dem Bildschirm Liegen „End“<br>10. Button Sollte Auf Dem Bildschirm Liegen „+ To-Do“<br>12. Fenster Sollte Nicht Maximiert Sein |
<!-- AUTO-ENDE -->

---

## 4. Was ist automatisch testbar – und was nicht?

| Funktion | Testbar? | Begründung |
|---|---|---|
| Fenster, Titel, Texte, Buttons | ✅ | Qt meldet Name und Typ an Windows (UI Automation). |
| Suchfeld, Dialoge, Tastenkürzel | ✅ | Echte Tastatur- und Mauseingaben. |
| Tabelleninhalt, Filtern, Scrollen | ✅ | Jede Textzelle hat einen Namen und eine Position. |
| Dateien auf der Festplatte | ✅ | Python prüft die Datei direkt. |
| Farben und Layout | ◐ | Nur über Pixel-Messung (TC-09). Kann von Nachtmodus oder HDR beeinflusst werden. |
| **Schloss-Buttons, Kategorie-Auswahl, Sterne und 🗑 in den Tabellenzeilen** | ◐ | Qt meldet diese Bedienelemente **nicht** an Windows. Nur per Klick auf eine berechnete Position erreichbar – fragil. *Lösung: im App-Code Test-Namen ergänzen.* |
| Kurze Hinweise (Toasts, 1,5–3 s) | ◐ | Möglich, aber zeitkritisch. |
| Ton ist hörbar, VU-Meter-Animation | ❌ | Ein Test kann nicht hören; bewegte Grafik hat keine festen Werte. |
| Globale Hotkeys, während eine andere App aktiv ist | ❌ | Hängt von Systemrechten und der App im Vordergrund ab. |

---

## 5. Testumgebung und Schutz deiner Daten

- **PC:** Windows 10/11, Python 3.11. Wave Pro muss **geschlossen** sein.
- **Während des Laufs:** Maus und Tastatur ca. 5 Min. nicht benutzen.
- **Deine Daten:**
  - Deine echte Musik wird nie berührt.
  - Einstellungen, Änderungshistorie und offene Aufgaben werden vorher gesichert und danach exakt wiederhergestellt – nach einem Absturz beim nächsten Lauf.

---

## 6. Grenzen und Befunde

- **Prüfung vor der Auslieferung:** Beide Werkzeuge liefen gegen die echte App, mit Qts Barrierefreiheits-Daten – denselben Daten, die pywinauto unter Windows liest. **Der erste Lauf auf deinem Windows-PC ist die endgültige Abnahme.**
- **TC-09** schlägt fehl, wenn deine EXE vor der Korrektur der Auswahlfarbe gebaut wurde → EXE mit `build.py` neu bauen.
- **TC-10** schlägt **gewollt** fehl, wenn der Bildschirm schmaler als ca. 1320 px ist (z. B. 1920 px bei 150 % Skalierung). Wave Pro ist dann breiter als der Bildschirm – ein echter Befund.
