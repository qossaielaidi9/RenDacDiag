"""Index lexical BM25 avec une normalisation adaptée au français et aux codes défaut."""
from __future__ import annotations

import re
import unicodedata

from rank_bm25 import BM25Okapi

STOP = set("""a au aux avec ce ces cette d de des du elle en est et il je l la le les leur lui ma mais me mes mon ne
ni nous on ou par pas pour qu que qui sa se ses son sur ta te tes ton tu un une vos votre vous y c j m n s t
quoi comment quel quelle quels quelles est-ce faire fait dois peut peux sont etre avoir ai a-t-il ca ça""".split())


def tokenize(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    toks = re.findall(r"[a-z]\d{4}|[a-z0-9]+", t)
    out = []
    for w in toks:
        if w in STOP or len(w) == 1 and not w.isdigit():
            continue
        if not re.fullmatch(r"[a-z]\d{4}", w):
            if len(w) > 4 and w.endswith(("s", "x")):
                w = w[:-1]
            w = w[:7]   # racinisation légère : clignote / clignotant -> clignot
        out.append(w)
    return out


class LexicalIndex:
    def __init__(self, ids: list[str], texts: list[str]):
        self.ids = ids
        self.bm25 = BM25Okapi([tokenize(t) for t in texts])

    def search(self, query: str, allowed: set[str] | None = None, k: int = 50) -> list[tuple[str, float]]:
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(((s, i) for i, s in zip(self.ids, scores) if s > 0 and (allowed is None or i in allowed)),
                        reverse=True)
        return [(i, float(s)) for s, i in ranked[:k]]
