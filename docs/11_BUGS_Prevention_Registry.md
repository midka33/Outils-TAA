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

### BUG-EXPORT-017 — Dossiers persistants visibles dans un nouveau projet Revit

**Symptôme** : après fermeture d'un projet puis création d'un nouveau `Projet1`, les dossiers persistants (`DCE`, `APD`, `DPC`, etc.) du projet précédent réapparaissaient dans Export, y compris après redémarrage complet de Revit.  
**Cause** : l'identité du projet non enregistré reposait sur des identifiants qui ne constituent pas une identité documentaire durable et, surtout, les dossiers étaient lus sans identité de projet propre. `ProjectInformation.UniqueId` pouvait être identique entre des projets indépendants et les dossiers du JSON n'étaient pas explicitement rattachés au projet courant.  
**Correction** : ajout d'un GUID Outils TAA embarqué dans le document Revit via Extensible Storage/DataStorage ; la persistance est désormais indexée par cette identité. Le JSON contient également `project_identity` et refuse tout stockage ne correspondant pas au document actif. Les anciennes clés de stockage sont migrées vers la nouvelle identité lorsqu'elles correspondent au document courant.  
**Règle** : une configuration Export persistante doit être isolée par une identité documentaire propre, persistante et embarquée dans le fichier Revit ; les dossiers ne doivent jamais être considérés comme des données globales à l'utilisateur.  
**Anti-régression** : créer un projet A, créer des dossiers/carnets, fermer Revit, créer un nouveau projet B sans l'enregistrer et ouvrir Export : seul `Général` doit apparaître. Redémarrer Revit et refaire le test. Puis enregistrer A, rouvrir A et vérifier que ses dossiers/carnets sont restaurés.

### BUG-EXPORT-018 — `_folder_targets` non disponible lors de la sélection d'un dossier

**Symptôme** : même sans créer de dossier, un clic sur `Général` provoquait une erreur IronPython `NameError: global name '_folder_targets' is not defined` dans `publication_preview_integration.py`, depuis `selection_changed_with_folder_action()` puis `update_selection_info()`.

**Cause** : le helper `_folder_targets` était défini dans `publication_folder.py` mais utilisé comme une globale du module `publication_preview_integration.py` sans import explicite. Une première tentative de correction reposait sur une injection dynamique via `sys.modules`, dépendante de l'identité et de l'ordre de chargement du module sous IronPython, ce qui n'est pas un contrat fiable.

**Correction** : import explicite du helper dans `publication_preview_integration.py` : `from publication_folder import PublicationFolder, _folder_targets`. Suppression de l'injection dynamique depuis `publication_folder.py`.

**Règle** : une fonction utilisée comme globale d'un module doit être importée ou définie explicitement dans ce module. Ne pas utiliser `sys.modules`, `builtins` ou des injections de namespace comme mécanisme normal de dépendance entre modules pyRevit/IronPython.

**Anti-régression** : ouvrir Export dans Revit 2025.4 sans créer de dossier supplémentaire, cliquer sur `Général`, puis cliquer successivement sur chaque dossier créé. Vérifier qu'aucune `NameError`, `UnboundNameException` ou fermeture de Revit ne se produit. Tester ensuite la sélection d'un carnet et d'une mise en page.

### BUG-EXPORT-019 — Sélection multiple et déplacement relatif incomplets dans l'arborescence

**Symptôme** : lors de la première validation du réordonnancement, la sélection multiple et le déplacement relatif vers le bas n'étaient pas fiables : plusieurs éléments ne pouvaient pas toujours être déplacés ensemble et un élément unique pouvait être déplacé au-dessus d'une cible mais pas en dessous. Le maintien de l'état ouvert du parent était en revanche attendu après déplacement.

**Cause** : la gestion de la sélection WPF reposait sur un état insuffisamment fiable sous IronPython, et la détermination de la zone de dépôt ne couvrait pas correctement le cas `AFTER` pour tous les éléments de l'arborescence.

**Correction** : fiabilisation de la sélection `Ctrl` / `Maj`, ajout d'un calcul explicite des zones `BEFORE` / `AFTER` / `INSIDE` pour les dossiers et du positionnement relatif pour carnets et mises en page. L'état des dossiers et carnets ouverts est capturé avant le déplacement puis restauré après rafraîchissement de l'arborescence.

**Règle** : toute fonction de réordonnancement WPF doit traiter explicitement les trois opérations `BEFORE`, `AFTER` et `INSIDE` lorsque le type de nœud le permet, et la sélection multiple doit être gérée indépendamment de la sélection native du `TreeView`.

**Anti-régression** : avec trois éléments `A / B / C`, vérifier le déplacement de `A` sous `B`, de `C` sous `A`, et, pour les dossiers, de `B` dans `A`. Sélectionner plusieurs carnets, mises en page puis dossiers avec `Ctrl`, les déplacer ensemble et vérifier la persistance de l'ordre après fermeture/réouverture. Vérifier également qu'un parent initialement développé reste développé après le déplacement.

### BUG-EXPORT-020 — Fermeture de l'arborescence après rafraîchissement

**Symptôme :** après ajout d'un carnet ou d'une mise en page, le dossier et/ou le carnet précédemment développé se refermait.

**Cause :** `_refresh_tree()` reconstruisait entièrement le `TreeView` après chaque opération sans restaurer l'état `IsExpanded` des nœuds.

**Correction :** la couche d'intégration mémorise les dossiers et carnets développés avant le rafraîchissement puis restaure leur état après reconstruction.

**Règle préventive :** tout rafraîchissement doit conserver les états ouverts.

**Test de non-régression :** TEST-04 — ajouter un carnet puis plusieurs mises en page en conservant les parents développés.

### BUG-EXPORT-021 — Sélection d'un profil appelant un handler inexistant

**Symptôme :** l'utilisation du contrôle Profil provoquait une erreur/crash de l'application. Le code appelait `self.Profile_SelectionChanged(...)`, alors que cette méthode n'existait pas dans `ExportWindow`.

**Cause :** le handler XAML `ProfileChanged` avait été injecté comme couche de compatibilité, mais son implémentation appelait un ancien nom de handler qui n'était plus présent après refactorisation.

**Correction :** implémentation directe de `ProfileChanged`, ajout des handlers `SaveProfile_Click`, `DeleteProfile_Click` et `SettingsChanged`, application persistante du profil au carnet et gestion explicite des profils intégrés/personnalisés.

**Règle préventive :** chaque handler doit appeler une API réellement disponible et avoir un propriétaire explicite.

**Test de non-régression :** TEST-14 et TEST-44 — sélectionner un profil, appliquer un profil, enregistrer puis supprimer un profil personnalisé sans exception WPF/IronPython.

### BUG-EXPORT-022 — PDF séparé exécuté comme une succession de PDF combinés

**Symptôme :** le mode PDF séparé d'un carnet provoquait un crash de Revit pendant la publication.

**Cause :** l'ancien orchestrateur parcourait les feuilles une par une et appelait `Document.Export` avec `Combine=True` pour chaque feuille. Cela ne correspondait pas au mode PDF séparé demandé par l'utilisateur et multipliait les appels au moteur PDF natif.

**Correction :** le mode séparé utilise maintenant `PDFExportOptions.Combine=False` et transmet toutes les feuilles du périmètre dans un seul appel natif `Document.Export`. Autodesk indique que `Combine=False` est précisément le mode prévu pour créer un PDF par vue/feuille ; les noms sont alors générés par la règle de nommage PDF de Revit.

**Règle préventive :** utiliser un seul appel natif par périmètre ; ne pas confondre correction statique et validation du crash dans Revit.

**Test de non-régression :** TEST-14 — publier un carnet de plusieurs feuilles en PDF séparé et vérifier qu'un PDF est produit par feuille sans crash de Revit.

### BUG-EXPORT-023 — Noms PDF séparés annoncés différents des fichiers créés

**Symptôme :** aperçu et rapport annoncent des noms TAA alors que Revit utilise sa règle native.
**Cause :** le modèle TAA n'était ni transmis au moteur ni appliqué après export ; le modèle hérité du dossier n'était pas transmis aux chemins de publication.
**Correction :** un export natif groupé `Combine=False` dans un répertoire temporaire, règle explicite `taa_` + numéro de feuille, correspondance exacte puis livraison sous les noms TAA. Les réglages effectifs sont transmis sur une copie du carnet, sans modifier l'héritage persistant. Une collision dans un carnet bloque avant export. Les anciens fichiers sont sauvegardés pendant la livraison et restaurés si celle-ci échoue.
**Règle préventive :** ne jamais annoncer un chemin calculé comme livré sans vérifier le fichier correspondant ; ne jamais associer les PDF par ordre de répertoire. Vérifier les correspondances de noms après nettoyage et refuser les ambiguïtés.
**Anti-régression :** `tests/test_pdf_delivery.py` couvre ordre natif inversé, noms personnalisés, collisions, sortie partielle/vide, retour False, exception, restauration et contrat des options Revit simulées ; TEST-14 dans Revit reste obligatoire.

