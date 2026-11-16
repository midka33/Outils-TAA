# Calculs des pièces

**Statut :** Validé dans Revit 2025.4 — livré depuis v1.0.3, **inchangé dans la release Outils TAA v1.4.0**  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Module :** `Calculs.panel`  
**Validation finale :** Revit 2025.4 / pyRevit 5.x — 6 octobre 2026 ; documentation utilisateur courante : `docs/release/Tutoriel_Calculs_Pieces_v1.4.0.md`

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

Pour un paramètre de projet non intégré configuré avec des valeurs **alignées par type de groupe**, Revit peut empêcher l'écriture directe sur les pièces groupées. Le module gère ce cas de façon transactionnelle :

```text
État initial : valeurs alignées par type de groupe
        ↓
Transaction Revit
        ↓
Autoriser temporairement les valeurs variables
        ↓
Écriture des résultats
        ↓
Restaurer l'alignement par type de groupe
        ↓
Contrôle des éléments réalignés par Revit
        ↓
Commit si aucun réalignement inattendu
```

La logique s'appuie sur `InternalDefinition.VariesAcrossGroups` et `SetAllowVaryBetweenGroups()`.

Sécurités :

- les paramètres Revit intégrés ne sont jamais déverrouillés par cette logique ;
- l'état initial est restauré dans la même transaction que l'écriture ;
- si Revit doit réaligner un ou plusieurs éléments lors du retour à l'état initial, la transaction est annulée ;
- les destinations réellement readonly pour une autre raison restent refusées.

Cette stratégie correspond au cas métier TAA où les occurrences d'un même type de groupe doivent produire le même résultat. **Le comportement historique sans conflit** a été validé dans Revit 2025.4 le 6 octobre 2026.

### 7.3.1 Divergences entre occurrences — correctif sur branche dédiée (16 novembre 2026)

**Statut : implémenté sur `fix/calculs-group-conflicts-design-options`, tests Revit à effectuer.**

La préparation du calcul repère, avant toute écriture, les types de groupes de modèle dont les différentes occurrences recevraient des totaux distincts. Le regroupement métier et la collecte de pièces restent inchangés. Les valeurs sont détectées avant conversion de sortie ; une différence très faible peut donc être signalée comme divergence.

Si une divergence est identifiée, la transaction n'est pas ouverte sans choix explicite dans la fenêtre :

1. **Autoriser les valeurs différentes** : `SetAllowVaryBetweenGroups(document, True)` demeure actif après une écriture réussie. Le changement est volontaire et durable pour la définition du paramètre de projet concernée ; l'utilisateur le confirme avant toute transaction.
2. **Conserver l'alignement** : l'utilisateur choisit, **pour chaque type de groupe en conflit**, une valeur de référence parmi les totaux déjà calculés pour ses occurrences. Cette valeur est affectée aux pièces concernées du type puis l'alignement est restauré. Un contrôle exige que la restauration ne modifie aucun autre élément ; sinon rollback.

**Garde-fous :** la seconde option n'est pas offerte si une même occurrence du type comporte plusieurs totaux de regroupements différents (écrasement de plusieurs logements). Une sélection incomplète ou incohérente est refusée. Le choix des valeurs ne change pas les pièces non groupées. Les écritures échouées lors de l'un de ces deux modes déclenchent l'annulation de la transaction. Les groupes dont la structure ne peut être lue restent protégés par l'ancien contrôle de restauration/rollback, mais une divergence non identifiable en préparation peut donc encore donner lieu à un refus.

Le réglage de la définition de paramètre est **global au projet**, pas limité à une variante ou à un groupe. Un changement « autoriser les valeurs différentes » peut donc concerner d'autres occurrences de cette définition dans le modèle.

### 7.3.2 Calcul indépendant des variantes de conception — correctif sur branche dédiée

**Décision utilisateur du 16 novembre 2026 :** deux appartements portant la même clé métier (`B200`, par exemple) mais présents dans deux variantes différentes ne doivent **jamais** être additionnés ensemble. Le filtre métier optionnel existant reste inchangé. Le module collecte toujours les pièces de tout le projet, indépendamment de la vue Revit active.

