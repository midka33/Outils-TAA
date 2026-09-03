# Outils TAA – Developer Handbook

# Chapter 07 — Git Workflow

**Version :** 1.0  
**Statut :** Référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Langue :** Français  
**Année :** 2026

---

# 1. Objectif

Ce document définit les règles d'utilisation de **Git** dans le développement des outils **Outils TAA**.

L'objectif est de garantir :

- un historique compréhensible ;
- un développement parallèle maîtrisé ;
- des modifications traçables ;
- des intégrations fiables ;
- la possibilité de revenir à une version stable ;
- une collaboration simple entre développeurs ;
- une intégration contrôlée du code généré avec l'aide de l'IA.

Le dépôt Git est considéré comme une partie intégrante de l'architecture du projet.

> **Chaque modification importante doit pouvoir être comprise, identifiée et, si nécessaire, annulée.**

---

# 2. Dépôt principal

Le dépôt principal contient l'ensemble du projet Outils TAA.

Structure générale :

```text
OutilsTAA/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── ARCHITECTURE.md
├── ROADMAP.md
├── docs/
├── OutilsTAA.extension/
└── tests/
```

Le dépôt doit rester exploitable à tout moment.

---

# 3. Branche principale

La branche principale est la référence du projet.

Convention recommandée :

```text
main
```

La branche `main` doit toujours représenter une version :

- fonctionnelle ;
- testée ;
- installable ;
- compatible avec la version cible de Revit.

Il est interdit de développer directement sur `main`, sauf modification documentaire ou correction exceptionnelle explicitement maîtrisée.

---

# 4. Branches de développement

Chaque développement doit être réalisé dans une branche dédiée.

Exemples :

```text
feature/publisherai-batch-export
feature/roomcalculator-ui
feature/quality-sheet-check
fix/pdf-export-error
fix/parameter-readonly
refactor/common-settings
docs/update-ai-guide
```

Le nom de la branche doit permettre de comprendre immédiatement son objectif.

---

# 5. Types de branches

Les préfixes suivants sont recommandés.

| Préfixe | Utilisation |
|---|---|
| `feature/` | Nouvelle fonctionnalité |
| `fix/` | Correction d'un bug |
| `refactor/` | Refactorisation sans changement fonctionnel recherché |
| `docs/` | Documentation |
| `test/` | Ajout ou modification de tests |
| `perf/` | Optimisation des performances |
| `build/` | Infrastructure / packaging |
| `chore/` | Maintenance technique |

Exemple :

```text
feature/publisherai-dwg-export
```

---

# 6. Une branche = un objectif

Une branche doit correspondre à un objectif clairement identifié.

Éviter :

```text
feature/misc
```

avec simultanément :

- modification de PublisherAI ;
- correction de RoomCalculator ;
- changement de l'interface ;
- modification de la documentation.

Préférer :

```text
feature/publisherai-dwg-export
```

puis une branche séparée pour une autre évolution.

---

# 7. Créer une branche

Avant de commencer un développement :

```bash
git checkout main
git pull
git checkout -b feature/nom-de-la-fonctionnalite
```

Ou avec les commandes Git modernes :

```bash
git switch main
git pull
git switch -c feature/nom-de-la-fonctionnalite
```

Le développement commence toujours à partir d'une branche `main` à jour.

---

# 8. Vérifier son environnement

Avant de commencer :

```bash
git status
```

Puis :

```bash
git branch
```

Il faut vérifier :

- la branche active ;
- les modifications locales ;
- les fichiers non suivis ;
- l'état du dépôt.

Ne jamais commencer un développement important sans savoir sur quelle branche on travaille.

---

# 9. Commits

Les commits doivent être :

- fréquents ;
- cohérents ;
- compréhensibles ;
- suffisamment petits ;
- liés à un objectif précis.

Un commit doit représenter une unité logique.

Bon exemple :

```text
feat(publisher): add booklet grouping by subtitle
```

Mauvais exemple :

```text
modifs
```

---

# 10. Convention des messages de commit

Outils TAA utilise une convention inspirée de **Conventional Commits**.

Format :

```text
type(scope): description
```

Exemples :

```text
feat(publisher): add DWG export
fix(parameters): handle read-only parameters
refactor(common): centralize unit conversion
docs(ai): update provider architecture
test(roomcalculator): add room parameter tests
perf(publisher): reduce sheet collectors
```

---

# 11. Types de commits

| Type | Signification |
|---|---|
| `feat` | Nouvelle fonctionnalité |
| `fix` | Correction |
| `refactor` | Refactorisation |
| `docs` | Documentation |
| `test` | Tests |
| `perf` | Performance |
| `build` | Build / packaging |
| `chore` | Maintenance |
| `style` | Formatage sans changement fonctionnel |

