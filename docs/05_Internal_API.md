# Outils TAA – Developer Handbook

## Chapitre 05 — Internal API

**Version :** 1.0  
**Statut :** Référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Langage :** Python / Revit API / WPF  
**Langue :** Français  
**Année :** 2026  

---

# 1. Objectif du document

Ce document définit l’**API interne Outils TAA**.

L’API interne constitue l’ensemble des composants communs utilisés par les différents outils de la suite :

```text
PublisherAI
RoomCalculator
Contrôle qualité
Annotation
Utilitaires
Outils BIM
Outils IA
```

L’objectif est d’éviter que chaque outil recrée ses propres fonctions pour :

- accéder au document Revit ;
- lire les paramètres ;
- écrire dans les paramètres ;
- gérer les transactions ;
- afficher des messages ;
- enregistrer les préférences ;
- écrire les logs ;
- gérer les unités ;
- afficher une progression ;
- manipuler des fichiers ;
- gérer les erreurs ;
- effectuer des opérations communes sur les éléments Revit.

L’API interne doit devenir la **fondation technique commune de Outils TAA**.

---

# 2. Principe fondamental

Un outil Outils TAA ne doit pas réimplémenter une fonction qui existe déjà dans l’API interne.

Avant de développer une fonction utilitaire, le développeur doit vérifier si une fonction équivalente existe dans :

```text
lib/common/
```

Principe :

> **Un comportement commun doit avoir une implémentation commune.**

---

# 3. Architecture générale

Structure recommandée :

```text
OutilsTAA.extension/
│
├── OutilsTAA.tab/
│   ├── Publication.panel/
│   ├── Calcul.panel/
│   ├── Controle.panel/
│   ├── Annotation.panel/
│   └── Utilitaires.panel/
│
├── lib/
│   │
│   ├── common/
│   │   ├── logger.py
│   │   ├── settings.py
│   │   ├── dialogs.py
│   │   ├── parameter_utils.py
│   │   ├── revit_utils.py
│   │   ├── transaction.py
│   │   ├── progress.py
│   │   ├── unit_utils.py
│   │   ├── file_utils.py
│   │   ├── selection_utils.py
│   │   ├── collector_utils.py
│   │   └── exceptions.py
│   │
│   ├── publication/
│   ├── calculation/
│   ├── quality/
│   └── annotation/
│
└── resources/
```

---

# 4. Rôle de `lib/common`

Le dossier :

```text
lib/common/
```

contient uniquement des composants pouvant être utilisés par plusieurs outils.

Il ne doit pas contenir de logique spécifique à :

```text
PublisherAI
```

ou :

```text
RoomCalculator
```

Exemple incorrect :

```text
lib/common/publisher_export.py
```

si ce fichier n’est utilisé que par PublisherAI.

Il devrait plutôt être placé dans :

```text
lib/publication/
```

---

# 5. API publique interne

Même s’il s’agit d’un projet interne, certaines fonctions doivent être considérées comme une API stable.

Exemple :

```python
from common.parameter_utils import get_parameter_value
```

Une fonction utilisée par de nombreux outils ne doit pas changer brutalement de signature.

Exemple :

```python
get_parameter_value(element, parameter_name)
```

ne doit pas devenir sans transition :

```python
get_parameter_value(
    document,
    element,
    parameter_definition,
    convert_units=True,
    strict_mode=False
)
```

si plusieurs outils utilisent déjà l’ancienne version.

---

# 6. API interne et implémentation privée

Les fonctions destinées aux autres modules doivent être clairement identifiables.

Convention Python :

```python
def get_parameter_value(element, parameter_name):
    pass
```

Fonction interne au module :

```python
def _convert_storage_value(parameter):
    pass
```

Le préfixe :

```text
_
```

indique qu’une fonction n’est pas destinée à être utilisée directement par d’autres modules.

---

# 7. Contrat d’une fonction

Toute fonction exposée dans l’API interne doit avoir un comportement prévisible.

Elle doit définir :

- ses entrées ;
- sa sortie ;
- les cas `None` ;
- les exceptions possibles ;
- les effets sur le modèle ;
- les transactions éventuelles.

---

# 8. Exemple de contrat

```python
def get_parameter_value(element, parameter_name):
    """
    Retourne la valeur d'un paramètre Revit.

    Args:
        element:
            Élément Revit contenant le paramètre.

        parameter_name:
            Nom du paramètre recherché.

    Returns:
        Valeur Python du paramètre.

        Retourne None si le paramètre n'existe pas.

    Raises:
        Aucun changement du modèle Revit.
    """
```

---

# 9. API de lecture et API d’écriture

Les fonctions doivent distinguer clairement :

```text
Lecture
```

et :

```text
Écriture
```

Exemple :

```python
get_parameter_value()
```

ne doit jamais modifier un élément Revit.

Une fonction effectuant une modification doit avoir un nom explicite :

```python
set_parameter_value()
```

---

# 10. Nommage des fonctions

Préfixes recommandés :

```text
get_        lecture d'une valeur
set_        modification d'une valeur
find_       recherche
collect_    collecte de plusieurs éléments
create_     création
delete_     suppression
update_     mise à jour
validate_   validation
convert_    conversion
format_     formatage
is_         test booléen
has_        vérification de présence
```

---

# 11. Valeurs booléennes

Une fonction booléenne doit être immédiatement compréhensible.

Préférer :

```python
is_parameter_writable(parameter)
```

à :

```python
check_parameter(parameter)
```

---

# 12. `logger.py`

Le module :

```text
lib/common/logger.py
```

centralise les logs de tous les outils Outils TAA.

Il doit éviter que chaque outil implémente son propre système de journalisation.

---

# 13. Interface minimale du logger

API recommandée :

```python
logger.debug(message)
logger.info(message)
logger.warning(message)
logger.error(message)
logger.exception(message)
```

---

# 14. Exemple

```python
from common.logger import get_logger

logger = get_logger("RoomCalculator")

logger.info("Démarrage du calcul")
```

---

# 15. Création d’un logger

API recommandée :

```python
def get_logger(tool_name):
    """
    Retourne un logger configuré pour un outil Outils TAA.
    """
```

Exemple :

```python
logger = get_logger("PublisherAI")
```

---

# 16. Format des logs

Format recommandé :

```text
2026-09-03 09:30:22
INFO
PublisherAI
Début de publication
```

ou sous forme compacte :

```text
2026-09-03 09:30:22 | INFO | PublisherAI | Début de publication
```

---

# 17. Informations à logger

Les logs peuvent contenir :

```text
Nom de l'outil
Version
Projet Revit
Étape exécutée
Nombre d'éléments
Durée
Erreur
Stack trace
```

Éviter d’enregistrer des informations personnelles non nécessaires.

---

# 18. `exceptions.py`

Les exceptions métier communes doivent être définies dans :

```text
lib/common/exceptions.py
```

---

# 19. Hiérarchie recommandée

