"""01 pytest – führt die zentrale Testspezifikation aus.

Hier steht KEIN einzelner Testfall. pytest liest
00_spezifikation/testfaelle.yaml und erzeugt daraus pro Eintrag einen Test
(Name = ID, z. B. "TC-04"). Neuer Testfall = nur die YAML-Datei ändern.
"""
import pytest

from spec import fuehre_testfall_aus, lade_spezifikation

TESTFAELLE = lade_spezifikation()


@pytest.mark.parametrize("fall", TESTFAELLE, ids=[f.id for f in TESTFAELLE])
def test_spezifikation(fall, kontext):
    fuehre_testfall_aus(kontext, fall)
