# Outils TAA v1.2.0 — Plans de vente V1

Outils TAA réunit désormais **Export**, **Calculs des pièces** et **Plans de vente**
pour **Autodesk Revit 2025.4 / pyRevit 5.x sur Windows**.

## Nouveau : Plans de vente

- Génération automatique depuis une feuille modèle Revit, avec filtrage des logements par paramètre.
- Logements mono-niveau, duplex et villas multi-niveaux : une feuille par niveau avec un modèle à une vue, ou deux niveaux sur une même feuille avec un modèle à deux vues.
- Zones de placement dessinées sur la feuille modèle, choix du style de ligne, échelle commune et placement des vues sans superposition.
- Création des vues logement avec crop, étiquettes, cotations, repérage et nomenclatures du modèle.
- Duplication de la mise en page et renseignement des paramètres logement, bâtiment, étage et typologie.
- Surfaces habitables et annexes consolidées pour les logements multi-niveaux.
- Aperçu réel de la feuille modèle, rapport détaillé et progression par étapes réellement terminées.

## Export et Calculs des pièces

**Export** conserve la publication PDF/DWG, l’arborescence de dossiers, la sélection
multiple et le nommage indépendant PDF/DWG de v1.1.0.

**Calculs des pièces** conserve le regroupement, les sommes, les filtres et
l’écriture contrôlée des résultats. La résolution interactive des divergences
entre occurrences de groupes reste hors périmètre.

Le code métier de ces deux modules est inchangé. Seules leurs icônes PNG ont été
harmonisées avec la palette de Plans de vente.

## Validation

- **259 tests Plans de vente, 323 tests Export et 79 tests Calculs réussis**, ainsi que le contrat ruban Export.
- Recette finale dans Revit 2025.4 confirmée par l’utilisateur le 16 octobre 2026 : ouverture, mono-niveau, multi-niveaux, lot, progression, Export, Calculs et nouvelles icônes.
- La publication vérifie les contrôles GitHub Actions du commit exact de `main` et le contenu du ZIP.
- Intégration par la **PR #26**, depuis la branche propre `release/plans-de-vente-v1`.

## Installation / mise à jour

1. Fermer Revit.
2. Télécharger et lancer **INSTALLER_Outils_TAA_v1.2.0.cmd**.
3. Relancer Revit ou utiliser Reload dans pyRevit.

Aucun droit administrateur n’est requis. L’installation conserve le fonctionnement
existant : dossier `%APPDATA%\pyRevit\Extensions\OutilsTAA.extension`, sauvegarde
de l’installation précédente et migration de l’ancien emplacement si nécessaire.

Le ZIP utilisateur **Outils-TAA_v1.2.0.zip** contient les trois modules, leurs
ressources, les trois tutoriels, la licence et le fichier LISEZ_MOI.
Les tutoriels et les sommes SHA-256 sont également joints séparément. Aucun MSI.

## Limites de cette V1

- Pas de mise à jour automatique des plans déjà générés.
- Au maximum deux vues principales sur une même feuille.
- Optimisations complémentaires des très grands lots à poursuivre.
- Contrôler les crops, cotations, étiquettes et avertissements du rapport pour les géométries particulières.

Le passage de v1.1.0 à **v1.2.0** correspond à l’ajout compatible d’un module,
sans changement cassant annoncé.
