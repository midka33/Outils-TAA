# Roadmap Outils TAA

## État d'ensemble au 3 novembre 2026

**Version de release préparée : Outils TAA v1.4.0 — Export**, après la fusion de la PR #39 dans `main`. Les six campagnes de recette **EXPORT-01 à EXPORT-06** sont confirmées dans Revit 2025.4. Dernier jalon : publier le tag et les livrables de v1.4.0 après réussite des contrôles sur le SHA de release. Consulter `docs/release/Preparation_Export_v1.4.0.md` et `docs/release/Notes_v1.4.0.md`.

- **Export :** validation fonctionnelle achevée ; publication de la version v1.4.0 en préparation.
- **Calculs des pièces :** stable, comportement métier inchangé depuis v1.3.0.
- **Plans de vente :** V1.1 fichiers liés stable, livrée depuis v1.3.0 ; pas de nouvelle fonction dans v1.4.0.
- **Cotations, Étiquettes, Légendes, Giration :** développer sur leurs branches ou dans leurs jalons dédiés ; **aucun travail non fusionné n'est inclus dans v1.4.0**.

Les cases historiques restées ouvertes ci-dessous ne sont pas des échecs de la recette v1.4.0 : elles correspondent à des campagnes anciennes ou à des tests ciblés non exécutés isolément.

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
- [x] Finaliser le socle Export V1 (versions v1.1.0 puis v1.4.0) ; réévaluer séparément les fonctionnalités V2.

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


## Modules futurs — Production documentaire

### Carnets de menuiseries extérieures

**Statut : préparation.**

Objectif : préparer un module dédié à la production automatisée des carnets de
mise en page des menuiseries extérieures.

- [ ] Définir le périmètre métier et les données sources.
- [ ] Définir le principe de regroupement des menuiseries et la structure des carnets.
- [ ] Définir les vues, annotations, nomenclatures et informations à placer sur les feuilles.
- [ ] Définir le modèle de feuille / cartouche et les règles de nommage.
- [ ] Préparer le workflow de génération, mise à jour et contrôle avant développement.

### Plans de repérage

**Statut : préparation.**

Objectif : préparer un module de génération automatisée des plans de repérage et
de leurs mises en page.

- [ ] Définir les usages de repérage à couvrir et les éléments concernés.
- [ ] Définir les règles de génération des vues et du graphisme de repérage.
- [ ] Définir les annotations, légendes, nomenclatures et informations associées.
- [ ] Définir le modèle de mise en page et les règles de nommage.
- [ ] Préparer le workflow de génération, mise à jour et contrôle avant développement.

## Module futur — Giration des véhicules