```python
class OutilsTAAError(Exception):
    """Exception de base Outils TAA."""
    pass


class ValidationError(OutilsTAAError):
    """Erreur de validation utilisateur."""
    pass


class ParameterNotFoundError(OutilsTAAError):
    """Paramètre Revit introuvable."""
    pass


class ParameterReadOnlyError(OutilsTAAError):
    """Paramètre Revit non modifiable."""
    pass


class RevitOperationError(OutilsTAAError):
    """Erreur lors d'une opération Revit."""
    pass


class ExportError(OutilsTAAError):
    """Erreur durant un export."""
    pass
```

---

# 20. Pourquoi utiliser des exceptions métier

Éviter :

```python
raise Exception("Erreur")
```

Préférer :

```python
raise ParameterReadOnlyError(
    "Le paramètre '{}' est en lecture seule.".format(parameter_name)
)
```

Cela facilite :

- le debug ;
- les messages utilisateur ;
- les logs ;
- les tests ;
- la maintenance.

---

# 21. `dialogs.py`

Le module :

```text
lib/common/dialogs.py
```

centralise les messages utilisateur simples.

---

# 22. API recommandée

```python
show_info()
show_warning()
show_error()
ask_confirmation()
```

---

# 23. Exemple

```python
from common.dialogs import show_warning

show_warning(
    title="RoomCalculator",
    message="Aucune pièce n'a été sélectionnée."
)
```

---

# 24. Confirmation

Exemple :

```python
confirmed = ask_confirmation(
    title="PublisherAI",
    message="248 feuilles vont être publiées.\nContinuer ?"
)

if not confirmed:
    return
```

---

# 25. Dialogues métier et WPF

Les fenêtres complexes restent développées en WPF.

`dialogs.py` est réservé aux interactions simples :

```text
Information
Erreur
Avertissement
Confirmation
```

Il ne doit pas remplacer une véritable interface métier.

---

# 26. `settings.py`

Le module :

```text
lib/common/settings.py
```

centralise la gestion des préférences persistantes.

---

# 27. Interface recommandée

```python
get_setting()
set_setting()
remove_setting()
load_settings()
save_settings()
```

---

# 28. Exemple

```python
last_folder = get_setting(
    tool="PublisherAI",
    key="last_export_folder",
    default=None
)
```

---

# 29. Enregistrement

```python
set_setting(
    tool="PublisherAI",
    key="last_export_folder",
    value=export_folder
)
```

---

# 30. Namespace par outil

Chaque outil doit disposer de son propre espace.

Exemple :

```text
PublisherAI.last_export_folder

PublisherAI.export_pdf

RoomCalculator.last_source_parameter

RoomCalculator.last_target_parameter
```

Éviter :

```text
last_folder
```

sans contexte.

---

# 31. Configuration utilisateur et projet

Il faut distinguer :

```text
settings utilisateur
```

et :

```text
settings projet
```

Exemple utilisateur :

```text
Dernier dossier ouvert
Taille de fenêtre
Options d'affichage
```

Exemple projet :

```text
Nom du paramètre utilisé comme carnet
Configuration d'export spécifique
Mapping métier
```

---

# 32. `transaction.py`

Le module :

```text
lib/common/transaction.py
```

centralise les transactions Revit lorsque cela apporte une valeur réelle.

---

# 33. Principe

Les transactions doivent être :

- explicites ;
- courtes ;
- contrôlées ;
- limitées aux écritures.

---

# 34. Wrapper recommandé

Exemple conceptuel :

```python
with taa_transaction(doc, "RoomCalculator - Mise à jour"):
    update_rooms()
```

---

# 35. Implémentation possible

```python
from Autodesk.Revit.DB import Transaction


class taa_transaction(object):

    def __init__(self, doc, name):
        self.doc = doc
        self.name = name
        self.transaction = None

    def __enter__(self):
        self.transaction = Transaction(self.doc, self.name)
        self.transaction.Start()
        return self.transaction

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None:
            self.transaction.Commit()
        else:
            self.transaction.RollBack()

        return False
```

Le code réel doit rester compatible avec l’environnement Python utilisé par pyRevit.

---

# 36. Transaction native pyRevit

Si pyRevit fournit déjà un wrapper répondant correctement aux besoins, il est préférable de l’utiliser plutôt que de reconstruire inutilement un système complet.

L’API Outils TAA peut éventuellement encapsuler ce wrapper afin de conserver une interface stable.

---

# 37. Pas de transaction implicite

Une fonction générique telle que :

```python
set_parameter_value()
```

ne devrait généralement pas créer automatiquement une transaction.

Le niveau appelant doit contrôler la transaction.

Exemple :

```python
with taa_transaction(doc, "Mise à jour des pièces"):

    for room in rooms:
        set_parameter_value(
            room,
            "Surface calculée",
            value
        )
```

---

# 38. Pourquoi éviter les transactions implicites

Cela évite :

```text
100 pièces
=
100 transactions
```

et permet :

```text
100 pièces
=
1 transaction
```

---

# 39. `parameter_utils.py`

Le module :

```text
lib/common/parameter_utils.py
```

centralise les opérations fréquentes sur les paramètres Revit.

---

# 40. API minimale recommandée

```python
get_parameter()
get_parameter_value()
set_parameter_value()

has_parameter()

is_parameter_writable()

get_parameter_storage_type()

get_parameter_display_value()

collect_parameters()

find_parameter_by_guid()
```

---

# 41. `get_parameter`

Signature possible :

```python
def get_parameter(element, parameter_name):
    """
    Retourne le Parameter correspondant au nom demandé.

    Retourne None si aucun paramètre n'est trouvé.
    """
```

---

# 42. Exemple

```python
parameter = get_parameter(
    room,
    "Commentaires"
)

if parameter is None:
    ...
```

---

# 43. Paramètres BuiltIn

Lorsque cela est pertinent, l’API doit pouvoir travailler avec :

```text
BuiltInParameter
```

et éviter de dépendre uniquement du nom affiché dans Revit.

---

# 44. API possible

```python
get_builtin_parameter(
    element,
    built_in_parameter
)
```

---

# 45. Paramètres partagés

Pour les paramètres partagés, privilégier l’identification par :

```text
GUID
```

lorsque le GUID est connu et stable.

Exemple :

```python
find_parameter_by_guid(element, parameter_guid)
```

---

# 46. Risque de `LookupParameter`

L’utilisation de :

```python
element.LookupParameter("Nom")
```

est pratique mais peut être ambiguë.

Des paramètres différents peuvent avoir le même nom.

L’API interne doit privilégier, lorsque possible :

```text
BuiltInParameter
GUID
Definition
```

selon le contexte.

---

# 47. Lecture des valeurs

`get_parameter_value()` doit convertir la valeur Revit vers une valeur Python cohérente selon :

```text
StorageType.Integer
StorageType.Double
StorageType.String
StorageType.ElementId
```

---

# 48. Exemple conceptuel

