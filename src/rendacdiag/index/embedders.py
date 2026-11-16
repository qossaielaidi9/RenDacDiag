"""Embedders texte et image.

- "bge-m3"     : BAAI/bge-m3 (multilingue, 1024 dim), via sentence-transformers. Fonctionne sur CPU.
- "clip"       : texte multilingue -> espace CLIP (sentence-transformers/clip-ViT-B-32-multilingual-v1)
                 et images -> CLIP ViT-B/32 (sentence-transformers/clip-ViT-B-32), 512 dim.
- "cnn-resnet" : extracteur CNN classique (ResNet-50, 2048 dim / ResNet-18, 512 dim via torchvision) pour images.
- "hash"       : embedder déterministe sans modèle, pour les tests et l'intégration continue.
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


class CnnResNetEmbedder:
    """Embedder d'images basé sur un CNN pré-entraîné (ResNet-50 / ResNet-18 via torchvision)."""
    name: str
    dim: int

    def __init__(self, model_name: str = "resnet50", device: str | None = None):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._preprocess = None
        if model_name == "resnet18":
            self.dim = 512
            self.name = "cnn-resnet18"
        else:
            self.dim = 2048
            self.name = "cnn-resnet50"

    def _load(self):
        if self._model is not None:
            return
        import torch
        from torchvision import models, transforms

        device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.model_name == "resnet18":
            weights = models.ResNet18_Weights.DEFAULT
            model = models.resnet18(weights=weights)
        else:
            weights = models.ResNet50_Weights.DEFAULT
            model = models.resnet50(weights=weights)

        # Remplacement de la couche de classification (fc) par l'identité pour extraire le vecteur caractéristique
        model.fc = torch.nn.Identity()
        model.to(device).eval()
        self._model = model
        self.device = device
        self._preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def embed_images(self, paths: Sequence[str]) -> list[list[float]]:
        self._load()
        import torch
        from PIL import Image

        tensors = []
        for p in paths:
            img = Image.open(p).convert("RGB")
            tensors.append(self._preprocess(img))
        batch = torch.stack(tensors).to(self.device)

        with torch.no_grad():
            features = self._model(batch)
            features = torch.nn.functional.normalize(features, p=2, dim=1)
        return features.cpu().tolist()


def text_embedder(name: str) -> TextEmbedder:
    return {"hash": HashEmbedder, "bge-m3": BGEM3Embedder}[name]()


def image_embedder(name: str):
    if name == "none":
        return None
    if name in ("cnn-resnet", "cnn-resnet50", "cnn"):
        return CnnResNetEmbedder(model_name="resnet50")
    if name == "cnn-resnet18":
        return CnnResNetEmbedder(model_name="resnet18")
    return ClipEmbedder()
