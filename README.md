# RenDacDiag

Assistant documentaire multimodal et agentique pour le diagnostic des véhicules Renault et Dacia (Clio V, Captur II, Sandero III, Duster II ; moteurs 1.0 TCe, 1.3 TCe et 1.5 Blue dCi). Application au diagnostic automobile du projet MaintiDoc.

Équipe RenDacDiag : Qossai Elaidi, Ebba Soufiane.

## État par livrable
| Livrable | Contenu | État |
|---|---|---|
| L1 | Cadrage, corpus (50 documents), architecture, risques | `docs/L1_MaintiDoc_RenDacDiag.pdf`, `corpus/` |
| L2 | Ingestion, index, recherche hybride, contrôle d'accès, évaluation | `src/`, `eval/`, `tests/`, `docs/L2_MaintiDoc_RenDacDiag.pdf` |

## Arborescence
```
corpus/            50 PDF, inventaire.csv, prompts_corpus.md, images, licences
config/users.yaml  utilisateurs de démonstration (mot de passe : demo-<login>)
src/rendacdiag/
  ingestion/       extraction PDF -> éléments (sections, tableaux, figures) + métadonnées
  index/           embedders (BGE-M3, CLIP, hash), BM25, construction Qdrant
  search/          recherche hybride (code exact + BM25 + dense + image, fusion RRF), CLI
  api/             API FastAPI : jeton, recherche filtrée, ouverture contrôlée des sources
  access.py        rôles, groupes d'accès, mots de passe
  dtc.py           extraction et décodage des codes défaut (format UDS inclus)
eval/              40 questions, script de mesure, résultats
tests/             20 tests pytest (sans modèle, embedder « hash »)
```

## Installation (Windows, macOS ou Linux, Python 3.11+)
```
python -m venv .venv
.venv\Scripts\activate            # Windows ;  source .venv/bin/activate  ailleurs
pip install -r requirements-models.txt
copy .env.example .env            # puis renseigner RDD_JWT_SECRET
set PYTHONPATH=src                # Windows ;  export PYTHONPATH=src  ailleurs
```
Aucun GPU n'est nécessaire pour le livrable 2 : BGE-M3 et CLIP tournent sur CPU (premier lancement : téléchargement d'environ 2,8 Go).

## Utilisation
```
python -m rendacdiag.ingestion.pipeline            # n'indexe que les documents « vérifié » de l'inventaire
python -m rendacdiag.ingestion.pipeline --inclure-non-verifies   # développement uniquement
python -m rendacdiag.index.build                   # index Qdrant texte (BGE-M3) et image (CLIP)
python -m rendacdiag.search.cli "DTC038096 sur un Duster dCi" --role technicien
python eval/run_eval.py                            # Recall@5, MRR@10, nDCG@5 + tests d'accès
uvicorn rendacdiag.api.main:app --app-dir src      # API sur http://localhost:8000/docs
pytest -q                                          # tests (RDD_TEXT_EMBEDDER=hash RDD_IMAGE_EMBEDDER=none)
```
Le Qdrant local (sur disque) n'accepte qu'un processus à la fois : arrêter l'API avant de lancer l'évaluation, ou utiliser `docker compose up` (serveur Qdrant).

## Résultats (40 questions, mode développement)
| Configuration | Recall@5 | MRR@10 | nDCG@5 | Top-1 |
|---|---|---|---|---|
| BM25 seul | 0.867 | 0.861 | 0.819 | 0.725 |
| Code exact + BM25 | 0.917 | 0.882 | 0.873 | 0.750 |
| Dense seul (BGE-M3) | 0.879 | 0.873 | 0.821 | 0.700 |
| Code exact + BM25 + dense | 0.917 | 0.921 | 0.899 | 0.825 |
| Hybride complet (+ CLIP) | 0.917 | 0.919 | 0.898 | 0.825 |

Tests d'accès : 10 / 10 sans fuite. Détail par question : `eval/resultats_l2.json`.
La liste image (CLIP) n'est utilisée que pour une question visuelle (schéma, voyant, témoin…) ou accompagnée d'une photo : appliquée à toutes les questions, elle faisait tomber le Top-1 de 0.825 à 0.675.

## Règle du corpus
Un document n'entre dans l'index que si son statut est « vérifié » dans `corpus/inventaire.csv` et que sa licence est renseignée. Les documents écartés et la raison sont listés dans `data/index/rapport_ingestion.json`.
