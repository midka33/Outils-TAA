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