```python
def get_parameter_value(parameter):

    storage_type = parameter.StorageType

    if storage_type == StorageType.String:
        return parameter.AsString()

    if storage_type == StorageType.Integer:
        return parameter.AsInteger()

    if storage_type == StorageType.Double:
        return parameter.AsDouble()

    if storage_type == StorageType.ElementId:
        return parameter.AsElementId()

    return None
```

---

# 49. Valeur brute et valeur affichée

Il faut distinguer :

```text
Raw value
```

et :

```text
Display value
```

Exemple :

```python
raw_value = get_parameter_value(parameter)
```

et :

```python
display_value = get_parameter_display_value(parameter)
```

---

# 50. Écriture des paramètres

API recommandée :

```python
set_parameter_value(
    element,
    parameter,
    value
)
```

La fonction doit :

1. vérifier l’existence ;
2. vérifier `IsReadOnly` ;
3. vérifier le type de stockage ;
4. effectuer l’écriture ;
5. lever une exception explicite en cas d’échec.

---

# 51. `unit_utils.py`

Le module :

```text
lib/common/unit_utils.py
```

centralise les conversions d’unités.

---

# 52. Pourquoi centraliser les unités

Revit travaille avec des unités internes.

Les outils ne doivent pas disperser des conversions telles que :

```python
value * 0.3048
```

dans tout le projet.

Cela rend le code fragile et difficile à comprendre.

---

# 53. API recommandée

```python
to_internal_units()
from_internal_units()
format_unit()
```

---

# 54. Utiliser l’API Revit

Les conversions doivent utiliser les fonctions prévues par Revit lorsque possible.

Exemple conceptuel :

```python
UnitUtils.ConvertToInternalUnits()
UnitUtils.ConvertFromInternalUnits()
```

---

# 55. Exemple

```python
surface_m2 = from_internal_units(
    raw_surface,
    unit_type="area"
)
```

L’implémentation réelle doit s’appuyer sur les identifiants d’unités compatibles Revit 2025.4.

---

# 56. `revit_utils.py`

Le module :

```text
lib/common/revit_utils.py
```

contient les opérations Revit générales qui ne correspondent pas à une catégorie plus spécifique.

---

# 57. API possible

```python
get_active_document()
get_active_view()
get_project_information()
get_element_name()
get_element_type()
get_element_by_id()
is_valid_element()
```

---

# 58. Éviter le fichier fourre-tout

`revit_utils.py` ne doit pas devenir un fichier contenant plusieurs milliers de lignes.

Lorsque certaines fonctions constituent un domaine cohérent, créer un module spécifique.

Exemple :

```text
selection_utils.py
collector_utils.py
view_utils.py
sheet_utils.py
family_utils.py
```

---

# 59. `collector_utils.py`

Le module :

```text
lib/common/collector_utils.py
```

centralise les recherches standards dans Revit.

---

# 60. Fonctions possibles

```python
collect_by_category()
collect_by_class()
collect_rooms()
collect_sheets()
collect_views()
collect_levels()
collect_families()
collect_types()
```

---

# 61. Exemple

```python
rooms = collect_rooms(
    doc,
    placed_only=True
)
```

plutôt que de recopier le même `FilteredElementCollector` dans plusieurs outils.

---

# 62. Paramètres de collecte

Les fonctions doivent permettre de préciser les critères importants.

Exemple :

```python
collect_rooms(
    doc,
    placed_only=True,
    phase=None
)
```

Éviter toutefois les fonctions possédant vingt paramètres optionnels.

---

# 63. Collector spécialisé ou générique

Une API générique peut exister :

```python
collect_by_category(doc, category)
```

mais les fonctions métier courantes restent utiles :

```python
collect_rooms(doc)
```

car elles rendent le code appelant plus clair.

---

# 64. `selection_utils.py`

Le module :

```text
lib/common/selection_utils.py
```

centralise la sélection des éléments dans Revit.

---

# 65. Fonctions possibles

```python
get_selected_elements()
get_selected_ids()
set_selection()
pick_element()
pick_elements()
```

---

# 66. Exemple

```python
rooms = get_selected_elements(
    uidoc,
    category=BuiltInCategory.OST_Rooms
)
```

---

# 67. Annulation utilisateur

Une annulation lors de :

```text
PickObject
```

ne doit pas être traitée comme une erreur système.

L’API doit pouvoir retourner proprement :

```python
None
```

ou lever une exception spécifique connue.

---

# 68. `progress.py`

Le module :

```text
lib/common/progress.py
```

centralise les comportements liés à la progression.

---

# 69. Fonctions ou classes possibles

```python
ProgressReporter
ProgressState
calculate_progress()
```

---

# 70. Exemple

```python
progress = ProgressReporter(total=len(elements))

for index, element in enumerate(elements):

    process(element)

    progress.update(
        current=index + 1,
        message=element.Name
    )
```

---

# 71. Séparer progression et interface

Le code métier ne doit pas dépendre directement d’un contrôle WPF.

Éviter :

```python
progress_bar.Value = 50
```

dans le service métier.

Préférer :

```python
progress_callback(50)
```

---

# 72. Callback de progression

Exemple :

```python
def calculate_rooms(
    rooms,
    progress_callback=None
):

    total = len(rooms)

    for index, room in enumerate(rooms):

        process_room(room)

        if progress_callback:

            progress_callback(
                index + 1,
                total
            )
```

---

# 73. Avantage

Cette approche permet d’utiliser le même service depuis :

```text
WPF
console pyRevit
tests
automatisation
```

---

# 74. `file_utils.py`

Le module :

```text
lib/common/file_utils.py
```

centralise les opérations génériques liées aux fichiers.

---

# 75. Fonctions possibles

```python
ensure_directory()
sanitize_filename()
file_exists()
directory_exists()
create_temp_directory()
safe_delete()
copy_file()
move_file()
```

---

# 76. `sanitize_filename`

Une fonction commune doit nettoyer les caractères interdits dans les noms de fichiers Windows.

Exemple :

```python
filename = sanitize_filename(
    "APS : Carnet / Logements"
)
```

Résultat possible :

```text
APS - Carnet - Logements
```

---

# 77. Ne pas intégrer PublisherAI dans `file_utils`

Une fonction :

```python
merge_publisher_pdf()
```

n’a pas sa place dans :

```text
common/file_utils.py
```

car elle est spécifique au domaine Publication.

---

# 78. Domain services

Lorsque plusieurs outils partagent une logique métier spécialisée, utiliser :

```text
lib/<domain>/
```

Exemple :

```text
lib/publication/
```

---

# 79. Structure Publication

Exemple :

```text
lib/publication/
├── sheet_service.py
├── pdf_service.py
├── dwg_service.py
├── booklet_service.py
├── naming_service.py
└── publication_models.py
```

---

# 80. PublisherAI

Le script pyRevit de PublisherAI ne devrait pas contenir directement toute la logique d’export.

Il doit principalement :

```text
charger l'interface
↓
récupérer les options utilisateur
↓
appeler PublicationService
↓
afficher la progression
↓
présenter le résultat
```

---

# 81. Exemple de service

