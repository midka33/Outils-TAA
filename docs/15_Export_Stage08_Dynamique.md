# Export — Étape 08 : Dynamique avancé

**Statut :** Architecture isolée + prévisualisation + pont vers `PublicationItem` — non connectée au workflow de publication  
**Cible :** Revit 2025.4 / pyRevit 5.x

## Objectif

L'Étape 08 prépare des carnets dont le contenu est résolu dynamiquement à partir de règles. Le résolveur reste indépendant de Revit, WPF et des moteurs PDF/DWG.

Le développement hors Revit comprend maintenant :

- le moteur de règles dynamiques ;
- la comparaison de résolutions ;
- la persistance des snapshots ;
- le pont vers `PublicationItem` ;
- un moteur de prévisualisation structuré destiné à une future UI.

Aucun de ces composants ne déclenche encore de publication réelle.

## Architecture

```text
DynamicRuleDefinition
        ↓
DynamicRuleResolver
        ↓
DynamicResolution
        ├──→ DynamicPreviewBuilder
        │          ↓
        │    DynamicPreview
        │
        └──→ DynamicPublicationAdapter
                   ↓
             PublicationItem existants
                   ↓
             Future intégration Stage 07
                   ↓
             Publication PDF / DWG existante
```

Aucun second moteur de publication n'est créé.

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

`DynamicResolution.compare(previous)` produit notamment `ADDED`, `REMOVED`, `REINCLUDED`, `UNCHANGED` et `EXCLUDED`. Un `REMOVED` est une évolution de périmètre et ne doit pas être publié.

## Prévisualisation dynamique

`DynamicPreviewBuilder` transforme une `DynamicResolution` courante et, lorsqu'il existe, une résolution précédente en un objet `DynamicPreview` sans effet de bord.

Chaque `DynamicPreviewRow` contient notamment :

- la clé stable ;
- l'état de changement ;
- le statut inclus/exclus ;
- les raisons de résolution.

La prévisualisation expose des collections dédiées pour `ADDED`, `REMOVED`, `EXCLUDED`, `REINCLUDED`, `UNCHANGED` et `NOT_MATCHED` ainsi que `publishable_rows`.

Les éléments `REMOVED` sont conservés dans l'aperçu même lorsqu'ils ne sont plus présents dans la résolution courante. Cela permet à une future interface d'expliquer clairement la disparition d'un élément du carnet dynamique.

Le moteur de prévisualisation ne publie rien, ne modifie pas la résolution et ne dépend ni de Revit ni de WPF.

## Pont vers `PublicationItem`

`DynamicPublicationAdapter.build_selection(resolution, publication_items)` rapproche chaque clé dynamique de `PublicationItem.unique_id`.

Le pont respecte les règles suivantes :

1. seuls les candidats inclus et non exclus sont transmis ;
2. l'ordre de la résolution est conservé ;
3. les instances `PublicationItem` existantes sont réutilisées, sans clonage ;
4. aucune collection ou instance source n'est modifiée ;
5. une clé absente produit `PUBLICATION_ITEM_NOT_FOUND` ;
6. une clé `unique_id` dupliquée produit `DUPLICATE_PUBLICATION_ITEM_KEY`.

Le résultat `DynamicPublicationSelection` contient `items`, `diagnostics` et `valid`. Il est destiné à être consommé ultérieurement par les services existants via leur paramètre `items`.

## Snapshots

`DynamicResolutionSnapshot` / `DynamicResolutionSnapshotStore` conservent séparément le dernier périmètre résolu par projet et carnet.

Le snapshot dynamique représente le **périmètre** ; l'historique Stage 07 représente l'**état de publication/version**. Les deux ne doivent pas être confondus.

## Tests hors Revit

`tests/test_dynamic_rule_resolver.py` couvre le moteur de règles et la comparaison des résolutions.

`tests/test_dynamic_publication_adapter.py` couvre la correspondance vers les `PublicationItem`, l'ordre, la réutilisation des instances, les exclusions, les éléments absents, les doublons et la résolution vide.

`tests/test_dynamic_preview.py` couvre les changements de périmètre, les exclusions, la réintégration, les suppressions, l'ordre, les diagnostics et l'absence de mutation.

Ces tests ne remplacent pas une validation Revit 2025.4.

## Limites actuelles

Ne sont pas encore intégrés :

- modèle complet de carnet dynamique ;
- interface de création de règles ;
- lecture des paramètres Revit ;
- gestionnaire de carnets ;
- persistance complète d'un carnet dynamique ;
- intégration de la prévisualisation dans WPF ;
- Stage 07 ;
- bouton `Publier` ;
- export PDF/DWG depuis une résolution dynamique.

Le prochain développement hors Revit porte sur le **modèle complet de carnet dynamique** : distinction manuel/dynamique, règles, exclusions, paramètres, persistance, versionnement, validation et migration. La validation Revit 2025.4 de Stage 07 reste un préalable au raccordement réel.
