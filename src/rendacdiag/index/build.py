"""Construction des index vectoriels Qdrant (texte et image) à partir de data/index/elements.jsonl.

Usage :
    python -m rendacdiag.index.build                  # BGE-M3 + CLIP (téléchargement des modèles au premier lancement)
    RDD_TEXT_EMBEDDER=hash RDD_IMAGE_EMBEDDER=none python -m rendacdiag.index.build   # tests
L'index BM25 est reconstruit en mémoire au démarrage de la recherche (corpus de quelques centaines d'éléments).
"""
from __future__ import annotations

import json
import uuid

from qdrant_client import QdrantClient, models

from ..config import Settings
from .embedders import image_embedder, text_embedder

TEXT_COLLECTION = "rdd_texte"
IMAGE_COLLECTION = "rdd_images"
PAYLOAD_KEYS = ("element_id", "document_id", "page", "type_element", "famille", "groupes_acces", "codes_dtc", "voyants", "image")


def client(settings: Settings) -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    (settings.index_dir / "qdrant").mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(settings.index_dir / "qdrant"))


def load_elements(settings: Settings) -> list[dict]:
    with open(settings.elements_file, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def point_id(element_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, element_id))


def _recreate(cli: QdrantClient, name: str, dim: int) -> None:
    if cli.collection_exists(name):
        cli.delete_collection(name)
    cli.create_collection(name, vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE))
    for key in ("groupes_acces", "famille", "codes_dtc", "document_id"):
        cli.create_payload_index(name, key, models.PayloadSchemaType.KEYWORD)


def build(settings: Settings, cli: QdrantClient | None = None) -> dict:
    els = load_elements(settings)
    cli = cli or client(settings)
    te = text_embedder(settings.text_embedder)
    _recreate(cli, TEXT_COLLECTION, te.dim)
    vecs = te.embed([e["texte"] for e in els])
    cli.upsert(TEXT_COLLECTION, [models.PointStruct(id=point_id(e["element_id"]), vector=v,
                                                    payload={k: e[k] for k in PAYLOAD_KEYS} | {"embedder": te.name})
                                 for e, v in zip(els, vecs)])
    info = {"elements_texte": len(els), "embedder_texte": te.name, "elements_image": 0}
    ie = image_embedder(settings.image_embedder)
    figs = [e for e in els if e.get("image")]
    if ie and figs:
        _recreate(cli, IMAGE_COLLECTION, ie.dim)
        ivecs = ie.embed_images([str(settings.corpus_dir / e["image"]) for e in figs])
        cli.upsert(IMAGE_COLLECTION, [models.PointStruct(id=point_id(e["element_id"]), vector=v,
                                                         payload={k: e[k] for k in PAYLOAD_KEYS})
                                      for e, v in zip(figs, ivecs)])
        info.update(elements_image=len(figs), embedder_image=ie.name)
    (settings.index_dir / "index_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


if __name__ == "__main__":
    print(json.dumps(build(Settings()), ensure_ascii=False))
