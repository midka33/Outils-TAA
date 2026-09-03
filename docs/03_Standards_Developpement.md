# Outils TAA – Developer Handbook

## Chapitre 03 — Standards de Développement

**Version :** 1.0  
**Statut :** Référence  
**Projet :** Outils TAA  
**Environnement cible :** Autodesk Revit 2025.4 / pyRevit 5.x  
**Langue du code et de la documentation :** Français  
**Dernière mise à jour :** 2026

---

# 1. Objectif du document

Ce document définit les standards de développement applicables à l'ensemble des outils constituant **Outils TAA**.

L'objectif n'est pas uniquement d'obtenir du code fonctionnel.

Le code développé pour Outils TAA doit être :

- compréhensible ;
- maintenable ;
- réutilisable ;
- robuste ;
- prévisible ;
- documenté ;
- compatible avec l'environnement TAA ;
- facilement transmissible à un autre développeur ;
- suffisamment structuré pour pouvoir évoluer.

Outils TAA doit être considéré comme un **logiciel métier modulaire**, et non comme une collection de scripts indépendants.

Ces standards s'appliquent donc aussi bien à un petit utilitaire qu'à un outil complexe comme Export ou CalculsPieces.

---

# 2. Principes fondamentaux

Les règles suivantes constituent les principes de base du développement Outils TAA.

## 2.1 Une responsabilité par composant

Chaque classe, fonction ou module doit avoir une responsabilité clairement identifiable.

Une fonction qui :

- récupère des éléments Revit ;
- calcule un résultat ;
- modifie le modèle ;
- affiche une fenêtre ;
- écrit un fichier de log ;

est probablement trop chargée.

Il faut découper ces responsabilités.

### Mauvais exemple

```python
def traiter_rooms():
    # Recherche les pièces
    # Affiche une fenêtre
    # Calcule les surfaces
    # Modifie les paramètres
    # Affiche un message
    # Enregistre un log
    pass
```

### Approche recommandée

```python
rooms = room_service.get_rooms()
result = calculator.calculate(rooms)
parameter_service.write(result)
logger.info("Calcul terminé")
```

Chaque composant possède ainsi une fonction précise.

---

## 2.2 Capitalisation des bugs et prévention de leur réapparition

Lorsqu'un bug est résolu, sa **cause racine** doit être recherchée et documentée lorsqu'elle révèle une erreur de conception, de codage, de compatibilité ou de processus reproductible.

Si cette cause peut être évitée par une règle générale, une règle correspondante doit être ajoutée ou précisée dans les standards de développement.

Le cycle attendu est :

```text
Bug
↓
Reproduction
↓
Cause racine
↓
Correction
↓
Règle préventive dans les standards
↓
Test ou contrôle permettant de vérifier la règle
```

L'objectif est de transformer les erreurs rencontrées pendant le développement en **connaissance durable du projet**, afin de ne pas reproduire les mêmes erreurs dans les outils suivants.

Si une règle existe déjà, elle doit être complétée ou renforcée plutôt que dupliquée.

Lorsqu'une règle issue d'un bug entraîne une modification du code, des tests ou de l'architecture, la correction et la règle doivent être liées dans le commit ou la documentation correspondante lorsque cela est pertinent.

# 3. Principe DRY

Le principe **DRY – Don't Repeat Yourself** doit être appliqué systématiquement.

Lorsqu'une même logique apparaît plusieurs fois, elle doit être étudiée afin de déterminer si elle doit être déplacée dans la bibliothèque commune.

## Exemple

Si plusieurs outils doivent récupérer la valeur d'un paramètre Revit :

```python
parameter = element.LookupParameter("Surface")
```

il ne faut pas nécessairement reproduire cette logique dans chaque outil.

Une fonction commune peut être créée :

```python
value = parameter_utils.get_parameter_value(
    element,
    "Surface"
)
```

La bibliothèque commune doit progressivement devenir la base technique des outils.

---

# 4. Bibliothèque commune

La bibliothèque `lib/common/` constitue le socle technique d'Outils TAA.

Architecture de référence :

```text
lib/
└── common/
    ├── logger.py
    ├── settings.py
    ├── dialogs.py
    ├── parameter_utils.py
    ├── revit_utils.py
    ├── progress.py
    └── transaction.py
```

Cette organisation est définie dans l'architecture générale du projet.

## 4.1 Règle générale

Avant de créer une nouvelle fonction utilitaire dans un outil, le développeur doit vérifier si une fonctionnalité équivalente existe déjà dans `lib/common`.

### À éviter

```text
Export/
└── utils.py

CalculsPieces/
└── utils.py
```

avec deux fonctions réalisant pratiquement la même opération.

### Préférer

```text
lib/
└── common/
    └── revit_utils.py
```

---

# 5. Organisation d'un outil

Chaque outil doit respecter une organisation cohérente.

Exemple :

