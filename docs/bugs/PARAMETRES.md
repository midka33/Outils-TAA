# Registre des bugs — Paramètres des pièces

**Cible :** Revit 2025.4 / pyRevit 5.x, IronPython.

### BUG-PARAM-001 — `ImportError: No module named Data` au clic sur les deux boutons

- **Symptôme :** depuis `Numeroter.pushbutton` ou `ModifierTexte.pushbutton`, le chargement de `room_parameters_window.py` s'arrête sur `from System.Data import DataTable`.
- **Cause :** l'assembly .NET `System.Data` n'était pas référencée explicitement dans la session IronPython avant l'import.
- **Correction :** ajouter `import clr` puis `clr.AddReference("System.Data")` avant `from System.Data import DataTable`.
- **Règle préventive :** charger explicitement les assemblies .NET non garanties par le runtime pyRevit, et vérifier leur ordre d'import avec un test statique. Un test CPython ne prouve pas le chargement sous IronPython.
- **Anti-régression :** `tests/test_room_parameter_wpf_contract.py::test_system_data_assembly_loaded_before_import`, puis lancement réel des deux boutons sous Revit 2025.4 / pyRevit 5.x.
- **État :** correctif implémenté, contrôle statique prévu, **recette Revit après correction en attente**.

### BUG-PARAM-002 — Présentation des commandes différente des boutons compacts pyRevit

- **Symptôme :** deux grands boutons distincts, alors que le modèle demandé est un groupe de petites commandes empilées avec icône et texte.
- **Cause :** les boutons étaient placés directement dans `Parametres.panel` au lieu d'un bundle `.stack`.
- **Correction :** création de `Commandes.stack` contenant deux `*.pushbutton`, avec métadonnées de layout et chemins d'accès à l'interface corrigés.
- **Règle préventive :** pour obtenir des boutons compacts superposés, utiliser un bundle `.stack` pyRevit de deux ou trois commandes et tester la résolution des chemins après déplacement.
- **Anti-régression :** `tests/test_room_parameter_wpf_contract.py::test_compact_revit_ribbon_stack_structure`, puis inspection visuelle du ruban Revit.
- **État :** implémenté, **recette visuelle Revit en attente**.

### BUG-PARAM-003 — Conflit de noms du ruban lors du rechargement à chaud

- **Symptôme constaté par l'utilisateur (23/11/2026) :** `Stack 'Commandes' skipped: The name already exists:Numeroter` au rechargement pyRevit ; les deux anciens grands boutons restent visibles.
- **Cause probable :** le ruban de la session Revit conserve les contrôles `Numeroter` et `ModifierTexte` créés avant le déplacement dans `Commandes.stack`. La nouvelle pile ne peut pas réutiliser ces identifiants déjà enregistrés. **Le redémarrage à froid n'a pas encore été testé.**
- **Correction implémentée :** identifiants internes propres à la pile (`TAA_NumeroterPieces`, `TAA_ModifierTextePieces`) ; titres visibles et moteurs inchangés. Le redémarrage complet de Revit est requis pour purger les contrôles historiques et vérifier l'affichage.
- **Règle préventive :** après le déplacement d'une commande dans un conteneur pyRevit, vérifier l'unicité des noms internes et recetter le ruban après fermeture complète de Revit ; ne pas interpréter un simple Reload comme une reconstruction de ruban à neuf.
- **Anti-régression :** `tests/test_room_parameter_wpf_contract.py::test_compact_revit_ribbon_stack_structure` et test visuel Revit après redémarrage.
- **État :** correction locale implémentée ; **26 tests ciblés réussis**, **971 tests complets réussis (87 avertissements)** ; recette Revit en attente.

### BUG-PARAM-004 — Saisie impossible dans les zones de texte WPF

- **Symptôme (retour Revit utilisateur) :** les zones « Valeur initiale », « Pas », « Texte à ajouter ou supprimer » et « Séparateur » ne permettent pas la saisie.
- **Cause racine :** non déterminée ; le XAML initial ne définissait aucune restriction explicite à l'édition. Il serait incorrect d'affirmer que l'ajout de `Focusable` traite la cause sans nouvel essai dans Revit.
- **Correction proposée/implémentée localement :** déclarer explicitement `IsReadOnly=False`, `IsEnabled=True`, `Focusable=True`, un fond et un premier plan lisibles ; réduire leur hauteur à 28 px.
- **Règle préventive :** tester l'entrée au clavier dans chaque `TextBox` directement dans Revit, y compris après `Hide()/Show()` de la fenêtre.
- **Anti-régression :** vérification statique des attributs dans `test_editable_fields_replace_choice_and_compact_preview`, puis recette clavier en Revit.
- **État :** changement local testé statiquement ; **28 tests ciblés et 973 tests complets réussis (87 avertissements)** ; **correction fonctionnelle non vérifiée sous Revit**.

**Retour supplémentaire :** l'utilisateur confirme que la saisie ne fonctionne
toujours pas dans la version essayée. Nouvelle tentative : focus WPF explicite
au premier rendu et non-restauration des anciennes valeurs vides pour Numéroter.
Les deux fenêtres sont maintenant séparées ; **test clavier réel encore ouvert**.
