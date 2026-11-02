# Projet MaintiDoc — Livrable 1 : Cadrage, Corpus et Architecture

## Application au diagnostic automobile : RenDacDiag
Assistant documentaire multimodal et agentique pour le diagnostic des véhicules **Renault** et **Dacia** (Clio V, Captur II, Sandero III, Duster II) équipés des motorisations Essence TCe (1.0 TCe, 1.3 TCe) et Diesel Blue dCi (1.5 Blue dCi).

---

## 1. Membres de l'équipe
- **Soufiane EBBA**
- **Qossai ELAIDI**
- **Anas OUJADDI**

*Module IA générative multimodale — EMSI 2026*  
*Encadrant : Prof. Mariam CHERRABI*

---

## 2. Objectif du projet
Le projet **RenDacDiag** vise à assister les techniciens d'atelier et chefs d'atelier Renault/Dacia dans la résolution des pannes automobiles complexes :
- **Identification multimodale** : analyse conjointe des questions textuelles, des photographies de tableaux de bord/voyants et des codes défaut OBD-II (DTC).
- **RAG multimodal sourcé** : recherche filtrée par motorisation et modèle avec vérification stricte des citations et distinction source / observation / hypothèse.
- **Agentique & MCP** : consultation d'outils atelier (historique, relevés OBD, campagnes) et rédaction assistée d'ordres de réparation (OR) soumise à validation humaine préalable obligatoire.

---

## 3. Contenu de l'archive (L1_MaintiDoc_EBBA-ELAIDI-OUJADDI.zip)
L'archive respecte scrupuleusement l'arborescence et la nomenclature imposées par le cahier des charges :

```
L1_MaintiDoc_EBBA-ELAIDI-OUJADDI.zip
└── L1_MaintiDoc_EBBA-ELAIDI-OUJADDI/
    ├── L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_Rapport.pdf
    ├── L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_LienGitHub.txt
    ├── README.md
    └── L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_Corpus/
        ├── inventaire.csv
        ├── prompts_corpus.md
        ├── documents/
        │   ├── famille_1/
        │   └── famille_2/
        └── images/
```

### Détail des éléments :
1. **`L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_Rapport.pdf`** : Rapport complet de cadrage (17 pages) avec page de garde mise à jour pour l'équipe (Qossai Elaidi, Ebba Soufiane, Anas Oujaddi).
2. **`L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_LienGitHub.txt`** : URL du dépôt GitHub officiel du projet.
3. **`README.md`** : Synthèse de présentation du livrable 1 et de l'équipe.
4. **`L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_Corpus/`** :
   - **`inventaire.csv`** : Registre complet des 50 documents indexés avec leurs métadonnées.
   - **`prompts_corpus.md`** : Traçabilité détaillée des prompts P-01 à P-06 ayant servi à produire et valider le corpus documentaire.
   - **`documents/famille_1/`** : 25 documents PDF d'une page dédiés à la **Famille 1 : Motorisation Essence TCe**.
   - **`documents/famille_2/`** : 25 documents PDF d'une page dédiés à la **Famille 2 : Motorisation Diesel Blue dCi**.
   - **`images/`** : Pictogrammes des 20 voyants du tableau de bord (V01 à V20) et schémas fonctionnels de principe (DOC-SCH-01 à DOC-SCH-07).

---

## 4. Structure du dépôt GitHub
```
maintidoc/
├── README.md
├── .gitignore
├── docs/
│   ├── diagrammes/
│   └── L1_MaintiDoc_EBBA-ELAIDI-OUJADDI_Rapport.pdf
├── corpus/
│   ├── inventaire.csv
│   ├── prompts_corpus.md
│   ├── documents/
│   │   ├── famille_1/
│   │   └── famille_2/
│   └── images/
├── data/
├── prompts/
├── src/
├── mcp_server/
└── eval/
```