```python
class PublicationService(object):

    def __init__(
        self,
        doc,
        logger=None
    ):
        self.doc = doc
        self.logger = logger

    def publish(
        self,
        booklets,
        options,
        progress_callback=None
    ):
        pass
```

---

# 82. `PublicationOptions`

Les paramètres complexes doivent être regroupés dans des objets dédiés.

Éviter :

```python
publish(
    sheets,
    folder,
    True,
    True,
    False,
    True,
    "A3",
    "Color",
    False
)
```

Préférer :

```python
options = PublicationOptions()

options.export_pdf = True
options.export_dwg = True
options.combine_pdf = True
options.output_folder = folder
```

puis :

```python
service.publish(
    booklets,
    options
)
```

---

# 83. Data models

Pour les données internes non directement liées à Revit, utiliser de petits modèles Python.

Exemple :

```python
class Booklet(object):

    def __init__(self, name, sheets=None):

        self.name = name
        self.sheets = sheets or []
```

---

# 84. Ne pas exposer inutilement les objets Revit

Lorsque le métier n’a pas besoin de l’objet Revit complet, préférer transmettre une structure de données simple.

Exemple :

```python
RoomData
```

peut contenir :

```text
id
name
number
level
surface
```

au lieu de transmettre constamment un objet `Room`.

---

# 85. Pipeline recommandé

Pour les outils importants :

```text
Revit
↓
Repository / Collector
↓
Data Model
↓
Business Service
↓
Validation
↓
Writer Revit
```

---

# 86. Exemple RoomCalculator

Architecture possible :

```text
RoomCollector
      ↓
RoomData
      ↓
RoomCalculatorService
      ↓
CalculationResult
      ↓
RoomParameterWriter
```

---

# 87. `RoomCollector`

Responsabilité :

```text
Lire Revit
```

Il ne doit pas :

```text
calculer les résultats métier
modifier les paramètres
afficher l'interface
```

---

# 88. `RoomCalculatorService`

Responsabilité :

```text
Effectuer les calculs
```

Idéalement, cette classe doit pouvoir fonctionner sans dépendre fortement de Revit.

Cela facilite les tests.

---

# 89. `RoomParameterWriter`

Responsabilité :

```text
Écrire les résultats dans Revit
```

Cette étape utilise une transaction.

---

# 90. Principe de dépendance

La logique métier ne doit pas dépendre de l’interface.

Correct :

```text
WPF
↓
Business Service
↓
Revit
```

Incorrect :

```text
Business Service
↓
MainWindow.xaml
```

---

# 91. Résultats d’opération

Pour les opérations complexes, éviter de retourner uniquement :

```python
True
```

ou :

```python
False
```

Créer un objet résultat.

---

# 92. `OperationResult`

Exemple :

```python
class OperationResult(object):

    def __init__(self):

        self.success = True

        self.processed = 0
        self.skipped = 0
        self.errors = []

        self.message = None
```

---

# 93. Exemple de résultat

```python
result = PublicationResult()

result.exported_sheets = 42
result.failed_sheets = 2
result.pdf_files = [...]
result.dwg_files = [...]
```

L’interface peut ensuite présenter un résumé clair.

---

# 94. Validation

La validation doit idéalement être séparée de l’exécution.

Exemple :

```python
errors = service.validate(options)

if errors:
    display_errors(errors)
    return

service.execute(options)
```

---

# 95. API de validation

Convention recommandée :

```python
validate()
```

retourne :

```text
liste d'erreurs
```

ou :

```text
objet ValidationResult
```

---

# 96. `ValidationResult`

Exemple :

```python
class ValidationResult(object):

    def __init__(self):

        self.errors = []
        self.warnings = []

    @property
    def is_valid(self):
        return not self.errors
```

---

# 97. Erreur et avertissement

Différence :

```text
Error
=
empêche l'opération
```

```text
Warning
=
l'opération reste possible
```

---

# 98. Accès au document

Éviter que les services récupèrent eux-mêmes systématiquement :

```python
__revit__.ActiveUIDocument.Document
```

Le document doit généralement être injecté.

Préférer :

```python
service = RoomService(doc)
```

---

# 99. Pourquoi injecter `doc`

Cela facilite :

- les tests ;
- la compréhension ;
- la réutilisation ;
- le découplage ;
- la maintenance.

---

# 100. `uidoc`

Le `UIDocument` doit seulement être passé aux composants nécessitant réellement une interaction avec l’interface Revit.

Exemple :

```text
sélection
zoom
PickObject
ShowElements
```

Un service de calcul n’a généralement pas besoin de `uidoc`.

---

# 101. État global

Éviter :

```python
global doc
global uidoc
global current_project
```

Les dépendances doivent être transmises explicitement.

---

# 102. Dependency injection légère

Outils TAA n’a pas besoin d’un framework complexe de dependency injection.

La simple injection via constructeur est suffisante.

Exemple :

```python
class RoomService(object):

    def __init__(
        self,
        doc,
        logger
    ):
        self.doc = doc
        self.logger = logger
```

---

# 103. Services partagés

Un service ne doit pas créer arbitrairement ses dépendances internes.

Éviter :

```python
class PublisherService(object):

    def __init__(self):
        self.logger = CustomLogger()
```

Préférer :

```python
class PublisherService(object):

    def __init__(self, logger=None):
        self.logger = logger or get_logger(
            "PublisherAI"
        )
```

---

# 104. API synchrone

Par défaut, les services Outils TAA sont considérés comme synchrones.

L’API Revit impose des contraintes fortes concernant les threads.

Ne jamais appeler arbitrairement l’API Revit depuis un thread secondaire.

---

# 105. Multithreading

Le multithreading peut éventuellement être utilisé pour du traitement ne touchant pas directement à Revit.

Exemple :

```text
calcul Python pur
traitement de données
certaines opérations fichiers
```

mais uniquement si :

- cela apporte un gain réel ;
- la sécurité est assurée ;
- la complexité reste maîtrisée.

---

# 106. ExternalEvent

Pour les interfaces WPF non modales nécessitant une interaction Revit, l’utilisation de :

```text
ExternalEvent
```

peut être nécessaire.

Cette logique doit être encapsulée et documentée.

---

# 107. API Revit et UI

Principe :

> Toute opération modifiant Revit doit s’exécuter dans un contexte autorisé par l’API Revit.

L’interface WPF ne doit jamais contourner cette règle.

---

# 108. Événements

Les événements WPF doivent appeler :

```text
ViewModel
```

ou :

```text
Controller
```

qui appelle ensuite les services.

Éviter les centaines de lignes de logique dans :

```python
button_click()
```

---

# 109. API UI commune

À terme, certains composants WPF communs peuvent disposer d’une API Python stable.

Exemple :

```python
show_progress_dialog()
show_validation_summary()
show_error_dialog()
```

---

# 110. API et ressources graphiques

Les composants UI doivent utiliser les ressources définies par :

```text
Colors.xaml
Buttons.xaml
Inputs.xaml
Typography.xaml
Theme.xaml
```

La logique Python ne doit généralement pas définir les couleurs.

---