### BUG-EXPORT-024 — Gestionnaire de glisser-déposer instancié trois fois

**Symptôme :** trois jeux de handlers WPF abonnés au même arbre, avec risque d'opérations multiples.
**Cause :** initialisation dans `ExportWindow`, son intégration et `script.main()` sous deux noms d'attributs.
**Correction :** `ExportWindow._drag_drop_manager` est l'unique propriétaire ; suppression des deux autres constructions et imports.
**Règle préventive :** une seule instance responsable de l'abonnement aux événements d'un contrôle.
**Anti-régression :** `test_drag_drop_has_one_constructor_owner` ; reprendre TEST-04 et un déplacement Ctrl/Maj dans Revit.

### BUG-TEST-002 — Tests désynchronisés des contrats de publication et de diagnostics

**Symptôme :** quatre échecs hors Revit.
**Cause :** fausses vues sans `Id` ; assertion d'identité de liste incompatible avec la copie défensive des diagnostics.
**Correction :** doubles exposant l'identifiant courant et test de contenu/non-mutation de la liste source. Les tests de lot utilisent le modèle réel PublicationSet.
**Règle préventive :** les doubles doivent respecter les propriétés effectivement lues ; vérifier le contrat métier plutôt qu'imposer une identité mémoire non spécifiée.
**Anti-régression :** suite pytest complète, avec `--import-mode=importlib` pour les deux fichiers `test_project_identity.py`.

### BUG-EXPORT-025 — Rapport masquant la cause d'un échec de publication

**Symptôme :** TEST-14 sur `858f858` : aucun PDF publié selon le retour utilisateur,
lignes « ERREUR » avec détail « Export terminé. », bas de fenêtre « 1 erreur(s) ».
**Cause confirmée du rapport :** l'orchestrateur transmet les exceptions dans
`report.errors`, mais la fenêtre n'affichait que leur nombre ; les lignes sans
message utilisaient un texte de succès indépendamment de leur statut. Elle ne
lisait pas non plus les champs `path` et `carnet` des résultats actuels.
**Correction :** erreurs/avertissements complets dans une zone copiable et
défilante, détail d'échec explicite et lecture des champs actuels.
**Règle préventive :** tester le contrat complet service → rapport, y compris
une erreur globale sans erreur locale et un échec avant création des lignes.
**Anti-régression :** `tests/test_export_report_window.py` (fenêtre simulée et
contrôle XAML), puis copier le diagnostic réel depuis Revit 2025.4.
**Suite :** le diagnostic réel a identifié `taa_PC 09*.pdf`, bloqué par la
validation du nom temporaire avant tout appel au moteur PDF.

### BUG-EXPORT-026 — Astérisque dans un numéro de feuille bloquant TEST-14

**Symptôme :** `PDF séparé — erreur : Nom PDF non valide : taa_PC 09*.pdf`,
aucun fichier créé pour le carnet DPC.
**Cause :** le numéro de feuille Revit `PC 09*` était injecté tel quel dans un
nom temporaire Windows, puis refusé avant export.
**Correction :** sécuriser le nom temporaire ; après l'export natif groupé,
rapprocher les PDF des feuilles par une clé conservatrice et unique qui ignore
la ponctuation. Ne livrer aucun PDF en cas d'ambiguïté ou de sortie inattendue.
**Règle préventive :** les noms Revit ne sont pas nécessairement des noms de
fichiers ; conserver la maquette et vérifier toute correspondance avant livraison.
**Anti-régression :** `tests/test_pdf_delivery.py` couvre le numéro étoilé,
l'ordre inversé, les collisions après nettoyage et les sorties inattendues.
Validation réelle du comportement de nommage Revit 2025.4 encore requise.

### BUG-EXPORT-027 — Liste Python refusée par l'export DWG

**Symptôme :** TEST-15/16 : `expected ICollection[ElementId], got list`.
**Cause :** les deux modes DWG passaient `list(view_ids)` à la surcharge Revit.
**Correction :** construction explicite de `List[ElementId]` avant l'appel natif.
**Règle préventive :** les doubles d'API doivent vérifier la collection typée,
pas seulement accepter toute liste Python ; respecter le contrat .NET de la surcharge.
**Anti-régression :** `tests/test_export_tests15_23.py`, modes séparé/combiné et
True Color activé/désactivé. Rejouer TEST-15 puis TEST-16 dans Revit.
Le retour TEST-16 démontre un blocage d'export, pas encore un défaut de couleur.

### BUG-EXPORT-028 — Aperçu du nom absent dans la fenêtre principale

**Symptôme :** TEST-22/23 : nom correct dans la fenêtre de publication, tiret dans
l'aperçu principal.
**Cause :** appel à `FilenameService.preview`, méthode inexistante, puis exception
masquée par un tiret.
**Correction :** appel au service canonique `resolve`, avec feuille sélectionnée
et dossier parent ; affichage des erreurs et variables non résolues.
**Règle préventive :** tester le raccordement de la vraie méthode UI au vrai
service ; ne pas masquer les erreurs comme une absence de sélection.
**Anti-régression :** `tests/test_export_tests15_23.py`, numéro/paramètre Revit/dossier
sur carnet et feuille sélectionnée ; rejouer TEST-22/23 dans Revit.

### BUG-EXPORT-029 — Filtrage expérimental retiré du périmètre V1

**Symptôme :** TEST-35 : collision au lieu du résultat attendu ; TEST-36 : une ligne
ajoutée sur une feuille n'est pas proposée comme modification.
**Cause :** le filtrage repose sur la comparaison du `VersionGuid` de la feuille ;
la couverture des modifications de contenu n'est pas démontrée. La cause exacte
Revit des retours 35/36 reste à analyser avant toute réintroduction.
**Décision V1 :** retrait de l'option demandé par l'utilisateur ; ce n'est pas une
correction de l'algorithme de détection. Le modèle force `modified_only=False`,
retire ce champ des réglages héritables/sérialisés et ignore les anciennes valeurs.
Le contrôle XAML et ses handlers sont supprimés ; le socle historique est conservé.
**Règle préventive :** retirer une option de l'interface exige de neutraliser aussi
les valeurs persistées, sinon un filtre invisible peut exclure des livrables.
**Anti-régression :** `tests/test_export_v1_scope.py` couvre profil/dossier/carnet
anciens, périmètre feuille/carnet/dossier et absence de références UI résiduelles.
TEST-V1-01 reste à exécuter dans Revit. Réétudier les tests 35/36 pour V2.

### BUG-EXPORT-030 — Publication récursive aplatie dans la destination

**Symptôme :** publier un dossier avec sous-dossiers et carnets ne créait pas
l'arborescence attendue sur disque.
**Cause :** les cibles ne transportaient pas leur chemin relatif et les moteurs
PDF/DWG utilisaient une destination unique quel que soit le mode.
**Correction :** copies de cibles portant le chemin depuis le dossier sélectionné,
service de chemins commun à l'aperçu et aux exports ; sous-dossier au nom du carnet
uniquement pour les formats séparés. Les destinations propres restent respectées.
**Règle préventive :** calculer les chemins dans un seul service sans effet disque,
ne pas muter les carnets persistants et contrôler les collisions entre carnets.
**Anti-régression :** `tests/test_publication_folder_paths.py`, quatre combinaisons
PDF/DWG, fichiers simulés comparés à l'aperçu, sélection partielle et noms Windows.
TEST-V1-02 reste à valider dans Revit 2025.4.

### BUG-EXPORT-031 — Héritage limité au dossier immédiat

**Symptôme :** un sous-dossier ne reprend pas la destination ni les modes du parent.
**Cause :** SettingsResolver ne recevait que le dossier immédiat ; l'UI affichait
les réglages bruts du sous-dossier plutôt que les valeurs effectives.
**Correction :** chaîne récursive des parents injectée depuis la fenêtre, résolution
par champ et affichage effectif ; sauvegarde limitée au champ changé conservée.
**Règle :** traverser tous les ancêtres sans écraser les surcharges ni confondre False/None.
**Test :** héritage sur trois niveaux, changement du parent, surcharge explicite,
retour à None, détection de cycle ; TEST-31 réel à rejouer.

### BUG-EXPORT-032 — Pas de dossier de carnet en publication directe séparée

