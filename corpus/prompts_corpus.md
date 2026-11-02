# Traçabilité des prompts du corpus RenDacDiag

Les 50 documents du corpus ont été produits avec l'aide de Claude (Anthropic), assistant conversationnel équivalent à ChatGPT, en novembre 2026. La génération s'est faite en deux temps :

1. **Conversation** : les demandes ci-dessous ont été formulées par l'équipe ; l'assistant a proposé les contenus (libellés, causes, étapes, schémas).
2. **Script** : les contenus validés dans la conversation ont été écrits dans `generer_corpus.py`, qui produit les PDF de façon reproductible. Le script est la trace exacte du texte de chaque document.

Chaque ligne de `inventaire.csv` renvoie à un identifiant de prompt (colonne `prompt_id`). Les demandes sont citées telles qu'elles ont été envoyées, fautes comprises.

**Aucun document n'est considéré comme vérifié tant que les colonnes `verifie_par`, `date_verification` et `statut_verification` de l'inventaire ne sont pas remplies.** Un document non vérifié ou sans licence claire est exclu du corpus.

---

## P-01 — Cadrage du corpus et choix des sources réelles

**Demandes de l'équipe :**
- « j ai choisiser la sujet : doagnostic des voitures de la marque renault dacia »
- « construire les data set (reel)* »

**Ce que l'assistant a fait :** recherche de sources ouvertes ; retenu python-OBD (GPL-2.0, 2 066 codes OBD-II génériques SAE J2012) et dtcdb (MIT, 467 codes) pour recouper les définitions ; écarté la liste mytrile/obd-trouble-codes (définitions décalées d'une ligne, ex. P0300 défini comme « Cylinder 12 Contribution ») ; écarté la documentation après-vente Renault (propriétaire).

**Utilisé pour :** colonne « Définition SAE J2012 » des fiches DTC.

## P-02 — Fiches codes défaut (20 documents DOC-DTC-xxxxx)

**Demandes de l'équipe :**
- « je veux les data set pdf »
- « oui » (en réponse à la proposition d'alléger les fiches, d'enrichir l'index et d'ajouter procédures et schémas)

**Consigne de génération appliquée à chaque fiche :**
> Pour le code {code}, rédiger une fiche d'une page en français : identification (code, système, motorisations concernées, définition SAE J2012 en anglais), description en une phrase, causes probables classées par fréquence, point d'attention propre au code s'il existe, codes voisins à ne pas confondre, documents liés (procédure, schéma, règles générales). Ne pas répéter le texte général déjà présent dans DOC-GEN-01.

**Points à vérifier :** libellé français, ordre des causes, point d'attention (ex. P0304 incohérent sur 1.0 TCe à 3 cylindres).

## P-03 — Fiches voyants (14 documents DOC-VOY-Vxx)

**Demandes de l'équipe :**
- « pour les voyants il faut des images »

**Consigne de génération :**
> Pour le voyant {nom}, rédiger une fiche d'une page : pictogramme indicatif, couleur, état (fixe ou clignotant), gravité, motorisations concernées, signification en une phrase, conduite à tenir en une phrase, documents liés.

**Images :** pictogrammes dessinés par script à partir des Material Design Icons (Apache-2.0), couleur rouge ou orange sur fond noir. Représentation indicative, à comparer à la notice du véhicule.

**Points à vérifier :** correspondance pictogramme / voyant réel sur Clio V, Captur II, Sandero III, Duster II ; conduite à tenir.

## P-04 — Procédures de contrôle (8 documents DOC-PROC-0x)

**Demande de l'équipe :** « oui » (ajout de procédures et de schémas)

**Consigne de génération :**
> Pour le thème {thème}, rédiger une procédure d'une page : codes et voyants concernés, motorisations, outillage, objectif, étapes numérotées, tableau observation → piste, consigne de sécurité. Ne donner aucune valeur chiffrée constructeur ; renvoyer aux données du constructeur.

Thèmes : ratés d'allumage, mélange et prises d'air, vanne EGR, filtre à particules, préchauffage, circuit de charge, refroidissement, suralimentation et pression carburant.

**Points à vérifier :** ordre des étapes, consignes de sécurité, absence d'action sur le véhicule réservée au technicien.

## P-05 — Schémas de principe (7 documents DOC-SCH-0x)

**Demandes de l'équipe :** « oui » ; « regler le designe de cette architecture » (règles de mise en page reprises pour les schémas)

**Consigne de génération :**
> Dessiner un schéma de principe simplifié du système {système} : composants en boîtes, flèches dans le sens du flux, codes défaut liés indiqués sous chaque composant ; ajouter une légende de figure avec identifiant ({doc}_fig1) et trois phrases de lecture.

Systèmes : allumage, admission et injection essence, air et EGR diesel, échappement diesel (FAP, SCR), préchauffage, charge, refroidissement.

**Points à vérifier :** exactitude des liaisons ; ne pas présenter le schéma comme un schéma constructeur.

## P-06 — Règles générales (1 document DOC-GEN-01)

**Demande de l'équipe :** « oui » (regrouper le texte commun aux fiches)

**Consigne de génération :**
> Regrouper dans un seul document les règles communes : couleur des voyants, identification d'un voyant sur photo, lecture d'un code défaut, après réparation, sécurité et limites, sources.

---

## Contrôles automatiques déjà effectués
- Aucun renvoi « Documents liés » ne pointe vers un document absent.
- Texte répété entre documents ramené de 46 % à 12 % des lignes (restent les titres de section).
- Chaque document tient sur une page et porte en pied de page son identifiant et sa version.
