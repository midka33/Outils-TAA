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

### Étape 07 — Historique et « modifiés uniquement »

- [x] Socle de persistance de l'historique des publications.
- [x] Classification NEW / MODIFIED / UNCHANGED / UNKNOWN.
- [x] Détection basée sur `VersionGuid` Revit lorsque disponible.
- [x] Sélection conservative des éléments à republier lorsque `MODIFIED_ONLY` est actif.
- [x] Persistance du réglage `modified_only` dans les paramètres.
- [x] Intégrer le contrôle `MODIFIED_ONLY` dans l'interface Export.
- [x] Intégrer le filtrage dans la prévisualisation.
- [x] Intégrer le filtrage dans la publication simple et multiple.
- [x] Enregistrer automatiquement l'état après publication réussie.
- [x] Ajouter l'affichage « jamais publié / modifié / inchangé » dans la prévisualisation et le rapport via le résumé d'état.
- [ ] Valider le comportement réel dans Revit 2025.4.

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

#### Fonctionnalités à raccorder après validation Stage 07

- [ ] Règles combinées dans l'interface.
- [ ] Prévisualisation de résolution dans WPF.
- [ ] Détection des nouveaux éléments.
- [ ] Diagnostic des éléments retirés.
- [ ] Exclusions explicites persistantes dans le carnet dynamique via l'interface.
- [ ] Lecture des paramètres Revit et construction des entrées normalisées.
- [ ] Intégration au workflow Stage 07 sans second moteur PDF/DWG.
- [ ] Intégration au bouton `Publier`.

## Étape suivante après validation Revit

La prochaine étape fonctionnelle reste **Étape 08 — Dynamique avancé**. Le socle métier, la prévisualisation, le modèle, la sérialisation et la persistance hors Revit sont préparés. Les `pytest` correspondants doivent être exécutés réellement lors du raccordement avant toute validation de Stage. Le raccordement au workflow réel ne doit intervenir qu'après la validation Revit 2025.4 de l'Étape 07 et la correction/capitalisation des éventuels bugs issus de la campagne de tests.

## Étape 09 — Extensibilité

- [ ] Vues publiables.
- [ ] IFC.
- [ ] Autres formats.
- [ ] Automatisations complémentaires.

## Phase 3 — Calculs des pièces

- [ ] Formaliser le modèle métier.
- [ ] Migrer les fonctionnalités existantes dans l'architecture commune.
- [ ] Ajouter UI, services et tests.

## Phase 4 — Industrialisation

- [ ] Ajouter tests automatisés hors Revit lorsque possible.
- [ ] Ajouter tests d'intégration Revit.
- [ ] Ajouter validation de structure du dépôt.
- [ ] Documenter les procédures de release.
