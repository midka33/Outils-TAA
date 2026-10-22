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


## Correctif « deux grandes dimensions » — 22 octobre 2026

**Retour en Revit :** 57 cotes sur `Collectifs A_Niveau 0`, mais des cotes
paralleles et des longueurs de petits troncons de mur a la place des
deux dimensions principales de chaque piece.

**Cause :** les cotes de secours par longueur de mur de Plans de vente
etaient utilisees lorsque les cotes de faces opposees echouaient.
C'est un comportement distinct du besoin des boutons Annotations.

**Regle metier obligatoire pour Cotation automatique :**

1. Identifier les faces finies de la piece en reutilisant le service PDV.
2. Retenir la meilleure paire de faces opposees (mesure interieure).
3. Retenir la seconde plus grande portee entre faces opposees dans une autre direction, sans imposer de perpendicularite.
4. Garder les deux emprises et references d'origine, avec placement adaptatif
   sans collision avec etiquette/cote et sans texte hors piece.
5. Si aucune position fiable n'existe pour un axe, n'ajouter aucune cote
   sur cet axe, et signaler le motif. **Ne jamais basculer vers la
   longueur d'un mur ou d'un autre segment en guise de remplacement.**
6. Creer une seule cote si un seul axe exploitable reste, plutot que
   deux cotes paralleles ou approximatives.

**Perimetre :** modification seulement de l'adaptateur
`GenericDimensions` et du helper pur
`lib/annotations/principal_dimension_axes.py` ; pas de modification
de `dimension_service.py` ou de la geometrie Plans de vente.

**IMPORTANT POUR LES TESTS :** les 57 cotes deja creees par la version
precedente ne sont pas identifiees comme provenant de TAA. Elles doivent
etre supprimees manuellement / annulees **sur une copie du projet** avant
nouveau test. Ne jamais les supprimer automatiquement, pour ne pas
effacer des cotes manuelles existantes. Le module reste prudent en
presence de cotes preexistantes.

- [ ] REV-ANN-17 : apres nettoyage de la copie, une piece rectangulaire
  recoit ses deux plus grandes mesures interieures entre faces opposees (orthogonales seulement si la geometrie l'est).
- [ ] REV-ANN-18 : aucune cote de longueur de mur / petit troncon,
  meme quand la seconde direction ne peut pas etre placee.
- [ ] REV-ANN-19 : une piece avec une seule paire opposable ne recoit
  au maximum qu'une cote.
- [ ] REV-ANN-20 : aucune collision sur les 40 etiquettes deja validees ;
  les pieces complexes produisent un diagnostic plutot qu'une fausse cote.


## Precision metier : les plus grandes cotes et alignement entre pieces

**Decision utilisateur du 22 octobre 2026 (prioritaire sur les anciens prototypes)** :

- Retenir **deux plus grandes distances utiles entre faces finies opposees de chaque piece**, par ordre de portee. Ces deux directions peuvent etre obliques et ne doivent **pas obligatoirement** etre perpendiculaires.
- Reutiliser la geometrie PDV de detection des faces et l'API de cotation native. Aucune longueur isolee de mur en remplacement d'une cote de piece.
- Pour les cotes de meme orientation dans les pieces voisines, rechercher une ligne de cote **colineaire** a une cote existante de la vue ; ne jamais modifier la longueur mesuree ni les references d'origine. Un guide eloigne n'impose aucun alignement.
- Aligner seulement si la nouvelle cote est positionnable dans la piece avec un texte interieur, **sans chevauchement d'etiquettes ni d'autres cotations**. A defaut, utiliser le meilleur placement sans collision, ou omettre cette cote et expliquer pourquoi.
- Si seulement une portee est mesurable sans conflit, ne creer que cette cote. Ne pas forcer de cotations incorrectes pour atteindre deux.

**Implementation beta :** `principal_dimension_axes.py` trie les paires PDV par distance ; `dimension_alignment.py` cherche les rails de meme orientation, peut generer une position exactement colineaire au rail voisin ; `strict_dimension_positioning.py` favorise ces candidats *apres* l'elimination des collisions. `GenericDimensions._alignment_rails` lit les lignes des cotes deja posees dans la vue (y compris les cotes creees sur les pieces precedentes). Le moteur PDV n'est pas modifie.

**Parametres internes beta :** proximite maximale du guide : 25 mm sur papier a l'echelle de la vue ; tolerance de coincidence : 0,25 mm papier ; parallelisme pour le calage exact : 0,05 degre (des cotes seulement approximativement paralleles ne sont pas forcees sur un meme rail). Les nouvelles positions sont colineaires exactement avec le guide, dans les limites de precision numerique. Ces valeurs sont ajustables apres recette Revit.

**Tests Revit a faire sur une copie propre** : piece rectangulaire, piece biaise, deux pieces voisines avec cotes paralleles et guides d'alignement, variante avec etiquette bloquant le guide, et second lancement sans doublons. Retirer *manuellement* les anciennes cotes incorrectes des essais beta avant de tester, sans suppression automatique des cotes utilisateur.