**Symptôme :** fichiers séparés directement dans la destination.
**Cause identifiée :** la création du dossier du carnet dépendait du chemin relatif
préparé seulement lors d'une sélection de dossier. La sélection exacte du retour
utilisateur n'a pas pu être vérifiée, la capture étant inaccessible.
**Correction :** le mode séparé ajoute toujours le dossier du carnet, même pour une
publication directe carnet/feuille ; les dossiers parents restent liés au périmètre choisi.
**Règle :** vérifier tous les points d'entrée utilisateur, pas uniquement le moteur.
**Test :** chemins aperçu/export dans les 4 combinaisons PDF/DWG et 3 périmètres ;
TEST-V1-02 réel à rejouer. Le constat utilisateur reste KO jusqu'à cette validation.

### BUG-EXPORT-033 — Surcharge intermédiaire sans retour à l'héritage accessible

**Symptôme :** A405 indique « Hérité du dossier » mais reste différent de DCE ;
l'interface ne précise pas quel dossier fournit les valeurs.
**Cause confirmée dans le code :** bouton de retour désactivé pour tous les dossiers,
handler limité aux carnets et origine affichée sans nom d'ancêtre. Une surcharge
intermédiaire reste donc prioritaire sans moyen UI de l'enlever.
**Correction :** retour explicite à l'héritage du parent pour le sous-dossier sélectionné,
sauvegarde et affichage du nom du dossier effectif pour chaque groupe de champs.
**Règle :** chaque niveau permettant des surcharges doit permettre leur retrait ;
ne jamais effacer automatiquement les réglages existants pour simuler un héritage.
**Test :** vraie méthode UI exécutée hors WPF, scénario DCE/Plan/A405, sauvegarde et
relecture du dossier, conservation des descendants ; validation Revit restante.

## 4. Bugs rencontrés sur Calculs des pièces

### BUG-CALCULS-001 — Collision du module générique `models`

**Symptôme :** la suite de tests `tests/calculation` échouait selon l'ordre de chargement avec `ImportError: cannot import name 'RoomCalculationItem' from 'models'`.  
**Cause :** `lib/calculation/room_calculator.py` et son test importaient `models` comme module top-level alors que `Calculs.panel/models` utilise également ce nom. Le premier module chargé dans `sys.modules` pouvait donc masquer l'autre.  
**Correction :** le moteur métier utilise désormais l'import explicite `calculation.models` depuis la racine `lib`, et le test suit le même contrat.  
**Règle :** dans Outils TAA, ne pas importer comme modules top-level des noms génériques présents dans plusieurs chemins Python (`models`, `services`, `settings`, etc.). Préférer un package explicitement qualifié ou un nom de module spécifique.  
**Anti-régression :** exécuter toute la suite `tests/calculation` dans un même processus afin de détecter les collisions dépendantes de l'ordre d'import.

### BUG-CALCULS-002 — Filtre `writable_only` appliqué avant agrégation

**Symptôme :** un paramètre pouvait rester proposé comme destination écrivable si sa première occurrence était modifiable mais qu'une occurrence suivante du même paramètre était en lecture seule.  
**Cause :** `get_parameter_descriptors(..., writable_only=True)` excluait les occurrences readonly avant de fusionner l'état des différentes pièces. L'information readonly n'atteignait donc jamais le descripteur agrégé.  
**Correction :** toutes les occurrences d'une même identité sont d'abord agrégées ; l'état `writable` est calculé avec un ET logique, puis le filtre `writable_only` est appliqué sur le résultat agrégé.  
**Règle :** lorsqu'une propriété de sécurité dépend de plusieurs éléments, ne pas filtrer les occurrences avant d'avoir calculé l'état agrégé complet.  
**Anti-régression :** deux pièces portant le même paramètre partagé, l'une modifiable et l'autre readonly, ne doivent pas faire apparaître ce paramètre dans une liste `writable_only`.

### BUG-CALCULS-003 — Séquences \\n transformées en retours ligne dans le code Python généré

**Symptôme :** certains fichiers Python WPF / workflow contenaient des chaînes littérales coupées sur plusieurs lignes, par exemple la confirmation utilisateur et la jointure avec `"\\n".join(...)`, ce qui rendait le module invalide au parsing Python.  
**Cause :** lors de la génération des fichiers, des séquences d'échappement destinées au code Python ont été interprétées une première fois par la couche de génération JavaScript au lieu d'être conservées comme `\\n` dans le fichier final.  
**Correction :** réécriture des fichiers concernés en conservant littéralement les séquences d'échappement et ajout d'un test statique `ast.parse` sur les fichiers UI et le workflow.  
**Règle :** lorsqu'un fichier source est généré par une autre couche de langage, préserver explicitement les antislashs ; ne jamais supposer qu'une chaîne générée est syntaxiquement valide.  
**Anti-régression :** parser avec `ast.parse` tous les nouveaux fichiers Python générés avant validation, en particulier ceux contenant des chaînes multi-lignes ou des séquences `\\n`.

### BUG-CALCULS-004 — Le dossier de tests masquait le package métier `calculation`

**Symptôme :** la CI pytest échouait pendant la collecte avec `ModuleNotFoundError: No module named 'calculation.models'` et des erreurs similaires sur `parameter_descriptor` et `unit_option`.  
**Cause :** `tests/calculation/__init__.py` transformait le dossier de tests en package Python nommé `calculation`. Ce package de tests était chargé avant `OutilsTAA.extension/lib/calculation` et masquait donc le vrai package métier.  
**Correction :** suppression de `tests/calculation/__init__.py`. Pytest collecte toujours le dossier de tests sans en faire un package concurrent.  
**Règle :** un dossier de tests ne doit pas porter le même nom de package importable qu'un package métier lorsque sa présence dans `sys.path` peut créer un masquage.  
**Anti-régression :** exécuter `python -m pytest tests/calculation -q` dans un environnement vierge et vérifier que les imports `calculation.*` résolvent le package sous `OutilsTAA.extension/lib`.

### BUG-CALCULS-005 — Paramètre de pièce bloqué par l'alignement des groupes

**Symptôme :** Calculs des pièces ne pouvait pas écrire dans un paramètre de pièce lorsque la pièce appartenait à un groupe et que le paramètre était configuré pour conserver la même valeur sur les occurrences du type de groupe. Le paramètre pouvait être absent de la liste des destinations ou refuser l'écriture.
**Cause :** le workflow traitait tout paramètre `IsReadOnly` comme définitivement non écrivable et ne prenait pas en compte `InternalDefinition.VariesAcrossGroups` / `SetAllowVaryBetweenGroups`.
**Correction :** ajout d'un service Revit dédié qui détecte les paramètres non intégrés déverrouillables, autorise temporairement les valeurs variables entre groupes dans la transaction d'écriture, puis restaure l'alignement avant commit. Si Revit doit réaligner des éléments lors de la restauration, la transaction est annulée.
**Règle :** lorsqu'un état Revit temporaire est nécessaire pour écrire, l'activer et le restaurer dans la même transaction ; toute restauration entraînant une modification secondaire inattendue doit provoquer un rollback.
**Anti-régression :** tests dédiés sur la découverte d'une destination readonly mais déverrouillable, le cycle `True → écriture → False`, l'exclusion des paramètres intégrés et le rollback lorsque la restauration réaligne des éléments.

### BUG-CALCULS-006 — Divergence de groupes entraînant un rollback sans choix utilisateur

**Symptôme :** lorsqu'un paramètre de pièce aligné par type de groupe devait recevoir des résultats différents entre plusieurs occurrences, Calculs des pièces annulait systématiquement toute la transaction avec le message indiquant que Revit aurait réaligné des éléments.
**Cause :** le correctif BUG-CALCULS-005 sécurisait la restauration de l'alignement mais ne proposait qu'une seule politique : restaurer l'état initial ou annuler. Il ne distinguait pas les deux intentions métier possibles : conserver les résultats exacts ou conserver l'alignement du paramètre.
**Correction :** analyse préalable des membres correspondants entre occurrences d'un même type de groupe, détection des valeurs projetées divergentes et choix explicite de l'utilisateur. L'utilisateur peut laisser le paramètre varier, conserver l'alignement en choisissant lui-même la valeur à appliquer, ou annuler. La valeur la plus fréquente est uniquement présélectionnée et n'est jamais imposée.
**Règle :** lorsqu'une normalisation nécessaire à une contrainte Revit peut remplacer des résultats métier valides, ne jamais choisir automatiquement la valeur à conserver. Présenter les valeurs et leurs fréquences, puis demander une décision explicite à l'utilisateur.
**Anti-régression :** tests dédiés sur la détection d'une majorité, la conservation des valeurs exactes avec paramètre variable, le choix volontaire d'une valeur minoritaire avec alignement conservé, l'absence de transaction sans décision et les contrats de l'interface WPF.

### BUG-EXPORT-034 — Champs de réglages comprimés par des largeurs fixes

