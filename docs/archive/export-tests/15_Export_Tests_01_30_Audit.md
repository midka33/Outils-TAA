# Export — Audit des tests 01 à 30

**Projet :** Outils TAA  
**Module :** Export  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Date de l'audit :** 2026-09-16  
**Objet :** établir la traçabilité entre les tests 01 à 30, les problèmes rencontrés, les corrections présentes dans le dépôt et la validation restante.

---

## 1. Conclusion de l'audit

La campagne historique des tests 01 à 30 est bien présente dans `docs/14_Export_Tests_Lundi.md`. Le commit `8a0536f` confirme que les résultats et erreurs avaient été consignés jusqu'au TEST-30.

L'audit du dépôt montre que les problèmes rencontrés pendant cette campagne ont ensuite fait l'objet de corrections dans le code et/ou de tests de non-régression.

**Important :** la présence d'un correctif dans GitHub ne constitue pas à elle seule une preuve qu'un test Revit manuel a été rejoué après le dernier correctif. L'audit distingue donc :

- **CORRIGÉ / COUVERT** : problème identifié et correction ou couverture anti-régression retrouvée dans le dépôt ;
- **À REVALIDER Revit** : correction présente mais nouveau passage manuel nécessaire pour certifier le comportement final dans Revit 2025.4 ;
- **NON ÉTABLI** : aucune preuve suffisante retrouvée pour affirmer le passage final du test.

À ce stade, il est donc incorrect d'affirmer que les 30 tests ont tous été rejoués et validés après les derniers commits. En revanche, les problèmes connus issus de la campagne sont désormais tracés et les principaux problèmes fonctionnels identifiés ont été corrigés.

---

## 2. Matrice de traçabilité TEST-01 à TEST-30

| Test | Domaine | Problème / constat connu | État du correctif dans le dépôt | Validation finale Revit |
|---|---|---|---|---|
| TEST-01 | Ouverture Export | Aucun problème consigné dans le résultat historique | Couvert par les corrections UI et handlers ultérieures | À revalider |
| TEST-02 | Arborescence | Aucun problème consigné dans le résultat historique | Couvert par la persistance et le filtrage projet | À revalider |
| TEST-03 | Création dossier | Aucun problème consigné dans le résultat historique | Persistance des dossiers présente | À revalider |
| TEST-04 | Création carnet dans dossier | **KO : `_folder_targets` non défini** lors de la sélection d'un dossier | **CORRIGÉ** par import explicite de `_folder_targets`; capitalisé en BUG-EXPORT-018 | À revalider |
| TEST-05 | Persistance carnet | Risque de perte/doublon de persistance identifié pendant le développement | Couverture repository/persistance présente | À revalider |
| TEST-06 | Carnet par paramètre | Le mode `PARAMETER` pouvait être transformé en carnet manuel | **CORRIGÉ**; BUG-EXPORT-005 | À revalider |
| TEST-07 | Filtrage par projet | Des données persistantes d'un autre projet pouvaient apparaître | **CORRIGÉ**; BUG-EXPORT-007 puis BUG-EXPORT-017 pour l'identité projet | À revalider |
| TEST-08 | Déplacement carnet vers dossier | Fonctionnalité de déplacement initialement défaillante | **CORRIGÉ**; déplacements persistants et drag/drop présents | À revalider |
| TEST-09 | Réordonnancement carnets | Ordre manuel devait être conservé | **CORRIGÉ**; persistance `sort_order` / `move_sets` | À revalider |
| TEST-10 | Sélection multiple | TreeView WPF ne fournit pas nativement la sélection multiple | **CORRIGÉ**; sélection Ctrl/Maj explicite | À revalider |
| TEST-11 | Déplacement groupé | Déplacement de plusieurs éléments initialement absent/incomplet | **CORRIGÉ**; `move_sets` puis mécanisme multi-déplacement généralisé | À revalider |
| TEST-12 | Insertion groupée | Insertion avant cible à fiabiliser | **CORRIGÉ**; réordonnancement multi-sélection | À revalider |
| TEST-13 | Ordre mises en page | L'ordre manuel devait être préservé | Couverture de l'ordre et du déplacement présente | À revalider |
| TEST-14 | PDF | Réglages PDF et enum Revit avaient nécessité une correction | **CORRIGÉ**; BUG-EXPORT-010 et tests PDF | À revalider avec export réel |
| TEST-15 | DWG | Modes combiné/séparé et destinations à contrôler | Implémentation et tests d'agrégation présents | À revalider avec export réel |
| TEST-16 | True Color | Résultat réel DWG à vérifier dans Revit | Paramètre/configuration DWG présente | **À REVALIDER impérativement** |
| TEST-17 | Destination persistante | Persistance des destinations implémentée | Couvert par persistance des réglages | À revalider |
| TEST-18 | Héritage dossier → carnet | Héritage implémenté | Couvert par settings dossier/carnet | À revalider |
| TEST-19 | Surcharge carnet | Une modification locale devait rester limitée au champ modifié | **CORRIGÉ**; BUG-EXPORT-012 | À revalider |
| TEST-20 | Conservation héritage | Une modification ne doit pas transformer les autres héritages en overrides | **CORRIGÉ**; BUG-EXPORT-012 | À revalider |
| TEST-21 | Retour héritage | Réinitialisation des overrides à contrôler | Implémentation présente | À revalider |
| TEST-22 | Variables nommage | Moteur de nommage couvert par tests | Couverture de preview/naming présente | À revalider |
| TEST-23 | Paramètre Revit dans nom | `{parametre:Sous-titre}` à contrôler | Découverte de paramètres et preview couvertes | À revalider |
| TEST-24 | Caractères interdits | Sécurisation Windows à contrôler | Utilitaires de nommage présents | À revalider |
| TEST-25 | Prévisualisation carnet | Prévisualisation séparée de l'export | **COUVERT** par tests de preview | À revalider UI |
| TEST-26 | Informations preview | Cohérence des lignes de livrables/destinations | **COUVERT** par tests de preview et agrégation | À revalider UI |
| TEST-27 | Feuille manquante | Les références persistantes doivent résoudre par `UniqueId` | **CORRIGÉ**; BUG-EXPORT-009 | À revalider |
| TEST-28 | Collision | Détection des fichiers existants à contrôler | Logique de publication/preview présente | À revalider |
| TEST-29 | Annulation | Aucun fichier ne doit être produit après annulation | Workflow preview présent | À revalider |
| TEST-30 | Confirmation | La confirmation doit déclencher la publication réelle | Orchestration et moteur de publication présents | **À REVALIDER impérativement** |

