# Registre des bugs — Export

**Statut :** Référence active de développement et de non-régression  
**Cible :** Revit 2025.4 / pyRevit 5.x

Bugs spécifiques au module Export et à sa publication PDF/DWG.

Avant toute modification liée à ce périmètre, lire les fiches applicables
et exécuter les tests anti-régression cités.

---

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

**Complément prévention progression (2026-10-07) :** raccorder les overrides
Stage 07 installés par le smartbutton, ainsi que les fonctions de repli. La session
UI possède seule ouverture/fermeture/restauration ; les handlers XAML restent sur
`PublicationProgressWindow`. Tests des vrais hooks : annulation de l'aperçu sans
export, progression après confirmation, fermeture avant rapport, erreur fatale
d'historique sans 100 % forcé. Ne pas se limiter à une ancienne fonction inactive.

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

**Complément prévention progression (2026-10-07) :** le reporter doit encadrer
l'unique `Document.Export` de chaque carnet, sans modifier le batching. Les PDF
séparés signalent la livraison seulement après le retour natif, et sa fin après
les déplacements ou leur restauration. `tests/test_publication_progress.py`
vérifie le nombre d'appels, le thread, l'ordre transmis, la stabilité du compteur
pendant le natif et les anciens fichiers restaurés après erreur.

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

### BUG-EXPORT-041 — Mode de sortie confondu avec la fusion des vues DWG

**Symptôme :** les exports Par feuille imposent des références externes, tandis que
le mode Combiné laisse croire qu'un carnet entier produit un DWG unique.

**Cause racine :** `PublicationService` déduit `MergedViews` de `dwg_combined` et
`DwgExportService` décrit à tort une fusion de feuilles. Le rapport devine le chemin
unique d'un lot multif feuille sans connaître les suffixes natifs.

**Correction :** réglage `dwg_merge_views` explicite, nullable et héritable, défaut
True ; propagation par tous les hooks réellement actifs. Preset natif conservé,
seules deux surcharges explicites autorisées. Le choix technique « Par feuille /
Lot Revit » est retiré de l'UI : une feuille utilise un appel simple et plusieurs
feuilles un lot natif automatique. Le champ `dwg_mode` reste seulement compatible
avec les anciens stockages. Commande de configuration postée après fermeture modale,
avec cache temporaire de la sélection et réouverture manuelle.

**Règle préventive :** distinguer organisation de la publication, références d'une
feuille et options du preset. Ne jamais dériver `MergedViews` d'une stratégie
d'appel, exposer un choix technique qui ne change pas le résultat métier, promettre
un DWG autonome, figer les réglages hérités au rafraîchissement ou poster une commande
sans rendre la main à Revit. La disponibilité future n'est pas garantie par
`CanPostCommand` ; journaliser/afficher les erreurs immédiates.

**Anti-régression :** `tests/test_export_dwg_settings.py`, tests de sélection multiple
sur le smartbutton actif et suite complète Export/PDF/progression. Recette historique TEST-DWG-SETUP-01 à 12 conservée dans `docs/archive/export-tests/25_Export_Recette_DWG.md`. Le workflow DWG principal a ensuite été validé dans Revit 2025.4 ; les limites natives sur ressources externes restent documentées dans `docs/24_Export_Reglages_DWG.md`.

### BUG-EXPORT-042 — « Dossier du carnet » dépendait du mode combiné/séparé

**Symptôme :** la case « Créer un sous-dossier pour ce carnet » était cochée mais un
PDF combiné ou un lot DWG restait à la racine ; PDF, DWG et annexes pouvaient être
mélangés dans le même dossier.

**Cause racine :** `publication_directory()` ajoutait le nom du carnet uniquement
lorsque `combined=False`. Un choix utilisateur de classement avait donc été couplé
à un détail technique du moteur d'export.

**Correction :** le booléen utilisateur contrôle uniquement l'existence du dossier
du carnet. S'il est actif, tous les modes produisent `NomCarnet/PDF/` et
`NomCarnet/DWG/`. Aperçu et exécution utilisent le même constructeur de chemin.

**Règle préventive :** un libellé métier doit avoir un effet stable et littéral.
Ne jamais faire dépendre une option de classement d'un mode technique non mentionné
dans son libellé. Les ressources auxiliaires d'un format restent dans le dossier
de ce format.

**Anti-régression :** `tests/test_publication_folder_paths.py` couvre PDF combiné
et séparé, DWG, option carnet active/inactive et les trois périmètres de publication.

