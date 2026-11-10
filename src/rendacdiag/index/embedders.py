"""Embedders texte et image.

- "bge-m3" : BAAI/bge-m3 (multilingue, 1024 dim), via sentence-transformers. Fonctionne sur CPU.
- "clip"   : texte multilingue -> espace CLIP (sentence-transformers/clip-ViT-B-32-multilingual-v1)
             et images -> CLIP ViT-B/32 (sentence-transformers/clip-ViT-B-32), 512 dim.
- "hash"   : embedder déterministe sans modèle, pour les tests et l'intégration continue.
             Il ne capture pas le sens : ses scores ne doivent jamais être rapportés comme résultats.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Protocol, Sequence


class TextEmbedder(Protocol):
    name: str
    dim: int
    def embed(self, texts: Sequence[str], query: bool = False) -> list[list[float]]: ...


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


class HashEmbedder:
    """Hachage de mots et de trigrammes de caractères, normalisé L2."""
    name = "hash"

    def __init__(self, dim: int = 512):
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        words = re.findall(r"[a-z0-9]+", _norm(text))
        feats = words + [w[i:i + 3] for w in words for i in range(max(1, len(w) - 2))]
        for f in feats:
            h = int(hashlib.md5(f.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0 if (h >> 8) & 1 else -1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed(self, texts, query=False):
        return [self._vec(t) for t in texts]


class BGEM3Embedder:
    name = "bge-m3"
    dim = 1024

    def __init__(self, device: str | None = None):
        from sentence_transformers import SentenceTransformer  # import tardif : dépendance lourde
        self.model = SentenceTransformer("BAAI/bge-m3", device=device)

    def embed(self, texts, query=False):
        return self.model.encode(list(texts), normalize_embeddings=True, batch_size=16).tolist()


class ClipEmbedder:
    """Requêtes texte (multilingue) et images dans le même espace CLIP."""
    name = "clip"
    dim = 512

    def __init__(self, device: str | None = None):
        from sentence_transformers import SentenceTransformer
        self.text_model = SentenceTransformer("sentence-transformers/clip-ViT-B-32-multilingual-v1", device=device)
        self.image_model = SentenceTransformer("sentence-transformers/clip-ViT-B-32", device=device)

    def embed(self, texts, query=False):
        return self.text_model.encode(list(texts), normalize_embeddings=True).tolist()

    def embed_images(self, paths: Sequence[str]) -> list[list[float]]:
        from PIL import Image
        imgs = [Image.open(p).convert("RGB") for p in paths]
        return self.image_model.encode(imgs, normalize_embeddings=True).tolist()


def text_embedder(name: str) -> TextEmbedder:
    return {"hash": HashEmbedder, "bge-m3": BGEM3Embedder}[name]()


def image_embedder(name: str):
    return None if name == "none" else ClipEmbedder()