---

## 3. Bugs effectivement capitalisés issus de la campagne

Les bugs directement pertinents pour cette campagne sont notamment :

- **BUG-EXPORT-005** — conservation du mode de carnet par paramètre ;
- **BUG-EXPORT-006** — doublons entre persistance et session ;
- **BUG-EXPORT-007** — carnets provenant d'un autre projet ;
- **BUG-EXPORT-009** — référence durable d'une feuille via `UniqueId` ;
- **BUG-EXPORT-010** — enum `PDFExportQualityType` ;
- **BUG-EXPORT-012** — héritage et overrides locaux ;
- **BUG-EXPORT-013** — destinations différentes lors d'une publication de dossier ;
- **BUG-EXPORT-014** — drag/drop et sélection multiple ;
- **BUG-EXPORT-015** — handlers `ExportWindow` et couche d'intégration ;
- **BUG-EXPORT-017** — isolation des dossiers persistants par projet ;
- **BUG-EXPORT-018** — `_folder_targets` non importé ;
- **BUG-EXPORT-019** — réordonnancement/multi-déplacement et conservation des parents ouverts.

Le registre global doit rester la référence de capitalisation de ces problèmes.

---

## 4. Derniers correctifs liés à la campagne

Les derniers commits pertinents montrent notamment :

- `00ad4b4` — correction de la multi-sélection et du déplacement après cible ;
- `93542b6` — réordonnancement multi-sélection et conservation des parents ouverts ;
- `689d66d` — persistance de l'ordre des dossiers ;
- `4ea98c8` — capitalisation des tests de réordonnancement et multi-sélection ;
- `4ea98c8` est le commit documentaire le plus récent au moment de cet audit.

Ces commits montrent que les problèmes de la dernière partie de la campagne ont continué à être traités après la consignation initiale des TEST-01 à TEST-30.

---

## 5. Ce qui peut être considéré comme débuggé

### Oui — problèmes identifiés

Les problèmes explicitement identifiés pendant la campagne et retrouvés dans le code ont une correction ou une couverture de non-régression correspondante.

### Non — certification finale des 30 tests

On ne peut pas encore écrire : **« TEST-01 à TEST-30 tous validés après tous les derniers correctifs »**.

La raison est simple : plusieurs corrections ont été apportées après la campagne initiale, notamment sur le drag/drop, le réordonnancement, la sélection multiple et la conservation de l'état développé. Ces corrections nécessitent un nouveau passage dans Revit pour constituer une preuve de validation finale.

---

## 6. Campagne de revalidation recommandée

Pour clôturer définitivement TEST-01 à TEST-30, refaire les 30 tests sur la version actuelle du dépôt, dans Revit 2025.4 / pyRevit 5.x, sans modifier le code pendant la campagne.

Pour chaque test :

```text
TEST-XX : OK / KO / NON TESTÉ
Erreur : message exact si KO
Capture : oui/non
Correction associée : BUG-EXPORT-XXX ou commit
```

Les tests prioritaires après les derniers changements sont :

```text
TEST-04  sélection d'un dossier / création carnet
TEST-08  déplacement carnet
TEST-09  ordre des carnets
TEST-10  sélection multiple
TEST-11  déplacement groupé
TEST-12  insertion groupée
TEST-13  ordre des mises en page
TEST-16  True Color réel
TEST-19  surcharge sans casser l'héritage
TEST-20  conservation de l'héritage
TEST-25  prévisualisation
TEST-26  informations de prévisualisation
TEST-27  feuille manquante
TEST-28  collision
TEST-29  annulation
TEST-30  confirmation / export réel
```

---

## 7. Règle de clôture

La campagne 01–30 sera considérée comme **VALIDÉE** uniquement lorsque les 30 lignes auront été rejouées sur la version actuelle et que chaque ligne sera `OK` ou, pour un scénario volontairement non reproductible, explicitement documentée avec justification.

Un correctif de code ne remplace pas une validation Revit lorsque le comportement concerné dépend de WPF, de l'API Revit ou du moteur PDF/DWG.
