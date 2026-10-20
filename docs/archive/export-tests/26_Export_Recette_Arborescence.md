# Export — recette arborescence à dossiers uniques

**Cible :** Revit 2025.4 / pyRevit 5.x  
**Branche de référence :** `main`

**Statut :** PR #22 et #23 fusionnées ; validation utilisateur Revit 2025.4
confirmée le 13 octobre 2026. Les scénarios ci-dessous restent la recette de
non-régression ; cette confirmation ne constitue pas un procès-verbal détaillé
de chaque point de la checklist.

## Préparation

Fermer Revit puis, dans le dépôt utilisé par pyRevit :

```bash
git fetch origin
git switch main
git pull --ff-only origin main
```

Redémarrer Revit 2025.4 ou faire Reload pyRevit.

Utiliser un projet contenant plusieurs mises en page et, si possible, une ancienne
arborescence Export déjà créée avec la v1.0.3.

## TEST-TREE-01 — Vocabulaire

Ouvrir Export.

### Attendu

Dans l'interface principale et dans la fenêtre d'ajout :

- l'utilisateur voit **Dossier** et **Mise en page** ;
- aucun concept « Carnet » n'est nécessaire pour comprendre l'organisation ;
- les anciens carnets apparaissent avec une icône dossier.

## TEST-TREE-02 — Migration d'un projet existant

Ouvrir un projet contenant déjà dossiers et carnets v1.0.3.

### Attendu

- aucune donnée perdue ;
- même contenu de publication ;
- réglages PDF/DWG conservés ;
- ordre initial cohérent avec l'ancien affichage ;
- aucune intervention manuelle sur le JSON.

## TEST-TREE-03 — Nouveau dossier dans le dossier actif

Sélectionner un dossier existant puis cliquer **Nouveau dossier**.

### Attendu

Le nouveau dossier est créé à l'intérieur du dossier actif et devient sélectionné /
visible dans l'arborescence.

Un dossier contenant déjà des mises en page peut également recevoir le nouveau
sous-dossier ; les deux types internes ont la même capacité d'imbrication.

## TEST-TREE-04 — Double-clic

Double-cliquer successivement sur :

- un dossier d'organisation ;
- un dossier contenant des mises en page.

### Attendu

Chaque double-clic ouvre/ferme directement le nœud dans le TreeView. Aucune fenêtre
secondaire « contenu du carnet » ne doit apparaître.

## TEST-TREE-05 — Seuil de drag

Cliquer plusieurs fois sur des lignes sans déplacer réellement la souris.

### Attendu

Aucun drag accidentel.

Puis déplacer volontairement la souris de quelques pixels au-delà du seuil système.

### Attendu

Le drag démarre normalement.

## TEST-TREE-06 — Avant / après / dedans

Déplacer un dossier :

- sur le haut d'une ligne ;
- sur le bas d'une ligne ;
- au centre d'un vrai dossier d'organisation.

### Attendu

- trait orange supérieur = insertion avant ;
- trait orange inférieur = insertion après ;
- surbrillance du dossier = déplacement dedans.

Après dépôt, l'ordre affiché est immédiatement le nouvel ordre enregistré.

## TEST-TREE-06B — Déposer dans un ancien dossier de publication

Choisir un dossier qui contient déjà des mises en page, par exemple
`A1000 Plan de niveaux`.

Glisser un autre dossier sur le **milieu** de sa ligne.

### Attendu

- la grande zone centrale (environ 70 % de la hauteur) affiche la surbrillance
  complète « dedans » ;
- le dossier devient réellement enfant de `A1000 Plan de niveaux` ;
- `A1000 Plan de niveaux` conserve ses propres mises en page ;
- le nouveau sous-dossier apparaît en développant A1000 ;
- fermeture/réouverture d'Export : la hiérarchie persiste ;
- sélectionner A1000 pour publication inclut aussi le contenu publiable du
  sous-dossier ;
- les réglages du sous-dossier peuvent hériter d'A1000.

Vérifier aussi que viser très près du bord supérieur/inférieur continue à produire
avant/après, mais que ces zones restent nettement plus petites.

## TEST-TREE-06C — Même dépôt dossier fermé et ouvert

Prendre un dossier A et un dossier B.

