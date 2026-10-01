# Changelog

Toutes les évolutions importantes du projet seront documentées ici.

Le format suit les principes de *Keep a Changelog*.

## [Unreleased]

### Changed
- Charte TAA appliquée aux cinq fenêtres Export : thème partagé, orange pastel,
  Segoe UI, pictogrammes vectoriels, tableaux et champs adaptables. Validation WPF/Revit restante.
- Publication de dossier : arborescence reproduite sur disque, sous-dossier par carnet
  pour les formats séparés et chemins partagés entre aperçu et export.
- Export V1 : retrait de « Publier uniquement les mises en page nouvelles ou modifiées ».
  Anciennes valeurs neutralisées, contrôle et handlers retirés. Retour éventuel reporté
  en V2 après finalisation/sortie V1 ; campagne de tests et feuille de route actualisées.

### Fixed
- Sous-dossiers : bouton de retour à l’héritage du parent, origine des réglages
  nommée et libellé lisible dans la liste des dossiers.
- Héritage des sous-dossiers : résolution récursive et affichage des valeurs effectives.
- Mode séparé : dossier au nom du carnet également en publication directe carnet/feuille.
- TEST-15/16 : collection DWG explicitement typée `List[ElementId]` pour IronPython.
- TEST-22/23 : aperçu principal raccordé au service de nommage existant, avec
  contexte de feuille/dossier et erreurs visibles. Validation Revit à rejouer.
- PDF séparés : numéro de feuille contenant `*` ou un autre caractère interdit
  dans un nom Windows ; rapprochement contrôlé des fichiers natifs, sans
  modifier les numéros dans Revit. Validation réelle TEST-14 à poursuivre.
- Rapport Export : erreurs globales complètes et copiables, suppression du faux
  message de succès sur les lignes en échec, chemins et carnets issus des résultats.
  Diagnostic TEST-14 amélioré ; cause native de l'absence de PDF encore à déterminer.

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
- Réorganisation des carnets par glisser-déposer dans l'arborescence Export.
- Sélection multiple `Ctrl` / `Maj` des carnets persistants pour les déplacements groupés.
- Socle `PublicationHistoryService` pour persister le dernier état publié d'un carnet.
- Classification hors Revit `NEW` / `MODIFIED` / `UNCHANGED` / `UNKNOWN` pour préparer `MODIFIED_ONLY`.
- Persistance du réglage `modified_only` dans les paramètres de publication.
- Contrôle WPF `MODIFIED_ONLY` dans l'interface Export.
- Filtrage du périmètre avant prévisualisation et avant publication, en réutilisant le moteur PDF/DWG existant.
- Enregistrement de l'historique après publication réussie, y compris lors d'une publication multiple partiellement réussie.
- Affichage des états de publication dans la prévisualisation et résumé des états dans les avertissements du rapport.
- Tests unitaires hors Revit de conservation de l'historique lors d'une publication partielle.
- Architecture isolée Stage 08 pour les règles dynamiques : `DynamicRule`, `DynamicRuleGroup`, `DynamicRuleDefinition`, `DynamicRuleResolver`, `DynamicResolution` et diagnostics.
- Tests unitaires hors Revit du moteur de résolution des règles dynamiques.
- Documentation `docs/15_Export_Stage08_Dynamique.md` décrivant le contrat et les limites de l'architecture préparatoire.
- Persistance hors Revit des snapshots de résolution dynamique par projet et carnet.
- Pont `DynamicPublicationAdapter` transformant une résolution en sélection des `PublicationItem` existants, sans second moteur de publication.
- Tests unitaires hors Revit du pont dynamique vers `PublicationItem`.
- Moteur de prévisualisation dynamique hors Revit avec états de changement, éléments retirés, éléments publiables et diagnostics.
- Modèle complet hors Revit de `DynamicPublicationSet`, couvrant les types manuel/dynamique, règles, exclusions, paramètres, validation et snapshot.
- Sérialisation, désérialisation, versionnement et migration du modèle de carnet dynamique.
- `DynamicPublicationSetManager` pour créer, mettre à jour, dupliquer, supprimer, charger et sérialiser les carnets dynamiques.
- Tests unitaires hors Revit du modèle et du gestionnaire de carnets dynamiques.
- `DynamicPublicationSetStore` pour persister les configurations dynamiques par projet dans un JSON versionné, sans objets Revit.
- `DynamicPublicationSetLifecycle` pour encadrer création, chargement, mise à jour, duplication et suppression avec validation métier.
- Tests unitaires hors Revit de la persistance et du cycle de vie dynamique.