**Symptôme :** les rangées de profil et de nommage peuvent dépasser la colonne de
réglages lors d'une réduction de fenêtre ; le bloc héritage laisse trop peu de place au texte.
**Cause :** somme des largeurs fixes dans des StackPanel horizontaux sans retour à la ligne.
**Correction :** rangées souples DockPanel/Grid, variables sur une seconde ligne,
profils/configuration en WrapPanel et action d'héritage sous la description.
**Règle préventive :** tester les largeurs minimales et les DPI réels ; ne pas assimiler
la validité XML à une validation WPF. Préserver les noms, événements et bindings.
**Contrôle :** contrats XAML conservés ; tests UI-01 à UI-06 à exécuter dans Revit.

### BUG-EXPORT-035 — Suppression ignorant la sélection Ctrl/Maj

**Symptôme :** plusieurs lignes sélectionnées mais une seule supprimée.
**Cause :** handler limité à TreeView.SelectedItem, distinct de la sélection du
 gestionnaire de glisser-déposer.
**Correction :** instantané des tags sélectionnés, confirmation nominative commune,
 enfants sélectionnés avant parents, protection Général et dossiers non vides,
 prise en compte des carnets de session. Navigation clavier efface la sélection
 multiple périmée ; un clic sur un élément non sélectionnable l'efface aussi.
**Règle préventive :** les actions groupées doivent utiliser la même sélection que
 l'affichage et ne jamais supprimer implicitement des enfants non sélectionnés.
**Tests :** `test_export_ui_completion.py` couvre suppression, annulation,
 sélection, sessions et protections ; UI-08 reste à valider dans Revit.

### BUG-EXPORT-036 — Formats et périmètre absents de la présentation principale

**Symptôme :** icônes génériques de feuilles et pied de fenêtre statique.
**Cause :** absence de raccordement des en-têtes et du résumé aux réglages résolus.
**Correction :** calcul à partir des mêmes cibles et du même SettingsResolver que
 la publication ; actualisation après sélection, modification, profil et héritage.
**Règle préventive :** afficher les valeurs effectives sans les enregistrer comme
 surcharges ; distinguer résumé prévu et validation par l'aperçu.
**Tests :** `test_export_ui_completion.py` couvre formats mixtes, ancêtres,
 feuille seule et actualisation des vraies méthodes ; UI-09/UI-11 à valider dans Revit.

### BUG-EXPORT-037 — Destination saisie au clavier non enregistrée

**Symptôme reproductible dans le XAML :** le chemin tapé dans la destination ne
 déclenche aucun enregistrement, contrairement au bouton Parcourir.
**Cause :** OutputDirectoryTextBox n'avait ni TextChanged ni LostFocus raccordé.
**Correction :** LostFocus appelle le handler canonique SettingsChanged, qui
 sauvegarde uniquement output_directory au niveau actif.
**Règle préventive :** tester aussi la saisie directe d'un champ possédant un
 sélecteur externe ; ne pas transformer tous les champs hérités en surcharges.
**Test :** test_manual_destination_saves_only_destination_at_active_level vérifie
 le raccordement XAML et les deux niveaux ; saisie réelle à contrôler dans Revit.

### BUG-EXPORT-038 — Libellé « Export » affiché deux fois dans le ruban

**Symptôme :** « Export » apparaît sous l’icône du bouton puis une seconde fois comme nom du panneau.  
**Cause racine :** le bouton standard porte un titre `Export` nécessaire à la création du `PushButtonData`, tandis que `Export.panel` affiche indépendamment le même nom comme titre de panneau.  
**Correction finale :** conserver le titre API non vide `Export` et le tooltip, puis utiliser le mécanisme pyRevit `.smartbutton` / `__selfinit__` pour masquer uniquement le rendu du texte via `Autodesk.Windows.RibbonButton.ShowText = False`. Le basename de commande reste `Export`, le panneau reste `Export.panel` et le script métier exécuté au clic reste inchangé.  
**Règle préventive :** distinguer identité de commande, texte API obligatoire, visibilité du texte, tooltip et titre du panneau. Pour une commande icon-only, ne jamais rendre `PushButtonData.Text` vide ; masquer l'affichage après création du contrôle.  
**Anti-régression :** `tests/test_export_ribbon_contract.py` vérifie le bundle smartbutton, le titre API `Export`, le hook `__selfinit__`, `ShowText = False`, le tooltip, les tailles PNG et l'absence de texte dans le SVG. Validation finale obligatoire dans Revit 2025.4.

### BUG-EXPORT-039 — Titre blanc du PushButton rejeté au rechargement pyRevit

**Symptôme :** rechargement pyRevit en erreur critique : `The value cannot be empty. Parameter name: text` lors de la création du bouton Export.  
**Cause racine :** la tentative `title: " "` est normalisée comme texte vide avant ou pendant la création du `PushButtonData`; l'API Revit refuse un texte vide.  
**Correction :** restaurer un titre réel `Export` pour la création API et agir uniquement sur la propriété visuelle `ShowText` du contrôle de ruban après sa création.  
**Règle préventive :** ne jamais utiliser chaîne vide, espace seul ou caractère invisible comme substitut au titre obligatoire d'un `PushButtonData`.  
**Anti-régression :** test statique exigeant `title: Export` et `ShowText = False`, puis rechargement réel pyRevit sans erreur dans Revit 2025.4.

### BUG-EXPORT-040 — Publication limitée au premier élément d'une sélection multiple

**Symptôme :** plusieurs feuilles/carnets surlignés avec Ctrl/Maj, mais seul l'élément natif actif apparaît dans le périmètre et est exporté.

**Cause racine :** la sélection du gestionnaire de glisser-déposer et `TreeView.SelectedItem` sont distinctes ; résumé, aperçu et publication utilisaient `_selected_set/_selected_item`. Ctrl/Maj interceptait en outre l'événement natif sans actualiser ces actions.

**Correction :** constructeur de périmètre unique à partir de `selected_tags()`, regroupement des feuilles par carnet, copies non persistées et priorité du parent complet sur ses descendants. Notification explicite Ctrl/Maj, distinction sélection vide/native et suppression du wrapper dossier susceptible de remplacer le bouton multiple.

**Règle préventive :** toutes les actions groupées et leur résumé doivent consommer le même état de sélection ; ne jamais confondre élément actif des réglages et périmètre d'action. Un repli clavier ne doit pas réactiver un élément explicitement désélectionné.

**Anti-régression :** `tests/test_export_multiselection.py` exécute les handlers et les hooks Stage 07 ; sous-ensembles, ordre, carnets multiples, paramètres/destinations indépendants, collisions, annulation, Ctrl/Maj et sélection vide. Les anciens tests pointant encore sur `Export.pushbutton/script.py` sont réalignés sur le smartbutton actuel. Fonctionnement de la sélection multiple confirmé par l’utilisateur dans Revit le 2026-10-05 après essai de la branche de la PR #11. Ce retour ne constitue pas une validation détaillée de chaque scénario MS-01 à MS-10.

### BUG-PDV-001 — Crop logement incliné dans une vue orientée

**Symptôme :** le prototype crée correctement une vue dépendante et englobe le logement, mais le rectangle de crop peut apparaître légèrement incliné par rapport à l'écran de la vue.

**Cause racine :** l'emprise était calculée dans les axes globaux X/Y du modèle. Une vue Revit possède son propre repère d'affichage ; ses axes écran sont exposés par `View.RightDirection` et `View.UpDirection`.

**Correction :** projeter les points de contour des pièces dans le repère de la vue, calculer et agrandir l'emprise en coordonnées `u/v`, puis reconstruire les coins XYZ avant `SetCropShape`.

**Règle préventive :** toute géométrie destinée à être alignée visuellement dans une vue doit être calculée dans le repère de cette vue, et non supposée alignée sur les axes globaux du modèle.

**Anti-régression :** test pur d'un `ViewFrame` tourné à 45°, contrôle statique de l'utilisation de `RightDirection` / `UpDirection`, puis validation réelle dans Revit 2025.4 sur une vue orientée.

### BUG-PDV-002 — Contour optimisé rejeté par le crop Revit

**Symptôme :** les trois cas de test du contour logement optimisé basculent en `Rectangle de secours`.

**Cause structurelle identifiée :** le moteur transmettait au `ViewCropRegionShapeManager` une boucle issue directement de l'union géométrique et de `CurveLoop.CreateViaOffset`. Ces boucles peuvent contenir des arcs, courbes tessellées ou autres courbes non linéaires. Or un crop non rectangulaire Revit n'accepte qu'une seule boucle fermée sans auto-intersection composée de **segments droits non nuls** dans un plan parallèle à la vue.