```text
MonOutil.pushbutton/
│
├── script.py
├── ui/
│   ├── main_window.xaml
│   └── main_window.py
│
├── services/
│   ├── calculator.py
│   └── revit_service.py
│
├── models/
│   └── result.py
│
└── README.md
```

Pour les petits outils, cette organisation peut être simplifiée.

Il ne faut cependant pas créer artificiellement une architecture complexe pour un outil de quelques dizaines de lignes.

---

# 6. Séparation des responsabilités

Le développement Outils TAA doit distinguer au minimum trois couches :

```text
┌──────────────────────────────┐
│              UI              │
│        Interface WPF         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        LOGIQUE MÉTIER        │
│      Services / Models       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          REVIT API           │
│ Elements / Documents / Tx    │
└──────────────────────────────┘
```

## 6.1 UI

La couche UI doit gérer :

- affichage ;
- saisie utilisateur ;
- sélection ;
- validation ;
- messages ;
- progression visuelle.

Elle ne doit pas contenir la logique métier principale.

---

## 6.2 Logique métier

La logique métier doit gérer :

- calculs ;
- règles ;
- transformations ;
- validation des données ;
- orchestration des opérations.

Elle doit être autant que possible indépendante de l'interface.

---

## 6.3 Accès Revit

La couche Revit doit gérer :

- recherche d'éléments ;
- lecture de paramètres ;
- écriture de paramètres ;
- création/suppression d'éléments ;
- transactions ;
- accès au document actif.

---

# 7. Architecture orientée objet

Pour les outils de taille moyenne ou importante, l'utilisation de classes est recommandée.

## Exemple

```python
class CalculsPieces:

    def __init__(self, rooms):
        self.rooms = rooms

    def calculate(self):
        results = []

        for room in self.rooms:
            results.append(
                self._calculate_room(room)
            )

        return results

    def _calculate_room(self, room):
        pass
```

Cette approche facilite :

- les tests ;
- la réutilisation ;
- l'évolution ;
- la compréhension du code.

---

# 8. Quand ne pas utiliser une classe

Une classe n'est pas obligatoire pour chaque opération.

Pour une opération simple et isolée :

```python
def format_area(value):
    return round(value, 2)
```

une fonction suffit.

Le principe est :

> Utiliser la structure la plus simple permettant de conserver un code clair et maintenable.

---

# 9. Convention de nommage Python

Les conventions suivantes sont recommandées.

## 9.1 Variables

Utiliser `snake_case`.

```python
room_count = 25
total_area = 1250.50
selected_rooms = []
```

Éviter :

```python
roomCount = 25
TotalArea = 1250
```

---

## 9.2 Fonctions

Utiliser `snake_case`.

```python
def calculate_total_area():
    pass
```

---

## 9.3 Classes

Utiliser `PascalCase`.

```python
class CalculsPieces:
    pass
```

---

## 9.4 Constantes

Utiliser des majuscules avec `_`.

```python
DEFAULT_PRECISION = 2
MAX_ROOM_COUNT = 5000
```

---

## 9.5 Modules

Utiliser des noms courts et explicites.

```text
parameter_utils.py
revit_utils.py
room_service.py
calculator.py
```

Éviter :

```text
utils2.py
functions.py
misc.py
stuff.py
```

---

# 10. Nommage métier

Le nommage doit refléter le vocabulaire utilisé dans le métier.

Pour les outils TAA, privilégier des termes compréhensibles par un architecte ou un BIM manager.

Exemple :

```python
room_area
room_number
room_name
sheet_subtitle
sheet_number
publication_set
```

plutôt que :

```python
x
data1
tmp2
obj
item
```

---

# 11. Variables temporaires

Les variables temporaires doivent rester explicites.

### Mauvais

```python
x = element.LookupParameter("Surface")
```

### Correct

```python
surface_parameter = element.LookupParameter("Surface")
```

### Exception

Pour une boucle courte :

```python
for room in rooms:
    ...
```

`room` est parfaitement acceptable.

---

# 12. Fonctions

Une fonction doit idéalement :

- faire une seule chose ;
- avoir un nom explicite ;
- avoir peu de paramètres ;
- retourner une valeur clairement définie.

### Exemple

```python
def get_room_area(room):
    """Retourne la surface de la pièce en unités Revit."""
    parameter = room.LookupParameter("Area")

    if parameter is None:
        return None

    return parameter.AsDouble()
```

---

# 13. Taille des fonctions

Une fonction dépassant environ 30 à 50 lignes doit être examinée.

Cela ne signifie pas qu'une fonction de 60 lignes est automatiquement mauvaise.

Cependant, une fonction longue doit provoquer une question :

> Peut-elle être découpée en plusieurs responsabilités ?

---

# 14. Documentation du code

Les fonctions importantes doivent être documentées.

## Exemple

