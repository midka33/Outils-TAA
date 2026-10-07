# Calculs des pièces

**Statut :** Base v1.0.1 validée — résolution interactive des divergences en validation  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Module :** `Calculs.panel`  
**Validation finale :** Revit 2025.4 / pyRevit 5.x — 6 octobre 2026

---

## 1. Responsabilité

Le module **Calculs des pièces** regroupe les traitements métier portant sur les pièces Revit : collecte, filtre métier optionnel, regroupement, agrégation et écriture contrôlée du résultat dans un paramètre de pièce.

Le nom historique **RoomCalculator** n'est utilisé que pour désigner l'ancien module source.

---

## 2. Périmètre source

Le périmètre est fixe :

> **Calculs des pièces travaille toujours à partir de toutes les pièces du projet Revit actif.**

L'interface ne propose pas de choix :

- Vue active ;
- Toutes les pièces ;
- Pièces sélectionnées.

Un filtre métier optionnel par paramètre peut ensuite réduire ce jeu de pièces.

Le flux est :

```text
Toutes les pièces du projet
        ↓
Filtre par paramètre (optionnel)
        ↓
Lecture des paramètres
        ↓
Regroupement
        ↓
Somme
        ↓
Validation
        ↓
Confirmation utilisateur
        ↓
Transaction Revit
        ↓
Écriture
        ↓
Rapport
```

La collecte n'exclut pas implicitement une pièce parce qu'elle n'est pas visible dans la vue active ou parce que sa surface vaut zéro.

---

## 3. Fonctionnalités migrées

La migration couvre désormais :

- collecte de toutes les pièces du projet ;
- filtre optionnel par paramètre et valeur exacte ;
- choix du paramètre de regroupement ;
- choix du paramètre numérique à additionner ;
- choix du paramètre de destination ;
- calcul d'une somme par groupe ;
- écriture du total dans les pièces appartenant au groupe ;
- gestion explicite des pièces ignorées pendant le calcul ;
- validation des paramètres avant écriture ;
- gestion des paramètres homonymes ;
- gestion centralisée des unités Revit ;
- progression ;
- confirmation avant modification du modèle ;
- rapport de succès / échecs / éléments ignorés ;
- persistance des choix utilisateur ;
- migration contrôlée des anciens réglages RoomTools ;
- interface WPF Outils TAA ;
- bouton pyRevit **Calculs des pièces**.

---

## 4. Architecture

```text
CalculsPieces.pushbutton/script.py
        ↓
UI WPF
        ↓
CalculationController
        ↓
RoomCalculationWorkflow
        ├── RoomCollectorService
        ├── RoomFilter
        ├── RoomParameterService
        ├── RoomParameterValidator
        ├── RoomCalculator
        ├── RoomWriter
        └── RevitTransaction
                ↓
             API Revit
```

Le moteur métier `lib/calculation` ne dépend ni de WPF ni directement de Revit.

---

## 5. Moteur de calcul

### 5.1 Entrée normalisée

`RoomCalculationItem` contient :

```text
room_key
group_value
source_value
```

### 5.2 Regroupement et somme

`RoomCalculator` :

- regroupe les pièces par `group_value` ;
- additionne les valeurs numériques ;
- accepte zéro comme valeur valide ;
- accepte zéro comme clé de groupe valide ;
- signale les groupes vides ;
- signale les sources non numériques ;
- conserve les membres d'un groupe même lorsqu'une pièce ne contribue pas à la somme.

Cette dernière règle permet de conserver le comportement métier historique : une pièce ayant un groupe valide mais une source vide peut recevoir le total calculé à partir des autres pièces de son groupe.

---

## 6. Collecte et filtre

`RoomCollectorService.collect_all_rooms()` collecte la catégorie des pièces dans le document entier.

Règles :

- aucun filtre de vue ;
- aucun recours à `ActiveView` ;
- aucune exclusion implicite par `Area == 0`.

`RoomFilter` applique ensuite, si demandé, un filtre métier par paramètre et valeur exacte.

---

## 7. Paramètres Revit

### 7.1 Identité

`RoomParameterDescriptor` conserve :

- nom affiché ;
- identité technique ;
- `StorageType` ;
- type de donnée Revit ;
- unité Revit ;
- état writable.

Priorité d'identification :

1. GUID de paramètre partagé ;
2. ForgeTypeId d'un paramètre Revit intégré ;
3. identifiant de définition ;
4. nom en dernier recours.

Deux paramètres homonymes mais distincts ne sont pas fusionnés silencieusement.

Si seul le nom est disponible et que plusieurs paramètres portent ce nom, la résolution est bloquée comme ambiguë.

### 7.2 Destination

Une destination doit :

- exister ;
- être directement écrivable **ou** être temporairement déverrouillable lorsqu'un blocage provient de l'alignement des groupes ;
- utiliser un type d'écriture pris en charge ;
- rester compatible avec les règles de type définies par le validateur.

Types de destination pris en charge :

```text
Double
Integer
String
```

