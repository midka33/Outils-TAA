# Calculs des pièces

**Statut :** Migration en cours — Blocs 1 à 3 implémentés hors Revit  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Module :** `Calculs.panel`

---

## 1. Responsabilité

Le module **Calculs des pièces** regroupe les traitements métier portant sur les pièces Revit : collecte, filtrage métier optionnel, regroupement, agrégation et mise à jour contrôlée de paramètres.

Le nom historique **RoomCalculator** est conservé uniquement lorsqu'il est nécessaire de décrire l'ancien module source.

---

## 2. Décision de périmètre

Le périmètre source est fixe :

> **Calculs des pièces travaille toujours à partir de toutes les pièces du projet Revit actif.**

L'interface ne doit pas proposer de choix entre :

- toutes les pièces ;
- vue active ;
- pièces sélectionnées.

Ces choix ne font pas partie de la cible actuelle.

Un **filtre métier optionnel par paramètre** peut ensuite réduire le jeu de pièces lorsque l'utilisateur le configure explicitement.

Le flux cible est donc :

```text
Toutes les pièces du projet
        ↓
Filtre par paramètre (optionnel)
        ↓
Lecture des valeurs
        ↓
Regroupement
        ↓
Somme
        ↓
Validation
        ↓
Écriture
```

La collecte ne doit pas exclure implicitement une pièce uniquement parce qu'elle n'est pas visible dans la vue active.

La gestion des pièces sans valeur exploitable, non placées ou invalides doit relever d'une règle de validation explicite et traçable, pas d'un changement silencieux de périmètre.

---

## 3. Fonctionnalités à préserver de l'ancien module

La migration doit conserver, après validation technique :

- filtre optionnel par paramètre et valeur ;
- choix du paramètre de regroupement ;
- choix du paramètre numérique à additionner ;
- choix du paramètre de destination ;
- calcul d'une somme par groupe ;
- écriture du résultat dans les pièces du groupe ;
- gestion cohérente des unités ;
- progression et retour utilisateur ;
- mémorisation des choix utiles.

Les contrôles historiques « vue active » et « toutes les pièces » sont volontairement retirés de la cible.

Les options historiques présentes dans l'UI mais non réellement raccordées ne doivent pas être reproduites sans implémentation réelle.

---

## 4. Architecture cible

```text
UI WPF
  ↓
Controller / orchestration
  ↓
Services métier
  ├── modèles normalisés
  ├── filtre métier
  ├── calculateur
  └── validation
  ↓
Adaptateurs Revit
  ├── collecte des pièces
  ├── lecture des paramètres
  ├── unités
  └── écriture
  ↓
API Revit
```

Règles :

- l'UI ne réalise aucun calcul métier ;
- le moteur de calcul ne dépend ni de Revit ni de WPF ;
- les transactions restent hors du moteur de calcul ;
- les lectures et écritures de paramètres sont séparées ;
- `lib/common` est réutilisé pour les comportements réellement transversaux ;
- le module reste indépendant d'Export.

---

## 5. Bloc 1 — moteur métier pur

Le premier bloc migré est placé dans :

```text
OutilsTAA.extension/
└── lib/
    └── calculation/
        ├── __init__.py
        ├── models.py
        └── room_calculator.py
```

### 5.1 Modèle d'entrée

`RoomCalculationItem` contient uniquement les données nécessaires au calcul :

```text
room_key
group_value
source_value
```

Il ne contient aucun objet Revit.

Les futurs adaptateurs Revit doivent transformer les paramètres Revit en ces données normalisées avant d'appeler le moteur.

### 5.2 Calcul

`RoomCalculator` :

- regroupe par `group_value` ;
- additionne les valeurs numériques `source_value` ;
- accepte zéro comme valeur valide ;
- accepte zéro comme clé de groupe valide ;
- ignore explicitement les groupes vides ;
- ignore explicitement les sources non numériques ;
- retourne les pièces ignorées avec une raison ;
- expose une progression indépendante de WPF.

### 5.3 Résultat

`CalculationResult` expose :

- les totaux par groupe ;
- le nombre d'éléments reçus ;
- le nombre d'éléments calculés ;
- les éléments ignorés ;
- le nombre de groupes.

---

## 6. Bloc 2 — collecte, filtre et lecture de paramètres