---

# 12. Description des commits

La description doit être courte et explicite.

Préférer :

```text
fix(publisher): prevent empty booklet names
```

à :

```text
fix
```

Le commit doit expliquer **ce qui a changé**, et non simplement indiquer qu'une modification a eu lieu.

---

# 13. Commits atomiques

Éviter les commits contenant plusieurs modifications sans rapport.

Mauvais :

```text
feat: publisher + roomcalculator + UI + documentation
```

Préférer :

```text
feat(publisher): add DWG exporter
test(publisher): add DWG export tests
docs(publisher): document DWG export
```

Cela facilite :

- la revue ;
- le debug ;
- le revert ;
- le suivi de l'historique.

---

# 14. Quand faire un commit ?

Un commit doit être réalisé lorsqu'une unité logique est terminée.

Exemples :

```text
Classe créée
↓
testée
↓
commit
```

Puis :

```text
Service terminé
↓
testé
↓
commit
```

Il n'est pas nécessaire d'attendre la fin de toute la fonctionnalité.

---

# 15. Commits fonctionnels

Éviter de faire un commit après chaque ligne modifiée.

Le but n'est pas d'avoir énormément de commits mais d'avoir un historique utile.

Un bon commit doit idéalement pouvoir répondre à :

> « Pourquoi cette modification existe-t-elle ? »

---

# 16. Vérification avant commit

Avant chaque commit :

```bash
git status
```

Puis vérifier les modifications :

```bash
git diff
```

Et éventuellement :

```bash
git diff --check
```

Il faut notamment vérifier :

- les fichiers modifiés ;
- les fichiers ajoutés ;
- les fichiers supprimés ;
- les modifications involontaires ;
- les secrets éventuels.

---

# 17. Ne jamais committer de secrets

Ne jamais committer :

```text
API keys
mots de passe
tokens
credentials
certificats privés
fichiers de configuration personnels
```

Exemple interdit :

```python
MISTRAL_API_KEY = "xxxxxxxx"
```

Les fichiers sensibles doivent être exclus du dépôt avec `.gitignore`.

---

# 18. `.gitignore`

Le dépôt doit disposer d'un `.gitignore` adapté à :

- Python ;
- pyRevit ;
- Visual Studio Code ;
- Revit ;
- fichiers temporaires ;
- fichiers de cache ;
- secrets locaux.

Exemples :

```text
__pycache__/
*.pyc
.vscode/
.env
*.log
*.tmp
```

Les fichiers nécessaires au fonctionnement commun du projet doivent cependant rester versionnés.

---

# 19. Fichiers locaux

Les fichiers spécifiques à un poste de travail ne doivent pas être versionnés.

Exemples :

```text
configuration locale
logs
cache
fichiers temporaires
paramètres utilisateur
```

Un fichier d'exemple peut être fourni :

```text
config.example.json
```

sans contenir de secret.

---

# 20. Pull avant développement

Avant de commencer une nouvelle tâche :

```bash
git switch main
git pull
```

Puis créer la branche.

Cela réduit les risques de développer à partir d'une version obsolète.

---

# 21. Synchronisation d'une branche

Une branche longue doit être régulièrement synchronisée avec `main`.

Exemple :

```bash
git fetch origin
git merge origin/main
```

ou, selon la stratégie retenue :

```bash
git fetch origin
git rebase origin/main
```

Le choix entre `merge` et `rebase` doit être cohérent avec les règles de l'équipe.

---

# 22. Merge ou Rebase

Pour Outils TAA, une approche simple est recommandée :

- `rebase` pour maintenir une branche personnelle à jour ;
- `merge` ou Pull Request pour intégrer une fonctionnalité dans `main`.

Exemple :

```text
main
 │
 ├── feature/publisher
 │
 │   développement
 │
 │   rebase sur main
 │
 └── Pull Request
         ↓
        main
```

---

# 23. Résolution des conflits

Lorsqu'un conflit apparaît :

```text
<<<<<<< HEAD
version A
=======
version B
>>>>>>> branch
```

Le développeur doit comprendre les deux modifications avant de choisir.

Ne jamais résoudre un conflit simplement en supprimant arbitrairement une version.

---

# 24. Conflits dans les fichiers Revit

Les fichiers Revit `.rvt` ne doivent pas être considérés comme des fichiers Git classiques.

Git est destiné principalement au :

- code ;
- documentation ;
- configuration ;
- tests ;
- ressources.

