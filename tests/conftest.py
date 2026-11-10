import sys
from pathlib import Path

import pytest
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rendacdiag.config import Settings  # noqa: E402
from rendacdiag.index.build import build  # noqa: E402
from rendacdiag.ingestion.pipeline import build_elements  # noqa: E402
from rendacdiag.search.retriever import Retriever  # noqa: E402


@pytest.fixture(scope="session")
def settings(tmp_path_factory):
    s = Settings()
    s.data_dir = tmp_path_factory.mktemp("data")
    s.include_unverified = True          # le corpus de test n'est pas encore vérifié
    s.text_embedder, s.image_embedder = "hash", "none"
    s.rate_per_minute = 1000
    build_elements(s)
    return s


@pytest.fixture(scope="session")
def qdrant(settings):
    cli = QdrantClient(":memory:")
    build(settings, cli)
    return cli


@pytest.fixture(scope="session")
def retriever(settings, qdrant):
    return Retriever(settings, use_dense=True, use_image=False, qdrant=qdrant)
