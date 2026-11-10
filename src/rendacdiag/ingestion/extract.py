"""Extraction d'un PDF du corpus en éléments : sections, tableaux et figures, avec leur page."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import pymupdf

TITLE_SIZE = 16.0      # titre du document
HEADING_SIZE = 11.8    # titres de section (gras, 12 pt)
FOOTER_Y = 770         # pied de page (identifiant, version, numéro de page)
LABEL_SIZE = 9.2       # libellés dessinés dans un schéma


@dataclass
class RawElement:
    kind: str                  # "section" | "tableau" | "figure"
    page: int
    title: str
    text: str
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    extra: dict = field(default_factory=dict)


def _inside(b, boxes) -> bool:
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return any(bx0 - 1 <= cx <= bx1 + 1 and by0 - 1 <= cy <= by1 + 1 for bx0, by0, bx1, by1 in boxes)


def extract_pdf(path: str) -> tuple[dict, list[RawElement]]:
    """Retourne (en-tête, éléments). L'en-tête contient le titre et le sous-titre du document."""
    doc = pymupdf.open(path)
    header = {"title": "", "subtitle": "", "pages": doc.page_count}
    elements: list[RawElement] = []
    for pno, page in enumerate(doc, start=1):
        tables = page.find_tables().tables
        tboxes = [t.bbox for t in tables]
        for i, t in enumerate(tables, start=1):
            rows = []
            for row in t.rows:
                rows.append([" ".join(page.get_textbox(c).split()) if c else "" for c in row.cells])
            lines = [" : ".join(c for c in r if c) for r in rows if any(r)]
            elements.append(RawElement("tableau", pno, f"Tableau {i}", "\n".join(lines), t.bbox, {"rows": rows}))
        lines = []
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            for ln in b["lines"]:
                spans = [s for s in ln["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                text = re.sub(r"^(\d+\.)(\S)", r"\1 \2", text)
                if text in ("•",) or text[:2].rstrip(".").isdigit() and len(text) <= 3:
                    continue
                s0 = spans[0]
                lines.append(dict(text=text, size=s0["size"], bold="Bold" in s0["font"], italic="Italic" in s0["font"],
                                  bbox=ln["bbox"], y=ln["bbox"][1]))
        lines.sort(key=lambda l: (round(l["y"]), l["bbox"][0]))
        caption, labels, sections, cur = [], [], [], None
        for l in lines:
            if l["y"] > FOOTER_Y or _inside(l["bbox"], tboxes):
                continue
            if l["size"] >= TITLE_SIZE:
                header["title"] = l["text"]; continue
            if not header["subtitle"] and 10.5 <= l["size"] < 11.5 and not cur and not l["bold"]:
                header["subtitle"] = l["text"]; continue
            if l["italic"] and (l["text"].startswith("Figure") or caption and l["size"] >= 8.9 and not cur):
                caption.append(l["text"]); continue
            if l["bold"] and l["size"] >= HEADING_SIZE:
                cur = RawElement("section", pno, l["text"], "", l["bbox"]); sections.append(cur); continue
            if l["size"] <= LABEL_SIZE and not cur:
                labels.append(l["text"]); continue
            if cur is None:
                continue
            sep = " " if cur.text and not cur.text.endswith((".", ":")) and l["text"][:1].islower() else "\n"
            cur.text = (cur.text + sep + l["text"]).strip()
        if caption or labels:
            elements.append(RawElement("figure", pno, "Figure 1", " ".join(caption),
                                       extra={"labels": [x for x in labels if len(x) > 1]}))
        elements.extend(s for s in sections if s.text)
    return header, elements
