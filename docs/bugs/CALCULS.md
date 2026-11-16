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
### BUG-CALCULS-007 — Divergences de valeurs entre occurrences et variantes non visibles

**Symptôme :** sur une maquette avec variantes de conception et plusieurs occurrences de groupes, l'écriture dans `Surface logement` échoue. La restauration de l'alignement par type de groupe aurait modifié 9 éléments ; 898 écritures sont annulées dans le rapport de référence du 16 novembre 2026. L'utilisateur ne peut pas choisir d'autoriser des valeurs différentes ni une valeur commune par type de groupe. Les variantes prises en compte ne sont pas indiquées.

**Cause racine confirmée pour l'écriture :** la logique de `BUG-CALCULS-005` rétablit systématiquement `VariesAcrossGroups=False`, y compris si différentes occurrences calculent des totaux incompatibles. Le rapport ne prouve pas, à lui seul, que les variantes sont la cause de la différence. La collecte documentée traite toutes les pièces du projet.

**Correction implémentée (branche `fix/calculs-group-conflicts-design-options`) :**
- Diagnostic en préparation des écarts de totaux entre les occurrences d'un même type de groupe ;
- Choix utilisateur entre conserver `VariesAcrossGroups=True` de façon permanente ou retenir une valeur commune de référence et restaurer l'alignement ;
- Interdiction d'uniformiser si plusieurs regroupements indépendants existent dans une même occurrence de groupe ;
- Protection contre les écritures partielles, restauration qui modifie des éléments et choix incomplets ;
- Affichage informatif des variantes existantes et des pièces collectées dans chaque variante, sans changer le calcul ni son périmètre.

**Règle préventive :** ne pas modifier un réglage de définition de paramètre partagée par des groupes sans décision explicite lorsqu'une divergence est connue. N'uniformiser que des valeurs dont la correspondance par type de groupe est identifiée. Pour les variantes, expliciter quelles pièces sont lues sans prétendre recalculer une géométrie spécifique à une vue.

**Anti-régression :** `tests/calculation/test_group_decisions.py`, puis suite `tests/calculation`. Revit 2025.4 : groupe type identique sur deux occurrences avec résultats différents, les deux choix, annulation, retour arrière, variante principale/secondaire, filtre, et cas historique sans divergence.

**Complément BUG-CALCULS-007 — séparation des variantes et fenêtre TAA (retour utilisateur Revit du 16 novembre 2026) :** la capture montre 24 pièces du modèle principal, 8 de la variante principale et 4 de la variante secondaire. Ancien comportement : les pièces partageant un numéro d'appartement (exemple B200) pouvaient être additionnées indépendamment de leur variante, mélangeant les solutions de conception. Correction de la branche : clé de groupe métier inchangée pour le scénario principal, clé distincte pour chaque variante secondaire. Le filtrage par vue a été envisagé, puis explicitement rejeté par l'utilisateur et retiré. La boîte pyRevit `CommandSwitchWindow` tronquait les explications et contrevenait à `docs/04_UI_Guidelines.md` ; choix des conflits et confirmation désormais en WPF avec thème partagé. Anti-régression B200 sur deux variantes et clé de groupe vide ajoutée. Ces corrections nécessitent la recette dans Revit avant fusion.\n\n**Complément — confirmation WPF TAA des appartements multi-variantes :** un même appartement B200 détecté dans plusieurs scénarios doit être explicitement confirmé comme **séparé** avant écriture. La fenêtre donne les totaux indépendants par scénario et permet d'annuler sans aucune transaction. Le moteur refuse également l'écriture si la confirmation manque, sans modifier les agrégations ni les variantes. **Anti-régression** : confirmation absente bloque la transaction, confirmation présente conserve la logique existante, appartement d'une seule variante ne déclenche pas le dialogue ; tests ajoutés dans `test_group_decisions.py`. **Recette Revit : en attente.**\n\n**Statut au 16 novembre 2026 :** code et tests créés ; **tests automatisés non encore exécutés**, **validation Revit en attente**. Ne pas déclarer le bug clos avant recette.

**Complément ergonomie BUG-CALCULS-007 (capture utilisateur du 16/11/2026) :** boutons Annuler / Confirmer absents de la fenêtre de confirmation multi-variantes : le code forçait une hauteur de 320 unités WPF, insuffisante pour l'en-tête, le récapitulatif et le pied d'actions. Correction : hauteur modale 440 unités WPF dans le mode confirmation ; texte long défilable, boutons hors du ScrollViewer. Libellé « variante Variante 1 » corrigé pour afficher le nom sans duplication et référence étiquetée. Anti-régression : tests de contrat de dimensionnement et libellés dans `test_group_decisions.py`. Validation visuelle en Revit 2025.4 toujours à refaire.