# 111. Constantes

Les valeurs constantes partagées doivent être centralisées.

Exemple :

```text
lib/common/constants.py
```

---

# 112. Exemple

```python
APPLICATION_NAME = "Outils TAA"

SUPPORTED_REVIT_VERSION = 2025

DEFAULT_LOG_LEVEL = "INFO"
```

---

# 113. Constantes métier

Une constante spécifique à PublisherAI ne doit pas être placée dans `common`.

Exemple :

```python
DEFAULT_DWG_EXPORT_SETUP
```

pourrait appartenir à :

```text
publication/constants.py
```

---

# 114. Version de l’API interne

Il est recommandé de versionner progressivement l’API commune.

Exemple :

```python
INTERNAL_API_VERSION = "1.0"
```

Cela facilite les futures migrations.

---

# 115. Compatibilité ascendante

Lorsqu’une fonction commune évolue, les outils existants doivent continuer à fonctionner autant que raisonnablement possible.

---

# 116. Dépréciation

Une fonction obsolète ne doit pas nécessairement être supprimée immédiatement.

Exemple :

```python
def old_get_parameter(...):

    logger.warning(
        "old_get_parameter est obsolète. "
        "Utiliser get_parameter."
    )

    return get_parameter(...)
```

---

# 117. Étapes de dépréciation

Processus recommandé :

```text
Version N
Nouvelle fonction introduite

Version N+1
Ancienne fonction marquée obsolète

Version N+2
Migration des outils

Version majeure suivante
Suppression possible
```

---

# 118. Changement de signature

Éviter :

```python
get_parameter(element, name)
```

qui devient brutalement :

```python
get_parameter(doc, category, element, name)
```

Créer éventuellement une nouvelle fonction.

---

# 119. Renommage

Lorsqu’une fonction doit être renommée :

```python
def old_name(*args, **kwargs):
    return new_name(*args, **kwargs)
```

peut temporairement maintenir la compatibilité.

---

# 120. Documentation de l’API

Toute fonction commune importante doit disposer d’une docstring.

Exemple :

```python
def collect_rooms(doc, placed_only=True):
    """
    Retourne les pièces du document.

    Args:
        doc:
            Document Revit.

        placed_only:
            Si True, ignore les pièces non placées.

    Returns:
        list:
            Liste de Room.

    Raises:
        RevitOperationError:
            Si la collecte échoue.
    """
```

---

# 121. Documentation minimale

Une API doit préciser :

```text
Description
Arguments
Valeur retournée
Exceptions
Effets de bord
```

---

# 122. Effets de bord

Une fonction effectuant une modification doit l’indiquer clairement.

Exemple :

```text
Modifie les paramètres des pièces.
Nécessite une transaction Revit active.
```

---

# 123. Fonctions pures

Lorsque cela est possible, les calculs doivent être implémentés avec des fonctions pures.

Exemple :

```python
def calculate_total(values):
    return sum(values)
```

Cette fonction :

- ne dépend pas de Revit ;
- ne dépend pas de l’UI ;
- ne modifie aucun état ;
- est facilement testable.

---

# 124. Tester l’API commune

Les fonctions communes sont particulièrement importantes à tester car une régression peut affecter plusieurs outils simultanément.

Priorité de tests :

```text
parameter_utils
unit_utils
file_utils
settings
services de calcul
```

---

# 125. Tests de paramètres

Cas à tester :

```text
Paramètre absent
Paramètre vide
Paramètre texte
Paramètre entier
Paramètre double
ElementId
Paramètre en lecture seule
Paramètre partagé
```

---

# 126. Tests d’unités

Cas à vérifier :

```text
Longueur
Surface
Volume
Angle
Valeurs nulles
Valeurs négatives
```

---

# 127. Mock des données

La logique métier doit idéalement pouvoir être testée avec des données simples sans lancer Revit.

Exemple :

```python
rooms = [
    RoomData(surface=10),
    RoomData(surface=15),
    RoomData(surface=20),
]

result = calculate_total_surface(rooms)

assert result == 45
```

---

# 128. Logging des erreurs API

Une exception ne doit pas être loggée cinq fois à différents niveaux.

Principe :

```text
le niveau qui sait gérer l'erreur
=
responsable du log principal
```

---

# 129. Exemple de propagation

```text
parameter_utils
↓
lève ParameterReadOnlyError

RoomParameterWriter
↓
ajoute le contexte métier

RoomCalculator
↓
log l'erreur

UI
↓
affiche un message utilisateur
```

---

# 130. Ne pas masquer les erreurs

Éviter :

```python
try:
    ...
except Exception:
    return None
```

Cela masque les problèmes réels.

---

# 131. Erreurs attendues

Une erreur métier attendue peut être traitée spécifiquement.

```python
try:

    set_parameter_value(
        room,
        parameter,
        value
    )

except ParameterReadOnlyError as error:

    result.errors.append(str(error))
```

---

# 132. `None`

Le comportement face à `None` doit être défini clairement.

Une fonction ne doit pas retourner arbitrairement :

```text
None
False
[]
""
```

pour représenter le même type d’échec.

---

# 133. Collections

Les fonctions retournant plusieurs éléments doivent généralement retourner une liste vide :

```python
[]
```

lorsqu’aucun élément n’existe.

Préférer :

```python
rooms = []
```

à :

```python
rooms = None
```

---

# 134. Objet absent

Pour la recherche d’un élément unique :

```python
find_view_by_name()
```

peut retourner :

```python
None
```

si aucune vue n’est trouvée.

---

# 135. Exceptions ou `None`

Utiliser `None` pour une absence normale.

Exemple :

```text
paramètre optionnel absent
```

Utiliser une exception lorsque l’absence empêche la fonction de remplir son contrat.

Exemple :

```text
paramètre obligatoire absent
```

---

# 136. Mutation des arguments

Éviter qu’une fonction modifie silencieusement une liste reçue en argument.

Éviter :

```python
def filter_rooms(rooms):
    rooms.remove(...)
```

Préférer :

```python
def filter_rooms(rooms):
    return [
        room
        for room in rooms
        if ...
    ]
```

---

# 137. API des fichiers

Les fonctions manipulant les fichiers doivent utiliser les objets standards Python lorsque possible :

```text
string path
list
dict
```

Éviter de créer des abstractions complexes sans nécessité.

---

# 138. Chemins

Les chemins doivent être construits avec les fonctions standards adaptées plutôt que par concaténation manuelle.

Éviter :

```python
folder + "\\" + filename
```

Préférer une fonction dédiée de gestion de chemin.

---

# 139. Nom des fichiers exportés

La logique de nommage doit être centralisée pour les outils de publication.

Exemple :

```python
build_export_filename()
```

Cela garantit une convention homogène.

---

# 140. API spécifique aux feuilles

Un module :

```text
lib/publication/sheet_service.py
```

peut exposer :

```python
collect_publishable_sheets()
group_sheets_by_booklet()
sort_sheets()
get_sheet_booklet()
```

---

# 141. Carnets PublisherAI

