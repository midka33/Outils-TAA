# Export — Étape 08 : Dynamique avancé

**Statut :** Architecture isolée + prévisualisation + modèle complet + persistance — non connectée au workflow de publication  
**Cible :** Revit 2025.4 / pyRevit 5.x

## Objectif

L'Étape 08 prépare des carnets dont le contenu est résolu dynamiquement à partir de règles. Le résolveur, le modèle métier et la persistance restent indépendants de Revit, WPF et des moteurs PDF/DWG.

Le développement hors Revit comprend maintenant :

- le moteur de règles dynamiques ;
- la comparaison de résolutions ;
- la persistance des snapshots ;
- le pont vers `PublicationItem` ;
- le moteur de prévisualisation ;
- le modèle complet `DynamicPublicationSet` ;
- la sérialisation, migration et validation du modèle ;
- le store persistant par projet ;
- le cycle de vie création / lecture / modification / duplication / suppression.

Aucun de ces composants ne déclenche encore de publication réelle.

## Architecture

```text
DynamicPublicationSet
        ↓
DynamicPublicationSetLifecycle
        ↓
DynamicPublicationSetStore
        ↓
JSON versionné / isolé par projet

DynamicRuleDefinition
        ↓
DynamicRuleResolver
        ↓
DynamicResolution
        ├──→ DynamicPreviewBuilder
        └──→ DynamicPublicationAdapter
                   ↓
             PublicationItem existants
                   ↓
             Future intégration Stage 07
```

Aucun second moteur de publication n'est créé.

## Modèle complet du carnet dynamique

`DynamicPublicationSet` porte la configuration persistante d'un carnet. Il distingue `manual` et `dynamic` et conserve notamment :

- identifiant stable ;
- nom ;
- dossier ;
- source ;
- destination ;
- modèle de nommage ;
- paramètres de publication ;
- définition des règles ;
- exclusions ;
- clé du snapshot.

Le modèle ne contient aucune instance Revit résolue. Les feuilles sont reconstruites depuis le document courant lors de la future résolution.

`DynamicPublicationSetSerializer` assure la sérialisation, désérialisation, validation et migration de schéma. Un schéma futur non supporté est refusé explicitement.

## Persistance complète

`DynamicPublicationSetStore` persiste les configurations dans un JSON versionné :

```text
{
  "schema_version": 1,
  "projects": {
    "project-key": {
      "carnet-id": { ... }
    }
  }
}
```

La clé projet isole les carnets entre projets. La persistance ne contient ni `Document`, ni `Element`, ni `PublicationItem` Revit.

Le store fournit :

- `list(project_key)` ;
- `get(project_key, set_id)` ;
- `save(project_key, set)` ;
- `delete(project_key, set_id)` ;
- `replace_project(project_key, sets)`.

Les écritures utilisent un fichier temporaire avant remplacement du fichier cible. Les fichiers absents ou JSON illisibles sont traités comme un store vide ; un schéma futur est refusé.

## Cycle de vie

`DynamicPublicationSetLifecycle` constitue la façade métier destinée à la future UI :

```text
Création
   ↓
Validation
   ↓
Persistance
   ↓
Chargement
   ↓
Modification
   ↓
Nouvelle validation + persistance
   ↓
Duplication éventuelle
   ↓
Suppression éventuelle
```

Les opérations disponibles sont `create`, `get`, `list`, `update`, `duplicate` et `delete`.

La création refuse un identifiant déjà utilisé. La modification refuse un carnet inexistant. La duplication passe par sérialisation/désérialisation afin d'obtenir une configuration indépendante, notamment pour les règles imbriquées et les exclusions.

## Règles dynamiques

`DynamicRule` prend un `field`, un `operator`, une `value` et un `label`. Les opérateurs disponibles sont `equals`, `not_equals`, `contains`, `not_contains`, `starts_with`, `ends_with`, `in`, `not_in`, `exists` et `not_exists`.

`DynamicRuleGroup` combine les règles avec `all` ou `any` et peut contenir des groupes imbriqués.

`DynamicRuleDefinition` contient `schema_version`, `name`, `root` et `exclusions`.

## Résolution

Les entrées utilisent le contrat abstrait :

```python
{
    "key": "UniqueId-ou-clé-stable",
    "properties": {
        "discipline": "Architecture",
        "sheet_number": "A-201",
        "phase": "PRO"
    }
}
```

Une exclusion explicite est prioritaire sur une règle correspondante. Les exclusions orphelines produisent `EXCLUSION_NOT_FOUND`.

## Prévisualisation et pont publication

`DynamicPreviewBuilder` expose les changements `ADDED`, `REMOVED`, `EXCLUDED`, `REINCLUDED`, `UNCHANGED` et `NOT_MATCHED` sans effet de bord.

`DynamicPublicationAdapter` rapproche les clés dynamiques des `PublicationItem.unique_id`, réutilise les instances existantes, conserve l'ordre et signale les clés absentes ou dupliquées. Il prépare l'utilisation du moteur de publication existant via son paramètre `items`.

## Snapshots

`DynamicResolutionSnapshot` / `DynamicResolutionSnapshotStore` conservent séparément le dernier périmètre résolu par projet et carnet.

Le snapshot dynamique représente le **périmètre** ; l'historique Stage 07 représente l'**état de publication/version**. Les deux ne doivent pas être confondus avec la configuration persistante du carnet.

## Tests hors Revit

Les tests existants couvrent les règles, le pont, la prévisualisation, le modèle et le manager. `tests/test_dynamic_publication_set_store.py` couvre maintenant la persistance et le cycle de vie : roundtrip sur disque, isolation projet, création, mise à jour, duplication indépendante, suppression, fichier corrompu, schéma futur et remplacement d'un projet.

**Ces tests ont été créés mais n'ont pas encore été exécutés dans cet environnement.** Conformément à `AI_INSTRUCTIONS.md` et `docs/08_Testing.md`, ils devront être réellement exécutés au raccordement avant de considérer cette partie validée.

## Limites actuelles

Ne sont pas encore intégrés :

- lecture des paramètres Revit ;
- création de candidats depuis le document Revit ;
- intégration du store dans `CarnetRepository` / workflow existant ;
- interface de création et d'édition des règles ;
- intégration de la prévisualisation dans WPF ;
- raccordement au Stage 07 ;
- bouton `Publier` dynamique ;
- export PDF/DWG depuis une résolution dynamique.

La prochaine étape reste le raccordement progressif, en conservant la stratégie de test : pytest d'abord, puis validation Revit 2025.4 des comportements réellement dépendants de Revit.
