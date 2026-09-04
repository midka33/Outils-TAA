# Outils TAA — Registre de capitalisation des bugs

**Statut :** Référence de développement  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Objectif :** Transformer les erreurs rencontrées pendant le développement en règles et contrôles anti-régression.

---

## 1. Principe

Chaque bug significatif rencontré pendant le développement doit être traité selon le cycle suivant :

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
```

Ce registre complète `03_Standards_Developpement.md`. Une règle générale doit être placée dans les standards ; le registre conserve le cas concret qui a conduit à cette règle.

---

# 2. Bugs rencontrés sur Export

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

Deux fichiers portaient le même nom `publication_report.py` :

- le module de fenêtre WPF ;
- le service de résultat de publication.

L'ajout du dossier `services` dans `sys.path` rendait l'import ambigu et pouvait charger le mauvais module.

**Correction**

Le module UI a été renommé :

```text
export_report_window.py
```

L'import est désormais explicite :

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

Tester systématiquement les appels aux méthodes WPF/NET depuis IronPython dans l'environnement cible.

---

## BUG-EXPORT-004 — Colonnes du tableau des mises en page vides

**Symptôme**

La fenêtre « Mises en pages du carnet » s'ouvrait mais les numéros et noms de mises en page n'étaient pas affichés.

**Cause racine**

Les bindings XAML ne correspondaient pas aux propriétés réellement exposées par le modèle Python : les bindings utilisaient une casse différente.

**Correction**

Les bindings ont été alignés sur les propriétés du modèle :

```xml
<DataGridTextColumn
    Header="N° de mise en page"
    Binding="{Binding sheet_number}" />

<DataGridTextColumn
    Header="Nom de mise en page"
    Binding="{Binding sheet_name}" />
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

La persistance conserve désormais :

- `source.mode` ;
- `parameter_name` ;
- `parameter_value`.

Si aucune source n'existe, le mode manuel est utilisé par défaut.

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

# 3. Règle obligatoire avant toute modification et tout commit

Cette règle est **obligatoire pour tout développement Outils TAA**.

Avant de créer ou modifier du code, et impérativement avant chaque commit contenant une modification ou une création de code, le développeur doit consulter `BUGS_Prevention_Registry.md`.

L'objectif n'est pas seulement de relire l'historique : il faut vérifier activement que le code créé ou modifié **ne reproduit aucune erreur déjà identifiée** et qu'il respecte les règles préventives associées.

## Procédure obligatoire

```text
1. Consulter BUGS_Prevention_Registry.md
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

- [ ] `BUGS_Prevention_Registry.md` a été consulté.
- [ ] Les bugs pertinents pour la modification ont été identifiés.
- [ ] Le code modifié/créé ne reproduit pas une erreur déjà documentée.
- [ ] Les règles préventives associées sont respectées.
- [ ] Les contrôles anti-régression applicables ont été réalisés.
- [ ] Le scénario ayant provoqué les bugs concernés a été vérifié lorsque nécessaire.
- [ ] Si un nouveau bug a été découvert, il a été ajouté au registre avant le commit.

> **Aucun commit de code ne doit être considéré comme terminé tant que cette checklist n'a pas été vérifiée.**

Cette règle s'applique particulièrement aux modifications de :

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

# 4. Règles générales déduites

Les bugs ci-dessus conduisent aux règles générales suivantes :

1. **Compatibilité cible réelle :** le code doit être validé dans Revit 2025.4 + pyRevit 5.x, pas uniquement dans un environnement Python/WPF générique.
2. **XAML :** vérifier systématiquement les propriétés directes et les Attached Properties.
3. **.NET/WPF :** conserver les noms réels des membres .NET ; ne pas appliquer automatiquement les conventions Python aux API .NET.
4. **Bindings :** les noms de propriétés XAML doivent correspondre exactement au modèle exposé.
5. **Imports :** éviter les noms de modules ambigus ou dupliqués lorsque plusieurs dossiers sont ajoutés au `sys.path`.
6. **Persistance :** sauvegarder et restaurer toutes les informations nécessaires à la reconstruction fidèle de l'objet métier.
7. **Document actif :** filtrer les références persistantes Revit par rapport au document courant.
8. **UTF-8 :** tous les scripts Python pyRevit doivent déclarer explicitement leur encodage.
9. **Régression :** toute correction d'un bug reproductible doit être accompagnée d'un contrôle ou d'un test permettant de vérifier qu'il ne revient pas.
10. **Pré-commit :** le registre des bugs doit être consulté avant toute modification de code et impérativement avant chaque commit ; le code doit être vérifié contre les erreurs déjà capitalisées.

---

# 5. Procédure obligatoire lors d'un nouveau bug

Lorsqu'un nouveau traceback ou comportement incorrect est rencontré :

### Étape 1 — Conserver le symptôme exact

Copier le message d'erreur et, si possible, le traceback complet.

### Étape 2 — Identifier la première cause exploitable

Pour une erreur XAML, rechercher en priorité le premier contrôle/propriété explicitement signalé comme inconnu.

### Étape 3 — Corriger la cause racine

Éviter les contournements qui masquent seulement le symptôme.

### Étape 4 — Ajouter l'entrée au registre

Documenter :

- symptôme ;
- cause ;
- correction ;
- règle préventive ;
- contrôle anti-régression.

### Étape 5 — Mettre à jour les standards si nécessaire

Si la leçon est généralisable à d'autres outils, ajouter ou renforcer la règle dans `03_Standards_Developpement.md`.

### Étape 6 — Tester le scénario initial

Le scénario qui provoquait le bug doit être rejoué avant de considérer la correction comme terminée.

### Étape 7 — Repasser par la checklist pré-commit

Avant le commit de la correction, relire le registre et vérifier que la correction elle-même ne reproduit pas un autre bug déjà capitalisé.

---

# 6. Règle de projet

> **Une erreur rencontrée une fois doit devenir une information qui protège tout le projet contre sa réapparition.**

> **Avant chaque commit de code, le registre des bugs doit être consulté et le code doit être vérifié contre les erreurs déjà capitalisées.**

Le registre doit donc évoluer avec Outils TAA. Il ne doit pas être considéré comme un historique figé.
