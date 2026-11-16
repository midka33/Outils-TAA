# Outils TAA v1.4.1 — Stabilisation Export et Plans de vente

**Version stable — 5 novembre 2026** · Revit 2025.4 / pyRevit 5.x / Windows.

Cette version contient les correctifs fusionnés depuis v1.4.0, validés dans Revit par l'utilisateur.

## Export
- PR #43 : saisie du nommage DWG en PDF combiné (BUG-EXPORT-060).
- PR #48 : réinitialisation de la sélection après ajout et rafraîchissement des noms/numéros des feuilles Revit (BUG-EXPORT-061/062).
- PR #51 : bouton **Effacer la sélection** au-dessus d'Ajouter. La sélection cumulée entre filtres est conservée ; l'effacement agit également sur les feuilles masquées (BUG-EXPORT-063). Validé dans Revit par l'utilisateur.

## Plans de vente
- PR #44 : quatre listes sélectionnables dans Options avancées.
- PR #45 : persistance locale des options par projet, y compris les quatre choix Revit.
- PR #47 : diagnostic lisible de feuilles modèles incomplètes, sans erreur Python.

## Installation
Télécharger `INSTALLER_Outils_TAA_v1.4.1.cmd`, fermer Revit et exécuter l'installateur. Aucun droit administrateur requis. Le script vérifie le SHA-256 de l'archive et conserve une sauvegarde de l'installation antérieure.

## Hors périmètre
Configuration collaborative (PR #30 encore Draft), réglages individuels par mise en page, autres branches non fusionnées.

Cette version sera publiée uniquement après succès du workflow de validation sur le commit exact de `main`.