### BUG-EXPORT-043 — Choix technique DWG exposé et panneau devenu trop haut

**Symptôme :** l'utilisateur devait choisir « Par feuille / Lot Revit » alors que le
livrable restait un DWG par feuille ; l'ajout de ce réglage augmentait également la
hauteur du panneau et favorisait un scroll vertical en usage standard.

**Cause racine :** une stratégie d'optimisation des appels API avait été présentée
comme un réglage métier et ajoutée à la fenêtre principale au lieu d'être pilotée
par le moteur.

**Correction :** suppression des contrôles de mode DWG. La stratégie devient
automatique : une feuille → appel simple ; plusieurs feuilles → lot natif Revit.
Le panneau DWG est compacté sans réduire la typographie et le ScrollViewer reste un
secours. Le contrat cible reste 1320 × 760 sur écran 1920 × 1080.

**Règle préventive :** ne pas exposer un choix purement technique lorsque les
livrables attendus sont identiques. Avant d'ajouter une ligne de réglage à une
fenêtre principale, vérifier qu'elle apporte une décision métier réelle et que les
réglages courants restent visibles sans scroll obligatoire en Full HD.

**Anti-régression :** contrat XAML dans `tests/test_export_dwg_settings.py` :
absence des contrôles de mode, hauteur bornée, libellé dossier du carnet ; recette
visuelle 1920 × 1080 à 100 % et 125 % dans `docs/archive/export-tests/25_Export_Recette_DWG.md`.

### BUG-EXPORT-044 — PDF combiné nommé avec la première feuille

**Symptôme :** un PDF combiné de plusieurs mises en page recevait un nom contenant
le numéro et le nom de la première feuille, par exemple A1101, alors que le fichier
représente le carnet entier.

**Cause racine :** le contexte générique de `FilenameService` utilisait la première
mise en page lorsque `item=None`. Un appel de nommage global pouvait donc résoudre
silencieusement `{numero}` et `{nom}` avec cette feuille.

**Correction :** ajout d'une résolution explicite au niveau carnet pour les
livrables globaux. Les variables propres aux feuilles ne sont plus résolues avec
l'élément 0 ; elles sont remplacées/neutralisées au profit de `{carnet}`.

**Règle préventive :** tout fichier représentant plusieurs éléments doit avoir un
contexte de nommage global explicite. `item=None` ne doit jamais signifier
implicitement « prendre le premier élément » dans un workflow de publication globale.

**Anti-régression :** tests PDF combiné, aperçu/publication et modèles contenant
`{numero}` / `{nom}`.

### BUG-EXPORT-045 — Le nom natif Revit « Feuille » fuit dans les DWG finaux

**Symptôme :** après un lot DWG, les fichiers finaux contenaient le préfixe/suffixe
natif Revit, par exemple `... - Feuille - A1101 - ...dwg`, en plus du modèle de
nommage TAA.

**Cause racine :** le lot Revit était performant mais les noms natifs produits par
`Document.Export` étaient traités comme des noms finaux.

**Correction :** export du lot dans un dossier temporaire, rapprochement conservateur
des DWG principaux par numéro de feuille puis nom de feuille, renommage selon le
moteur TAA, livraison avec sauvegarde/rollback, puis déplacement des ressources
auxiliaires dans le dossier DWG.

**Règle préventive :** lorsque l'API native contrôle le nom d'un fichier intermédiaire,
ne jamais exposer ce nom comme contrat final si l'application possède son propre
moteur de nommage. Toute association native→métier doit échouer en cas d'ambiguïté
plutôt que s'appuyer sur l'ordre ou sur un mot localisé comme « Feuille ».

**Anti-régression :** `tests/test_export_dwg_settings.py` vérifie notamment que les
DWG natifs contenant « Feuille » deviennent des noms TAA exacts et que les PNG/JPG
auxiliaires restent dans le dossier DWG.

### BUG-EXPORT-046 — Progression bloquée pendant les exports longs

**Symptôme :** la fenêtre passait d'une phase à la suivante en un seul saut ; pendant
un export long, l'utilisateur ne savait pas si Revit avançait ni quelle mise en page
était réellement traitée.

**Cause racine :** le pourcentage ne tenait compte que des grandes unités terminées.
Aucune fraction de l'unité native ni progression de livraison n'était remontée.

**Correction :** fraction réelle issue de `Application.ProgressChanged`
(`Position / UpperRange`) pendant les appels natifs, abonnement limité à la durée
de `Document.Export`, puis progression exacte `X / Y mises en page` pendant les
livraisons PDF/DWG contrôlées par Outils TAA.

