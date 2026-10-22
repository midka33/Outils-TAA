# Roadmap Outils TAA

## Phase 1 — Socle architectural

- [x] Formaliser l'architecture du dépôt.
- [x] Définir les frontières entre UI, métier, Revit et infrastructure commune.
- [x] Créer `OutilsTAA.extension/`.
- [ ] Créer `lib/common/` et ses services fondamentaux.
- [x] Normaliser les noms des documents de documentation.
- [x] Mettre en place la structure pyRevit de base.
- [x] Mettre en place les règles de gouvernance IA, documentation, roadmap et capitalisation des bugs.

## Phase 2 — Export

### Étapes réalisées

- [x] Modèles de publication Dossier → Carnet → Mise en page.
- [x] Création de carnets par paramètre.
- [x] Carnets manuels persistants et temporaires.
- [x] Dossiers persistants et création d'un carnet dans le dossier sélectionné.
- [x] Déplacement et réorganisation des carnets par glisser-déposer.
- [x] Sélection multiple `Ctrl` / `Shift` et déplacement groupé.
- [x] Profils de publication.
- [x] Héritage Profil → Dossier → Carnet et retour à l'héritage.
- [x] PDF combiné/séparé.
- [x] DWG combiné/séparé.
- [x] True Color DWG.
- [x] Moteur de nommage dynamique et paramètres Revit.
- [x] Prévisualisation avant publication.
- [x] Publication récursive d'un dossier.
- [x] Prévisualisation et rapport globaux pour publication multiple.
- [x] Persistance des destinations et des réglages.
- [x] Registre de bugs et règles anti-régression.

### Stabilisation avant TEST-14 — 2026-09-28

- [x] Associer les PDF séparés aux noms TAA et contrôler les fichiers livrés.
- [x] Transmettre le modèle hérité sans changer les surcharges persistantes.
- [x] Supprimer les deux initialisations redondantes du glisser-déposer.
- [x] Actualiser les tests et capitaliser les bugs 020 à 024.
- [x] TEST-14 validé par l'utilisateur le 2026-09-29 dans Revit 2025.4 : profils, PDF combinés/séparés, noms et contenu des fichiers (dont `PC 09*`), code `7bb533c`. Voir `docs/archive/export-tests/17_Export_Preparation_TEST14.md`.
- [ ] Recontrôler TEST-04 et un déplacement multiple après suppression des doublons.
- [ ] Consolider la surcouche `stage07` après validation réelle.

### V1 — Sélection multiple et tutoriel (2026-10-05)

