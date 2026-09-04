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

La branche `stage08-dynamic-architecture` constitue donc un espace de préparation avant raccordement au workflow réel, après validation de Stage 07 dans Revit 2025.4.

## 2. Principe architectural

La résolution dynamique doit rester distincte de la publication.

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
Future étape : conversion en PublicationItem
        ↓
Stage 07 : historique / MODIFIED_ONLY
        ↓
Publication PDF / DWG existante
```

Le résolveur ne connaît pas Revit. La couche Revit future aura pour responsabilité de transformer les éléments Revit en propriétés normalisées et de résoudre les `UniqueId`.

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

## 6. Diagnostics

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
- ce qui nécessite l'attention de l'utilisateur.

## 7. Interaction future avec Stage 07

Stage 08 ne remplace pas Stage 07.

Le principe cible est :

```text
Source dynamique
      ↓
Résolution du contenu actuel
      ↓
Liste de PublicationItem
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

## 8. Éléments ajoutés et retirés

La détection des éléments ajoutés et retirés sera réalisée au niveau de comparaison entre deux résolutions, et non dans le moteur atomique des règles.

À terme :

```text
Résolution précédente       Résolution courante
A-101                       A-101       → inchangé dans le périmètre
A-102                       A-103       → A-102 retiré, A-103 ajouté
A-104                       A-104       → inchangé dans le périmètre
```

Un élément `REMOVED` est un diagnostic d'évolution du carnet dynamique. Il ne doit pas être envoyé au moteur PDF/DWG comme élément à publier.

Cette distinction évite de confondre :

- élément modifié dans Revit ;
- élément nouvellement entré dans le carnet ;
- élément sorti du carnet par évolution de la règle.

## 9. Prévisualisation future

La future prévisualisation Stage 08 devra pouvoir présenter :

```text
✓ Inclus par la règle
✓ Inclus après combinaison de règles
⊘ Exclusion explicite
+ Nouveau dans le carnet dynamique
− Retiré du carnet dynamique
⚠ Diagnostic
```

Elle devra également afficher les règles ayant conduit à la sélection lorsque cela est utile au diagnostic.

Aucune interface n'est ajoutée dans cette étape isolée.

## 10. Persistance future

`DynamicRuleDefinition.to_dict()` fournit déjà une représentation versionnée.

Le raccordement à `PublicationSource.rule_definition` devra respecter les règles existantes :

- ne jamais transformer silencieusement un carnet dynamique en carnet manuel ;
- conserver le mode de source ;
- conserver la définition complète ;
- prévoir une migration explicite si le schéma évolue.

## 11. Tests hors Revit

`tests/test_dynamic_rule_resolver.py` vérifie notamment :

1. règle `equals` ;
2. combinaison `all` ;
3. combinaison `any` ;
4. exclusion explicite prioritaire ;
5. exclusion devenue orpheline ;
6. propriété absente ;
7. recherche `contains` insensible à la casse.

Ces tests sont volontairement indépendants de Revit et ne constituent pas une validation de l'API Revit.

## 12. Limites de cette étape

Cette étape **ne fournit pas encore** :

- interface de création de règles ;
- lecture de paramètres Revit ;
- persistance d'un carnet dynamique dans le repository existant ;
- conversion automatique vers `PublicationItem` ;
- détection réelle des ajouts/retraits entre deux publications ;
- intégration à la prévisualisation ;
- intégration à PDF/DWG ;
- intégration au bouton Publier.

Ces éléments seront traités après validation Stage 07 et validation de cette architecture.

## 13. Critère de sortie de l'architecture isolée

L'architecture sera considérée prête à être raccordée lorsque :

- le contrat des règles est stabilisé ;
- les tests hors Revit passent ;
- la résolution reste sans dépendance Revit/WPF ;
- les exclusions sont déterministes ;
- les diagnostics sont exploitables par une future UI ;
- le raccordement futur à Stage 07 ne nécessite pas de second moteur de publication.
