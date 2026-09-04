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

## 3. Bugs rencontrés sur Export

Les bugs `BUG-EXPORT-*` sont spécifiques au module Export. Les règles communes restent applicables à l'ensemble des outils.

### BUG-EXPORT-001 — Propriété WPF `TreeView.VerticalScrollBarVisibility` inconnue

**Symptôme** : erreur WPF au chargement de la fenêtre.  
**Cause** : propriétés `ScrollViewer` utilisées comme propriétés directes du `TreeView`.  
**Correction** : utiliser `ScrollViewer.VerticalScrollBarVisibility` et `ScrollViewer.HorizontalScrollBarVisibility`.  
**Règle** : vérifier le propriétaire des Attached Properties WPF.  
**Anti-régression** : charger la fenêtre dans Revit après chaque modification XAML.

### BUG-EXPORT-002 — Collision de modules `publication_report.py`

**Symptôme** : import de la fenêtre de rapport ambigu.  
**Cause** : deux modules portant le même nom dans des chemins Python différents.  
**Correction** : fenêtre renommée `export_report_window.py`.  
**Règle** : éviter les noms de modules identiques dans les chemins ajoutés à `sys.path`.  
**Anti-régression** : contrôler les imports après toute modification de `sys.path`.

### BUG-EXPORT-003 — Appel incorrect de `ShowDialog()`

**Symptôme** : appel de fenêtre WPF avec `show_dialog()`.  
**Cause** : confusion entre convention Python et membre .NET réel.  
**Correction** : utiliser `ShowDialog()`.  
**Règle** : respecter les noms des membres .NET/WPF.  
**Anti-régression** : tester les fenêtres dans IronPython/Revit.

### BUG-EXPORT-004 — Colonnes du tableau des mises en page vides

**Symptôme** : numéros et noms non affichés dans le DataGrid.  
**Cause** : casse incorrecte dans les bindings XAML.  
**Correction** : bindings alignés sur `sheet_number` et `sheet_name`.  
**Règle** : vérifier les bindings contre le modèle réel.  
**Anti-régression** : tester chaque DataGrid avec des données Revit réelles.

### BUG-EXPORT-005 — Carnets issus d'un paramètre transformés en carnets manuels

**Symptôme** : perte du mode « par paramètre » après sauvegarde.  
**Cause** : source réinitialisée lors de la persistance.  
**Correction** : conserver `source.mode`, `parameter_name` et `parameter_value`.  
**Règle** : une sauvegarde ne doit pas modifier l'origine métier.  
**Anti-régression** : sauvegarder, redémarrer et vérifier la reconstruction du carnet.

### BUG-EXPORT-006 — Carnets persistants et session ajoutés en double

**Symptôme** : doublons après retour du gestionnaire.  
**Cause** : mélange des sources persistante et temporaire.  
**Correction** : séparer les collections et recharger la persistance comme source de vérité.  
**Règle** : distinguer explicitement persistant/temporaire.  
**Anti-régression** : ouvrir plusieurs fois le gestionnaire et vérifier l'absence de doublon.

### BUG-EXPORT-007 — Carnets provenant d'un autre projet Revit

**Symptôme** : affichage de carnets appartenant à un autre projet.  
**Cause** : absence de filtrage par `UniqueId` du document actif.  
**Correction** : filtrage sur les feuilles du projet courant.  
**Règle** : toute donnée Revit persistante doit être validée contre le document actif.  
**Anti-régression** : tester deux projets distincts.

### BUG-EXPORT-008 — Encodage Python incompatible avec IronPython

**Symptôme** : erreurs de décodage/parsing avec caractères accentués.  
**Cause** : encodage non déclaré.  
**Correction** : fichiers Python en UTF-8 avec `# -*- coding: utf-8 -*-`.  
**Règle** : conserver cette déclaration sur tout nouveau `.py` pyRevit.  
**Anti-régression** : contrôler les nouveaux fichiers Python.

### BUG-EXPORT-009 — Publication d'une mise en page seule avec un ElementId persistant obsolète

