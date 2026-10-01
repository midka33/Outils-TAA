# Plans de vente

Module Outils TAA pour Revit 2025.4 / pyRevit 5.x.

## État actuel — Prototype contour optimisé

Le premier incrément est volontairement en lecture seule :

- collecte de toutes les pièces du document actif ;
- découverte des paramètres texte des pièces ;
- choix du paramètre identifiant le logement ;
- regroupement des pièces par valeur ;
- affichage des logements détectés, du nombre de pièces et des niveaux ;
- signalement des pièces sans valeur.

Aucune vue, cote, nomenclature ou feuille n'est créée à cette étape.

Référence fonctionnelle : `docs/20_Plans_de_Vente.md`.


## Prototype géométrique en cours

Après validation de la détection et des vues dépendantes, le prototype construit maintenant le crop à partir de l'union géométrique des pièces du logement :

- frontières de pièces au centre des séparations ;
- union de solides temporaires Revit ;
- extraction de la boucle extérieure ;
- marge par offset du contour ;
- fallback rectangulaire explicite si Revit refuse une géométrie.

Validation réelle dans Revit 2025.4 requise avant de généraliser ce moteur.


### Correctif crop Revit

Le crop Revit exige une boucle composée uniquement de segments droits. Le contour issu de l'union est désormais tessellé puis reconstruit en lignes, avant et après l'offset de marge.

En cas de fallback, l'interface indique maintenant l'étape géométrique exacte en échec.
