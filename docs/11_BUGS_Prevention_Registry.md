# Outils TAA — Registre global de capitalisation des bugs

**Statut :** Référence de développement et de non-régression  
**Périmètre :** Tous les outils Outils TAA  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Objectif :** Transformer les erreurs rencontrées pendant le développement en règles et contrôles anti-régression réutilisables par l'ensemble du projet.

---

## 1. Rôle du registre

Ce registre est **transversal à tous les outils Outils TAA**. Il ne constitue pas une documentation spécifique à Export ou à RoomCalculator.

Chaque bug significatif rencontré pendant le développement, les tests ou la validation Revit doit être capitalisé lorsqu'il peut éviter une réapparition du problème.

Le registre complète `03_Standards_Developpement.md` et `08_Testing.md` :

- `03_Standards_Developpement.md` définit les standards généraux ;
- `08_Testing.md` définit le processus de test et de non-régression ;
- ce registre conserve les **cas concrets**, leur cause racine, leur correction et le contrôle permettant d'éviter leur réapparition.

Le registre est donc une **base de connaissance qualité commune à tous les outils**.

## 2. Cycle obligatoire de capitalisation

Chaque bug significatif suit le cycle :

```text
Bug
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
Capitalisation dans ce registre
```

Un bug corrigé mais non capitalisé reste susceptible de réapparaître dans un autre outil.

---

# 3. Bugs rencontrés sur Export

## BUG-EXPORT-001 — Propriété WPF `TreeView.VerticalScrollBarVisibility` inconnue

**Symptôme**

Au lancement de la fenêtre Export :

```text
Impossible de définir le membre inconnu
'System.Windows.Controls.TreeView.VerticalScrollBarVisibility'.
```

**Cause racine**

`VerticalScrollBarVisibility` et `HorizontalScrollBarVisibility` sont des propriétés attachées de `ScrollViewer`, et non des propriétés directes du `TreeView`. Le chargeur XAML utilisé par pyRevit/IronPython peut rejeter la syntaxe directe.

**Correction**

Utiliser :

```xml
<TreeView
    ScrollViewer.VerticalScrollBarVisibility="Auto"
    ScrollViewer.HorizontalScrollBarVisibility="Auto" />
```

**Règle préventive**

Pour chaque propriété WPF utilisée dans un XAML pyRevit, vérifier si elle appartient au contrôle ou si elle est une Attached Property. Utiliser le propriétaire correct de la propriété attachée.

**Contrôle anti-régression**

Le premier test d'une modification XAML est le chargement de la fenêtre dans Revit avec pyRevit, avant de tester la logique métier.

---

## BUG-EXPORT-002 — Collision de modules `publication_report.py`

**Symptôme**

La fenêtre de rapport ne pouvait pas être importée alors que le fichier existait.

**Cause racine**

Deux fichiers portaient le même nom `publication_report.py` : le module de fenêtre WPF et le service de résultat de publication. L'ajout du dossier `services` dans `sys.path` rendait l'import ambigu et pouvait charger le mauvais module.

**Correction**

Le module UI a été renommé `export_report_window.py` et l'import est désormais explicite :

```python
from export_report_window import PublicationReportWindow
```

**Règle préventive**

Éviter les noms de modules identiques dans des chemins placés simultanément dans `sys.path`. Les noms des modules UI doivent être suffisamment spécifiques pour éviter les collisions.

**Contrôle anti-régression**

Après ajout d'un dossier à `sys.path`, vérifier les imports des modules portant des noms génériques (`report`, `utils`, `service`, `window`, etc.).

---

## BUG-EXPORT-003 — Appel incorrect de `ShowDialog()`

**Symptôme**

La fenêtre de rapport était appelée avec une méthode inexistante / incorrecte :

```python
PublicationReportWindow(...).show_dialog()
```

**Cause racine**

Confusion entre la convention Python `snake_case` et le nom réel de la méthode WPF/.NET exposée par `Window`.

**Correction**

Utiliser :

```python
PublicationReportWindow(report, owner=self).ShowDialog()
```

