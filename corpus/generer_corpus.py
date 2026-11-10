"""Corpus RenDacDiag v2 : fiches allégées, règles générales, procédures, schémas, index enrichi."""
import csv, shutil, math, subprocess
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                Image, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, PolyLine
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

F = "/usr/share/fonts/truetype/crosextra/"
pdfmetrics.registerFont(TTFont("Carlito", F + "Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Carlito-Bold", F + "Carlito-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Carlito-Italic", F + "Carlito-Italic.ttf"))
registerFontFamily("Carlito", normal="Carlito", bold="Carlito-Bold", italic="Carlito-Italic", boldItalic="Carlito-Bold")

NAVY = colors.HexColor("#1F3864"); LIGHT = colors.HexColor("#E8EEF7"); GREY = colors.HexColor("#5A5A5A")
EDGE = colors.HexColor("#4A5A78"); GRID = colors.HexColor("#B4C2D9")
SEV = {"critique": colors.HexColor("#F4CCCC"), "élevée": colors.HexColor("#FCE5CD"),
       "moyenne": colors.HexColor("#FFF2CC"), "faible": colors.HexColor("#D9EAD3")}
FAM = {"essence": "Essence (TCe)", "diesel": "Diesel (1.5 Blue dCi)", "les_deux": "Essence et diesel",
       "hors_perimetre": "Hors périmètre"}
st = {
 "t": ParagraphStyle("t", fontName="Carlito-Bold", fontSize=18, leading=22, textColor=NAVY),
 "s": ParagraphStyle("s", fontName="Carlito", fontSize=11, leading=14, textColor=GREY),
 "h": ParagraphStyle("h", fontName="Carlito-Bold", fontSize=12, leading=15, textColor=NAVY, spaceBefore=9, spaceAfter=3),
 "b": ParagraphStyle("b", fontName="Carlito", fontSize=10.5, leading=14, spaceAfter=3),
 "li": ParagraphStyle("li", fontName="Carlito", fontSize=10.5, leading=14, leftIndent=16, bulletIndent=2, spaceAfter=2),
 "c": ParagraphStyle("c", fontName="Carlito", fontSize=9.5, leading=12),
 "ch": ParagraphStyle("ch", fontName="Carlito-Bold", fontSize=9.5, leading=12, textColor=colors.white),
 "n": ParagraphStyle("n", fontName="Carlito-Italic", fontSize=9, leading=11.5, textColor=GREY),
}
def P(t, s="b"): return Paragraph(t, st[s])
def bul(items): return [Paragraph(i, st["li"], bulletText="•") for i in items]
def num(items): return [Paragraph(i, st["li"], bulletText=f"{k}.") for k, i in enumerate(items, 1)]
def kv(rows, extra=None):
    t = Table([[Paragraph(k, st["ch"]), Paragraph(v, st["c"])] for k, v in rows], colWidths=[42 * mm, 128 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)] + (extra or [])))
    return t
def grid(rows, widths):
    data = [[Paragraph(c, st["ch"]) for c in rows[0]]] + [[Paragraph(c, st["c"]) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)] +
                          [("BACKGROUND", (0, i), (-1, i), LIGHT) for i in range(2, len(data), 2)]))
    return t

def build(path, doc_id, story, version="2.0"):
    def deco(c, d):
        c.saveState(); w, h = A4
        c.setStrokeColor(NAVY); c.setLineWidth(0.8); c.setDash(4, 3)
        c.rect(12 * mm, 12 * mm, w - 24 * mm, h - 24 * mm); c.setDash()
        c.setFont("Carlito", 8.5); c.setFillColor(GREY)
        c.drawString(20 * mm, 16 * mm, f"RenDacDiag · {doc_id} · v{version} · Document synthétique à usage pédagogique, à valider")
        c.drawRightString(w - 20 * mm, 16 * mm, f"Page {d.page}")
        c.restoreState()
    d = BaseDocTemplate(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm,
                        bottomMargin=22 * mm, title=doc_id, author="Équipe RenDacDiag", subject="Corpus RenDacDiag")
    d.addPageTemplates([PageTemplate(frames=[Frame(d.leftMargin, d.bottomMargin, d.width, d.height)], onPage=deco)])
    d.build(story)
    return int(subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])

DS = Path("/home/claude/RenDacDiag_datasets")
OUT = Path("/home/claude/RenDacDiag_corpus_v2")
if OUT.exists(): shutil.rmtree(OUT)
for d in ["fiches_dtc", "fiches_voyants", "procedures", "schemas", "general", "images/pictogrammes", "images/schemas", "licences"]:
    (OUT / d).mkdir(parents=True)

INDEX, ELEMENTS = [], []
ALL_MODELS = "Clio V;Captur II;Sandero III;Duster II"
def reg(doc_id, titre, typ, pages, fam, codes, voy, lies, groupes, origine, licence, fichier, models=ALL_MODELS):
    INDEX.append(dict(document_id=doc_id, titre=titre, type=typ, version="2.0", pages=pages,
                      marques="Renault;Dacia", modeles=models, famille_moteur=fam, codes_dtc=";".join(codes),
                      voyants=";".join(voy), documents_lies=";".join(lies), groupes_acces=groupes,
                      origine=origine, licence=licence, statut_validation="à valider", fichier=fichier))
def elem(eid, doc_id, page, typ, desc, img=""):
    ELEMENTS.append(dict(element_id=eid, document_id=doc_id, page=page, type=typ, description=desc, fichier_image=img))