Le deuxième bloc ajoute :

```text
Calculs.panel/services/
├── room_collector_service.py
└── room_parameter_service.py

lib/calculation/
└── room_filter.py
```

### 6.1 Collecte

`RoomCollectorService.collect_all_rooms()` collecte les éléments de la catégorie des pièces dans le document entier.

Règles implémentées :

- aucun filtre de vue ;
- aucun recours à `ActiveView` ;
- aucune exclusion implicite basée sur `Area == 0` ;
- la collecte renvoie le jeu complet des pièces, la validation intervenant ensuite.

Ce comportement traduit directement la décision utilisateur de toujours partir de toutes les pièces du projet.

### 6.2 Filtre métier optionnel

`RoomFilter` applique éventuellement un filtre par paramètre et valeur.

Sans paramètre ou sans valeur de filtre, toutes les pièces collectées sont conservées.

Le filtre est indépendant du périmètre de collecte.

### 6.3 Lecture des paramètres

`RoomParameterService` fournit actuellement :

- découverte des noms de paramètres ;
- possibilité de limiter la liste aux paramètres numériques ;
- lecture `String` ;
- lecture `Integer` ;
- lecture `Double` ;
- lecture `ElementId` ;
- détection explicite de l'état lecture seule.

Cette première implémentation reste à compléter par l'identité stable des paramètres et leur type de donnée Revit avant raccordement final de l'UI et de la persistance.

---

## 7. Bloc 3 — identité, validation et unités

Le troisième bloc fiabilise les paramètres avant toute écriture dans Revit.

### 7.1 Descripteur de paramètre

Le modèle `calculation.parameter_descriptor.RoomParameterDescriptor` conserve :

```text
nom affiché
identité technique
StorageType
DataType Revit
unité Revit
état writable
```

L'identité est choisie dans cet ordre :

1. GUID pour un paramètre partagé ;
2. identifiant ForgeTypeId pour un paramètre Revit intégré ;
3. identifiant de définition Revit ;
4. nom uniquement en dernier recours.

Deux paramètres portant le même nom mais ayant deux identités différentes ne sont donc plus fusionnés silencieusement.

Lorsqu'un simple nom est le seul identifiant disponible et que plusieurs paramètres portent ce nom, la résolution est considérée ambiguë et doit être bloquée.

### 7.2 Agrégation de l'état d'écriture

Pour une destination présente sur plusieurs pièces, l'état `writable` est agrégé sur toutes les occurrences observées.

Si une seule occurrence du même paramètre est en lecture seule, le descripteur agrégé n'est pas considéré comme une destination sûre dans un filtre `writable_only`.

### 7.3 Type de donnée Revit

Le service lit le type de donnée de la définition via l'API Revit moderne et le conserve sous forme d'identifiant sérialisable.

Pour deux paramètres `Double`, une différence connue de type de donnée est bloquante avant écriture.

Exemple :

```text
Surface → Surface = compatible
Surface → Volume  = incompatible
```

### 7.4 Validation de la destination

`RoomParameterValidator` vérifie actuellement :

- source numérique ;
- destination prise en charge ;
- destination non readonly ;
- compatibilité des types de donnée pour une écriture `Double → Double` ;
- avertissement pour `Double → Integer` ;
- avertissement pour une destination texte ;
- rejet d'une destination `ElementId`.

Ces règles sont préparatoires au futur `RoomWriter`.

### 7.5 Unités

Le nouveau module commun :

```text
lib/common/unit_utils.py
```

centralise :

- conversion depuis les unités internes Revit ;
- conversion vers les unités internes Revit ;
- comparaison des types de donnée normalisés.

Principe retenu :

> les valeurs `Double` utilisées par le moteur de calcul restent en unités internes Revit.

Les conversions ne doivent intervenir que lorsqu'une entrée ou un affichage exige une unité explicite.

Le service `RoomUnitService` utilise l'unité fournie par le paramètre Revit lorsqu'elle existe.

Aucun facteur manuel basé sur le nom « surface », « volume », « longueur », etc. n'est repris de l'ancien module.

### 7.6 Compatibilité API à valider dans Revit

Le raccordement réel devra être vérifié dans Revit 2025.4 pour :

