from rendacdiag.access import User

TECH = User("t", "technicien", "ATELIER-A")
REC = User("r", "receptionnaire", "ATELIER-B")
INV = User("i", "invite", "")


def test_exact_code_ranks_the_right_fiche_first(retriever):
    res = retriever.search("Que veut dire le code P0302 ?", TECH)
    assert res["documents"][0] == "DOC-DTC-P0302"


def test_uds_code_is_decoded_and_found(retriever):
    res = retriever.search("DTC038096 actif sur un Duster dCi", TECH)
    assert res["uds"][0]["code"] == "P0380"
    assert res["documents"][0] == "DOC-DTC-P0380"


def test_receptionist_never_sees_technical_documents(retriever):
    for q in ["causes du code P0301", "procédure vanne EGR", "schéma du préchauffage"]:
        res = retriever.search(q, REC, k=10)
        assert all(r["document_id"].startswith(("DOC-VOY", "DOC-GEN")) for r in res["resultats"])


def test_guest_only_sees_public_documents(retriever):
    res = retriever.search("voyant moteur et procédure de contrôle", INV, k=10)
    assert res["resultats"] and all(INV.can_read(retriever.by_id[r["element_id"]]) for r in res["resultats"])


def test_diesel_query_excludes_petrol_only_documents(retriever):
    res = retriever.search("perte de puissance sur un moteur diesel dCi", TECH, k=10)
    assert res["famille"] == "B"
    assert all(retriever.by_id[r["element_id"]]["famille"] in ("B", "AB") for r in res["resultats"])


def test_manufacturer_code_is_flagged(retriever):
    res = retriever.search("DTC145392 capteur pression différentielle FAP", TECH)
    assert "P1453" in res["codes_constructeur"]


def test_image_list_only_for_visual_queries():
    from rendacdiag.search.retriever import is_visual
    assert is_visual("schéma du préchauffage") and is_visual("témoin orange allumé")
    assert not is_visual("causes du code P0301") and not is_visual("perte de puissance en côte")
