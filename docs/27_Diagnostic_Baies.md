# Diagnostic des baies — Outils TAA

**Statut : V0.1 en cours de validation**, branche de développement `feature/calculs-regle-1-6-baies`.
**Cible :** Autodesk Revit 2025.4 et pyRevit 5.x.

## Objectif

Vérifier les paramètres dimensionnels effectivement présents dans les fenêtres et les portes des familles du projet, pour décider ultérieurement comment calculer la **surface de baie en tableau** utile à la règle des 1/6 RE2020. Ce module de diagnostic **n'est pas** un calcul des 1/6 et **ne certifie pas** les surfaces réglementaires.

## Utilisation

1. Ouvrir le projet Revit représentatif.
2. Lancer **Outils TAA → Calculs → Diagnostic des baies**.
3. Cocher éventuellement **Inclure les fichiers Revit liés directs chargés**.
4. Cliquer **Analyser**, consulter la synthèse famille/type, le nombre d'occurrences et les alertes.
5. Cliquer **Exporter les CSV** et choisir la destination.

Trois CSV Excel français, **UTF-8 avec BOM, séparateur point-virgule** :
- Fichier principal : **une ligne par occurrence**, source hôte ou lien, catégorie, famille, type, identifiants, hôte, pièces From/To (si disponibles), paramètres dimensionnels, méthode envisagée, surface candidate et limites.
- Fichier `_types.csv` : synthèse par source et type, compte des occurrences, divergences.
- Fichier `_alertes.csv` : incidents de collecte, liens non chargés, éléments illisibles.

Les liens imbriqués ne sont pas analysés. Chaque **instance de lien direct** est distinguée, même si plusieurs instances chargent le même fichier.

## Logique de diagnostic

Les longueurs de paramètres (`SpecTypeId.Length`) sont converties en mètres. Le moteur recherche des noms explicites et privilégie :
1. `Largeur tableau` + `Hauteur tableau` (et variantes) : `CANDIDAT_TABLEAU`.
2. `Rough Width` + `Rough Height` ou noms d'ouverture : `CANDIDAT_OUVERTURE`.
3. `Largeur` + `Hauteur` nominaux : `NOMINAL_A_CONFIRMER`.

Les paramètres d'occurrence priment sur les paramètres de type ; toute contradiction à portée identique est signalée. `A_VERIFIER` indique un manque ou une ambiguïté de mesures. `VARIABLE_SELON_OCCURRENCE` est affiché en synthèse lorsque les occurrences d'un type divergent.

**Point critique :** `Largeur x Hauteur` reste un **produit indicatif** tant que la construction de la famille, son vide de découpe et le mur hôte n'ont pas confirmé le tableau exact. Les dimensions de boîte englobante sont montrées uniquement comme indice géométrique : elles **ne mesurent pas** l'ouverture du mur.

## Sécurité et limites

- Aucune transaction Revit : **lecture seule**, ni ouverture ni modification de familles.
- Fenêtres et portes seulement, **y compris les portes pleines**. Le vitrage, les panneaux de mur-rideau et la conformité RE2020 ne sont pas évalués.
- Les valeurs de FromRoom/ToRoom ne prouvent pas le caractère extérieur d'une baie ; la fonction d'un mur non plus.
- Les paramètres numériques qui ne sont pas typés comme **longueur** ne sont pas convertis artificiellement.
- Les documents liés déchargés donnent une alerte, sans arrêter le diagnostic.
- Pour les familles ambiguës : examen manuel dans l'éditeur de familles requis.

## Architecture et tests

- `Calculs.panel/DiagnosticBaies.pushbutton/` : entrée pyRevit.
- `Calculs.panel/ui/baies_diagnostic_window.py`, `ui/baies_diagnostic.xaml` : interface WPF, thème Outils TAA.
- `Calculs.panel/services/baies_diagnostic_service.py` : collecte Revit.
- `OutilsTAA.extension/lib/baies_diagnostic/evaluator.py` : moteur pur.
- `tests/baies_diagnostic/test_evaluator.py` : tests hors Revit.

Commande : `python -m pytest tests/baies_diagnostic -q`.

**Avant fusion main :** tester réellement dans Revit 2025.4 : fenêtre standard, porte-fenêtre, porte pleine, famille fabricant avec cotes différentes, lien chargé et déchargé, deux instances du même lien, export CSV accentué, absence de famille, sensibilité aux paramètres de type/occurrence. Aucune validation Revit réelle n'est revendiquée à ce stade.

## Correctif de compatibilité IronPython — 22 octobre 2026

L'erreur rencontrée lors du premier essai dans Revit 2025.4 était `ImportError: No module named Data` pendant la création du tableau de synthèse WPF, **après** la collecte initiale. Le composant `baies_diagnostic/ui_table.py` charge désormais explicitement l'assembly `System.Data.Common` (avec repli `System.Data`), puis remplit des `DataRow` typés avec des chaînes Unicode.

