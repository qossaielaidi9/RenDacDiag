"""Recherche en ligne de commande.

    python -m rendacdiag.search.cli "DTC038096 sur un Duster dCi" --role technicien
"""
from __future__ import annotations

import argparse

from ..access import User
from .retriever import Retriever


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--role", default="technicien", choices=["technicien", "chef_atelier", "receptionnaire", "invite"])
    ap.add_argument("--famille", choices=["A", "B"])
    ap.add_argument("--image", help="chemin d'une photo (recherche image, nécessite CLIP)")
    ap.add_argument("-k", type=int, default=5)
    a = ap.parse_args()
    res = Retriever().search(a.question, User("cli", a.role, ""), famille=a.famille, k=a.k, image_path=a.image)
    print(f"Famille : {res['famille'] or 'non détectée'} · codes : {', '.join(res['codes']) or 'aucun'}")
    for u in res["uds"]:
        print(f"  {u['brut']} -> {u['code']} ({u['type']})")
    if res["codes_constructeur"]:
        print(f"  Codes constructeur hors corpus : {', '.join(res['codes_constructeur'])}")
    for i, r in enumerate(res["resultats"], 1):
        print(f"{i}. {r['element_id']} (p. {r['page']}) · {r['score']} · {r['sources']}")
        print("   " + r["extrait"].splitlines()[-1][:140])


if __name__ == "__main__":
    main()
