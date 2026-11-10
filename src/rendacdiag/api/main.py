"""API RenDacDiag (livrable 2) : authentification, recherche filtrée, ouverture contrôlée des sources.

Lancement :
    uvicorn rendacdiag.api.main:app --reload --app-dir src
Contrôle d'accès appliqué à trois endroits ici : jeton (API), filtre de recherche, ouverture d'une page ou d'une image.
Le quatrième point (serveur MCP) arrive au livrable 4.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt
import pymupdf
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..access import User, UserStore
from ..config import Settings
from ..search.retriever import Retriever


class Login(BaseModel):
    login: str
    password: str


def create_app(settings: Settings | None = None, retriever: Retriever | None = None) -> FastAPI:
    s = settings or Settings()
    users = UserStore(s.users_file)
    state: dict = {"retriever": retriever}
    calls: dict[str, deque] = defaultdict(deque)
    bearer = HTTPBearer(auto_error=False)
    app = FastAPI(title="RenDacDiag", version="0.2.0")

    def r() -> Retriever:
        if state["retriever"] is None:
            state["retriever"] = Retriever(s)
        return state["retriever"]

    def audit(user: str, endpoint: str, decision: str, **extra) -> None:
        s.audit_file.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "user": user, "endpoint": endpoint,
               "decision": decision, **extra}
        with open(s.audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
        if not cred:
            raise HTTPException(401, "Jeton manquant")
        try:
            data = jwt.decode(cred.credentials, s.jwt_secret, algorithms=["HS256"])
        except jwt.PyJWTError:
            raise HTTPException(401, "Jeton invalide ou expiré")
        u = users.get(data.get("sub", ""))
        if not u:
            raise HTTPException(401, "Utilisateur inconnu")
        q = calls[u.login]; now = time.time()
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= s.rate_per_minute:
            audit(u.login, "quota", "refus")
            raise HTTPException(429, "Trop de requêtes, réessayez dans une minute")
        q.append(now)
        return u

    @app.get("/health")
    def health():
        return {"statut": "ok", "elements": len(r().elements), "dense": bool(r().te), "image": bool(r().ie)}

    @app.post("/auth/token")
    def token(body: Login):
        u = users.authenticate(body.login, body.password)
        if not u:
            audit(body.login, "/auth/token", "refus")
            raise HTTPException(401, "Identifiants incorrects")
        exp = datetime.now(timezone.utc) + timedelta(hours=s.jwt_hours)
        audit(u.login, "/auth/token", "ok")
        return {"access_token": jwt.encode({"sub": u.login, "role": u.role, "exp": exp}, s.jwt_secret, algorithm="HS256"),
                "token_type": "bearer", "role": u.role, "atelier": u.atelier}

    @app.get("/search")
    def search(q: str = Query(..., min_length=2), famille: str | None = Query(None, pattern="^(A|B)$"),
               k: int = Query(5, ge=1), user: User = Depends(current_user)):
        if len(q) > s.max_query_chars:
            raise HTTPException(413, f"Question trop longue (maximum {s.max_query_chars} caractères)")
        res = r().search(q, user, famille=famille, k=min(k, s.max_k))
        audit(user.login, "/search", "ok", role=user.role, question_sha256=hashlib.sha256(q.encode()).hexdigest()[:16],
              longueur=len(q), documents=res["documents"][:k])
        return res

    def _doc_elements(doc_id: str) -> list[dict]:
        els = [e for e in r().elements if e["document_id"] == doc_id]
        if not els:
            raise HTTPException(404, "Document inconnu")
        return els

    @app.get("/documents/{doc_id}/pages/{page}")
    def page_image(doc_id: str, page: int, user: User = Depends(current_user)):
        els = _doc_elements(doc_id)
        if not user.can_read(els[0]):
            audit(user.login, "/documents", "refus", document=doc_id)
            raise HTTPException(403, "Accès refusé à ce document")
        pdf = pymupdf.open(str(s.store_dir / f"{doc_id}.pdf"))
        if not 1 <= page <= pdf.page_count:
            raise HTTPException(404, "Page inexistante")
        audit(user.login, "/documents", "ok", document=doc_id, page=page)
        return Response(pdf[page - 1].get_pixmap(dpi=110).tobytes("png"), media_type="image/png")

    @app.get("/elements/{element_id}/image")
    def element_image(element_id: str, user: User = Depends(current_user)):
        e = r().by_id.get(element_id)
        if not e or not e.get("image"):
            raise HTTPException(404, "Image inconnue")
        if not user.can_read(e):
            audit(user.login, "/elements/image", "refus", element=element_id)
            raise HTTPException(403, "Accès refusé à cette image")
        audit(user.login, "/elements/image", "ok", element=element_id)
        return FileResponse(s.corpus_dir / e["image"], media_type="image/png")

    return app


app = create_app()
