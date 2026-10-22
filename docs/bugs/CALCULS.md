# Registre des bugs — Calculs des pièces

**Statut :** Référence active de développement et de non-régression  
**Cible :** Revit 2025.4 / pyRevit 5.x

Bugs spécifiques au module Calculs des pièces.

Avant toute modification liée à ce périmètre, lire les fiches applicables
et exécuter les tests anti-régression cités.

---

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

### BUG-CALCULS-006 — Découverte des paramètres répétée trois fois à l'ouverture

**Symptôme :** sur un projet comportant beaucoup de logements/pièces et de paramètres,
la fenêtre Calculs des pièces met plusieurs secondes à apparaître.

**Cause :** `CalculationController.load_context()` demandait successivement la liste
complète, la liste numérique puis la liste écrivable. Chaque demande reparcourait
toutes les pièces et tous leurs paramètres et recalculait les mêmes métadonnées Revit.

**Correction :** effectuer une seule découverte complète, puis dériver les listes
numériques et destinations par filtrage des descripteurs déjà agrégés en mémoire.
Pendant ce scan, réutiliser les métadonnées invariantes par `Parameter.Id` ; relire
uniquement les états susceptibles de varier par pièce.

**Règle :** lorsqu'une collecte API coûteuse produit déjà un modèle suffisamment
riche pour plusieurs vues de données, ne pas relancer la collecte pour chaque filtre.
Collecter une fois, dériver ensuite en mémoire.

**Anti-régression :** le test du contrôleur vérifie explicitement qu'un chargement de
contexte n'appelle `get_parameter_descriptors()` qu'une seule fois ; un second test
vérifie que deux occurrences partageant le même `Parameter.Id` ne relisent les
métadonnées Revit qu'une seule fois.
 
### BUG-CALCULS-007 — Import de `System.Data` échoue dans IronPython (Diagnostic des baies)

**Symptôme :** dans Revit 2025.4 / pyRevit 5.1, au clic sur **Analyser** du diagnostic des baies, erreur `ImportError: No module named Data` à l'instruction `from System.Data import DataTable` (trace écran du 22 octobre 2026, `baies_diagnostic_window.py`, ligne 33).

**Cause racine :** le code utilisait un espace de noms .NET sans charger explicitement son assembly CLR. La collecte pouvait s'exécuter, mais le tableau WPF échouait avant affichage des résultats.

**Correction :** chargement explicite par `clr.AddReference("System.Data.Common")` (Revit 2025 / .NET 8), avec repli `System.Data` si nécessaire ; affichage déplacé dans `baies_diagnostic/ui_table.py`. Utilisation de `DataTable.NewRow()` + `Rows.Add(DataRow)` et conversion Unicode pour éviter les ambiguïtés de surcharge et les erreurs sur les accents.

**Règle préventive :** tout type issu d'un assembly .NET non automatiquement chargé doit être importé **après** `clr.AddReference`; les appels à des collections `.NET` avec surcharges doivent privilégier des objets fortement typés. Ne pas assimiler la réussite de tests CPython à une validation IronPython/WPF dans Revit.

**Anti-régression :** `tests/baies_diagnostic/test_ui_table.py` vérifie le chargement explicite, le repli, les lignes de synthèse et les accents sous mocks CLR (4 tests). **À rejouer impérativement dans Revit 2025.4 / pyRevit 5.1** : ouvrir Diagnostic des baies, lancer Analyser, vérifier le tableau et exporter les 3 CSV (projet simple et familles accentuées).