**Règle préventive**

Ne pas traduire ou renommer arbitrairement les membres des objets .NET/WPF en conventions Python. Utiliser le nom réellement exposé par l'API .NET.

**Contrôle anti-régression**

Tester systématiquement les appels aux méthodes WPF/.NET depuis IronPython dans l'environnement cible.

---

## BUG-EXPORT-004 — Colonnes du tableau des mises en page vides

**Symptôme**

La fenêtre « Mises en pages du carnet » s'ouvrait mais les numéros et noms de mises en page n'étaient pas affichés.

**Cause racine**

Les bindings XAML ne correspondaient pas aux propriétés réellement exposées par le modèle Python : les bindings utilisaient une casse différente.

**Correction**

Les bindings ont été alignés sur les propriétés du modèle :

```xml
<DataGridTextColumn Header="N° de mise en page" Binding="{Binding sheet_number}" />
<DataGridTextColumn Header="Nom de mise en page" Binding="{Binding sheet_name}" />
```

**Règle préventive**

Tout binding XAML doit être vérifié contre le nom exact de la propriété du modèle, y compris la casse.

**Contrôle anti-régression**

Lorsqu'une nouvelle fenêtre DataGrid est créée, tester avec au moins une donnée réelle et vérifier visuellement que chaque colonne affiche la valeur attendue.

---

## BUG-EXPORT-005 — Carnets issus d'un paramètre transformés en carnets manuels lors de la persistance

**Symptôme**

Un carnet créé à partir d'un paramètre pouvait perdre son origine « par paramètre » lors de son enregistrement persistant.

**Cause racine**

La sauvegarde réinitialisait la source au mode manuel au lieu de conserver le mode et les informations du paramètre.

**Correction**

La persistance conserve désormais `source.mode`, `parameter_name` et `parameter_value`. Si aucune source n'existe, le mode manuel est utilisé par défaut.

**Règle préventive**

Une opération de sauvegarde ne doit pas modifier silencieusement le type ou l'origine métier d'un objet. Le modèle persistant doit conserver les informations nécessaires à sa reconstruction.

**Contrôle anti-régression**

Créer un carnet par paramètre, le sauvegarder, redémarrer l'outil et vérifier que son mode et ses données de résolution sont toujours conservés.

---

## BUG-EXPORT-006 — Carnets persistants et carnets de session ajoutés en double

**Symptôme**

Après retour de la fenêtre « Ajouter des carnets », un carnet déjà persisté pouvait être réintroduit dans la collection de session.

**Cause racine**

La fenêtre principale ajoutait indistinctement les résultats du gestionnaire à la liste temporaire avant de recharger les carnets persistants.

**Correction**

Les carnets persistants retournés par le gestionnaire ne sont pas ajoutés à `session_carnets`. La liste persistante est ensuite rechargée et filtrée.

**Règle préventive**

Séparer explicitement les objets persistants des objets temporaires et définir une source de vérité unique pour chaque catégorie.

**Contrôle anti-régression**

Créer un carnet persistant, fermer/réouvrir le gestionnaire, puis vérifier qu'il n'apparaît qu'une seule fois.

---

## BUG-EXPORT-007 — Carnets affichés provenant d'un autre projet Revit

**Symptôme**

La liste principale pouvait contenir des carnets persistants ne concernant pas le document Revit actuellement ouvert.

**Cause racine**

Les carnets persistants étaient chargés sans filtrage préalable sur les `UniqueId` des feuilles du document actif.

**Correction**

La fenêtre principale construit l'ensemble des `UniqueId` des feuilles du projet actif et conserve uniquement les carnets contenant au moins une mise en page appartenant à cet ensemble.

**Règle préventive**

Toute donnée persistante liée à des éléments Revit doit être validée par rapport au document actif avant d'être présentée à l'utilisateur.

**Contrôle anti-régression**

Ouvrir deux projets contenant des feuilles différentes et vérifier que la liste des carnets change correctement avec le document actif.

---

## BUG-EXPORT-008 — Encodage Python incompatible avec IronPython

**Symptôme**

