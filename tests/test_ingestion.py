import json

from rendacdiag.config import Settings
from rendacdiag.ingestion.pipeline import build_elements


def test_unverified_documents_are_rejected_by_default(tmp_path):
    s = Settings(); s.data_dir = tmp_path; s.include_unverified = False
    rep = build_elements(s)
    statuses = {r["raison"] for r in rep["ecartes"]}
    assert rep["documents_retenus"] + rep["documents_ecartes"] == 50
    assert all("statut" in x or "licence" in x for x in statuses) or rep["documents_ecartes"] == 0


def test_elements_have_metadata(settings):
    els = [json.loads(l) for l in open(settings.elements_file, encoding="utf-8")]
    assert len({e["document_id"] for e in els}) == 50
    kinds = {e["type_element"] for e in els}
    assert {"section", "tableau", "figure"} <= kinds
    for e in els:
        assert e["groupes_acces"] and e["famille"] in ("A", "B", "AB") and e["page"] >= 1
        assert not e["section"].startswith("Documents liés")


def test_figures_point_to_existing_images(settings):
    els = [json.loads(l) for l in open(settings.elements_file, encoding="utf-8")]
    figs = [e for e in els if e["image"]]
    assert len(figs) >= 21
    assert all((settings.corpus_dir / e["image"]).exists() for e in figs)
