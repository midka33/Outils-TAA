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
- [ ] Intégrer le contrôle `MODIFIED_ONLY` dans l'interface Export.
- [ ] Intégrer le filtrage dans la prévisualisation.
- [ ] Intégrer le filtrage dans la publication simple et multiple.
- [ ] Enregistrer automatiquement l'état après publication réussie.
- [ ] Ajouter l'affichage « jamais publié / modifié / inchangé » dans l'interface et le rapport.
- [ ] Valider le comportement réel dans Revit 2025.4.

### Étape 08 — Dynamique avancé

- [ ] Règles combinées.
- [ ] Prévisualisation de résolution.
- [ ] Détection des nouveaux éléments.
- [ ] Diagnostic des éléments retirés.
- [ ] Exclusions explicites.

### Étape 09 — Extensibilité

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