G_TECH = "techniciens;chefs_atelier"
G_ALL = "techniciens;chefs_atelier;receptionnaires"

# ============================================================ PROCÉDURES
PROCS = {
 "PROC-01": dict(titre="Contrôle des ratés d'allumage", fam="essence",
   codes=["P0300", "P0301", "P0302", "P0303", "P0304", "P0351"], voy=["V01", "V02"], sch=["SCH-01"],
   outils="Outil de diagnostic OBD, clé à bougie, multimètre, compressiomètre",
   but="Localiser l'origine d'un raté d'allumage : bobine, bougie, injecteur ou mécanique.",
   etapes=["Lire les codes et les données figées ; noter le cylindre concerné (P0301 à P0304) ou des ratés multiples (P0300).",
           "Vérifier l'identification du moteur : le 1.0 TCe compte 3 cylindres, un code P0304 y est donc incohérent.",
           "Contact coupé et moteur froid, déposer la bobine du cylindre concerné et inspecter le connecteur.",
           "Permuter cette bobine avec celle d'un cylindre voisin, effacer les codes, faire tourner le moteur puis relire les codes.",
           "Si le raté ne suit pas la bobine, contrôler la bougie : usure des électrodes, encrassement, fissure de la céramique.",
           "Si le raté persiste, contrôler l'injecteur du cylindre puis la compression.",
           "En cas de ratés multiples sans cylindre dominant, rechercher une prise d'air ou un problème de carburant (PROC-02)."],
   interp=[("Le raté suit la bobine permutée", "Bobine d'allumage défectueuse"),
           ("Le raté reste sur le même cylindre, bougie usée", "Bougie à remplacer"),
           ("Compression faible sur un cylindre", "Défaut mécanique : investigation atelier"),
           ("Ratés sur plusieurs cylindres", "Cause commune : air, carburant, allumage")],
   secu="Ne pas prolonger un essai témoin clignotant : les ratés surchauffent le catalyseur."),
 "PROC-02": dict(titre="Contrôle du mélange air/carburant et des prises d'air", fam="essence",
   codes=["P0171", "P0172", "P0100", "P0101", "P0130", "P0505"], voy=["V01"], sch=["SCH-02"],
   outils="Outil de diagnostic OBD (lecture des paramètres en direct), bombe de détection ou générateur de fumée",
   but="Distinguer une prise d'air, un débitmètre défaillant ou un défaut d'alimentation en carburant.",
   etapes=["Lire les codes, puis relever les corrections de richesse court terme et long terme, moteur chaud, au ralenti et vers 2 500 tr/min.",
           "Une correction long terme fortement positive indique un mélange pauvre compensé ; fortement négative, un mélange riche.",
           "Mélange pauvre au ralenti qui se normalise en charge : rechercher une prise d'air (durites, joint de collecteur, recyclage des vapeurs d'huile).",
           "Mélange pauvre à tous les régimes : contrôler le débitmètre (connecteur, propreté) et la pression d'alimentation en carburant.",
           "Mélange riche : rechercher un injecteur qui fuit, une pression de carburant excessive ou un débitmètre qui surestime.",
           "Contrôler l'oscillation du signal de la sonde lambda amont."],
   interp=[("Pauvre au ralenti seulement", "Prise d'air probable"),
           ("Pauvre à tous les régimes", "Débitmètre ou pression de carburant"),
           ("Riche à tous les régimes", "Injecteur, pression excessive ou débitmètre"),
           ("Signal lambda figé", "Sonde lambda ou son chauffage")],
   secu="Pas de flamme ni de point chaud pendant la recherche de fuite ; travailler en zone ventilée.",
   note="Les relevés réels fournis avec les jeux de données contiennent les colonnes correction_court_terme_pct et correction_long_terme_pct : ils montrent le format attendu."),
 "PROC-03": dict(titre="Contrôle de la vanne EGR", fam="les_deux",
   codes=["P0401", "P0402", "P0403"], voy=["V01"], sch=["SCH-03"],
   outils="Outil de diagnostic OBD, multimètre, outillage de dépose",
   but="Établir si le défaut de recirculation vient de l'encrassement, de la commande ou du circuit électrique.",
   etapes=["Lire les codes et les conditions d'apparition (régime, charge, température).",
           "Inspecter le connecteur de la vanne et, selon le montage, les durites de commande.",
           "Pour P0403, contrôler l'alimentation, la masse et la continuité du circuit de commande.",
           "Comparer la position commandée et la position mesurée de la vanne dans les paramètres en direct.",
           "Déposer la vanne et rechercher calamine et point dur.",
           "Nettoyer ou remplacer la vanne, contrôler les conduits, puis effacer les codes et faire un essai routier."],
   interp=[("Position mesurée différente de la commande", "Vanne grippée ou encrassée"),
           ("Circuit ouvert ou en court-circuit", "Faisceau ou connecteur"),
           ("Conduits obstrués, vanne libre", "Nettoyage des conduits")],
   secu="Laisser refroidir la ligne d'échappement avant dépose."),
 "PROC-04": dict(titre="Contrôle du filtre à particules", fam="diesel",
   codes=["P2002", "P0471"], voy=["V04"], sch=["SCH-04"],
   outils="Outil de diagnostic OBD, lampe d'inspection",
   but="Distinguer un FAP colmaté, un FAP endommagé et un défaut de mesure de pression différentielle.",
   etapes=["Lire les codes ; relever la pression différentielle et, si disponible, la charge en suies estimée.",
           "Témoin V04 allumé sans code de défaillance : colmatage, la régénération est à prévoir.",
           "Inspecter les deux durites du capteur de pression différentielle : fissure, débranchement ou inversion amont/aval (P0471).",
           "Pression différentielle anormalement faible avec un FAP réputé chargé : FAP endommagé possible (P2002).",
           "Rechercher la cause de l'encrassement : trajets courts, vanne EGR, injecteurs, huile non conforme.",
           "Une régénération forcée se fait avec l'outil du technicien, jamais depuis l'assistant."],
   interp=[("Pression élevée, aucun code de défaillance", "FAP colmaté : régénération"),
           ("Pression nulle ou incohérente", "Durites ou capteur (P0471)"),
           ("Pression faible, fumée à l'échappement", "FAP endommagé (P2002)")],
   secu="Régénération : véhicule à l'extérieur, loin de toute matière inflammable ; l'échappement devient très chaud."),
 "PROC-05": dict(titre="Contrôle du préchauffage diesel", fam="diesel",
   codes=["P0380", "P0670"], voy=["V03"], sch=["SCH-05"],
   outils="Outil de diagnostic OBD, multimètre, clé dynamométrique",
   but="Identifier une bougie de préchauffage coupée ou un défaut du boîtier de préchauffage.",
   etapes=["Lire les codes et observer le témoin V03 au contact.",
           "Contrôler l'alimentation et la masse du boîtier de préchauffage.",
           "Débrancher chaque bougie et mesurer sa résistance : une bougie coupée présente un circuit ouvert.",
           "Comparer les bougies entre elles et contrôler le faisceau entre le boîtier et chaque bougie.",
           "Remplacer l'élément défaillant en respectant le couple de serrage préconisé."],
   interp=[("Une bougie en circuit ouvert", "Bougie de préchauffage (P0380)"),
           ("Aucune bougie alimentée", "Boîtier ou sa commande (P0670)")],
   secu="Une bougie grippée peut casser à la dépose : suivre la méthode du constructeur."),
 "PROC-06": dict(titre="Contrôle du circuit de charge", fam="les_deux",
   codes=["P0562"], voy=["V07"], sch=["SCH-06"],
   outils="Multimètre, testeur de batterie",
   but="Distinguer une batterie faible, un défaut de charge et un mauvais contact.",
   etapes=["Mesurer la tension de la batterie au repos, moteur arrêté depuis plusieurs heures.",
           "Mesurer la tension moteur tournant et la comparer à la plage de charge prévue par le constructeur.",
           "Contrôler l'état et la tension de la courroie d'accessoires.",
           "Contrôler cosses et masses : oxydation, serrage.",
           "Tester la batterie avec un testeur adapté.",
           "Si la tension de charge reste basse avec une batterie saine, contrôler l'alternateur et son régulateur."],
   interp=[("Tension au repos basse, charge correcte", "Batterie à recharger ou remplacer"),
           ("Tension de charge basse", "Alternateur, régulateur ou courroie"),
           ("Chute de tension aux cosses", "Contact oxydé ou desserré")],
   secu="Ne jamais débrancher la batterie moteur tournant."),
 "PROC-07": dict(titre="Contrôle du circuit de refroidissement et du thermostat", fam="les_deux",
   codes=["P0117", "P0118", "P0128"], voy=["V06"], sch=["SCH-07"],
   outils="Outil de diagnostic OBD, multimètre, thermomètre infrarouge",
   but="Distinguer un défaut de capteur, un thermostat bloqué et un manque de liquide.",
   etapes=["Lire les codes et suivre la température du liquide dans les paramètres en direct.",
           "Moteur froid uniquement, contrôler le niveau du vase d'expansion.",
           "P0117 ou P0118 : contrôler connecteur et faisceau du capteur ; comparer la valeur lue à la température réelle.",
           "P0128 : suivre la montée en température en roulant ; une température qui plafonne bas oriente vers un thermostat bloqué ouvert.",
           "Contrôler la mise en marche du motoventilateur.",
           "Après intervention, purger le circuit selon la méthode du constructeur."],
   interp=[("Valeur lue aberrante, moteur froid", "Capteur ou faisceau (P0117, P0118)"),
           ("Montée en température trop lente", "Thermostat bloqué ouvert (P0128)"),
           ("Surchauffe, témoin V06", "Manque de liquide, pompe ou ventilateur : arrêt immédiat")],
   secu="Ne jamais ouvrir le vase d'expansion moteur chaud : risque de brûlure grave."),
 "PROC-08": dict(titre="Contrôle de la suralimentation et de la pression carburant", fam="les_deux",
   codes=["P0234", "P0299", "P0087", "P0088"], voy=["V01"], sch=["SCH-03"],
   outils="Outil de diagnostic OBD, lampe d'inspection",
   but="Localiser une fuite d'air de suralimentation ou un défaut de régulation de pression.",
   etapes=["Lire les codes ; comparer pression de suralimentation demandée et mesurée, puis pression rail demandée et mesurée.",
           "P0299 : inspecter durites, colliers et échangeur (fuite, trace d'huile).",
           "Contrôler la commande de l'actionneur du turbocompresseur.",
           "P0234 : rechercher un actionneur bloqué ou un capteur de pression défaillant.",
           "P0087 : contrôler le filtre à carburant, l'alimentation basse pression et le régulateur.",
           "P0088 : contrôler le régulateur et le capteur de pression rail."],
   interp=[("Mesurée inférieure à la demandée en charge", "Fuite d'air ou actionneur (P0299)"),
           ("Mesurée supérieure à la demandée", "Actionneur bloqué ou capteur (P0234)"),
           ("Pression rail basse", "Filtre, pompe ou régulateur (P0087)")],
   secu="Circuit carburant haute pression : ne desserrer aucun raccord moteur tournant ; attendre la chute de pression."),
}
for pid, p in PROCS.items():
    S = [P(f"Procédure {pid}", "t"), P(p["titre"], "s"), Spacer(1, 8),
         kv([("Codes concernés", ", ".join(p["codes"])), ("Voyants", ", ".join(p["voy"])),
             ("Motorisations", FAM[p["fam"]]), ("Outillage", p["outils"]), ("Schéma associé", ", ".join(p["sch"]))]),
         P("Objectif", "h"), P(p["but"]), P("Étapes", "h")] + num(p["etapes"]) + [
         P("Interprétation des résultats", "h"), grid([["Observation", "Piste"]] + [list(x) for x in p["interp"]], [85 * mm, 85 * mm]),
         P("Sécurité", "h"), P(p["secu"])]
    if p.get("note"):
        S += [P("Remarque", "h"), P(p["note"])]
    n = build(OUT / "procedures" / f"DOC-{pid}.pdf", f"DOC-{pid}", S)
    reg(f"DOC-{pid}", p["titre"], "procedure", n, p["fam"], p["codes"], p["voy"],
        [f"DOC-{s}" for s in p["sch"]] + [f"DOC-DTC-{c}" for c in p["codes"]], G_TECH,
        "rédigé par l'équipe", "équipe RenDacDiag", f"procedures/DOC-{pid}.pdf")
    elem(f"DOC-{pid}_etapes", f"DOC-{pid}", 1, "liste", f"Étapes de la procédure {p['titre'].lower()}")
    elem(f"DOC-{pid}_tab1", f"DOC-{pid}", 1, "tableau", "Interprétation des résultats")