Les modèles Revit ne doivent généralement pas être versionnés directement dans Git.

---

# 25. Développement sur Revit

Les tests doivent être réalisés sur :

- une copie du modèle ;
- un modèle de test ;
- un environnement contrôlé.

Éviter de tester une branche expérimentale directement sur un modèle de production critique.

---

# 26. Pull Request

Toute fonctionnalité significative doit passer par une Pull Request.

La Pull Request doit expliquer :

```text
Objectif
Modifications
Tests réalisés
Impacts
Points particuliers
```

Exemple :

```text
## Objectif

Ajouter l'export DWG par carnet dans PublisherAI.

## Modifications

- ajout de DwgExporter
- ajout du regroupement par Sous-titre
- création automatique des dossiers
- gestion des noms invalides

## Tests

- 3 carnets
- 25 feuilles
- noms avec caractères spéciaux
- carnet vide

## Impact

Aucune modification de l'API commune.
```

---

# 27. Revue de code

Une fonctionnalité importante doit être relue avant intégration.

La revue doit notamment vérifier :

### Architecture

- respect de l'architecture Outils TAA ;
- séparation des responsabilités ;
- réutilisation de `lib/common`.

### Revit

- transactions ;
- collecte des éléments ;
- paramètres ;
- unités ;
- performances.

### UI

- séparation logique / interface ;
- messages utilisateur ;
- gestion des erreurs.

### Qualité

- lisibilité ;
- nommage ;
- duplication ;
- tests.

---

# 28. Checklist Pull Request

Avant validation :

- [ ] La fonctionnalité répond à son objectif.
- [ ] Le code respecte l'architecture.
- [ ] Les fonctions communes existantes ont été recherchées.
- [ ] Aucun code inutilement dupliqué.
- [ ] Les erreurs sont correctement gérées.
- [ ] Les transactions sont maîtrisées.
- [ ] Les paramètres sont vérifiés.
- [ ] Les unités sont correctement gérées.
- [ ] Les tests sont réalisés.
- [ ] La documentation est mise à jour si nécessaire.
- [ ] Aucun secret n'est présent.
- [ ] Aucun fichier temporaire n'est inclus.

---

# 29. Tests avant intégration

Une Pull Request ne doit pas être intégrée uniquement parce que :

```text
"ça fonctionne chez moi"
```

Il faut tester au minimum :

- cas nominal ;
- cas vide ;
- cas invalide ;
- cas limite ;
- erreur utilisateur ;
- erreur Revit ;
- comportement après annulation.

---

# 30. Compatibilité Revit

Chaque fonctionnalité doit respecter la cible officielle du projet :

```text
Revit 2025.4
pyRevit 5.x
```

Toute modification nécessitant une autre version doit être explicitement identifiée.

---

# 31. Changements incompatibles

Une modification qui casse une API interne existante doit être traitée explicitement.

Exemple :

```text
ancienne fonction :
get_parameter_value(element, name)

nouvelle fonction :
get_parameter_value(element, parameter)
```

Il ne faut pas supprimer brutalement l'ancienne interface si d'autres outils l'utilisent.

Préférer :

```text
ancienne API
↓
dépréciation
↓
migration
↓
suppression future
```

---

# 32. CHANGELOG

Les modifications importantes doivent être reportées dans :

```text
CHANGELOG.md
```

Exemple :

```text
## [1.2.0]

### Added
- Export DWG par carnet dans PublisherAI.

### Fixed
- Gestion des paramètres en lecture seule.

### Changed
- Amélioration du regroupement des feuilles.
```

---

# 33. Releases

Les versions stables doivent être identifiées par un tag Git.

Exemple :

```text
v1.0.0
v1.1.0
v1.2.0
```

Une release doit correspondre à une version testée.

---

# 34. Versionnement sémantique

Outils TAA utilise le principe :

```text
MAJOR.MINOR.PATCH
```

Exemple :

```text
2.4.1
```

Signification :

```text
2 = version majeure
4 = nouvelle fonctionnalité
1 = correction
```

---

# 35. MAJOR

Augmenter `MAJOR` lorsqu'une évolution introduit une rupture importante.

Exemple :

```text
1.x.x
→
2.0.0
```

Cas possibles :

- architecture interne profondément modifiée ;
- API incompatible ;
- comportement majeur changé ;
- migration nécessaire.

---

# 36. MINOR

Augmenter `MINOR` lorsqu'une fonctionnalité est ajoutée sans casser la compatibilité.

Exemple :

```text
1.2.0
→
1.3.0
```

---

# 37. PATCH

Augmenter `PATCH` pour :