**Symptôme** : feuille existante signalée comme introuvable.  
**Cause** : utilisation directe d'un `ElementId` persistant au lieu du `UniqueId`.  
**Correction** : résolution par `UniqueId`, puis récupération de l'`ElementId` courant.  
**Règle** : un `ElementId` sérialisé n'est jamais une référence durable.  
**Anti-régression** : publier une feuille seule après rechargement du carnet puis publier le carnet complet.

### BUG-EXPORT-010 — Valeur numérique incompatible avec `PDFExportQualityType`

**Symptôme** : `Cannot convert numeric value 300 to PDFExportQualityType`.  
**Cause** : affectation directe de `300` à une propriété attendante une enum Revit.  
**Correction** : conversion explicite vers `PDFExportQualityType.DPI300`.  
**Règle** : utiliser les membres des enums .NET attendus par l'API Revit.  
**Anti-régression** : tester PDF seul, combiné et séparé.

### BUG-EXPORT-011 — `CarnetController.document` absent lors de l'initialisation de la fenêtre

**Symptôme** : au lancement de Export après l'intégration de l'éditeur de nommage :

```text
AttributeError: 'CarnetController' object has no attribute 'document'
```

La trace pointe vers l'initialisation de `ExportWindow`, lors de la création de `FilenameService(controller.document)`.

**Cause racine**

`ExportWindow` a besoin du document Revit pour résoudre les variables de nommage liées au projet et aux paramètres Revit. `CarnetController` possédait déjà les services utilisant le document, mais ne l'exposait pas explicitement à l'interface.

**Correction**

`CarnetController` expose désormais :

```python
self.document = getattr(export_service, "document", None)
```

La même instance du document utilisée par `ExportService` est ainsi disponible pour les services UI concernés.

**Règle préventive**

Lorsqu'une nouvelle fonctionnalité UI nécessite le contexte Revit, ne pas supposer qu'une façade métier expose automatiquement ce contexte. Vérifier explicitement le contrat de l'objet injecté et, si nécessaire, exposer le document à un emplacement unique et cohérent.

**Contrôle anti-régression**

1. Lancer le bouton Export dans Revit 2025.4.
2. Vérifier que la fenêtre se charge sans `AttributeError`.
3. Vérifier que l'éditeur de nommage s'initialise.
4. Tester la prévisualisation d'un nom utilisant `{projet}`.
5. Tester un token `{parametre:Nom}` sur une feuille disposant du paramètre.

## 4. Identifiants des bugs

```text
BUG-EXPORT-001
BUG-EXPORT-002
BUG-EXPORT-003
BUG-EXPORT-004
BUG-EXPORT-005
BUG-EXPORT-006
BUG-EXPORT-007
BUG-EXPORT-008
BUG-EXPORT-009
BUG-EXPORT-010
BUG-EXPORT-011
BUG-ROOMCALC-001
BUG-COMMON-001
BUG-UI-001
BUG-REVIT-001
BUG-TEST-001
```

## 5. Règle obligatoire avant toute modification et tout commit

Avant de créer ou modifier du code, et impérativement avant chaque commit contenant une modification ou une création de code, le développeur doit consulter ce registre et vérifier que les règles préventives applicables sont respectées.

Tout nouveau bug significatif doit être ajouté au registre avec :

- symptôme ;
- cause racine ;
- correction ;
- règle préventive ;
- scénario de test anti-régression.

### Règles transversales minimales

1. **WPF/XAML :** vérifier les propriétés attachées et le comportement réel dans Revit.
2. **Imports Python :** éviter les collisions de noms après modification de `sys.path`.
3. **.NET :** utiliser les membres réels des API .NET/WPF.
4. **Données Revit persistantes :** privilégier `UniqueId` pour les références durables et résoudre l'`ElementId` courant.
5. **Encodage :** tous les `.py` pyRevit sont UTF-8 avec déclaration d'encodage.
6. **Énumérations Revit :** utiliser explicitement les membres des enums .NET plutôt que leurs valeurs numériques.
7. **API réelle :** vérifier les propriétés et méthodes contre la version Revit cible.
8. **Régression :** chaque bug corrigé doit avoir un scénario de test reproductible.