Le concept de carnet doit être encapsulé.

Éviter que chaque partie de PublisherAI lise directement le paramètre Revit utilisé comme carnet.

Préférer :

```python
booklet_service.get_booklet_name(sheet)
```

---

# 142. Avantage

Si demain le carnet n’est plus défini par :

```text
Subtitle
```

mais par un autre paramètre, seule l’implémentation du service doit être modifiée.

---

# 143. Abstraction des exports

PublisherAI peut définir une interface commune :

```python
class Exporter(object):

    def export(self, sheets, output_folder):
        raise NotImplementedError
```

Implémentations :

```python
PdfExporter
DwgExporter
```

---

# 144. Avantage

Le service principal peut orchestrer :

```text
PDF
DWG
```

sans connaître tous les détails techniques de chaque exporteur.

---

# 145. Exemple

```python
exporters = []

if options.export_pdf:
    exporters.append(PdfExporter(doc))

if options.export_dwg:
    exporters.append(DwgExporter(doc))

for exporter in exporters:
    exporter.export(...)
```

---

# 146. API native Revit

Lorsque Revit propose une API native fiable, elle doit être privilégiée.

Exemple :

```text
export PDF natif Revit
```

plutôt que d’introduire une dépendance externe sans nécessité.

---

# 147. Encapsulation de l’API Autodesk

Lorsque certaines parties de l’API Revit sont particulièrement complexes ou susceptibles d’évoluer, les encapsuler.

Exemple :

```python
RevitPdfExporter
```

Ainsi le reste du système dépend de :

```python
PdfExporter
```

et non directement de tous les détails Autodesk.

---

# 148. Couche Autodesk

Architecture possible :

```text
Business
↓
Outils TAA API
↓
Adapter Revit
↓
Autodesk Revit API
```

---

# 149. Adapter pattern

Exemple :

```python
class RevitParameterAdapter(object):

    def get_value(self, element, parameter):
        ...

    def set_value(self, element, parameter, value):
        ...
```

À utiliser seulement lorsque cette abstraction apporte une réelle valeur.

---

# 150. Ne pas surarchitecturer

L’API interne doit simplifier le développement.

Elle ne doit pas devenir plus complexe que Revit lui-même.

Éviter les couches inutiles telles que :

```text
Interface
↓
Controller
↓
Manager
↓
Service
↓
Provider
↓
Repository
↓
Adapter
↓
Helper
↓
Revit
```

pour une opération simple.

---

# 151. Architecture proportionnée

Pour un outil simple :

```text
UI
↓
Service
↓
common
↓
Revit
```

peut suffire.

Pour un outil complexe :

```text
UI
↓
ViewModel
↓
Business Services
↓
Repositories / Adapters
↓
common
↓
Revit API
```

---

# 152. Dépendances entre modules

Le dossier :

```text
common/
```

ne doit jamais dépendre de :

```text
publication/
calculation/
quality/
annotation/
```

---

# 153. Direction des dépendances

Correct :

```text
publication
      ↓
    common
```

Incorrect :

```text
common
  ↓
publication
```

---

# 154. Dépendances inter-domaines

Éviter également :

```text
RoomCalculator
↓
PublisherAI
```

Les deux outils doivent dépendre de services communs lorsque nécessaire.

---

# 155. Exemple

Si PublisherAI et RoomCalculator ont besoin d’une fonction de lecture de paramètres :

Incorrect :

```text
RoomCalculator
↓
PublisherAI.parameter_reader
```

Correct :

```text
PublisherAI ─┐
             ↓
       parameter_utils
             ↑
RoomCalculator ─┘
```

---

# 156. Imports

Préférer des imports explicites.

Exemple :

```python
from common.parameter_utils import (
    get_parameter,
    get_parameter_value,
)
```

Éviter :

```python
from common.parameter_utils import *
```

---

# 157. Import de modules lourds

Ne pas charger inutilement des modules complexes au démarrage de tous les outils.

Un module commun doit rester léger autant que possible.

---

# 158. Dépendances circulaires

Architecture interdite :

```text
service_a
↓
service_b
↓
service_a
```

Si cela apparaît, les responsabilités doivent être réévaluées.

---

# 159. Version Revit

Les différences d’API entre versions doivent être isolées autant que possible.

Exemple futur :

```text
lib/compat/
```

---

# 160. Module de compatibilité

Structure potentielle :

```text
lib/compat/
├── revit_version.py
├── units.py
├── pdf_export.py
└── api_features.py
```

À introduire uniquement lorsque plusieurs versions de Revit doivent réellement être supportées.

---

# 161. Cible actuelle

La cible de référence reste :

```text
Autodesk Revit 2025.4
pyRevit 5.x
```

Il n’est donc pas nécessaire de complexifier immédiatement toute l’API pour supporter des versions anciennes.

---

# 162. Feature detection

Lorsque cela est possible, vérifier qu’une fonctionnalité existe plutôt que de multiplier les tests sur le numéro de version.

Mais pour certaines évolutions Autodesk, un contrôle explicite de version peut être nécessaire.

---

# 163. API IA

Les futurs outils IA doivent également passer par une couche interne.

Éviter :

```text
UI
↓
API IA externe directement
```

Préférer :

```text
UI
↓
AIService
↓
AIProvider
↓
API externe
```

---

# 164. `AIService`

Responsabilités possibles :

```text
préparer les données
anonymiser si nécessaire
construire le prompt
appeler le provider
valider la réponse
transformer le résultat
```

---

# 165. Provider IA

Exemple :

```python
class AIProvider(object):

    def complete(self, request):
        raise NotImplementedError
```

Implémentations possibles :

```text
MistralProvider
OpenAIProvider
LocalProvider
```

Ainsi le métier ne dépend pas directement d’un fournisseur particulier.

---

# 166. Données IA

Une fonction IA ne doit pas recevoir automatiquement l’intégralité du modèle Revit.

L’API doit sélectionner uniquement les données nécessaires au traitement.

---

# 167. Réponse IA

Une réponse générée par IA ne doit pas être appliquée automatiquement au modèle lorsqu’elle peut avoir un impact significatif.

Pipeline recommandé :

```text
IA
↓
Validation
↓
Aperçu
↓
Confirmation utilisateur
↓
Transaction Revit
```

---

# 168. API de contrôle qualité

Les futurs outils de contrôle peuvent adopter une structure commune :

```python
class CheckResult(object):

    def __init__(
        self,
        element_id=None,
        status=None,
        message=None
    ):
        self.element_id = element_id
        self.status = status
        self.message = message
```

---

# 169. États communs

Exemple :

```text
PASS
WARNING
ERROR
SKIPPED
```

Ces états doivent être normalisés pour pouvoir créer une UI commune de contrôle qualité.

---

# 170. `QualityCheck`

Interface possible :

```python
class QualityCheck(object):

    name = None
    description = None

    def run(self, doc):
        raise NotImplementedError
```

---

# 171. Exemple

```python
class RoomNameCheck(QualityCheck):

    name = "Nom des pièces"

    def run(self, doc):

        results = []

        ...

        return results
```