- [x] Raccorder la sélection Ctrl/Maj au résumé, à l'aperçu et à la publication.
- [x] Tester hors Revit les sous-ensembles, l'ordre, les doublons et les réglages indépendants.
- [x] Rédiger le [tutoriel utilisateur](docs/archive/export/20_Export_Tutoriel.md).
- [x] Validation utilisateur du fonctionnement de la sélection multiple dans Revit le 2026-10-05 (PR #11).
- [ ] Valider MS-01 à MS-10 dans Revit 2025.4 : [recette](docs/archive/export-tests/21_Export_Recette_Selection_Multiple.md).
- [ ] Valider le tutoriel avec l'utilisateur avant release.

### V1 — Stabilisation et sortie

- [x] Retirer l'option « Publier uniquement les mises en page nouvelles ou modifiées » (décision du 2026-09-30).
- [x] Neutraliser les anciennes valeurs `modified_only`, y compris dans les dossiers, carnets et profils.
- [x] Reproduire les dossiers/sous-dossiers sur disque ; ranger les formats séparés par carnet.
- [ ] Valider les quatre combinaisons PDF/DWG et les chemins réels (TEST-V1-02).
- [ ] Valider dans Revit la publication complète après retrait de l'option (TEST-V1-01).
- [x] Résoudre les réglages à travers les dossiers parents (TEST-31).
- [ ] Revalider TEST-31 dans Revit après correction.
- [ ] Terminer les tests V1, dont TEST-44 et profils P1 à P4, puis la non-régression.
- [ ] Finaliser et sortir Export V1 avant de reprendre les fonctionnalités V2.

### V1 — Finition graphique TAA

- [x] Socle fonctionnel validé par l'utilisateur le 2026-09-30, TEST-44 et profils P1–P4 compris.
- [x] Thème commun orange pastel, typographie, contrôles, tableaux et pictogrammes.
- [x] Application aux cinq fenêtres Export et adaptation des champs au redimensionnement.
- [x] Valider le rendu réel, clavier et DPI dans Revit 2025.4.
- [x] Rejouer la non-régression après refonte dans Revit 2025.4.
- [x] Accepter la finition graphique et le sélecteur de paramètres après validation utilisateur le 2026-10-01.

Voir `docs/18_Export_Charte_UI_V1.md` pour les contrôles réalisés et ceux restant dans Revit.

### V2 — Réévaluer la publication des seules mises en page nouvelles ou modifiées

**Reportée après finalisation et sortie de la V1 ; réintroduction à décider.**
Le socle historique et ses tests isolés sont conservés, mais le filtrage est désactivé en V1.

- [ ] Analyser les retours TEST-35 (collision) et TEST-36 (ligne ajoutée non détectée).
- [ ] Définir une détection fiable des changements du contenu des feuilles et des vues placées ; ne pas supposer que le seul `VersionGuid` de la feuille suffit.
- [ ] Réévaluer les livrables manquants, renommés et les réglages d'export modifiés.
- [ ] Réintroduire, si retenus, le réglage, son héritage, la prévisualisation filtrée et la publication simple/multiple.
- [ ] Rejouer TEST-34 à TEST-43 et TEST-45 à TEST-56 dans Revit 2025.4, PDF/DWG séparés et combinés.

### Étape 08 — Dynamique avancé

#### Architecture et modèle métier isolés

- [x] Définir le modèle `DynamicRule` / `DynamicRuleGroup` / `DynamicRuleDefinition`.
- [x] Définir le contrat de résolution `DynamicRuleResolver` → `DynamicResolution`.
- [x] Préparer les diagnostics et exclusions explicites.
- [x] Ajouter les tests unitaires hors Revit du moteur de règles.
- [x] Documenter l'architecture isolée dans `docs/15_Export_Stage08_Dynamique.md`.
- [x] Maintenir l'architecture isolée hors du workflow de publication Stage 01–07.
- [x] Ajouter la persistance des snapshots de résolution dynamique.
- [x] Ajouter le pont `DynamicResolution` → `PublicationItem` existants.
- [x] Ajouter le modèle complet `DynamicPublicationSet`.
- [x] Ajouter sérialisation, versionnement, validation et migration.
- [x] Ajouter le gestionnaire CRUD hors Revit.
- [x] Ajouter la persistance JSON complète par projet.
- [x] Ajouter le cycle de vie création / lecture / mise à jour / duplication / suppression.
- [x] Ajouter les tests hors Revit du store et du cycle de vie.

#### Fonctionnalités futures à réévaluer après sortie V1

- [ ] Règles combinées dans l'interface.
- [ ] Prévisualisation de résolution dans WPF.
- [ ] Détection des nouveaux éléments.
- [ ] Diagnostic des éléments retirés.
- [ ] Exclusions explicites persistantes dans le carnet dynamique via l'interface.
- [ ] Lecture des paramètres Revit et construction des entrées normalisées.
- [ ] Intégration au workflow Stage 07 sans second moteur PDF/DWG.
- [ ] Intégration au bouton `Publier`.

## Étape suivante après validation Revit

La priorité est de finaliser les tests et corrections de la V1, puis de la sortir. Le dynamique avancé et le retour éventuel de « modifiés uniquement » seront réévalués ensuite pour la V2. Les tests isolés devront être exécutés au raccordement, puis complétés par une validation réelle dans Revit.

## Étape 09 — Extensibilité

- [ ] Vues publiables.
- [ ] IFC.
- [ ] Autres formats.
- [ ] Automatisations complémentaires.

## Phase 3 — Calculs des pièces

- [x] Formaliser le modèle métier du regroupement et de la somme.
- [x] Ajouter le moteur métier pur indépendant de Revit/WPF.
- [x] Migrer la collecte de toutes les pièces du projet et le filtre métier optionnel par paramètre.
- [x] Finaliser l'identité/validation des paramètres et la gestion des unités.
- [x] Implémenter l'écriture contrôlée et le workflow transactionnel.
- [x] Ajouter la persistance Outils TAA et la migration des anciens réglages.
- [x] Ajouter l'interface WPF et le rapport.
- [x] Raccorder le bouton pyRevit.
- [x] Exécuter la CI hors Revit : 71 tests réussis.
- [x] Valider la campagne `docs/18_Calculs_Pieces_Tests_Revit.md` dans Revit 2025.4 / pyRevit 5.x.
- [x] Revalider le correctif visuel final (icône + fenêtre compacte) et autoriser la fusion dans `main`.

## Phase 4 — Plans de vente

**Statut : V1.1 fichiers liés validée le 20 octobre 2026 — intégrée par la PR #28 et livrée dans Outils TAA v1.3.0.**
Spécification de référence : `docs/20_Plans_de_Vente.md`.

### Conception

- [x] Analyser fonctionnellement un plugin Plans de vente existant comme référence de workflow, sans réutilisation de code propriétaire.
- [x] Définir le besoin métier TAA : pièces de la maquette principale, 1 ou 2 vues, plan de repérage, nomenclatures intérieure/extérieure, légende et cartouche.
- [x] Définir le principe du **Modèle de plan de vente** configurable.
- [x] Définir la règle des deux cotations principales par pièce sur dimensions intérieures finies.
- [x] Définir la sélection du type d'étiquette et des gabarits de vues.
- [x] Valider le périmètre final de la V1.

### Développement V1

- [x] Créer le bundle `PlansDeVente` et son architecture UI / services / métier.
- [x] Collecter et regrouper les pièces par paramètre logement.
- [x] Filtrer les logements par paramètre texte.
- [x] Générer une vue logement mono-niveau depuis une feuille modèle.
- [x] Générer un logement multi-niveaux soit sur une feuille par niveau, soit sur une feuille unique à deux vues selon le modèle.
- [x] Appliquer les gabarits et l'échelle issus des vues modèles.
- [x] Implémenter le crop automatique.
- [x] Générer les étiquettes de pièces avec placement contrôlé.
- [x] Générer les cotations principales par pièce.
- [x] Dupliquer, filtrer et placer toutes les nomenclatures présentes sur la feuille modèle.
- [x] Générer le plan de repérage.
- [x] Assembler la feuille à partir du modèle.
- [x] Renseigner les paramètres de cartouche : logement, bâtiment, étage et typologie.
- [x] Renseigner les surfaces habitables et annexes sur l'ensemble du logement multi-niveaux.
- [x] Implémenter le nommage et le contrôle des collisions.
- [x] Ajouter l'aperçu réel de la feuille modèle.
- [x] Ajouter le rapport de création détaillé.
- [x] Ajouter les zones explicites de placement des vues principales dessinées directement sur la feuille modèle.
- [x] Ajouter une fenêtre de progression par jalons réels pendant la création.
- [x] Harmoniser la palette des icônes Calculs / Export / Plans de vente.
- [x] Appliquer le Design System Outils TAA.
- [x] Valider les workflows principaux dans Revit 2025.4 : mono-vue, duplex une feuille par niveau, duplex deux vues sur une feuille, génération par lot.
- [x] Recette finale réussie sur `release/plans-de-vente-v1` le 16 octobre 2026, confirmée par l’utilisateur (ouverture, mono-niveau, multi-niveaux, lot, progression, Export, Calculs et icônes).
- [x] Intégration finale de `release/plans-de-vente-v1` dans `main` par la PR #26.
- [x] Livraison de Plans de vente V1 avec [Outils TAA v1.2.0](https://github.com/midka33/Outils-TAA/releases/tag/v1.2.0).

Ces deux derniers jalons correspondent à la fusion et à la publication de cette
préparation de release ; l’état GitHub de la PR et de la release fait foi.

### Plans de vente V1.1 — pièces des fichiers Revit liés

**Statut : livrée dans Outils TAA v1.3.0 le 20 octobre 2026 — PR #28 fusionnée, recette utilisateur Revit 2025.4 validée.**

Objectif : lancer Plans de vente depuis un fichier hôte / SITE contenant les
feuilles et cartouches, en analysant les pièces des fichiers Revit liés directs.

- [x] Ajouter l'option **Inclure les pièces des fichiers Revit liés**.
- [x] Conserver le comportement document actif lorsque l'option est décochée.
- [x] Analyser les pièces du document actif et des liens Revit chargés directs.
- [x] Ignorer proprement les liens déchargés et signaler les sources en erreur.
- [x] Afficher la **Source** du logement dans le tableau de portée.
- [x] Utiliser une identité interne robuste **Source + N° logement**.
- [x] Transformer les coordonnées liées vers SITE pour crop et repérage.
- [x] Créer les étiquettes de pièces liées avec `LinkElementId`.
- [x] Créer les cotations automatiques avec les références natives des liens.
- [x] Adapter les nomenclatures natives et les filtres fichier / instance.
- [x] Lire bâtiment / étage / typologie et conserver les surfaces multi-niveaux.
- [x] Créer automatiquement les niveaux SITE manquants à l'altitude transformée.
- [x] Créer une vue plan source SITE lorsque le niveau automatique n'en possède pas.
- [x] Garder l'identifiant technique du lien hors des noms visibles.
- [x] Demander un libellé utilisateur uniquement lorsqu'un numéro logement est réellement en doublon entre plusieurs sources.
- [x] Réutiliser les légendes de la feuille modèle sans dupliquer la vue Legend.
- [x] Ajouter les tests unitaires / contrats nécessaires.
- [x] Valider un workflow réel `SITE.rvt` + bâtiments liés + génération dans SITE avec Revit 2025.4.

**Condition connue acceptée pour la release :** les types d'étiquette de pièce
et de cote doivent exister dans le fichier hôte SITE. Des annotations visibles
uniquement à travers une vue liée ne sont pas utilisées pour déduire ces types.

Recette finale : `docs/release/Preparation_Plans_de_Vente_V1.1_Liens.md`.

### Hors périmètre V1 / suite

- [ ] Mise à jour durable des plans déjà générés : reportée après la V1.
- [ ] Optimisations supplémentaires de performance sur les grands lots.
- [ ] Extension éventuelle à plus de deux vues principales sur une même feuille.


## Phase 4 bis — Règle des 1/6 : surfaces des baies

**Statut au 22 octobre 2026 :** diagnostic V0.1 intégré à la branche, tests unitaires ajoutés ; validation Revit réelle à effectuer. Branche de travail : `feature/calculs-regle-1-6-baies`. **Non livré et non validé dans Revit.**

- [x] Définir le périmètre initial : logements individuels et collectifs, comparaison surfaces des baies / SHAB.
- [x] Préparer un prototype V0.1 indépendant en ZIP.
- [x] Créer la branche de développement et documenter le périmètre dans le README principal.
- [x] Intégrer le diagnostic V0.1 au dépôt (bouton, WPF, export CSV, moteur isolé, thème TAA).
- [ ] Vérifier précisément les modalités réglementaires (niveau bâtiment ou logement, exceptions et méthode de mesure en tableau) avant validation des verdicts.
- [ ] Fiabiliser SHAB, identification des logements et analyse des sources Revit directes et liées.
- [x] Analyser les exports réels du 22 octobre 2026 et intégrer le filtre FEN-EXT / PORFEN-EXT activé par défaut, avec signalement des cas atypiques.
- [ ] Identifier les baies éligibles et traiter les doublons, portes vitrées, murs-rideaux et ouvertures non renseignées.
- [ ] Séparer valeurs mesurées, estimées et inconnues ; produire un diagnostic prudent, non assimilé à une attestation réglementaire.
- [x] Ajouter les tests unitaires du moteur de diagnostic, la CI et la documentation.
- [ ] Exécuter et vérifier les workflows GitHub Actions sur la branche / PR.
- [x] Corriger le premier blocage du diagnostic WPF (`System.Data` non chargé), enregistrer BUG-CALCULS-007 et ajouter quatre tests unitaires simulant l'assembly.
- [x] Corriger BUG-CALCULS-008 : accès `Name` des familles/types et ajouter des tests anti-régression.
- [x] Valider sur capture Revit 2025.4 le filtre hôte `FEN-EXT` / `PORFEN-EXT` : **416 occurrences / 18 types / 0 alerte**, grille et classifications visibles.
- [x] Ajouter deux exclusions indépendantes, activées par défaut : lanterneaux et familles/types `MRX`, avec export des éléments exclus et exclusion permanente du futur calcul.
- [x] Contrôler les 4 CSV du 22 octobre 2026 à 17 h 43 : **396 occurrences, 14 types, 11 lanterneaux et 9 MRX exclus, 0 alerte**, sans chevauchement ni écart de quantités.
- [x] Documenter la réservation du coffre tunnel (hauteur brute +30 cm sur le type 270×218) ; marquer ces cotes comme **à vérifier** avant usage réglementaire, sans assimilation de la réservation au tableau.
- [x] Valider la convention de paramètres TAA sur captures (type 270×200) : `Hauteur brute = Hauteur + Volet roulant_Dim`, `Largeur brute = Largeur + 2×Tapees_Ep` ; privilégier `Largeur×Hauteur` pour les surfaces diagnostiques.
- [x] Comparer les CSV avant/après choix des dimensions nominales dans Revit : 396 identifiants conservés, 153 portes-fenêtres passées en `NOMINALE`, surface indicative réduite de **1 131,9948 à 1 047,5910 m²** (−84,4038 m²), 0 alerte.
- [ ] Examiner dans Revit les familles `FEN-EXT-GEN-1V_ITI.rfa` et `PORFEN-EXT-GEN-2V_1F_ITI_VR tunnel.rfa` pour déterminer les dimensions réellement mesurées en tableau.
- [ ] Vérifier l'export CSV filtré, les liens Revit et les cas de familles réelles atypiques ; contrôler ensuite les surfaces en tableau.
- [ ] Valider les parcours réels sous Revit 2025.4 / pyRevit 5.x avant toute fusion dans `main`.

## Phase 5 — Industrialisation

- [ ] Ajouter tests automatisés hors Revit lorsque possible.
- [ ] Ajouter tests d'intégration Revit.
- [ ] Ajouter validation de structure du dépôt.
- [ ] Documenter les procédures de release.

### Export — après stabilisation V1

- Étudier l'export PDF en arrière-plan : suivi des tâches Revit, annulation, rapport
  différé et livraison/renommage sécurisés après achèvement. La case reste désactivée
  dans la V1 synchrone ; ne pas l'activer uniquement via SetExportInBackground(True).
