# Index de la documentation Outils TAA

**Version courante : Outils TAA v1.3.0**  
**Cible : Autodesk Revit 2025.4 / pyRevit 5.x**

Ce fichier indique quelles documentations décrivent le comportement **actuel**.
Les documents placés sous `docs/archive/` sont conservés pour la traçabilité
mais ne constituent pas une source de vérité fonctionnelle.

## Socle commun

- `00_Conventions_Nommage.md` — conventions de noms.
- `01_Vision_Philosophie.md` — principes du projet.
- `02_Architecture_Generale.md` — architecture globale.
- `03_Standards_Developpement.md` — standards de développement.
- `04_UI_Guidelines.md` — design system et règles UI.
- `05_Internal_API.md` — contrats internes.
- `06_AI_Development_Guide.md` — règles de développement assisté.
- `07_Git_Workflow.md` — branches, commits, PR et releases.
- `08_Testing.md` — stratégie de test.
- `11_BUGS_Prevention_Registry.md` — registre global des bugs et règles préventives.

## Export

**Référence fonctionnelle principale :** `09_Export.md`

Compléments techniques encore actifs :

- `09_Export_Project_Persistence.md` — identité projet et persistance.
- `18_Export_Charte_UI_V1.md` — charte UI validée.
- `19_Export_UI_Compacte_PDF.md` — interface compacte et PDF.
- `22_Export_Progression.md` — progression.
- `24_Export_Reglages_DWG.md` — réglages et stratégie DWG.
- `15_Export_Stage08_Dynamique.md` — évolution future non raccordée à la publication.

Les anciennes étapes, audits et recettes de campagne sont sous
`archive/export/` et `archive/export-tests/`.

## Calculs des pièces

**Référence fonctionnelle principale :** `10_Calculs_Pieces.md`

- `18_Calculs_Pieces_Tests_Revit.md` — campagne de validation Revit.

## Plans de vente

**Référence fonctionnelle principale :** `20_Plans_de_Vente.md`

- `references/plans-vente/` — références visuelles.
- `release/Preparation_Plans_de_Vente_V1.1_Liens.md` — recette de la V1.1 liée.
- `release/Tutoriel_Plans_de_Vente_v1.3.0.md` — tutoriel utilisateur courant.

La spécification de développement détaillée des étapes 01 à 09 est archivée dans
`archive/plans-de-vente/20_Plans_de_Vente_Historique_Stages_01_09.md`.

## Release courante

Le dossier `release/` ne contient que les documents utiles à la release
courante v1.3.0 :

- `Notes_v1.3.0.md`
- `Tutoriel_Export_v1.3.0.md`
- `Tutoriel_Calculs_Pieces_v1.3.0.md`
- `Tutoriel_Plans_de_Vente_v1.3.0.md`
- `Preparation_Plans_de_Vente_V1.1_Liens.md`

Les documents des anciennes releases sont sous `archive/releases/`.

## Archives

`docs/archive/` contient les anciennes spécifications de branches, recettes,
audits et tutoriels de versions précédentes.

**Règle :** ne jamais déduire le comportement courant d'un fichier d'archive
sans le confronter à la documentation de référence ci-dessus et au code actuel.