- corrections ;
- petits ajustements ;
- corrections de bugs ;
- améliorations sans changement majeur.

Exemple :

```text
1.3.0
→
1.3.1
```

---

# 38. Tags et releases

Une release doit idéalement contenir :

- version ;
- résumé ;
- fonctionnalités ;
- corrections ;
- éventuelles incompatibilités ;
- documentation associée.

Exemple :

```text
v1.3.0

PublisherAI
- export DWG par carnet

RoomCalculator
- nouvelle gestion des paramètres

Common
- nouvelle API de conversion d'unités
```

---

# 39. Hotfix

Pour une correction urgente sur une version stable :

```text
hotfix/
```

peut être utilisé.

Exemple :

```text
hotfix/publisher-pdf-export
```

Le correctif doit être ensuite réintégré dans la branche de développement.

---

# 40. Travail expérimental

Les fonctionnalités expérimentales peuvent utiliser :

```text
experiment/
```

ou :

```text
feature/experimental-...
```

Elles ne doivent pas être considérées comme stables tant qu'elles n'ont pas été validées.

---

# 41. Code généré avec l'IA

Le code produit avec l'aide d'une IA suit exactement les mêmes règles que le code écrit manuellement.

L'utilisation d'une IA ne justifie pas :

- un commit sans test ;
- une architecture incohérente ;
- du code non compris ;
- une API inventée ;
- une absence de revue.

Principe :

> **Le développeur est responsable du code intégré, quelle que soit son origine.**

---

# 42. Commit de code généré par IA

Il n'est pas obligatoire de créer un commit spécifique uniquement parce que l'IA a été utilisée.

En revanche, si l'origine IA est importante pour la traçabilité d'une expérimentation, elle peut être mentionnée dans la Pull Request.

Exemple :

```text
Assistance IA utilisée pour le premier prototype du service.
Code entièrement revu et adapté à l'architecture Outils TAA.
```

---

# 43. Ne pas committer les conversations IA

Les conversations complètes avec une IA ne doivent pas être ajoutées au dépôt simplement pour documenter le développement.

Seule la documentation utile au projet doit être conservée.

---

# 44. Documentation issue d'une IA

Lorsqu'une IA génère de la documentation :

1. vérifier le contenu ;
2. vérifier les API citées ;
3. vérifier les versions ;
4. vérifier les exemples ;
5. vérifier la cohérence avec le code réel.

La documentation doit toujours représenter le fonctionnement réel du projet.

---

# 45. Dépendances

Toute nouvelle dépendance doit être justifiée.

Avant d'ajouter une bibliothèque :

```text
Existe-t-il déjà une solution dans Outils TAA ?
Existe-t-il une solution native Revit ?
Est-elle réellement nécessaire ?
Est-elle compatible avec pyRevit ?
Est-elle maintenue ?
```

Une dépendance inutile augmente le risque de maintenance.

---

# 46. Modifications de `lib/common`

Les fichiers de :

```text
lib/common/
```

sont particulièrement sensibles.

Une modification de :

```text
parameter_utils.py
settings.py
transaction.py
unit_utils.py
revit_utils.py
```

peut avoir un impact sur plusieurs outils.

Ces modifications doivent donc faire l'objet d'une revue plus attentive.

---

# 47. Modification d'une API commune

Avant de modifier une API commune :

1. rechercher ses utilisations ;
2. identifier les modules dépendants ;
3. vérifier les tests ;
4. mesurer l'impact ;
5. documenter le changement ;
6. prévoir une migration si nécessaire.

Exemple :

```text
Recherche
↓
PublisherAI
RoomCalculator
Quality
Annotation
↓
Modification
↓
Tests globaux
```

---

# 48. Recherche avant création

Avant de créer une nouvelle fonction utilitaire :

```text
Recherche dans lib/common
↓
Recherche dans le module
↓
Recherche dans les autres outils
↓
Création uniquement si nécessaire
```

Cette règle limite la duplication.

---

# 49. Rebase avant Pull Request

Pour une branche ayant évolué pendant plusieurs jours, il est recommandé de la synchroniser avec `main` avant la Pull Request.

Exemple :

```bash
git fetch origin
git rebase origin/main
```

Puis effectuer les tests à nouveau.

---

# 50. Ne jamais forcer `main`

Les commandes destructrices comme :

```bash
git push --force
```

sont interdites sur `main`.

Le dépôt principal doit être protégé contre les réécritures accidentelles de l'historique.

---

# 51. Force push

Un `force push` peut éventuellement être utilisé sur une branche personnelle après un `rebase`.

Exemple :

```bash
git push --force-with-lease
```

Préférer :

