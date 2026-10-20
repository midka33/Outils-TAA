# Export — Correctifs de la campagne de tests 01 à 30 — 2026-09-17

**Projet :** Outils TAA  
**Module :** Export  
**Cible :** Revit 2025.4 / pyRevit 5.x

## Correctifs issus des tests réels

### BUG-EXPORT-020 — Fermeture de l'arborescence après rafraîchissement

**Symptôme :** après ajout d'un carnet ou d'une mise en page, le dossier et/ou le carnet précédemment développé se refermait.

**Cause :** `_refresh_tree()` reconstruisait entièrement le `TreeView` après chaque opération sans restaurer l'état `IsExpanded` des nœuds.

**Correction :** la couche d'intégration mémorise les dossiers et carnets développés avant le rafraîchissement puis restaure leur état après reconstruction.

**Test de non-régression :** TEST-04 — ajouter un carnet puis plusieurs mises en page en conservant les parents développés.

### BUG-EXPORT-021 — Sélection d'un profil appelant un handler inexistant

**Symptôme :** l'utilisation du contrôle Profil provoquait une erreur/crash de l'application. Le code appelait `self.Profile_SelectionChanged(...)`, alors que cette méthode n'existait pas dans `ExportWindow`.

**Cause :** le handler XAML `ProfileChanged` avait été injecté comme couche de compatibilité, mais son implémentation appelait un ancien nom de handler qui n'était plus présent après refactorisation.

**Correction :** implémentation directe de `ProfileChanged`, ajout des handlers `SaveProfile_Click`, `DeleteProfile_Click` et `SettingsChanged`, application persistante du profil au carnet et gestion explicite des profils intégrés/personnalisés.

**Test de non-régression :** TEST-14 et TEST-44 — sélectionner un profil, appliquer un profil, enregistrer puis supprimer un profil personnalisé sans exception WPF/IronPython.

### BUG-EXPORT-022 — PDF séparé exécuté comme une succession de PDF combinés

**Symptôme :** le mode PDF séparé d'un carnet provoquait un crash de Revit pendant la publication.

**Cause :** l'ancien orchestrateur parcourait les feuilles une par une et appelait `Document.Export` avec `Combine=True` pour chaque feuille. Cela ne correspondait pas au mode PDF séparé demandé par l'utilisateur et multipliait les appels au moteur PDF natif.

**Correction :** le mode séparé utilise maintenant `PDFExportOptions.Combine=False` et transmet toutes les feuilles du périmètre dans un seul appel natif `Document.Export`. Autodesk indique que `Combine=False` est précisément le mode prévu pour créer un PDF par vue/feuille ; les noms sont alors générés par la règle de nommage PDF de Revit.

**Test de non-régression :** TEST-14 — publier un carnet de plusieurs feuilles en PDF séparé et vérifier qu'un PDF est produit par feuille sans crash de Revit.

## Commits

- `5ad3588` — correction profils + conservation de l'arborescence ouverte
- `eb7fd91` — stabilisation du PDF séparé par export natif groupé

## Validation

Ces correctifs sont présents dans `main`, mais ils doivent être rejoués dans Revit 2025.4 avant de considérer TEST-04 et TEST-14 comme définitivement validés.
