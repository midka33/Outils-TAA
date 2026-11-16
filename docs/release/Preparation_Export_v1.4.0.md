# Outils TAA v1.4.0 — Préparation et recette Export

**Version :** v1.4.0  
**Module concerné :** Export  
**Date de validation fonctionnelle :** 3 novembre 2026  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x / Windows  
**PR fonctionnelle :** [#39](https://github.com/midka33/Outils-TAA/pull/39) — fusionnée dans `main`, commit `5a37be83e3d5893156399b242b838f4a9805ef58`.  
**Branche de préparation :** `release/v1.4.0-export` — dédiée aux notes, tutoriels, packaging et release.  
**Statut documentaire :** **release v1.4.0 publiée et vérifiée** le 3 novembre 2026 ; le test manuel de l'installateur Windows reste à réaliser.

## 1. Périmètre précis

La version ajoute et stabilise l'explorateur de feuilles, la sélection et les ajouts multiples, les opérations de dossiers, l'organisation indépendante des fichiers par format et la publication récursive. Les correctifs assurent la continuité des modèles et paramètres hérités.

**Hors périmètre :**
- nouvelles fonctions Calculs des pièces ;
- nouvelles fonctions Plans de vente (V1.1 reste inchangée) ;
- travaux non fusionnés des branches Cotations/Étiquettes, Giration ou autres ;
- réintroduction de « publier uniquement les modifiés » ;
- exécution PDF en arrière-plan.

La procédure de release ne fusionne, ne supprime et ne réécrit aucune autre branche : elle utilise exclusivement le code déjà intégré à `main` et les documents de préparation.

## 2. Recette fonctionnelle confirmée par l'utilisateur

| ID | Vérifications principales | Résultat |
|---|---|---|
| EXPORT-01 | A2000, 5 PDF combinés + 16 DWG, fichiers réels et chemins | ✅ |
| EXPORT-02 | Renommage, contenu et réglages conservés, persistance | ✅ |
| EXPORT-03 | Retrait des feuilles et dossiers, garde-fous, réouverture | ✅ |
| EXPORT-04 | Ajout, glisser-déposer, Ctrl/Maj, doublons, ordre | ✅ |
| EXPORT-05 | Héritage, surcharges, annulation des surcharges, aperçu | ✅ |
| EXPORT-06 | Redémarrage Revit, persistance globale et indépendance des projets | ✅ |

**Source de validation :** confirmation directe de l'utilisateur lors de la recette du 3 novembre 2026.

**Précision :** le comportement des commandes F2 et clic droit, ainsi que chacune des quatre combinaisons de dossiers, ne disposent pas d'une confirmation manuelle isolée ; les principaux scénarios métier et la validation des options indépendantes sont confirmés, et les chemins croisés disposent de tests automatisés.

## 3. Contrôles de non-régression

- [x] PR #39 fusionnée proprement dans `main`.
- [x] 375 tests automatisés Export passés sur la branche validée avant la fusion.
- [x] Contrat ruban Export réussi sur cette branche.
- [x] Aucune modification de code métier hors Export dans la PR #39.
- [x] Compatibilité des anciens réglages et modèles de noms testée.
- [x] Workflow de publication v1.4.0 terminé avec succès sur le SHA exact `21336b3df7f54ea2b4692384ba414e048bfae89e` : **375 Export, 3 ruban, 79 Calculs, 297 Plans de vente**, soit 754 tests.
- [x] ZIP vérifié : **191 entrées**, modules Export, Calculs des pièces et Plans de vente présents ; aucun fichier interdit détecté.
- [x] SHA-256 des actifs générés et vérifiés pendant le workflow de publication ; `SHA256SUMS.txt` disponible dans la release.
- [x] [GitHub Releases v1.4.0](https://github.com/midka33/Outils-TAA/releases/tag/v1.4.0) vérifiée : tag sur `21336b3df7f54ea2b4692384ba414e048bfae89e`, six actifs et notes publiques, non brouillon.
- [ ] Test d'installation Windows par un utilisateur après publication de l'installateur v1.4.0.

Les cases non cochées seront attestées par les exécutions GitHub Actions / tests Windows après leur réalisation. Ne pas les considérer comme réussies du seul fait de la présence de ce document.

## 4. Distribution prévue

- ZIP `Outils-TAA_v1.4.0.zip` : uniquement l'arborescence `OutilsTAA.extension/` du commit.
- CMD `INSTALLER_Outils_TAA_v1.4.0.cmd` : téléchargement HTTPS, contrôle SHA-256, fermeture préalable de Revit, sauvegarde de la précédente extension puis remplacement utilisateur.
- `SHA256SUMS.txt` : contrôles de l'archive, de l'installateur et des tutoriels.
- Tutoriels Export, Calculs des pièces et Plans de vente adaptés à v1.4.0.
- Notes de release affichées sur GitHub à partir de `docs/release/Notes_v1.4.0.md`.

**Règle de publication :** créer le tag `v1.4.0` sur le SHA de `main` testé par la CI de release, jamais sur la tête d'une branche de fonctionnalité encore en cours.

## 5. Prochaines étapes après publication

1. Vérifier la visibilité de la release et de ses actifs sur GitHub.
2. Installer depuis le CMD sur le poste Windows de recette, sans élévation.
3. Ouvrir Revit 2025.4, effectuer un test de non-régression simple des trois modules.
4. Reprendre les développements parallèles sur leurs branches respectives en se synchronisant avec `main`, sans merge automatique entre elles.


## 6. Attestation de publication — 3 novembre 2026

- **PR de préparation :** [#41](https://github.com/midka33/Outils-TAA/pull/41), fusionnée dans `main`.
- **Commit Git et tag `v1.4.0` :** `21336b3df7f54ea2b4692384ba414e048bfae89e` (tag léger de type commit, contrôlé sur l'API GitHub).
- **Pipeline terminé :** [GitHub Actions — Publication Outils TAA v1.4.0](https://github.com/midka33/Outils-TAA/actions/runs/41667879829), deux jobs réussis (validation puis publication).
- **Actifs vérifiés :** `Outils-TAA_v1.4.0.zip` (334 595 octets), `INSTALLER_Outils_TAA_v1.4.0.cmd`, `SHA256SUMS.txt`, trois tutoriels.
- **Contrôles sur le SHA publié :** Export 375, ruban 3, Calculs 79, Plans de vente 297 ; ZIP validé et somme SHA-256 correcte.
- **Limite restante :** aucune exécution réelle de l'installateur v1.4.0 sur Windows n'est encore attestée. La recette utilisateur Export, elle, a été effectuée dans Revit 2025.4 avant la distribution.