**Correction :** linéariser la boucle extérieure par tessellation puis reconstruction en `Line.CreateBound`, supprimer les doublons / sommets quasi colinéaires, appliquer la marge sur cette boucle droite, puis linéariser une seconde fois avant `IsCropRegionShapeValid`. Ajouter un diagnostic par étape afin qu'un éventuel échec restant indique précisément s'il provient de l'union, de l'extraction, de l'offset ou de la validation Revit.

**Règle préventive :** ne jamais envoyer directement une géométrie de pièce, de face ou un résultat d'offset à `SetCropShape`. Le contrat final doit être normalisé explicitement en boucle de segments droits et contrôlé par `IsCropRegionShapeValid`.

**Anti-régression :** tests statiques imposant la linéarisation avant et après l'offset, l'utilisation de `Line.CreateBound` et le diagnostic d'étape ; revalidation dans Revit 2025.4 sur les trois logements déjà testés.

### BUG-PDV-003 — Capacité non rectangulaire testée sur la mauvaise vue

**Symptôme :** après le correctif de linéarisation, le prototype affiche directement « Cette vue Revit n'autorise pas un crop non rectangulaire » avant même la création de la vue dépendante.

**Cause racine :** `CanHaveShape` était contrôlé pendant le calcul géométrique sur la **vue source**. Cette vue peut être pilotée par un Scope Box ou une autre contrainte de cadrage, alors que la forme finale doit être appliquée à la **nouvelle vue dépendante**. Le test de capacité était donc fait sur le mauvais objet.

**Correction :** séparer la validation géométrique de la capacité de la vue. Le moteur calcule le contour sans exiger `CanHaveShape` sur la source. Après création de la vue dépendante, `apply_to_view` vérifie `CanHaveShape` sur la cible. Si un Scope Box est affecté et que son paramètre est modifiable, il est retiré uniquement sur la nouvelle vue puis la capacité est réévaluée. Si la cible reste incompatible, le rectangle de secours est utilisé avec un avertissement explicite.

**Règle préventive :** toute capacité API liée à l'élément qui recevra une modification doit être évaluée sur l'élément cible final, jamais sur un objet utilisé seulement comme référence de calcul.

**Anti-régression :** test statique garantissant l'absence de `CanHaveShape` dans `build_optimized_crop`, sa présence dans `apply_to_view`, la gestion de `VIEWER_VOLUME_OF_INTEREST_CROP` et la disponibilité d'un fallback rectangulaire.

### BUG-PDV-004 — `CreateViaOffset` échoue au-delà d'une petite marge

