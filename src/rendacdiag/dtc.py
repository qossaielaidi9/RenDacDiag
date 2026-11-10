"""Codes défaut : extraction, normalisation et décodage des codes UDS à 6 chiffres.

Exemples :
    extract_codes("La valise affiche p0301 et P0300")  -> ["P0301", "P0300"]
    decode_uds("DTC038096") -> ("P0380", "96", "défaillance d'un composant interne")
"""
from __future__ import annotations

import re

# Types de défaillance (Failure Type Byte, SAE J2012-DA) les plus fréquents en atelier
FTB = {
    "00": "pas d'information complémentaire", "01": "défaut électrique général", "11": "court-circuit à la masse",
    "12": "court-circuit au positif", "13": "circuit ouvert", "14": "court-circuit à la masse ou circuit ouvert",
    "15": "court-circuit au positif ou circuit ouvert", "16": "tension sous le seuil", "17": "tension au-dessus du seuil",
    "1C": "tension hors plage", "29": "signal invalide", "31": "aucun signal", "62": "comparaison de signaux en défaut",
    "64": "plausibilité du signal en défaut", "71": "actionneur bloqué", "72": "actionneur bloqué ouvert",
    "73": "actionneur bloqué fermé", "87": "message manquant", "92": "performance ou fonctionnement incorrect",
    "94": "fonctionnement inattendu", "96": "défaillance d'un composant interne", "98": "température excessive",
}

_OBD = re.compile(r"\b([PCBU])\s?([0-3])([0-9A-F]{3})\b", re.IGNORECASE)
_UDS = re.compile(r"\bDTC\s?([0-9A-F]{6})\b", re.IGNORECASE)


def decode_uds(code: str) -> tuple[str, str, str] | None:
    """Convertit un code UDS (3 octets) en code OBD + type de défaillance."""
    m = _UDS.search(code) or re.fullmatch(r"([0-9A-Fa-f]{6})", code.strip())
    if not m:
        return None
    hexa = m.group(1).upper()
    first = int(hexa[0], 16)
    obd = f"{'PCBU'[first >> 2]}{first & 0b11}{hexa[1:4]}"
    ftb = hexa[4:6]
    return obd, ftb, FTB.get(ftb, "type de défaillance non répertorié")


def extract_codes(text: str) -> list[str]:
    """Codes OBD présents dans un texte, y compris ceux décodés depuis un format UDS, sans doublon, dans l'ordre."""
    found: list[str] = []
    for m in _UDS.finditer(text):
        dec = decode_uds(m.group(0))
        if dec and dec[0] not in found:
            found.append(dec[0])
    for m in _OBD.finditer(text):
        c = (m.group(1) + m.group(2) + m.group(3)).upper()
        if c not in found:
            found.append(c)
    return found


def is_generic(code: str) -> bool:
    """Vrai pour les codes génériques SAE (P0, P2, P3, U0…) ; faux pour les codes constructeur (P1xxx…)."""
    return code[1] in "023" if code[0] == "P" else code[1] in "03"
