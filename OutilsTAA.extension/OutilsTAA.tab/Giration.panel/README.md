# Giration.panel - Module Giration des véhicules

**Module :** Giration des véhicules  
**Version :** 0.1 (Développement)  
**Statut :** Phase P0 - Prototype initial  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x

---

## Description

Ce module permet de simuler et visualiser les trajectoires de véhicules dans Autodesk Revit,
en reproduisant les fonctionnalités de tracé manuel d'**Autodesk Vehicle Tracking**.

## Fonctionnalités

### Implémentées (testables sans Revit)

- ✅ Moteur cinématique d'Ackermann pour véhicules rigides
- ✅ Calcul des trajectoires en ligne droite et courbes
- ✅ Calcul des trajectoires des roues
- ✅ Calcul de l'enveloppe balayée
- ✅ Validation des trajectoires
- ✅ Bibliothèque de véhicules (SDIS 33, camions, utilitaires, etc.)
- ✅ Interface utilisateur WPF de base
- ✅ Tests unitaires

### À implémenter (nécessitent Revit)

- ⚠️ Intégration avec l'API Revit (capture souris, prévisualisation)
- ⚠️ Création des éléments graphiques finaux
- ⚠️ Persistance des simulations
- ⚠️ Modification des simulations existantes

## Structure

```text
Giration.panel/
├── models/
│   └── __init__.py
├── services/
│   └── __init__.py
├── ui/
│   ├── __init__.py
│   ├── giration_main_window.xaml
│   └── giration_main_window.py
├── TracerGiration.pushbutton/
│   ├── script.py          # Point d'entrée pyRevit
│   └── icon.png           # Icône (à créer)
├── giration_controller.py  # Contrôleur principal
└── README.md               # Ce fichier
```

## Dépendances

### Internes

- `lib/giration/` - Moteur cinématique et bibliothèque des véhicules
- `lib/common/` - Bibliothèques communes Outils TAA

### Externes

- Autodesk Revit 2025.4
- pyRevit 5.x
- Python 3.x (compatible IronPython)

## Installation

1. Copier le dossier `Giration.panel` dans `OutilsTAA.extension/OutilsTAA.tab/`
2. Copier le dossier `giration` dans `OutilsTAA.extension/lib/`
3. Redémarrer Revit ou recharger l'extension pyRevit

## Utilisation

### Sans Revit (tests unitaires)

```bash
# Exécuter les tests du moteur cinématique
python -m pytest tests/test_giration_*.py -v
```

### Avec Revit (à implémenter)

1. Ouvrir un projet Revit
2. Dans l'onglet **Outils TAA**, cliquer sur **Giration** → **Tracer Giration**
3. Sélectionner un véhicule
4. Cliquer dans la vue de plan pour définir le point de départ
5. Tracer la trajectoire à la souris
6. Valider et enregistrer

## Exemples de code

### Utilisation du moteur cinématique

```python
from lib.giration.models.vehicle import Vehicle
from lib.giration.services.kinematics import AckermannKinematics
import math

# Créer un véhicule
vehicle = Vehicle(
    name="Mon Véhicule",
    length=5.0,
    width=2.0,
    wheelbase=3.0,
    max_steering_angle=math.radians(45)
)

# Créer le moteur cinématique
kinematics = AckermannKinematics(vehicle)

# Calculer une trajectoire
segments = [
    {'distance': 5.0, 'steering_angle': 0.0, 'is_reverse': False},
    {'distance': 3.0, 'steering_angle': math.radians(30), 'is_reverse': False}
]
trajectory = kinematics.calculate_path((0, 0), 0.0, segments)

# Calculer les trajectoires des roues
wheel_trajectories = kinematics.calculate_wheel_trajectories(trajectory)

# Calculer l'enveloppe balayée
swept_area = kinematics.calculate_swept_area(trajectory)

# Valider la trajectoire
is_valid, errors = kinematics.validate_trajectory(trajectory)
```

### Utilisation de la bibliothèque des véhicules

```python
from lib.giration.data.vehicles import get_all_vehicles, get_vehicle_by_name

# Lister tous les véhicules
all_vehicles = get_all_vehicles()
for vehicle in all_vehicles:
    print(f"{vehicle.name} ({vehicle.category})")

# Récupérer un véhicule spécifique
vehicle = get_vehicle_by_name("Camion Échelle - SDIS 33")
if vehicle:
    print(f"Longueur: {vehicle.length}m, Largeur: {vehicle.width}m")
```

## Tests

### Exécution des tests

```bash
# Tous les tests de giration
python -m pytest tests/test_giration_*.py -v

# Test spécifique
python -m pytest tests/test_giration_vector2d.py -v
python -m pytest tests/test_giration_vehicle.py -v
python -m pytest tests/test_giration_kinematics.py -v
```

### Couverture des tests

| Composant | Couverture |
|-----------|------------|
| Vector2D | ✅ Complète |
| Vehicle | ✅ Complète |
| AckermannKinematics | ✅ Partielle |
| UI | ❌ Non testée (nécessite Revit) |
| Intégration Revit | ❌ Non testée (nécessite Revit) |

## Documentation

- [Documentation complète](docs/25_Giration_Vehicules.md)
- [Standards de développement Outils TAA](docs/03_Standards_Developpement.md)
- [Architecture générale](docs/02_Architecture_Generale.md)

## Contribution

### Branche de développement

```bash
git checkout feature/giration-v1
```

### Workflow

1. Lire la documentation existante
2. Respecter les standards de développement
3. Écrire des tests unitaires
4. Documenter les modifications
5. Valider avec Revit si nécessaire
6. Créer une Pull Request

### Règles

- ✅ Respecter l'architecture modulaire
- ✅ Écrire des tests unitaires
- ✅ Documenter le code
- ✅ Respecter les conventions de nommage
- ❌ Ne pas modifier `main` directement
- ❌ Ne pas inventer des données de véhicules
- ❌ Ne pas déclarer une fonctionnalité validée sans test Revit

## Prochaines étapes

1. **Phase P0** : Implémenter l'interaction Revit (ExternalEvent, prévisualisation)
2. **Phase P1** : Valider le moteur cinématique dans Revit
3. **Phase P2** : Implémenter la représentation graphique finale
4. **Phase P3** : Compléter la bibliothèque des véhicules
5. **Phase P4** : Implémenter la persistance
6. **Phase P5** : Stabilisation et validation finale

## Licence

Ce module fait partie d'**Outils TAA** et est soumis à la même licence.
Voir [LICENSE](LICENSE) pour plus de détails.

---

*Module Giration des véhicules - Outils TAA v0.1*