**Symptôme :** sur les logements testés, le contour optimisé fonctionne avec une marge de **20 mm**, mais bascule en rectangle de secours à partir d'environ **25 mm**. Le diagnostic indique : `Application de la marge : Revit n'a pas réussi à décaler le contour du logement avec la marge demandée.`

**Cause :** `CurveLoop.CreateViaOffset` doit décaler chaque arête puis retailler les courbes adjacentes pour reconstruire une boucle continue. Sur un contour concave comportant de petits décrochements, une augmentation de la marge peut provoquer des intersections / inversions locales que Revit ne sait pas résoudre. L'échec dépend donc de la géométrie et peut apparaître brutalement à quelques millimètres près. L'API documente qu'un `InvalidOperationException` est levé lorsque la boucle ne peut pas être offsetée.

**Correction :** ne plus utiliser `CurveLoop.CreateViaOffset` pour la marge du plan de vente. Construire une dilatation géométrique robuste par union booléenne : surface du logement + bandes rectangulaires de largeur `2 × marge` autour des arêtes + raccords octogonaux autour des sommets. L'octogone est circonscrit au rayon demandé afin de garantir au moins la marge souhaitée. La boucle extérieure de l'union devient ensuite le crop.

**Règle préventive :** une fonction d'offset topologique Revit ne doit pas être le mécanisme unique pour une marge importante sur un polygone concave métier. Préférer un buffer géométrique robuste dont les changements de topologie sont absorbés par une union booléenne.

**Anti-régression :** vérifier que le service n'utilise plus `CreateViaOffset`, qu'il construit bandes + raccords, puis tester dans Revit 2025.4 des marges 20, 25, 100 et 500 mm sur logements rectangulaire, en L et irrégulier.

### BUG-PDV-005 — Artefacts de marge et décrochements dus aux gaines sans pièce

**Symptôme :** le contour optimisé fonctionne à 20, 50, 200 et 500 mm, mais des facettes / renflements apparaissent dans les angles aux grandes marges. Le contour suit également certains petits retraits liés à des gaines techniques dépourvues de pièce, ce qui donne une enveloppe graphiquement trop détaillée pour un plan de vente.

**Cause :** les raccords octogonaux utilisés pour simuler la dilatation deviennent visuellement perceptibles quand la marge augmente. Par ailleurs, l'union exacte des pièces considère comme significatif tout décrochement de l'enveloppe, même lorsqu'il provient d'un vide technique non destiné à structurer le cadrage graphique.

**Correction :** remplacer les raccords octogonaux par des carrés alignés sur le repère de la vue afin d'obtenir des angles francs. Ajouter ensuite une passe de nettoyage des petits détours rectangulaires en U. La tolérance graphique est bornée entre 300 et 600 mm et varie avec la marge afin de gommer les petites gaines / retraits sans aplatir les grandes formes en L.

**Règle préventive :** distinguer le contour géométrique exact d'un logement de son enveloppe graphique de cadrage. Pour un plan de vente, la seconde doit pouvoir simplifier de petits accidents qui n'apportent aucune information de composition.

**Anti-régression :** tests statiques sur raccords carrés, suppression des petits U et bornes de nettoyage ; validation Revit 2025.4 sur le même logement aux marges 20, 50, 200 et 500 mm.

### BUG-PDV-006 — Le crop entre dans les gaines sans pièce

**Symptôme :** après amélioration des raccords de marge, les angles deviennent propres mais le contour continue à rentrer dans certaines gaines techniques dépourvues de pièce.

**Cause :** le moteur se basait sur l'union exacte des pièces. Une gaine sans Room apparaît donc comme une poche concave du polygone logement. Le nettoyage précédent ne reconnaissait que des motifs simples en U de quatre points et ne couvrait pas les gaines dont le contour comporte davantage de sommets.

**Correction :** fermer les petites poches concaves **avant** la construction de la marge. Le moteur détecte les sommets concaves, teste des ponts directs entre paires de sommets, rejette les ponts qui croisent le contour, puis n'accepte le remplissage que si la bouche, la profondeur et l'aire ajoutée restent sous des seuils conservateurs. Les grandes formes en L doivent donc rester intactes.

Seuils du prototype :
- bouche maximale : 1 500 mm ;
- profondeur maximale : 1 500 mm ;
- aire ajoutée maximale : 2,0 m².

**Règle préventive :** le contour de crop doit être une enveloppe graphique métier, pas l'union brute des Rooms. Les petits vides techniques sans pièce doivent pouvoir être comblés de façon contrôlée avant marge.

**Anti-régression :** test statique garantissant que la fermeture des gaines précède le buffer, plus validation Revit sur le logement A003 utilisé pendant les prototypes.

### BUG-PDV-007 — Les petites marges révèlent encore les gaines

**Symptôme :** après les premiers correctifs, les gaines sont moins visibles à grande marge mais restent encore suivies par le crop lorsqu'on utilise une petite marge.

**Cause :** la détection des poches reposait sur des paires de sommets classés concaves. Selon le sens de la boucle et la géométrie exacte d'une gaine, les deux points qui forment sa bouche ne sont pas nécessairement tous les deux identifiés comme concaves. La grande marge masquait partiellement le défaut, ce qui donnait l'impression que le nettoyage dépendait de la marge.

**Correction :** détecter les poches indépendamment de la marge. Le moteur teste désormais toutes les paires de sommets non adjacents sous des seuils conservateurs. Un pont n'est accepté que s'il ne coupe aucune arête, passe par une zone extérieure au polygone, augmente légèrement l'aire et remplit une poche limitée en bouche, profondeur et surface.

Seuils du prototype :
- bouche maximale : 2 000 mm ;
- profondeur maximale : 2 000 mm ;
- aire remplie maximale : 3,0 m².

**Règle préventive :** la simplification de l'enveloppe métier doit être calculée avant la marge de présentation. Une gaine jugée négligeable doit disparaître de la même manière à 20 mm et à 500 mm.

**Anti-régression :** test statique de l'analyse de toutes les paires de sommets, du test point-dans-polygone et de l'ordre fermeture des gaines → marge robuste ; validation Revit sur A003 aux marges 20/50/200/500 mm.

### BUG-PDV-008 — Nettoyage trop agressif des gaines provoque un fallback systématique

**Symptôme :** après généralisation de la détection des petites poches, les quatre marges testées basculent en `Rectangle de secours`.

**Cause :** le nettoyeur testait toutes les paires de sommets non adjacents. Il pouvait produire un polygone auto-intersectant ou topologiquement incorrect avant même la construction de la marge.

**Correction :** revenir à une stratégie conservatrice : ne traiter que des poches locales limitées entre deux sommets concaves proches, limiter le nombre de sommets de la chaîne remplacée, vérifier le point de pont, contrôler les intersections et valider la simplicité du polygone avant de l'accepter. Si le nettoyage reste douteux, conserver le contour d'origine plutôt que faire échouer tout le crop optimisé.

**Règle préventive :** une simplification graphique ne doit jamais être plus fragile que la géométrie de base. Tout nettoyage doit être optionnel et réversible vers le contour original.

**Anti-régression :** vérifier qu'un échec du nettoyage ne peut pas provoquer à lui seul un fallback rectangle, et rejouer A003 aux marges 20/50/200/500 mm.

### BUG-PDV-009 — Helper de surface polygonale appelé comme méthode d'instance

**Symptôme :** tous les essais passent immédiatement en `Rectangle de secours` avec l'erreur `_polygon_signed_area() takes exactly 1 argument (2 given)` à l'étape « Fermeture des petites gaines et retraits ».

**Cause :** `_polygon_signed_area(points)` avait été définie sans `@staticmethod` mais appelée via `self._polygon_signed_area(...)`. IronPython injectait donc implicitement `self` en premier argument.

**Correction :** déclarer explicitement `_polygon_signed_area` en `@staticmethod`.

**Règle préventive :** tout helper pur placé dans une classe de service doit être explicitement décoré en `@staticmethod` lorsqu'il ne consomme ni `self` ni `cls`.

**Anti-régression :** test statique imposant le décorateur `@staticmethod` sur `_polygon_signed_area`.

### BUG-PDV-010 — Helpers de nettoyage supprimés pendant un refactor

**Symptôme :** tous les essais passent en `Rectangle de secours` avec l'erreur `'CropGeometryService' object has no attribute '_vertices_are_adjacent'`.

**Cause :** lors du remplacement de l'algorithme de fermeture des gaines, les helpers `_vertices_are_adjacent` et `_point_in_polygon` ont été supprimés du fichier alors que la nouvelle méthode continuait à les appeler.

**Correction :** restaurer les deux helpers et ajouter un test de contrat vérifiant explicitement leur présence.

**Règle préventive :** après tout remplacement de bloc important dans un service Python, vérifier les appels `self._...` contre la liste des méthodes réellement définies avant commit.

**Anti-régression :** test statique sur les deux helpers et contrôle automatique des méthodes privées appelées lors des prochains refactors.

### BUG-PDV-011 — Les lèvres d'une gaine ne sont pas toujours des sommets concaves

**Symptôme :** après sécurisation du moteur, le contour optimisé fonctionne mais continue à suivre certaines gaines techniques, notamment avec une petite marge.

**Cause :** le nettoyeur conservateur supposait qu'une poche de gaine était bornée par deux sommets concaves. Ce n'est pas garanti : selon le sens du contour et la forme exacte de la gaine, l'un ou les deux sommets de la bouche peuvent être convexes ou neutres.

**Correction :** tester toutes les paires de sommets non adjacents, mais avec des garde-fous stricts : pont court, aucune intersection avec le contour, milieu du pont situé à l'extérieur du polygone, polygone candidat simple, aire ajoutée positive et limitée, profondeur limitée. Le nettoyage reste réversible vers le contour d'origine en cas de doute.

**Règle préventive :** ne pas déduire la sémantique « gaine / poche extérieure » uniquement de la concavité locale d'un sommet. Utiliser la topologie globale du polygone et la variation d'aire.

**Anti-régression :** test statique du parcours de toutes les paires de sommets et test générique vérifiant que chaque appel `self._...` correspond à une méthode réellement définie.

### BUG-PDV-012 — Buffer 3D instable après nettoyage du contour

**Symptôme :** le crop optimisé retombe en rectangle de secours à l'étape `Construction de la marge robuste`, avec une erreur `BooleanOperationsUtils` signalant des imprécisions géométriques entre solides.

**Cause :** après fermeture de certaines poches techniques, le contour est plus simple mais la construction de marge par bandes + caps extrudés peut créer des solides avec faces ou arêtes presque coïncidentes. Les booléens 3D Revit deviennent alors instables.

**Correction :** essayer en priorité `CurveLoop.CreateViaOffset` sur le contour **déjà nettoyé**, puis ne conserver le buffer 3D par booléens qu'en secours. L'offset natif avait échoué auparavant sur le contour brut à cause des micro-concavités ; après nettoyage, il peut à nouveau être viable et produit des angles propres sans opérations booléennes.

**Règle préventive :** préférer l'opération géométrique la plus simple une fois le contour métier stabilisé. Les booléens 3D ne doivent pas être utilisés par défaut lorsqu'une opération 2D native peut suffire.

**Anti-régression :** test statique garantissant que l'offset natif est essayé avant le buffer booléen.

### BUG-PDV-013 — Le fallback booléen 3D reste instable

**Symptôme :** malgré la priorité donnée à `CreateViaOffset`, le moteur retombe encore sur `BooleanOperationsUtils` pour la marge et échoue avec le message Revit `Failed to perform a Boolean operation for the two solids`.

**Cause :** le simple fait de conserver le buffer 3D comme second choix réintroduit une branche connue comme instable sur des solides quasi coplanaires. Le moteur de marge pouvait donc encore échouer exactement de la même manière qu'avant.

**Correction :** supprimer complètement les booléens 3D de l'étape de marge. La marge est désormais 100 % 2D : essai d'offset natif sur le contour nettoyé, puis simplification adaptative de petites concavités et nouvel essai d'offset. Si aucun contour 2D valide n'est obtenu, le niveau supérieur utilise directement le rectangle de secours.

**Règle préventive :** une stratégie déjà identifiée comme instable ne doit pas rester cachée comme fallback par défaut. Les fallbacks doivent être plus simples et plus sûrs que le chemin principal.

**Anti-régression :** test de contrat vérifiant l'absence de `BooleanOperationsUtils` dans `_buffer_outward` et l'ordre offset natif → simplification adaptative.

### BUG-PDV-014 — Fermeture de gaine par pont diagonal

**Symptôme :** le moteur détecte et comble certaines gaines, mais la fermeture
relie directement deux lèvres dont les positions ne sont pas parfaitement en
vis-à-vis. Le crop crée alors un segment biaisé sans rapport avec une arête de
mur réelle.

**Cause :** la fermeture des poches utilisait la distance minimale entre deux
sommets comme critère principal. Un pont direct pouvait donc être valide
topologiquement tout en introduisant une nouvelle direction diagonale dans le
dessin.

**Correction :** relever les murs droits qui bornent les Rooms, calculer leur
face opposée à la pièce à partir de `Wall.Orientation` et `Wall.Width`, puis
utiliser ces faces comme guides de fermeture. Les lèvres sont projetées
perpendiculairement sur le guide et reliées le long du chant du mur. Un pont
direct n'est autorisé en secours que s'il est déjà parallèle à une direction
locale du contour.

**Règle préventive :** une simplification de crop destinée à un plan
architectural ne doit pas créer une direction graphique nouvelle uniquement
parce qu'elle est topologiquement plus courte. Lorsqu'une fermeture correspond
à un vide bordé par des murs, la géométrie construite doit privilégier les
directions et faces de ces murs.

**Anti-régression :** test de contrat sur la collecte des faces opposées, le
pont guidé par mur et le refus des ponts directs créant une direction oblique ;
validation Revit sur le logement de référence aux marges 20 / 50 / 200 / 500 mm.

### BUG-PDV-015 — Le filtre d'angle rejette le mur qui devait supprimer le biais

**Symptôme :** après l'introduction des fermetures guidées par mur, le logement
de référence bascule en `Rectangle de secours` à l'étape
`Construction de la marge robuste`.

**Cause :** le premier filtre exigeait que la corde entre les deux lèvres de la
poche soit presque parallèle au mur guide. Or, lorsque les lèvres sont
décalées, cette corde est précisément diagonale. Le bon mur était donc rejeté,
la poche restait non simplifiée et `CurveLoop.CreateViaOffset` pouvait encore
échouer sur la concavité.

**Correction :** supprimer la comparaison d'angle entre la corde des lèvres et
le mur. Les lèvres sont projetées indépendamment sur une même face opposée de
mur. La validité repose ensuite sur la proximité au guide, la position
extérieure du segment, l'aire ajoutée, la profondeur et la simplicité du
polygone.

**Règle préventive :** un filtre géométrique ne doit pas tester comme condition
d'entrée la propriété que l'algorithme a justement pour objectif de corriger.
Pour une fermeture guidée, valider le guide et les projections plutôt que la
corde brute entre les points.

**Anti-régression :** test de contrat garantissant l'absence de filtre
`mouth_vector / parallel_sin` dans `_wall_aligned_bridge_paths`, présence
des projections sur le mur et validation Revit sur A003.

### BUG-TEST-003 — Workflow Plans de vente sans PYTHONPATH

**Symptôme :** le premier run GitHub Actions du module Plans de vente échoue
pendant la collecte avec `ModuleNotFoundError: No module named 'plans_vente'`
sur les tests purs `crop_bounds`, `housing_grouper` et `view_frame`.

**Cause :** les modules métier du plugin résident dans
`OutilsTAA.extension/lib`, mais le nouveau workflow lançait pytest sans ajouter
ce répertoire au chemin d'import Python.

**Correction :** définir `PYTHONPATH=${{ github.workspace }}/OutilsTAA.extension/lib`
sur l'étape pytest du workflow Plans de vente.

**Règle préventive :** tout workflow pytest d'un module pyRevit dont les tests
importent les bibliothèques de `OutilsTAA.extension/lib` doit reproduire
explicitement ce chemin d'import.

**Anti-régression :** exécution réelle du workflow
`Plans de vente — tests hors Revit` après le correctif.

### BUG-TEST-004 — Contrats Plans de vente désynchronisés du moteur de marge

**Symptôme :** après correction du `PYTHONPATH`, la suite Plans de vente exécute
34 tests mais deux contrats échouent alors que le code concerné n'a pas
réintroduit de booléen dans la marge.

**Cause :** un test cherchait encore l'ancien libellé
`Application de la marge` alors que l'étape s'appelle désormais
`Construction de la marge robuste`. Un autre interdisait la simple chaîne
`BooleanOperationsUtils` dans le bloc, y compris lorsqu'elle apparaissait
uniquement dans un commentaire de documentation décrivant l'erreur évitée.

**Correction :** aligner le test sur le nom d'étape actuel et vérifier l'absence
d'appels réels `BooleanOperationsUtils.` / `ExecuteBooleanOperation`, pas
l'absence du mot dans les commentaires.

**Règle préventive :** les tests de contrat textuels doivent cibler un contrat
exécutable ou un identifiant stable, et ne pas confondre une mention
documentaire avec un appel de code.

**Anti-régression :** exécution complète de `python -m pytest tests/plans_vente -q`
dans GitHub Actions.

### BUG-PDV-016 — Détection automatique trop large : 50 fermetures et calcul lent

**Symptôme :** sur A003, la fenêtre de diagnostic indique
`50 poche(s), dont 50 alignée(s) sur mur` avant un échec de marge. Le calcul
est sensiblement long.

**Cause :** la fermeture automatique parcourt les paires de sommets du contour
et les compare aux guides de murs. Sur un logement complexe, beaucoup de
couples peuvent satisfaire les garde-fous successifs. La boucle de sécurité
atteint alors sa limite de 50 modifications, avec un coût combinatoire élevé,
sans garantir une enveloppe architecturale plus pertinente.

**Correction :** permettre à l'utilisateur de choisir explicitement le type de
mur périphérique. Pour ce chemin, les segments de ce type qui bordent les
Rooms sont convertis en bandes 2D de largeur égale à l'épaisseur du mur puis
unis aux Rooms avant extraction du contour. La recherche combinatoire des
poches est entièrement ignorée lorsque ce type explicite est fourni.

**Règle préventive :** lorsqu'une information métier fiable est disponible
(type de mur périphérique), la privilégier à une inférence géométrique globale
coûteuse. Une optimisation ne doit pas parcourir tout le graphe des sommets si
un sous-ensemble architectural explicite permet de construire directement
l'enveloppe.

**Anti-régression :** tests de contrat sur le sélecteur WPF, la transmission du
`UniqueId` du type, l'union des bandes de murs aux Rooms et le contournement
de `_close_small_recesses` dans le chemin explicite ; validation Revit A003
sur le temps de calcul et le contour obtenu.

### BUG-PDV-017 — Le mur périphérique choisi n'est pas la limite directe de Room

**Symptôme :** le type de mur périphérique est bien sélectionné mais le
diagnostic retourne `Murs périphériques utilisés : 0` et
`Aucun mur droit du type périphérique sélectionné ne borde les pièces`.

**Cause :** la première implémentation ne considérait que
`BoundarySegment.ElementId`. Elle supposait donc que le mur périphérique
sélectionné était directement room-bounding. Cette hypothèse est fausse dès
qu'un doublage, une contre-cloison ou une autre limite de pièce se trouve entre
la Room et le mur extérieur.

**Correction :** calculer d'abord le contour extérieur des Rooms puis rechercher
toutes les instances du type choisi à proximité de ce contour. Les candidats
doivent être proches et sensiblement parallèles à une arête extérieure. Seule
la portion en vis-à-vis du logement est transformée en bande, étendue côté
Room pour franchir un doublage et côté opposé jusqu'au mur.

**Règle préventive :** distinguer proximité architecturale et relation
topologique Revit. Un élément métier « périphérique » ne doit pas être supposé
être l'élément qui porte directement le `BoundarySegment` d'une Room.

**Anti-régression :** test de contrat garantissant que le collecteur explicite
utilise `FilteredElementCollector` + proximité au `room_outer_loop` et ne
dépend plus de `segment.ElementId`; validation Revit sur A003 avec le même
type de mur.

### BUG-PDV-018 — Les murs périphériques d'un lien Revit sont invisibles au moteur

**Symptôme :** la recherche par proximité retourne toujours
`Murs périphériques utilisés : 0` alors que le mur visible est clairement
à moins de 1 000 mm du contour des Rooms.

**Cause :** le sélecteur et le collecteur ne parcouraient que le document hôte.
Un mur affiché dans la vue peut cependant appartenir à un `RevitLinkInstance`.
Dans ce cas, son type et ses instances ne sont pas accessibles via un
`FilteredElementCollector` du projet actif.

**Correction :** exposer dans le sélecteur les types de murs du projet et des
liens Revit chargés, avec une source explicite. Pour une source liée, collecter
dans `GetLinkDocument()` puis transformer points, vecteurs et plage Z dans le
repère hôte avec `GetTotalTransform()` avant le test de proximité.

**Règle préventive :** toute géométrie visible dans une vue de coordination ne
doit pas être supposée appartenir au document actif. Les sélections de types
doivent conserver l'identité de leur document source.

**Anti-régression :** tests de contrat sur `RevitLinkInstance`,
`GetLinkDocument`, les clés `HOST|...` / `LINK|...` et la transformation
des murs liés ; validation Revit A003 en choisissant explicitement la source
affichée dans la liste.

### BUG-PDV-019 — Mur hôte visible mais aucune instance du type n'est retenue

**Symptôme :** Revit montre directement une instance hôte du type
`MUR-EXT-BET-Béton20CM` au niveau du logement, alors que le moteur retourne
toujours zéro mur périphérique.

**Cause potentielle isolée :** le collecteur comparait le texte `UniqueId` du
`WallType` de chaque instance avec la clé de sélection. Ce détour est inutile
et rend le diagnostic impossible lorsque le filtre échoue avant la géométrie.

**Correction :** résoudre une seule fois le `WallType` sélectionné dans le
document source et comparer son `ElementId` à `wall.GetTypeId()`. Ajouter
des compteurs après chaque filtre : type, courbe droite, niveau, zone 2D et
proximité/parallélisme.

**Règle préventive :** pour relier une instance Revit à son type, utiliser
prioritairement `GetTypeId()` et l'identité d'élément Revit. Les identifiants
textuels servent à sérialiser une sélection, pas à répéter le test de type sur
toutes les instances.

**Anti-régression :** test de contrat sur `GetTypeId()`, résolution du type
par `Document.GetElement(uniqueId)` et présence du diagnostic par étapes ;
validation Revit sur A003.

### BUG-TEST-005 — Contrat de type de mur resté sur l'ancien UniqueId

**Symptôme :** la suite Plans de vente échoue après le passage à
`wall.GetTypeId()` parce qu'un ancien test exige encore la chaîne
`wall_type_unique_id != selected_unique_id`.

**Cause :** le test de contrat n'a pas été réaligné avec la correction
BUG-PDV-019 qui remplace volontairement la comparaison de `UniqueId` par
l'identité Revit du type.

**Correction :** vérifier la présence de `wall.GetTypeId()` et
`selected_type_id` à la place de l'ancien filtre textuel.

**Règle préventive :** lorsqu'un test encode précisément une implémentation
qui est remplacée pour corriger un bug, mettre à jour ce contrat dans le même
commit de comportement.

**Anti-régression :** suite complète `tests/plans_vente` dans GitHub Actions.

### BUG-PDV-020 — Raccords arbitraires et recherche globale des poches

**Symptôme :** gaines comblées par des biais, puis collecte de murs complexe et
jusqu'à 50 fermetures avec temps de calcul excessif.
**Cause :** fermeture fondée sur des paires globales de sommets et des cordes,
puis projection sur des murs externes au contour ; validations d'aire ne
prouvant pas la contenance. La marge adaptative pouvait recréer une diagonale
en supprimant un sommet concave, même après correction du premier nettoyage.
**Correction :** moteur pur local `local_crop_geometry.py` ; chaîne bornée à
12 arêtes, supports immédiatement voisins, colinéarité / TR / perpendiculaire.
Murs, types, bandes, faces guides et liens retirés de ce sous-module. Contenance
sur toutes les arêtes, simplicité avec contacts et recouvrements, seuils
3,5 m / 2 m / 5 m², extension maximale 3,5 m, deux passes et 128 validations.
Les chemins de nettoyage de marge utilisent le même moteur ; conservation de
l'original si reconstruction impossible. Les règles historiques BUG-PDV-006 à
011 et 014 à 019 relatives aux paires globales et murs sont remplacées par celle-ci.
**Règle préventive :** ni gain d'aire ni sommets contenus ne garantissent qu'un
candidat ne coupe pas le logement. Contrôler les arêtes complètes et tester
le chemin de secours autant que le chemin principal. Ne pas réintroduire le
buffer 3D de marge (BUG-PDV-013).
**Tests :** `test_local_crop_geometry.py` (A–H, sens/rotation, seuils, 20 poches,
budget), `test_local_crop_adapter.py` (conservation/reconstruction/diagnostic),
contrats sans murs et suite `tests/plans_vente`. A003 reste à valider dans Revit.

### BUG-PDV-021 — Diagnostic suffixé court-circuitant CanHaveShape

**Symptôme identifié dans le code :** dès qu'un compteur était ajouté au mode
« Contour optimisé », sa comparaison exacte échouait et le contrôle de capacité
non rectangulaire de la vue cible pouvait être sauté.
**Cause :** `mode == "Contour optimisé"` mélangeait statut et texte de diagnostic.
**Correction :** test du préfixe du mode conservant les diagnostics détaillés.
**Règle préventive :** les diagnostics ne doivent jamais désactiver un garde-fou.
**Test :** vraie méthode `apply_to_view` avec vue incapable et mode suffixé ;
le rectangle de secours est appliqué. Contrôle réel Revit toujours requis.

### BUG-PDV-022 — Petits segments résiduels utilisés comme supports A/B

**Symptôme :** le moteur local ferme correctement les gaines et reste rapide, mais
quelques petits décrochements persistent à proximité immédiate de certaines poches.

**Cause :** le segment immédiatement avant ou après la chaîne détectée peut lui-même
être un petit retour appartenant visuellement à la poche. Il était alors utilisé comme
support A ou B. Le raccord était géométriquement valide mais s'appuyait sur un segment
trop local, laissant un résidu.

**Correction :** normaliser localement A/B avant raccord. Au maximum deux segments
adjacents peuvent être absorbés de chaque côté lorsqu'ils sont courts relativement au
contexte local. Les règles colinéaire / Trim-Extend / perpendiculaire et tous les
garde-fous de contenance restent inchangés. Le diagnostic compte les segments absorbés.

**Règle préventive :** une chaîne de poche doit être distinguée de ses supports
structurels. Avant de raccorder, vérifier localement que A/B ne sont pas eux-mêmes des
petits retours parasites. Ne jamais remplacer cette normalisation bornée par une
simplification globale du polygone.

**Anti-régression :** tests purs sur absorption gauche, droite, segment court
structurel, limite de deux segments et cas complet avec deux lèvres résiduelles ;
test adaptateur sur le diagnostic des segments absorbés.

### BUG-PDV-023 — Crop optimisé rejeté selon certaines marges sans fallback final

**Symptôme :** selon la marge saisie, Revit affiche
`Le contour calculé n'est pas accepté par Revit comme crop.` et la création
du prototype échoue. Un cas a été confirmé le 2026-10-05 à l'échelle 1:100
avec une marge de 50 mm.