Les 4 tests de l'adaptateur exécutés hors Revit utilisent des simulations CLR et **ne valident pas** la présence ou le fonctionnement de cet assembly dans le vrai moteur pyRevit. Rejouer le diagnostic dans Revit puis exporter les trois CSV pour confirmer. Voir `BUG-CALCULS-007`.

## Correctif noms FamilySymbol / Family — 22 octobre 2026

Le second essai utilisateur a montré **1 349 occurrences exclues** avec le même message `Name`. Les paramètres n'étaient pas en cause : l'appel direct de `symbol.Name` pouvait échouer sous IronPython. Les noms des familles et types sont désormais lus par `DB.Element.Name.GetValue` avec mécanismes de repli, afin de conserver l'occurrence même en cas de nom inaccessible. Voir `BUG-CALCULS-008`. La reprise de l'analyse dans le Revit réel reste à confirmer.

## Périmètre métier des fenêtres de façade — 22 octobre 2026

Selon les conventions TAA, **les familles dont le nom commence par `FEN-EXT` ou `PORFEN-EXT`** sont la cible privilégiée du diagnostic. Le contrôle est maintenant **coché par défaut** dans l'interface, et peut être désactivé pour conserver l'inventaire complet. Le tri se fait sur le **nom de famille** (pas le nom de type, ni uniquement la catégorie Revit). Les familles `PORFEN-EXT` présentes dans la catégorie Revit Fenêtres sont bien retenues.

Analyse des trois exports du projet du 22 octobre 2026 (`Diagnostic_Baies_20261022_165459*.csv`) :

- **1 349 occurrences** globales, **0 alerte**.
- **416 occurrences** correspondant aux préfixes, **12 familles, 18 types**.
- Parmi ces 416 : **250** surfaces candidates d'après `Largeur × Hauteur` nominaux, **159** d'après `Largeur brute × Hauteur brute`, **7** sans paire de dimensions exploitable.
- **405 occurrences** hébergées par un mur déclaré `Exterior`, **11 lanterneaux en toiture**.
- **9 occurrences** de `FEN-EXT-GEN-1V_MRX` (dont type `Métal perforé`) demandent vérification ; elles ne doivent pas être comptabilisées automatiquement comme vitrage.
- Il reste ainsi **396 occurrences présumées correspondre à des menuiseries de façade usuelles**, avant vérification réelle du verre, du tableau et du périmètre réglementaire.
- Sur 153 portes-fenêtres ordinaires `PORFEN-EXT`, `Largeur brute` excède `Largeur` de 4 cm et `Hauteur brute` excède `Hauteur` de 20 à 30 cm : les surfaces brutes sont environ 11 à 17 % plus élevées, selon les types.
- Les types `170x140` de la famille `FEN-EXT-GEN-2V_VR_ITI` ont pourtant `Hauteur = 1,28 m` dans le relevé : **le nom du type ne doit pas être considéré comme une mesure**.

La colonne `facade_status` est maintenant ajoutée aux exports occurrences et types ainsi qu'à la grille WPF. Les classifications possibles : `FACADE_PRESUMEE_A_VALIDER`, `CAS_SPECIAL_LANTERNEAU`, `CAS_SPECIAL_NON_VITRE_A_VERIFIER`, `HOTE_NON_MUR_A_VERIFIER`, `EXTERIORITE_A_VERIFIER` et `HORS_PREFIXES`.

Ces classements sont **strictement indicatifs** : le préfixe ne démontre pas la présence de vitrage ni la dimension effective du tableau. Il faudra vérifier une famille témoin par configuration, notamment les écartements entre `Largeur brute` et `Largeur`.

Tests ajoutés : `tests/baies_diagnostic/test_facade_scope.py`. Recette restant à effectuer dans Revit 2025.4 : sur le modèle source, obtenir les **416** éléments ciblés en cochant le filtre, puis les 1 349 en le décochant, sous réserve d'absence de changements du modèle entre essais.

## Recette utilisateur — filtre façade dans Revit 2025.4 (22 octobre 2026)

Capture transmise depuis le module **Outils TAA — Diagnostic des baies**, avec la case `Limiter aux familles commençant par FEN-EXT ou PORFEN-EXT` cochée et la case liens Revit décochée :

- **416 occurrences, 18 types et 0 alerte**, correspondant au total attendu d'après les CSV antérieurs.
- **250** occurrences `NOMINAL_A_CONFIRMER`, **159** `CANDIDAT_OUVERTURE` et **7** `A_VERIFIER`.
- La grille affiche les familles, types, quantités, méthode dimensionnelle, statut dimensionnel et statut façade.
- Les exceptions `CAS_SPECIAL_LANTERNEAU` et `CAS_SPECIAL_NON_VITRE_A_VERIFIER` apparaissent dans la synthèse.

**Validation limitée :** l'utilisateur a confirmé par capture le fonctionnement du **filtre hôte + collecte + affichage WPF + comptage sans erreur**. L'export CSV du *nouveau filtre* n'a pas été montré, les liens directs n'étaient pas cochés, et aucune surface en tableau ni conformité RE2020 n'a été validée. Les contrôles manquants restent à réaliser avant fusion dans `main`.
