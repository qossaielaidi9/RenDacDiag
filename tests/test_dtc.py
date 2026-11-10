from rendacdiag.dtc import decode_uds, extract_codes, is_generic


def test_extract_obd_codes():
    assert extract_codes("La valise affiche p0301 puis P0300, encore P0301") == ["P0301", "P0300"]


def test_decode_uds_examples_from_real_screen():
    assert decode_uds("DTC038096") == ("P0380", "96", "défaillance d'un composant interne")
    assert decode_uds("DTC145392")[:2] == ("P1453", "92")


def test_uds_codes_are_extracted():
    assert extract_codes("DTC038096 actif, DTC145396 mémoire") == ["P0380", "P1453"]


def test_generic_vs_manufacturer():
    assert is_generic("P0301") and is_generic("P2002") and not is_generic("P1453")