**Cause racine :** le fallback rectangulaire existe lorsque la vue cible ne
supporte pas les crops non rectangulaires, mais il n'est pas utilisé lorsque
`ViewCropRegionShapeManager.IsCropRegionShapeValid(selected_loop)` rejette le
contour optimisé après construction de la marge. Le service lève alors une
erreur au lieu d'essayer le `fallback_curve_loop`.

**Correction planifiée :** lors de la passe de consolidation de l'Étape 03,
si le contour optimisé échoue au contrôle final, valider puis appliquer le
rectangle de secours avant de déclarer un échec. Conserver en parallèle le
diagnostic du contour optimisé afin d'identifier les marges/topologies qui
produisent une boucle non acceptée.

**Règle préventive :** tout chemin de génération d'un crop optimisé doit avoir
un fallback final contrôlé au point exact où Revit valide la boucle. Un fallback
présent uniquement sur un test de capacité amont n'est pas suffisant.

**Anti-régression :** ajouter un test adaptateur où
`CanHaveShape=True`, le contour optimisé est refusé par
`IsCropRegionShapeValid`, mais le rectangle de secours est accepté ; vérifier
que le rectangle est appliqué et qu'un avertissement remplace l'exception.
Rejouer ensuite dans Revit les marges 20 / 50 / 200 / 500 mm sur les logements
de référence.

