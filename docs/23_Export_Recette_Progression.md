# Export — recette de progression Revit 2025.4

**Statut : à exécuter par l'utilisateur avant fusion.**
Branche : `feature/export-progress-ui`. Aucun de ces essais réels n'a été exécuté
dans l'environnement de développement hors Revit.

## Préparer le test

1. Fermer Export et Revit. Utiliser une copie de maquette et un dossier de sortie
   de test. Conserver une publication de référence depuis `main` avec les mêmes
   réglages, pour comparer noms, destinations, contenu et ordre des pages.
2. Dans le dossier local **Outils-TAA utilisé par pyRevit**, ouvrir Git Bash :

```bash
git status
git fetch origin
git switch feature/export-progress-ui
git pull --ff-only origin feature/export-progress-ui
```

`git switch` crée la branche locale depuis la branche distante si elle n'existe
pas encore et que le nom n'est pas ambigu. Ne pas écraser de modifications locales
signalées par `git status`.

3. Redémarrer Revit **2025.4**, puis **Outils TAA > Export**. Choisir un carnet
   suffisamment volumineux pour observer la fenêtre. Confirmer l'aperçu.
4. Noter le résultat de chaque test ci-dessous, le commit (`git rev-parse --short HEAD`),
   la version pyRevit 5.x, le nombre de feuilles et l'échelle d'affichage Windows.
   En cas d'échec, copier le diagnostic du rapport ou le traceback pyRevit.

## Contrôles communs

- Avant confirmation : aucune progression, aucun fichier créé ; annuler l'aperçu
  doit conserver cet état.
- Après confirmation : fenêtre au premier plan, départ 0 %, valeur globale
  monotone et bornée, nom du carnet, opération et compteur « unités » lisibles.
- Pendant le natif : « Export PDF Revit », pourcentage fixe possible. Aucun faux
  compteur de feuilles, temps restant ou assemblage annoncé.
- Fin normale : 100 %, fermeture de la progression, puis **rapport existant**.
  100 % indique des unités traitées, pas une garantie de succès ; lire les erreurs.
- Le bouton de publication et les réglages ne doivent pas permettre une seconde
  exécution pendant la première. La croix/Alt+F4 de la progression ne doit pas
  interrompre l'export ni fermer prématurément son interface.
- Après fermeture : Export redevient utilisable. Aucun changement des sélections,
  réglages persistants, destinations, noms, ordre de pages ou règles d'historique.

## Scénarios

| Test | Manipulation | Résultat attendu |
|---|---|---|
| TEST-PROGRESS-01 | Publier 1 carnet PDF combiné avec plusieurs feuilles. | Un PDF identique à la référence ; progression par opérations (4 unités sans DWG), valeur fixe pendant le natif, aucun faux nom de feuille. |
| TEST-PROGRESS-02 | Publier le même carnet en PDF séparés avec un nom par feuille. | Un lot natif conservé, puis phase Livraison ; fichiers au bon nom et dans le dossier du carnet ; 5 unités sans DWG. Vérifier aussi la réécriture de PDF déjà présents. |
| TEST-PROGRESS-03 | Sélectionner plusieurs carnets, avec modes et destinations différents ; inclure un carnet PDF + DWG. | Un seul compteur global et dénominateur constant ; changement de carnet sans retour à zéro ; DWG achevés avant 100 % ; un seul rapport global. |
| TEST-PROGRESS-04 | Publier un dossier contenant des carnets et sous-dossiers. | Tous les carnets du périmètre récursif sont traités ; arborescence, réglages hérités et destinations conservés ; progression globale. |
| TEST-PROGRESS-05 | Ctrl : feuilles non contiguës de deux carnets ; Maj : plage ; puis une feuille seule. Examiner l'aperçu avant chaque publication. | Périmètre réellement exporté identique à l'aperçu ; aucune feuille supplémentaire ; ordre métier et comportement combiné/séparé inchangés. |
| TEST-PROGRESS-06 | Provoquer une erreur de destination dans le dossier de test (ex. droit d'écriture retiré après l'aperçu par un collègue habilité, ou PDF de test verrouillé exclusivement). | Diagnostic utile dans le rapport ; aucune fenêtre résiduelle ; absence d'historique de succès pour le carnet en échec ; autres carnets traités si l'erreur est récupérable. Les erreurs déjà bloquées dans l'aperçu ne doivent pas lancer la progression. |
| TEST-PROGRESS-07 | Rejouer un succès, un échec récupérable, puis annuler un aperçu. Vérifier fermeture, focus et possibilité de republier. Tester un nom de carnet long à 100/150 % Windows. | Rapport seulement après fermeture, pas de fenêtre bloquée, champs lisibles sans chevauchement ; aucune fenêtre en cas d'annulation de l'aperçu. |
| TEST-PROGRESS-08 | Faire 3 publications successives, fermer Export, Reload pyRevit, rouvrir Export et publier à nouveau. Lancer aussi un export PDF natif Revit hors Outils TAA. | Pas de crash, doublon de fenêtre, callback parasite ou changement de l'export natif. Aucun abonnement Revit n'est ajouté par cette implémentation. |

Le chemin d'exception **fatale** (historique indisponible, échec d'ouverture de
fenêtre) est couvert par simulation hors Revit. S'il se produit en recette,
vérifier « Publication interrompue », fermeture/restauration et conservation du
traceback, sans 100 % forcé. Ne pas détériorer l'historique réel pour créer ce cas.

## Relevé de recette

| Test | Résultat / observations / capture |
|---|---|
| TEST-PROGRESS-01 | À exécuter |
| TEST-PROGRESS-02 | À exécuter |
| TEST-PROGRESS-03 | À exécuter |
| TEST-PROGRESS-04 | À exécuter |
| TEST-PROGRESS-05 | À exécuter |
| TEST-PROGRESS-06 | À exécuter |
| TEST-PROGRESS-07 | À exécuter |
| TEST-PROGRESS-08 | À exécuter |

## Revenir à main après les essais

Fermer Revit, puis :

```bash
git switch main
git pull --ff-only origin main
```

Redémarrer Revit. La PR reste en brouillon jusqu'à validation ; **ne pas fusionner
ni créer de release** dans le cadre de cette recette.