---

# 172. Avantage de l’API Quality

Une seule interface pourra ensuite exécuter :

```text
Contrôle des pièces
Contrôle des vues
Contrôle des feuilles
Contrôle des familles
Contrôle des paramètres
```

sans recréer une UI pour chaque contrôle.

---

# 173. API d’annotation

Les outils d’annotation peuvent également partager des services :

```text
TagService
TextService
DimensionService
ViewAnnotationService
```

Toutefois, ces services ne doivent être créés qu’en cas de besoin réel.

---

# 174. Cache

Un cache peut être utilisé pour éviter les recherches Revit répétitives.

Exemple :

```python
parameter_cache = {}
```

mais son cycle de vie doit rester clairement défini.

---

# 175. Cache et Revit

Attention :

le modèle Revit peut évoluer pendant l’utilisation de l’outil.

Un cache contenant des données Revit peut devenir obsolète.

Il doit donc être :

- limité ;
- invalidé ;
- recréé lorsque nécessaire.

---

# 176. Ne pas conserver les éléments Revit indéfiniment

Une fenêtre persistante ne doit pas nécessairement conserver des centaines d’objets API Revit pendant toute sa durée de vie.

Selon les cas, préférer :

```text
ElementId
```

puis récupérer l’élément au moment nécessaire.

---

# 177. ElementId

L’utilisation de :

```text
ElementId
```

est recommandée comme identifiant interne pour relier les résultats aux éléments Revit.

---

# 178. Identifiants persistants

Pour certaines opérations nécessitant une identification persistante, considérer :

```text
UniqueId
```

plutôt que l’ElementId.

Le choix dépend du besoin.

---

# 179. API et performances

Toute fonction commune exécutée fréquemment doit éviter :

- les collectors complets répétés ;
- les accès paramètre inutiles ;
- les conversions répétitives ;
- les transactions répétées ;
- les appels UI excessifs.

---

# 180. Bulk operations

Lorsque plusieurs éléments sont traités :

préférer :

```python
set_parameter_values(elements, parameter, values)
```

ou une boucle dans une transaction unique

à plusieurs appels ouvrant chacun leur propre contexte.

---

# 181. Batching

Pour les opérations très importantes, un traitement par lot peut être envisagé.

Exemple :

```text
5000 éléments
↓
lots de 250
```

mais seulement lorsqu’il apporte un bénéfice mesurable.

---

# 182. Métriques

Les services importants peuvent éventuellement exposer :

```text
duration
processed_count
failed_count
```

dans leur résultat.

Cela facilite :

- les logs ;
- le diagnostic ;
- l’amélioration des performances.

---

# 183. API stable vs expérimental

Les fonctions stables vivent dans :

```text
lib/common/
```

Les fonctions expérimentales peuvent temporairement être isolées :

```text
lib/experimental/
```

---

# 184. Passage en stable

Une fonction expérimentale peut entrer dans l’API commune lorsqu’elle est :

- utilisée réellement ;
- testée ;
- documentée ;
- suffisamment générique ;
- considérée stable.

---

# 185. Fonction générique

Une fonction ne doit pas être ajoutée à `common` uniquement parce qu’elle pourrait éventuellement servir un jour.

Règle :

> Une abstraction commune doit répondre à un besoin réel et répété.

---

# 186. Critère de mutualisation

Une fonction mérite généralement d’être déplacée dans `common` lorsqu’elle :

```text
est utilisée par au moins deux outils
```

ou représente une règle technique fondamentale qui doit rester centralisée.

Exemple :

```text
transaction
logging
settings
unit conversion
```

---

# 187. Checklist avant création d’une API

Avant d’ajouter une fonction dans `lib/common` :

```text
☐ Cette fonction est-elle réellement générique ?

☐ Existe-t-elle déjà ailleurs ?

☐ Peut-elle être utilisée sans connaître un outil spécifique ?

☐ Son nom décrit-il clairement son comportement ?

☐ Sa signature est-elle simple ?

☐ Son comportement avec None est-il défini ?

☐ Les exceptions sont-elles définies ?

☐ Modifie-t-elle Revit ?

☐ Nécessite-t-elle une transaction ?

☐ Est-elle testable ?
```

---

# 188. Checklist d’une fonction publique

Toute fonction publique importante doit vérifier :

```text
☐ Nom explicite

☐ Docstring

☐ Arguments documentés

☐ Type de retour cohérent

☐ Gestion des erreurs

☐ Aucun effet de bord caché

☐ Pas de dépendance UI inutile

☐ Pas de dépendance métier spécifique dans common

☐ Logging approprié

☐ Compatibilité Revit 2025.4
```

---

# 189. Checklist d’un service métier

```text
☐ Une responsabilité principale

☐ Dépendances injectées

☐ Pas de logique WPF

☐ Pas d'accès global à __revit__ sans nécessité

☐ Validation séparée si utile

☐ Résultat structuré pour les opérations complexes

☐ Erreurs métier explicites

☐ API Revit isolée autant que raisonnable

☐ Transactions contrôlées

☐ Progression possible par callback
```

---

# 190. API minimale cible — version 1.0

La première version de `lib/common` devrait idéalement contenir :

```text
common/
│
├── __init__.py
│
├── constants.py
│
├── exceptions.py
│
├── logger.py
│
├── dialogs.py
│
├── settings.py
│
├── transaction.py
│
├── parameter_utils.py
│
├── unit_utils.py
│
├── collector_utils.py
│
├── selection_utils.py
│
├── revit_utils.py
│
├── file_utils.py
└── progress.py
```

---

# 191. Fonctions prioritaires — `parameter_utils.py`

Version initiale :

```text
get_parameter
get_parameter_value
get_parameter_display_value
set_parameter_value
has_parameter
is_parameter_writable
find_parameter_by_guid
```

---

# 192. Fonctions prioritaires — `collector_utils.py`

```text
collect_by_category
collect_rooms
collect_sheets
collect_views
collect_levels
```

---

# 193. Fonctions prioritaires — `selection_utils.py`

```text
get_selected_elements
get_selected_ids
set_selection
```

---

# 194. Fonctions prioritaires — `file_utils.py`

```text
ensure_directory
sanitize_filename
file_exists
directory_exists
```

---

# 195. Fonctions prioritaires — `dialogs.py`

```text
show_info
show_warning
show_error
ask_confirmation
```

---

# 196. Fonctions prioritaires — `settings.py`

```text
get_setting
set_setting
load_settings
save_settings
```

---

# 197. Fonctions prioritaires — `logger.py`

```text
get_logger
```

puis interface standard :

```text
debug
info
warning
error
exception
```

---

# 198. Fonctions prioritaires — `transaction.py`

```text
taa_transaction
```

ou un wrapper équivalent basé sur les mécanismes pyRevit existants.

---

# 199. Fonctions prioritaires — `unit_utils.py`

```text
to_internal_units
from_internal_units
format_unit
```

---

# 200. API spécifique aux outils

Architecture finale cible :