**Clé d'agrégation :**
- **Scénario de référence :** les pièces du modèle principal et les pièces des variantes principales sont regroupées par leur seule clé métier historique, lorsque celle-ci est identique. Une variante principale par jeu contribue au scénario de référence.
- **Scénario de variante secondaire :** chaque variante secondaire dispose de son propre espace de regroupement, identifié par l'ID de la variante + la clé métier. Deux appartements `B200` dans deux variantes secondaires différentes produisent deux sommes distinctes, tout comme un `B200` de variante secondaire et un `B200` du scénario de référence.
- La somme est calculée sur les valeurs déjà calculées par Revit pour chacune de ses pièces. Aucune pièce ne participe à deux écritures, aucun filtrage implicite selon la vue, aucun nouveau calcul géométrique de limites de pièces.
- Les pièces sans clé métier continuent d'être ignorées.
- Le rapport et la confirmation détaillent les variantes présentes et les pièces retenues, avec rappel de la séparation des variantes secondaires.

**Exemple :** `B200` du scénario de référence = 70 m² ; `B200` de « Variante 1 » = 65 m² ; `B200` de « Variante 2 » = 72 m². Ce sont trois totaux et non un total à 207 m².

**Confirmation conditionnelle avant écriture :** si un même numéro d'appartement apparaît dans au moins deux scénarios distincts (référence/variante secondaire ou deux variantes secondaires), le module présente une fenêtre **WPF TAA** indiquant chaque scénario et son total indépendant. Le bouton de confirmation valide **la séparation des surfaces uniquement** ; il n'existe pas de choix pour les additionner. Le refus ou la fermeture annule la commande avant toute écriture. Ce contrôle précède la résolution éventuelle des conflits de paramètres de groupes et la confirmation générale. Il n'apparaît pas lorsqu'un appartement existe dans un seul scénario. Le workflow bloque aussi toute tentative d'écriture sans confirmation, même si l'interface était contournée.

**Interface :** les décisions relatives aux groupes et la confirmation d'écriture utilisent désormais une fenêtre modale WPF TAA (`calculation_decision.xaml`, `calculation_decision_window.py`) avec thème central, libellés lisibles et choix non tronqués. Aucun choix de collecte par vue n'est conservé.

**À valider dans Revit 2025.4 :** `Room.DesignOption`, séparation effective des totaux B200 entre variantes, pièce de variante principale, écriture des paramètres de groupes, fermeture/annulation WPF et non-régression sans variante.

**Anti-régression :** `tests/calculation/test_group_decisions.py` comporte les cas B200 dans plusieurs variantes et pièce à groupe vide ; exécuter `python -m pytest tests/calculation -q`. Les tests hors Revit ne remplacent pas cette recette.

### 7.3.3 Gestion des variantes : séparation ou addition volontaire (16 novembre 2026)

**Nouvelle fonctionnalité sur PR #56 (branche de test, non fusionnée).** La fenêtre principale propose une liste déroulante `GESTION DES VARIANTES` avec deux valeurs :

- **Surfaces séparées par variante (par défaut)** : garde le comportement développé précédemment (scénario de référence partagé par modèle principal et variantes principales, variante secondaire avec un total indépendant).
- **Additionner toutes les surfaces des variantes** : pour chaque numéro d'appartement, additionne les surfaces de **toutes les pièces**, y compris celles des variantes secondaires. La clé de regroupement redevient le seul numéro d'appartement, sans identifiant de variante. Le **même total cumulé est écrit dans toutes les pièces** correspondant à ce numéro, quelle que soit leur variante, sous réserve du traitement habituel des paramètres de groupes.

Le choix est **volontaire et non mémorisé** : une nouvelle ouverture de l'outil revient au mode séparé. Le filtre métier optionnel existant s'applique toujours avant le regroupement, et le collecteur ne dépend pas de la vue Revit active. Si un appartement est présent dans plusieurs scénarios, une fenêtre WPF TAA liste les totaux par scénario. En mode addition, elle affiche aussi le total cumulé, avertit sur le risque de **double comptage de solutions alternatives** et exige une confirmation avant écriture. Une annulation ferme le parcours sans transaction. Le moteur refuse l'écriture sans cette confirmation, même si le dialogue était contourné. La confirmation finale d'écriture reste obligatoire.

**Exemple :** B200 = 35,330 m² (référence) + 29,522 m² (Variante 1) : en mode séparé les deux résultats restent respectivement 35,330 et 29,522 m² ; en mode addition, **64,852 m² est écrit dans les pièces des deux scénarios**. Le calcul est une somme de paramètres de pièces déjà calculés par Revit, pas une fusion géométrique de variantes.