- GUID de paramètre partagé ;
- `ForgeTypeId` d'un paramètre intégré ;
- identité de définition des paramètres projet ;
- type de donnée de la définition ;
- unité du paramètre ;
- résolution de paramètres homonymes.

---

## 8. Transactions et écriture

Le workflow cible reste :

```text
READ
  ↓
DATA
  ↓
CALCULATE
  ↓
VALIDATE
  ↓
WRITE
```

Le calcul est réalisé hors transaction.

La transaction Revit n'est ouverte qu'au moment de l'écriture des résultats validés.

---

## 9. Interface cible

L'interface suit `docs/04_UI_Guidelines.md`.

Principes spécifiques :

- titre fonctionnel : **Calculs des pièces** ;
- pas de choix « toutes les pièces / vue active » ;
- affichage informatif : **Toutes les pièces du projet** ;
- filtre optionnel par paramètre ;
- paramètres de regroupement, source et destination clairement séparés ;
- une seule action principale : **Calculer** ;
- progression et résultat visibles ;
- styles WPF communs Outils TAA lorsque disponibles.

---

## 10. Tests

Les Blocs 1 à 3 possèdent actuellement **34 tests unitaires hors Revit**, exécutés avec succès dans l'environnement de travail.

Ils couvrent notamment :

- regroupement et somme ;
- cas vide, zéro et valeurs non numériques ;
- progression ;
- filtre métier optionnel ;
- collecte de toutes les pièces du projet sans filtre de vue ;
- conservation d'une pièce à surface nulle dans le périmètre source ;
- lecture String / Integer / Double / ElementId ;
- identité par GUID partagé ;
- identité de paramètre intégré ;
- identité de définition ;
- paramètres homonymes distincts ;
- refus d'un fallback par nom ambigu ;
- sérialisation du descripteur ;
- agrégation readonly sur plusieurs pièces ;
- compatibilité / incompatibilité de types de donnée ;
- avertissements de conversion de type ;
- conversions d'unités via un adaptateur UnitUtils ;
- rejet d'un paramètre non mesurable lorsque l'unité est requise ;
- non-régression de la collision Python entre modules génériques.

Les blocs suivants devront ajouter les tests sur :

- paramètres absents ;
- paramètres homonymes et identités stables lorsque pertinentes ;
- String / Integer / Double / ElementId ;
- paramètres en lecture seule ;
- unités ;
- écriture ;
- rollback ;
- persistance ;
- chargement WPF ;
- workflow complet dans Revit 2025.4.

---

## 11. État d'implémentation

### Implémenté et testé hors Revit

- modèle métier de calcul ;
- moteur de regroupement/somme ;
- diagnostics simples des entrées ignorées ;
- callback de progression ;
- tests unitaires du moteur ;
- collecte complète du projet sans filtre de vue ;
- filtre métier optionnel par paramètre ;
- première lecture normalisée des paramètres Revit ;
- descripteurs sérialisables avec identité stable lorsque disponible ;
- détection des homonymes ;
- métadonnées DataType / unité ;
- validation source / destination ;
- utilitaires communs d'unités ;
- agrégation conservative de l'état writable.

### À implémenter

- écriture Revit ;
- persistance Outils TAA ;
- UI WPF ;
- bouton pyRevit ;
- tests d'intégration.

### À valider dans Revit 2025.4

Tout comportement dépendant de :

- collecte Revit ;
- paramètres ;
- unités Revit ;
- transactions ;
- WPF / pyRevit ;
- écriture dans le modèle.

---

## 12. Règles non négociables

1. Le périmètre source est toujours toutes les pièces du projet actif.
2. Le filtre par paramètre est un filtre métier optionnel appliqué après cette collecte.
3. L'UI ne contient pas de logique de calcul.
4. Le moteur métier ne dépend pas de Revit.
5. Les unités ne sont pas devinées uniquement depuis le nom d'un paramètre.
6. Les paramètres de destination sont validés avant écriture.
7. Une exception importante ne doit pas être masquée par `except: pass`.
8. Une transaction n'est ouverte qu'au moment de l'écriture.
9. Le comportement documenté doit rester synchronisé avec le code.
10. Toute validation Revit doit être réalisée dans Revit 2025.4 avant d'être déclarée acquise.
