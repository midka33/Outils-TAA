# Export — Étape 07 : Historique et « modifiés uniquement »

**Statut :** Intégration technique réalisée — validation Revit 2025.4 restante  
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

L'outil récupère ce GUID sur l'élément Revit courant à partir du `UniqueId` persistant du `PublicationItem`.

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

En mode `MODIFIED_ONLY`, l'enregistrement fusionne les états publiés avec l'historique existant afin de ne pas perdre les états des mises en page volontairement non publiées parce qu'elles sont inchangées.

## 5. Première publication

Si aucun historique n'existe pour un carnet, toutes ses mises en page sont considérées comme `NEW`.

Ainsi, activer `MODIFIED_ONLY` sur un carnet jamais publié ne produit pas une publication vide.

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

L'interface Export expose une case :

**« Publier uniquement les mises en page nouvelles ou modifiées »**

Lorsque la case est active :

- `NEW` est publié ;
- `MODIFIED` est publié ;
- `UNKNOWN` est publié par sécurité ;
- `UNCHANGED` est exclu.

Le réglage est mémorisé au niveau dossier ou carnet selon le niveau sélectionné, conformément au mécanisme d'héritage existant.

## 8. Intégration du workflow

Le flux complet est maintenant raccordé au workflow existant :

```text
Carnet / Dossier
  ↓
Résolution des réglages
  ↓
Lecture de VersionGuid Revit
  ↓
Comparaison avec historique
  ↓
Filtrage MODIFIED_ONLY
  ↓
Prévisualisation
  ↓
Confirmation
  ↓
Publication avec le moteur PDF/DWG existant
  ↓
Enregistrement de l'état après réussite
  ↓
Rapport
```

Pour une publication de dossier, la comparaison et le filtrage sont réalisés indépendamment pour chaque carnet.

La publication n'utilise pas de second moteur PDF/DWG : le périmètre est filtré avant de transmettre le carnet au moteur existant.

## 9. Prévisualisation

La prévisualisation reçoit les informations de classification et affiche l'état sur chaque ligne lorsque le mode `MODIFIED_ONLY` est actif.

Le résumé rappelle les quantités :

```text
NEW
MODIFIED
UNCHANGED
UNKNOWN
```

Si aucun candidat n'est disponible, la prévisualisation bloque la confirmation et aucun PDF/DWG vide n'est proposé.

Les contrôles existants restent actifs : destination, mise en page introuvable, doublons, imprimabilité, collisions de noms et variables inconnues.

## 10. Publication et historique

L'historique est enregistré uniquement après une publication réussie.

Pour une publication multiple, chaque carnet est traité indépendamment : la réussite d'un carnet peut donc être capitalisée même si un autre carnet échoue.

Une publication échouée ne doit jamais être considérée comme une nouvelle référence historique.

Lorsqu'une publication ne concerne qu'une mise en page, l'état publié est fusionné avec l'historique du carnet parent afin de préserver les autres entrées.

## 11. Règles de sécurité

1. Une première publication doit publier toutes les mises en page.
2. Une mise en page `UNKNOWN` doit être conservativement republiée.
3. Une publication échouée ne doit pas écraser l'historique précédent comme si elle avait réussi.
4. Une suppression d'une mise en page du carnet ne doit pas être interprétée comme une modification d'une autre mise en page.
5. Le `UniqueId` reste la référence persistante de la mise en page ; l'`ElementId` courant est résolu au moment du contrôle.
6. Le mode `MODIFIED_ONLY` ne doit jamais contourner les validations et contrôles de la prévisualisation.
7. Un carnet sans candidat en `MODIFIED_ONLY` ne doit pas générer de fichier vide.
8. L'historique doit être conservé par carnet, même lors d'une publication multiple.

## 12. Tests hors Revit déjà préparés

`tests/test_publication_history_service.py` couvre :

- première publication ;
- classification d'une mise en page modifiée ;
- classification `UNKNOWN` ;
- sélection conservative en `MODIFIED_ONLY` ;
- désactivation de `MODIFIED_ONLY` ;
- persistance et rechargement de l'historique.

Des tests supplémentaires sont attendus pour vérifier la fusion de l'historique lorsqu'une publication partielle ne concerne qu'une partie des mises en page.

## 13. Tests Revit à réaliser

La validation finale nécessite Revit 2025.4 et doit notamment vérifier :

1. lancer Export sur un carnet jamais publié ;
2. publier le carnet ;
3. activer `MODIFIED_ONLY` ;
4. vérifier qu'une seconde publication sans modification ne republie aucune mise en page et bloque la confirmation ;
5. modifier une feuille dans Revit ;
6. vérifier que seule cette feuille est proposée ;
7. créer une nouvelle mise en page dans un carnet dynamique ou manuel ;
8. vérifier qu'elle est considérée comme `NEW` ;
9. vérifier le cas `UNKNOWN` lorsque `VersionGuid` ne peut pas être exploité ;
10. vérifier qu'une publication échouée ne met pas à jour l'historique comme une réussite ;
11. répéter les contrôles avec PDF séparé, PDF combiné, DWG séparé et DWG combiné lorsque applicable ;
12. vérifier le comportement sur une publication de dossier avec plusieurs carnets ;
13. vérifier qu'un carnet réussi reste historisé même si un autre carnet du lot échoue ;
14. publier une seule mise en page puis vérifier que les autres états du carnet sont conservés.

## 14. État actuel

Le socle de persistance, la classification, le contrôle d'interface, le filtrage de prévisualisation, le filtrage avant publication et l'enregistrement post-publication sont raccordés.

**La validation fonctionnelle réelle dans Revit 2025.4 reste obligatoire avant de cocher l'étape 07 comme entièrement validée.**