```python
def get_parameter_value(element, parameter_name):
    """
    Retourne la valeur d'un paramètre Revit.

    Args:
        element: Élément Revit concerné.
        parameter_name: Nom du paramètre.

    Returns:
        Valeur du paramètre ou None si introuvable.
    """
```

La documentation doit expliquer :

- ce que fait la fonction ;
- ses paramètres ;
- son résultat ;
- les cas particuliers éventuels.

---

# 15. Commentaires

Les commentaires doivent expliquer **pourquoi**, et non simplement répéter le code.

### Mauvais

```python
# Boucle sur les pièces
for room in rooms:
```

Le code est déjà explicite.

### Meilleur

```python
# Les pièces non placées doivent être exclues
# car leur paramètre Surface peut être inexploitable.
for room in rooms:
```

---

# 16. Langue des commentaires

Les commentaires et docstrings du projet Outils TAA sont rédigés en **français**.

Exemple :

```python
# Vérifie que le document actif est bien disponible.
if doc is None:
    return
```

Le code technique peut naturellement conserver les noms imposés par l'API Revit :

```python
FilteredElementCollector
BuiltInCategory
Transaction
Parameter
```

---

## 16.1 Encodage des fichiers Python

Tous les fichiers Python (`.py`) du projet doivent être enregistrés en **UTF-8**.

Pour garantir la compatibilité avec **IronPython 2 utilisé par pyRevit**, tout fichier Python doit déclarer explicitement son encodage en première ligne :

```python
# -*- coding: utf-8 -*-
```

Cette déclaration doit être placée avant toute autre ligne du fichier.

Cette règle doit être appliquée systématiquement, même lorsque le fichier ne contient pas encore de caractères accentués, afin d'éviter les erreurs de parsing liées à l'encodage lors de l'exécution dans pyRevit.

# 17. Gestion des erreurs

Aucun outil destiné aux utilisateurs ne doit planter silencieusement.

Les exceptions doivent être :

1. interceptées lorsqu'elles sont prévisibles ;
2. journalisées ;
3. expliquées à l'utilisateur lorsque nécessaire ;
4. accompagnées d'une solution lorsque celle-ci est connue.

---

# 18. try / except

### À éviter

```python
try:
    do_something()
except:
    pass
```

Cette pratique masque les erreurs.

### Préférer

```python
try:
    do_something()

except Exception as error:
    logger.error(
        "Erreur lors de l'opération : {}".format(error)
    )
    raise
```

---

# 19. Exceptions métier

Lorsqu'une situation est attendue, une erreur explicite peut être utilisée.

```python
if not selected_rooms:
    raise ValueError(
        "Aucune pièce n'a été sélectionnée."
    )
```

Cela permet de distinguer une erreur métier d'un véritable problème technique.

---

# 20. Messages utilisateur

Les messages affichés dans Revit doivent être :

- courts ;
- compréhensibles ;
- orientés solution.

### Mauvais

```text
Erreur : NoneType object has no attribute...
```

### Correct

```text
Impossible de poursuivre.

Aucune pièce valide n'a été trouvée.

Vérifiez que les pièces sont placées et renseignées.
```

Les détails techniques doivent rester dans le log.

---

# 21. Logging

Tous les outils importants doivent utiliser le système de logging commun.

Exemple :

```python
logger.info("Début du traitement")
logger.info("Nombre de pièces : {}".format(len(rooms)))
logger.warning("Pièce sans numéro")
logger.error("Impossible d'écrire le paramètre")
```

Le logger ne doit pas être remplacé par une succession de `print()`.

---

# 22. Niveaux de log

Les niveaux principaux sont :

### DEBUG

Informations utiles au développeur.

```python
logger.debug("Paramètre trouvé : {}".format(parameter_name))
```

### INFO

Déroulement normal.

```python
logger.info("Publication démarrée")
```

### WARNING

Situation anormale mais non bloquante.

```python
logger.warning("Feuille sans Subtitle")
```

### ERROR

Erreur empêchant une opération.

```python
logger.error("Impossible de générer le PDF")
```

---

# 23. Transactions Revit

Toute modification du modèle Revit doit être effectuée dans une transaction appropriée.

Exemple :

```python
with Transaction(doc, "Mise à jour des pièces"):
    ...
```

La gestion des transactions doit idéalement passer par le module commun prévu à cet effet.

---

# 24. Principe de transaction minimale

Une transaction doit être aussi courte que possible.

### À éviter

```text
Transaction
    recherche des éléments
    calcul complexe
    traitement de fichiers
    calcul IA
    modification Revit
Fin Transaction
```

### Préférer

```text
Recherche
   ↓
Calcul
   ↓
Validation
   ↓
Transaction
   ↓
Écriture Revit
```

Cela réduit :

- les risques de blocage ;
- les risques d'annulation ;
- les temps de transaction ;
- les problèmes liés au document Revit.

---

