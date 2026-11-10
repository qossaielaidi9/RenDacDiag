"""Évaluation de la recherche (livrable 2) : Recall@5, MRR@10, nDCG@5 par document, et tests d'accès.

Usage :
    python eval/run_eval.py                      # configurations disponibles selon les index construits
    python eval/run_eval.py --configs bm25 code+bm25
Les résultats sont écrits dans eval/resultats_l2.json et eval/resultats_l2.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rendacdiag.access import User  # noqa: E402
from rendacdiag.search.retriever import Retriever  # noqa: E402

HERE = Path(__file__).parent
USERS = {"technicien": User("eval_tech", "technicien", "ATELIER-A"), "receptionnaire": User("eval_rec", "receptionnaire", "ATELIER-B"),
         "invite": User("eval_inv", "invite", ""), "chef_atelier": User("eval_chef", "chef_atelier", "ATELIER-A")}
CONFIGS = {"bm25": ("bm25",), "code+bm25": ("code", "bm25"), "dense": ("dense",), "code+bm25+dense": ("code", "bm25", "dense"),
           "hybride complet": ("code", "bm25", "dense", "image")}


def metrics(ranked: list[str], relevant: list[str]) -> dict:
    rel = set(relevant)
    r5 = len(rel & set(ranked[:5])) / len(rel)
    mrr = next((1 / i for i, d in enumerate(ranked[:10], 1) if d in rel), 0.0)
    gains = [1 if d in rel else 0 for d in ranked[:5]]
    dcg = sum(g / math.log2(i + 1) for i, g in enumerate(gains, 1))
    idcg = sum(1 / math.log2(i + 1) for i in range(1, min(len(rel), 5) + 1))
    return {"recall@5": r5, "mrr@10": mrr, "ndcg@5": dcg / idcg, "top1": float(bool(ranked) and ranked[0] == relevant[0])}


def access_checks(r: Retriever) -> list[dict]:
    """Aucun document hors des droits du rôle ne doit apparaître."""
    out = []
    probes = ["causes du code P0301 et procédure de contrôle", "procédure vanne EGR", "schéma du préchauffage diesel",
              "P0171 prise d'air", "voyant FAP allumé"]
    for role in ("receptionnaire", "invite"):
        u = USERS[role]
        for q in probes:
            res = r.search(q, u, k=10)
            leaked = [x["element_id"] for x in res["resultats"] if not u.can_read(r.by_id[x["element_id"]])]
            out.append({"role": role, "question": q, "fuites": leaked, "ok": not leaked})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="*")
    a = ap.parse_args()
    r = Retriever()
    available = [c for c, modes in CONFIGS.items()
                 if ("dense" not in modes or r.te and r.te.name != "hash") and ("image" not in modes or r.ie)]
    configs = a.configs or available
    qs = list(csv.DictReader(open(HERE / "questions_l2.csv", encoding="utf-8")))
    results = {}
    for c in configs:
        per_q, agg = [], {}
        for q in qs:
            rel = q["documents_attendus"].split(";")
            res = r.search(q["question"], USERS[q["role"]], k=10, modes=CONFIGS[c])
            m = metrics(res["documents"], rel)
            per_q.append({"id": q["id"], "categorie": q["categorie"], "top5": res["documents"][:5], "attendus": rel, **m})
            for k, v in m.items():
                agg[k] = agg.get(k, 0) + v
        results[c] = {"global": {k: round(v / len(qs), 3) for k, v in agg.items()}, "questions": per_q}
        cats = sorted({q["categorie"] for q in qs})
        results[c]["par_categorie"] = {cat: round(sum(p["recall@5"] for p in per_q if p["categorie"] == cat) /
                                                  sum(1 for p in per_q if p["categorie"] == cat), 3) for cat in cats}
    acc = access_checks(r)
    out = {"configurations": results, "acces": {"tests": len(acc), "reussis": sum(x["ok"] for x in acc), "details": acc}}
    (HERE / "resultats_l2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["| Configuration | Recall@5 | MRR@10 | nDCG@5 | Top-1 |", "|---|---|---|---|---|"]
    for c, v in results.items():
        g = v["global"]; lines.append(f"| {c} | {g['recall@5']} | {g['mrr@10']} | {g['ndcg@5']} | {g['top1']} |")
    lines.append(f"\nTests d'accès : {out['acces']['reussis']} / {out['acces']['tests']} sans fuite.")
    (HERE / "resultats_l2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
