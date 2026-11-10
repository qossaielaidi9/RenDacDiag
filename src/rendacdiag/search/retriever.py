"""Recherche hybride : code exact + BM25 + dense (BGE-M3) + image (CLIP), fusion RRF, filtrée par droits et moteur.

Le filtre d'accès est appliqué AVANT le classement dans chaque liste : un élément interdit ne peut pas
apparaître, même en dernière position, ni influencer la fusion.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from qdrant_client import models

from ..access import User
from ..config import Settings
from ..dtc import decode_uds, extract_codes, is_generic
from ..index.build import IMAGE_COLLECTION, TEXT_COLLECTION, client, load_elements
from ..index.embedders import image_embedder, text_embedder
from ..index.lexical import LexicalIndex

RRF_K = 60
WEIGHTS = {"code": 2.0, "bm25": 1.0, "dense": 1.0, "image": 0.7}


VISUAL_RE = re.compile(r"\b(schemas?|voyants?|temoins?|pictogrammes?|symboles?|logos?|images?|photos?|figures?|"
                       r"dessins?|cablages?|brochages?|allumee?s?|clignotante?s?|orange|rouge|jaune|tableau de bord)\b")


def is_visual(query: str) -> bool:
    """La liste image (CLIP) n'est utile que pour une question visuelle ou accompagnée d'une photo."""
    q = "".join(c for c in unicodedata.normalize("NFKD", query.lower()) if not unicodedata.combining(c))
    return bool(VISUAL_RE.search(q))


def detect_famille(query: str) -> str | None:
    q = unicodedata.normalize("NFKD", query.lower())
    if re.search(r"\b(diesel|dci|blue ?dci|gazole|fap|adblue|prechauffage|k9k)\b", q):
        return "B"
    if re.search(r"\b(essence|tce|sce|bougie d.allumage|bobine)\b", q):
        return "A"
    return None


@dataclass
class Hit:
    element: dict
    score: float = 0.0
    ranks: dict = field(default_factory=dict)


class Retriever:
    def __init__(self, settings: Settings | None = None, use_dense: bool = True, use_image: bool = True, qdrant=None):
        self.s = settings or Settings()
        self.elements = load_elements(self.s)
        self.by_id = {e["element_id"]: e for e in self.elements}
        self.lex = LexicalIndex([e["element_id"] for e in self.elements], [e["texte"] for e in self.elements])
        self.qdrant = qdrant
        self.te = self.ie = None
        if use_dense or use_image:
            self.qdrant = self.qdrant or client(self.s)
        if use_dense and self.qdrant.collection_exists(TEXT_COLLECTION):
            self.te = text_embedder(self.s.text_embedder)
        if use_image and self.s.image_embedder != "none" and self.qdrant.collection_exists(IMAGE_COLLECTION):
            self.ie = image_embedder(self.s.image_embedder)

    # ------------------------------------------------------------------ filtres
    def _allowed(self, user: User, famille: str | None) -> set[str]:
        fams = {famille, "AB"} if famille else {"A", "B", "AB"}
        return {e["element_id"] for e in self.elements if user.can_read(e) and e["famille"] in fams}

    def _qfilter(self, user: User, famille: str | None) -> models.Filter:
        must = [models.FieldCondition(key="groupes_acces", match=models.MatchAny(any=user.groups))]
        if famille:
            must.append(models.FieldCondition(key="famille", match=models.MatchAny(any=[famille, "AB"])))
        return models.Filter(must=must)

    # ------------------------------------------------------------------ listes candidates
    def _code_hits(self, codes: list[str], allowed: set[str]) -> list[str]:
        primary, secondary = [], []
        for c in codes:
            for e in self.elements:
                if e["element_id"] not in allowed:
                    continue
                if c in e["codes_document"] and e["type_document"] == "fiche_dtc":
                    primary.append(e["element_id"])
                elif c in e["codes_document"]:
                    secondary.append(e["element_id"])
        return list(dict.fromkeys(primary + secondary))

    def _dense(self, query: str, user: User, famille: str | None, k: int) -> list[str]:
        if not self.te:
            return []
        v = self.te.embed([query], query=True)[0]
        res = self.qdrant.query_points(TEXT_COLLECTION, query=v, query_filter=self._qfilter(user, famille), limit=k)
        return [p.payload["element_id"] for p in res.points]

    def _image(self, query: str, user: User, famille: str | None, k: int, image_path: str | None) -> list[str]:
        if not self.ie:
            return []
        v = self.ie.embed_images([image_path])[0] if image_path else self.ie.embed([query])[0]
        res = self.qdrant.query_points(IMAGE_COLLECTION, query=v, query_filter=self._qfilter(user, famille), limit=k)
        return [p.payload["element_id"] for p in res.points]

    # ------------------------------------------------------------------ recherche
    def search(self, query: str, user: User, famille: str | None = None, k: int = 5, image_path: str | None = None,
               modes: tuple[str, ...] = ("code", "bm25", "dense", "image")) -> dict:
        famille = famille or detect_famille(query)
        codes = extract_codes(query)
        uds = [dict(zip(("code", "ftb", "type"), d)) | {"brut": m}
               for m in re.findall(r"\bDTC\s?[0-9A-Fa-f]{6}\b", query) if (d := decode_uds(m))]
        allowed = self._allowed(user, famille)
        lists: dict[str, list[str]] = {}
        if "code" in modes and codes:
            lists["code"] = self._code_hits(codes, allowed)
        if "bm25" in modes:
            lists["bm25"] = [i for i, _ in self.lex.search(query, allowed, k=50)]
        if "dense" in modes:
            lists["dense"] = [i for i in self._dense(query, user, famille, 50) if i in allowed]
        if "image" in modes and (image_path or is_visual(query)):
            lists["image"] = [i for i in self._image(query, user, famille, 20, image_path) if i in allowed]
        hits: dict[str, Hit] = {}
        for name, ids in lists.items():
            for rank, eid in enumerate(ids, start=1):
                h = hits.setdefault(eid, Hit(self.by_id[eid]))
                h.score += WEIGHTS[name] / (RRF_K + rank)
                h.ranks[name] = rank
        ranked = sorted(hits.values(), key=lambda h: -h.score)[: max(1, min(k, self.s.max_k)) * 4]
        results = [dict(element_id=h.element["element_id"], document_id=h.element["document_id"], page=h.element["page"],
                        type_element=h.element["type_element"], titre=h.element["titre"], score=round(h.score, 5),
                        sources=h.ranks, extrait=h.element["texte"][:300], image=h.element.get("image", ""))
                   for h in ranked]
        return dict(famille=famille, codes=codes, codes_constructeur=[c for c in codes if not is_generic(c)], uds=uds,
                    listes={n: len(v) for n, v in lists.items()}, resultats=results[: min(k, self.s.max_k)],
                    documents=list(dict.fromkeys(r["document_id"] for r in results)))
