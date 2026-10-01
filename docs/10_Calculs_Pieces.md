# Calculs des pièces

**Statut :** Migration en cours — Blocs 1 et 2 implémentés hors Revit  
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

## 7. Paramètres Revit — cible du prochain bloc

La couche Revit devra distinguer :

- identité du paramètre ;
- nom affiché ;
- type de stockage ;
- type de donnée Revit ;
- lecture possible ;
- écriture possible ;
- `IsReadOnly` ;
- valeur vide ;
- compatibilité d'unité.

Lorsque disponible, une identité stable doit être préférée à une recherche fragile uniquement par nom :

- `BuiltInParameter` ;
- GUID de paramètre partagé ;
- identifiant de définition approprié.

Le nom affiché reste utilisable dans l'interface.

---

## 8. Unités — cible du prochain bloc

Les calculs doivent travailler autant que possible sur des valeurs normalisées issues de Revit.

Les conversions doivent être centralisées et utiliser les API d'unités Revit prévues par Outils TAA.

Les facteurs de conversion dispersés et la détection d'un type d'unité à partir du nom du paramètre ne doivent pas être migrés comme solution finale.

---

## 9. Transactions et écriture

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

## 10. Interface cible

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

## 11. Tests

Les Blocs 1 et 2 possèdent actuellement **14 tests unitaires hors Revit**, exécutés avec succès pendant la migration.

Ils couvrent notamment :

- somme par groupe ;
- entrée vide ;
- groupe vide ;
- source non numérique ;
- groupe zéro et valeur zéro ;
- progression ;
- protection du dictionnaire de résultats ;
- absence de filtre ;
- filtre optionnel par paramètre ;
- collecte de toutes les pièces du document ;
- conservation d'une pièce à surface nulle dans le périmètre de collecte ;
- découverte de paramètres ;
- lecture String / Integer / Double / ElementId ;
- état lecture seule.

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

## 12. État d'implémentation

### Implémenté et testé hors Revit

- modèle métier de calcul ;
- moteur de regroupement/somme ;
- diagnostics simples des entrées ignorées ;
- callback de progression ;
- tests unitaires du moteur ;
- collecte complète du projet sans filtre de vue ;
- filtre métier optionnel par paramètre ;
- première lecture normalisée des paramètres Revit.

### À implémenter

- identité stable des paramètres ;
- type de donnée Revit / compatibilité d'unité ;
- unités communes ;
- validation du paramètre de destination ;
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

## 13. Règles non négociables

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
