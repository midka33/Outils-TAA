# Calculs

Module **Calculs des pièces** pour Revit 2025.4 / pyRevit 5.x.

## Périmètre

Le module part toujours de **toutes les pièces du projet Revit actif**.

Il n'expose pas de choix « Vue active / Toutes les pièces ».

Un filtre métier optionnel par paramètre peut ensuite réduire le jeu de pièces.

## État

La migration depuis l'ancien RoomTools est terminée et validée dans Revit 2025.4 / pyRevit 5.x.

Sont désormais présents :

- moteur de regroupement/somme ;
- collecte projet entière ;
- filtre optionnel ;
- identités et validation des paramètres ;
- unités Revit ;
- écriture contrôlée et transaction ;
- persistance ;
- interface WPF ;
- rapport ;
- bouton pyRevit ;
- tests automatisés.

La CI hors Revit valide actuellement :

```text
71 passed
```

Le module a été **validé dans Revit 2025.4 réel** le 1er octobre 2026.

Voir :

```text
docs/18_Calculs_Pieces_Tests_Revit.md
```

## Diagnostic des baies (V0.1, en développement)

Bouton séparé **Diagnostic des baies** : inventaire en lecture seule des paramètres dimensionnels des fenêtres/portes, possibilité d'inclure les fichiers Revit liés directs chargés et export de quatre CSV (occurrences, synthèse types, alertes, exclusions). **Aucune conformité réglementaire n'est calculée.** La collecte et le filtre préfixe ont été validés dans Revit 2025.4 ; les exclusions par défaut et leurs quatre CSV ont été validés sur un projet hôte (396 conservées, 20 exclues, 0 alerte). Les liens et la mesure en tableau restent à valider. Voir `docs/27_Diagnostic_Baies.md`.


### Règle de mesure candidate (capture 22/10/2026)

Pour les familles `FEN-EXT` / `PORFEN-EXT`, le diagnostic privilégie `Largeur × Hauteur` par rapport aux dimensions brutes (`Hauteur brute` peut inclure le coffre tunnel, `Largeur brute` les tapées). Les paramètres explicitement nommés `Largeur/Hauteur tableau` conservent la priorité. En absence de paire nominale ou en tableau, les dimensions brutes restent visibles pour analyse mais **ne sont pas comptées automatiquement**. La surface diagnostique est indicative, sans validation réglementaire. Voir `docs/27_Diagnostic_Baies.md`.
