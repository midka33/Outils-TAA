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
- [x] TEST-14 validé par l'utilisateur le 2026-09-29 dans Revit 2025.4 : profils, PDF combinés/séparés, noms et contenu des fichiers (dont `PC 09*`), code `7bb533c`. Voir `docs/17_Export_Preparation_TEST14.md`.
- [ ] Recontrôler TEST-04 et un déplacement multiple après suppression des doublons.
- [ ] Consolider la surcouche `stage07` après validation réelle.

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

**Statut : spécification / conception.**  
Spécification de référence : `docs/20_Plans_de_Vente.md`.

### Conception

- [x] Analyser fonctionnellement un plugin Plans de vente existant comme référence de workflow, sans réutilisation de code propriétaire.
- [x] Définir le besoin métier TAA : pièces de la maquette principale, 1 ou 2 vues, plan de repérage, nomenclatures intérieure/extérieure, légende et cartouche.
- [x] Définir le principe du **Modèle de plan de vente** configurable.
- [x] Définir la règle des deux cotations principales par pièce sur dimensions intérieures finies.
- [x] Définir la sélection du type d'étiquette et des gabarits de vues.
- [x] Définir l'objectif de mise à jour durable des plans déjà générés.
- [ ] Valider le périmètre final de la V1 avant création du bundle pyRevit.

### Prototypes techniques prioritaires

- [ ] PROTO-PDV-01 — Vues dépendantes : crop, annotations, cotations, gabarit et mise à jour dans Revit 2025.4. **Sous-prototype vue dépendante + crop rectangulaire validé dans Revit 2025.4 le 2026-10-01. Correctif suivant implémenté : crop calculé dans le repère écran de la vue (RightDirection / UpDirection) afin d'éliminer l'inclinaison due aux axes globaux ; validation Revit requise.**
- [ ] PROTO-PDV-02 — Cotations : deux dimensions principales, faces finies, suppression des petits décrochements.
- [ ] PROTO-PDV-03 — Crop logement : union/simplification des contours sur cas simples et complexes. **Union géométrique des pièces et offset extérieur implémentés ; validation Revit 2025.4 requise.**

### Développement V1

- [x] Créer le bundle `PlansDeVente` et son architecture UI / modèles / services.
- [x] Collecter et regrouper les pièces par paramètre logement.
- [x] Étape 01 validée dans Revit 2025.4 par l'utilisateur le 2026-10-01 : bouton, fenêtre, paramètres texte, analyse des logements, comptages et niveaux.
- [ ] Implémenter le modèle de configuration de plan de vente.
- [ ] Générer une ou deux vues par logement selon la configuration.
- [ ] Appliquer les gabarits sélectionnés.
- [ ] Implémenter le crop automatique.
- [ ] Générer les étiquettes avec placement contrôlé.
- [ ] Générer les deux cotations principales par pièce.
- [ ] Dupliquer, filtrer et placer les nomenclatures intérieure et extérieure.
- [ ] Générer le plan de repérage.
- [ ] Assembler la feuille à partir du modèle.
- [ ] Implémenter le mapping des paramètres de feuille.
- [ ] Implémenter nommage et contrôle des collisions.
- [ ] Ajouter prévisualisation et rapport.
- [ ] Implémenter l'identification durable et la mise à jour des plans existants.
- [ ] Appliquer le Design System Outils TAA.
- [ ] Créer la campagne de tests Revit 2025.4.

## Phase 5 — Industrialisation

- [ ] Ajouter tests automatisés hors Revit lorsque possible.
- [ ] Ajouter tests d'intégration Revit.
- [ ] Ajouter validation de structure du dépôt.
- [ ] Documenter les procédures de release.

### Export — après stabilisation V1

- Étudier l'export PDF en arrière-plan : suivi des tâches Revit, annulation, rapport
  différé et livraison/renommage sécurisés après achèvement. La case reste désactivée
  dans la V1 synchrone ; ne pas l'activer uniquement via SetExportInBackground(True).
