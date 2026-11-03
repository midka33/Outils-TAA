# Giration des véhicules — Spécification fonctionnelle V1

**Statut :** planifié — aucune implémentation ni validation dans Revit à ce stade.  
**Décision de cadrage :** 2026-11-03.  
**Compatibilité cible :** Autodesk Revit 2025.4 / pyRevit 5.x (IronPython, WPF).  
**Issue de suivi :** [#40 — Giration des véhicules](https://github.com/midka33/Outils-TAA/issues/40).

## 1. Finalité

Créer dans **Outils TAA** un outil de **giration manuelle** comparable à la partie simulation de trajectoires d'Autodesk Vehicle Tracking, **avec une interface plus intuitive et un rendu graphique aussi complet sur les plans Revit**.

La capture Vehicle Tracking transmise par l'utilisateur le 03/11/2026 est la **référence visuelle de cadrage** : véhicule(s) à différents instants, trajectoires parallèles correspondant aux roues et à la carrosserie, enveloppes balayées, points de contrôle et repères de progression.

Le module doit rester **natif à l'écosystème pyRevit de la suite**, sans application externe ni dépendance à Dynamo. Il ne s'agit **pas** d'un outil de tracé de simples arcs ou polylignes.

## 2. Responsabilités

- **Utilisateur :** sélectionne librement le véhicule approprié au projet et à son contexte réglementaire, décide du point de départ et **pilote manuellement le chemin voulu** dans Revit.
- **Moteur de giration :** applique les caractéristiques géométriques et cinématiques du véhicule choisi, empêche ou signale une courbure impossible, calcule les trajectoires des roues/essieux et les enveloppes balayées.
- **Aucune sélection automatique du véhicule selon le bâtiment** et aucune déclaration automatique de conformité réglementaire.

Le moteur doit distinguer **les dimensions et capacités mécaniques d'un véhicule** des **prescriptions d'une voie** (largeur, surlargeur, rayon intérieur minimal, hauteur, pente, etc.). Les dernières ne peuvent pas être utilisées comme substitution au rayon de braquage mécanique.

## 3. Parcours utilisateur cible

1. Dans une vue en plan Revit, ouvrir le bouton **Giration** du ruban Outils TAA.
2. Choisir un véhicule de la bibliothèque ; voir ses dimensions et la référence de ses données.
3. Définir la position initiale et le cap du véhicule.
4. **Piloter/tracer manuellement** sa progression à la souris, avec aperçu de la silhouette, des roues et de l'enveloppe, et courbure limitée par les données du véhicule. Choisir marche avant ou arrière ; annuler le dernier tronçon.
5. Valider le tracé et retrouver dans Revit tous les graphiques de giration paramétrés.
6. Rouvrir une giration pour revoir ses caractéristiques, ajuster son parcours et régénérer ses représentations.

L'ergonomie visée est celle de Vehicle Tracking ; **l'aperçu continu sous le curseur est un point de faisabilité à démontrer**, pas une capacité pyRevit déjà validée. Un mode de tracé par points ne pourra être adopté comme remplacement définitif qu'après arbitrage utilisateur explicite.

## 4. Données des véhicules et traçabilité

Une fiche véhicule doit contenir, selon disponibilité :
- catégorie, désignation, source du document et date/version ;
- longueur, largeur, empattement, voie(s), porte-à-faux avant et arrière ;
- positions des essieux/roues, paramètres utiles de direction, angle de braquage ou rayon minimal **avec sa convention de mesure** ;
- particularités de géométrie/cinématique et sens de déplacement pris en charge.

**Sources possibles :** documentation officielle SDIS 33 et autres SDIS, fiches constructeurs, carrossiers, autres références techniques vérifiables. Une valeur provenant d'une prescription de voirie ne doit pas devenir automatiquement une caractéristique du véhicule.

**Règles de qualité :** aucun véhicule présenté comme validé si les données déterminantes de la simulation manquent ; signaler les approximations, hypothèses et valeurs non vérifiées. Prévoir des véhicules personnalisables, avec traçabilité de la source et des modifications.

## 5. Graphiques exigés sur le plan

La restitution doit pouvoir montrer séparément :
- silhouette à l'échelle au départ, à l'arrivée et aux positions intermédiaires ;
- trajectoire de référence (point de pilotage à définir explicitement) ;
- courbes de déplacement des roues avant et arrière et/ou des essieux ;
- **enveloppes balayées** intérieure et extérieure, incluant les déports de carrosserie et porte-à-faux ;
- repères de changement de tronçon, points de contrôle et numérotation ;
- sens de circulation, marche avant/arrière, rayons et informations de giration pertinents.

Des **préréglages d'affichage** (complet, présentation) doivent agir sur la visibilité sans effacer les données sous-jacentes. Styles de lignes Revit dédiés, unités cohérentes, lisibilité sur feuille et export PDF/DWG compatibles avec les modules existants.

## 6. Architecture envisagée (à valider)

- Intégration au panneau technique `Giration.panel` du ruban `OutilsTAA.tab`.
- Interface WPF légère conforme à la charte Outils TAA ; commandes de tracé/annulation/marche avant-arrière et visibilité des couches.
- **Moteur de cinématique et calcul d'enveloppes isolé** de WPF et de l'API Revit, avec tests reproductibles hors Revit.
- Adaptateur Revit dédié pour l'acquisition des points/événements, la prévisualisation et l'écriture des éléments.
- Persistance par trajectoire : identité stable, véhicule, version de ses paramètres, points/segments, sens et options d'affichage. Ne pas sérialiser naïvement des `ElementId` Revit non stables.
- Journalisation, gestion des transactions, annulation sûre, performances et indicateur de progression dès lors qu'un traitement peut dépasser 20 secondes, conformément à `AI_INSTRUCTIONS.md`.

**Risque majeur :** Revit n'expose pas la même interaction libre au curseur qu'AutoCAD. Les options compatibles pyRevit 5.x doivent être démontrées sur Revit 2025.4 **avant de promettre une commande de suivi continu identique**. La solution finale doit rester en pyRevit.

## 7. Phases et critères de recette

### P0 — Prototype d'interaction (bloquant)
- [ ] Vérifier acquisition du cap, interaction à la souris et aperçu fluide dans une vue en plan.
- [ ] Tester annulation, changement de direction et stabilité de Revit.
- [ ] Documenter la solution effective et ses limites sur Revit 2025.4 / pyRevit 5.x.

### P1 — Cinématique
- [ ] Définir le point de référence, les unités, les conventions du rayon minimal et le modèle de braquage.
- [ ] Calculer les trajectoires admissibles, marches avant/arrière et transitions entre segments.
- [ ] Tester des virages et contre-virages connus, la limite de braquage et les déports.

### P2 — Rendu Vehicle Tracking
- [ ] Restituer roues, silhouettes, enveloppes intérieure/extérieure, positions, repères et annotations.
- [ ] Produire des éléments persistants visibles sur feuilles, imprimables et exportables.
- [ ] Comparer des cas de test et le rendu au niveau d'information de la capture de référence.

### P3 — Utilisation en production
- [ ] Bibliothèque de véhicules sourcés et édition de fiches personnalisées.
- [ ] Enregistrement, réouverture et modification d'une giration.
- [ ] Préréglages d'affichage, tests de robustesse et recette utilisateur Revit 2025.4.

## 8. Hors périmètre V1

- Recherche automatique d'itinéraire ou de manœuvre (l'utilisateur pilote).
- Choix automatique du véhicule selon la catégorie de bâtiment.
- Attestation/contrôle automatique de conformité réglementaire.
- Détection automatique des collisions avec la maquette, analyse 3D des rampes.
- Modules spécialisés de conception de giratoires ou d'aménagement de parkings.

## 9. Validation

Aucune tâche de développement n'est déclarée réalisée par ce document. **Avant d'annoncer une giration fiable**, confronter les enveloppes à des cas connus (dont références externes lorsque disponibles), vérifier la conservation des données après fermeture/réouverture et exécuter la recette dans **Revit 2025.4 / pyRevit 5.x**.

La documentation Autodesk Vehicle Tracking sert de **référence de comportement et de rendu**, pas de source de code à reproduire. Ne pas reprendre d'éléments propriétaires.
