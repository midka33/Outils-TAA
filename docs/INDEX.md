# Index de la documentation Outils TAA

**Version courante : Outils TAA v1.4.0**  
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
- `11_BUGS_Prevention_Registry.md` — point d’entrée du registre des bugs.
- `bugs/INDEX.md` — index des registres modulaires (Export, Calculs, Plans de vente, Commun, Tests).

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
- `archive/releases/v1.3.0/Preparation_Plans_de_Vente_V1.1_Liens.md` — recette historique de la V1.1 liée.
- `release/Tutoriel_Plans_de_Vente_v1.4.0.md` — tutoriel utilisateur courant (comportement métier V1.1 inchangé).

La spécification de développement détaillée des étapes 01 à 09 est archivée dans
`archive/plans-de-vente/20_Plans_de_Vente_Historique_Stages_01_09.md`.

## Giration des véhicules (planifié)

**Spécification de référence :** `25_Giration_Vehicules.md` — module de tracé manuel type Vehicle Tracking, bibliothèque de véhicules sourcés, calcul d'enveloppes et rendu exploitable dans Revit.

**État :** cadrage fonctionnel validé ; développement non démarré ; faisabilité de l'interaction dynamique sous pyRevit à tester en priorité. [Suivi GitHub #40](https://github.com/midka33/Outils-TAA/issues/40).

## Release courante

**Outils TAA v1.4.0 — Export** : explorateur de mises en page, publications PDF/DWG multi-dossiers et options de sortie séparées. La recette **EXPORT-01 à EXPORT-06** est validée par l'utilisateur dans Revit 2025.4 ; voir la [PR #39](https://github.com/midka33/Outils-TAA/pull/39).

Le dossier `release/` contient uniquement les documents de cette version :

- [`Notes_v1.4.0.md`](release/Notes_v1.4.0.md) — nouveautés, compatibilité, installation et limites ;
- [`Preparation_Export_v1.4.0.md`](release/Preparation_Export_v1.4.0.md) — matrice de tests, CI et décisions de release ;
- [`Tutoriel_Export_v1.4.0.md`](release/Tutoriel_Export_v1.4.0.md) — guide utilisateur actuel ;
- [`Tutoriel_Calculs_Pieces_v1.4.0.md`](release/Tutoriel_Calculs_Pieces_v1.4.0.md) — guide utilisateur, module inchangé ;
- [`Tutoriel_Plans_de_Vente_v1.4.0.md`](release/Tutoriel_Plans_de_Vente_v1.4.0.md) — guide utilisateur, module V1.1 inchangé.

Les documents de la précédente release v1.3.0 sont archivés sous `archive/releases/v1.3.0/`. Ceux de v1.2.0 et des versions antérieures restent dans leurs archives respectives.

**Release publiée et vérifiée le 3 novembre 2026 :** [Outils TAA v1.4.0 sur GitHub](https://github.com/midka33/Outils-TAA/releases/tag/v1.4.0), tag `v1.4.0` pointant sur le SHA `21336b3d`, avec six actifs et 754 tests automatisés réussis dans la CI de publication. La recette d'installation Windows du CMD reste à confirmer.

## Archives

`docs/archive/` contient les anciennes spécifications de branches, recettes,
audits et tutoriels de versions précédentes.

**Règle :** ne jamais déduire le comportement courant d'un fichier d'archive
sans le confronter à la documentation de référence ci-dessus et au code actuel.