```text
lib/
│
├── common/
│
│   └── API technique commune
│
├── publication/
│
│   └── API métier Publication
│
├── calculation/
│
│   └── API métier Calcul
│
├── quality/
│
│   └── API métier Contrôle
│
├── annotation/
│
│   └── API métier Annotation
│
└── ai/
    └── API métier IA
```

---

# 201. Principe de frontière

`common` répond à la question :

> **Comment faire techniquement ?**

Les modules métier répondent à la question :

> **Que doit faire l’outil ?**

Exemple :

```text
common.parameter_utils
=
Comment écrire un paramètre Revit ?
```

```text
RoomCalculator
=
Quelle valeur doit être écrite dans ce paramètre ?
```

---

# 202. Exemple d’architecture RoomCalculator

```text
RoomCalculator.pushbutton/
│
├── script.py
│
├── ui/
│   ├── MainWindow.xaml
│   └── MainWindow.py
│
└── services/
    └── room_calculator_controller.py


lib/
│
├── common/
│   ├── parameter_utils.py
│   ├── transaction.py
│   ├── logger.py
│   └── settings.py
│
└── calculation/
    ├── room_collector.py
    ├── room_calculator.py
    ├── room_writer.py
    └── models.py
```

---

# 203. Exemple de flux RoomCalculator

```text
Utilisateur clique sur Calculer
        ↓
MainWindow
        ↓
RoomCalculatorController
        ↓
Validation
        ↓
RoomCollector
        ↓
RoomData[]
        ↓
RoomCalculatorService
        ↓
CalculationResult
        ↓
Transaction
        ↓
RoomWriter
        ↓
parameter_utils
        ↓
Revit API
```

---

# 204. Exemple d’architecture PublisherAI

```text
PublisherAI.pushbutton/
│
├── script.py
│
├── ui/
│   ├── MainWindow.xaml
│   └── MainWindow.py
│
└── controller.py


lib/publication/
│
├── publication_service.py
├── booklet_service.py
├── sheet_service.py
├── pdf_exporter.py
├── dwg_exporter.py
├── naming_service.py
├── models.py
└── results.py
```

avec :

```text
lib/common/
├── logger.py
├── settings.py
├── file_utils.py
├── progress.py
└── revit_utils.py
```

---

# 205. Flux PublisherAI

```text
MainWindow
↓
PublisherController
↓
PublicationOptions
↓
PublicationService
↓
BookletService
↓
SheetService
↓
PdfExporter / DwgExporter
↓
Revit API
↓
PublicationResult
↓
UI
```

---

# 206. Import recommandé depuis un outil

Exemple :

```python
from common.logger import get_logger
from common.settings import get_setting
from common.transaction import taa_transaction
from common.parameter_utils import (
    get_parameter,
    set_parameter_value,
)
```

---

# 207. Import métier

Exemple :

```python
from calculation.room_calculator import (
    RoomCalculatorService,
)
```

L’outil doit ainsi avoir des dépendances explicites.

---

# 208. Point d’entrée pyRevit

Le fichier :

```text
script.py
```

doit rester très léger.

Exemple idéal :

```python
from controller import RoomCalculatorController


def main():

    controller = RoomCalculatorController()

    controller.run()


if __name__ == "__main__":
    main()
```

---

# 209. Ce que `script.py` ne doit pas devenir

Éviter :

```text
3000 lignes
```

contenant :

```text
UI
collectors
calculs
transactions
exports
logging
settings
gestion fichiers
```

dans un seul fichier.

---

# 210. Compatibilité avec les scripts simples

Cette architecture ne signifie pas qu’un outil de dix lignes doit nécessairement disposer de :

```text
Controller
Service
Repository
Model
ViewModel
```

L’architecture doit rester proportionnée.

---

# 211. Documentation du package

Chaque domaine important peut disposer d’un :

```text
README.md
```

interne expliquant :

```text
responsabilité du module
API publique
exemples
dépendances
```

---

# 212. Documentation automatique future

Si le projet devient suffisamment important, les docstrings pourront éventuellement servir à produire une documentation technique automatique.

Cela justifie dès maintenant des conventions cohérentes.

---

# 213. Principe directeur de l’API interne

Une bonne API interne doit permettre au développeur d’écrire :

```python
rooms = collect_rooms(doc)

with taa_transaction(
    doc,
    "Mise à jour des pièces"
):

    for room in rooms:

        set_parameter_value(
            room,
            "TAA_Surface_Calculee",
            value
        )
```

sans avoir à réécrire les mécanismes techniques Revit à chaque outil.

---

# 214. Objectif à long terme

À terme, développer un nouvel outil Outils TAA devrait principalement consister à écrire :

```text
la logique métier spécifique
```

et non à reconstruire :

```text
logging
transactions
paramètres
UI de base
settings
progression
sélection
collectors
gestion fichiers
```

---

# 215. Règles essentielles

```text
1. common ne contient que du générique.

2. Un outil ne duplique pas une fonction commune.

3. Les fonctions de lecture ne modifient jamais Revit.

4. Les transactions sont contrôlées par le niveau appelant.

5. Les dépendances sont injectées plutôt que globales.

6. La logique métier ne dépend pas de WPF.

7. Les paramètres Revit passent par parameter_utils lorsque possible.

8. Les unités passent par unit_utils.

9. Les erreurs métier utilisent des exceptions explicites.

10. Les opérations complexes retournent des résultats structurés.

11. Les APIs utilisées par plusieurs outils doivent rester stables.

12. Les changements incompatibles doivent être accompagnés d'une migration.

13. L'API Autodesk doit être encapsulée lorsqu'elle est complexe ou instable.

14. L'architecture doit rester proportionnée à la complexité de l'outil.

15. La simplicité reste prioritaire.
```

---

# 216. Conclusion

L’API interne constitue la colonne vertébrale technique de **Outils TAA**.

Elle doit permettre aux différents outils de partager les mêmes fondations sans dupliquer le code et sans créer de dépendances fortes entre les modules.

L’architecture cible peut être résumée ainsi :

```text
┌──────────────────────────────┐
│        OUTILS PYREVIT        │
│                              │
│ PublisherAI                  │
│ RoomCalculator               │
│ Quality Control              │
│ Annotation                   │
│ Utilitaires                  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       SERVICES MÉTIER        │
│                              │
│ publication/                 │
│ calculation/                 │
│ quality/                     │
│ annotation/                  │
│ ai/                          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          COMMON API          │
│                              │
│ parameters                   │
│ transactions                 │
│ logging                      │
│ settings                     │
│ units                        │
│ collectors                   │
│ selection                    │
│ progress                     │
│ files                        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     AUTODESK REVIT API       │
│          2025.4              │
└──────────────────────────────┘
```

Le principe fondamental reste :

> **Les outils définissent le métier.  
> L’API interne fournit les fondations techniques.**

Une API interne stable, documentée et simple permettra à Outils TAA de passer progressivement d’une collection d’automatisations Revit à une véritable plateforme logicielle interne commune à l’agence.