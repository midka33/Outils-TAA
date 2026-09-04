# Outils TAA – Developer Handbook

# Chapter 08 — Testing

**Version :** 1.1  
**Statut :** Référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Langue :** Français  
**Année :** 2026

---

## 1. Objectif

Ce document définit la stratégie de tests du projet **Outils TAA**.

L'objectif est de garantir que les outils restent fonctionnels, fiables, compatibles avec Revit 2025.4 / pyRevit 5.x et protégés contre les régressions.

Les tests font partie du développement et ne constituent pas une étape finale.

> **Un code qui fonctionne aujourd'hui mais dont le comportement ne peut pas être vérifié demain n'est pas suffisamment fiable.**

## 2. Philosophie

La stratégie Outils TAA repose sur plusieurs niveaux :

```text
Tests unitaires
      ↓
Tests de services
      ↓
Tests d'intégration
      ↓
Tests Revit
      ↓
Validation utilisateur
```

Le niveau de test doit être proportionnel au risque de la fonctionnalité.

## 3. Les quatre niveaux principaux

### 3.1 Tests unitaires

Ils vérifient une fonction ou une classe indépendamment du reste du système.

Exemples : conversion d'unités, calcul de surface, validation de paramètre, génération de nom, validation d'une réponse IA.

### 3.2 Tests d'intégration

Ils vérifient plusieurs composants ensemble :

```text
Collector
   ↓
Service métier
   ↓
Validation
   ↓
Writer
```

### 3.3 Tests Revit / pyRevit

Certains comportements ne peuvent être validés qu'à l'intérieur de Revit : transactions, collecte d'éléments, modification de paramètres, export PDF/DWG, comportement des vues et feuilles.

### 3.4 Tests fonctionnels

Ils reproduisent le workflow réel d'un utilisateur dans Revit et permettent de valider le résultat final et l'expérience utilisateur.

## 4. Structure des tests

```text
OutilsTAA/
├── tests/
│   ├── common/
│   ├── publication/
│   ├── calculation/
│   ├── quality/
│   ├── annotation/
│   └── ai/
├── docs/
└── OutilsTAA.extension/
```

Les tests doivent suivre autant que possible la structure du code testé.

## 5. Nommage

Le nom d'un test doit décrire le comportement vérifié.

```text
test_sanitize_filename_removes_invalid_characters
test_room_calculator_sums_selected_parameters
test_read_only_parameter_is_rejected
test_empty_booklet_is_not_exported
```

Éviter les noms génériques comme `test_01` ou `test_bug`.

## 6. Arrange / Act / Assert

Les tests peuvent suivre le modèle :

```text
ARRANGE → préparer les données
ACT     → exécuter le comportement
ASSERT  → vérifier le résultat
```

## 7. Cas à couvrir

Chaque fonctionnalité doit couvrir au minimum :

- cas nominal ;
- liste vide ;
- un seul élément ;
- valeurs nulles ou vides lorsque pertinentes ;
- valeurs invalides ;
- caractères spéciaux ;
- paramètres absents ;
- paramètres en lecture seule ;
- erreurs attendues ;
- annulation utilisateur lorsque pertinente.

Les cas limites sont aussi importants que les cas nominaux.

## 8. Tests de `lib/common`

Les composants communs sont prioritaires car plusieurs modules peuvent en dépendre.

À tester particulièrement :

```text
parameter_utils.py
unit_utils.py
settings.py
file_utils.py
collector_utils.py
selection_utils.py
transaction.py
```

Une régression dans `lib/common` peut affecter plusieurs outils simultanément.

## 9. Tests des paramètres Revit

Tester notamment :

- paramètre existant ;
- paramètre inexistant ;
- paramètre en lecture seule ;
- String ;
- Integer ;
- Double ;
- ElementId ;
- valeur vide ;
- valeur invalide ;
- identification par GUID lorsque pertinente.

## 10. Tests des unités

Tester les conversions dans les deux sens :

```text
unité utilisateur → unité interne Revit
unité interne Revit → unité utilisateur
```

Les conversions doivent utiliser `UnitUtils` et non des facteurs dispersés dans le code.

## 11. Tests des fichiers

Tester :

- nom valide ;
- caractères interdits ;
- nom long ;
- fichier existant / absent ;
- dossier existant / absent ;
- conflit de nom ;
- chemin invalide.

## 12. Tests des transactions

Vérifier :