CODE2PROC = {c: pid for pid, p in PROCS.items() for c in p["codes"]}
VOY2PROC = {}
for pid, p in PROCS.items():
    for v in p["voy"]:
        if v != "V01": VOY2PROC.setdefault(v, pid)

# ============================================================ SCHÉMAS
class Sch:
    def __init__(self, Hu):
        self.W = 170 * mm; self.s = self.W / 760.0; self.H = Hu * self.s
        self.d = Drawing(self.W, self.H)
    def X(self, v): return v * self.s
    def Y(self, v): return self.H - v * self.s
    def box(self, cx, cy, w, name, sub="", accent=False, h=50):
        s = self.s
        self.d.add(Rect(self.X(cx - w / 2), self.Y(cy + h / 2), w * s, h * s, rx=4, ry=4,
                        fillColor=colors.HexColor("#DCE6F4") if accent else colors.white,
                        strokeColor=NAVY if accent else EDGE, strokeWidth=1.4 if accent else 0.9))
        dy = -3 if sub else 3
        self.d.add(String(self.X(cx), self.Y(cy + dy), name, fontName="Carlito-Bold", fontSize=9, fillColor=NAVY, textAnchor="middle"))
        if sub:
            self.d.add(String(self.X(cx), self.Y(cy + 14), sub, fontName="Carlito", fontSize=7.5, fillColor=GREY, textAnchor="middle"))
    def path(self, pts, end=True, start=False, dash=False):
        flat = []
        for x, y in pts: flat += [self.X(x), self.Y(y)]
        pl = PolyLine(flat, strokeColor=EDGE, strokeWidth=1.1)
        if dash: pl.strokeDashArray = [3, 2]
        self.d.add(pl)
        if end: self._head(pts[-2], pts[-1])
        if start: self._head(pts[1], pts[0])
    def _head(self, a, b):
        ang = math.atan2(self.Y(b[1]) - self.Y(a[1]), self.X(b[0]) - self.X(a[0])); L = 5.5
        bx, by = self.X(b[0]), self.Y(b[1])
        self.d.add(Polygon([bx, by, bx - L * math.cos(ang - 0.42), by - L * math.sin(ang - 0.42),
                            bx - L * math.cos(ang + 0.42), by - L * math.sin(ang + 0.42)],
                           fillColor=EDGE, strokeColor=EDGE, strokeWidth=0.1))
    def label(self, x, y, t, anchor="start"):
        self.d.add(String(self.X(x), self.Y(y), t, fontName="Carlito-Italic", fontSize=7.5, fillColor=GREY, textAnchor=anchor))