Des fichiers Python contenant des caractères accentués pouvaient provoquer des erreurs de décodage/parsing.

**Cause racine**

Le fichier n'indiquait pas explicitement son encodage alors qu'il était exécuté par IronPython 2.

**Correction**

Tous les fichiers Python du projet doivent être enregistrés en UTF-8 et commencer par :

```python
# -*- coding: utf-8 -*-
```

**Règle préventive**

Tout nouveau fichier `.py` destiné à pyRevit doit être créé en UTF-8 avec cette déclaration d'encodage en première ligne.

**Contrôle anti-régression**

Avant intégration, vérifier les nouveaux fichiers Python contenant des accents ou commentaires français.

---

## BUG-EXPORT-009 — Publication d'une mise en page seule avec un ElementId persistant obsolète

**Symptôme**

Lorsqu'une mise en page seule était sélectionnée depuis l'arborescence puis publiée, Export affichait :

```text
ERREUR: la feuille '204' est introuvable dans le document revit
```

alors que la feuille `204` était bien présente dans le projet Revit courant.

**Cause racine**

Le `PublicationItem` persisté pouvait conserver un `sheet_id` qui n'était plus l'identifiant valide à utiliser dans le document courant. La référence persistante fiable est le `UniqueId` de l'élément Revit. La logique de publication utilisait directement l'ancien `sheet_id` au lieu de résoudre d'abord la feuille courante.

**Correction**

La publication résout désormais chaque `PublicationItem` dans le document Revit courant :

1. recherche par `unique_id` ;
2. récupération de l'`ElementId` courant ;
3. utilisation de cet `ElementId` pour l'export PDF/DWG.

La validation et l'export utilisent la même résolution afin d'éviter qu'une feuille validée soit ensuite envoyée avec un identifiant obsolète.

**Règle préventive**

Pour toute référence Revit persistante, ne jamais considérer un `ElementId` sérialisé comme une référence durable. Utiliser le `UniqueId` pour retrouver l'élément dans le document courant, puis récupérer son `ElementId` courant avant toute opération API nécessitant un `ElementId`.

**Contrôle anti-régression**

1. Créer ou enregistrer un carnet contenant une feuille.
2. Fermer et rouvrir le projet ou recharger le carnet.
3. Sélectionner uniquement cette mise en page dans l'arborescence.
4. Publier en PDF.
5. Vérifier que seule la feuille sélectionnée est publiée et qu'aucune erreur « feuille introuvable » n'apparaît.
6. Refaire le test avec un carnet complet afin de vérifier que la résolution individuelle de chaque feuille reste correcte.

---

# 4. Identifiants des bugs

Les identifiants permettent de distinguer les problèmes spécifiques d'un outil des problèmes transversaux :

```text
BUG-EXPORT-001
BUG-ROOMCALC-001
BUG-COMMON-001
BUG-UI-001
BUG-REVIT-001
BUG-TEST-001
```

Un bug commun doit être enregistré sous `BUG-COMMON-*` lorsqu'il peut concerner plusieurs outils. Les bugs propres à un outil utilisent son identifiant court.

Un bug initialement spécifique à un outil peut être reclassé comme transversal si son origine est ensuite identifiée comme commune.

---

# 5. Règle obligatoire avant toute modification et tout commit

Cette règle est **obligatoire pour tout développement Outils TAA**.

Avant de créer ou modifier du code, et impérativement avant chaque commit contenant une modification ou une création de code, le développeur doit consulter ce registre.

L'objectif n'est pas seulement de relire l'historique : il faut vérifier activement que le code créé ou modifié **ne reproduit aucune erreur déjà identifiée** et qu'il respecte les règles préventives associées.

## Procédure obligatoire

```text
1. Consulter 11_BUGS_Prevention_Registry.md
             ↓
2. Identifier les bugs/règles susceptibles de concerner la modification
             ↓
3. Relire le code créé ou modifié à la lumière de ces règles
             ↓
4. Vérifier les contrôles anti-régression applicables
             ↓
5. Corriger toute régression détectée
             ↓
6. Tester
             ↓
7. Commit
```

