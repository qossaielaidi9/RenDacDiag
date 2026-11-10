"""Configuration lue dans les variables d'environnement (fichier .env possible)."""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Chargement simple d'un fichier .env à la racine du dépôt (les variables déjà définies sont prioritaires)
if (ROOT / ".env").exists():
    for _line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        _line = _line.split("#", 1)[0].strip()
        if "=" in _line:
            _k, _v = _line.split("=", 1)
            if _v.strip():
                os.environ.setdefault(_k.strip(), _v.strip())


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class Settings:
    corpus_dir: Path = field(default_factory=lambda: Path(_env("RDD_CORPUS_DIR", str(ROOT / "corpus"))))
    data_dir: Path = field(default_factory=lambda: Path(_env("RDD_DATA_DIR", str(ROOT / "data"))))
    # Qdrant : URL d'un serveur (docker-compose) ou vide pour le mode local sur disque
    qdrant_url: str = field(default_factory=lambda: _env("RDD_QDRANT_URL", ""))
    # Embedder texte : "bge-m3" (production) ou "hash" (tests, sans téléchargement)
    text_embedder: str = field(default_factory=lambda: _env("RDD_TEXT_EMBEDDER", "bge-m3"))
    # Embedder image : "clip" (production), "none" (désactivé)
    image_embedder: str = field(default_factory=lambda: _env("RDD_IMAGE_EMBEDDER", "clip"))
    # N'indexer que les documents « vérifié » de l'inventaire (règle du corpus)
    include_unverified: bool = field(default_factory=lambda: _env("RDD_INCLUDE_UNVERIFIED", "0") == "1")
    users_file: Path = field(default_factory=lambda: Path(_env("RDD_USERS_FILE", str(ROOT / "config" / "users.yaml"))))
    jwt_secret: str = field(default_factory=lambda: os.environ.get("RDD_JWT_SECRET") or secrets.token_hex(32))
    jwt_hours: int = field(default_factory=lambda: int(_env("RDD_JWT_HOURS", "8")))
    max_query_chars: int = 500
    max_k: int = 10
    rate_per_minute: int = field(default_factory=lambda: int(_env("RDD_RATE_PER_MINUTE", "30")))

    @property
    def elements_file(self) -> Path:
        return self.data_dir / "index" / "elements.jsonl"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def store_dir(self) -> Path:
        """Stockage des fichiers d'origine (équivalent local de MinIO)."""
        return self.data_dir / "store"

    @property
    def audit_file(self) -> Path:
        return self.data_dir / "logs" / "audit.jsonl"