def sch01():
    g = Sch(310)
    g.box(130, 60, 180, "Batterie 12 V")
    g.box(380, 60, 220, "Calculateur moteur", "gestion de l'avance et de l'allumage", True)
    g.box(640, 60, 200, "Capteur de vilebrequin", "régime et position (P0335)")
    g.box(640, 140, 200, "Capteur d'arbre à cames", "phase (P0340, P0016)")
    g.box(640, 220, 200, "Capteur de cliquetis", "détonation (P0325)")
    g.box(380, 170, 220, "Bobines crayon", "une par cylindre (P0351)")
    g.box(380, 275, 220, "Bougies d'allumage", "ratés : P0300 à P0304")
    g.path([(220, 60), (270, 60)]); g.label(245, 52, "+12 V", "middle")
    g.path([(540, 140), (515, 140)], end=False); g.path([(540, 220), (515, 220), (515, 60)], end=False)
    g.path([(540, 60), (490, 60)]); g.label(497, 52, "signaux", "start")
    g.path([(380, 85), (380, 145)]); g.label(388, 120, "commande")
    g.path([(380, 195), (380, 250)]); g.label(388, 226, "haute tension")
    return g.d, "Schéma de principe du circuit d'allumage (moteurs essence TCe)", \
        ["Le calculateur reçoit le régime et la position du vilebrequin, la phase de l'arbre à cames et le signal de cliquetis.",
         "Il commande chaque bobine crayon, qui fournit la haute tension à la bougie de son cylindre.",
         "Le 1.0 TCe compte 3 cylindres, le 1.3 TCe en compte 4."], "essence", \
        ["P0300", "P0301", "P0302", "P0303", "P0304", "P0351", "P0335", "P0340", "P0016", "P0325"], ["PROC-01"]