# 25. Lecture / calcul / écriture

Une architecture particulièrement recommandée pour les outils TAA est :

```text
LECTURE
   ↓
DONNÉES
   ↓
CALCUL
   ↓
VALIDATION
   ↓
ÉCRITURE
```

Exemple :

```python
rooms = room_service.get_rooms()

results = calculator.calculate(rooms)

validator.validate(results)

parameter_service.write(results)
```

Cette structure rend le comportement du programme beaucoup plus prévisible.

---

# 26. Revit API

Les accès à l'API Revit doivent être regroupés autant que possible.

### À éviter

Une interface WPF qui manipule directement :

```python
FilteredElementCollector
Transaction
Parameter
Element
Document
```

dans tous ses événements.

### Préférer

```text
UI
 ↓
Service
 ↓
Revit Utils / Revit Service
 ↓
Revit API
```

---

# 27. Recherche d'éléments

Les recherches doivent être aussi précises que possible.

### À éviter

```python
FilteredElementCollector(doc).ToElements()
```

sur un modèle important si seuls les éléments d'une catégorie sont nécessaires.

### Préférer

```python
FilteredElementCollector(doc) \
    .OfCategory(BuiltInCategory.OST_Rooms) \
    .WhereElementIsNotElementType()
```

L'objectif est de limiter le volume d'éléments manipulés.

---

# 28. Performance

La performance doit être considérée dès la conception.

Principes :

- éviter les recherches Revit répétées ;
- éviter les transactions inutiles ;
- limiter les conversions ;
- ne pas recalculer une donnée identique ;
- utiliser des dictionnaires lorsque pertinent ;
- traiter les éléments par lots si nécessaire.

---

# 29. Exemple de problème de performance

### Mauvais

```python
for room in rooms:

    for element in all_elements:
        if element.Id == room.Id:
            ...
```

Cette structure peut devenir très coûteuse.

### Préférer

```python
elements_by_id = {
    element.Id.IntegerValue: element
    for element in all_elements
}
```

puis :

```python
element = elements_by_id.get(
    room.Id.IntegerValue
)
```

---

# 30. Interface WPF

Les interfaces graphiques doivent respecter les principes définis dans le chapitre UI Guidelines.

Le code métier ne doit pas être directement écrit dans les événements graphiques.

### À éviter

```python
def button_click(sender, args):

    # 200 lignes de logique métier
    ...
```

### Préférer

```python
def button_click(sender, args):

    try:
        controller.execute()

    except Exception as error:
        logger.error(error)
        dialogs.show_error(error)
```

---

# 31. Validation des entrées

Toute donnée saisie par l'utilisateur doit être validée.

Exemple :

```python
if not output_folder:
    dialogs.show_warning(
        "Veuillez sélectionner un dossier de sortie."
    )
    return
```

Ne jamais supposer qu'une valeur saisie est valide.

---

# 32. État de l'interface

L'interface doit refléter l'état réel du traitement.

Exemple :

```text
[ Lancer ]

       ↓

[ Traitement en cours... ]

       ↓

[ Terminé ]
```

Pendant une opération longue :

- désactiver les boutons incompatibles ;
- afficher une progression si possible ;
- éviter que l'utilisateur lance deux traitements simultanément.

---

# 33. Progression

Pour les opérations longues, utiliser le système de progression commun.

Exemple :

```text
Traitement des pièces...

████████████░░░░░░░░ 60 %

120 / 200
```

La progression doit être utile et ne doit pas être affichée pour une opération instantanée.

---

# 34. Paramètres utilisateur

Les paramètres persistants doivent être centralisés.

Exemples :

```text
Dernier dossier utilisé
Dernière option sélectionnée
Préférences d'affichage
Configuration Export
```

Ils ne doivent pas être dispersés dans plusieurs fichiers arbitraires.

Le module `settings.py` de la bibliothèque commune est prévu pour cette fonction.

---

# 35. Chemins de fichiers

Éviter les chemins codés en dur.

### Mauvais

```python
output = r"C:\Users\Jean\Desktop\Exports"
```

### Correct

```python
output = settings.get_output_directory()
```

Les chemins doivent être configurables.

---

# 36. Encodage

Tous les fichiers texte du projet doivent utiliser :

```text
UTF-8
```

Cela concerne notamment :

- `.py`
- `.md`
- `.json`
- `.xaml`
- `.txt`
- fichiers de configuration.

Cela permet notamment de gérer correctement les caractères français :

```text
é è ê à ç œ
```

---

# 37. Configuration

Les valeurs susceptibles d'être modifiées doivent être externalisées.

### À éviter

```python
MAX_FILES = 100
```

si cette valeur est destinée à être configurée par l'utilisateur ou l'administrateur.

Selon le besoin, elle pourra être placée dans :

```text
config.json
```

ou dans le système de configuration commun.

---

# 38. Dépendances

