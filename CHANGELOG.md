# Changelog

Toutes les évolutions importantes du projet seront documentées ici.

Le format suit les principes de *Keep a Changelog*.

## [Unreleased]

### Added
- Architecture explicite du repository.
- Contrat d'architecture entre UI, métier, API Revit et infrastructure commune.
- Structure initiale des modules `Export` et `Calculs`.
- Première infrastructure `lib/common`.
- Documentation dédiée à **Calculs des pièces**.
- Documentation de contribution, sécurité et roadmap.
- Moteur de création des carnets `Export` avec les modes `PARAMETER`, `MANUAL` et `TEMPORARY`.
- Identifiant stable des carnets et déduplication des éléments par `UniqueId`.
- Persistance JSON des carnets manuels.
- Tests unitaires du moteur de création et de persistance des carnets.
- Service PDF natif Revit avec publication combinée ou séparée.
- Service DWG natif Revit avec publication séparée ou combinée via `MergedViews`.
- Orchestrateur de publication avec validation des feuilles, contrôle `CanBePrinted` et rapport synthétique.
- Fenêtre WPF dédiée au rapport de publication avec une ligne par fichier produit.
- Détection des fichiers PDF/DWG produits pour alimenter le rapport de publication.
- Tests unitaires de l'orchestrateur de publication.
- Service de profils de publication persistants avec profils intégrés et profils personnalisés.
- Interface Export permettant d'appliquer, enregistrer et supprimer des profils de publication.

### Changed
- `Export` est désormais le nom fonctionnel officiel de l'ancien module PublisherAI.
- `Calculs des pièces` est désormais le nom fonctionnel officiel de l'ancien module RoomCalculator.
- Normalisation de la structure cible du dépôt pour pyRevit.
- `PublicationSet` porte désormais son identifiant, son état de persistance et ses options de sortie.
- Les services d'export isolent maintenant les appels directs à l'API Revit de l'orchestration métier.
- Le bouton de publication ouvre désormais un rapport détaillé au lieu d'afficher un simple message de fin.
- Les profils agissent uniquement sur les réglages techniques PDF/DWG ; la destination et le nommage restent propres au carnet afin de ne pas écraser les réglages persistants du carnet.

## [0.1.0] - 2026-07-21

### Added
- Initialisation du repository.
- Création des documents fondateurs.