- ouverture correcte ;
- validation correcte ;
- gestion d'une exception ;
- rollback lorsque nécessaire ;
- absence de transaction inutile ;
- absence de transaction imbriquée non maîtrisée.

## 13. Modèles Revit de test

Les tests Revit doivent utiliser des modèles dédiés et contrôlés lorsque possible.

Exemple :

```text
TestModels/
├── MinimalProject.rvt
├── Export_Test.rvt
├── RoomCalculator_Test.rvt
└── QualityControl_Test.rvt
```

Les modèles doivent rester petits et contenir uniquement les éléments nécessaires au scénario.

## 14. Tests Export

Le workflow principal est :

```text
Identification des carnets
        ↓
Regroupement des feuilles
        ↓
Nommage
        ↓
Export PDF
        ↓
Export DWG
        ↓
Organisation des dossiers
        ↓
Résultat de publication
```

### Regroupement

Tester :

```text
Sous-titre identique
Sous-titre différent
Sous-titre vide
Sous-titre avec espaces
Sous-titre avec caractères spéciaux
```

### PDF

Tester :

- un carnet ;
- plusieurs carnets ;
- carnet vide ;
- feuille unique ;
- plusieurs feuilles ;
- nom nécessitant un nettoyage ;
- dossier inexistant ;
- export interrompu ;
- PDF combiné ;
- PDF séparé ;
- conservation des réglages persistants du carnet.

### DWG

Tester :

- une feuille ;
- plusieurs feuilles ;
- plusieurs carnets ;
- création du dossier par carnet ;
- nommage ;
- caractères spéciaux ;
- fichier existant ;
- échec d'export ;
- DWG combiné ;
- DWG séparé ;
- configuration DWG sélectionnée ;
- Couleur vraie lorsque demandée.

### Arborescence et persistance

Tester :

- dossier contenant plusieurs carnets ;
- carnet contenant plusieurs mises en page ;
- sélection d'un carnet dans l'arborescence ;
- réglages PDF persistants ;
- réglages DWG persistants ;
- destination persistante ;
- modèle de nommage persistant ;
- réouverture de Revit et restauration des réglages ;
- suppression d'un carnet ;
- carnet contenant une feuille du document actif ;
- carnet ne contenant aucune feuille du document actif.

## 15. Tests RoomCalculator

Tester séparément :

```text
Collecte
   ↓
Calcul
   ↓
Validation
   ↓
Écriture
```

Cas nominal :

```text
20 m² + 15 m² + 10 m² = 45 m²
```

Cas limites :

- aucune pièce ;
- une pièce ;
- pièce sans valeur ;
- paramètre inexistant ;
- paramètre cible en lecture seule ;
- valeur nulle ;
- valeur non numérique ;
- grand nombre de pièces.

## 16. Tests de l'interface WPF

Tester notamment :

- ouverture ;
- fermeture ;
- champs obligatoires ;
- valeurs invalides ;
- boutons correctement activés/désactivés ;
- progression ;
- annulation ;
- messages d'erreur ;
- conservation des paramètres utilisateur ;
- chargement XAML sans erreur ;
- bindings correspondant exactement aux propriétés du modèle ;
- absence de collision entre modules UI et services ;
- appels aux méthodes .NET/WPF avec leur nom réel.

La logique métier ne doit pas être testée uniquement via l'interface.

## 17. Tests IA

Les fonctionnalités IA doivent pouvoir être testées avec un provider simulé.

```python
class FakeAIProvider:

    def generate(self, prompt):
        return {
            "status": "success",
            "items": []
        }
```

Tester :

- réponse valide ;
- JSON invalide ;
- champ manquant ;
- type incorrect ;
- réponse vide ;
- timeout ;
- erreur réseau ;
- fournisseur indisponible ;
- action interdite ;
- élément Revit inexistant.

Une réponse IA incorrecte ne doit jamais provoquer directement une modification non contrôlée du modèle.

## 18. Tests de sécurité IA

Tester les entrées contenant des instructions parasites ou des données inattendues.

Le contenu provenant de Revit ou d'une source externe doit être considéré comme une donnée et non comme une instruction exécutable.

## 19. Tests de performance

Les opérations traitant beaucoup d'éléments doivent être mesurées :

- collecte de milliers d'éléments ;
- calcul de nombreuses pièces ;
- publication de nombreux carnets ;
- traitement de nombreuses feuilles ;
- appels IA groupés.

Principe :