**Anti-régression** : `tests/calculation/test_group_decisions.py`, cas B200 de deux variantes, écritures distinctes/cumulées, absence de confirmation, mode invalide. **Recette Revit 2025.4 à effectuer** : vérifier fenêtre et confirmation WPF, résultat des deux modes sur copie, valeurs dans toutes les pièces concernées, fonctionnement des groupes et Undo.

### 7.4 Performance d'ouverture

À l'ouverture de la fenêtre, la découverte des paramètres est effectuée en **un seul
parcours** des pièces du projet.

Avant cette optimisation, `CalculationController.load_context()` appelait trois fois
`RoomParameterService.get_parameter_descriptors()` :

1. tous les paramètres ;
2. les paramètres numériques ;
3. les paramètres écrivable.

Or chaque appel reparcourait toutes les pièces et tous leurs paramètres, et
`create_descriptor()` relisait notamment les identités Revit, types de données,
unités et états readonly/groupes.

Le contexte UI est désormais construit ainsi :

```text
Collecte des pièces
        ↓
1 scan de tous les paramètres
        ↓
descripteurs agrégés
        ├── liste complète
        ├── filtre numérique en mémoire
        └── filtre destination écrivable en mémoire
```

Cette optimisation ne modifie ni les règles de sélection des paramètres, ni la
compatibilité avec les groupes, ni le calcul. Elle supprime deux scans Revit
redondants au démarrage.

Pendant l'unique scan restant, les métadonnées invariantes d'une définition de
paramètre (identité, type de donnée, unité, StorageType) sont également mises en
cache localement par `Parameter.Id`. Elles ne sont donc plus redemandées à Revit
pour chaque pièce portant le même paramètre. L'état `IsReadOnly` et la compatibilité
avec les groupes restent contrôlés sur chaque pièce, car ces informations peuvent
varier par occurrence.

Le cache ne survit pas à l'ouverture de la fenêtre et n'introduit donc aucun problème
d'invalidation après modification du projet.

**Validation réelle :** ouverture observée autour de **3 secondes** dans Revit 2025.4
sur le projet de validation d'environ 80 logements, le 8 octobre 2026.

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
78 passed
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
- paramètres de pièces alignés par type de groupe, restauration et rollback de sécurité ;
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
- `BUG-CALCULS-005` — écriture impossible dans les paramètres alignés entre occurrences de groupes.

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
- CI hors Revit : **78 tests réussis**.

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

Le module est considéré comme validé pour intégration dans `main`.

**Correctif ergonomique du 16/11/2026 (retour utilisateur dans Revit) :** la fenêtre de confirmation WPF des appartements multi-variantes affichait les surfaces, mais ses boutons étaient hors de la zone visible, car la hauteur était forcée à 320 unités WPF dans le mode sans liste. La hauteur a été rétablie à 440 unités WPF afin de réserver la place du pied d'actions ; le contenu long conserve son ScrollViewer. Les libellés distinguent désormais explicitement le « scénario de référence » et les variantes par leur nom exact (sans duplication « variante Variante 1 »). Vérification automatisée statique et contrôle réel en Revit à renouveler.

**Ajustement redimensionnement (retour utilisateur Revit du 16/11/2026) :** dans la fenêtre de décision WPF, le panneau blanc de détails demeurait de hauteur fixe lorsque l'utilisateur agrandissait la fenêtre. Cause : deuxième ligne du `Grid` définie en `Auto`, troisième ligne en `*` alors que le panneau de choix pouvait être masqué, et `ScrollViewer.MaxHeight=170`. Correction ciblée : ligne du récapitulatif en `*`, ligne des choix en `Auto`, retrait de la hauteur maximale du récapitulatif et limite du panneau de choix à 180 unités WPF. Le pied d'actions reste en ligne `Auto` hors du défilement. Aucun changement au calcul ni à la transaction. Vérification du redimensionnement dans Revit à effectuer après déploiement.

### 7.3.4 Confirmation unique et information réduite — évolution UI (16 novembre 2026)

**Nouvelle règle validée fonctionnellement par l'utilisateur, recette Revit en attente :** une seule fenêtre **WPF TAA** de revue avant écriture, au lieu d'une succession de dialogues « variantes », « groupes », puis « confirmation ». Son contenu se limite au nombre de pièces à écrire, au nombre de totaux, au paramètre de destination et à la situation des variantes. Le risque de double comptage est signalé en une phrase lorsque le mode **Additionner** est sélectionné.

