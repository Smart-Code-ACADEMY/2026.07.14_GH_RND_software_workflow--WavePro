*** Settings ***
Documentation     Wave Pro – dieselben 10 Testfälle wie pytest_suite/test_wavepro.py,
...               geschrieben als lesbare Schlüsselwörter (Robot Framework).
...               Jeder Test startet die EXE neu mit einer eigenen Testbibliothek.
Library           WaveProLibrary.py
Suite Setup       Sichere Benutzerprofil
Suite Teardown    Stelle Benutzerprofil Wieder Her
Test Setup        Starte Wave Pro Mit Testbibliothek
Test Teardown     Schliesse Wave Pro


*** Test Cases ***
TC-01 Start: Hauptfenster erscheint
    Fenstertitel Sollte Beginnen Mit    Wave Pro - Music Studio
    Startzeit Sollte Unter 30 Sekunden Liegen

TC-02 Texte: Beschriftungen sind sichtbar
    Text Sollte Sichtbar Sein    60 songs
    Text Sollte Sichtbar Sein    Nothing is playing
    Button Sollte Existieren    Play Filtered
    Button Sollte Existieren    Reset filters
    Button Sollte Existieren    + To-Do

TC-03 Daten: Tabelle zeigt die Lieder
    Tabelle Sollte Enthalten    Artist 01
    Tabelle Sollte Enthalten    Song 01
    Tabelle Sollte Enthalten    Artist 60
    Zeile Sollte Im Sichtbaren Bereich Sein    Artist 01

TC-04 Eingabe: Suche filtert die Liste
    Tippe In Suchfeld    Song 07
    Suchfeld Sollte Enthalten    Song 07
    Zeile Sollte Angezeigt Werden    Song 07
    Zeile Sollte Ausgeblendet Sein    Song 08

TC-05 Klick: Reset filters setzt zurück
    Tippe In Suchfeld    Song 07
    Zeile Sollte Ausgeblendet Sein    Song 08
    Klicke Button    Reset filters
    Suchfeld Sollte Enthalten    ${EMPTY}
    Zeile Sollte Angezeigt Werden    Song 08

TC-06 Dialog + Datei: To-Do erzeugt .txt
    Klicke Button    + To-Do
    Dialog Sollte Erscheinen    Add To-Do
    Tippe In Dialog    Add To-Do    TC06 Testlied
    Klicke Im Dialog    Add To-Do    Create To-Do
    Dialog Sollte Geschlossen Sein    Add To-Do
    Datei Sollte Existieren    To-Do/TC06 Testlied.txt    To-Do: TC06 Testlied
    Tabelle Sollte Enthalten    TC06 Testlied

TC-07 Tastatur: Strg+E+T öffnet Dialog, Esc bricht ab
    ${vorher}=    Zaehle Textdateien
    Druecke Strg+E+T
    Dialog Sollte Erscheinen    Add To-Do
    Druecke Escape
    Dialog Sollte Geschlossen Sein    Add To-Do
    ${nachher}=    Zaehle Textdateien
    Should Be Equal As Integers    ${vorher}    ${nachher}

TC-08 Scrollen: End, Top und Mausrad
    Zeile Sollte Nicht Im Sichtbaren Bereich Sein    Artist 60
    Klicke Button    End
    Zeile Sollte Im Sichtbaren Bereich Sein    Artist 60
    Zeile Sollte Nicht Im Sichtbaren Bereich Sein    Artist 01
    Klicke Button    Top
    Zeile Sollte Im Sichtbaren Bereich Sein    Artist 01
    Scrolle Mit Mausrad    -10
    Zeile Sollte Nicht Im Sichtbaren Bereich Sein    Artist 01

TC-09 Visuell: Auswahl ist in jeder Spalte blau
    Klicke Zeile    Artist 02
    Speichere Screenshot    tc09_auswahl_robot.png
    Zeile Sollte In Allen Spalten Blau Sein    Artist 02
    Zeile Sollte Nicht Blau Sein    Artist 04

TC-10 Fenster: Bedienelemente bleiben erreichbar
    Fenster Sollte Auf Den Bildschirm Passen
    Aendere Fenstergroesse    900    600
    Button Sollte Im Fenster Liegen    Reset filters
    Button Sollte Im Fenster Liegen    End
    Button Sollte Im Fenster Liegen    + To-Do
    Maximiere Fenster
    Fenster Sollte Maximiert Sein
    Button Sollte Auf Dem Bildschirm Liegen    Reset filters
    Button Sollte Auf Dem Bildschirm Liegen    End
    Button Sollte Auf Dem Bildschirm Liegen    + To-Do
    Stelle Fenster Wieder Her
    Fenster Sollte Nicht Maximiert Sein
