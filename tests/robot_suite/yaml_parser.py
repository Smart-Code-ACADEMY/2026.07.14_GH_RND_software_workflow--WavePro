"""Robot-Framework-Parser: liest die zentrale Testspezifikation (YAML).

Robot Framework kennt YAML-Testfälle nicht von selbst. Dieser kleine Parser
bringt es ihm bei: Er liest spec/testfaelle.yaml und baut daraus eine
Robot-Testsuite – ein Robot-Test pro Testfall, ein Robot-Schritt pro
YAML-Schritt. Es gibt keine handgeschriebene .robot-Datei mehr.

Aufruf (siehe run_robot.bat):
    python -m robot --parser robot_suite/yaml_parser.py spec/testfaelle.yaml
"""
import sys
from pathlib import Path

from robot.running import TestSuite
from robot.utils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.spec import lade_spezifikation  # noqa: E402

EXTENSION = ".yaml"
LIBRARY = str(Path(__file__).with_name("WaveProLibrary.py"))


def parse(source: Path, defaults=None) -> TestSuite:
    faelle = lade_spezifikation(Path(source))
    suite = TestSuite(name="Wave Pro Testspezifikation", source=source,
                      doc=f"Automatisch erzeugt aus {Path(source).name}")
    suite.resource.imports.library(LIBRARY)
    suite.setup.config(name="Sichere Benutzerprofil")
    suite.teardown.config(name="Stelle Benutzerprofil Wieder Her")

    for fall in faelle:
        test = suite.tests.create(
            name=fall.name,
            doc=f"Prinzip: {fall.prinzip}. {fall.ziel}",
            tags=[fall.id, fall.prinzip])
        test.setup.config(name="Starte Wave Pro Mit Testbibliothek")
        test.teardown.config(name="Schliesse Wave Pro")
        for aufruf in fall.schritte:
            # escape(): Texte wie "${…}" werden NICHT als Robot-Variable gelesen.
            test.body.create_keyword(
                name=aufruf.name,
                args=[escape(w) if w else "${EMPTY}" for w in aufruf.werte])
    return suite
