# Outils TAA – Conventions de nommage

**Statut :** Référence
**Cible :** Revit 2025.4 / pyRevit 5.x

## 1. Principe général

Le projet distingue systématiquement le **nom fonctionnel**, visible par l'utilisateur, et le **nom technique**, utilisé dans l'arborescence, les fichiers et le code.

Les noms fonctionnels sont en français et doivent être compréhensibles par les architectes et BIM managers.

Les noms techniques sont en ASCII, sans espaces ni accents, afin de garantir une bonne compatibilité avec Python, pyRevit, Git et les systèmes de fichiers.

## 2. Repository

Le repository GitHub porte le nom :

```text
Outils-TAA
```

Le dossier racine technique de l'extension pyRevit est :

```text
OutilsTAA.extension
```

Le tab pyRevit est :

```text
OutilsTAA.tab
```

Le trait d'union de `Outils-TAA` est réservé au nom du repository. Il ne doit pas être ajouté au nom de l'extension pyRevit.

## 3. Modules

| Nom fonctionnel | Nom technique pyRevit |
|---|---|
| Export | `Export.panel` |
| Calculs des pièces | `Calculs.panel` |
| Contrôle | `Controle.panel` |
| Annotation | `Annotation.panel` |
| Utilitaires | `Utilitaires.panel` |

Les accents sont conservés dans les libellés d'interface mais supprimés dans les noms techniques.

## 4. Documentation

Tous les fichiers Markdown de référence utilisent :

- une numérotation lorsqu'ils appartiennent au Developer Handbook ;
- `snake_case` ;
- uniquement des caractères ASCII ;
- aucun espace ;
- aucun accent.

Convention :

```text
NN_Nom_Du_Document.md
```

Exemples :

```text
01_Vision_Philosophie.md
02_Architecture_Generale.md
03_Standards_Developpement.md
04_UI_Guidelines.md
05_Internal_API.md
06_AI_Development_Guide.md
07_Git_Workflow.md
08_Testing.md
09_Export.md
10_Calculs_Pieces.md
```

## 5. Python

### Fichiers et modules

Utiliser `snake_case` :

```text
publication_service.py
filename_service.py
parameter_utils.py
```

### Fonctions et variables

Utiliser `snake_case` :

```python
publication_set = None
def get_parameter_value():
    pass
```

### Classes

Utiliser `PascalCase` :

```python
class PublicationService:
    pass
```

### Constantes

Utiliser `UPPER_SNAKE_CASE` :

```python
DEFAULT_TIMEOUT = 30
```

## 6. Vocabulaire fonctionnel actuel

Les noms suivants sont les noms officiels du projet :

- **Export** pour la publication de documents PDF/DWG ;
- **Calculs des pièces** pour les outils de calcul liés aux pièces ;
- **Contrôle** pour les outils de contrôle ;
- **Annotation** pour les outils d'annotation ;
- **Utilitaires** pour les fonctions générales.

Les anciens noms de développement `PublisherAI` et `RoomCalculator` sont historiques uniquement et ne doivent plus apparaître dans les interfaces ou dans les nouveaux identifiants techniques.

## 7. Règle de migration

Lorsqu'un ancien nom est rencontré dans un document courant, un exemple de code ou un nouvel élément de l'architecture, il doit être remplacé par le nom officiel correspondant.

Les anciens noms peuvent être conservés uniquement dans :

- le changelog ;
- les notes de migration ;
- l'historique du projet ;
- les explications explicitement historiques.