1. Fermer B puis déposer A au milieu de B.
2. Revenir à l'état initial.
3. Ouvrir B, laisser ses enfants visibles, puis déposer A exactement au même endroit
   sur la ligne de B.

### Attendu

Les deux opérations doivent produire exactement le même résultat :

- la ligne de B est surlignée comme cible « dedans » ;
- A devient enfant de B ;
- les enfants visibles de B ne modifient pas la zone 15/70/15 ;
- viser les 15 % supérieurs/inférieurs de la ligne de B continue à donner
  avant/après.

## TEST-TREE-07 — Ordre mixte

Dans un même dossier parent, disposer :

```text
📁 A1000 Plans
📁 Références
📁 A2000 Coupes
```

où A1000/A2000 contiennent des mises en page et Références est un dossier
d'organisation.

Réordonner pour obtenir plusieurs combinaisons.

### Attendu

Les trois dossiers peuvent être intercalés librement ; l'interface ne force plus les
dossiers d'organisation avant les dossiers contenant des feuilles.

Fermer puis rouvrir Export : l'ordre doit persister.

## TEST-TREE-08 — Déplacer une mise en page entre dossiers

Prendre une mise en page de A1000 Plans et la déposer :

- au centre de A2000 Coupes ;
- avant une mise en page précise de A2000 ;
- après une mise en page précise.

### Attendu

La mise en page disparaît du dossier source, apparaît au bon endroit dans le dossier
cible et reste sélectionnée après le dépôt.

Fermer/réouvrir Export : le déplacement doit persister.

## TEST-TREE-09 — Sélection multiple

Avec Ctrl, sélectionner plusieurs dossiers puis les déplacer en bloc.

Faire de même avec plusieurs mises en page.

### Attendu

- l'ordre relatif visible des éléments sélectionnés est conservé ;
- le déplacement se fait en bloc ;
- la sélection reste visible après dépôt.

## TEST-TREE-10 — Auto-ouverture

Pendant un drag, rester environ 700 ms au centre d'un dossier fermé.

### Attendu

Le dossier s'ouvre automatiquement sans relâcher la souris.

## TEST-TREE-11 — Auto-scroll

Créer une arborescence plus haute que la zone visible.

Pendant un drag :

- approcher le pointeur du bord supérieur ;
- approcher le pointeur du bord inférieur.

### Attendu

L'arborescence défile dans la direction correspondante sans lâcher l'élément.

## TEST-TREE-12 — Conserver le contexte

Développer plusieurs dossiers, descendre dans l'arbre, sélectionner plusieurs
éléments puis effectuer un déplacement.

### Attendu

Après dépôt :

- les dossiers précédemment ouverts restent ouverts ;
- le scroll reste proche de la même position ;
- les éléments déplacés restent sélectionnés ;
- le panneau droit affiche un contexte cohérent.

## TEST-TREE-13 — Publication inchangée

Après plusieurs réorganisations, publier :

- un dossier contenant des mises en page ;
- un dossier parent récursif ;
- une sélection de mises en page.

### Attendu

Les PDF/DWG, règles de nommage, progression, dossiers de sortie et rapport restent
fonctionnellement identiques à la v1.0.3 hors changement volontaire d’organisation
et nouvelles options de nommage PDF/DWG de la PR #23 décrites dans `09_Export.md`.

## Fiche de validation

Modèle pour une prochaine exécution détaillée. La validation fonctionnelle globale
des PR #22 et #23 a été confirmée par l’utilisateur ; aucun relevé individuel
TREE-01 à TREE-13 n’a été fourni pour remplir cette grille rétrospectivement.

| Test | Résultat |
|---|---|
| TREE-01 | À tester |
| TREE-02 | À tester |
| TREE-03 | À tester |
| TREE-04 | À tester |
| TREE-05 | À tester |
| TREE-06 | À tester |
| TREE-07 | À tester |
| TREE-08 | À tester |
| TREE-09 | À tester |
| TREE-10 | À tester |
| TREE-11 | À tester |
| TREE-12 | À tester |
| TREE-13 | À tester |

Les PR #22 et #23 sont déjà fusionnées. Conserver cette recette pour les futures
régressions d’arborescence dans Revit 2025.4.
