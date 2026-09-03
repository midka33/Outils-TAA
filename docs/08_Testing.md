# Outils TAA – Developer Handbook

# Chapter 08 — Testing

**Version :** 1.0  
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
├── PublisherAI_Test.rvt
├── RoomCalculator_Test.rvt
└── QualityControl_Test.rvt
```

Les modèles doivent rester petits et contenir uniquement les éléments nécessaires au scénario.

## 14. Tests PublisherAI

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

Exemple :

```text
A101 → PRO
A102 → PRO
A103 → DCE
```

Résultat attendu :

```text
PRO → A101, A102
DCE → A103
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
- export interrompu.

Le fichier PDF réel doit être vérifié lorsque le test porte sur l'export.

### DWG

Tester :

- une feuille ;
- plusieurs feuilles ;
- plusieurs carnets ;
- création du dossier par carnet ;
- nommage ;
- caractères spéciaux ;
- fichier existant ;
- échec d'export.

### Résultat

Le `PublicationResult` doit permettre de vérifier au minimum :

```text
success
exported_pdf_count
exported_dwg_count
skipped_count
errors
output_directory
```

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
- conservation des paramètres utilisateur.

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

## 21. Tests de non-régression

Chaque bug important doit idéalement devenir un test :

```text
Bug détecté
    ↓
Test reproduisant le bug
    ↓
Correction
    ↓
Test réussi
```

Ne jamais supprimer un test uniquement parce qu'il échoue après une modification.

## 22. Tests déterministes

Éviter les dépendances inutiles :

- heure système ;
- réseau ;
- fichiers temporaires persistants ;
- ordre aléatoire ;
- état précédent du modèle ;
- configuration personnelle.

Un test intermittent doit être traité comme un problème à corriger.

## 23. Tests automatisés

Les tests sans dépendance directe à Revit doivent être automatisés lorsque possible.

```text
git push
   ↓
Tests automatiques
   ↓
Validation
```

Les tests nécessitant Revit peuvent conserver un processus dédié si leur automatisation complète n'est pas réaliste.

## 24. CI future

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
```

Les tests Revit pourront être exécutés dans un environnement contrôlé dédié si l'infrastructure le permet.

## 25. Couverture

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

## 26. Validation manuelle

Certains comportements doivent rester validés manuellement :

- rendu de l'interface ;
- lisibilité du PDF ;
- contenu du DWG ;
- expérience utilisateur ;
- workflow complet dans Revit.

Les tests automatisés complètent la validation humaine mais ne la remplacent pas complètement.

## 27. Tests avant Pull Request

```text
☐ Tests unitaires
☐ Tests d'intégration concernés
☐ Tests Revit concernés
☐ Scénario principal testé manuellement
☐ Cas limites vérifiés
☐ Aucun secret
☐ Documentation mise à jour
```

## 28. Tests avant Release

```text
☐ Tests unitaires complets
☐ Tests des modules modifiés
☐ Tests Revit
☐ PublisherAI testé si concerné
☐ RoomCalculator testé si concerné
☐ Exports vérifiés
☐ Installation vérifiée
☐ Documentation vérifiée
☐ CHANGELOG vérifié
```

## 29. Rapport de test

Pour une fonctionnalité importante, conserver une trace simple :

```text
Fonctionnalité : PublisherAI – Export DWG
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

## 30. Modification de `lib/common`

Après toute modification d'une API commune, il faut vérifier les modules qui en dépendent.

Exemple :

```text
parameter_utils.py modifié
        ↓
PublisherAI
RoomCalculator
Quality
Annotation
        ↓
Tests concernés
```

Une modification commune ne doit pas être considérée comme validée par le seul test du fichier modifié.

## 31. Test fonctionnel PublisherAI complet

```text
Ouvrir modèle de test
        ↓
Lancer PublisherAI
        ↓
Sélectionner plusieurs carnets
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

## 32. Test fonctionnel RoomCalculator complet

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

## 33. Processus lorsqu'un test échoue

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
```

## 34. Checklist développeur

### Code

- [ ] Cas nominal testé.
- [ ] Cas limites testés.
- [ ] Exceptions importantes testées.
- [ ] Dépendances contrôlées.

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

## 35. Règles fondamentales

1. **Tout comportement critique doit être testable.**
2. **Les calculs doivent être testés indépendamment de Revit lorsque possible.**
3. **Les API communes doivent être particulièrement bien testées.**
4. **Les cas limites sont aussi importants que les cas nominaux.**
5. **Chaque bug important doit idéalement devenir un test de non-régression.**
6. **Les tests Revit doivent utiliser des modèles contrôlés.**
7. **Les tests ne doivent pas dépendre inutilement du poste du développeur.**
8. **Les fonctionnalités IA doivent être testables sans dépendre systématiquement d'une API réelle.**
9. **Les tests automatisés ne remplacent pas les validations fonctionnelles humaines.**
10. **Une modification de `lib/common` nécessite une vérification des modules dépendants.**
11. **Un test qui échoue ne doit pas être supprimé pour masquer le problème.**
12. **La couverture est un indicateur, pas une finalité.**
13. **Les tests doivent rester simples, lisibles et maintenables.**
14. **Une release doit être testée sur la version cible de Revit.**
15. **La fiabilité du logiciel passe avant la rapidité de livraison.**

## 36. Philosophie finale

La stratégie de test Outils TAA doit permettre de faire évoluer le projet sans introduire progressivement de régressions invisibles.

```text
Développer
    ↓
Tester
    ↓
Revoir
    ↓
Intégrer
    ↓
Tester à nouveau
    ↓
Publier
```

> **Le meilleur test est celui qui permet à un développeur de modifier le code avec confiance.**