Les dépendances externes doivent être limitées.

Avant d'ajouter une bibliothèque externe, vérifier :

1. si Python / pyRevit fournit déjà la fonctionnalité ;
2. si Revit API permet de réaliser l'opération ;
3. si une bibliothèque interne existe ;
4. si la dépendance est compatible avec l'environnement TAA ;
5. si elle peut être maintenue dans le temps.

Une dépendance externe doit avoir une justification.

---

# 39. Compatibilité

La cible officielle du projet est :

```text
Autodesk Revit 2025.4
pyRevit 5.x
Python fourni par l'environnement pyRevit
```

Cette compatibilité constitue un principe fondateur du projet.

Toute utilisation d'une fonctionnalité dépendant d'une autre version de Revit doit être explicitement documentée.

---

# 40. Compatibilité API

Éviter les API expérimentales ou non documentées lorsque cela est possible.

Lorsqu'une fonctionnalité repose sur un comportement particulier de Revit :

- documenter le comportement ;
- préciser la version testée ;
- prévoir une gestion d'erreur ;
- éviter de supposer que le comportement est universel.

---

# 41. Imports

Les imports doivent être regroupés au début du fichier.

### Exemple

```python
import os
import json

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory
)

from pyrevit import revit

from common import logger
```

Éviter les imports dispersés dans le code.

---

# 42. Imports inutilisés

Tout import inutilisé doit être supprimé.

Cela facilite :

- la lecture ;
- la maintenance ;
- le diagnostic ;
- la compréhension des dépendances.

---

# 43. Variables globales

Les variables globales doivent être limitées.

### À éviter

```python
CURRENT_DOCUMENT = None
ROOMS = []
RESULTS = []
```

dans plusieurs modules.

Préférer :

```python
class CalculsPieces:
    def __init__(self, document):
        self.document = document
```

---

# 44. État global

L'état global est particulièrement dangereux dans Revit.

Un outil ne doit pas dépendre implicitement :

- d'une exécution précédente ;
- d'une variable globale modifiée par un autre module ;
- d'une fenêtre précédente ;
- d'un cache non contrôlé.

L'état doit être explicite.

---

# 45. Types et contrats

Même lorsque le langage utilisé est dynamique, le développeur doit savoir précisément ce qu'une fonction reçoit et retourne.

Exemple :

```python
def calculate_area(
    rooms
):
    """
    Args:
        rooms: Liste d'éléments Revit Room.

    Returns:
        float: Surface totale en unités Revit.
    """
```

---

# 46. Valeurs `None`

Les valeurs `None` doivent être traitées explicitement.

### Mauvais

```python
value = parameter.AsString()
result = value.upper()
```

### Correct

```python
value = parameter.AsString()

if value is None:
    return ""

result = value.upper()
```

---

# 47. Paramètres Revit

Ne jamais supposer qu'un paramètre existe.

### À éviter

```python
element.LookupParameter("MonParametre").Set(value)
```

### Préférer

```python
parameter = element.LookupParameter(
    "MonParametre"
)

if parameter is None:
    logger.warning(
        "Paramètre absent : MonParametre"
    )
    return False

parameter.Set(value)
return True
```

---

# 48. Paramètres en lecture seule

Toujours vérifier qu'un paramètre peut être modifié.

```python
if parameter.IsReadOnly:
    logger.warning(
        "Paramètre en lecture seule."
    )
    return False
```

---

# 49. Unités Revit

Les unités internes Revit ne doivent pas être confondues avec les unités affichées dans l'interface.

Lorsqu'une conversion est nécessaire, elle doit être centralisée.

Exemple conceptuel :

```python
meters = unit_utils.to_meters(value)
```

Éviter de disperser des conversions arbitraires dans le code.

---

# 50. Collections Revit

Les collections retournées par Revit doivent être converties en structures Python uniquement lorsque cela apporte un bénéfice réel.

Exemple :

```python
rooms = list(
    collector.ToElements()
)
```

Cette conversion doit être justifiée si le volume d'éléments est important.

---

# 51. Traitement par lots

Pour les gros modèles, privilégier les traitements par lots.

Exemple :

```text
2000 éléments
     ↓
lot 1 : 0–499
lot 2 : 500–999
lot 3 : 1000–1499
lot 4 : 1500–1999
```

Cela peut permettre :

- une meilleure progression ;
- une meilleure gestion mémoire ;
- une meilleure expérience utilisateur.

---

# 52. Annulation utilisateur

Les opérations longues doivent, lorsque cela est techniquement possible, permettre une interruption propre.

Une interruption ne doit pas laisser le modèle dans un état incohérent.

Le principe est :

```text
Préparation
   ↓
Traitement
   ↓
Vérification
   ↓
Écriture
```

plutôt qu'une modification irréversible à chaque étape.

---

# 53. Fichiers temporaires

