# Export — Étape 07 : Historique et « modifiés uniquement »

**Statut :** Socle technique implémenté — intégration Revit/UI en cours  
**Cible :** Revit 2025.4 / pyRevit 5.x

## 1. Objectif

L'étape 07 prépare le suivi des publications afin de permettre à Export de proposer :

- l'historique de la dernière publication d'un carnet ;
- l'état de chaque mise en page ;
- la publication des seules mises en page nouvelles ou modifiées ;
- un comportement conservatif lorsqu'une modification ne peut pas être déterminée de manière fiable.

Le principe est de ne jamais considérer une mise en page comme « inchangée » lorsque son état ne peut pas être vérifié.

## 2. États métier

Chaque mise en page peut être classée :

| État | Signification |
|---|---|
| `NEW` | aucune publication précédente connue pour cette mise en page |
| `MODIFIED` | le `VersionGuid` courant diffère de celui enregistré lors de la dernière publication réussie |
| `UNCHANGED` | le `VersionGuid` courant correspond à celui enregistré |
| `UNKNOWN` | l'état précédent ou courant ne permet pas une comparaison fiable |

En mode `MODIFIED_ONLY`, les états publiables sont :

```text
NEW + MODIFIED + UNKNOWN
```

`UNCHANGED` est exclu.

## 3. Source de comparaison Revit

Lorsque l'environnement Revit le permet, Export utilise `Element.VersionGuid` comme indicateur de version de la mise en page.

L'outil doit récupérer ce GUID sur l'élément Revit courant à partir du `UniqueId` persistant du `PublicationItem`.

Un identifiant de feuille, un numéro de feuille ou son nom ne constitue pas à lui seul une preuve fiable de modification du contenu Revit.

## 4. Historique persistant

`PublicationHistoryService` conserve un fichier JSON indépendant de la persistance des carnets.

Pour chaque carnet persistant, l'historique conserve notamment :

```text
set_id
set_name
published_at
items
output_paths
```

Pour chaque mise en page :

```text
item_key
version_guid
sheet_number
sheet_name
```

L'historique n'est mis à jour qu'après une publication considérée comme réussie.

## 5. Première publication

Si aucun historique n'existe pour un carnet, toutes ses mises en page sont considérées comme `NEW`.

Ainsi, activer `MODIFIED_ONLY` sur un carnet jamais publié ne doit pas produire une publication vide.

## 6. État inconnu

Si le `VersionGuid` n'est pas disponible au moment de la comparaison, la mise en page est classée `UNKNOWN`.

En mode `MODIFIED_ONLY`, `UNKNOWN` est volontairement republiée :

> mieux vaut republier une mise en page potentiellement inchangée que supprimer silencieusement une mise en page réellement modifiée.

## 7. Réglage `modified_only`

`PublicationSettings` possède désormais le champ :

```text
modified_only
```

Il est :

- persistant ;
- héritable comme les autres réglages de publication ;
- `False` par défaut ;
- résolu par `SettingsResolver`.

La valeur par défaut garantit qu'aucun comportement existant n'est modifié tant que l'option n'est pas exposée et activée dans l'interface.

## 8. Intégration prévue

Le socle technique doit ensuite être branché dans le workflow existant :

```text
Carnet
  ↓
Résolution des réglages
  ↓
Résolution des feuilles Revit
  ↓
Lecture de VersionGuid
  ↓
Comparaison avec historique
  ↓
Filtrage MODIFIED_ONLY
  ↓
Prévisualisation
  ↓
Confirmation
  ↓
Publication
  ↓
Enregistrement de l'état publié
```

Pour une publication de dossier, la comparaison doit être réalisée indépendamment pour chaque carnet.

## 9. Règles de sécurité

1. Une première publication doit publier toutes les mises en page.
2. Une mise en page `UNKNOWN` doit être conservativement republiée.
3. Une publication échouée ne doit pas écraser l'historique précédent comme si elle avait réussi.
4. Une suppression d'une mise en page du carnet ne doit pas être interprétée comme une modification d'une autre mise en page.
5. Le `UniqueId` reste la référence persistante de la mise en page ; l'`ElementId` courant est résolu au moment du contrôle.
6. Le mode `MODIFIED_ONLY` ne doit jamais contourner les validations et contrôles de la prévisualisation.

## 10. Tests hors Revit déjà préparés

`tests/test_publication_history_service.py` couvre :

- première publication ;
- classification d'une mise en page modifiée ;
- classification `UNKNOWN` ;
- sélection conservative en `MODIFIED_ONLY` ;
- désactivation de `MODIFIED_ONLY` ;
- persistance et rechargement de l'historique.

## 11. Tests Revit à réaliser

La validation finale nécessite Revit 2025.4 et doit notamment vérifier :

1. lancer Export sur un carnet jamais publié ;
2. publier le carnet ;
3. activer `MODIFIED_ONLY` ;
4. vérifier qu'une seconde publication sans modification ne republie aucune mise en page ;
5. modifier une feuille dans Revit ;
6. vérifier que seule cette feuille est proposée ;
7. créer une nouvelle mise en page dans un carnet dynamique ou manuel ;
8. vérifier qu'elle est considérée comme `NEW` ;
9. supprimer ou rendre introuvable une référence et vérifier le comportement `UNKNOWN`/manquant ;
10. vérifier qu'une publication échouée ne met pas à jour l'historique comme une réussite ;
11. répéter les contrôles avec PDF séparé, PDF combiné, DWG séparé et DWG combiné lorsque applicable ;
12. vérifier le comportement sur une publication de dossier avec plusieurs carnets.

## 12. État actuel

Le service de comparaison et la persistance de l'historique sont en place. L'interface et le moteur de publication doivent encore être raccordés à ce socle avant de considérer l'étape 07 comme terminée.
