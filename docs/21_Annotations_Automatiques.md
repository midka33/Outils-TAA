# Outils TAA — Cotation automatique et Étiquetage automatique

**État : bêta de recette, non validée dans Revit.**
**Compatibilité visée : Revit 2025.4 / pyRevit 5.x.**
**Branche :** `feature/annotations-automatiques-beta`.
Ne pas fusionner dans `main` avant validation d'un projet de test.

## Objet

Deux boutons dans le panneau **Annotations** du ruban Outils TAA :

- **Cotation auto** : cotes natives par pièce (jusqu'à deux orientations principales) ;
- **Étiquetage auto** : étiquettes de pièces natives, avec sélection du type.

Les moteurs `dimension_service.py`, `room_tag_service.py` et la bibliothèque géométrique `lib/plans_vente/` sont importés depuis Plans de vente. Les contrôles spécifiques aux vues `PDV PROTO` sont adaptés uniquement par sous-classes. Aucun service Plan de vente existant n'a été modifié par cette bêta.

## Fonctionnement

1. Lancer le bouton voulu dans **Outils TAA → Annotations**.
2. Si des vues en plan ont été sélectionnées dans le navigateur Revit, elles sont reprises. Sinon, sélectionner une ou plusieurs vues en plan dans la liste.
3. Choisir un type de cote ou d'étiquette **chargé dans le document hôte**.
4. Pour les cotes, choisir le style des **petites lignes 2D de référence** ; le style est lu parmi les styles de lignes du document. Les lignes mesurent au maximum 5 mm.
5. Confirmer l'opération ; consulter le rapport pyRevit.

Les deux fonctions limitent les collisions selon leurs estimations géométriques. En l'absence d'une position satisfaisante, l'annotation doit être omise et l'échec signalé (aucune position chevauchante volontaire).

### Pièces hors groupe

Annotations normales dans la vue, sans groupe de détails.

### Pièces dans un groupe de modèle

Le service cherche un groupe de détails attaché TAA existant correspondant au bouton, et l'affiche sur l'occurrence si possible.

À défaut, il prépare des annotations pour les pièces de cette occurrence, puis **tente** un rattachement natif via l'API Revit. Il annule le traitement complet du groupe si Revit refuse l'opération ou si l'intégrité du groupe de modèle ne peut être garantie.

Pour les cotes utilisant un élément extérieur au groupe, une petite ligne de détail 2D est placée sur la limite de pièce et sert de référence à la cote. La ligne est volontairement **non associative avec le mur de façade**. La correction d'une façade déplacée relève de l'utilisateur. Aucune vérification des écarts géométriques entre occurrences n'est prévue.

Les lignes de référence candidates sont limitées aux principales directions retenues par le moteur ; les références de longueur issues de murs hors groupe sont exclues.

**Point de validation prioritaire :** l'API de création d'un groupe de détails attaché à un groupe de modèle *déjà existant* doit être testée dans Revit 2025.4. Les validations statiques ne démontrent pas ce comportement. En cas de refus, le module annule l'ensemble pour ce groupe et indique le motif.

## Périmètre / limites bêta

- Plans d'étage uniquement, et pièces du document actif visibles dans ces plans.
- Pas de pièces issues des fichiers Revit liés dans cette première recette, même si Plans de vente les prend en charge.
- Types de cotes linéaires et types d'étiquettes de pièces chargés dans le document hôte.
- Pas de déplacement des annotations manuelles existantes.
- Les cotes existantes proches d'une pièce entraînent une exclusion prudente de cette pièce plutôt qu'une nouvelle cotation.
- Les bounding boxes Revit et l'estimation des lignes de cote peuvent être conservatrices.
- Le placement des détails réutilisés entre occurrences n'est pas réoptimisé : aucun contrôle de géométrie inter-occurrences, conformément à la décision métier.
- Pas de test réel Revit 2025.4 à ce stade ; ne pas déclarer les groupes validés.

## Recette Revit à réaliser (sur copie de maquette)

- [ ] REV-ANN-01 : les deux boutons sont présents et ouvrent leur sélection.
- [ ] REV-ANN-02 : sélectionner deux vues et choisir des types distincts ; vérifier les créations.
- [ ] REV-ANN-03 : lancer Étiquetage puis Cotation ; aucun chevauchement.
- [ ] REV-ANN-04 : lancer Cotation puis Étiquetage ; aucun chevauchement.
- [ ] REV-ANN-05 : relancer chaque module ; aucune annotation doublée.
- [ ] REV-ANN-06 : pièce seule, sans groupe, vue en plan ordinaire.
- [ ] REV-ANN-07 : pièce dans un groupe, murs référencés dans le groupe, groupe de détails réellement attaché.
- [ ] REV-ANN-08 : mur de façade hors groupe ; petite ligne 2D du style choisi, cote associative à la ligne.
- [ ] REV-ANN-09 : autre occurrence du groupe, réutilisation du type de groupe de détails.
- [ ] REV-ANN-10 : erreur API groupement, annulation atomique, aucune annotation/lignes 2D isolées.
- [ ] REV-ANN-11 : vues sans pièces / gabarits / liens ; sortie explicite sans crash.
- [ ] REV-ANN-12 : non-régression Plans de vente V1.1 sur projet témoin.

## Architecture

```text
OutilsTAA.extension/
  OutilsTAA.tab/
    Annotations.panel/
      Cotation.pushbutton/
      Etiquetage.pushbutton/
      services/
        launcher.py
        annotations_service.py
    PlansDeVente.panel/
      services/ dimension_service.py, room_tag_service.py (inchangés)
  lib/plans_vente/ (inchangé)
```

Les nouveaux adaptateurs sont le premier pas vers un moteur de référence
commun ; l'extraction définitive dans une bibliothèque d'annotation autonome
est reportée après validation de cette bêta dans Revit.


## Correctif après retour du 22 octobre 2026

Les captures utilisateur montrent 40 pièces au niveau 0 et 44 au niveau 1,
mais aucune cote ni étiquette créée, avec le message `(Name)`.
Le premier adaptateur lisait directement `room.Name`, connu pour lever
`AttributeError: Name` sous IronPython.

Correctifs : paramètres `ROOM_NAME` / `ROOM_NUMBER`, noms d'éléments
via `Element.Name.GetValue`, validation de niveau fiable, traceback complet
dans le rapport, isolation des pièces non groupées pour éviter un rollback
global de tout l'étage.

**État :** tests de régression hors Revit préparés ; corrections à revalider
sur les mêmes deux vues. Le rattachement des groupes attachés reste un point
de recette séparé.

## Correctif de cotation — essai du 22 octobre 2026

**Résultat de recette :** Étiquetage auto a créé 40 étiquettes au niveau 0. Cotation auto a créé 0 cote sur les 40 pièces du niveau 0 et 44 du niveau 1, avec `Aucune position de cote sans collision` pour chaque pièce.

**Racine :** dans l'adaptateur de la bêta, un conflit détecté pour l'une des deux cotations entraînait le rejet complet du calcul par pièce, alors que Plans de vente conserve historiquement les deux cotes avec avertissement. Le nouveau module doit garantir l'absence de collision sans supprimer toute cotation réalisable.

**Comportement corrigé :** calcul des positions candidates via `plans_vente.dimension_positioning.placement_candidates`, sélection d'une ou deux cotes avec `annotations.strict_dimension_positioning.select_collision_free_placements`. Les cotes conflictuelles sont ignorées individuellement et expliquées dans le rapport ; les cotes restantes sont conservées. Le moteur Plans de vente reste identique.

**Contrôles pour la prochaine recette :**

- [ ] REV-ANN-13 : relancer la cotation après les 40 étiquettes du niveau 0 ; au moins certaines pièces doivent être cotées, sans chevauchement.
- [ ] REV-ANN-14 : relancer sur le niveau 1 ; vérifier qu'une cote peut être créée même si la seconde ne trouve pas de place.
- [ ] REV-ANN-15 : pièces 1123 et 2213 : comparer visuellement les deux directions et le rapport par orientation.
- [ ] REV-ANN-16 : vérifier qu'une seconde exécution ne duplique pas les cotes.

**Statut :** code et tests hors Revit ; validation visuelle et API Revit 2025.4 à effectuer.
