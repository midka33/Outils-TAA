# Export — Checklist de tests Revit 2025.4

**Projet :** Outils TAA  
**Module :** Export  
**Étape :** 07 — Historique et `MODIFIED_ONLY`  
**Environnement cible :** Revit 2025.4 / pyRevit 5.x  
**Date prévue :** lundi

> Ce fichier contient la campagne complète de validation Revit. Les tests 01 à 53 couvrent les fonctions déjà développées ; les tests 54 à 56 ciblent les derniers points ajoutés à l'intégration Stage 07.

## Tests complémentaires Stage 07

## TEST-54 — Héritage de MODIFIED_ONLY dossier → carnet

Activer `MODIFIED_ONLY` au niveau d'un dossier, puis sélectionner plusieurs carnets de ce dossier sans définir de surcharge locale.

**Attendu :** tous les carnets héritent de la valeur du dossier. Désactiver ensuite le réglage au niveau d'un seul carnet.

**Attendu complémentaire :** seul ce carnet devient localement désactivé ; les autres restent hérités.

## TEST-55 — Historique indépendant entre projets Revit

Publier un carnet dans un premier projet, puis ouvrir un autre projet contenant un carnet portant le même nom.

**Attendu :** le second projet ne réutilise pas à tort l'historique du premier. Les feuilles du second projet sont considérées comme `NEW` lors de leur première publication.

## TEST-56 — Contenu réel d'un PDF/DWG combiné filtré

Après avoir publié un carnet, modifier une seule feuille et activer `MODIFIED_ONLY`. Utiliser successivement PDF combiné et DWG combiné.

**Attendu :** le livrable combiné ne contient que le périmètre sélectionné pour cette publication ; aucune feuille `UNCHANGED` ne doit être exportée dans le nouveau livrable.

---

## Rappel de campagne

Pour chaque test, noter `OK`, `KO` ou `NON TESTÉ`. En cas de `KO`, copier l'erreur IronPython complète et, si possible, joindre une capture d'écran. Ne pas modifier le code entre deux tests : les corrections seront faites après analyse afin de préserver la reproductibilité.

## Tableau des nouveaux résultats

```text
TEST-54 :
TEST-55 :
TEST-56 :
```