def sch02():
    g = Sch(345)
    for x, n, sub in [(95, "Filtre à air", ""), (265, "Débitmètre", "P0100, P0101"), (435, "Papillon motorisé", "ralenti : P0505"),
                      (605, "Collecteur d'admission", "")]:
        g.box(x, 70, 150, n, sub)
    for a, b in [(170, 190), (340, 360), (510, 530)]:
        g.path([(a, 70), (b, 70)])
    g.label(100, 30, "air", "middle")
    g.box(350, 200, 220, "Calculateur moteur", "corrections : P0171, P0172", True)
    g.box(605, 200, 150, "Injecteurs", "un par cylindre")
    g.box(350, 310, 220, "Sonde lambda amont", "richesse (P0130)")
    g.box(605, 310, 150, "Pompe à carburant", "alimentation")
    g.path([(265, 95), (265, 175)]); g.label(258, 140, "débit d'air", "end")
    g.path([(435, 95), (435, 175)], start=True); g.label(443, 140, "position / commande")
    g.path([(460, 200), (530, 200)]); g.label(495, 192, "commande", "middle")
    g.path([(605, 175), (605, 95)]); g.label(613, 140, "carburant")
    g.path([(350, 285), (350, 225)]); g.label(358, 258, "signal")
    g.path([(605, 285), (605, 225)]); g.label(613, 258, "pression")
    return g.d, "Schéma de principe de l'admission et de l'injection (moteurs essence TCe)", \
        ["L'air traverse le filtre, le débitmètre puis le papillon motorisé avant le collecteur.",
         "Le calculateur dose l'injection d'après le débit d'air et corrige la richesse avec la sonde lambda amont.",
         "Une prise d'air en aval du débitmètre n'est pas mesurée : le mélange devient pauvre (P0171)."], "essence", \
        ["P0100", "P0101", "P0505", "P0171", "P0172", "P0130", "P0087", "P0088"], ["PROC-02", "PROC-08"]

def sch03():
    g = Sch(350)
    for x, n, sub in [(95, "Filtre à air", ""), (265, "Débitmètre", "P0101"), (435, "Compresseur du turbo", "P0234, P0299"),
                      (605, "Échangeur", "refroidit l'air")]:
        g.box(x, 70, 150, n, sub)
    for a, b in [(170, 190), (340, 360), (510, 530)]:
        g.path([(a, 70), (b, 70)])
    g.box(435, 195, 220, "Moteur 1.5 Blue dCi", "admission / échappement", True)
    g.box(150, 195, 160, "Vanne EGR", "P0401, P0402, P0403")
    g.box(435, 310, 220, "Turbine du turbo", "entraîne le compresseur")
    g.box(665, 310, 150, "Ligne d'échappement", "vers le FAP (SCH-04)")
    g.path([(605, 95), (605, 195), (545, 195)]); g.label(613, 150, "air suralimenté")
    g.path([(325, 205), (230, 205)]); g.label(278, 222, "gaz prélevés", "middle")
    g.path([(150, 170), (150, 132), (435, 132), (435, 170)]); g.label(292, 125, "gaz réinjectés à l'admission", "middle")
    g.path([(435, 220), (435, 285)]); g.label(443, 255, "gaz d'échappement")
    g.path([(545, 310), (590, 310)])
    return g.d, "Schéma de principe de l'air et de la recirculation EGR (diesel 1.5 Blue dCi)", \
        ["Le compresseur du turbo, entraîné par la turbine, comprime l'air refroidi ensuite par l'échangeur.",
         "La vanne EGR prélève une partie des gaz d'échappement et la réinjecte à l'admission pour réduire les oxydes d'azote.",
         "Une fuite entre le compresseur et le moteur provoque une suralimentation insuffisante (P0299)."], "diesel", \
        ["P0101", "P0234", "P0299", "P0401", "P0402", "P0403"], ["PROC-03", "PROC-08"]

def sch04():
    g = Sch(350)
    for x, w, n, sub in [(80, 120, "Moteur", "et turbine"), (230, 150, "Catalyseur d'oxydation", ""),
                         (395, 150, "Filtre à particules", "FAP (P2002)"), (560, 150, "Catalyseur SCR", "oxydes d'azote"),
                         (700, 90, "Sortie", "")]:
        g.box(x, 90, w, n, sub)
    for a, b in [(140, 155), (305, 320), (470, 485), (635, 655)]:
        g.path([(a, 90), (b, 90)])
    g.box(360, 210, 200, "Capteur de pression", "différentielle (P0471)")
    g.path([(330, 185), (330, 115)], end=False); g.path([(440, 185), (440, 115)], end=False)
    g.label(322, 152, "amont", "end"); g.label(448, 152, "aval")
    g.box(360, 320, 200, "Calculateur moteur", "pilote la régénération", True)
    g.path([(360, 235), (360, 295)]); g.label(368, 268, "mesure")
    g.box(600, 210, 160, "Injecteur d'AdBlue", "voyant V19")
    g.box(600, 320, 160, "Réservoir d'AdBlue", "")
    g.path([(600, 185), (600, 115)])
    g.path([(600, 295), (600, 235)])
    return g.d, "Schéma de principe de la ligne d'échappement diesel", \
        ["Le FAP retient les suies ; le capteur de pression différentielle mesure son colmatage entre l'amont et l'aval.",
         "Le calculateur déclenche la régénération quand la charge en suies est élevée (voyant V04).",
         "L'AdBlue injecté avant le catalyseur SCR réduit les oxydes d'azote (voyant V19)."], "diesel", \
        ["P2002", "P0471"], ["PROC-04"]

