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

**Symptôme** : `AttributeError: 'CarnetController' object has no attribute 'document'` au lancement de Export.  
**Cause** : le contexte Revit n'était pas exposé explicitement par la façade métier.  
**Correction** : `CarnetController` expose le document utilisé par `ExportService`.  
**Règle** : vérifier explicitement le contrat des dépendances injectées par l'UI.  
**Anti-régression** : lancer Export et tester la prévisualisation de nommage.

### BUG-EXPORT-012 — Une modification de carnet transformait tous les réglages hérités en surcharges locales

**Symptôme** : un carnet affichant des réglages hérités du dossier cessait d'hériter après modification d'un seul champ.  
**Cause** : la sauvegarde réécrivait simultanément toutes les valeurs affichées par l'UI, y compris celles provenant du dossier.  
**Correction** : une modification UI ne sauvegarde désormais que le champ effectivement modifié. Les autres champs restent à `None` lorsqu'ils sont hérités.  
**Règle** : ne jamais persister une valeur effective comme une surcharge locale sans action explicite de l'utilisateur.  
**Anti-régression** : définir un réglage au niveau dossier, vérifier son héritage dans un carnet, modifier uniquement un autre réglage du carnet et vérifier que le premier reste hérité.

### BUG-EXPORT-013 — Publication de dossier utilisant une seule destination pour plusieurs carnets

**Symptôme** : lors d'une publication multiple, la prévisualisation pouvait afficher une destination unique alors que les carnets utilisaient des destinations différentes.  
**Cause** : l'agrégation de prévisualisation conservait la dernière destination rencontrée.  
**Correction** : l'aperçu signale désormais explicitement plusieurs destinations et conserve le chemin complet sur chaque ligne de livrable.  
**Règle** : une agrégation multi-carnets ne doit jamais masquer une différence de configuration entre les unités publiées.  
**Anti-régression** : créer deux carnets d'un même dossier avec deux destinations différentes, lancer `Publier le dossier` et vérifier que les deux destinations sont visibles avant confirmation.

### BUG-EXPORT-014 — Glisser-déposer des carnets non opérationnel et absence de sélection multiple

**Symptôme** : les carnets ne pouvaient pas être déplacés à la souris pour changer de dossier ou d'ordre, et plusieurs carnets ne pouvaient pas être sélectionnés pour un déplacement groupé.  
**Cause** : le premier mécanisme de drag-and-drop transmettait directement un objet Python WPF et ne disposait d'aucun état de sélection multiple. Le `TreeView` WPF ne fournit pas nativement de sélection multiple.  
**Correction** : ajout d'un `DataObject` WPF avec format de données explicite, sélection `Ctrl` / `Maj`, surbrillance des carnets sélectionnés et nouvelle opération repository `move_sets` permettant le déplacement groupé avec conservation de l'ordre.  
**Règle** : pour un `TreeView` WPF nécessitant une sélection multiple, implémenter explicitement l'état de sélection et utiliser un format de données WPF explicite pour le drag-and-drop.  
**Anti-régression** : sélectionner plusieurs carnets avec `Ctrl` ou une plage avec `Maj`, les glisser vers un dossier, puis les glisser sur un carnet cible pour vérifier leur insertion avant celui-ci et la persistance de l'ordre après fermeture/réouverture.

### BUG-EXPORT-015 — Handler `ExportWindow` manquant après refactorisation et couche de compatibilité incorrecte

**Symptôme** : au lancement de l'outil, IronPython levait d'abord `AttributeError: 'type' object has no attribute 'Publish_Click'` dans `publication_preview_integration.py`. Après ajout de la couche de compatibilité, une seconde erreur apparaissait : `AttributeError: 'ExportWindow' object has no attribute '_set_no_selection_compat'` lors de la mise à jour de la sélection.  
**Cause** : `publication_preview_integration.py` supposait que plusieurs handlers historiques (`Publish_Click`, `OpenCarnetManager_Click`, etc.) existaient encore dans `ExportWindow`, alors qu'une refactorisation les avait retirés ou déplacés. La couche de compatibilité introduite pour les réinjecter contenait elle-même un appel vers `_set_no_selection_compat`, nom qui n'était pas exposé sur l'instance alors que le vrai `_set_no_selection()` existait déjà.  
**Correction** : injection des handlers manquants avant création de la fenêtre et correction de `update_selection_info()` pour appeler le handler canonique `_set_no_selection()`. Le correctif immédiat a été commit dans `d795989882098e75f3dcdc759954f11c00217605`.  
**Règle** : les handlers d'événements WPF doivent avoir un propriétaire canonique, idéalement `ExportWindow`. Une couche d'intégration doit décorer ou envelopper ces handlers, pas multiplier les alias incompatibles. Toute refactorisation de l'UI doit vérifier les contrats attendus par les intégrations.  
**Anti-régression** : charger `ExportWindow` dans IronPython/Revit et déclencher successivement : sélection d'un dossier, sélection d'un carnet, sélection d'une feuille, retour à aucune sélection, ouverture du gestionnaire de carnets, création/sélection d'un dossier, modification des paramètres, prévisualisation puis publication d'un carnet et d'une feuille. Vérifier qu'aucun `AttributeError` lié à un handler attendu par l'intégration n'apparaît.

### BUG-EXPORT-016 — Historique non enregistré lorsque `MODIFIED_ONLY` était désactivé

**Symptôme** : le socle Stage 07 pouvait filtrer correctement les publications en `MODIFIED_ONLY`, mais le chemin de publication classique ne préparait pas d'information d'historique et pouvait donc laisser le carnet sans nouvel état après une publication réussie.

**Cause** : l'intégration associait initialement les informations de classification uniquement au chemin `modified_only=True`. L'enregistrement de l'historique était donc conditionné à l'activation de cette option, alors que l'historique doit servir de référence pour les publications suivantes quel que soit le mode utilisé.

**Correction** : calculer systématiquement les états courants et la classification avant publication ; l'enregistrement post-publication est maintenant déclenché après toute publication réussie. Le filtrage `MODIFIED_ONLY` ne fait que réduire le périmètre transmis au moteur.

**Règle** : l'historique de publication est indépendant du mode de sélection. Toute publication réussie d'un carnet doit mettre à jour sa référence historique.

**Anti-régression** : publier un carnet avec `MODIFIED_ONLY` désactivé, activer ensuite `MODIFIED_ONLY` sans modifier aucune feuille et vérifier que les feuilles sont reconnues comme `UNCHANGED` et ne sont pas republiées.

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
BUG-EXPORT-012
BUG-EXPORT-013
BUG-EXPORT-014
BUG-EXPORT-015
BUG-EXPORT-016
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