Les fichiers temporaires doivent :

- être créés dans un emplacement approprié ;
- avoir un nom identifiable ;
- être supprimés après utilisation ;
- ne pas polluer le projet.

Exemple :

```text
%TEMP%/
└── OutilsTAA/
```

---

# 54. Gestion des fichiers

Toujours vérifier :

- existence du fichier ;
- accès ;
- extension ;
- droits ;
- conflit de nom.

Exemple :

```python
if not os.path.exists(source_file):
    raise FileNotFoundError(
        "Fichier source introuvable."
    )
```

---

# 55. Nommage des fichiers générés

Les fichiers produits par les outils doivent avoir des noms prévisibles.

Exemple :

```text
Projet_A_Carnet_A.pdf
Projet_A_Carnet_A.dwg
Projet_A_Carnet_B.pdf
```

Le nommage doit être cohérent avec les règles propres à l'outil.

---

# 56. Sécurité

Les outils ne doivent jamais :

- supprimer massivement des fichiers sans confirmation ;
- écraser silencieusement des données importantes ;
- modifier un modèle sans avertissement lorsque l'opération est destructive ;
- exécuter du code arbitraire provenant d'une source non contrôlée.

Pour les opérations sensibles, demander une confirmation.

---

# 57. Modifications destructives

Une opération destructrice doit être identifiable.

Exemples :

```text
⚠ Cette opération va modifier 1 284 éléments.
Voulez-vous continuer ?
```

Pour les opérations particulièrement importantes :

```text
Annuler
Continuer
```

doit être préférable à une exécution automatique.

---

# 58. Principe de réversibilité

Lorsque cela est possible, les outils doivent privilégier les opérations facilement annulables avec Revit.

Une transaction Revit bien structurée permet notamment de conserver cette possibilité.

---

# 59. Documentation utilisateur

Chaque outil important doit disposer d'une documentation minimale :

```text
README.md
```

Elle doit expliquer :

1. objectif ;
2. utilisateur cible ;
3. prérequis ;
4. fonctionnement ;
5. paramètres ;
6. résultat ;
7. erreurs connues ;
8. exemples.

---

# 60. Documentation développeur

Les outils complexes doivent également documenter :

- architecture ;
- classes principales ;
- dépendances ;
- flux de données ;
- points d'entrée ;
- paramètres ;
- limitations ;
- tests.

---

# 61. Exemple de fiche outil

```markdown
# CalculsPieces

## Objectif

Calculer et reporter automatiquement des données issues
des pièces Revit.

## Entrée

- Document Revit actif
- Pièces sélectionnées ou filtrées

## Traitement

1. Collecte
2. Validation
3. Calcul
4. Agrégation
5. Écriture

## Sortie

Paramètres Revit mis à jour.

## Compatibilité

Revit 2025.4
pyRevit 5.x
```

---

# 62. Tests

Un outil ne doit pas être considéré comme terminé simplement parce qu'il fonctionne sur le poste du développeur.

Il doit être testé dans différentes situations.

### Cas nominal

```text
Modèle correct
→ résultat correct
```

### Cas vide

```text
Aucune donnée
→ message utilisateur approprié
```

### Cas incomplet

```text
Paramètre manquant
→ avertissement
```

### Cas erreur

```text
Fichier inaccessible
→ erreur contrôlée
```

---

# 63. Modèle de test minimal

Pour chaque fonctionnalité importante :

```text
[ ] Cas nominal
[ ] Aucun élément
[ ] Un élément
[ ] Plusieurs éléments
[ ] Donnée manquante
[ ] Paramètre absent
[ ] Paramètre en lecture seule
[ ] Annulation
[ ] Erreur Revit
[ ] Erreur fichier
```

---

# 64. Tests sur copie du modèle

Les développements et tests destructifs doivent être réalisés sur une copie du modèle.

Ne jamais tester une nouvelle fonction de modification massive directement sur le fichier projet de production.

---

# 65. Validation avant livraison

Avant de considérer une fonctionnalité comme terminée :

```text
[ ] Code fonctionnel
[ ] Pas d'erreur connue
[ ] Logs vérifiés
[ ] Interface testée
[ ] Cas limites testés
[ ] Modèle lourd testé si nécessaire
[ ] Documentation mise à jour
[ ] Changelog mis à jour
```

---

# 66. Git

Chaque modification significative doit être versionnée.

Un commit doit correspondre à une modification cohérente.

### Mauvais

```text
update
fix
test
changes
```

### Préférer

```text
feat(roomcalculator): ajout du calcul des surfaces cumulées
fix(publisherai): correction du regroupement par Subtitle
refactor(common): centralisation des transactions Revit
```

---

# 67. Commits

Un commit doit idéalement :

- avoir un objectif unique ;
- être suffisamment petit ;
- être compréhensible ;
- pouvoir être annulé indépendamment.

---

# 68. Branches