**Complément BUG-CALCULS-007 — redimensionnement du panneau de détails :** après réapparition des boutons de confirmation, la recette Revit montre que le rectangle blanc contenant le texte ne suit pas l'agrandissement vertical de la fenêtre. Cause identifiée dans `calculation_decision.xaml` : `Grid.Row=1` dimensionnée `Auto`, rangée des choix masquée dimensionnée `*` et `ScrollViewer.MaxHeight=170`. Correction : détails `*` sans MaxHeight, choix `Auto` plafonnés, pied d'actions conservé hors zone de défilement. Test anti-régression : analyse XML/XAML dans `test_group_decisions.py` des définitions de lignes et de la hauteur du ScrollViewer. La validation visuelle finale Revit reste ouverte.

### BUG-CALCULS-008 — Addition volontaire des surfaces de variantes (nouvelle option)

**Besoin :** après validation du mode « surfaces séparées », l'utilisateur doit aussi pouvoir additionner toutes les surfaces d'un même numéro d'appartement, y compris celles situées dans plusieurs variantes. Le regroupement séparé était codé sans alternative accessible dans l'interface.

**Cause :** `variant_group_key` distinguait systématiquement les variantes secondaires ; la fenêtre principale n'exposait aucun mode de regroupement alternatif.

**Correction implémentée, non validée dans Revit :** liste `GESTION DES VARIANTES` WPF TAA (mode séparé par défaut ; mode addition explicite). En mode addition, clé de regroupement = numéro d'appartement sans variante ; **le total cumulé est écrit dans toutes les pièces du regroupement**. Détection des appartements multi-scénarios conservée à partir d'un second calcul *séparé* informatif ; avertissement sur le double comptage de variantes alternatives, détail des composantes, total cumulé, confirmation obligatoire avant transaction. Mode inconnu rejeté ; mode séparé inchangé ; aucun filtre selon la vue.

**Règle préventive :** ne jamais additionner implicitement des solutions de conception différentes ; séparer par défaut et exiger confirmation pour l'addition lorsqu'un appartement appartient à plusieurs scénarios. Rappeler explicitement la portée de l'écriture dans toutes les variantes.

**Anti-régression :** `tests/calculation/test_group_decisions.py` vérifie B200 en mode séparé, en mode addition, le total écrit à chaque pièce, la confirmation bloquante et les modes invalides. Exécuter la suite `tests/calculation` et la suite Export. **Validation dans Revit 2025.4 / pyRevit 5.x en attente.**

### BUG-CALCULS-009 — Trop de fenêtres de confirmation / surcharge d'informations

**Retour utilisateur :** le calcul pouvait ouvrir successivement une confirmation des variantes, un choix du mode groupes, une boîte par type de groupe lors d'une uniformisation, puis une confirmation générale et un rapport final. Le récapitulatif général affichait de nombreuses informations techniques non utiles à la décision.

**Cause :** parcours WPF séquencé en boîtes indépendantes, et rapport modal imposé après toute exécution.