def sch05():
    g = Sch(325)
    g.box(150, 70, 200, "Calculateur moteur", "durée de préchauffage", True)
    g.box(430, 70, 200, "Boîtier de préchauffage", "P0670")
    g.box(680, 70, 140, "Batterie 12 V")
    g.box(160, 190, 220, "Témoin de préchauffage", "voyant V03")
    g.path([(250, 70), (330, 70)]); g.label(290, 62, "commande", "middle")
    g.path([(610, 70), (530, 70)]); g.label(570, 62, "+12 V", "middle")
    g.path([(160, 95), (160, 165)]); g.label(168, 132, "allumage du témoin")
    xs = [160, 320, 480, 640]
    g.path([(430, 95), (430, 245)], end=False); g.path([(160, 245), (640, 245)], end=False)
    for k, x in enumerate(xs, 1):
        g.path([(x, 245), (x, 275)])
        g.box(x, 300, 130, f"Bougie {k}", "P0380")
    return g.d, "Schéma de principe du préchauffage diesel", \
        ["Le calculateur fixe la durée de préchauffage et commande le boîtier, alimenté par la batterie.",
         "Le boîtier alimente chacune des quatre bougies de préchauffage.",
         "Le témoin V03 reste allumé pendant le préchauffage ; il ne doit pas clignoter en roulant."], "diesel", \
        ["P0380", "P0670"], ["PROC-05"]

def sch06():
    g = Sch(250)
    g.box(130, 80, 180, "Alternateur", "avec régulateur")
    g.box(380, 80, 180, "Batterie 12 V")
    g.box(630, 80, 180, "Réseau de bord", "consommateurs")
    g.box(130, 200, 180, "Courroie d'accessoires", "entraînée par le moteur")
    g.box(380, 200, 180, "Calculateur moteur", "tension : P0562", True)
    g.box(630, 200, 180, "Témoin de charge", "voyant V07")
    g.path([(220, 80), (290, 80)]); g.label(255, 72, "charge", "middle")
    g.path([(470, 80), (540, 80)]); g.label(505, 72, "alimentation", "middle")
    g.path([(130, 175), (130, 105)]); g.label(138, 142, "entraînement")
    g.path([(380, 105), (380, 175)]); g.label(388, 142, "tension mesurée")
    g.path([(470, 200), (540, 200)]); g.label(505, 192, "alerte", "middle")
    return g.d, "Schéma de principe du circuit de charge", \
        ["L'alternateur, entraîné par la courroie d'accessoires, recharge la batterie et alimente le réseau de bord.",
         "Le calculateur surveille la tension ; une tension trop basse enregistre P0562 et peut allumer le témoin V07."], "les_deux", \
        ["P0562"], ["PROC-06"]

def sch07():
    g = Sch(360)
    g.box(110, 80, 140, "Pompe à eau")
    g.box(380, 80, 200, "Moteur", "chemises d'eau", True)
    g.box(640, 80, 180, "Thermostat", "P0128")
    g.box(640, 210, 180, "Radiateur", "et motoventilateur")
    g.box(380, 210, 200, "Capteur de température", "P0117, P0118")
    g.box(130, 210, 140, "Calculateur moteur", "témoin V06")
    g.path([(180, 80), (280, 80)])
    g.path([(480, 80), (550, 80)])
    g.path([(640, 105), (640, 185)]); g.label(648, 148, "moteur chaud")
    g.path([(640, 235), (640, 330), (30, 330), (30, 80), (40, 80)]); g.label(335, 322, "retour du liquide refroidi", "middle")
    g.path([(380, 185), (380, 105)], end=False, start=True); g.label(388, 148, "mesure")
    g.path([(280, 210), (200, 210)]); g.label(240, 202, "signal", "middle")
    return g.d, "Schéma de principe du circuit de refroidissement", \
        ["La pompe fait circuler le liquide dans le moteur ; le thermostat l'envoie au radiateur une fois le moteur chaud.",
         "Le capteur de température informe le calculateur, qui pilote le motoventilateur et le témoin V06.",
         "Un thermostat bloqué ouvert empêche le moteur d'atteindre sa température (P0128)."], "les_deux", \
        ["P0117", "P0118", "P0128"], ["PROC-07"]