`ElementId` n'est pas une destination autorisée.

### 7.3 Pièces appartenant à des groupes

Les pièces placées dans des groupes restent dans le périmètre de calcul.

Pour un paramètre de projet non intégré configuré avec des valeurs **alignées par type de groupe**, Revit peut empêcher l'écriture directe sur les pièces groupées. Le module analyse désormais les membres correspondants entre les différentes occurrences d'un même type de groupe avant toute transaction.

La correspondance s'appuie sur l'ordre retourné par `Group.GetMemberIds()`, afin d'identifier le même membre dans les différentes instances du type de groupe.

#### Cas 1 — toutes les valeurs projetées sont identiques

Le comportement reste automatique :

```text
État initial : valeurs alignées par type de groupe
        ↓
Autoriser temporairement les valeurs variables
        ↓
Écriture des résultats
        ↓
Restaurer l'alignement par type de groupe
        ↓
Commit
```

#### Cas 2 — des valeurs différentes sont détectées

L'outil ne choisit plus silencieusement une valeur et n'annule plus automatiquement le calcul. L'utilisateur choisit entre trois stratégies :

1. **Conserver les résultats exacts**  
   Les valeurs calculées sont conservées telles quelles et le paramètre reste durablement configuré pour permettre des valeurs différentes entre les occurrences de groupes.

2. **Conserver l'alignement et choisir les valeurs**  
   Une fenêtre présente, pour chaque membre correspondant concerné :
   - le type de groupe Revit ;
   - la pièce correspondante ;
   - toutes les valeurs rencontrées ;
   - le nombre d'occurrences de chaque valeur.

   La valeur la plus fréquente est **présélectionnée uniquement comme aide**, mais elle n'est jamais imposée. L'utilisateur peut sélectionner n'importe quelle valeur proposée. La valeur retenue est ensuite appliquée à toutes les occurrences correspondantes avant restauration de l'alignement.

3. **Annuler**  
   Aucune modification n'est écrite.

La logique continue de s'appuyer sur `InternalDefinition.VariesAcrossGroups` et `SetAllowVaryBetweenGroups()`.

Sécurités :

- les paramètres Revit intégrés ne sont jamais déverrouillés par cette logique ;
- l'analyse des divergences est réalisée avant l'ouverture de la transaction ;
- les occurrences non incluses par un filtre de calcul sont également prises en compte avec leur valeur existante afin de ne pas provoquer un réalignement imprévu ;
- si l'utilisateur choisit de conserver l'alignement et que Revit signale malgré tout un réalignement résiduel, la transaction est annulée ;
- les destinations réellement readonly pour une autre raison restent refusées.

Le comportement automatique sans divergence a été validé dans Revit 2025.4 le 6 octobre 2026. La nouvelle résolution interactive des divergences doit être validée dans Revit 2025.4 avant fusion dans `main`.

---

## 8. Unités

Les valeurs `Double` restent en unités internes Revit pendant le calcul.

Les conversions sont centralisées dans :

```text
lib/common/unit_utils.py
```

L'interface utilise les unités compatibles retournées par Revit pour le type de donnée concerné.

Le système historique basé sur des facteurs manuels et la détection par mots-clés dans le nom du paramètre n'est pas repris.

Pour une écriture `Double → Double`, la valeur reste en unités internes Revit.

Pour une sortie `Double → Integer` ou `Double → String`, l'unité de sortie peut être choisie lorsqu'une conversion explicite est pertinente.

---

## 9. Validation et écriture

Le workflow applique :

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

Aucune transaction n'est ouverte pendant la collecte ou le calcul.

Avant écriture :

- la paire source/destination est validée ;
- chaque destination est recontrôlée sur la pièce ;
- la valeur à écrire est préparée hors transaction.

La transaction est ensuite ouverte uniquement pour les écritures valides.

Un échec local sur une pièce est rapporté sans masquer les autres résultats valides.

Une erreur fatale de transaction provoque un rollback et aucun succès n'est déclaré pour les écritures annulées.

---

## 10. Persistance

Les préférences sont stockées sous :

```text
%APPDATA%/Outils-TAA/Calculs/settings.json
```

Le stockage conserve uniquement des données sérialisables et jamais d'objet Revit.

Sont mémorisés :

- paramètre de regroupement ;
- paramètre source ;
- paramètre destination ;
- filtre éventuel ;
- valeur de filtre ;
- unité de sortie.

L'ancien fichier :

```text
%APPDATA%/RoomTools/settings.json
```

peut être lu pour migrer les anciens noms de paramètres.

Les anciens tags d'unités manuels ne sont pas transformés artificiellement en ForgeTypeId.

---

## 11. Interface

L'interface suit `docs/04_UI_Guidelines.md`.

Elle comporte :

- titre **Calculs des pièces** ;
- source informative **Toutes les pièces du projet** ;
- compteur de pièces détectées ;
- filtre optionnel ;
- Regrouper par ;
- Additionner ;
- Paramètre destination ;
- unité de sortie contextuelle ;
- état et progression ;
- bouton secondaire Fermer ;
- une seule action principale : **Calculer** ;
- confirmation avant écriture ;
- rapport détaillé après exécution.

