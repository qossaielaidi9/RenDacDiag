import json

import pytest
from fastapi.testclient import TestClient

from rendacdiag.api.main import create_app


@pytest.fixture(scope="module")
def client(settings, retriever):
    return TestClient(create_app(settings, retriever))


def login(client, who):
    r = client.post("/auth/token", json={"login": who, "password": f"demo-{who}"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_bad_password_is_refused(client):
    assert client.post("/auth/token", json={"login": "technicien_01", "password": "x"}).status_code == 401


def test_search_requires_a_token(client):
    assert client.get("/search", params={"q": "P0301"}).status_code == 401


def test_technician_can_search_and_open_a_procedure(client):
    h = login(client, "technicien_01")
    res = client.get("/search", params={"q": "P0301 raté cylindre 1"}, headers=h).json()
    assert res["documents"][0] == "DOC-DTC-P0301"
    page = client.get("/documents/DOC-PROC-01/pages/1", headers=h)
    assert page.status_code == 200 and page.headers["content-type"] == "image/png"


def test_receptionist_cannot_open_a_procedure(client):
    h = login(client, "receptionnaire_b")
    assert client.get("/documents/DOC-PROC-01/pages/1", headers=h).status_code == 403
    assert client.get("/elements/DOC-SCH-01_fig1/image", headers=h).status_code == 403
    assert client.get("/elements/DOC-VOY-V05_fig1/image", headers=h).status_code == 200


def test_query_length_budget(client):
    h = login(client, "technicien_01")
    assert client.get("/search", params={"q": "x" * 600}, headers=h).status_code == 413


def test_audit_log_has_no_raw_question(client, settings):
    h = login(client, "technicien_01")
    client.get("/search", params={"q": "question confidentielle P0171"}, headers=h)
    log = settings.audit_file.read_text(encoding="utf-8")
    assert "confidentielle" not in log
    assert any(json.loads(l).get("endpoint") == "/search" for l in log.splitlines())