**Conflits entre groupes :** si une divergence entre occurrences est détectée, le choix entre « valeurs différentes » et « valeur commune par type de groupe » se fait dans **cette même fenêtre**, sans nouvelle fenêtre. Pour le mode uniforme, les valeurs de référence se sélectionnent directement en dessous pour chaque type de groupe. Aucune valeur ni modification de la définition du paramètre n'est retenue implicitement : un choix manquant bloque le bouton de confirmation, sans transaction. Le contrôle de transaction et les règles métier préexistantes sont conservés.

**Rapport après calcul :** en cas de réussite, le rapport détaillé n'est plus ouvert systématiquement ; le résultat apparaît dans l'état de la fenêtre principale et le bouton **Rapport** permet de l'afficher à la demande. En cas d'échec de transaction ou d'écritures, le rapport reste affiché automatiquement. Les pièces ignorées sont signalées par leur nombre dans l'état, avec détails consultables dans le rapport.

**Implémentation :** `ui/calculation_review.xaml` et `calculation_review_window.py`, `ui/calculs_window.py`, `ui/calculs_ui.xaml`. **Non fusionnée** (PR #56). Vérifier dans Revit 2025.4 : parcours sans conflit, avec conflit, sélection de valeur commune, mode d'addition des variantes, annulation, rapport facultatif et rapport d'erreurs. Le tests automatisés hors Revit ne valident pas l'affichage WPF réel.

### 7.3.5 Gestion des groupes accessible dès la fenêtre principale (16 novembre 2026)

**Décision utilisateur :** comme pour la gestion des variantes, le mode de gestion des groupes doit être accessible avant le calcul, même si aucun conflit n'est encore détecté.

La fenêtre principale WPF TAA propose maintenant **GESTION DES GROUPES** :
- **Automatique — conserver les réglages (défaut)** : comportement historique ; conservation de l'alignement et proposition d'un choix lors d'un conflit confirmé dans la fenêtre de revue unique.
- **Autoriser des valeurs différentes entre groupes** : choix explicite de conserver durablement les valeurs variables lorsque le paramètre de destination nécessite le déverrouillage par occurrence. La confirmation unique ne redemande pas ce choix. L'effet est global à la définition du paramètre dans le projet.
- **Conserver une valeur commune entre groupes** : alignement préservé ; si des occurrences du même type exigent des valeurs différentes, la fenêtre de revue demande seulement la valeur de référence par type, sans seconde fenêtre. Si l'uniformisation est dangereuse (plusieurs appartements distincts dans une même occurrence), le calcul est refusé.

**Sécurité :** choix invalide refusé dès la préparation ; aucun choix de référence fictif ou silencieux, transaction et rollback inchangés. Le mode n'est pas mémorisé et revient à « Automatique » à chaque ouverture. Aucun changement aux regroupements des variantes ni aux sommes.

**Tests :** `tests/calculation/test_group_decisions.py` couvre le contrôle WPF, les trois modes, la validation précoce et le blocage sans valeur commune. Recette Revit requise avant fusion : choix manuel dans la fenêtre principale, confirmation unique, valeurs variables et uniformisation.

### 7.3.6 Limite Revit : alignement global par type de groupe (retour du 16 novembre 2026)

**Retour maquette :** choix « Conserver une valeur commune entre groupes » sur le paramètre `Surface logement`, puis rollback de 36 écritures car Revit aurait réaligné 36 éléments lors de `SetAllowVaryBetweenGroups(False)`.

**Distinction :** la préparation du module n'observe que les valeurs qu'il prévoit d'écrire. Le réalignement Revit s'applique à la définition du paramètre sur tous les éléments concernés par les occurrences du même type de groupe, y compris ceux qui peuvent ne pas apparaître dans le calcul. Une sélection de valeur commune parmi les résultats ne garantit donc pas à elle seule une restauration sans modification annexe. La transaction est volontairement annulée pour préserver la maquette.

**Correctif ergonomique et diagnostic :** en cas d'échec, une seule cause de rollback est affichée, avec nombre de pièces annulées, et une solution alternative : choisir explicitement « Autoriser des valeurs différentes entre groupes » dans la fenêtre principale. **Attention : ce réglage change durablement la définition du paramètre dans le projet.** Aucun basculement automatique n'est effectué. Le mode « conserver une valeur commune » reste disponible pour les modèles compatibles ; le correctif ne prétend pas rendre ce mode universellement possible.

**Test requis :** confirmer l'absence de changement après rollback, tester le mode valeurs différentes sur copie du RVT, inspecter les valeurs des groupes et l'état `VariesAcrossGroups`, et effectuer Undo. Ne pas fusionner avant ces contrôles.
