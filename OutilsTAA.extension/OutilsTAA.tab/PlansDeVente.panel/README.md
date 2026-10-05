# Plans de vente

Module Outils TAA pour Revit 2025.4 / pyRevit 5.x.

## État actuel — Étape 04 validée : nomenclatures et repérage

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

Le détourage est validé pour la V1 dans Revit 2025.4, avec une limite connue sur certaines gaines palières. La validation finale de l'Étape 03 porte désormais sur les groupes de vues principales par échelle.


### Correctif crop Revit

Le crop Revit exige une boucle composée uniquement de segments droits. Le contour issu de l'union est désormais tessellé puis reconstruit en lignes, avant et après l'offset de marge.

En cas de fallback, l'interface indique maintenant l'étape géométrique exacte en échec.


### Contour local et marge 2D

Après linéarisation, les petites poches sont raccordées par colinéarité,
Trim/Extend ou projection perpendiculaire entre supports parallèles décalés.
La géométrie utilise uniquement les pièces ; aucun type de mur n'est demandé.
La contenance complète et la simplicité sont contrôlées avant toute fermeture.

La marge utilise CreateViaOffset, puis une tentative de nettoyage local sûr.
Aucun buffer booléen 3D de marge n'est conservé. Si la marge échoue, le rectangle
de secours reste explicite. Les compteurs détaillent les trois types de raccord.
Voir `docs/20_Plans_de_Vente.md`, A.3.20, pour seuils et test manuel A003.

### Groupes de vues principales par échelle

La vue source n'est jamais modifiée. Le module crée ou réutilise une vue
principale technique `PDV MASTER` pour chaque combinaison source / niveau /
échelle, puis crée les vues logement comme dépendantes de ce master.

L'échelle est explicite en V1 ; aucun ajustement automatique à la feuille n'est
encore effectué.

L'Étape 03 a été validée dans Revit 2025.4 le 5 octobre 2026 : masters 1:50 / 1:100, réutilisation, dépendances et préservation de la vue source sont conformes.

Prochaine étape : **Étape 04 — Nomenclatures et repérage**.


### Dette connue : validation finale du crop selon la marge

L'Étape 03 reste validée V1, mais un cas Revit a confirmé que certaines marges
peuvent produire un contour optimisé rejeté par `IsCropRegionShapeValid`.
Le fallback final sera consolidé ultérieurement (BUG-PDV-023). Ce point ne
bloque pas le démarrage de l'Étape 04.


### Étape 04

Ordre retenu :

1. duplication et filtrage des nomenclatures modèles intérieure / extérieure ;
2. création du plan de repérage ;
3. préparation des rôles et ancrages pour l'assemblage feuille.

Les nomenclatures modèles conservent la logique métier intérieur / extérieur ;
le plugin ajoute uniquement le filtre du logement choisi.


### Prototype 04A — Nomenclatures

Le prototype permet maintenant de choisir deux nomenclatures modèles compatibles avec le paramètre logement, puis de créer une copie intérieure et une copie extérieure filtrées sur le logement sélectionné.

Nommage : `PDV_<logement>_INT` / `PDV_<logement>_EXT`.

Les modèles restent inchangés. Les autres filtres, champs, tris et mises en forme sont conservés par duplication. Prototype 04A validé dans Revit 2025.4 le 5 octobre 2026.

Le paramètre partagé `N° Appartement` est sélectionné par défaut à l'ouverture lorsqu'il est disponible ; sinon le premier paramètre texte reste utilisé.


### Prototype 04B — Plan de repérage

Le module peut maintenant dupliquer une vue plan source en `PDV_<logement>_REP`, conserver sa présentation ou appliquer un gabarit choisi, puis créer **une zone remplie globale** sur l'enveloppe du logement. Cette zone utilise le moteur de contour de l'Étape 03 à marge nulle et passe sur les cloisons intérieures.

La vue source reste inchangée. 04B validé dans Revit 2025.4 le 5 octobre 2026, avec une seule zone remplie globale couvrant aussi les cloisons intérieures.

Le premier essai 04B a révélé des libellés vides pour les types de zones remplies sous IronPython ; correction BUG-PDV-024 validée dans Revit 2025.4 le 5 octobre 2026.


### 04C — Contrat de placement

Les éléments générés portent maintenant un rôle et un ancrage explicites :
`MainView/main_view`, `LocationView/location_view`,
`InteriorSchedule/interior_schedule` et
`ExteriorSchedule/exterior_schedule`.

Aucune coordonnée de feuille n'est encore appliquée. L'Étape 07 traduira ces
ancrages sémantiques en positions réelles dans le modèle de feuille.


### Étape 04 validée V1

04A Nomenclatures et 04B Plan de repérage ont été validés dans Revit 2025.4.
04C Contrat de placement est validé par tests purs.

Le module dispose désormais des artefacts nécessaires à l'assemblage futur :
vue logement, vue de repérage, nomenclatures intérieure/extérieure, avec rôles
et ancrages explicites.