### Checklist avant commit

- [ ] `11_BUGS_Prevention_Registry.md` a été consulté.
- [ ] Les bugs pertinents pour la modification ont été identifiés.
- [ ] Le code modifié/créé ne reproduit pas une erreur déjà documentée.
- [ ] Les règles préventives associées sont respectées.
- [ ] Les contrôles anti-régression applicables ont été réalisés.
- [ ] Le scénario ayant provoqué les bugs concernés a été vérifié lorsque nécessaire.
- [ ] Si un nouveau bug a été découvert, il a été ajouté au registre avant le commit.

> **Aucun commit de code ne doit être considéré comme terminé tant que cette checklist n'a pas été vérifiée.**

Cette règle s'applique à tous les outils et particulièrement aux modifications de :

- Python / IronPython ;
- XAML / WPF ;
- imports et `sys.path` ;
- modèles et bindings ;
- persistance ;
- accès aux éléments Revit ;
- logique de publication ;
- tests ;
- scripts pyRevit.

---

# 6. Règles générales déduites

Les bugs ci-dessus conduisent aux règles générales suivantes :

1. **Compatibilité cible réelle :** le code doit être validé dans Revit 2025.4 + pyRevit 5.x, pas uniquement dans un environnement Python/WPF générique.
2. **XAML :** vérifier systématiquement les propriétés directes et les Attached Properties.
3. **.NET/WPF :** conserver les noms réels des membres .NET ; ne pas appliquer automatiquement les conventions Python aux API .NET.
4. **Bindings :** les noms de propriétés XAML doivent correspondre exactement au modèle exposé.
5. **Imports :** éviter les noms de modules ambigus ou dupliqués lorsque plusieurs dossiers sont ajoutés au `sys.path`.
6. **Persistance :** sauvegarder et restaurer toutes les informations nécessaires à la reconstruction fidèle de l'objet métier.
7. **Document actif :** filtrer les références persistantes Revit par rapport au document courant.
8. **Références Revit persistantes :** privilégier `UniqueId` pour retrouver un élément dans le document courant et ne pas utiliser directement un `ElementId` sérialisé comme identifiant durable.
9. **UTF-8 :** tous les scripts Python pyRevit doivent déclarer explicitement leur encodage.
10. **Régression :** toute correction d'un bug reproductible doit être accompagnée d'un contrôle ou d'un test permettant de vérifier qu'il ne revient pas.
11. **Pré-commit :** le registre global des bugs doit être consulté avant toute modification de code et impérativement avant chaque commit ; le code doit être vérifié contre les erreurs déjà capitalisées.
12. **Transversalité :** lorsqu'une erreur peut concerner plusieurs outils, sa règle préventive doit être formulée de manière générique afin que tous les outils puissent en bénéficier.

---

# 7. Procédure obligatoire lors d'un nouveau bug

Lorsqu'un nouveau traceback ou comportement incorrect est rencontré :

### Étape 1 — Conserver le symptôme exact

Copier le message d'erreur et, si possible, le traceback complet.

### Étape 2 — Identifier la première cause exploitable

Pour une erreur XAML, rechercher en priorité le premier contrôle/propriété explicitement signalé comme inconnu.

### Étape 3 — Corriger la cause racine

Éviter les contournements qui masquent seulement le symptôme.

### Étape 4 — Ajouter l'entrée au registre

Documenter :

- identifiant unique ;
- outil ou périmètre concerné ;
- symptôme ;
- cause ;
- correction ;
- règle préventive ;
- contrôle anti-régression.

### Étape 5 — Déterminer le périmètre

Décider si le bug est :

- spécifique à un outil ;
- spécifique à l'UI ;
- spécifique à Revit/pyRevit ;
- commun à plusieurs outils ;
- spécifique au processus de test.

Si la règle est transversale, elle doit être formulée pour être réutilisable par tous les outils.

### Étape 6 — Mettre à jour les standards si nécessaire

Si le bug révèle une lacune dans les standards de développement ou de test, mettre également à jour le document concerné.