```text
--force-with-lease
```

à :

```text
--force
```

car cette commande offre une protection supplémentaire contre l'écrasement de modifications distantes.

---

# 52. Protection de `main`

La branche `main` devrait être configurée avec des protections telles que :

- Pull Request obligatoire ;
- revue avant merge ;
- tests obligatoires ;
- interdiction du force push ;
- interdiction de suppression accidentelle.

---

# 53. CI / automatisation

Lorsque l'infrastructure du projet le permettra, une intégration continue pourra vérifier automatiquement :

```text
Git push
   ↓
Tests
   ↓
Vérification syntaxique
   ↓
Contrôle structure
   ↓
Validation
```

Les contrôles automatisables doivent progressivement être déplacés vers cette infrastructure.

---

# 54. Vérifications automatisables

Exemples :

- syntaxe Python ;
- imports ;
- tests unitaires ;
- détection de fichiers interdits ;
- présence de secrets ;
- conventions de nommage ;
- documentation minimale.

---

# 55. Workflow standard

Le workflow recommandé est :

```text
1. Pull de main
        ↓
2. Création de branche
        ↓
3. Développement
        ↓
4. Tests locaux
        ↓
5. Commit
        ↓
6. Push
        ↓
7. Pull Request
        ↓
8. Revue
        ↓
9. Tests
        ↓
10. Merge
        ↓
11. Tag / Release si nécessaire
```

---

# 56. Exemple complet

Pour développer une nouvelle fonctionnalité PublisherAI :

```bash
git switch main
git pull

git switch -c feature/publisherai-booklet-export
```

Développement :

```text
Création de BookletService
↓
Tests
↓
Commit
```

Puis :

```bash
git add .
git commit -m "feat(publisher): add booklet service"
```

Continuer :

```text
Création du DWG exporter
↓
Tests
↓
Commit
```

Puis :

```bash
git add .
git commit -m "feat(publisher): add DWG exporter"
```

Push :

```bash
git push -u origin feature/publisherai-booklet-export
```

Puis création de la Pull Request.

---

# 57. Workflow de correction de bug

Pour un bug :

```text
Bug identifié
    ↓
Créer fix/...
    ↓
Reproduire le problème
    ↓
Ajouter un test
    ↓
Corriger
    ↓
Tester
    ↓
Pull Request
```

L'ajout d'un test de non-régression est fortement recommandé.

---

# 58. Workflow de refactorisation

Une refactorisation ne doit pas être mélangée inutilement avec une nouvelle fonctionnalité.

Préférer :

```text
refactor(common): simplify parameter access
```

puis :

```text
feat(roomcalculator): use parameter service
```

Cela permet d'identifier clairement les changements.

---

# 59. Historique lisible

L'historique Git doit pouvoir raconter l'évolution du projet.

Exemple :

```text
feat(publisher): add booklet grouping
feat(publisher): add PDF exporter
fix(publisher): handle invalid filenames
test(publisher): add export tests
docs(publisher): document publication workflow
```

Un développeur doit pouvoir comprendre l'évolution sans lire tous les fichiers.

---

# 60. Règles fondamentales

Les règles Git Outils TAA sont :

1. **Ne pas développer directement sur `main`.**
2. **Une branche = un objectif.**
3. **Les commits doivent être cohérents et compréhensibles.**
4. **Utiliser une convention de commit commune.**
5. **Ne jamais versionner de secrets.**
6. **Tester avant intégration.**
7. **Les fonctionnalités importantes passent par Pull Request.**
8. **Les API communes nécessitent une attention particulière.**
9. **Les modèles Revit ne sont pas des fichiers Git classiques.**
10. **Les modifications assistées par IA sont soumises aux mêmes règles.**
11. **`main` doit toujours rester stable.**
12. **Une release doit correspondre à une version testée.**
13. **Toute rupture d'API doit être anticipée.**
14. **L'historique Git doit rester compréhensible.**
15. **Le dépôt doit pouvoir être repris par un autre développeur.**

---

# 61. Philosophie finale

Git n'est pas uniquement un système de sauvegarde.

Dans Outils TAA, Git constitue :

```text
Historique
+
Collaboration
+
Traçabilité
+
Revue
+
Versionnement
+
Retour arrière
+
Documentation du développement
```

Le bon workflow est donc celui qui permet à un développeur de comprendre :

> **ce qui a changé, pourquoi cela a changé, qui l'a validé et dans quelle version le changement est disponible.**

L'objectif final est de pouvoir faire évoluer **Outils TAA** pendant plusieurs années sans perdre la compréhension de son architecture ni la maîtrise de ses différentes versions.