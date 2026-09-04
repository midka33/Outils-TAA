# Export — Étape 08 : Dynamique avancé

**Statut :** Architecture isolée préparatoire — non connectée au workflow de publication  
**Cible :** Revit 2025.4 / pyRevit 5.x

## 1. Objectif

L'Étape 08 prépare le passage des carnets à contenu fixe vers des carnets dont le contenu peut être **résolu dynamiquement** à partir de règles.

Cette première implémentation est volontairement isolée :

- elle ne modifie pas `PublicationService` ;
- elle ne modifie pas `PublicationBatchService` ;
- elle ne modifie pas le workflow WPF ;
- elle ne déclenche aucun export PDF/DWG ;
- elle ne remplace pas le mécanisme Stage 07 ;
- elle est testable hors Revit.

## 2. Principe architectural

La résolution dynamique reste distincte de la publication.

```text
Définition du carnet dynamique
        ↓
DynamicRuleResolver
        ↓
DynamicResolution
        ├── candidats inclus
        ├── exclusions
        └── diagnostics
        ↓
Comparaison avec la résolution précédente
        ├── ADDED
        ├── REMOVED
        ├── REINCLUDED
        └── UNCHANGED / EXCLUDED
        ↓
Future étape : conversion en PublicationItem
        ↓
Stage 07 : historique / MODIFIED_ONLY
        ↓
Publication PDF / DWG existante
```

Le résolveur ne connaît pas Revit. La couche Revit future transformera les éléments Revit en propriétés normalisées et résoudra les `UniqueId`.

## 3. Modèle de règle

### 3.1 `DynamicRule`

Une règle atomique contient :

```text
field
operator
value
label
```

Opérateurs préparés :

```text
equals
not_equals
contains
not_contains
starts_with
ends_with
in
not_in
exists
not_exists
```

### 3.2 `DynamicRuleGroup`

Un groupe combine plusieurs règles ou groupes avec :

```text
all = toutes les conditions doivent être vraies
any = au moins une condition doit être vraie
```

Les groupes peuvent être imbriqués. Cela prépare les règles complexes sans les mélanger au moteur de publication.

### 3.3 `DynamicRuleDefinition`

La définition complète d'un carnet dynamique contient :

```text
schema_version
name
root
exclusions
```

La version de schéma permet de faire évoluer la persistance sans ambiguïté.

## 4. Données d'entrée normalisées

Le résolveur travaille sur des éléments abstraits :

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

Ce format n'est pas une représentation persistante finale de Revit. Il constitue le contrat minimal du moteur de règles.

Lors du raccordement à Revit, les propriétés disponibles devront être déterminées à partir de l'API réellement accessible dans Revit 2025.4.

## 5. Résolution

`DynamicRuleResolver.resolve()` produit un `DynamicResolution`.

Chaque candidat porte :

```text
key
included
excluded
reasons
```

La résolution conserve l'ordre de la collection d'entrée. Aucun tri automatique par numéro ou nom n'est introduit par le moteur de règles.

### 5.1 Priorité de l'exclusion

Une exclusion explicite est prioritaire sur une règle qui aurait sélectionné l'élément.

```text
Règle → inclut A-201
Exclusion → A-201

Résultat → exclu
```

Une exclusion qui ne correspond plus à aucun élément courant produit un diagnostic `EXCLUSION_NOT_FOUND`.

## 6. Comparaison des résolutions

`DynamicResolution.compare(previous)` compare le **périmètre résultant** de deux résolutions.

La comparaison ne considère pas les éléments qui restent hors périmètre dans les deux résolutions. Elle se concentre sur les évolutions utiles à la publication dynamique.

### États préparés

| État | Signification |
|---|---|
| `ADDED` | élément absent du périmètre précédent et maintenant inclus |
| `REMOVED` | élément inclus précédemment et qui n'est plus inclus |
| `REINCLUDED` | élément précédemment exclu et maintenant inclus |
| `UNCHANGED` | élément inclus dans les deux résolutions |
| `EXCLUDED` | élément explicitement exclu dans la résolution courante |

Exemple :

```text
Précédent : A-101, A-102
Courant   : A-101, A-103

A-101 → UNCHANGED
A-102 → REMOVED
A-103 → ADDED
```

Un `REMOVED` est une évolution du **périmètre dynamique**, pas une demande d'export. Il ne doit jamais être transmis au moteur PDF/DWG comme élément à publier.