**Statut : planifié (cadrage validé le 2026-11-03) — non développé.**  
**Spécification :** [`docs/25_Giration_Vehicules.md`](docs/25_Giration_Vehicules.md). **Suivi :** [issue #40](https://github.com/midka33/Outils-TAA/issues/40).

**Objectif :** retrouver dans Revit 2025.4 via pyRevit 5.x le **tracé manuel de giration** d'Autodesk Vehicle Tracking et son niveau d'information graphique sur plan, avec une interface WPF plus intuitive.

**Décisions :**
- L'utilisateur choisit le véhicule adapté à son projet, sans sélection automatique en fonction du type de bâtiment.
- Il dessine/pilote librement le parcours ; le plugin impose les contraintes de giration du véhicule sélectionné.
- Véhicules définis à partir de données géométriques et cinématiques sourcées (SDIS 33, autres SDIS, constructeurs), **sans confondre exigences de voirie et rayon de braquage mécanique**.
- Même famille d'informations graphiques que Vehicle Tracking : silhouettes successives, trajectoires de roues, enveloppes intérieure/extérieure, rayons, sens et repères de contrôle ; graphiques utilisables en plan/feuille et export PDF/DWG.
- **Technologie imposée :** pyRevit 5.x / IronPython, moteur métier Python indépendant de WPF et de l'API Revit ; pas de complément autonome C# et pas de Dynamo.

### Jalons V1
- [ ] **P0 — Faisabilité :** valider dans Revit 2025.4 un tracé manuel et un aperçu dynamique à la souris fluides via pyRevit ; documenter les limites réelles de l'API (jalon bloquant).
- [ ] **P1 — Cinématique :** moteur de braquage, limitation du rayon, transition entre segments, marche avant/arrière, trajectoires des roues et tests géométriques hors Revit.
- [ ] **P2 — Représentation :** positions du véhicule, lignes de parcours, enveloppes balayées et repères comparables à la référence Vehicle Tracking ; production de géométrie Revit exportable.
- [ ] **P3 — Production :** bibliothèque de véhicules sourcés, interface WPF, enregistrement et modification des trajectoires, options d'affichage et validation utilisateur en conditions réelles.

**Hors V1 :** calcul d'itinéraire automatique, sélection réglementaire du véhicule, certification de conformité, contrôle automatique des collisions, analyse 3D des rampes.

**Aucun code livré et aucun test de faisabilité Revit encore exécuté.** Ce module est ajouté au backlog sans décaler automatiquement les jalons déjà engagés d'Export, Calculs et Plans de vente.

## Phase 5 — Industrialisation

- [ ] Ajouter tests automatisés hors Revit lorsque possible.
- [ ] Ajouter tests d'intégration Revit.
- [ ] Ajouter validation de structure du dépôt.
- [x] Documenter la release v1.4.0 et son pipeline de packaging, contrôle des trois modules et publication par SHA testé.

### Export — après stabilisation V1

- Étudier l'export PDF en arrière-plan : suivi des tâches Revit, annulation, rapport
  différé et livraison/renommage sécurisés après achèvement. La case reste désactivée
  dans la V1 synchrone ; ne pas l'activer uniquement via SetExportInBackground(True).


### Export — ergonomie de l'ajout des mises en page (décision du 2026-10-22, réalisée dans la PR #39)

**Statut : développée, intégrée et validée (PR #39, recettes EXPORT-01 à 06).** Référence : `docs/09_Export.md` et `docs/release/Tutoriel_Export_v1.4.0.md`.

- [x] Auditer les XAML, handlers et services existants de « Ajouter / gerer… » et du glisser-deposer.
- [x] Integrer un panneau gauche escamotable, redimensionnable et a etat memorise, sans supprimer les panneaux publication et parametres.
- [x] Afficher les feuilles du document Revit actif, recherche instantanee et filtres, indicateurs d'utilisation et regroupements utiles.
- [x] Selection Ctrl/Maj/Ctrl+A persistante entre recherches ; ajout par bouton, double-clic, menu contextuel et glisser-deposer multiple vers les dossiers.
- [x] Reutiliser le comportement de survol, ouverture automatique, scroll et insertion de l'arborescence existante ; eviter les doublons dans un dossier, autoriser la reutilisation inter-dossiers.
- [x] Preserver le modele a dossiers uniques, les parametres PDF/DWG, le stockage, les profils et les publications existantes.
- [x] Ajouter tests automatisés et recette fonctionnelle Revit 2025.4 / pyRevit 5.x : interactions, persistance et non-régression (EXPORT-01 à 06). La matrice complète DPI/écrans reste un contrôle ciblé éventuel.


### Export — explorateur escamotable (validé dans Revit 2025.4 le 2026-11-03)

La branche `feature/export-explorateur-feuilles` a été intégrée à `main` par la **PR #39** le 2026-11-03. La fenêtre finale, les filtres, regroupements, ajouts, déplacements, PDF/DWG et la persistance sont validés par l'utilisateur.

- [x] Integrer le panneau escamotable, redimensionnable et les preferences de largeur/visibilite.
- [x] Recherche, filtre des non ajoutees, regroupements repliables et indicateurs d'utilisation.
- [x] Selection multiple et ajout par bouton, double-clic, menu et drag-and-drop distinct du deplacement interne.
- [x] Ajouter une operation de persistance atomique preservant les sources et evitant les doublons par dossier.
- [x] Ecrire les tests unitaires de l'ajout dans un dossier.
- [x] Exécuter les tests : **375 tests Export** et contrat ruban réussis sur la tête finale de la PR #39 (2026-11-03).
- [x] Valider la fenêtre et les interactions utilisateur dans Revit 2025.4 / pyRevit 5.x (EXPORT-02 à 06).
- [x] Rejouer la recette fonctionnelle PDF/DWG multi-dossiers, suppression, drag-and-drop, héritage et persistance (EXPORT-01 à 06).
- [x] Fusionner uniquement après validation utilisateur : PR #39 fusionnée sur `main` (SHA `5a37be83e3d5893156399b242b838f4a9805ef58`).

### Export — recette publication par sous-dossier (2026-11-03)

- [x] Écarter les dossiers de publication vides du périmètre récursif PDF/DWG sans les supprimer de l'arborescence ; 5 PDF combinés + 16 DWG validés par test automatisé (BUG-EXPORT-056).
- [x] Confirmer dans Revit 2025.4 l'aperçu puis l'export réel d'`A2000 Plan des façades` : 5 PDF combinés + 16 DWG (EXPORT-01).



### Export — renommage des dossiers et terminologie (2026-11-03)

- [x] Ajouter un bouton Renommer visible et un menu contextuel attaché à chaque dossier.
- [x] Permettre le renommage sans changer l'ID, les enfants, les feuilles, les paramètres et la position.
- [x] Uniformiser les libellés visibles de l'aperçu, du rapport, de la progression et du résumé autour de « Dossier ».
- [x] Ajouter `{nom_dossier}` comme alias de `{carnet}` et conserver la lecture des anciens modèles.
- [x] Couvrir les contrats d'interface et l'alias de nommage par tests automatisés.
- [x] Recette Revit : renommage, conservation du contenu et des réglages, persistance après réouverture (EXPORT-02).
- [ ] Contrôles isolés encore utiles : raccourci F2, clic droit et ancienne variable de nommage `{carnet}` dans un projet existant (couverts par tests de contrat, pas confirmés individuellement par l'utilisateur).



### Export — organisation indépendante des dossiers et formats (2026-11-03)

- [x] Séparer « Créer ce dossier dans la sortie » et « Créer un sous-dossier par format (PDF et DWG) » dans l'interface.
- [x] Ajouter `separate_format_subfolders` dans le modèle, l'héritage et les profils personnalisés.
- [x] Conserver les destinations des anciens dossiers et projets qui n'ont pas encore le nouveau réglage.
- [x] Appliquer exactement les mêmes chemins dans l'aperçu et les exporteurs PDF/DWG.
- [x] Couvrir quatre combinaisons de dossiers, PDF combiné/séparé, héritage, profils et compatibilité JSON par tests hors Revit.
- [x] Recette Revit 2025.4 : indépendance des options, export réel PDF/DWG et héritage des réglages confirmés (EXPORT-01 et EXPORT-05).
- [ ] Procès-verbal manuel distinct des quatre combinaisons de dossiers (les quatre chemins sont couverts par la suite automatisée).

### Release Outils TAA v1.4.0 — checklist (2026-11-03)

- [x] Recette Revit Export EXPORT-01 à EXPORT-06 validée.
- [x] PR #39 intégrée dans `main` sans fusionner les branches parallèles.
- [x] Notes, tutoriels, changelog, index documentaire et procédures de test actualisés.
- [x] Préparer ZIP utilisateur, installateur CMD sans admin et manifeste SHA-256 dans le workflow de release.
- [ ] Contrôles CI de release sur le SHA exact de `main` et ZIP vérifié.
- [ ] Tag Git et release GitHub `v1.4.0` publiés avec actifs vérifiés.
- [ ] Recette d'installation de l'installateur v1.4.0 sur Windows.
