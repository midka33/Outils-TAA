# Outils TAA — Module Giration des véhicules

**Version :** 0.1 (Développement)  
**Statut :** Phase P0 - Prototype initial  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x  
**Date :** 2026  
**Issue GitHub :** [#40](https://github.com/midka33/Outils-TAA/issues/40)

---

## 1. Objectif du module

Le module **Giration des véhicules** permet de simuler et visualiser les trajectoires
de véhicules dans Autodesk Revit, en reproduisant les fonctionnalités de tracé manuel
d'**Autodesk Vehicle Tracking**.

L'objectif principal est de fournir aux architectes un outil permettant de :

- Sélectionner un véhicule parmi une bibliothèque prédéfinie
- Tracer manuellement une trajectoire dans une vue de plan
- Visualiser le déplacement du véhicule avec ses contraintes de giration
- Afficher les trajectoires des roues, les enveloppes balayées et les positions successives
- Enregistrer et modifier les simulations

**Ce module ne calcule pas automatiquement d'itinéraire.** Le chemin est entièrement
piloté par l'utilisateur, et le moteur cinématique applique les limites physiques
du véhicule.

---

## 2. Architecture

### 2.1 Organisation des fichiers

```text
OutilsTAA.extension/
├── OutilsTAA.tab/
│   └── Giration.panel/
│       ├── models/
│       │   └── __init__.py
│       ├── services/
│       │   └── __init__.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── giration_main_window.xaml
│       │   └── giration_main_window.py
│       ├── TracerGiration.pushbutton/
│       │   ├── script.py
│       │   └── icon.png (à créer)
│       └── giration_controller.py
│
└── lib/
    └── giration/
        ├── __init__.py
        ├── models/
        │   ├── __init__.py
        │   └── vehicle.py
        ├── services/
        │   ├── __init__.py
        │   └── kinematics.py
        ├── geometry/
        │   ├── __init__.py
        │   └── vector2d.py
        └── data/
            ├── __init__.py
            └── vehicles.py
```

### 2.2 Séparation des responsabilités

| Couche | Responsabilité | Composants |
|--------|---------------|------------|
| **UI** | Interface utilisateur WPF | `giration_main_window.xaml`, `giration_main_window.py` |
| **Contrôle** | Orchestration | `giration_controller.py` |
| **Modèles** | Données des véhicules et trajectoires | `vehicle.py`, `kinematics.py` |
| **Géométrie** | Calculs mathématiques | `vector2d.py` |
| **Données** | Bibliothèque des véhicules | `vehicles.py` |
| **Revit** | Intégration avec l'API Revit | `script.py` (à compléter) |

---

## 3. Fonctionnalités

### 3.1 Fonctionnalités implémentées (Phase P0)

#### 3.1.1 Moteur cinématique

✅ **Implémenté et testé**

- Modèle cinématique d'Ackermann pour véhicules rigides
- Calcul des trajectoires en ligne droite
- Calcul des trajectoires courbes avec braquage
- Calcul des trajectoires des roues (avant et arrière)
- Calcul de l'enveloppe balayée (simplifiée)
- Validation des trajectoires par rapport aux contraintes du véhicule
- Gestion de la marche avant et arrière

**Composants :**
- `lib/giration/geometry/vector2d.py` - Vecteurs 2D
- `lib/giration/models/vehicle.py` - Modèle de véhicule
- `lib/giration/services/kinematics.py` - Moteur cinématique

#### 3.1.2 Bibliothèque des véhicules

✅ **Implémenté**

- Définition des caractéristiques géométriques et cinématiques
- Véhicules de secours (SDIS 33)
- Camions de collecte
- Véhicules utilitaires
- Poids lourds
- Véhicules particuliers

**Composants :**
- `lib/giration/data/vehicles.py` - Bibliothèque des véhicules

#### 3.1.3 Interface utilisateur de base

✅ **Implémenté (partiellement)**

- Sélection des véhicules par catégorie
- Affichage des caractéristiques du véhicule sélectionné
- Options d'affichage (véhicule, trajectoires des roues, enveloppe balayée)
- Boutons de contrôle (Démarrer, Annuler, Effacer, Terminer)

**Composants :**
- `OutilsTAA.extension/OutilsTAA.tab/Giration.panel/ui/giration_main_window.xaml`
- `OutilsTAA.extension/OutilsTAA.tab/Giration.panel/ui/giration_main_window.py`

#### 3.1.4 Contrôleur

✅ **Implémenté (partiellement)**

- Gestion de la sélection des véhicules
- Orchestration des calculs
- Validation des trajectoires

**Composants :**
- `OutilsTAA.extension/OutilsTAA.tab/Giration.panel/giration_controller.py`

### 3.2 Fonctionnalités à implémenter

#### 3.2.1 Phase P0 - Faisabilité interactive (en cours)

⚠️ **À implémenter et tester dans Revit**

- [ ] **Intégration avec l'API Revit**
  - Capture des clics souris dans la vue de plan
  - Prévisualisation dynamique des trajectoires
  - Création des éléments graphiques finaux
  - Gestion des transactions Revit

- [ ] **Interaction utilisateur**
  - Sélection du point de départ
  - Définition de l'orientation initiale
  - Tracé interactif avec la souris
  - Validation des segments
  - Annulation et retour en arrière

- [ ] **Affichage dans Revit**
  - Affichage du véhicule à sa position
  - Affichage des trajectoires (lignes, arcs)
  - Affichage des trajectoires des roues
  - Affichage de l'enveloppe balayée
  - Styles de lignes identifiables

#### 3.2.2 Phase P1 - Moteur de cinématique (validé)

✅ **Implémenté et testable sans Revit**

- [x] Modèle cinématique d'Ackermann
- [x] Calcul des trajectoires
- [x] Calcul des trajectoires des roues
- [x] Calcul de l'enveloppe balayée
- [x] Validation des trajectoires
- [x] Tests unitaires

#### 3.2.3 Phase P2 - Représentation graphique

⚠️ **À implémenter**

- [ ] Création des éléments Revit natifs
- [ ] Styles de lignes personnalisables
- [ ] Organisation des éléments (groupes, sous-projets)
- [ ] Gestion des unités
- [ ] Export PDF/DWG

#### 3.2.4 Phase P3 - Bibliothèque des véhicules

✅ **Base implémentée, à compléter**

- [x] Structure de la bibliothèque
- [x] Véhicules de base
- [ ] Intégration des données SDIS 33 complètes
- [ ] Ajout de véhicules personnalisés par l'utilisateur
- [ ] Import/export de véhicules

#### 3.2.5 Phase P4 - Persistance et modification

⚠️ **À implémenter**

- [ ] Enregistrement des simulations
- [ ] Chargement des simulations existantes
- [ ] Modification des simulations
- [ ] Régénération des éléments graphiques
- [ ] Suppression des simulations

#### 3.2.6 Phase P5 - Stabilisation

⚠️ **À implémenter**

- [ ] Tests de non-régression
- [ ] Documentation utilisateur complète
- [ ] Tutoriels
- [ ] Validation utilisateur finale

---

## 4. Modèle de données

### 4.1 Véhicule

Un véhicule est défini par les caractéristiques suivantes :

| Propriété | Type | Description | Unité |
|-----------|------|-------------|-------|
| `name` | str | Nom du véhicule | - |
| `category` | str | Catégorie (ex: "Véhicule de secours") | - |
| `length` | float | Longueur totale | m |
| `width` | float | Largeur totale | m |
| `wheelbase` | float | Empattement (distance entre essieux) | m |
| `front_overhang` | float | Porte-à-faux avant | m |
| `rear_overhang` | float | Porte-à-faux arrière | m |
| `front_track` | float | Voie avant (distance entre roues avant) | m |
| `rear_track` | float | Voie arrière (distance entre roues arrière) | m |
| `max_steering_angle` | float | Angle maximal de braquage des roues avant | radians |
| `min_turning_radius` | float | Rayon minimal de giration (optionnel) | m |
| `source` | str | Source des données | - |
| `reference` | str | Référence du document | - |

**Note :** Si `min_turning_radius` n'est pas fourni, il est calculé automatiquement
a partir de l'empattement et de l'angle maximal de braquage.

### 4.2 Trajectoire

Une trajectoire est composée d'une série de **TrajectoryPoint** :

| Propriété | Type | Description | Unité |
|-----------|------|-------------|-------|
| `position` | Vector2D | Position du point de référence | m |
| `angle` | float | Orientation du véhicule | radians |
| `steering_angle` | float | Angle de braquage des roues avant | radians |
| `is_reverse` | bool | True si le véhicule est en marche arrière | - |
| `timestamp` | float | Temps écoulé depuis le début (optionnel) | s |

Le point de référence peut être :
- L'arrière du véhicule (par défaut)
- Le centre du véhicule
- L'avant du véhicule

### 4.3 Simulation

Une simulation enregistrée contient :

```python
{
    'id': str,                      # Identifiant unique
    'name': str,                    # Nom de la simulation
    'vehicle': dict,                # Données du véhicule (via to_dict())
    'trajectory': list,             # Liste de TrajectoryPoint (via to_dict())
    'wheel_trajectories': dict,     # Trajectoires des roues
    'swept_area': list,             # Enveloppe balayée
    'options': dict,                # Options d'affichage
    'timestamp': datetime,          # Date de création
    'revit_elements': list          # Références aux éléments Revit créés
}
```

---

## 5. Moteur cinématique

### 5.1 Modèle Ackermann

Le module utilise le **modèle cinématique d'Ackermann** pour les véhicules rigides.

**Hypothèses :**
1. Les roues arrière suivent la même trajectoire (pas de dérapage latéral)
2. Les roues avant sont orientées selon un angle moyen
3. Le véhicule tourne autour d'un centre de rotation instantané
4. La vitesse est constante ou variable, mais n'affecte pas la géométrie

**Formules :**

Pour un véhicule avec :
- Empattement L (wheelbase)
- Angle de braquage δ (steering angle)

Le rayon de courbure R est donné par :
```
R = L / tan(δ)
```

Le centre de rotation est situé à une distance R derrière l'essieu arrière,
sur la perpendiculaire à l'axe du véhicule.

### 5.2 Calcul des trajectoires

Le moteur cinématique (`AckermannKinematics`) fournit les méthodes suivantes :

#### 5.2.1 `calculate_trajectory()`

Calcule une trajectoire pour un segment donné.

**Paramètres :**
- `start_point` : Point de départ (tuple ou Vector2D)
- `start_angle` : Orientation initiale (radians)
- `steering_angle` : Angle de braquage (radians)
- `distance` : Distance à parcourir (m)
- `is_reverse` : True pour marche arrière
- `num_points` : Nombre de points intermédiaires

**Retour :** Liste de `TrajectoryPoint`

#### 5.2.2 `calculate_path()`

Calcule un chemin complet à partir d'une série de segments.

**Paramètres :**
- `start_point` : Point de départ
- `start_angle` : Orientation initiale
- `segments` : Liste de dictionnaires `{distance, steering_angle, is_reverse, num_points}`

**Retour :** Liste de `TrajectoryPoint`

#### 5.2.3 `calculate_wheel_trajectories()`

Calcule les trajectoires des 4 roues à partir de la trajectoire du véhicule.

**Paramètres :**
- `trajectory` : Liste de `TrajectoryPoint`
- `reference_point` : Point de référence ('rear' ou 'center')

**Retour :** Dictionnaire avec les trajectoires des 4 roues

#### 5.2.4 `calculate_swept_area()`

Calcule l'enveloppe balayée par le véhicule.

**Paramètres :**
- `trajectory` : Liste de `TrajectoryPoint`
- `reference_point` : Point de référence

**Retour :** Liste de polygones (chaque polygone est une liste de Vector2D)

#### 5.2.5 `validate_trajectory()`

Valide une trajectoire par rapport aux contraintes du véhicule.

**Paramètres :**
- `trajectory` : Liste de `TrajectoryPoint`

**Retour :** Tuple `(is_valid, errors)`

### 5.3 Limites et contraintes

**Contraintes respectées :**
- Angle de braquage ≤ angle maximal du véhicule
- Rayon de courbure ≥ rayon minimal de giration

**Limitations actuelles :**
- Véhicules rigides uniquement (pas de véhicules articulés)
- Modèle 2D uniquement (pas de pente)
- Pas de dérapage latéral
- Pas de suspension
- Pas de déformation de la carrosserie

**Améliorations futures :**
- Support des véhicules articulés (semi-remorques, etc.)
- Modèle 3D pour les pentes
- Prise en compte du dérapage
- Simulation plus réaliste de la dynamique

---

## 6. Bibliothèque des véhicules

### 6.1 Véhicules disponibles

La bibliothèque (`lib/giration/data/vehicles.py`) contient actuellement :

#### Véhicules de secours (SDIS 33)

| Nom | Longueur | Largeur | Empattement | Rayon min |
|-----|----------|---------|-------------|-----------|
| Camion Échelle | 12.0 m | 2.55 m | 6.5 m | 12.5 m |
| Fourgon Pompe-Tonne | 9.5 m | 2.5 m | 5.0 m | 10.0 m |
| VSAV | 7.2 m | 2.2 m | 4.0 m | 8.5 m |

#### Camions de collecte

| Nom | Longueur | Largeur | Empattement | Rayon min |
|-----|----------|---------|-------------|-----------|
| Camion standard | 10.0 m | 2.5 m | 5.5 m | 11.0 m |
| Camion grand volume | 12.0 m | 2.6 m | 6.0 m | 13.0 m |

#### Véhicules utilitaires

| Nom | Longueur | Largeur | Empattement | Rayon min |
|-----|----------|---------|-------------|-----------|
| Utilitaire léger | 5.5 m | 2.0 m | 3.2 m | 6.0 m |
| Fourgon de livraison | 7.0 m | 2.2 m | 4.0 m | 7.5 m |

#### Poids lourds

| Nom | Longueur | Largeur | Empattement | Rayon min |
|-----|----------|---------|-------------|-----------|
| Poids lourd 3 essieux | 16.0 m | 2.6 m | 7.0 m | 18.0 m |

#### Véhicules particuliers

| Nom | Longueur | Largeur | Empattement | Rayon min |
|-----|----------|---------|-------------|-----------|
| Voiture standard | 4.5 m | 1.8 m | 2.7 m | 5.5 m |
| SUV grand format | 5.2 m | 2.0 m | 3.0 m | 6.5 m |

### 6.2 Ajout de nouveaux véhicules

Pour ajouter un nouveau véhicule à la bibliothèque :

1. Créer une instance de `Vehicle` dans `lib/giration/data/vehicles.py`
2. L'ajouter à la liste `ALL_VEHICLES`

**Exemple :**

```python
VEHICLE_MON_CAMION = Vehicle(
    name="Mon Camion",
    category="Camion",
    length=10.5,
    width=2.5,
    wheelbase=5.8,
    front_overhang=2.2,
    rear_overhang=2.5,
    front_track=2.0,
    rear_track=1.8,
    max_steering_angle=math.radians(42),
    min_turning_radius=11.5,
    source="Fiche technique constructeur",
    reference="MON-CAMION-001"
)

ALL_VEHICLES.append(VEHICLE_MON_CAMION)
```

### 6.3 Sources des données

Les données des véhicules proviennent de :

1. **Documents SDIS** (Services Départementaux d'Incendie et de Secours)
   - Fiches techniques des véhicules de secours
   - Données spécifiques au SDIS 33

2. **Fiches techniques constructeurs**
   - Données officielles des fabricants de véhicules
   - Spécifications techniques détaillées

3. **Normes et réglementations**
   - Normes de sécurité
   - Réglementations sur les dimensions des véhicules

**Important :** Les prescriptions réglementaires d'une voie ne constituent
**pas** nécessairement les caractéristiques géométriques ou cinématiques d'un véhicule.
Un rayon intérieur réglementaire de voirie ne doit pas être utilisé directement
comme rayon mécanique de braquage.

---

## 7. Interface utilisateur

### 7.1 Description

La fenêtre principale (`giration_main_window.xaml`) est organisée en :

1. **En-tête** : Titre et description
2. **Panneau de gauche** : Sélection et informations du véhicule
   - Sélection par catégorie
   - Sélection du véhicule
   - Affichage des caractéristiques
   - Options d'affichage
3. **Zone centrale** : Visualisation et commandes
   - Barre d'outils (Démarrer, Annuler, Effacer, Terminer)
   - Zone de visualisation (affichage Revit)
   - Informations et statut
4. **Pied de page** : Boutons Aide et Fermer

### 7.2 Flux utilisateur

```
1. Ouvrir la fenêtre Giration
   │
2. Sélectionner un véhicule
   │
3. Cliquer sur "Démarrer le tracé"
   │
4. Cliquer dans la vue de plan Revit pour définir le point de départ
   │
5. Définir l'orientation initiale (par clic ou saisie)
   │
6. Déplacer la souris pour prévisualiser la trajectoire
   │
7. Cliquer pour valider un segment
   │
8. Répéter les étapes 6-7 pour ajouter des segments
   │
9. Utiliser "Annuler dernier" pour corriger
   │
10. Cliquer sur "Terminer" pour finaliser
   │
11. La simulation est enregistrée et les éléments graphiques sont créés
```

### 7.3 Options d'affichage

| Option | Description |
|--------|-------------|
| Afficher le véhicule | Affiche la silhouette du véhicule |
| Trajectoires des roues | Affiche les trajectoires des 4 roues |
| Enveloppe balayée | Affiche la surface balayée par la carrosserie |
| Positions intermédiaires | Affiche les positions successives du véhicule |

---

## 8. Intégration Revit

### 8.1 Prérequis

- Autodesk Revit 2025.4
- pyRevit 5.x
- Module Outils TAA installé

### 8.2 Installation

1. Copier le dossier `Giration.panel` dans `OutilsTAA.extension/OutilsTAA.tab/`
2. Copier le dossier `giration` dans `OutilsTAA.extension/lib/`
3. Redémarrer Revit ou recharger l'extension pyRevit

### 8.3 Accès

Le module sera accessible via :
- **Onglet Outils TAA** → **Panneau Giration** → **Tracer Giration**

### 8.4 Intégration avec l'API Revit

**À implémenter dans les phases suivantes :**

- Utilisation de `ExternalEvent` pour capturer les interactions utilisateur
- Utilisation de `Idling` pour la prévisualisation dynamique
- Création d'éléments Revit natifs (lignes, arcs, etc.)
- Gestion des transactions
- Organisation des éléments (groupes, sous-projets)

**Méthodes clés à implémenter :**

```python
# Dans giration_controller.py
def create_revit_elements(self, trajectory, wheel_trajectories, swept_area):
    """Crée les éléments Revit pour visualiser la trajectoire."""
    # 1. Créer une transaction Revit
    # 2. Créer les lignes de trajectoire
    # 3. Créer les trajectoires des roues
    # 4. Créer l'enveloppe balayée (surface ou lignes)
    # 5. Créer les positions intermédiaires
    # 6. Valider la transaction
    pass
```

---

## 9. Persistance

### 9.1 Enregistrement des simulations

**À implémenter dans la phase P4 :**

Les simulations seront enregistrées dans :
- Les paramètres de projet Revit (pour les simulations spécifiques à un projet)
- Un fichier JSON externe (pour les simulations réutilisables)

**Structure des données :**

```json
{
    "version": "1.0",
    "simulations": [
        {
            "id": "unique-id-1",
            "name": "Simulation 1",
            "vehicle": {
                "name": "Camion Échelle",
                "category": "Véhicule de secours",
                "length": 12.0,
                "width": 2.55,
                "wheelbase": 6.5,
                "...": "..."
            },
            "trajectory": [
                {"x": 0.0, "y": 0.0, "angle": 0.0, "steering_angle": 0.0, "is_reverse": false},
                {"x": 5.0, "y": 0.0, "angle": 0.0, "steering_angle": 0.0, "is_reverse": false},
                ...
            ],
            "options": {
                "show_vehicle": true,
                "show_wheel_trajectories": true,
                "show_swept_area": true,
                "show_positions": true
            },
            "timestamp": "2026-01-01T12:00:00",
            "revit_elements": ["element-id-1", "element-id-2", ...]
        }
    ]
}
```

### 9.2 Chargement des simulations

**À implémenter dans la phase P4 :**

- Charger les simulations depuis le fichier de persistance
- Sélectionner une simulation existante
- Modifier les paramètres de la simulation
- Régénérer les éléments graphiques Revit
- Supprimer une simulation

---

## 10. Tests

### 10.1 Tests unitaires

Les tests unitaires sont situés dans le dossier `tests/` :

| Fichier | Description |
|---------|-------------|
| `test_giration_vector2d.py` | Tests des opérations sur Vector2D |
| `test_giration_vehicle.py` | Tests du modèle Vehicle |
| `test_giration_kinematics.py` | Tests du moteur cinématique |

**Exécution des tests :**

```bash
# Exécuter tous les tests de giration
python -m pytest tests/test_giration_*.py -v

# Exécuter un test spécifique
python -m pytest tests/test_giration_vector2d.py::TestVector2DInitialization -v
```

### 10.2 Tests d'intégration

**À implémenter dans les phases suivantes :**

- Tests avec Revit API (nécessitent Revit 2025.4)
- Tests de l'interface utilisateur
- Tests de persistance
- Tests de non-régression

### 10.3 Validation manuelle

**À effectuer dans Revit 2025.4 :**

1. Ouvrir un projet Revit
2. Lancer le module Giration
3. Sélectionner un véhicule
4. Tracer une trajectoire
5. Vérifier l'affichage
6. Enregistrer la simulation
7. Charger la simulation
8. Modifier et régénérer

---

## 11. Roadmap de développement

### Phase P0 - Faisabilité interactive

**Objectif :** Démontrer que l'utilisateur peut piloter un véhicule dans une vue Revit.

- [x] Créer la structure initiale du module
- [x] Créer une interface WPF minimale
- [x] Développer le moteur cinématique (testable sans Revit)
- [x] Créer la bibliothèque des véhicules
- [ ] Permettre de sélectionner une position initiale (nécessite Revit)
- [ ] Permettre de définir l'orientation du véhicule (nécessite Revit)
- [ ] Développer et tester une méthode de prévisualisation dynamique (nécessite Revit)
- [ ] Préparer une procédure de test dans Revit 2025.4

**Critère de validation :** L'utilisateur peut piloter visuellement un véhicule dans sa vue de plan.

### Phase P1 - Moteur de cinématique

**Objectif :** Développer et valider le calcul des trajectoires.

- [x] Calcul des trajectoires en ligne droite
- [x] Calcul des trajectoires courbes
- [x] Calcul des trajectoires des roues
- [x] Calcul de l'enveloppe balayée
- [x] Validation des trajectoires
- [x] Tests unitaires
- [ ] Tests dans Revit (nécessite P0)

**Critère de validation :** Le moteur cinématique produit des résultats corrects et validés.

### Phase P2 - Représentation graphique

**Objectif :** Créer les représentations graphiques exploitables dans Revit.

- [ ] Création des éléments Revit natifs
- [ ] Styles de lignes personnalisables
- [ ] Organisation des éléments
- [ ] Gestion des unités
- [ ] Export PDF/DWG
- [ ] Reproduire les informations de Vehicle Tracking

**Critère de validation :** Les graphiques produits sont comparables à ceux d'Autodesk Vehicle Tracking.

### Phase P3 - Bibliothèque des véhicules

**Objectif :** Intégrer les véhicules documentés.

- [x] Structure de la bibliothèque
- [x] Véhicules de base
- [ ] Intégration complète des données SDIS 33
- [ ] Ajout de véhicules personnalisés
- [ ] Import/export de véhicules

**Critère de validation :** La bibliothèque contient tous les véhicules nécessaires pour les cas d'usage.

### Phase P4 - Persistance et modification

**Objectif :** Enregistrer et modifier les simulations.

- [ ] Enregistrement des simulations
- [ ] Chargement des simulations
- [ ] Modification des simulations
- [ ] Régénération des éléments graphiques
- [ ] Suppression des simulations

**Critère de validation :** Les simulations peuvent être enregistrées, chargées, modifiées et supprimées.

### Phase P5 - Stabilisation

**Objectif :** Finaliser et stabiliser le module.

- [ ] Tests de non-régression
- [ ] Documentation utilisateur complète
- [ ] Tutoriels
- [ ] Validation utilisateur finale

**Critère de validation :** Le module est prêt pour une utilisation en production.

---

## 12. Limitations et contraintes

### 12.1 Limitations techniques

1. **Environnement requis**
   - Autodesk Revit 2025.4 (obligatoire pour l'interaction graphique)
   - pyRevit 5.x (obligatoire)
   - Python compatible avec IronPython

2. **Fonctionnalités non disponibles sans Revit**
   - Tracé interactif avec la souris
   - Prévisualisation dynamique dans la vue Revit
   - Création des éléments graphiques finaux

3. **Modèle cinématique simplifié**
   - Véhicules rigides uniquement (pas de véhicules articulés dans la version initiale)
   - Modèle 2D uniquement
   - Pas de dérapage latéral
   - Pas de suspension

### 12.2 Contraintes de développement

1. **Ne pas inventer des caractéristiques de véhicules**
   - Toutes les données doivent provenir de sources documentées
   - Ne pas utiliser des rayons réglementaires comme rayons mécaniques

2. **Ne pas remplacer la simulation cinématique par des approximations**
   - Les trajectoires doivent être calculées selon les lois de la cinématique
   - Pas de simples arcs ou lignes droites approximatives

3. **Respecter l'architecture existante**
   - Intégration dans Outils TAA
   - Respect des conventions de nommage
   - Respect des standards de développement

4. **Validation obligatoire dans Revit**
   - Les fonctionnalités nécessitant Revit doivent être testées dans Revit
   - Ne pas déclarer une phase validée sans test réel

---

## 13. Responsabilités de l'utilisateur

Le module **Giration des véhicules** est un outil d'aide à la conception. Il est de
la responsabilité de l'utilisateur de :

1. **Choisir le bon véhicule**
   - Le choix du véhicule appartient entièrement à l'utilisateur
   - Le plugin ne détermine pas automatiquement quel véhicule correspond à un type de bâtiment

2. **Vérifier les résultats**
   - Les calculs sont basés sur des modèles simplifiés
   - L'utilisateur doit vérifier que les résultats sont adaptés à son cas d'usage

3. **Respecter les réglementations**
   - Le plugin ne délivre pas de certificat de conformité réglementaire
   - L'utilisateur doit s'assurer que ses conceptions respectent les normes applicables

4. **Utiliser des données fiables**
   - Les données des véhicules doivent provenir de sources fiables
   - L'utilisateur est responsable des données qu'il utilise

---

## 14. Documentation de référence

- [Autodesk Vehicle Tracking Documentation](https://knowledge.autodesk.com/support/vehicle-tracking)
- [Revit API Developer Guide](https://www.revitapidocs.com/)
- [pyRevit Documentation](https://pyrevit.readthedocs.io/)
- [Outils TAA - Documentation principale](../INDEX.md)
- [Outils TAA - Standards de développement](../03_Standards_Developpement.md)
- [Outils TAA - Architecture générale](../02_Architecture_Generale.md)
- [Outils TAA - Git Workflow](../07_Git_Workflow.md)

---

## 15. Historique des versions

| Version | Date | Description |
|---------|------|-------------|
| 0.1 | 2026-XX-XX | Phase P0 - Prototype initial (moteur cinématique et bibliothèque) |

---

## 16. Contacts et support

Pour toute question ou problème concernant ce module :

- Ouvrir une issue sur [GitHub](https://github.com/midka33/Outils-TAA/issues)
- Consulter la documentation existante
- Vérifier les registres de bugs

---

*Documentation générée pour le module Giration des véhicules - Outils TAA*