Les styles communs sont définis dans :

```text
OutilsTAA.extension/resources/ui/taa_theme.xaml
```

La fenêtre utilise l'accent **TAA Orange UI `#FD8B5A`** ; la référence de marque `#FA641F` reste utilisée notamment par l'icône du ruban.

### 11.1 Compacité de la fenêtre

La fenêtre principale vise environ **860 × 560 px** en taille nominale.

Sur un écran **1920 × 1080**, les réglages courants doivent être visibles sans défilement vertical.

Le ScrollViewer reste présent uniquement comme sécurité lorsque :

- la fenêtre est fortement réduite ;
- le scaling Windows diminue l'espace disponible ;
- la résolution est insuffisante.

La compacité est obtenue sans diminuer la lisibilité :

- sections plus rapprochées ;
- paddings verticaux réduits ;
- filtre sur une ligne ;
- trois paramètres de calcul sur une ligne ;
- textes explicatifs secondaires déplacés en ToolTips.

### 11.2 Icône du ruban

Le bouton pyRevit utilise l'icône validée **Plan 2×2 + somme Σ** :

```text
CalculsPieces.pushbutton/
├── icon.png
└── icon.dark.png
```

Le pictogramme associe :

- un plan de pièces simplifié ;
- une pièce en TAA Orange ;
- un badge Σ indiquant l'agrégation / somme.

---

## 12. Tests automatisés hors Revit

Une CI dédiée exécute :

```text
python -m pytest tests/calculation -q
```

Exécution validée après ajout de la gestion des paramètres de groupes :

```text
84 passed
```

Les tests couvrent notamment :

- calcul et regroupement ;
- valeurs vides, zéro et valeurs non numériques ;
- membres de groupe sans source exploitable ;
- filtre métier ;
- collecte du projet entier ;
- paramètres String / Integer / Double / ElementId ;
- identités GUID / ForgeTypeId / définition ;
- homonymes ;
- ReadOnly et déverrouillage temporaire des paramètres alignés entre groupes ;
- compatibilité source / destination ;
- unités ;
- préparation et écriture ;
- transaction / rollback ;
- paramètres de pièces alignés par type de groupe, détection des divergences, choix utilisateur et rollback de sécurité ;
- persistance ;
- migration des réglages historiques ;
- contrôleur ;
- structure et événements XAML ;
- syntaxe Python des fichiers du module ;
- absence de `ActiveView` ;
- absence de `except:` nu.

La CI hors Revit ne valide pas le comportement réel de l'API Autodesk ni le chargement WPF dans IronPython/pyRevit.

---

## 13. Bugs capitalisés pendant la migration

Voir `docs/11_BUGS_Prevention_Registry.md`.

Bugs spécifiques actuellement capitalisés :

- `BUG-CALCULS-001` — collision du module générique `models` ;
- `BUG-CALCULS-002` — état writable filtré avant agrégation ;
- `BUG-CALCULS-003` — échappements de chaînes corrompant le code Python généré ;
- `BUG-CALCULS-004` — dossier de tests masquant le package métier `calculation` ;
- `BUG-CALCULS-005` — écriture impossible dans les paramètres alignés entre occurrences de groupes ;
- `BUG-CALCULS-006` — divergence entre occurrences entraînant un rollback systématique sans choix utilisateur.

---

## 14. État final

### Validé hors Revit

- moteur métier ;
- collecte/adaptateur ;
- filtre ;
- paramètres et identités ;
- validation ;
- unités ;
- écriture préparée ;
- transaction contrôlée ;
- persistance ;
- contrôleur ;
- interface WPF ;
- rapport ;
- bouton pyRevit ;
- CI hors Revit : **84 tests réussis** sur la branche de résolution des divergences.

### Validé dans Revit 2025.4

Le module a été validé dans Revit 2025.4. La campagne initiale a été confirmée le 1er octobre 2026, puis la gestion des paramètres de pièces alignés entre groupes a été validée le 6 octobre 2026, notamment :

- apparition et lisibilité de l'icône **Plan 2×2 + somme Σ** dans le ruban ;
- chargement de la fenêtre WPF ;
- interface compacte sans défilement vertical obligatoire sur écran 1920 × 1080 ;
- fonctionnement métier des calculs ;
- collecte des pièces ;
- résolution et écriture des paramètres ;
- transaction / Undo ;
- persistance ;
- comportement général du module ;
- écriture dans un paramètre de pièce aligné par type de groupe, avec restauration de l'alignement après calcul.

La campagne de validation est archivée dans :

```text
docs/18_Calculs_Pieces_Tests_Revit.md
```

La base v1.0.1 reste validée dans Revit 2025.4. La résolution interactive des divergences entre occurrences de groupes reste sur branche dédiée jusqu'à validation de TEST-CALC-22.