Le développement doit éviter de modifier directement la branche principale pour une fonctionnalité importante.

Exemple :

```text
main
 │
 ├── feature/publisherai-export-dwg
 │
 ├── feature/roomcalculator-somme
 │
 └── fix/dialog-error
```

---

# 69. Revue de code

Lorsqu'une fonctionnalité importante est développée, une revue doit vérifier :

### Architecture

```text
[ ] Bonne séparation des responsabilités
[ ] Pas de duplication
[ ] Utilisation de lib/common
```

### Code

```text
[ ] Nommage correct
[ ] Gestion des erreurs
[ ] Commentaires utiles
[ ] Pas de code mort
```

### Revit

```text
[ ] Transactions maîtrisées
[ ] Performance correcte
[ ] Paramètres vérifiés
```

---

# 70. Code mort

Le code commenté ou inutilisé ne doit pas rester indéfiniment dans le projet.

### À éviter

```python
# ancienne version
# rooms = ...
# result = ...
# ...
```

Git permet de retrouver l'historique.

Le code mort doit donc être supprimé plutôt que conservé en commentaire.

---

# 71. Debug

Les outils de debug doivent être désactivés ou contrôlés en production.

### À éviter

```python
print("ICI")
print(data)
print(element)
```

Utiliser le logger.

---

# 72. Fonctions expérimentales

Une fonctionnalité expérimentale doit être clairement identifiée.

Exemple :

```python
# EXPERIMENTAL
# Cette méthode est utilisée uniquement pour les tests IA.
```

Elle ne doit pas être présentée comme une fonctionnalité stable.

---

# 73. Intelligence artificielle

Les fonctions utilisant une IA doivent respecter les mêmes standards que le reste du logiciel.

L'IA ne doit jamais être considérée comme une source infaillible.

Les résultats doivent être :

- validés ;
- contrôlés ;
- traçables lorsque nécessaire ;
- séparés de la logique critique.

Les règles détaillées relatives au développement assisté par IA seront définies dans le chapitre **06 — AI Development Guide**.

---

# 74. Données envoyées à une IA

Avant d'envoyer des données à un service externe :

- vérifier leur nature ;
- éviter les informations sensibles ;
- limiter les données au strict nécessaire ;
- documenter le comportement.

Une fonctionnalité IA ne doit pas transmettre automatiquement l'intégralité du modèle Revit.

---

# 75. Architecture recommandée pour les outils IA

```text
Revit
  │
  ▼
Extraction contrôlée
  │
  ▼
Données minimales
  │
  ▼
Service IA
  │
  ▼
Résultat
  │
  ▼
Validation
  │
  ▼
Revit
```

La validation entre l'IA et Revit est obligatoire pour les opérations sensibles.

---

# 76. Code généré par IA

Le code produit avec l'aide d'une IA doit être considéré comme du code proposé, et non comme du code automatiquement validé.

Le développeur reste responsable de :

- sa sécurité ;
- sa compatibilité ;
- sa logique ;
- ses performances ;
- sa maintenance.

---

# 77. Principe de simplicité

Il ne faut pas sur-architecturer les outils.

### Petit outil

```text
script.py
```

peut suffire.

### Outil moyen

```text
script.py
services/
ui/
```

### Outil complexe

```text
models/
services/
repositories/
ui/
common/
```

L'architecture doit évoluer avec la complexité.

---

# 78. Principe d'évolution

Lorsqu'un outil devient complexe, il doit être refactorisé plutôt que continuer à accumuler du code dans un seul fichier.

Signes indiquant qu'un refactoring devient nécessaire :

- fichier de plusieurs centaines de lignes ;
- fonctions très longues ;
- logique métier dans l'UI ;
- nombreuses variables globales ;
- duplication ;
- difficultés à tester ;
- modifications risquant de casser plusieurs fonctions.

---

# 79. Compatibilité ascendante

Lorsqu'une API interne est utilisée par plusieurs outils, sa modification doit être faite avec prudence.

### Exemple

Si :

```python
parameter_utils.get_value()
```

est utilisé par plusieurs outils, il ne faut pas modifier brutalement son comportement sans vérifier les consommateurs.

Préférer :

```python
get_value()
```

reste compatible, tandis qu'une nouvelle fonction peut être introduite :

```python
get_typed_value()
```

---

# 80. Dépréciation

Une fonctionnalité appelée à disparaître doit être marquée comme dépréciée avant suppression.

Exemple :

```python
def old_function():
    """
    Deprecated.

    Utiliser new_function() à la place.
    """
```

La suppression doit être documentée dans le CHANGELOG.

---

# 81. Checklist développeur

Avant de soumettre une fonctionnalité :

## Architecture

- [ ] Responsabilités séparées
- [ ] Pas de duplication
- [ ] Bibliothèque commune utilisée lorsque pertinente
- [ ] Architecture adaptée à la taille de l'outil