**Règle préventive :** une barre chiffrée doit être alimentée uniquement par une
mesure réelle. Utiliser les événements natifs lorsqu'ils existent ; sinon accepter
une phase temporairement stable. La progression fine par élément n'est autorisée
que lorsque l'application sait réellement que cet élément est terminé.

**Anti-régression :** tests de monotonie, bornes, progression native, progression
`X / Y`, callback défaillant et désabonnement du bridge ; validation réelle
`ProgressChanged` à effectuer dans Revit 2025.4.

### BUG-EXPORT-047 — Fenêtre de progression instable et compteur technique exposé

**Symptôme :** la fenêtre de progression changeait légèrement de hauteur selon la
longueur du message sous le titre. Le bloc « Traitement » affichait en outre des
valeurs comme `1 / 100 progression Revit`, interprétables à tort comme un nombre
de feuilles.

**Cause racine :** la fenêtre utilisait `SizeToContent="Height"` avec un texte de
statut de hauteur variable. Le compteur brut `ProgressChanged.Position/UpperRange`,
utile au calcul de la barre, était affiché directement comme information métier.

**Correction :** hauteur fixe de la fenêtre et zone de statut réservée à hauteur
constante. Les valeurs natives Revit continuent d'alimenter le pourcentage, mais
l'UI affiche « Revit travaille… ». Pendant une livraison réellement contrôlée,
l'UI affiche en revanche `X / Y` sous le libellé « Mises en page ».

**Règle préventive :** une fenêtre de progression doit conserver une géométrie
stable pendant toute l'opération. Les compteurs techniques de l'API ne doivent pas
être présentés comme des compteurs métier sans sémantique explicite.

**Anti-régression :** contrat XAML sur l'absence de `SizeToContent`, hauteur fixe et
zone de statut stable ; tests UI sur l'affichage « Revit travaille… » et
`X / Y` mises en page.

### BUG-EXPORT-048 — Distinction Dossier / Carnet incompréhensible pour l'utilisateur

**Symptôme :** l'utilisateur devait comprendre qu'un dossier organise des carnets,
alors qu'un carnet contient les mises en page et porte les réglages de publication.
Dans l'usage courant, les deux objets étaient manipulés comme des dossiers.

**Cause racine :** la structure interne du moteur était exposée directement dans
l'interface au lieu d'être traduite en un modèle utilisateur plus simple.

**Correction :** l'interface présente désormais uniquement des dossiers et des mises
en page. Les anciens PublicationSet/CARNET restent internes pour compatibilité mais
utilisent l'icône et le vocabulaire dossier.

**Règle préventive :** ne jamais exposer un type technique distinct si cette
distinction n'apporte aucune décision métier utile à l'utilisateur. Adapter le
modèle visuel au vocabulaire naturel de l'usage.

**Anti-régression :** tests XAML et code vérifiant l'absence de « carnet » dans les
libellés principaux et l'utilisation de `TaaFolderIcon` pour les PublicationSet.

### BUG-EXPORT-049 — Drag/drop éloigné du comportement Explorateur Windows

**Symptôme :** déplacements accidentels, difficulté à viser une position, dossiers
qui ne s'ouvrent pas au survol, absence d'auto-scroll et perte de repères après le
rafraîchissement de l'arbre.

**Cause racine :** le seuil de drag comparait une position locale au lieu du delta
depuis MouseDown, le TreeView était reconstruit sans restaurer complètement son
état et aucun comportement de survol/scroll n'était implémenté.

**Correction :** vrai delta MouseDown, auto-scroll, ouverture au survol ~700 ms,
indicateurs avant/après/dedans, restauration de la sélection, des nœuds développés
et du scroll, déplacement de mises en page entre dossiers.

**Règle préventive :** pour une arborescence de type explorateur, le glisser-déposer
doit préserver le contexte visuel. La reconstruction des données ne doit pas être
perçue comme une remise à zéro de l'interface.

**Anti-régression :** tests de contrat sur seuil système, auto-scroll,
auto-expansion, restauration de scroll et déplacement inter-dossiers.

### BUG-EXPORT-050 — Ordres séparés empêchant d'intercaler les dossiers

**Symptôme :** les sous-dossiers apparaissaient systématiquement avant les anciens
carnets, même lorsque l'utilisateur voulait les intercaler.

**Cause racine :** `PublicationFolder.sort_order` et
`PublicationSet.sort_order` étaient gérés séparément, et l'arbre ajoutait d'abord
tous les dossiers puis tous les carnets.