Un `REINCLUDED` signifie qu'un élément qui était explicitement exclu revient dans le périmètre. Lors de son raccordement à Stage 07, il devra être traité comme un candidat à classifier par l'historique, sans inventer un état de publication.

## 7. Diagnostics

Les diagnostics sont séparés du résultat métier.

Format préparé :

```text
severity
code
message
key (optionnelle)
```

Exemples :

```text
WARNING / MISSING_KEY
WARNING / EXCLUSION_NOT_FOUND
```

Cette séparation permettra à la future prévisualisation de distinguer :

- ce qui sera publié ;
- ce qui est explicitement exclu ;
- ce qui a quitté le périmètre ;
- ce qui nécessite l'attention de l'utilisateur.

## 8. Interaction future avec Stage 07

Stage 08 ne remplace pas Stage 07.

Le principe cible est :

```text
Source dynamique
      ↓
Résolution du contenu actuel
      ↓
Comparaison avec la résolution précédente
      ↓
Liste actuelle de PublicationItem
      ↓
Classification historique
      ↓
MODIFIED_ONLY
      ↓
Prévisualisation
      ↓
Publication existante
```

Ainsi, un carnet dynamique reste soumis aux mêmes règles de sécurité que les carnets manuels : `NEW`, `MODIFIED`, `UNCHANGED`, `UNKNOWN` et historique par `UniqueId`.

## 9. Ordre et déterminisme

Le résolveur conserve l'ordre de la collection d'entrée. En revanche, la comparaison retourne les changements dans un ordre déterministe basé sur la clé stable afin que les tests, diagnostics et futures prévisualisations soient reproductibles.

L'ordre final de publication d'un carnet dynamique devra être décidé explicitement lors du raccordement : il ne faut pas laisser le moteur de règles imposer accidentellement un ordre différent de l'ordre métier TAA.

## 10. Prévisualisation future

La future prévisualisation Stage 08 devra pouvoir présenter :

```text
✓ Inclus par la règle
✓ Inclus après combinaison de règles
⊘ Exclusion explicite
+ Nouveau dans le carnet dynamique
− Retiré du carnet dynamique
↻ Réintégré
⚠ Diagnostic
```

Elle devra également afficher les règles ayant conduit à la sélection lorsque cela est utile au diagnostic.

Aucune interface n'est ajoutée dans cette étape isolée.

## 11. Persistance future

`DynamicRuleDefinition.to_dict()` fournit déjà une représentation versionnée.

Le raccordement à `PublicationSource.rule_definition` devra respecter les règles existantes :

- ne jamais transformer silencieusement un carnet dynamique en carnet manuel ;
- conserver le mode de source ;
- conserver la définition complète ;
- prévoir une migration explicite si le schéma évolue.

La résolution précédente ne doit pas être confondue avec la définition de la règle. Elle constitue un **snapshot d'exécution** utile à la détection des évolutions du périmètre.

## 12. Tests hors Revit

`tests/test_dynamic_rule_resolver.py` vérifie notamment :

1. règle `equals` ;
2. combinaison `all` ;
3. combinaison `any` ;
4. exclusion explicite prioritaire ;
5. exclusion devenue orpheline ;
6. propriété absente ;
7. recherche `contains` insensible à la casse ;
8. détection d'un élément ajouté ;
9. détection d'un élément retiré ;
10. détection d'un élément réintégré après exclusion.

Ces tests sont indépendants de Revit et ne constituent pas une validation de l'API Revit.

## 13. Limites de cette étape

Cette étape **ne fournit pas encore** :

- interface de création de règles ;
- lecture de paramètres Revit ;
- persistance d'un carnet dynamique dans le repository existant ;
- conversion automatique vers `PublicationItem` ;
- persistance des snapshots de résolution ;
- intégration à la prévisualisation ;
- intégration à PDF/DWG ;
- intégration au bouton Publier.

Ces éléments seront traités après validation Stage 07 et validation de cette architecture.

## 14. Critère de sortie de l'architecture isolée

L'architecture sera considérée prête à être raccordée lorsque :

- le contrat des règles est stabilisé ;
- les tests hors Revit passent ;
- la résolution reste sans dépendance Revit/WPF ;
- les exclusions sont déterministes ;
- la comparaison des snapshots est déterministe ;
- les diagnostics sont exploitables par une future UI ;
- le raccordement futur à Stage 07 ne nécessite pas de second moteur PDF/DWG.
