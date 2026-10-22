# Outils TAA — Plans de vente

**Version fonctionnelle :** V1.1  
**Livraison :** Outils TAA v1.3.0  
**Statut :** validé dans Autodesk Revit 2025.4 / pyRevit 5.x  
**Date de référence :** 20 octobre 2026

Cette page décrit le **comportement courant** du module. L'historique détaillé des
étapes 01 à 09 est conservé dans
`docs/archive/plans-de-vente/20_Plans_de_Vente_Historique_Stages_01_09.md`.

## 1. Objet

Plans de vente automatise la création de feuilles de plans de vente à partir des
pièces Revit d'un logement.

Le module travaille depuis le document hôte, typiquement `SITE.rvt`, qui
contient les feuilles, cartouches, vues modèles et nomenclatures. Les pièces
peuvent provenir :

- du document actif ;
- de liens Revit **directs et chargés** lorsque l'option
  **Inclure les pièces des fichiers Revit liés** est cochée.

Les éléments générés restent dans le document hôte.

## 2. Identification des logements

L'utilisateur choisit un paramètre texte porté par les pièces pour identifier les
logements.

Exemple :

```text
Séjour        → A18
Cuisine       → A18
Chambre       → A18
```

Les pièces partageant la même valeur et la même source forment un logement.

L'identité interne d'un logement lié comprend la source / instance du lien et le
numéro logement. Deux bâtiments peuvent donc contenir chacun `A18` sans être
fusionnés.

### Nommage visible

L'identité technique du lien n'apparaît pas dans les noms Revit.

Un logement unique reste :

```text
A18
PDV-A18
Plan de vente - A18
```

Si plusieurs sources contiennent réellement le même numéro logement, le module
demande à l'utilisateur un libellé lisible de différenciation, par exemple
`BAT A` et `BAT B`.

Aucun suffixe automatique de type `-L5530419` n'est utilisé.

## 3. Feuille modèle

La feuille modèle est située dans le document hôte et définit la présentation à
reproduire.

Elle peut contenir :

- le cartouche ;
- une ou deux vues principales de type plan d'étage ;
- un plan de repérage ;
- des nomenclatures ;
- des légendes ;
- des rectangles / zones de placement ;
- les annotations hôtes servant de référence pour les types d'étiquette et de cote.

Seules les vues `FloorPlan` participent à la détection des vues logement et du
repérage. Une vue `Legend` est reconnue comme légende et ne compte jamais comme
une vue logement supplémentaire.

Les légendes placées sur le modèle sont replacées sur chaque feuille générée en
réutilisant la **même vue Legend**. La vue de légende n'est pas dupliquée.

## 4. Sources Revit liées

`SourceRoom` conserve pour chaque pièce liée :

- le document source ;
- la pièce source ;
- l'instance de `RevitLinkInstance` ;
- une identité durable ;
- la transformation `GetTotalTransform()` vers le document hôte.

La géométrie numérique est transformée vers SITE avant d'être transmise aux
moteurs de cadrage et de repérage.

Les liens déchargés sont ignorés avec avertissement.

Les liens imbriqués ne sont pas parcourus dans la V1.1.

Les liens dont la transformation renverse ou incline l'axe vertical sont hors
périmètre et sont signalés.

## 5. Niveaux SITE

Une vue Revit créée dans SITE doit appartenir à un niveau du document SITE.

Pour un logement lié, Plans de vente rapproche le niveau source de SITE à partir
de son altitude projet transformée, avec une tolérance de 1 mm.

Règle :

1. un niveau SITE unique existe à cette altitude → il est réutilisé ;
2. aucun niveau n'existe → création automatique d'un niveau
   `PDV_AUTO_±XX.XXX` ;
3. aucune vue plan source exploitable n'existe sur ce niveau → création d'une
   vue plan technique SITE ;
4. plusieurs niveaux SITE existent à la même altitude → arrêt avec erreur
   d'ambiguïté, sans choix arbitraire.

Plusieurs logements situés à la même altitude partagent le même niveau SITE.

## 6. Vues logement et cadrage

Les vues logement sont créées dans SITE à partir d'une vue source / vue
principale technique compatible avec le niveau et l'échelle demandée.

Le moteur conserve le principe de vues principales techniques et de vues
dépendantes afin de permettre un cadrage indépendant par logement sans modifier
la vue métier choisie comme référence.

Le crop est construit à partir des contours des pièces du logement. Pour une
pièce liée, les points sont transformés dans le repère SITE avant calcul.

Les options de marge et les règles de cadrage restent celles définies dans
l'interface Plans de vente.

## 7. Étiquettes de pièces

Pour une pièce du document actif, le module crée une étiquette de pièce native.

Pour une pièce liée, il utilise un `LinkElementId` basé sur l'instance du lien
et l'id de la pièce source.

Le moteur évite de considérer deux pièces issues de liens différents comme la
même pièce.

### Pré-requis V1.1

Le **type d'étiquette** utilisé est déterminé à partir d'une étiquette appartenant
au document hôte / vue modèle.

Une étiquette seulement visible parce que la vue affiche un lien Revit appartient
au document lié et ne fournit pas le type hôte.

Le type attendu doit donc être disponible et représenté dans SITE.

## 8. Cotations

L'objectif reste de produire jusqu'à deux dimensions principales par pièce,
orientées selon les dimensions intérieures finies pertinentes.