**Correction :** schéma de stockage 7 avec `tree_order` commun aux deux types.
Le repository sait déplacer des nœuds de types différents dans un même ordre de
fratrie. La migration reprend l'ordre visuel historique comme point de départ.

**Règle préventive :** une liste visuelle unique doit avoir une source d'ordre
persistant unique, même si plusieurs types internes y coexistent.

**Anti-régression :** tests repository sur migration schema 6 → 7 et déplacement
mixte dossier / dossier de publication.

### BUG-EXPORT-051 — Un dossier visuel ne pouvait pas toujours recevoir un sous-dossier

**Symptôme :** après suppression du vocabulaire « Carnet », tous les conteneurs
avaient une icône dossier, mais les anciens PublicationSet n'acceptaient toujours
pas un vrai sous-dossier. Il fallait aussi viser un tiers central trop étroit pour
obtenir un dépôt « dedans ».

**Cause racine :** la première simplification était principalement visuelle :
`PublicationFolder` seul pouvait servir de parent structurel. Le drag utilisait
encore une répartition 1/3 avant, 1/3 dedans, 1/3 après.

**Correction :** schéma 8 avec parent générique par identifiant : PublicationFolder
et PublicationSet persistants peuvent tous deux recevoir des sous-dossiers et
d'autres dossiers de publication. L'arbre, la publication récursive, l'héritage des
réglages, la suppression et la détection de cycles suivent cette hiérarchie réelle.
La zone de dépôt « dedans » occupe désormais 70 % de la ligne, avec 15 % seulement
pour avant/après.

**Règle préventive :** si deux objets ont la même représentation et le même nom
métier dans l'UI, leurs capacités structurelles fondamentales doivent être identiques.
Une simplification visuelle ne doit jamais masquer deux comportements incompatibles.

**Anti-régression :** tests du schéma 8, parent PublicationSet, cycle, suppression
d'un parent non vide, publication récursive et contrat 15/70/15.

### BUG-EXPORT-052 — Dépôt « dedans » incorrect sur un dossier ouvert

**Symptôme :** un dossier pouvait recevoir un autre dossier lorsqu'il était fermé,
mais le même geste devenait difficile ou impossible lorsqu'il était déplié.

**Cause racine :** le calcul des zones 15/70/15 utilisait
`TreeViewItem.ActualHeight`. En WPF, cette hauteur inclut les enfants lorsque le
nœud est ouvert. La position du pointeur sur la ligne d'en-tête était donc comparée
à la hauteur de tout le sous-arbre.

**Correction :** calculer les zones de dépôt uniquement avec le visuel
`TreeViewItem.Header` et les coordonnées relatives à cet en-tête. La hauteur
totale du nœud n'est utilisée qu'en fallback.

**Règle préventive :** dans un TreeView hiérarchique, toute hit-zone correspondant à
la ligne du nœud doit utiliser les dimensions du header, jamais
`TreeViewItem.ActualHeight` lorsque le nœud peut être développé.

**Anti-régression :** test avec un TreeViewItem simulé à 220 px et un header à
20 px ; le centre du header doit rester `INSIDE`, indépendamment de la hauteur
des enfants.

### BUG-EXPORT-053 — Wrapper d'initialisation incompatible avec le nouveau contexte de stockage

**Symptôme :** après raccordement du smartbutton collaboratif, l'appel
`ExportWindow(..., storage_context=...)` aurait pu échouer à l'ouverture avec
un argument inattendu, alors que la classe `ExportWindow` elle-même acceptait
bien ce nouveau paramètre.

**Cause racine :** `publication_preview_integration.install_preview_on_export_window`
remplace dynamiquement `ExportWindow.__init__` par un wrapper dont la signature
était restée limitée à `(controller, repository)`. L'extension dynamique
masquait donc le nouveau contrat du constructeur réel.

**Correction :** faire suivre explicitement `storage_context=None` dans le
wrapper puis appeler le constructeur d'origine avec ce paramètre.

**Règle préventive :** tout monkey-patch ou décorateur qui remplace une méthode
publique doit préserver son contrat d'appel, y compris les nouveaux paramètres
optionnels. Lorsqu'un constructeur est enveloppé, ajouter un test statique ou
d'intégration couvrant les arguments transmis par le point d'entrée réel.

**Anti-régression :** `tests/test_export_collaborative_ui.py` vérifie que le
wrapper accepte et retransmet `storage_context`.