```text
Mesurer
↓
Identifier le goulot
↓
Optimiser
↓
Mesurer à nouveau
```

## 20. Tests de compatibilité

La cible officielle est :

```text
Revit 2025.4
pyRevit 5.x
```

Une fonctionnalité non compatible avec cette cible n'est pas considérée comme validée.

## 21. Registre global des bugs et non-régression

Le registre **`11_BUGS_Prevention_Registry.md`** est une ressource transversale du projet Outils TAA. Il n'est pas spécifique à un outil.

Il capitalise les erreurs réellement rencontrées afin qu'elles deviennent des règles préventives et des contrôles de non-régression pour l'ensemble du projet.

La relation entre les tests et le registre est :

```text
Bug rencontré
      ↓
Reproduction
      ↓
Cause racine
      ↓
Correction
      ↓
Règle préventive
      ↓
Test / contrôle anti-régression
      ↓
Capitalisation dans 11_BUGS_Prevention_Registry.md
```

### Règle obligatoire avant toute modification de code

Avant de créer ou modifier du code, le développeur doit consulter le registre et identifier les règles susceptibles de concerner la modification.

Cela s'applique notamment à :

- Python / IronPython ;
- XAML / WPF ;
- imports et `sys.path` ;
- modèles et bindings ;
- persistance ;
- accès aux éléments Revit ;
- logique de publication ;
- tests ;
- scripts pyRevit.

### Règle obligatoire avant chaque commit de code

Avant chaque commit contenant une modification ou une création de code :

```text
1. Consulter 11_BUGS_Prevention_Registry.md
2. Identifier les bugs/règles pertinents
3. Relire le code modifié ou créé
4. Vérifier les contrôles anti-régression applicables
5. Corriger les éventuelles régressions
6. Tester
7. Commit
```

Checklist minimale :

- [ ] Registre global consulté.
- [ ] Bugs pertinents identifiés.
- [ ] Code vérifié contre les erreurs déjà capitalisées.
- [ ] Règles préventives respectées.
- [ ] Contrôles anti-régression réalisés.
- [ ] Nouveau bug ajouté au registre s'il a été découvert.

> **Un commit de code n'est pas considéré comme terminé tant que cette vérification n'a pas été effectuée.**

## 22. Tests de non-régression

Chaque bug important doit idéalement devenir un test :

```text
Bug détecté
    ↓
Test reproduisant le bug
    ↓
Correction
    ↓
Test réussi
    ↓
Règle ajoutée au registre global
```

Les tests correspondant à un bug corrigé ne doivent pas être supprimés sans justification documentée.

Lorsqu'un bug concerne un composant commun, les outils qui en dépendent doivent également être vérifiés.

## 23. Tests déterministes

Éviter les dépendances inutiles :

- heure système ;
- réseau ;
- fichiers temporaires persistants ;
- ordre aléatoire ;
- état précédent du modèle ;
- configuration personnelle.

Un test intermittent doit être traité comme un problème à corriger.

## 24. Tests automatisés

Les tests sans dépendance directe à Revit doivent être automatisés lorsque possible.

```text
git push
   ↓
Tests automatiques
   ↓
Validation
```

Les tests nécessitant Revit peuvent conserver un processus dédié si leur automatisation complète n'est pas réaliste.

## 25. CI future

À terme, une CI pourra contrôler automatiquement :

```text
Syntaxe Python
↓
Tests unitaires
↓
Imports
↓
Secrets
↓
Structure du dépôt
↓
Documentation
↓
Contrôles issus du registre des bugs
```

Les tests Revit pourront être exécutés dans un environnement contrôlé dédié si l'infrastructure le permet.

## 26. Couverture

La couverture de code est un indicateur et non un objectif absolu.

La priorité doit être donnée aux zones critiques :

```text
lib/common
Calculs
Validation
Export
Écriture Revit
Gestion des erreurs
```

100 % de couverture ne garantit pas l'absence de défaut.

## 27. Validation manuelle

Certains comportements doivent rester validés manuellement :

- rendu de l'interface ;
- lisibilité du PDF ;
- contenu du DWG ;
- expérience utilisateur ;
- workflow complet dans Revit.

Les tests automatisés complètent la validation humaine mais ne la remplacent pas complètement.

## 28. Tests avant Pull Request

