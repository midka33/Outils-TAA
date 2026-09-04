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
- Première infrastructure d'héritage des réglages `Profil → Dossier → Carnet` avec `SettingsResolver`.
- Persistance des réglages de publication au niveau des dossiers.
- Interface d'héritage affichant les réglages hérités du dossier et les réglages définis au niveau du carnet.
- Action `Revenir à l'héritage du dossier` pour supprimer les surcharges du carnet.
- Service de prévisualisation de publication sans export Revit.
- Fenêtre de confirmation listant les fichiers attendus, noms finaux, chemins, formats et modes.
- Détection préalable des feuilles introuvables, feuilles non imprimables, doublons, variables inconnues et collisions avec des fichiers existants.
- Service de publication multiple `PublicationBatchService` pour agréger l'exécution de plusieurs carnets.
- Publication d'un dossier avec prise en compte récursive des sous-dossiers.
- Prévisualisation globale avant publication d'un dossier, avec agrégation des livrables et collisions inter-carnets.
- Tests unitaires de l'orchestrateur de publication multiple.

### Changed
- `Export` est désormais le nom fonctionnel officiel de l'ancien module PublisherAI.
- `Calculs des pièces` est désormais le nom fonctionnel officiel de l'ancien module RoomCalculator.
- Normalisation de la structure cible du dépôt pour pyRevit.
- `PublicationSet` porte désormais son identifiant, son état de persistance et ses options de sortie.
- Les services d'export isolent maintenant les appels directs à l'API Revit de l'orchestration métier.
- Le bouton de publication ouvre désormais un rapport détaillé au lieu d'afficher un simple message de fin.
- Les profils agissent uniquement sur les réglages techniques PDF/DWG ; la destination et le nommage restent propres au carnet afin de ne pas écraser les réglages persistants du carnet.
- Les réglages de publication acceptent désormais `None` comme état « hériter », tout en conservant la lecture des carnets existants.
- Le schéma de persistance des carnets/dossiers passe à la version 3 pour conserver les réglages de dossier.
- Les modifications d'un réglage de carnet ne transforment plus les autres réglages hérités en surcharges locales.
- La publication et la prévisualisation utilisent désormais les réglages effectivement résolus par `SettingsResolver`.
- Le bouton `Publier` passe désormais obligatoirement par un aperçu et une confirmation avant de lancer l'export réel.
- La sélection d'un dossier active désormais l'action `Publier le dossier` lorsque le dossier contient au moins un carnet publiable.
- Une publication de dossier produit un rapport unique couvrant tous les carnets exécutés.
- L'aperçu fusionne désormais les destinations multiples au lieu d'en masquer une derrière une destination unique.

## [0.1.0] - 2026-07-21

### Added
- Initialisation du repository.
- Création des documents fondateurs.
