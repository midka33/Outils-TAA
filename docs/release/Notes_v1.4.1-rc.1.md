# Outils TAA v1.4.1-rc.1 — Version de validation (5 novembre 2026)

**Statut : candidat de validation, non publié.** Cible Autodesk Revit 2025.4 / pyRevit 5.x.

Cette version candidate regroupe les modifications fusionnées dans `main` depuis la release v1.4.0 du 3 novembre 2026. Elle ne contient pas les branches de travail encore ouvertes.

## Correctifs à vérifier

### Export
- **PR #43 — BUG-EXPORT-060 :** saisie libre de la règle « Nommage DWG » en PDF combiné ; validation à la sortie du champ.
- **PR #48 — BUG-EXPORT-061/062 :** remise à zéro de la sélection après ajout ; affichage actualisé des numéros et noms de feuilles existantes après modification dans Revit. Ces deux régressions ont été validées par l'utilisateur dans Revit le 5 novembre 2026.

### Plans de vente
- **PR #44 — BUG-PDV-031 :** quatre listes réellement sélectionnables dans Options avancées (gabarit logement, gabarit repérage, type d'étiquette, type de cote).
- **PR #45 — BUG-PDV-032 :** enregistrement local des Options avancées séparément pour chaque projet, y compris les choix Revit par `UniqueId`.
- **PR #47 — BUG-PDV-033 :** diagnostic compréhensible d'une feuille modèle incomplète en l'absence de repérage, sans erreur Python `NoneType.view`.

### Hors périmètre
- **PR #30** (configuration collaborative serveur) : toujours en Draft, non fusionnée.
- **PR #49** (synchronisation documentaire) : Draft au moment de la préparation, non incluse.
- Réglages individuels de publication par mise en page : non développés dans ce candidat.

## Installation de validation
Utiliser les actifs ZIP / CMD générés par le workflow de release pour **le SHA exact testé**, sans droits administrateur. Ne pas utiliser les actifs de v1.4.0 pour cette recette.

**Important :** cette note n'atteste ni l'exécution des tests de packaging sur cette version, ni une release publiée. Exiger les contrôles CI et l'intégrité SHA-256 des actifs avant toute publication.

## Retour attendu
Reporter le résultat de chacun des tests de `Preparation_v1.4.1-rc.1.md`. En cas d'anomalie, conserver la release stable v1.4.0 et ne pas promouvoir ce candidat.