Pour une pièce liée :

- les références sont recherchées dans le document source ;
- les points numériques sont transformés vers SITE ;
- les références Revit sont converties par `CreateLinkReference` ;
- aucune cote graphique fictive n'est créée si l'API refuse une référence.

Les refus sont signalés dans le rapport.

### Pré-requis V1.1

Comme pour les étiquettes, le **type de cote** doit être détectable dans le
document hôte. Une cote visible uniquement dans une vue liée ne suffit pas.

## 9. Nomenclatures

Les nomenclatures de la feuille modèle sont copiées et adaptées au logement.

Pour les logements liés, les nomenclatures de pièces modèles doivent utiliser
l'option Revit native permettant d'inclure les éléments des fichiers liés.

Le module conserve autant que possible :

- champs ;
- filtres métier ;
- regroupements ;
- totaux ;
- unités ;
- présentation.

Il ajoute les critères nécessaires pour isoler le fichier / l'instance source
et le numéro logement.

Une source native ambiguë ou une nomenclature impossible à filtrer bloque le
logement plutôt que de produire un tableau mélangeant plusieurs bâtiments.

## 10. Plan de repérage

Le repérage est généré dans SITE à partir des mêmes pièces et transformations que
la vue logement.

Les coordonnées liées sont donc traitées dans le repère hôte avant calcul de
l'emprise et de la mise en évidence du logement.

## 11. Logements multi-niveaux

Les logements mono-niveau et multi-niveaux sont pris en charge.

Selon la feuille modèle :

| Modèle | Résultat |
|---|---|
| Une vue principale | une feuille par niveau pour un logement multi-niveaux |
| Deux vues principales | jusqu'à deux niveaux sur une même feuille |

Pour un logement lié, l'ordre des niveaux repose sur l'altitude transformée dans
SITE et non sur le texte du nom de niveau.

Les surfaces et informations logement restent consolidées à l'échelle du logement
lorsque les nomenclatures le demandent.

## 12. Cartouche et métadonnées

Les paramètres configurés pour logement, bâtiment, étage, typologie et surfaces
sont renseignés à partir des pièces pertinentes.

Pour une source liée, bâtiment et typologie sont lus dans le document source.
Le numéro métier du logement reste le `filter_key` et n'est pas remplacé par
l'identité technique du lien.

## 13. Progression, transactions et rapport

La création par lot affiche une progression fondée sur des jalons réellement
terminés :

- analyse ;
- vue ;
- étiquettes ;
- cotations ;
- repérage ;
- nomenclatures ;
- feuille ;
- finalisation.

Les erreurs sont contextualisées par logement, source et étape.

Une erreur sur un logement ne doit pas être présentée comme une génération
valide. Les avertissements et éléments ignorés restent visibles dans le rapport.

## 14. Limites de la V1.1

Hors périmètre de la release v1.3.0 :

- liens Revit imbriqués ;
- liens inclinés / renversés verticalement ;
- déduction d'un type d'étiquette ou de cote uniquement depuis une annotation
  appartenant à un fichier lié ;
- mise à jour automatique d'un plan déjà généré ;
- plus de deux vues principales sur une même feuille ;
- automatisation des réglages de phase / visibilité des liens ou des gabarits.

## 15. Architecture de référence

Bibliothèque métier :

```text
OutilsTAA.extension/lib/plans_vente/
```

Services Revit / orchestration :

```text
OutilsTAA.extension/OutilsTAA.tab/PlansDeVente.panel/services/
```

Interface :

```text
OutilsTAA.extension/OutilsTAA.tab/PlansDeVente.panel/ui/
```

Tests hors Revit :

```text
tests/plans_vente/
```

## 16. Références

- Tutoriel courant : `docs/release/Tutoriel_Plans_de_Vente_v1.3.0.md`
- Recette V1.1 : `docs/release/Preparation_Plans_de_Vente_V1.1_Liens.md`
- Références UI : `docs/references/plans-vente/`
- Registre des bugs : `docs/11_BUGS_Prevention_Registry.md`
- Historique détaillé : `docs/archive/plans-de-vente/20_Plans_de_Vente_Historique_Stages_01_09.md`


### Note d'architecture bêta — recherche des arêtes de dalle partagée

Sur la branche `feature/annotations-automatiques-beta` uniquement, le
service de cotation de Plans de vente délègue la **sélection des planchers**
à `lib/common/floor_reference_policy.py`. Son mode par défaut
(`legacy`) et la clé de cache par niveau reproduisent exactement
la sélection d'avant refactorisation : tous les planchers du même niveau,
ou ceux de niveaux proches uniquement lorsqu'aucun plancher du même
niveau n'existe. L'extraction native des arêtes, les critères
d'appariement, la priorité des références, le fallback et la
création des cotes sont **inchangés**.

Le module Cotation automatique hérite du même collecteur d'arêtes mais
active une politique distincte `local` : recherche par emprise XY
de la pièce (marge 300 mm), support des planchers de niveaux voisins
déjà filtrés en altitude, six planchers maximum et cache par pièce.

Cette abstraction ne constitue **pas** une nouvelle validation Revit
du moteur commun ; aucun changement du moteur stable de la branche
`main` n'est effectué. Référence : BUG-COMMON-011 et
`tests/annotations/test_floor_reference_policy.py`.
