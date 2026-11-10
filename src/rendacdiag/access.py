"""Modèle d'accès : utilisateurs, rôles, ateliers et groupes d'accès des documents.

Un élément du corpus est lisible si l'un des groupes de l'utilisateur figure dans ses groupes_acces.
L'atelier sert aux données d'atelier (historique, OR) exposées par le serveur MCP au livrable 4.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

ROLE_GROUPS = {
    "technicien": ["techniciens"],
    "chef_atelier": ["chefs_atelier", "techniciens"],
    "receptionnaire": ["receptionnaires"],
    "invite": ["invites"],
}


@dataclass(frozen=True)
class User:
    login: str
    role: str
    atelier: str

    @property
    def groups(self) -> list[str]:
        return ROLE_GROUPS.get(self.role, [])

    def can_read(self, element: dict) -> bool:
        return bool(set(self.groups) & set(element.get("groupes_acces", [])))


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        _, salt, dk = stored.split("$")
    except ValueError:
        return False
    test = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return hmac.compare_digest(test.hex(), dk)


class UserStore:
    def __init__(self, path: Path):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        self._users = {u["login"]: u for u in data.get("users", [])}

    def authenticate(self, login: str, password: str) -> User | None:
        u = self._users.get(login)
        if not u or not check_password(password, u.get("password_hash", "")):
            return None
        return User(u["login"], u["role"], u.get("atelier", ""))

    def get(self, login: str) -> User | None:
        u = self._users.get(login)
        return User(u["login"], u["role"], u.get("atelier", "")) if u else None
