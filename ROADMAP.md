# Roadmap Outils TAA

## Phase 1 — Socle architectural

- [x] Formaliser l'architecture du dépôt.
- [x] Définir les frontières entre UI, métier, Revit et infrastructure commune.
- [ ] Créer `OutilsTAA.extension/`.
- [ ] Créer `lib/common/` et ses services fondamentaux.
- [ ] Normaliser les noms des documents de documentation.
- [ ] Mettre en place la structure pyRevit de base.

## Phase 2 — Export

- [ ] Implémenter les modèles de publication.
- [ ] Implémenter la création de carnets par paramètre.
- [ ] Implémenter les carnets manuels persistants et temporaires.
- [ ] Implémenter les profils, hiérarchies, héritages et scopes V2.
- [ ] Implémenter PDF combiné/séparé.
- [ ] Implémenter DWG combiné/séparé.
- [ ] Implémenter le moteur de nommage dynamique.
- [ ] Implémenter validation, journal, historique et état depuis dernière publication.

## Phase 3 — Calculs des pièces

- [ ] Formaliser le modèle métier.
- [ ] Migrer les fonctionnalités existantes dans l'architecture commune.
- [ ] Ajouter UI, services et tests.

## Phase 4 — Industrialisation

- [ ] Ajouter tests automatisés hors Revit lorsque possible.
- [ ] Ajouter tests d'intégration Revit.
- [ ] Ajouter validation de structure du dépôt.
- [ ] Documenter les procédures de release.