```text
☐ Tests unitaires
☐ Tests d'intégration concernés
☐ Tests Revit concernés
☐ Scénario principal testé manuellement
☐ Cas limites vérifiés
☐ Aucun secret
☐ Documentation mise à jour
☐ 11_BUGS_Prevention_Registry.md consulté
☐ Contrôles anti-régression applicables réalisés
☐ Nouveaux bugs capitalisés
```

## 29. Tests avant Release

```text
☐ Tests unitaires complets
☐ Tests des modules modifiés
☐ Tests Revit
☐ Export testé si concerné
☐ RoomCalculator testé si concerné
☐ Exports vérifiés
☐ Installation vérifiée
☐ Documentation vérifiée
☐ CHANGELOG vérifié
☐ Registre global des bugs à jour
```

## 30. Rapport de test

Pour une fonctionnalité importante, conserver une trace simple :

```text
Fonctionnalité : Export – Publication DWG
Version : 1.2.0
Revit : 2025.4

Tests :
✓ 1 carnet
✓ 3 carnets
✓ 20 feuilles
✓ noms spéciaux
✓ dossier existant
✓ dossier inexistant
✓ erreur d'export

Résultat : VALIDÉ
```

## 31. Modification de `lib/common`

Après toute modification d'une API commune, il faut vérifier les modules qui en dépendent.

Exemple :

```text
parameter_utils.py modifié
        ↓
Export
RoomCalculator
Quality
Annotation
        ↓
Tests concernés
        ↓
Contrôle des bugs communs
```

Une modification commune ne doit pas être considérée comme validée par le seul test du fichier modifié.

## 32. Test fonctionnel Export complet

```text
Ouvrir modèle de test
        ↓
Lancer Export
        ↓
Sélectionner plusieurs carnets
        ↓
Vérifier l'arborescence
        ↓
Vérifier les réglages persistants
        ↓
Publier PDF + DWG
        ↓
Vérifier les dossiers
        ↓
Vérifier les PDF
        ↓
Vérifier les DWG
        ↓
Vérifier le rapport
```

## 33. Test fonctionnel RoomCalculator complet

```text
Ouvrir modèle de test
        ↓
Sélectionner les pièces
        ↓
Choisir les paramètres
        ↓
Lancer le calcul
        ↓
Vérifier le résultat
        ↓
Écrire le résultat
        ↓
Vérifier le paramètre Revit
```

## 34. Processus lorsqu'un test échoue

```text
Test échoué
↓
Reproduire
↓
Identifier la cause
↓
Déterminer bug ou test incorrect
↓
Corriger
↓
Relancer le test
↓
Relancer les tests liés
↓
Capitaliser le bug si nécessaire
```

Si la cause correspond à une nouvelle erreur reproductible, elle doit être ajoutée à `11_BUGS_Prevention_Registry.md` avant la clôture de la correction.

## 35. Checklist développeur

### Code

- [ ] Cas nominal testé.
- [ ] Cas limites testés.
- [ ] Exceptions importantes testées.
- [ ] Dépendances contrôlées.
- [ ] Registre global des bugs consulté.

### Revit

- [ ] Transactions testées.
- [ ] Paramètres testés.
- [ ] Unités testées.
- [ ] Modèle de test utilisé.

### UI

- [ ] Ouverture testée.
- [ ] Validation des entrées testée.
- [ ] Erreurs testées.
- [ ] Annulation testée si pertinente.
- [ ] XAML chargé dans l'environnement cible.
- [ ] Bindings vérifiés.

### IA

- [ ] Provider simulé disponible.
- [ ] Réponse invalide testée.
- [ ] Timeout testé.
- [ ] Validation de sortie testée.

### Publication

- [ ] PDF vérifié.
- [ ] DWG vérifié.
- [ ] Nommage vérifié.
- [ ] Dossiers vérifiés.
- [ ] Réglages persistants vérifiés si concernés.

## 36. Règles fondamentales

1. **Tout comportement critique doit être testable.**
2. **Les calculs doivent être testés indépendamment de Revit lorsque possible.**
3. **Les API communes doivent être particulièrement bien testées.**
4. **Les cas limites sont aussi importants que les cas nominaux.**
5. **Tout bug significatif doit produire une protection contre sa réapparition.**
6. **Le registre `11_BUGS_Prevention_Registry.md` est transversal à tous les outils.**
7. **La consultation du registre est obligatoire avant toute modification de code et avant tout commit de code.**
8. **Une correction n'est terminée qu'après validation du scénario qui provoquait le bug.**