## Code

- [ ] Nommage cohérent
- [ ] Fonctions courtes
- [ ] Classes justifiées
- [ ] Pas de variables globales inutiles
- [ ] Pas de code mort
- [ ] Imports propres

## Revit

- [ ] Accès API contrôlés
- [ ] Transactions minimales
- [ ] Paramètres vérifiés
- [ ] Gestion des unités
- [ ] Performance vérifiée

## Interface

- [ ] Messages compréhensibles
- [ ] Entrées validées
- [ ] Progression si nécessaire
- [ ] Boutons correctement activés/désactivés

## Erreurs

- [ ] Exceptions gérées
- [ ] Logs disponibles
- [ ] Aucun `except: pass`
- [ ] Messages utilisateur propres

## Documentation

- [ ] README mis à jour
- [ ] Docstrings ajoutées
- [ ] CHANGELOG mis à jour
- [ ] Limitations documentées

## Git

- [ ] Commit propre
- [ ] Message explicite
- [ ] Branche appropriée
- [ ] Code testé avant fusion

---

# 82. Checklist de revue de code

```text
┌────────────────────────────────────────┐
│        REVUE DE CODE Outils TAA        │
├────────────────────────────────────────┤
│                                        │
│ Architecture                            │
│ [ ] Responsabilité unique               │
│ [ ] Séparation UI / métier / Revit      │
│ [ ] Réutilisation common                 │
│                                        │
│ Code                                    │
│ [ ] Nommage                             │
│ [ ] Lisibilité                          │
│ [ ] Documentation                       │
│ [ ] Pas de duplication                  │
│                                        │
│ Revit                                   │
│ [ ] Transactions                        │
│ [ ] Paramètres                          │
│ [ ] Performance                         │
│                                        │
│ Robustesse                              │
│ [ ] Exceptions                          │
│ [ ] Logging                             │
│ [ ] Cas limites                         │
│                                        │
│ Interface                               │
│ [ ] Cohérence                           │
│ [ ] Validation                          │
│ [ ] Messages                            │
│                                        │
│ Documentation                           │
│ [ ] README                              │
│ [ ] CHANGELOG                           │
│                                        │
└────────────────────────────────────────┘
```

---

# 83. Standard minimal obligatoire

Même un petit script doit respecter au minimum :

```text
1. UTF-8
2. Nommage clair
3. Gestion des erreurs
4. Logging lorsque pertinent
5. Pas de code mort
6. Pas de modification Revit hors transaction
7. Validation des paramètres
8. Compatibilité Revit 2025.4
9. Compatibilité pyRevit 5.x
10. Documentation minimale
```

---

# 84. Standard pour les outils complexes

Pour un outil comme Export ou CalculsPieces, les exigences sont supérieures :

```text
Architecture modulaire
        +
Classes métier
        +
Services Revit
        +
UI WPF
        +
Logging
        +
Gestion des erreurs
        +
Tests
        +
Documentation
        +
Versioning
```

---

# 85. Principe directeur

Le standard Outils TAA peut être résumé par la règle suivante :

> **Un développeur qui découvre un outil doit pouvoir comprendre son fonctionnement sans avoir besoin de contacter son auteur.**

Le code doit donc être écrit non seulement pour être exécuté par Python, mais également pour être **lu et maintenu par un autre développeur**.

---

# 86. Résumé des règles essentielles

| Domaine | Standard |
|---|---|
| Architecture | Modulaire |
| Responsabilité | Une responsabilité par composant |
| Code | Lisible et explicite |
| Python | `snake_case` |
| Classes | `PascalCase` |
| Commentaires | Français |
| Encodage | UTF-8 |
| UI | WPF |
| API | Revit API |
| Transactions | Minimales et maîtrisées |
| Paramètres | Toujours vérifiés |
| Erreurs | Gérées et journalisées |
| Logs | Logger commun |
| Configuration | Centralisée |
| Performance | Considérée dès la conception |
| IA | Validée avant impact sur Revit |
| Git | Commits cohérents |
| Tests | Cas nominaux + cas limites |
| Documentation | Obligatoire |
| Compatibilité | Revit 2025.4 / pyRevit 5.x |

---

# 87. Conclusion

Les standards de développement Outils TAA ont pour objectif de permettre à la suite de logiciels de grandir sans devenir difficile à maintenir.

Le projet doit rester :

```text
SIMPLE
   ↓
MODULAIRE
   ↓
RÉUTILISABLE
   ↓
ROBUSTE
   ↓
MAINTENABLE
   ↓
ÉVOLUTIF
```

Les chapitres suivants s'appuieront sur ces standards.

Le chapitre **04 — UI Guidelines** définira notamment les règles précises applicables aux interfaces WPF, aux fenêtres, boutons, listes, messages, couleurs, états, progression et cohérence visuelle des outils TAA.
