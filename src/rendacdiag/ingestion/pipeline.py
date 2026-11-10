"""Ingestion : inventaire -> PDF vérifiés -> éléments avec métadonnées -> data/index/elements.jsonl.

Usage :
    python -m rendacdiag.ingestion.pipeline              # documents « vérifié » uniquement
    python -m rendacdiag.ingestion.pipeline --inclure-non-verifies   # développement
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

from ..config import Settings
from ..dtc import extract_codes
from .extract import extract_pdf

FAMILLE = {"A – essence TCe": "A", "B – diesel Blue dCi": "B", "A et B": "AB"}


def _split(v: str) -> list[str]:
    return [x.strip() for x in v.replace(";", "|").split("|") if x.strip()]


def load_inventory(settings: Settings) -> tuple[list[dict], list[dict]]:
    """Retourne (documents retenus, documents écartés avec la raison)."""
    kept, rejected = [], []
    with open(settings.corpus_dir / "inventaire.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            reason = None
            if not r.get("licence", "").strip():
                reason = "licence absente"
            elif r.get("statut_verification", "").strip().lower() not in ("vérifié", "verifie", "vérifie") and not settings.include_unverified:
                reason = f"statut « {r.get('statut_verification', '')} »"
            elif not (settings.corpus_dir / r["fichier"]).exists():
                reason = "fichier introuvable"
            (rejected if reason else kept).append({**r, "raison": reason} if reason else r)
    return kept, rejected


def build_elements(settings: Settings) -> dict:
    kept, rejected = load_inventory(settings)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    store = settings.store_dir
    store.mkdir(parents=True, exist_ok=True)
    out, n_by_kind = [], {}
    for r in kept:
        pdf = settings.corpus_dir / r["fichier"]
        header, raws = extract_pdf(str(pdf))
        doc_id = r["document_id"]
        # stockage du fichier d'origine (équivalent local de MinIO), nommé par empreinte
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]
        shutil.copy(pdf, store / f"{doc_id}.pdf")
        doc_codes = _split(r.get("codes_dtc", ""))
        base = dict(document_id=doc_id, version=r.get("version", ""), type_document=r["type"], titre=r["titre"],
                    famille=FAMILLE.get(r["famille"], "AB"), modeles=_split(r.get("modeles", "")),
                    voyants=_split(r.get("voyants", "")), groupes_acces=_split(r["groupes_acces"]),
                    licence=r["licence"], fichier=r["fichier"], sha256=digest, statut=r.get("statut_verification", ""))
        counters: dict[str, int] = {}
        context = f"{header['title']} — {header['subtitle']}".strip(" —")
        links = []
        for e in raws:
            if e.kind == "section" and e.title.startswith("Documents liés"):
                links = [x.strip() for x in e.text.replace("\n", ",").split(",") if x.strip().startswith("DOC-")]
        raws = [e for e in raws if not (e.kind == "section" and e.title.startswith("Documents liés"))]
        base["documents_lies"] = links
        for e in raws:
            counters[e.kind] = counters.get(e.kind, 0) + 1
            suffix = {"section": "s", "tableau": "tab", "figure": "fig"}[e.kind]
            eid = f"{doc_id}_{suffix}{counters[e.kind]}" if e.kind != "section" else f"{doc_id}_s{counters[e.kind]:02d}"
            body = e.text
            if e.kind == "figure" and e.extra.get("labels"):
                body = (body + "\nÉléments du schéma : " + ", ".join(e.extra["labels"])).strip()
            text = f"{context}\n{e.title}\n{body}" if e.kind == "section" else f"{context}\n{body}"
            codes = list(dict.fromkeys(doc_codes + extract_codes(text)))
            image = ""
            if e.kind == "figure":
                cand = [settings.corpus_dir / "images/schemas" / f"{doc_id}_fig1.png"]
                cand += [settings.corpus_dir / "images/pictogrammes" / f"{v}.png" for v in base["voyants"]]
                image = next((str(p.relative_to(settings.corpus_dir)) for p in cand if p.exists()), "")
            out.append({**base, "element_id": eid, "type_element": e.kind, "page": e.page, "section": e.title,
                        "codes_dtc": codes, "codes_document": doc_codes, "texte": text, "image": image})
            n_by_kind[e.kind] = n_by_kind.get(e.kind, 0) + 1
    with open(settings.elements_file, "w", encoding="utf-8") as f:
        for e in out:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    report = dict(documents_retenus=len(kept), documents_ecartes=len(rejected), elements=len(out), par_type=n_by_kind,
                  ecartes=[{"document_id": r["document_id"], "raison": r["raison"]} for r in rejected])
    (settings.index_dir / "rapport_ingestion.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingestion du corpus RenDacDiag")
    ap.add_argument("--inclure-non-verifies", action="store_true", help="indexer aussi les documents « à vérifier » (développement)")
    a = ap.parse_args()
    s = Settings()
    if a.inclure_non_verifies:
        s.include_unverified = True
    rep = build_elements(s)
    print(json.dumps({k: v for k, v in rep.items() if k != "ecartes"}, ensure_ascii=False))
    if rep["documents_ecartes"]:
        print(f"{rep['documents_ecartes']} document(s) écarté(s) : voir {s.index_dir / 'rapport_ingestion.json'}")


if __name__ == "__main__":
    main()