**Correction implémentée (PR #56, Revit non encore validé) :** une **revue WPF TAA unique** avant écriture, récapitulatif concis, avertissement court de double comptage, choix des groupes et des valeurs de référence à l'intérieur de cette fenêtre. Confirmation unique et refus d'écrire si les choix nécessaires sont absents. En cas de succès, état dans la fenêtre principale ; rapport détaillé accessible par bouton facultatif. Un échec conserve un rapport automatique.

**Protection :** ne jamais modifier automatiquement `VariesAcrossGroups` en présence de divergences, ne pas perdre les confirmations de variante déjà imposées par le moteur et annuler sans transaction. **Anti-régression :** tests de contrat UI et suite `tests/calculation`, plus essais sous Revit 2025.4 (avec et sans conflit), non encore effectués.

### BUG-CALCULS-010 — Choix de gestion des groupes absent de la fenêtre principale

**Retour Revit utilisateur :** le choix de groupes n'est proposé qu'au moment de la confirmation lorsqu'un conflit est détecté. Demande d'un réglage de premier niveau comme pour les variantes. L'utilisateur confirme parallèlement les scénarios de recette **2 à 8 OK** du bilan de PR #56 ; le scénario 1 (autoriser les valeurs différentes durablement) n'est pas déclaré validé.

**Cause :** le choix `group_mode` était défini au stade `PreparedCalculation` et uniquement géré par la revue conditionnelle.

**Correction proposée et implémentée sur `feat/calculs-group-mode-main-ui` :** `GESTION DES GROUPES` dans la fenêtre WPF principale, trois choix `auto/vary/uniform`, transmis `CalculationRequest → Controller → Workflow → revue WPF`. En mode manuel, ne pas redemander l'option à la confirmation ; en mode commun, demander uniquement les références nécessaires. Toujours refuser les uniformisations non sûres et les valeurs manquantes avant transaction.

**Anti-régression :** tests ciblés `test_group_decisions.py` et CI Calculs + Export, validation Revit 2025.4 du sélecteur et des deux parcours de groupe. **Non validé dans Revit au moment du commit.**

### BUG-CALCULS-012 — Uniformisation partielle des occurrences de groupe

**Symptôme :** « Conserver une valeur commune entre groupes » peut échouer avec plusieurs dizaines d'éléments réalignés. Les opérations préparées ne couvraient que les pièces collectées/filtrées ; les éléments homologues situés dans d'autres occurrences du même type de groupe n'étaient pas comparés. En mode « valeurs différentes », une boîte « aucun résultat » pouvait apparaître avant transaction sans expliquer quelle donnée était absente.

**Cause :** `group_conflicts` analyse seulement les écritures du calcul. La restauration `SetAllowVaryBetweenGroups(False)` agit à l'échelle de la définition du paramètre ; l'ancien contrôle rejetait systématiquement tout élément retourné par l'API, même s'il était attendu et conservait la bonne valeur.

**Correction proposée/implémentée sur `fix/calculs-uniform-revit-groups-v2` :** plan des membres homologues par ordre documenté de `Group.GetMemberIds()`, récupération de toutes les occurrences du type, écritures supplémentaires explicites, restauration et vérification de toutes les valeurs post-restauration avant commit. Modification durable `VariesAcrossGroups=True` maintenue en mode « valeurs différentes ». Le mode uniforme rend aussi `VariesAcrossGroups=False` lorsque le paramètre était auparavant variable. Les validations historiques et rollback ne sont pas supprimés. Causes des sommes absentes détaillées sans transaction.

**Règle préventive :** ne jamais considérer qu'un ensemble de pièces sélectionnées représente toutes les occurrences d'un type de groupe. Ne pas approuver un réalignement si le membre concerné n'a pas été explicitement préparé ou si la valeur finale diffère. Aucune suppression/reconstruction de groupe.

**Tests :** `test_member_alignment.py` : écriture d'un membre homologue hors filtre, alignement précédemment variable, durabilité de valeurs différentes, retour d'ID attendu, ID hors plan et valeur modifiée entraînant rollback, diagnostic sources/groupes vides. CI puis validation Revit obligatoires.

### BUG-CALCULS-013 — Uniformisation écrasée par le réalignement Revit malgré les membres homologues

**Retour utilisateur Revit 2025.4 du 16/11/2026, PR #59 (non fusionnée) :** mode **« Autoriser des valeurs différentes » validé OK** ; mode **« Conserver une valeur commune » KO**. Pendant la restauration, l'élément ID **5630105** a vu son résultat prévu **380.286410009** remplacé par **324.979623715**. Transaction des 36 écritures annulée. Les valeurs sont des nombres en unités internes Revit dans le journal ; ne pas les qualifier arbitrairement de m².

**Cause observée :** Revit remplace une valeur précédemment écrite au moment de `SetAllowVaryBetweenGroups(False)`. La documentation Autodesk confirme que cette méthode effectue un réalignement automatique ; l'ordre des membres homologues ne garantit pas à lui seul la valeur qu'elle retient. La cause précise de la valeur source 324.979623715 reste à identifier sur le RVT.

**Correction expérimentale sur PR #59 :**
- Pré-contrôle des consignes par couple `(ID du type de groupe, position de membre retournée par GetMemberIds())` : deux valeurs différentes au même emplacement sont refusées avant la transaction, avec type et pièces concernés.
- `Document.Regenerate()` appelé **après les écritures et avant le rétablissement de l'alignement** du paramètre, seulement en mode uniforme, pour forcer les mises à jour différées. Hypothèse : Revit pouvait employer des valeurs/caches non encore régénérés. L'appel doit être testé dans Revit ; ce n'est **pas** une preuve de correction.
- Si Revit remplace encore une valeur, erreur contextualisée avec ID et type de groupe et maintien du rollback. Aucune écriture forcée après le réalignement et aucune suppression/reconstruction de groupes.
- Mode valeurs différentes validé laissé inchangé.

**Règle préventive :** ne jamais considérer `SetAllowVaryBetweenGroups(False)` comme une simple propriété booléenne sans effet sur les données. Vérifier les valeurs effectives après régénération et réalignement et annuler dès qu'elles diffèrent. Ne jamais annoncer l'uniformisation comme résolue sans essai réel Revit.

**Anti-régression :** `test_member_alignment.py` : conflit de valeurs homologues 380.286410009 / 324.979623715 avant transaction, restauration qui écrase une valeur, ordre `writes → Document.Regenerate → SetAllowVaryBetweenGroups(False)` simulé. Tests sur une copie du RVT obligatoires, en confirmant l'ID 5630105.

**Complément BUG-CALCULS-013 — nouvelle recette Revit (captures utilisateur du 16/11/2026).** Le mode uniforme montre explicitement **2 types de groupes** : type ID `5629042`, choix « Groupe 1 — 35.330 m² » ; type ID `5629531`, choix « Groupe 2 — 16.047 m² ». Les 36 écritures sont une nouvelle fois annulées : pour l'élément `5630105`, attendu `380.286410009` (valeur interne correspondant à ≈35.33 m²), Revit impose `324.979623715` (≈30.19 m²) après le retour à `VariesAcrossGroups=False`. La régénération proposée lors du tour précédent **n'a pas suffi** : ne plus considérer l'hypothèse « régénération seule » comme corrective. Les captures indiquent que le diagnostic de type de groupe renvoyait `inconnu` malgré le fait que l'interface connaissait deux IDs de types.

**Nouvelle correction instrumentée (PR #59, toujours en brouillon) :** relever pour chaque élément la valeur effective **après écritures et `Document.Regenerate()`, juste avant le réalignement**, refuser immédiatement les pertes de valeur survenues avant ce passage ; après `SetAllowVaryBetweenGroups(False)`, comparer de nouveau les valeurs attendues et les valeurs effectives. Sur échec, le message distingue les deux étapes et tente de remonter nom/ID du type depuis le groupe Revit ou à défaut le diagnostic de conflits préparé. Ce changement **ne prétend pas uniformiser** une maquette qui est réalignée d'autorité par Revit ; il maintient le rollback et ne touche pas au mode « valeurs différentes » validé.

**Tests anti-régression :** simulation d'une valeur écrasée lors de régénération (pas d'appel `False`) ; simulation d'une valeur écrasée seulement par la restauration (capture de valeur avant/valeur après et ID du type). La validation Revit reste à réaliser.

**Complément décisif BUG-CALCULS-013 — règle Autodesk retrouvée le 16/11/2026 :** [Documentation Autodesk — Create or Modify Project Parameters](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Model/files/GUID-28CBBEC2-6262-42D3-AE41-B36166E8318F.htm) précise explicitement que lorsqu'un paramètre passe de valeurs variables à valeurs alignées, **la valeur retenue par Revit est celle attribuée au membre dans la première occurrence du groupe**. La documentation [InternalDefinition.SetAllowVaryBetweenGroups](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/6f5af0cc-2ab3-153a-e07d-78fbc12aefc1.htm) confirme que l'appel `False` réaligne les membres et peut modifier des éléments. Ceci explique le mécanisme du remplacement de 380.286410009 par 324.979623715, sans démontrer à lui seul de quelle occurrence provient cette valeur dans ce RVT.

**Conséquence technique :** les modifications actuellement codées (écriture de tous les homologues, régénération puis `False`) **ne permettent pas de garantir la valeur commune explicitement sélectionnée**. Un simple changement d'ordre des écritures ou une nouvelle régénération ne résoudra pas ce contrat. Ne jamais déclarer le mode uniforme corrigé dans PR #59. Pour fixer arbitrairement la valeur du membre de groupe, Autodesk décrit l'édition interactive du groupe. L'API Revit ne fournit pas d'équivalent transactionnel simple et fiable de ce mode. Ne pas tenter d'ungroup/regroup automatique sans accord explicite et protocole d'intégrité/Undo.

**Résultat final de la dernière recette :** type 5629042, élément 5630105, valeur voulue 380.286410009 et valeur imposée 324.979623715 ; valeur AVANT restauration = 380.286410009, donc seule la phase `SetAllowVaryBetweenGroups(False)` provoque le remplacement. Rollback des 36 écritures correct.

**Prochaine conception :** dissocier « garder l'alignement existant » de « définir une nouvelle valeur commune ». Préférer pour le second un parcours assisté d'édition du groupe ou une proposition d'opération avancée séparée, explicitement approuvée. Préserver le mode valeurs différentes déjà validé.

### BUG-CALCULS-014 — Choix d'une nouvelle valeur commune incompatible avec la valeur de référence Revit

**Symptôme :** l'utilisateur choisit 35,330 m² pour le type 5629042, mais `SetAllowVaryBetweenGroups(False)` rétablit une valeur différente : élément 5630105 attendu 380.286410009 et obtenu 324.979623715 en unités internes. Le rollback protège le projet ; les tentatives d'écritures de membres homologues et `Document.Regenerate()` ne suffisent pas.

**Cause confirmée du mécanisme :** Revit réutilise la valeur du membre de la première occurrence lorsqu'on désactive la variabilité du paramètre entre occurrences. Cette règle est documentée dans l'aide Autodesk relative aux paramètres de projet. L'identité de cette occurrence de référence dans le RVT doit encore être vérifiée.

**Correction proposée et implémentée dans PR #59 (non fusionnée) :** contrôle **en lecture seule avant écriture** des valeurs actuelles du paramètre cible sur les membres des types où un conflit de surfaces est détecté. Si une nouvelle référence est demandée, la revue unique WPF affiche nom/ID du type, valeur cible, valeur actuelle et exemple d'ID pièce/groupe ; elle demande d'utiliser « Modifier le groupe » dans Revit, sans transaction. Même règle imposée par le moteur pour éviter un contournement de l'interface. Si les références existent déjà, le comportement historique validé le 6 octobre reste disponible, avec rollback si Revit impose tout de même un changement non prévu. Aucune modification du mode « valeurs différentes » (validé Revit).

**Règle préventive :** ne pas assimiler l'écriture en mode temporairement variable à l'édition de la valeur de référence du type de groupe. Ne pas présenter une intervention manuelle comme une automatisation du mode uniforme. N'ajouter ni `UngroupMembers` ni régénération supplémentaire comme substitut à une édition de groupe.

**Anti-régression :** test d'une nouvelle référence qui bloque **avant** toute transaction et vérifie le guide, test d'une référence déjà compatible et du chemin historique, vérification du raccordement de la fenêtre WPF, suite Calculs et Export. Validation dans Revit 2025.4 encore attendue.

### BUG-CALCULS-015 — Sélecteur de groupes inutile et blocage d'une nouvelle valeur commune

**Symptôme :** la fenêtre principale proposait trois modes de groupes, puis le parcours uniforme nécessitait une édition manuelle du groupe. L'utilisateur demande une gestion automatique avec explication visible de la modification du réglage du paramètre plutôt qu'un sélecteur.

**Cause :** l'alignement `VariesAcrossGroups=False` par Revit peut remplacer la valeur commune nouvellement calculée. L'assistance précédente interdisait l'écriture alors que l'utilisateur accepte le changement durable de réglage du paramètre cible.

**Correction implémentée en branche PR #59 :** retirer le `GroupModeCombo` de la fenêtre principale ; afficher une phrase informative `GroupPolicyText`. Le mode automatique conserve un choix de valeur commune par type uniquement si sûr. Si cette référence n'est pas déjà compatible avec l'alignement existant, l'outil écrit les valeurs communes mais **laisse `VariesAcrossGroups=True` durablement**, avec avertissement dans la fenêtre et dans le rapport. Les groupes non uniformisables passent par les écritures individuelles. Le mode de valeurs différentes déjà validé n'est pas modifié au niveau du moteur.

**Règle préventive :** ne pas qualifier un paramètre de « suit les groupes » après le repli : l'égalité des valeurs écrites est un instantané, pas une contrainte Revit permanente. Toujours informer explicitement de la modification globale de la définition. Pas de dégroupage ni réactivation de `False` si cela écraserait la valeur choisie.

**Tests :** contrat XAML fenêtre principale, choix auto + référence par type dans la revue unique, repli explicite et durabilité du réglage, cas historique encore aligné. CI Calculs et Export, recette Revit sur copie avant fusion.
