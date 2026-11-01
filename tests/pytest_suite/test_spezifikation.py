"""pytest führt die zentrale Testspezifikation aus.

Hier steht KEIN einzelner Testfall. pytest liest spec/testfaelle.yaml und
erzeugt daraus für jeden Eintrag einen Test (Name = ID, z. B. "TC-04").
Neuer Testfall = nur die YAML-Datei ändern.
"""
import pytest

from common.schritte import Kontext
from common.spec import fuehre_testfall_aus, lade_spezifikation

TESTFAELLE = lade_spezifikation()


@pytest.mark.parametrize("fall", TESTFAELLE, ids=[f.id for f in TESTFAELLE])
def test_spezifikation(fall, wavepro):
    fuehre_testfall_aus(Kontext(wavepro), fall)
