"""02 Robot Framework – Parser: liest die zentrale Testspezifikation (YAML).

Robot Framework kennt YAML-Testfälle nicht von selbst. Dieser Parser baut
aus 00_spezifikation/testfaelle.yaml eine Robot-Testsuite: ein Robot-Test
pro Testfall, ein Robot-Schritt pro YAML-Schritt.

Aufruf (siehe run_02_robot.bat):
    python -m robot --parser 02_robot/yaml_parser.py 00_spezifikation/testfaelle.yaml
"""
import sys
from pathlib import Path

from robot.running import TestSuite
from robot.utils import escape

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "09_gemeinsam"))

from spec import lade_spezifikation  # noqa: E402

EXTENSION = ".yaml"
# WICHTIG: as_posix() = Pfad mit "/". Mit Windows-"\" würde Robot die
# Zeichen als Escape lesen ("\t" = Tabulator) und die Bibliothek nicht finden.
LIBRARY = Path(__file__).with_name("WaveProLibrary.py").as_posix()


def parse(source: Path, defaults=None) -> TestSuite:
    faelle = lade_spezifikation(Path(source))
    suite = TestSuite(name="Wave Pro Testspezifikation", source=source,
                      doc=f"Automatisch erzeugt aus {Path(source).name}")
    suite.resource.imports.library(LIBRARY)
    suite.setup.config(name="Beginne Sitzung")
    suite.teardown.config(name="Beende Sitzung")

    for fall in faelle:
        test = suite.tests.create(
            name=fall.name,
            doc=f"Prinzip: {fall.prinzip}. {fall.ziel}",
            tags=[fall.id, fall.prinzip])
        test.setup.config(name="Starte Test")
        test.teardown.config(name="Beende Test")
        for aufruf in fall.schritte:
            # escape(): Texte wie "${…}" oder "\" bleiben genau so, wie sie sind.
            test.body.create_keyword(
                name=aufruf.name,
                args=[escape(w) if w else "${EMPTY}" for w in aufruf.werte])
    return suite
