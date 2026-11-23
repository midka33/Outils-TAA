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