### Changed
- `Export` est désormais le nom fonctionnel officiel de l'ancien module PublisherAI.
- `Calculs des pièces` est désormais le nom fonctionnel officiel de l'ancien module RoomCalculator.
- Normalisation de la structure cible du dépôt pour pyRevit.
- `PublicationSet` porte désormais son identifiant, son état de persistance et ses options de sortie.
- Les services d'export isolent maintenant les appels directs à l'API Revit de l'orchestration métier.
- Le bouton de publication ouvre désormais un rapport détaillé au lieu d'afficher un simple message de fin.
- Les profils agissent uniquement sur les réglages techniques PDF/DWG ; la destination et le nommage restent propres au carnet afin de ne pas écraser les réglages persistants du carnet.
- Les réglages de publication acceptent désormais `None` comme état « hériter », tout en conservant la lecture des carnets existants.
- Le schéma de persistance des carnets/dossiers passe à la version 4 afin de conserver l'ordre manuel des carnets.
- Les modifications d'un réglage de carnet ne transforment plus les autres réglages hérités en surcharges locales.
- La publication et la prévisualisation utilisent désormais les réglages effectivement résolus par `SettingsResolver`.
- Le bouton `Publier` passe désormais obligatoirement par un aperçu et une confirmation avant de lancer l'export réel.
- La sélection d'un dossier active désormais l'action `Publier le dossier` lorsque le dossier contient au moins un carnet publiable.
- Une publication de dossier produit un rapport unique couvrant tous les carnets exécutés.
- L'aperçu fusionne désormais les destinations multiples au lieu d'en masquer une derrière une destination unique.
- Lors de la création de carnets depuis un dossier sélectionné, le `folder_id` du dossier courant est désormais appliqué avant persistance.
- Les carnets persistants peuvent être déplacés dans un autre dossier et réordonnés sans modifier leurs réglages de publication.
- Le drag-and-drop utilise désormais un `DataObject` WPF explicite et une opération repository dédiée au déplacement de plusieurs carnets en conservant leur ordre.
- Le réglage `modified_only` est désormais totalement intégré à l'interface, à la prévisualisation, à la publication simple et multiple et à l'historique ; la validation réelle dans Revit 2025.4 reste obligatoire.
- Stage 08 reste volontairement isolé : son résolveur ne dépend ni de Revit, ni de WPF, ni du moteur PDF/DWG, et n'est pas appelé par le workflow de publication actuel.

## [0.1.0] - 2026-07-21

### Added
- Initialisation du repository.

## Correctifs préparatoires TEST-14 — 2026-09-28

- Nommage réel des PDF séparés aligné sur le modèle TAA, avec contrôle des fichiers,
  collisions bloquantes et restauration sur échec de livraison.
- Transmission des réglages hérités sur une copie de publication.
- Suppression de deux abonnements redondants au glisser-déposer.
- Tests et documentation synchronisés ; validation Revit 2025.4 encore requise.

## 2026-10-01 — Compléments de la fenêtre Export

- Menu Dossier des réglages retiré ; déplacement conservé dans l'arborescence.
- Suppression multiple des carnets/dossiers avec confirmation et protections.
- Pictogrammes PDF/DWG hérités, résumé de périmètre et icône Export du ruban.
- Qualité PDF persistée/héritée (300 DPI par défaut), profils et deux modes raccordés.
- 173 tests hors Revit ; validation WPF/Revit UI-07 à UI-12 restante.