### BUG-PDV-024 — Noms des types de zones remplies vides dans pyRevit

**Symptôme :** la liste **Zone remplie** contient bien des éléments sélectionnables,
mais toutes les lignes sont visuellement vides dans l'interface Plans de vente.

**Cause racine :** `FilledRegionType` hérite de `ElementType`. Sous
IronPython/pyRevit, l'accès direct à `ElementType.Name` peut être illisible ou
retourner une valeur non exploitable à cause du masquage de la propriété héritée.
Le service utilisait `getattr(region_type, "Name", "")`, ce qui produisait des
libellés vides.

**Correction :** lire en priorité le nom par
`Autodesk.Revit.DB.Element.Name.GetValue(element_type)`, puis conserver
`Name` comme fallback. La même lecture est utilisée dans la liste et dans le
rapport de création.

**Règle préventive :** pour les sous-classes de `ElementType` utilisées sous
IronPython/pyRevit, ne pas supposer que `.Name` est lisible directement.
Centraliser une lecture sûre lorsque le type doit être affiché dans l'UI.

**Anti-régression :** test statique du service imposant
`Element.Name.GetValue(element_type)` pour les `FilledRegionType`, puis
validation réelle dans Revit 2025.4 de l'affichage des noms dans la ComboBox.

**Validation Revit :** confirmée le **5 octobre 2026** ; les noms des types de
zones remplies sont correctement affichés et sélectionnables.

## 5. Identifiants des bugs

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
BUG-EXPORT-017
BUG-EXPORT-018
BUG-EXPORT-019
BUG-EXPORT-020
BUG-EXPORT-021
BUG-EXPORT-022
BUG-EXPORT-023
BUG-EXPORT-024
BUG-EXPORT-025
BUG-EXPORT-026
BUG-EXPORT-027
BUG-EXPORT-028
BUG-EXPORT-029
BUG-EXPORT-030
BUG-EXPORT-031
BUG-EXPORT-032
BUG-EXPORT-033
BUG-EXPORT-037
BUG-EXPORT-038
BUG-EXPORT-039
BUG-EXPORT-036
BUG-EXPORT-035
BUG-EXPORT-034
BUG-TEST-002
BUG-TEST-003
BUG-TEST-004
BUG-TEST-005
BUG-CALCULS-001
BUG-CALCULS-002
BUG-CALCULS-003
BUG-CALCULS-004
BUG-PDV-001
BUG-PDV-002
BUG-PDV-003
BUG-PDV-004
BUG-PDV-005
BUG-PDV-006
BUG-PDV-007
BUG-PDV-008
BUG-PDV-009
BUG-PDV-010
BUG-PDV-011
BUG-PDV-012
BUG-PDV-013
BUG-PDV-014
BUG-PDV-015
BUG-PDV-016
BUG-PDV-017
BUG-PDV-018
BUG-PDV-019
BUG-PDV-020
BUG-PDV-021
BUG-PDV-022
BUG-PDV-023
BUG-PDV-024
BUG-ROOMCALC-001
BUG-COMMON-001
BUG-UI-001
BUG-REVIT-001
BUG-TEST-001
```

## 6. Règle obligatoire avant toute modification et tout commit
