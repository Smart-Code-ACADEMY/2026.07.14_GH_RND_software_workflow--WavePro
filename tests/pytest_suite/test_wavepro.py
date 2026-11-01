"""Wave Pro – 10 Testfälle (pytest + pywinauto).

Jeder Testfall prüft ein ANDERES Prinzip (siehe TESTSPEZIFIKATION.md).
Dieselben 10 Testfälle gibt es in robot_suite/wavepro.robot.
"""
from common.wavepro import REPORTS_DIR, SONG_COUNT, WINDOW_TITLE_START


def test_tc01_start_hauptfenster(wavepro):
    """TC-01 Start: EXE startet, Hauptfenster erscheint mit richtigem Titel."""
    assert wavepro.window_title().startswith(WINDOW_TITLE_START)
    assert wavepro.startup_seconds < 30


def test_tc02_texte_vorhanden(wavepro):
    """TC-02 Texte: feste Beschriftungen sind sichtbar."""
    assert wavepro.text_exists(f"{SONG_COUNT} songs")
    assert wavepro.text_exists("Nothing is playing")
    for name in ("Play Filtered", "Reset filters", "+ To-Do"):
        assert wavepro.button_exists(name), f"Button fehlt: {name}"


def test_tc03_tabelle_zeigt_daten(wavepro):
    """TC-03 Daten: Tabelle zeigt die Lieder der Testbibliothek."""
    assert wavepro.cell_exists("Artist 01")
    assert wavepro.cell_exists("Song 01")
    assert wavepro.cell_exists(f"Artist {SONG_COUNT:02d}")
    assert wavepro.is_row_in_view("Artist 01")


def test_tc04_suche_filtert(wavepro):
    """TC-04 Eingabe: Suchtext filtert die Liste."""
    wavepro.type_search("Song 07")
    assert wavepro.search_value() == "Song 07"
    assert wavepro.is_row_shown("Song 07")
    assert not wavepro.is_row_shown("Song 08")


def test_tc05_reset_button(wavepro):
    """TC-05 Klick: 'Reset filters' leert die Suche, alle Lieder wieder da."""
    wavepro.type_search("Song 07")
    assert not wavepro.is_row_shown("Song 08")
    wavepro.click_button("Reset filters")
    assert wavepro.search_value() == ""
    assert wavepro.is_row_shown("Song 08")


def test_tc06_todo_dialog_erzeugt_datei(wavepro):
    """TC-06 Dialog + Datei: To-Do anlegen erzeugt eine .txt auf der Festplatte."""
    wavepro.click_button("+ To-Do")
    assert wavepro.wait_for_dialog("Add To-Do")
    wavepro.dialog_type("Add To-Do", "TC06 Testlied")
    wavepro.dialog_click("Add To-Do", "Create To-Do")
    assert wavepro.wait_dialog_closed("Add To-Do")

    txt = wavepro.library / "To-Do" / "TC06 Testlied.txt"
    assert txt.is_file(), "Datei wurde nicht angelegt"
    assert txt.read_text(encoding="utf-8").startswith("To-Do: TC06 Testlied")
    assert wavepro.cell_exists("TC06 Testlied")


def test_tc07_tastenkuerzel_oeffnet_dialog(wavepro):
    """TC-07 Tastatur: Strg+E+T öffnet den To-Do-Dialog, Esc bricht ab."""
    before = wavepro.library_files("**/*.txt")
    wavepro.press_ctrl_e_plus("T")
    assert wavepro.wait_for_dialog("Add To-Do")
    wavepro.press_escape()
    assert wavepro.wait_dialog_closed("Add To-Do")
    assert wavepro.library_files("**/*.txt") == before, "Abbrechen darf nichts anlegen"


def test_tc08_scrollen(wavepro):
    """TC-08 Scrollen: End/Top-Buttons und Mausrad bewegen die Liste."""
    last = f"Artist {SONG_COUNT:02d}"
    assert not wavepro.is_row_in_view(last)

    wavepro.click_button("End")
    assert wavepro.is_row_in_view(last)
    assert not wavepro.is_row_in_view("Artist 01")

    wavepro.click_button("Top")
    assert wavepro.is_row_in_view("Artist 01")

    wavepro.wheel_scroll_table(-10)
    assert not wavepro.is_row_in_view("Artist 01")


def test_tc09_auswahl_ist_blau(wavepro):
    """TC-09 Visuell: ausgewählte Zeile ist in JEDER Spalte blau (Pixelprüfung)."""
    wavepro.click_row("Artist 02")
    wavepro.screenshot(REPORTS_DIR / "screenshots" / "tc09_auswahl.png")

    selected = wavepro.row_blue_ratios("Artist 02")
    other = wavepro.row_blue_ratios("Artist 04")
    assert len(selected) >= 8, f"nur {len(selected)} Spalten gefunden"
    assert all(r >= 0.5 for r in selected), f"nicht überall blau: {selected}"
    assert all(r < 0.1 for r in other), f"falsche Zeile blau: {other}"


def test_tc10_fenstergroesse(wavepro):
    """TC-10 Fenster: Bedienelemente bleiben bei Größenänderung erreichbar."""
    key_buttons = ("Reset filters", "End", "+ To-Do")
    screen = wavepro.screen_rect()

    # Beim Start muss das Fenster vollständig auf den Bildschirm passen.
    assert screen.contains(wavepro.window_rect(), tolerance=10), \
        f"Startfenster {wavepro.window_rect()} größer als Bildschirm {screen}"

    wavepro.resize_window(900, 600)
    win = wavepro.window_rect()
    for name in key_buttons:
        assert win.contains(wavepro.button_rect(name)), f"{name} außerhalb (klein)"

    wavepro.maximize()
    assert wavepro.is_maximized()
    for name in key_buttons:
        assert screen.contains(wavepro.button_rect(name)), \
            f"{name} liegt außerhalb des Bildschirms (maximiert)"

    wavepro.restore()
    assert not wavepro.is_maximized()