CODE2SCH = {}
for k, fn in enumerate([sch01, sch02, sch03, sch04, sch05, sch06, sch07], 1):
    sid = f"SCH-{k:02d}"; doc_id = f"DOC-{sid}"
    dr, titre, lecture, fam, codes, procs = fn()
    S = [P(f"Schéma {sid}", "t"), P(titre, "s"), Spacer(1, 10), dr, Spacer(1, 4),
         P(f"Figure 1 ({doc_id}_fig1) : {titre[0].lower() + titre[1:]}. Schéma simplifié, non contractuel.", "n"),
         P("Lecture du schéma", "h")] + bul(lecture) + [
         P("Codes défaut liés", "h"), P(", ".join(codes)),
         P("Documents liés", "h"), P(", ".join(f"DOC-{p}" for p in procs))]
    n = build(OUT / "schemas" / f"{doc_id}.pdf", doc_id, S)
    img = f"images/schemas/{doc_id}_fig1.png"
    from reportlab.graphics import renderPM
    renderPM.drawToFile(dr, str(OUT / img), fmt="PNG", dpi=200, bg=0xFFFFFF)
    reg(doc_id, titre, "schema", n, fam, codes, [], [f"DOC-{p}" for p in procs], G_TECH,
        "rédigé par l'équipe", "équipe RenDacDiag", f"schemas/{doc_id}.pdf")
    elem(f"{doc_id}_fig1", doc_id, 1, "figure", titre, img)
    for c in codes: CODE2SCH.setdefault(c, sid)

# ============================================================ FICHES DTC (allégées)
allcodes = {r["code"]: r for r in csv.DictReader(open(DS / "01_codes_dtc/dtc_codes.csv", encoding="utf-8"))}
prio = [r for r in allcodes.values() if r["prioritaire"] == "oui"]
SPECIFIC = {
 "P0304": "Code incohérent sur un 1.0 TCe (3 cylindres) : vérifier l'identification du véhicule avant tout diagnostic.",
 "P0300": "Si le témoin moteur clignote, réduire la charge : des ratés prolongés endommagent le catalyseur.",
 "P0420": "Un catalyseur ne s'use pas seul : rechercher d'abord des ratés d'allumage ou une consommation d'huile antérieurs.",
 "P0700": "Ce code signale seulement un défaut mémorisé dans le calculateur de boîte : lire ce calculateur pour le code précis.",
 "P0606": "Ne pas conclure au remplacement du calculateur avant d'avoir contrôlé ses alimentations et ses masses.",
 "P2002": "Contrôler d'abord les durites du capteur de pression différentielle : leur défaut imite un FAP endommagé.",
 "P0128": "Le défaut apparaît surtout par temps froid et sur trajets courts ; vérifier en roulant la montée en température.",
}
for k in ["P0301", "P0302", "P0303"]:
    SPECIFIC[k] = "Méthode rapide : permuter la bobine avec un cylindre voisin et observer si le code suit la bobine."
for r in sorted(prio, key=lambda x: x["code"]):
    c = r["code"]; doc_id = f"DOC-DTC-{c}"
    causes = [x.strip()[0].upper() + x.strip()[1:] for x in r["causes_probables_fr"].split(";") if x.strip()]
    voisins = [k for k in sorted(allcodes) if k != c and k[:4] == c[:4]][:4]
    lies = [f"DOC-{x}" for x in [CODE2PROC.get(c), CODE2SCH.get(c)] if x] + ["DOC-GEN-01"]
    S = [P(f"Fiche code défaut {c}", "t"), P(r["libelle_fr"], "s"), Spacer(1, 8),
         kv([("Code", c), ("Système", f"{r['systeme']} · {r['sous_systeme']}"),
             ("Motorisations", FAM.get(r["famille_moteur"], r["famille_moteur"])),
             ("Définition SAE J2012", r["description_en"])]),
         P("Description", "h"),
         P(f"Le calculateur enregistre {c} lorsqu'il détecte : {r['libelle_fr'][0].lower() + r['libelle_fr'][1:]}."),
         P("Causes probables, par ordre de fréquence", "h")] + num(causes)
    if c in SPECIFIC:
        S += [P("Point d'attention", "h"), P(SPECIFIC[c])]
    S += [P("Codes voisins à ne pas confondre", "h")] + bul([f"{k} : {allcodes[k]['description_en']}" for k in voisins]) + [
          P("Documents liés", "h"), P(", ".join(lies))]
    n = build(OUT / "fiches_dtc" / f"{doc_id}.pdf", doc_id, S)
    reg(doc_id, f"Fiche code {c} – {r['libelle_fr']}", "fiche_dtc", n, r["famille_moteur"], [c], [], lies, G_TECH,
        "définition SAE via python-OBD ; libellé et causes rédigés par l'équipe", "GPL-2.0 (définition) ; équipe",
        f"fiches_dtc/{doc_id}.pdf")
    elem(f"{doc_id}_causes", doc_id, 1, "liste", f"Causes probables du code {c}")

