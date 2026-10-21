# Registre des bugs — Tests et livraison

**Statut :** Référence active de développement et de non-régression  
**Cible :** Revit 2025.4 / pyRevit 5.x

Bugs liés aux tests, à la CI et à la validation des livrables.

Avant toute modification liée à ce périmètre, lire les fiches applicables
et exécuter les tests anti-régression cités.

---

### BUG-TEST-002 — Tests désynchronisés des contrats de publication et de diagnostics

**Symptôme :** quatre échecs hors Revit.
**Cause :** fausses vues sans `Id` ; assertion d'identité de liste incompatible avec la copie défensive des diagnostics.
**Correction :** doubles exposant l'identifiant courant et test de contenu/non-mutation de la liste source. Les tests de lot utilisent le modèle réel PublicationSet.
**Règle préventive :** les doubles doivent respecter les propriétés effectivement lues ; vérifier le contrat métier plutôt qu'imposer une identité mémoire non spécifiée.
**Anti-régression :** suite pytest complète, avec `--import-mode=importlib` pour les deux fichiers `test_project_identity.py`.

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

### BUG-TEST-006 — Aucun contrôle Export déclenché sur le commit de main

**Symptôme :** les PR #22 et #23 sont vertes, mais aucune exécution ni check run
n’est associé au commit de fusion `44503dff` de `main`.

**Cause racine :** le workflow Export ne ciblait en push que l’ancienne branche
`feature/export-progress-ui` ; aucun déclenchement manuel n’était disponible.

**Correction :** ajout de `main` aux branches de push, de `workflow_dispatch`
et des documents de livraison aux chemins de PR déclenchant la suite Export.

**Règle préventive :** une vérification de release doit identifier le commit
exact couvert par les résultats CI ; ne pas confondre tête de PR et merge commit.

**Anti-régression :** contrôle des événements YAML, suite Export sur la PR,
puis vérification des Actions du commit de `main` avant toute publication.

**Complément livraison Plans de vente — 16 octobre 2026 :** la règle
BUG-TEST-006 est étendue aux workflows Plans de vente, Calculs et contrat ruban
Export : exécution sur `main` et contrôle du SHA exact avant création du tag.
BUG-COMMON-002 s’applique aussi au ZIP utilisateur : retrait des répertoires de
tests/caches et contrôle du contenu décompressé avant publication.