# Préparation de la release Outils TAA v1.5.0

**Date cible :** 17 novembre 2026 · Revit 2025.4 · pyRevit 5.x · Windows.

## Périmètre à publier

Le paquet est construit depuis **le commit exact de `main` qui déclenche le workflow**, après fusion de la PR #60 (« À propos »). Le code de `main` comprend notamment :

- **PR #55 (fusionnée)** : dossiers automatiques Export, sous-dossiers paramétriques, gel individuel et réversibilité ; recette Revit confirmée par l'utilisateur (DYN-12 à DYN-20).
- **PR #30 (fusionnée)** : configuration collaborative JSON Export par central, statut local/partagé, révision et protections contre écrasement ; **validation simultanée sur deux postes non établie**, à vérifier en agence.
- **PR #60 (fusionnée)** : bouton À propos dans le ruban OutilsTAA, premier panneau à gauche, fenêtre WPF et couleur orange TAA ; capture utilisateur du dialogue et de la position du bouton confirmée le 17/11/2026.
- **Calculs des pièces** : améliorations des groupes Revit, variantes et revues WPF. Le parcours courant a été testé positivement par l'utilisateur ; les cas de groupes complexes, alignement de valeur commune et rollback demeurent soumis aux précautions du document `docs/10_Calculs_Pieces.md`.
- **Plans de vente** : conserver la V1.1 et les options présentes en v1.4.1, sans annoncer de nouvelles fonctionnalités.

**Version de la suite :** `OutilsTAA.extension/version.json` doit indiquer `version=1.5.0`, `channel=stable`, `last_published=1.5.0`. Le bouton À propos affichera **1.5.0** (sans « développement »).

## Chaîne de publication

1. PR dédiée `release/v1.5.0` : notes de version, tutoriels, installateur CMD, manifeste et workflow `.github/workflows/release-v1.5.0.yml`.
2. À la PR : faire passer **tous les tests** Export, ruban, collaboratif, Calculs, Plans de vente, puis vérifier le ZIP et les signatures SHA-256.
3. Contrôler l'archive : **trois modules + À propos + `version.json` stable**, absence de modèles RVT, caches, MSI ou fichiers temporaires. `git archive` doit porter sur le SHA du commit testé.
4. Installer CMD : contrôle SHA-256 avec la bonne expression **`Outils-TAA_v1[.]5[.]0[.]zip$`**, et contrôle de la version embarquée avant remplacement. L'ancien installateur v1.4.1 recherchait par erreur le nom ZIP v1.4.0 dans son contrôle SHA : **corrigé dans cette version**.
5. Fusion de la PR seulement si les contrôles sont verts.
6. Sur `main`, le job `publish` est conditionné par la réussite de `validate`; il crée `v1.5.0` sur **`github.sha`**, refuse de remplacer une release déjà publiée, téléverse ZIP, CMD, SHA256SUMS et trois tutoriels.
7. **Vérification finale obligatoire :** contrôler l'existence de la release v1.5.0, la cible du tag, le statut de publication, la présence effective des six actifs et leurs sommes SHA-256. Ne pas déclarer « release publiée » à partir de la seule fusion de PR.

## Contrôles et limites à divulguer

- Recette fonctionnelle des dossiers automatiques et de la réversibilité : **confirmée dans Revit 2025.4**.
- Bouton À propos : présence en première position et dialogue version développement : **confirmés dans Revit**. Affichage du nouveau numéro **1.5.0 stable** à vérifier sur le ZIP installé.
- Configuration collaborative sur **deux postes Windows/SMB en parallèle** : à confirmer en agence, même si tests unitaires et intégration sont verts.
- Installateur CMD v1.5.0 **exécuté sur un vrai poste Windows** : non encore testé à la préparation.
- Plans de vente : moteur métier inchangé depuis v1.4.1 ; garder ses non-régressions automatisées.
- Modules cotation, étiquetage, légendes, giration : non livrés.

## Résultats

**En attente des jobs du commit final de la branche de release**, puis du commit de `main`. Consigner ici la cible réelle du tag, le lien de la release et les actifs seulement après vérification.