# ============================================================ FICHES VOYANTS (allégées)
for v in csv.DictReader(open(DS / "03_voyants/catalogue_voyants.csv", encoding="utf-8")):
    vid = v["id"]; doc_id = f"DOC-VOY-{vid}"
    picto = DS / "03_voyants/pictogrammes" / f"{vid}.png"
    shutil.copy(picto, OUT / "images/pictogrammes" / f"{vid}.png")
    img = Image(str(picto), width=38 * mm, height=38 * mm)
    head = Table([[[P(f"Fiche voyant {vid}", "t"), P(v["nom"], "s"), Spacer(1, 6),
                    P(f"Figure 1 ({doc_id}_fig1) : pictogramme indicatif, couleur {v['couleur']}.", "n")], img]],
                 colWidths=[128 * mm, 42 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    lies = [f"DOC-{VOY2PROC[vid]}"] if vid in VOY2PROC else []
    lies += ["DOC-GEN-01"]
    S = [head, Spacer(1, 4),
         kv([("Couleur", v["couleur"]), ("État", v["etat"]), ("Gravité", v["gravite"]),
             ("Motorisations", FAM.get(v["famille_moteur"], v["famille_moteur"]))],
            [("BACKGROUND", (1, 2), (1, 2), SEV.get(v["gravite"], colors.white))]),
         P("Signification", "h"), P(v["signification"] + "."),
         P("Conduite à tenir", "h"), P(v["conduite_a_tenir"] + "."),
         P("Documents liés", "h"), P(", ".join(lies))]
    n = build(OUT / "fiches_voyants" / f"{doc_id}.pdf", doc_id, S)
    reg(doc_id, f"Fiche voyant – {v['nom']}", "fiche_voyant", n, v["famille_moteur"], [], [vid], lies, G_ALL,
        "rédigé par l'équipe ; pictogramme dérivé de Material Design Icons", "équipe ; Apache-2.0 (pictogramme)",
        f"fiches_voyants/{doc_id}.pdf")
    elem(f"{doc_id}_fig1", doc_id, 1, "figure", f"Pictogramme du voyant {v['nom']}", f"images/pictogrammes/{vid}.png")

# ============================================================ RÈGLES GÉNÉRALES
S = [P("Règles générales de diagnostic", "t"), P("Principes communs à toutes les fiches du corpus", "s"), Spacer(1, 8),
     P("1. Couleur des voyants", "h"),
     grid([["Couleur", "Signification", "Conduite"],
           ["Rouge", "Défaut grave ou risque pour la sécurité", "S'arrêter dès que possible en sécurité"],
           ["Orange", "Fonctionnement dégradé ou alerte", "Faire contrôler rapidement en atelier"],
           ["Vert ou bleu", "Information sur un système en fonctionnement", "Aucune action"]], [30 * mm, 75 * mm, 65 * mm]),
     P("2. Identifier un voyant sur photo", "h")] + bul([
       "Confirmer la couleur exacte et si le voyant est fixe ou clignotant.",
       "Vérifier le modèle et la phase du véhicule : l'emplacement des voyants varie d'un tableau de bord à l'autre.",
       "Une ressemblance ne suffit pas : en cas de doute, demander une nouvelle photo ou consulter la notice du véhicule."]) + [
     P("3. Lire un code défaut", "h")] + bul([
       "Un code oriente le diagnostic ; il ne désigne pas à lui seul la pièce défectueuse.",
       "Relever les données figées (régime, température, charge, vitesse) au moment de l'apparition du code.",
       "Les codes P0xxx, P2xxx et P3xxx sont génériques ; les codes P1xxx sont propres au constructeur et ne figurent pas dans ce corpus."]) + [
     P("4. Après réparation", "h")] + bul([
       "Effacer les codes uniquement après réparation, avec l'outil de diagnostic du technicien.",
       "Réaliser un essai routier puis relire les codes pour confirmer la réparation."]) + [
     P("5. Sécurité et limites", "h")] + bul([
       "Respecter les procédures du constructeur et les consignes de sécurité de l'atelier.",
       "Systèmes hors périmètre : haute tension des véhicules E-Tech, airbags, antidémarrage, compteur kilométrique.",
       "L'assistant n'envoie aucune commande au véhicule : effacement, codage et régénération forcée restent des actions du technicien."]) + [
     P("6. Sources", "h"),
     P("Définitions normalisées des codes : python-OBD (GPL-2.0), recoupées avec dtcdb (MIT). Pictogrammes dérivés des "
       "Material Design Icons (Pictogrammers, Apache-2.0). Libellés, causes, procédures et schémas rédigés par l'équipe "
       "RenDacDiag, à valider par un technicien qualifié.")]
n = build(OUT / "general" / "DOC-GEN-01.pdf", "DOC-GEN-01", S)
reg("DOC-GEN-01", "Règles générales de diagnostic", "regles_generales", n, "les_deux", [], [], [], G_ALL,
    "rédigé par l'équipe", "équipe RenDacDiag", "general/DOC-GEN-01.pdf")
elem("DOC-GEN-01_tab1", "DOC-GEN-01", 1, "tableau", "Signification des couleurs de voyants")

# ============================================================ INDEX
INDEX.sort(key=lambda r: ({"regles_generales": 0, "procedure": 1, "schema": 2, "fiche_dtc": 3, "fiche_voyant": 4}[r["type"]], r["document_id"]))
with open(OUT / "index_corpus.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(INDEX[0].keys())); w.writeheader(); w.writerows(INDEX)
with open(OUT / "index_elements.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(ELEMENTS[0].keys())); w.writeheader(); w.writerows(ELEMENTS)
TYPES = {"regles_generales": "Règles", "procedure": "Procédure", "schema": "Schéma", "fiche_dtc": "Fiche DTC", "fiche_voyant": "Fiche voyant"}
rows = [["Document", "Titre", "Type", "Motorisation"]] + [[r["document_id"], r["titre"], TYPES[r["type"]], FAM.get(r["famille_moteur"], r["famille_moteur"])] for r in INDEX]
cnt = {t: sum(1 for r in INDEX if r["type"] == t) for t in TYPES}
build(OUT / "00_INDEX_CORPUS.pdf", "INDEX", [P("Corpus RenDacDiag — index", "t"),
      P(f"{len(INDEX)} documents : {cnt['regles_generales']} règles générales, {cnt['procedure']} procédures, {cnt['schema']} schémas, "
        f"{cnt['fiche_dtc']} fiches codes défaut, {cnt['fiche_voyant']} fiches voyants", "s"), Spacer(1, 8),
      grid(rows, [30 * mm, 90 * mm, 24 * mm, 26 * mm])])
print(len(INDEX), len(ELEMENTS), cnt)
