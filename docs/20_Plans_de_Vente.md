# Outils TAA — Plans de vente

## Spécification fonctionnelle et technique

**Version :** 1.9  
**Statut :** Développement — prototypes géométriques  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x  
**Interface :** WPF — Design System Outils TAA  
**Langue :** Français  
**Date :** 2026-10-01

---

# 1. Objet

Le module **Plans de vente** doit automatiser la production, la mise à jour et l'assemblage des plans de vente à partir de la maquette Revit.

L'objectif n'est pas de créer un générateur opaque. Le module doit appliquer des règles de présentation choisies par l'agence, tout en laissant à l'utilisateur le contrôle sur les gabarits, annotations, cotations, nomenclatures et éléments de mise en page.

Le module doit s'intégrer à **Outils TAA** et respecter :

- Revit 2025.4 ;
- pyRevit 5.x ;
- les standards de développement du repository ;
- le Design System défini dans `docs/04_UI_Guidelines.md` ;
- les règles de séparation UI / métier / services Revit ;
- les principes de persistance et d'identification durable déjà retenus dans Outils TAA.

---

# 2. Sources de conception

La conception du module repose sur deux sources principales.

## 2.1 Besoin métier TAA

Le besoin défini pour Outils TAA est le suivant :

- les pièces sont, pour la V1, dans la **maquette principale** ;
- un logement est identifié par une valeur commune portée par les pièces ;
- une feuille de plan de vente comporte **une ou deux vues de plan** suivant le logement ;
- une vue de **plan de repérage** est créée ;
- une nomenclature des **pièces intérieures** est créée ;
- une nomenclature des **pièces / surfaces extérieures** est créée ;
- une légende peut être placée sur la feuille ou être intégrée au cartouche ;
- le module crée les vues et les nomenclatures nécessaires ;
- lorsque plusieurs vues de logement sont issues du même niveau, l'utilisation de **vues dépendantes** doit être étudiée et privilégiée lorsque cela est fiable ;
- l'utilisateur choisit le **gabarit de vue** à appliquer pour chaque type de vue créé ;
- l'utilisateur choisit le **type de cote** ;
- l'objectif est d'obtenir **deux dimensions principales par pièce** ;
- les dimensions sont des **dimensions intérieures finies** ;
- les dimensions générales sont prioritaires ;
- les petits décrochements ne doivent pas générer des cotes parasites ;
- l'utilisateur choisit le **type d'étiquette de pièce** ;
- l'étiquette est placée au centre de la pièce autant que possible ;
- l'étiquette ne doit pas entrer en conflit avec les cotations.

## 2.2 Analyse fonctionnelle d'un plugin tiers

Un installateur du plugin **E&A Plans de vente** a été analysé comme référence fonctionnelle.

Cette analyse a permis d'identifier plusieurs principes utiles :

- regroupement des pièces par logement ;
- création de vues dédiées ;
- calcul du contour d'un logement ;
- application d'un cadrage ;
- duplication et filtrage de nomenclatures ;
- création d'un plan de repérage ;
- assemblage d'une feuille à partir d'un modèle ;
- copie de paramètres de feuille ;
- ajustement possible de l'échelle ;
- gestion d'annotations et de cotations.

Cette référence est utilisée **uniquement pour comprendre les principes fonctionnels**.

Aucun code propriétaire, aucune DLL, aucune ressource protégée et aucun système de licence du plugin tiers ne doivent être copiés ou intégrés dans Outils TAA.

Le module Outils TAA doit être une implémentation indépendante.

---

# 3. Principe directeur

Le module doit être construit autour d'un **Modèle de plan de vente**.

Ce modèle définit la règle de production à appliquer aux logements.

Exemple :

```text
Modèle de plan de vente
│
├── Paramètre identifiant le logement
├── Feuille modèle
├── Type de cartouche
│
├── Vue principale
│   ├── Gabarit
│   ├── Échelle
│   └── Emplacement sur feuille
│
├── Deuxième vue éventuelle
│   ├── Gabarit
│   ├── Échelle
│   └── Emplacement sur feuille
│
├── Plan de repérage
│   ├── Gabarit
│   ├── style graphique
│   └── emplacement
│
├── Nomenclature intérieure
├── Nomenclature extérieure
├── Type d'étiquette de pièce
├── Type de cote
├── Légende(s)
├── Règles de nommage
└── Mapping des paramètres de feuille
```

Une fois ce modèle configuré, l'utilisateur doit pouvoir générer plusieurs logements avec une présentation homogène.

---

# 4. Parcours utilisateur cible

Le parcours principal doit rester court.

```text
Ouvrir Plans de vente
        ↓
Choisir / charger un modèle de plan de vente
        ↓
Choisir le paramètre identifiant les logements
        ↓
Prévisualiser les logements détectés
        ↓
Choisir les logements à générer / mettre à jour
        ↓
Vérifier les vues, gabarits, cotes et nomenclatures
        ↓
Prévisualiser les opérations
        ↓
Générer / mettre à jour
        ↓
Rapport de résultat
```

La fenêtre principale doit suivre le Design System Outils TAA et privilégier une interface dense, claire et adaptée à un écran Full HD.

---

# 5. Identification des logements

## 5.1 Source de vérité

La V1 ne doit pas essayer de deviner automatiquement quels locaux constituent un logement.

La **source de vérité** est un paramètre Revit texte présent sur les pièces.

Exemple :

```text
Paramètre : Numéro logement

Séjour       → A101
Cuisine      → A101
Chambre 01   → A101
Salle de bain→ A101
```

Toutes les pièces ayant la même valeur appartiennent au même logement.

## 5.2 V1

Pour la V1 :

- les pièces sont issues de la maquette principale ;
- les pièces sans valeur d'identification sont ignorées et signalées ;
- les doublons ou valeurs incohérentes sont signalés dans la prévisualisation.

## 5.3 Évolution future

Le support complet des pièces provenant de fichiers Revit liés pourra être étudié ultérieurement.

Il ne doit pas bloquer la V1.

---

# 6. Analyse d'un logement

Pour chaque logement, le module construit un modèle métier contenant au minimum :

```text
Housing
├── key
├── rooms
├── levels
├── bounding geometry
├── interior rooms
├── exterior rooms / annexes
├── generated views
├── generated schedules
└── generated sheet
```

Le modèle doit être indépendant de l'interface WPF.

---

# 7. Création des vues

## 7.1 Nombre de vues

Un plan de vente doit pouvoir contenir :

- **une vue principale** ;
- ou **deux vues principales** lorsque le logement nécessite de représenter deux niveaux ou deux parties distinctes.

Le moteur ne doit donc pas être limité à une seule vue par logement.

## 7.2 Vue principale et vues dépendantes

Lorsque plusieurs logements utilisent le même niveau, le module doit étudier l'utilisation de vues dépendantes afin de conserver une logique Revit propre.

Principe visé :

```text
Vue principale du niveau
│
├── Vue dépendante — logement A101
├── Vue dépendante — logement A102
└── Vue dépendante — logement A103
```

Ce comportement doit être validé par prototype dans Revit 2025.4 avant d'être considéré comme architecture définitive.

Le prototype doit vérifier :

- cadrage indépendant ;
- annotations ;
- étiquettes ;
- cotations ;
- gabarits ;
- comportement lors de la mise à jour.

## 7.3 Gabarits

L'utilisateur doit pouvoir choisir explicitement un gabarit pour chaque type de vue généré.

Exemple :

```text
Vue principale        [ PDV - Plan logement ▼ ]
Deuxième vue          [ PDV - Plan logement ▼ ]
Plan de repérage      [ PDV - Repérage ▼ ]
```

Aucun nom de gabarit ne doit être codé en dur.

---

# 8. Contour et cadrage automatique

Le module doit calculer l'emprise générale du logement à partir des pièces qui le composent.

Pipeline cible :

```text
Pièces
   ↓
Contours / BoundarySegments
   ↓
Normalisation géométrique
   ↓
Union des contours
   ↓
Suppression des micro-segments
   ↓
Simplification
   ↓
Ajout d'une marge
   ↓
CropShape de la vue
```

Le service responsable doit rester indépendant de la couche UI.

Nom de service suggéré :

```text
CropGeometryService
```

La géométrie doit être suffisamment robuste pour gérer :

- pièces non rectangulaires ;
- décrochements ;
- séparateurs de pièces ;
- gaines ;
- logements composés de plusieurs pièces ;
- contours comprenant des arcs lorsque Revit le permet.

---

# 9. Cotations automatiques

La cotation automatique est un point critique du module.

## 9.1 Règle métier

Pour chaque pièce, l'objectif est de créer **deux cotes principales** :

- longueur intérieure finie ;
- largeur intérieure finie.

Ces deux cotes doivent représenter les dimensions générales de la pièce.

## 9.2 Priorité aux dimensions générales

Le moteur ne doit pas coter mécaniquement tous les segments du contour.

Il doit privilégier :

- les axes principaux de la pièce ;
- les faces finies opposées ;
- les longueurs les plus représentatives.

Les petits décrochements, niches ou retours doivent être ignorés lorsqu'ils ne décrivent pas la dimension générale.

## 9.3 Pipeline cible

```text
Contour fini de la pièce
        ↓
Analyse des segments
        ↓
Filtrage des petits décrochements
        ↓
Détermination des directions dominantes
        ↓
Recherche des deux dimensions principales
        ↓
Recherche des références Revit fiables
        ↓
Création des deux cotes
```

## 9.4 Type de cote

Le type de cote n'est jamais imposé par le code.

L'utilisateur choisit :

```text
Type de cote
[ PDV - Cotes intérieures ▼ ]
```

## 9.5 Prototype obligatoire

Avant le développement complet, tester :

- pièce rectangulaire ;
- pièce en L ;
- pièce avec petit décrochement ;
- murs composés ;
- cloison ;
- murs non orthogonaux ;
- références sur faces finies.

Le prototype doit prouver que les dimensions créées sont associatives et stables.

---

# 10. Étiquettes de pièces

L'utilisateur choisit le type d'étiquette.

Le moteur doit :

1. calculer un point représentatif de la pièce ;
2. vérifier que ce point est réellement intérieur à la pièce ;
3. placer l'étiquette ;
4. vérifier les collisions avec les zones de cotation ;
5. rechercher une position alternative si nécessaire.

Pipeline :

```text
Centre géométrique
       ↓
Point intérieur ?
       ├── Oui → tester collision
       └── Non → chercher un point intérieur alternatif
                          ↓
                   tester collision
                          ↓
                     placer tag
```

L'étiquette doit rester dans la pièce autant que possible.

---

# 11. Nomenclatures

Chaque plan de vente doit pouvoir comporter au minimum :

- une nomenclature des pièces intérieures ;
- une nomenclature des pièces ou surfaces extérieures.

## 11.1 Principe

Les nomenclatures peuvent être basées sur des nomenclatures modèles configurées par l'agence.

Le module :

1. récupère la nomenclature modèle ;
2. la duplique ;
3. identifie le filtre lié au paramètre logement ;
4. applique la valeur du logement ;
5. place la nomenclature sur la feuille.

Exemple :

```text
Nomenclature modèle
Filtre : Numéro logement = <VALEUR>

        ↓ duplication

PDV_A101_Interieur
Filtre : Numéro logement = A101
```

## 11.2 Ancrage

Le placement doit permettre un point d'ancrage stable lorsque la hauteur de la nomenclature varie.

Options envisagées :

- haut ;
- centre ;
- bas.

---

# 12. Plan de repérage

Chaque plan de vente doit comporter un plan de repérage.

Le plan de repérage doit permettre d'identifier immédiatement la position du logement dans le bâtiment.

Principe :

```text
Vue de repérage
        +
Contour du logement
        ↓
Zone remplie / surbrillance
        ↓
Placement sur la feuille
```

Le style graphique ou le type de zone remplie doit être configurable.

Le gabarit du plan de repérage doit également être sélectionnable.

---

# 13. Feuille modèle et assemblage

La feuille modèle sert de référence de composition.

Elle peut définir :

- type de cartouche ;
- emplacements des vues ;
- emplacements des nomenclatures ;
- emplacement du plan de repérage ;
- légendes ;
- annotations fixes ;
- images éventuelles ;
- paramètres de feuille à reprendre.

Le module doit éviter de dépendre uniquement d'une détection implicite fragile.

Le **Modèle de plan de vente** doit mémoriser explicitement le rôle des éléments de la feuille.

---

# 14. Légendes

Une légende peut être :

- placée directement sur la feuille ;
- ou déjà intégrée au cartouche.

Le modèle doit pouvoir gérer les deux cas.

Une légende déjà intégrée au cartouche ne doit évidemment pas être dupliquée.

---

# 15. Échelle et optimisation de la vue

Deux stratégies doivent être possibles :

```text
Échelle
● Imposée                       [1:50 ▼]
○ Ajuster automatiquement si nécessaire
```

L'ajustement automatique doit rester une option.

Il ne doit jamais changer silencieusement l'échelle définie par l'utilisateur sans que cette règle soit activée.

Le moteur d'optimisation doit comparer :

- l'emprise de la vue ;
- la zone disponible sur la feuille ;
- les échelles Revit autorisées.

---

# 16. Paramètres du cartouche et de la feuille

Le module doit utiliser un système de mapping configurable.

Exemple :

| Paramètre feuille | Source |
|---|---|
| Numéro logement | Paramètre logement |
| Typologie | Paramètre de pièce / valeur calculée |
| Niveau | Niveau du logement |
| Bâtiment | Paramètre projet |
| Phase | Paramètre projet |

Les noms de paramètres métier ne doivent pas être codés en dur lorsque cela peut être configuré.

---

# 17. Nommage

Le module doit permettre de définir des règles de nommage pour :

- vues ;
- nomenclatures ;
- feuilles.

Exemple :

```text
Vue        : PDV_{logement}_{niveau}
Feuille    : PDV_{logement}
Nomenclature intérieure : PDV_{logement}_INT
Nomenclature extérieure : PDV_{logement}_EXT
```

Les collisions doivent être détectées avant création.

---

# 18. Mise à jour des plans existants

Le module ne doit pas être limité à une logique « supprimer puis recréer ».

Une génération doit pouvoir être identifiée durablement.

Principe :

```text
Logement A101
      ↓
Éléments Plans de vente existants ?
      │
      ├── Non → Créer
      │
      └── Oui → Mettre à jour
```

Les éléments générés doivent pouvoir être reliés à une identité métier stable, par exemple :

```text
GeneratedBy = OutilsTAA.PlansVente
HousingKey = A101
TemplateId = ...
Role = MainView / LocationView / InteriorSchedule / Sheet
```

L'implémentation technique pourra s'appuyer sur une persistance projet adaptée, par exemple Extensible Storage ou un mécanisme équivalent compatible avec les standards Outils TAA.

Ne pas persister uniquement des `ElementId` si une référence plus durable est nécessaire.

---

# 19. Prévisualisation avant génération

Avant toute création ou mise à jour importante, afficher une prévisualisation.

Exemple :

```text
12 logements sélectionnés

À créer
  8 feuilles
  16 vues
  16 nomenclatures

À mettre à jour
  4 feuilles

Avertissements
  A207 — aucune pièce extérieure
  A304 — deuxième niveau détecté
```

L'utilisateur doit comprendre ce qui va être créé ou modifié avant validation.

---

# 20. Transactions et sécurité

Le module doit éviter une transaction globale incontrôlable.

Le contrôleur doit séparer clairement :

- analyse ;
- prévalidation ;
- génération ;
- rapport.

Les transactions Revit doivent être structurées pour permettre :

- rollback en cas d'erreur bloquante ;
- rapport précis du logement en erreur ;
- absence de modèle partiellement corrompu.

Une erreur sur un logement ne doit pas nécessairement empêcher le diagnostic des autres logements.

---

# 21. Architecture logicielle cible

Architecture proposée :

```text
OutilsTAA.extension/
└── OutilsTAA.tab/
    └── PlansDeVente.panel/
        └── PlansDeVente.pushbutton/
            ├── script.py
            ├── bundle.yaml
            ├── icon.png
            │
            ├── models/
            │   ├── housing.py
            │   ├── plan_template.py
            │   ├── generation_plan.py
            │   └── generation_result.py
            │
            ├── services/
            │   ├── housing_collector.py
            │   ├── template_analyzer.py
            │   ├── crop_geometry_service.py
            │   ├── view_generator.py
            │   ├── tagging_service.py
            │   ├── dimension_service.py
            │   ├── schedule_service.py
            │   ├── location_plan_service.py
            │   ├── sheet_service.py
            │   ├── persistence_service.py
            │   └── generation_controller.py
            │
            └── ui/
                ├── plans_vente.xaml
                └── plans_vente_window.py
```

Cette structure pourra évoluer pendant les prototypes.

Le principe obligatoire est la séparation entre :

- UI ;
- modèle métier ;
- logique géométrique ;
- opérations Revit ;
- persistance.

---

# 22. Interface utilisateur

L'interface doit utiliser le design system officiel :

- `docs/04_UI_Guidelines.md` ;
- `docs/assets/ui/UI_Design_System_TAA.jpg` ;
- `docs/assets/ui/UI_Suite_Outils_TAA_Orange.jpg`.

Principes :

- thème clair ;
- orange pastel TAA comme accent ;
- Segoe UI ;
- interface compacte ;
- sections lisibles ;
- options avancées repliables ;
- une action principale clairement identifiable ;
- prévisualisation avant génération ;
- aucun grand panneau vide ;
- pas de logique métier importante dans le code-behind.

Exemple d'organisation :

```text
┌───────────────────────────────────────────────────────┐
│ TAA   Plans de vente                                  │
│       Génération et mise à jour                       │
├───────────────────────┬───────────────────────────────┤
│ Logements détectés    │ Modèle de plan de vente      │
│                       │                               │
│ A101                  │ Paramètre logement            │
│ A102                  │ Gabarits                      │
│ A103                  │ Étiquettes                    │
│ ...                   │ Cotations                     │
│                       │ Nomenclatures                 │
│                       │ Repérage                      │
├───────────────────────┴───────────────────────────────┤
│ Résumé                 [Aperçu] [Générer / Mettre à jour] │
└───────────────────────────────────────────────────────┘
```

---

# 23. Fonctions à ne pas reproduire du plugin étudié

Outils TAA ne doit pas reprendre :

- authentification distante ;
- système de crédits ;
- facturation ;
- licence serveur ;
- détection automatique complexe de logements lorsque le paramètre logement existe ;
- dépendances techniques du plugin tiers ;
- code ou ressources propriétaires.

---

# 24. Prototypes techniques obligatoires

Avant le développement complet, trois prototypes doivent être réalisés.

## Prototype A — Vues dépendantes

Valider dans Revit 2025.4 :

- création d'une vue dépendante ;
- crop propre au logement ;
- gabarit ;
- étiquettes ;
- cotations ;
- placement sur feuille ;
- mise à jour.

## Prototype B — Cotations intérieures finies

Tester au minimum :

- pièce rectangulaire ;
- pièce en L ;
- petit décrochement ;
- murs composés ;
- cloisons ;
- murs non orthogonaux.

Critère :

> obtenir deux cotes principales fiables et associatives.

## Prototype C — Crop logement

Tester :

- logement simple ;
- logement avec plusieurs pièces ;
- logement concave ;
- logement comprenant plusieurs niveaux ;
- contours avec arcs ou géométries irrégulières.

---

# 25. Découpage de développement proposé

## Étape 01 — Socle

- créer le bundle pyRevit ;
- créer les modèles métier ;
- créer l'interface minimale ;
- collecter les pièces ;
- regrouper par paramètre logement.

## Étape 02 — Modèle de plan de vente

- sélection de la feuille modèle ;
- sélection des gabarits ;
- choix des types d'étiquette et de cote ;
- choix des nomenclatures ;
- persistance de la configuration.

## Étape 03 — Vues et crop

- génération des vues ;
- validation des vues dépendantes ;
- crop automatique ;
- échelle.

## Étape 04 — Nomenclatures et repérage

- nomenclature intérieure ;
- nomenclature extérieure ;
- plan de repérage ;
- placement sur feuille.

## Étape 05 — Étiquettes

- placement automatique ;
- recherche de point intérieur ;
- anti-collision de base.

## Étape 06 — Cotations

- deux cotes principales par pièce ;
- faces finies ;
- filtrage des décrochements ;
- type de cote configurable.

## Étape 07 — Assemblage feuille

- cartouche ;
- vues ;
- nomenclatures ;
- repérage ;
- légendes ;
- paramètres ;
- nommage.

## Étape 08 — Mise à jour

- identification durable ;
- détection des éléments existants ;
- création / mise à jour ;
- rapport des changements.

## Étape 09 — Stabilisation

- tests Revit ;
- tests multi-logements ;
- erreurs ;
- performance ;
- documentation ;
- non-régression.

---

# 26. Critères de validation V1

La V1 sera considérée comme fonctionnelle lorsque les points suivants seront validés dans Revit 2025.4 :

```text
☐ Les logements sont détectés à partir d'un paramètre choisi.

☐ L'utilisateur peut sélectionner plusieurs logements.

☐ Une ou deux vues peuvent être générées selon le logement.

☐ Le gabarit de chaque type de vue est configurable.

☐ Le crop du logement est généré automatiquement.

☐ Les étiquettes sont créées avec le type choisi.

☐ Les étiquettes restent dans la pièce autant que possible.

☐ Deux dimensions principales sont générées par pièce.

☐ Les dimensions utilisent les références intérieures finies.

☐ Les petits décrochements ne génèrent pas de cotations parasites.

☐ Une nomenclature intérieure est générée et filtrée par logement.

☐ Une nomenclature extérieure est générée et filtrée par logement.

☐ Un plan de repérage est généré.

☐ Le cartouche et les éléments fixes sont correctement repris.

☐ Les vues et nomenclatures sont correctement placées sur la feuille.

☐ Une légende peut être placée ou laissée dans le cartouche.

☐ Les paramètres de feuille configurés sont renseignés.

☐ Les règles de nommage sont appliquées.

☐ Les collisions de noms sont contrôlées.

☐ Une prévisualisation présente les opérations avant modification.

☐ Un logement déjà généré peut être mis à jour sans recréation aveugle.

☐ Un rapport final distingue succès, avertissements et erreurs.

☐ L'interface respecte le Design System Outils TAA.

☐ Le module reste compatible Revit 2025.4 / pyRevit 5.x.
```

---

# 27. Évolutions possibles après V1

À étudier après stabilisation :

- support complet des pièces de liens Revit ;
- rotation automatique des vues ;
- synchronisation d'une rose des vents ;
- règles avancées d'optimisation de l'échelle ;
- amélioration de l'anti-collision des annotations ;
- recalcul intelligent uniquement des logements modifiés ;
- gestion de plusieurs modèles de plans de vente par projet ;
- publication directe via le module Export Outils TAA.

---

# 28. Règle de développement

Le module Plans de vente doit rester un outil métier Outils TAA et non une copie du plugin analysé.

Les principes à conserver sont :

```text
Modèle configurable
+
Automatisation contrôlée
+
Prévisualisation
+
Génération reproductible
+
Mise à jour fiable
+
Interface cohérente
```

La priorité doit rester la fiabilité des résultats Revit avant l'automatisation maximale.


---

# 29. État du développement

## Étape 01 — Détection des logements

Premier incrément implémenté sur la branche `feature/plans-de-vente-stage01`.

Le module est volontairement **en lecture seule** à ce stade.

Fonctions implémentées :

- bouton pyRevit `Plans de vente` ;
- fenêtre WPF utilisant le thème commun Outils TAA ;
- collecte de toutes les pièces du document actif, indépendamment de la vue ;
- découverte des paramètres texte portés par les pièces ;
- sélection du paramètre identifiant le logement ;
- identité de paramètre basée, lorsque disponible, sur GUID partagé, ForgeTypeId Revit ou identifiant de définition plutôt que sur le seul nom ;
- création de snapshots métier conservant le `UniqueId` Revit des pièces ;
- regroupement pur et testable des pièces par valeur logement ;
- exclusion et comptage des valeurs vides ;
- affichage des logements détectés, du nombre de pièces et des niveaux concernés.

Aucune modification du modèle Revit n'est réalisée pendant cette étape :

- aucune vue créée ;
- aucune feuille créée ;
- aucune nomenclature créée ;
- aucune étiquette créée ;
- aucune cote créée.

Cette séparation permet de valider d'abord la détection et les données métier avant d'introduire des transactions Revit.

## Tests Étape 01

Tests hors Revit préparés et exécutés avant commit :

- regroupement des pièces ;
- normalisation des valeurs logement ;
- comptage des valeurs vides ;
- agrégation des niveaux ;
- validité XML du XAML ;
- présence des handlers WPF ;
- en-tête UTF-8 obligatoire des fichiers Python ;
- titre pyRevit non vide.

Résultat local avant commit : **6 tests réussis**.

La validation du chargement de la fenêtre et de la lecture réelle des paramètres reste à effectuer dans **Revit 2025.4 / pyRevit 5.x**.


## Validation Revit Étape 01

Validation utilisateur réalisée le **2026-10-01** dans **Revit 2025.4 / pyRevit 5.x**.

Résultat : **validé**.

Points confirmés :

- le bouton Plans de vente est visible et se charge correctement ;
- la fenêtre WPF s'ouvre sans erreur ;
- les paramètres texte des pièces sont proposés ;
- le paramètre logement peut être sélectionné ;
- l'analyse regroupe correctement les pièces par logement ;
- le nombre de pièces par logement est cohérent ;
- les niveaux affichés sont cohérents ;
- aucun effet de bord ni modification de la maquette n'a été constaté sur cette étape en lecture seule.

L'Étape 01 peut servir de base stable pour les prototypes suivants.


## Prototype A — Vue dépendante + crop

Implémentation préparée sur la branche `feature/plans-de-vente-proto-views-crop`.

Objectif de ce prototype : vérifier dans Revit 2025.4 qu'une vue principale de plan peut être dupliquée en **vue dépendante**, puis recevoir un crop propre au logement sans casser la relation avec sa vue principale.

### Périmètre actuel

Le prototype :

- fonctionne sur un logement sélectionné ;
- est volontairement limité aux logements présents sur **un seul niveau** ;
- propose uniquement les vues plan principales du même niveau ;
- exclut les gabarits et les vues déjà dépendantes ;
- vérifie que la vue peut être dupliquée avec `ViewDuplicateOption.AsDependent` ;
- crée une vraie vue dépendante dans une transaction Revit ;
- conserve les pièces par `UniqueId` et les résout au moment de l'action ;
- récupère les `BoundarySegments` des pièces du logement ;
- calcule une emprise rectangulaire englobante ;
- ajoute une marge configurable, par défaut **500 mm** ;
- active le crop de la vue dépendante ;
- applique le contour avec `ViewCropRegionShapeManager.SetCropShape` ;
- vérifie après création que `GetPrimaryViewId()` correspond bien à la vue source ;
- crée un nom unique de type `PDV PROTO - <logement> - <niveau>`.

Ce prototype utilise volontairement un **crop rectangulaire**. L'union géométrique détaillée et le crop polygonal suivront uniquement après validation du comportement des vues dépendantes.

### Limites assumées

Ne sont pas encore traités dans ce prototype :

- logements sur plusieurs niveaux ;
- choix d'un gabarit de vue ;
- étiquettes ;
- cotations ;
- annotation crop ;
- plan de repérage ;
- nomenclatures ;
- feuilles ;
- mise à jour d'une vue prototype existante.

Aucun élément existant n'est supprimé.

### Contrôles hors Revit

Les tests préparés pour ce prototype vérifient :

- calcul pur de l'emprise ;
- marge de crop ;
- refus des emprises vides ;
- refus d'une marge négative ;
- parsing Python ;
- encodage UTF-8 IronPython ;
- validité XML du XAML ;
- présence des handlers WPF ;
- utilisation de `ViewDuplicateOption.AsDependent` ;
- utilisation du `UniqueId` des pièces ;
- raccordement à `GetCropRegionShapeManager` et `SetCropShape`.

Exécution locale avant commit : **6 tests réussis**.

### Validation Revit à effectuer

Le prototype n'est pas considéré validé tant que le scénario suivant n'a pas été exécuté dans Revit 2025.4 :

1. analyser les logements ;
2. sélectionner un logement sur un seul niveau ;
3. sélectionner une vue plan principale proposée ;
4. conserver une marge de 500 mm ;
5. lancer **Créer le prototype** ;
6. vérifier qu'une vue `PDV PROTO - ...` est créée ;
7. vérifier dans l'arborescence Revit qu'elle est réellement dépendante de la vue choisie ;
8. vérifier que son crop englobe le logement avec la marge demandée ;
9. modifier le crop de la vue dépendante et confirmer que la vue principale reste intacte ;
10. vérifier qu'une seconde génération produit un nom unique sans écraser la première.

La suite du développement dépend de ce résultat.


### Validation Revit — vue dépendante + crop rectangulaire

Validation utilisateur réalisée le **2026-10-01** dans **Revit 2025.4 / pyRevit 5.x**.

Résultat : **validé pour le principe technique**.

Constats confirmés :

- la vue dépendante est créée correctement ;
- elle est bien rattachée à la vue principale choisie ;
- le cadrage global englobe correctement le logement ;
- la vue principale n'est pas modifiée ;
- la création d'une vue dépendante avec un crop propre au logement est donc considérée comme techniquement viable pour Outils TAA.

Point restant :

- le cadrage apparaît légèrement incliné par rapport à la géométrie principale du logement dans certains cas ;
- le prototype actuel utilise volontairement une emprise rectangulaire simple calculée à partir des contours des pièces ;
- la prochaine itération doit étudier l'orientation dominante du logement / de la vue et préparer un cadrage plus propre et plus proche du contour réel.

Cette validation permet de poursuivre le prototype sans remettre en cause le principe des vues dépendantes.


## Prototype A.2 — Crop aligné au repère de la vue

À la suite de la validation du prototype initial, l'utilisateur a signalé que le cadrage global était correct mais apparaissait **légèrement incliné**.

### Cause identifiée

Le premier prototype calculait l'emprise rectangulaire directement dans les axes globaux du modèle Revit :

```text
Model X / Model Y
```

Or une vue Revit peut présenter le modèle suivant un repère écran différent. L'API expose précisément ce repère par :

- `View.Origin` ;
- `View.RightDirection` ;
- `View.UpDirection`.

Un rectangle aligné sur les axes globaux peut donc apparaître incliné lorsque la vue elle-même n'est pas alignée sur ces axes.

### Correction

Le nouveau calcul :

1. collecte les points des `BoundarySegments` des pièces ;
2. les projette dans le repère 2D de la vue ;
3. calcule l'emprise dans les coordonnées écran `u / v` ;
4. ajoute la marge dans ce même repère ;
5. reconstruit les quatre coins dans les coordonnées monde ;
6. applique ce rectangle à la vue dépendante.

Pipeline :

```text
Contours des pièces
        ↓
Coordonnées monde XYZ
        ↓
Projection dans RightDirection / UpDirection
        ↓
Emprise rectangulaire u/v
        ↓
Marge
        ↓
Retour vers XYZ
        ↓
SetCropShape
```

Le crop reste volontairement rectangulaire à ce stade, mais il est désormais **aligné avec l'écran de la vue source**, et non avec les axes globaux du projet.

### Architecture

Un modèle métier pur `ViewFrame` a été ajouté dans :

```text
OutilsTAA.extension/lib/plans_vente/view_frame.py
```

Il ne dépend pas de Revit et permet de tester :

- projection monde → vue ;
- reconstruction vue → monde ;
- normalisation des axes ;
- validation de l'orthogonalité.

Le service Revit `CropGeometryService` reste responsable de la conversion entre objets `XYZ` Revit et le modèle pur.

### Tests hors Revit

Suite ciblée Plans de vente exécutée avant commit :

```text
16 passed
```

Les tests couvrent notamment :

- regroupement des logements ;
- calcul d'emprise ;
- marges ;
- projection dans un repère tourné ;
- reconstruction dans le modèle ;
- validation des axes ;
- contrats XAML / handlers ;
- présence de `RightDirection` et `UpDirection` ;
- utilisation de `ViewDuplicateOption.AsDependent` ;
- raccordement à `SetCropShape`.

### Validation Revit à effectuer

1. reprendre le même logement et la même vue source que lors du test précédent ;
2. créer un nouveau prototype avec une marge de 500 mm ;
3. vérifier que le cadrage est visuellement horizontal/vertical par rapport à l'écran de la vue ;
4. confirmer que tout le logement reste inclus ;
5. confirmer que la marge reste cohérente ;
6. confirmer que la vue principale n'est toujours pas modifiée.

Cette étape ne modifie pas encore le contour pour suivre précisément la forme du logement. Le crop polygonal éventuel sera étudié séparément après validation du repère de vue.


## Prototype A.3 — Contour logement optimisé

Le prototype passe du rectangle englobant à un **contour réellement dérivé des pièces du logement**.

### Objectif

Réduire les zones vides autour des logements en L, irréguliers ou présentant des retraits, tout en conservant une marge de présentation configurable.

Le crop final reste une seule boucle extérieure compatible avec `ViewCropRegionShapeManager.SetCropShape`.

### Principe géométrique

Les frontières des pièces sont lues avec :

```text
SpatialElementBoundaryLocation.Center
```

Ce choix est volontaire : deux pièces séparées par une même paroi partagent ainsi la même limite centrale, ce qui facilite leur union géométrique.

Pipeline :

```text
Pièces du logement
        ↓
BoundarySegments au centre des séparations
        ↓
Boucle extérieure de chaque pièce
        ↓
Extrusion temporaire en solides Revit
        ↓
BooleanOperationsUtils — Union
        ↓
Face plane correspondant au niveau
        ↓
Plus grande boucle extérieure
        ↓
CurveLoop.CreateViaOffset
        ↓
Marge utilisateur
        ↓
Validation IsCropRegionShapeValid
        ↓
SetCropShape
```

### Gestion des trous

L'union peut contenir plusieurs boucles, par exemple autour d'une gaine ou d'un vide intérieur.

Pour un crop de plan de vente, ces trous ne doivent pas devenir des trous dans le cadrage.

Le service sélectionne donc la **plus grande boucle extérieure** et ignore les boucles intérieures.

### Marge

La marge utilisateur est appliquée sur le contour extérieur avec `CurveLoop.CreateViaOffset`.

Le service teste les deux signes de décalage et retient le contour dont l'aire est supérieure à celle du contour de base. Cela évite de dépendre du sens horaire ou antihoraire de la boucle renvoyée par Revit.

### Sécurité et fallback

Les opérations booléennes et les offsets Revit peuvent échouer sur certaines géométries très complexes ou non contiguës.

Le prototype ne masque pas ce cas.

Si le contour optimisé ne peut pas être produit :

- la vue est créée avec le rectangle aligné à la vue déjà validé ;
- le résultat indique explicitement `Rectangle de secours` ;
- la fenêtre affiche l'avertissement et la cause remontée par Revit.

Le fallback évite de bloquer le test tout en permettant d'identifier les cas que le moteur optimisé devra encore couvrir.

### UI

Le panneau prototype indique désormais :

```text
Prototype — contour logement optimisé
```

et le résultat précise le mode réellement utilisé :

```text
Contour optimisé
```

ou :

```text
Rectangle de secours
```

Aucun fallback n'est donc silencieux.

### Tests hors Revit

Des tests ont été ajoutés pour contrôler :

- la présence du calcul par frontières centrales ;
- la création d'extrusions temporaires ;
- l'union booléenne des solides ;
- l'extraction des boucles de face ;
- l'offset du contour ;
- la conservation du fallback explicite ;
- la remontée du mode et des avertissements vers l'interface ;
- le parsing Python et l'encodage UTF-8 des fichiers concernés.

Une suite ciblée de géométrie et de contrats a été exécutée dans l'environnement disponible : **10 tests réussis**.

La validation réelle de `GeometryCreationUtilities`, des opérations booléennes et de `CurveLoop.CreateViaOffset` reste obligatoirement à faire dans Revit 2025.4.

### Validation Revit demandée

Tester au minimum trois logements :

1. un logement presque rectangulaire ;
2. un logement en L ou avec un retrait important ;
3. le logement irrégulier déjà utilisé pour les prototypes précédents.

Pour chaque cas :

- créer le prototype avec une marge de 500 mm ;
- vérifier le message final ;
- confirmer que le mode est `Contour optimisé` et non `Rectangle de secours` ;
- vérifier que le crop suit la forme générale du logement ;
- vérifier que les retraits importants réduisent réellement les zones vides ;
- vérifier que les gaines ou trous intérieurs ne créent pas de trou dans le crop ;
- vérifier que la marge reste extérieure au logement ;
- vérifier que la vue principale reste inchangée.

Si un cas bascule en `Rectangle de secours`, conserver le texte complet de l'avertissement pour analyse.


## Prototype A.3.1 — Correctif de normalisation du crop

Le premier essai du contour optimisé a basculé en `Rectangle de secours` sur les trois logements testés.

Une contrainte importante de l'API Revit 2025 a été identifiée : `ViewCropRegionShapeManager.IsCropRegionShapeValid` et `SetCropShape` exigent une boucle fermée composée uniquement de **segments droits non nuls**.

Le prototype précédent pouvait transmettre une boucle issue de l'union ou de `CreateViaOffset` contenant encore des courbes non linéaires.

### Nouveau pipeline

```text
Union des pièces
      ↓
Boucle extérieure
      ↓
Tessellation
      ↓
Suppression des doublons
      ↓
Suppression des sommets quasi colinéaires
      ↓
Reconstruction uniquement en Line
      ↓
Offset de marge
      ↓
Linéarisation finale
      ↓
IsCropRegionShapeValid
      ↓
SetCropShape
```

La tolérance `Application.ShortCurveTolerance` est utilisée pour éviter de produire des segments trop courts.

### Diagnostic

Chaque étape critique est maintenant nommée :

- Lecture des contours de pièces ;
- Union géométrique des pièces ;
- Extraction du contour extérieur ;
- Linéarisation du contour extérieur ;
- Application de la marge ;
- Linéarisation finale ;
- Validation du crop Revit.

Si le moteur doit encore revenir au rectangle de secours, l'avertissement indiquera précisément **l'étape en échec**. Cela permettra de corriger le vrai cas géométrique restant sans masquer la cause.

### Validation à rejouer

Reprendre les trois logements du test précédent.

Résultat attendu : `Contour optimisé`.

Si un logement reste en `Rectangle de secours`, transmettre le texte après `Étape en échec :`.


## Prototype A.3.2 — Capacité testée sur la vue cible

Le test Revit suivant a remonté :

```text
Cette vue Revit n'autorise pas un crop non rectangulaire.
```

La cause n'était pas le contour lui-même mais le moment où la capacité `CanHaveShape` était vérifiée.

Le prototype contrôlait cette propriété sur la **vue source** avant création de la vue dépendante. Une vue source pilotée par un Scope Box peut interdire l'édition libre du crop, alors que la cible à modifier est la nouvelle vue dépendante.

### Nouveau comportement

```text
Vue source
   ↓
Calcul géométrique uniquement
   ↓
Création de la vue dépendante
   ↓
Contrôle CanHaveShape sur la VUE CIBLE
   ↓
Scope Box sur la cible ?
   ├─ Oui et modifiable → le retirer sur la vue créée uniquement
   └─ Non / lecture seule → conserver
   ↓
Recontrôle CanHaveShape
   ├─ Oui → appliquer le contour optimisé
   └─ Non → appliquer le rectangle de secours + avertissement
```

La vue principale n'est jamais modifiée par cette logique.

Le Scope Box est identifié via le paramètre Revit `VIEWER_VOLUME_OF_INTEREST_CROP`.

### Test à rejouer

Reprendre un des trois logements testés précédemment.

Le comportement attendu est maintenant :

1. la vue dépendante est créée ;
2. aucune erreur bloquante « Cette vue Revit n'autorise pas... » ne doit apparaître avant création ;
3. si la vue dépendante accepte la forme après création, le résultat doit indiquer `Contour optimisé` ;
4. si elle reste incompatible, le résultat doit indiquer `Rectangle de secours` avec la raison précise liée à la vue cible / au Scope Box.


## Prototype A.3.3 — Marge géométrique robuste

Le test Revit a permis d'isoler précisément le problème de marge :

- **20 mm : contour optimisé fonctionnel** ;
- **25 mm et plus : fallback rectangle** ;
- étape en échec : `Application de la marge`.

Ce comportement montre que l'union des pièces et l'extraction du contour sont correctes. Le point faible était `CurveLoop.CreateViaOffset`.

### Pourquoi l'offset échoue

Sur un contour concave, certains petits décrochements ou retours deviennent incompatibles lorsque la distance d'offset dépasse leur taille locale. Revit doit décaler puis retailler les arêtes pour reconstituer une boucle continue ; cette opération peut échouer brutalement lorsque la topologie doit changer.

La marge d'un plan de vente pouvant atteindre plusieurs centaines de millimètres, cette dépendance n'est pas suffisamment robuste.

### Nouveau principe

`CreateViaOffset` est retiré du moteur de marge.

Le contour est dilaté par géométrie booléenne :

```text
Contour extérieur du logement
           ↓
Solide de base
           +
Bandes autour de chaque arête
largeur = 2 × marge
           +
Raccord octogonal autour
de chaque sommet
           ↓
Union booléenne
           ↓
Boucle extérieure
           ↓
Linéarisation
           ↓
Crop Revit
```

Les bandes garantissent la marge perpendiculairement aux façades du contour.

Les raccords octogonaux absorbent les changements de topologie dans les angles et les petits décrochements. Leur rayon est ajusté pour que l'apothème corresponde à la marge demandée : le crop ne doit donc jamais être inférieur à la marge saisie.

### Conséquence visuelle

La marge est très proche d'un buffer arrondi mais reste constituée uniquement de segments droits, ce qui reste compatible avec le crop Revit.

Aux raccords, l'écart peut être légèrement supérieur à la marge demandée, mais jamais inférieur.

### Validation Revit

Rejouer un logement irrégulier avec :

- 20 mm ;
- 25 mm ;
- 100 mm ;
- 500 mm.

Le résultat attendu est `Contour optimisé` pour chaque valeur.

Ensuite refaire au minimum :

- un logement presque rectangulaire ;
- un logement en L ;
- un logement irrégulier.

La vue principale doit rester inchangée.


## Prototype A.3.4 — Enveloppe graphique propre

Le test visuel aux marges 20 / 50 / 200 / 500 mm confirme que le contour optimisé fonctionne, mais met en évidence deux défauts de présentation :

1. des facettes / renflements dans les angles à 200 et surtout 500 mm ;
2. des petits décrochements dus aux gaines techniques ne comportant pas de pièce.

### Décision de conception

Le crop du plan de vente ne doit pas être une reproduction millimétrique de chaque accident du contour des pièces.

Il doit représenter une **enveloppe graphique propre du logement**.

Les grandes formes du logement sont conservées :

- rectangle ;
- forme en L ;
- retraits importants ;
- loggias / extensions significatives selon les pièces prises en compte.

Les petits accidents liés à des gaines, micro-retraits ou imperfections de modélisation peuvent être simplifiés.

### Raccords de marge

Les anciens raccords octogonaux sont remplacés par des **carrés alignés avec la vue**.

Cela supprime l'effet facetté visible avec de grandes marges et donne des coins plus architecturaux.

### Nettoyage des petits décrochements

Une passe spécifique recherche les détours rectangulaires en U.

Lorsqu'un retrait est suffisamment petit, ses deux sommets intérieurs sont supprimés et le contour est ponté par une ligne directe.

Tolérance actuelle du prototype :

```text
minimum : 300 mm
maximum : 600 mm
```

Elle est liée à la marge de crop tout en restant bornée.

Cette valeur est volontairement interne pendant le prototype. Si les tests montrent qu'un réglage utilisateur est utile, elle deviendra un paramètre du Modèle de plan de vente.

### Validation demandée

Reprendre le même logement avec :

- 20 mm ;
- 50 mm ;
- 200 mm ;
- 500 mm.

Vérifier :

- disparition des artefacts d'angles ;
- maintien des grandes formes du logement ;
- simplification des petites gaines / retraits ;
- absence de coupe dans une pièce ;
- vue principale inchangée.

Si un retrait légitime est supprimé, noter sa largeur approximative afin d'ajuster la tolérance.


## Prototype A.3.5 — Fermeture des petites gaines

Le test visuel suivant confirme que les raccords de marge sont nettement meilleurs, mais montre que certaines gaines techniques sans pièce restent interprétées comme des retraits du logement.

### Cause

L'union des Rooms représente fidèlement les pièces, pas nécessairement l'enveloppe graphique souhaitée pour un plan de vente.

Une gaine technique sans Room crée une poche concave dans l'union.

Le nettoyage précédent ne traitait que des décrochements simples en U. Certaines gaines comportent davantage de sommets et ne sont donc pas reconnues par cette règle locale.

### Nouveau principe

Les petites poches sont analysées **avant la marge**.

```text
Contour extérieur des Rooms
        ↓
Détection des sommets concaves
        ↓
Recherche de paires pouvant fermer une petite poche
        ↓
Pont direct testé
        ↓
Contrôles :
- pas d'intersection avec le contour
- bouche limitée
- profondeur limitée
- aire ajoutée limitée
        ↓
Fermeture de la gaine
        ↓
Marge robuste
        ↓
Crop final
```

### Seuils du prototype

```text
Bouche maximale      : 1 500 mm
Profondeur maximale  : 1 500 mm
Aire remplie maximale: 2,0 m²
```

Ces valeurs sont volontairement conservatrices afin de combler une petite gaine sans supprimer une vraie forme en L du logement.

Elles pourront ensuite devenir configurables dans le Modèle de plan de vente si les projets TAA montrent des besoins différents.

### Validation demandée

Reprendre le logement A003 de la campagne de test et contrôler les marges :

- 20 mm ;
- 50 mm ;
- 200 mm ;
- 500 mm.

Le résultat attendu est :

- angles propres ;
- petites gaines comblées ;
- grandes formes du logement conservées ;
- aucune pièce rognée ;
- vue principale inchangée.

Si une gaine reste visible, mesurer approximativement sa largeur et sa profondeur. Si au contraire une vraie forme du logement est comblée, noter également ses dimensions afin d'ajuster les seuils.


## Prototype A.3.6 — Nettoyage indépendant de la marge

Le test visuel confirme que les angles sont désormais propres, mais que certaines gaines restent visibles surtout avec une petite marge.

Cela montre que la marge ne doit pas servir à masquer une imperfection de l'enveloppe.

### Correction

La détection des petites gaines est maintenant totalement indépendante de la marge de crop.

Au lieu de rechercher uniquement des sommets concaves, le moteur teste toutes les paires de sommets non adjacents pouvant former une bouche de poche.

Un pont n'est retenu que si :

- sa longueur est sous le seuil ;
- il ne coupe pas une autre arête ;
- son milieu se situe à l'extérieur du polygone logement ;
- le nouveau contour augmente l'aire, donc comble bien une poche ;
- la profondeur de la poche reste limitée ;
- l'aire ajoutée reste limitée.

Seuils du prototype :

```text
Bouche maximale       : 2 000 mm
Profondeur maximale   : 2 000 mm
Aire ajoutée maximale : 3,0 m²
```

### Conséquence recherchée

Une même gaine doit être supprimée du contour de la même façon avec :

- 20 mm ;
- 50 mm ;
- 200 mm ;
- 500 mm.

La marge ne sert plus à compenser la géométrie de l'enveloppe ; elle est appliquée uniquement après le nettoyage.


## Prototype A.3.7 — Nettoyage conservateur des gaines

La version précédente de la fermeture générique des poches a provoqué une régression : les quatre marges testées ont basculé en rectangle de secours.

La cause est un nettoyeur trop permissif qui pouvait fabriquer une enveloppe auto-intersectante.

Le nettoyage est maintenant volontairement conservateur :

- seules des poches locales sont candidates ;
- les deux extrémités doivent être des sommets concaves ;
- la chaîne remplacée est limitée à quelques sommets ;
- le pont doit passer à l'extérieur du logement ;
- aucune intersection avec le contour n'est autorisée ;
- le polygone candidat doit rester simple ;
- si le moindre doute subsiste, le contour original est conservé.

Le nettoyage devient ainsi une amélioration graphique facultative et ne doit plus pouvoir casser le moteur de crop validé.


## Prototype A.3.8 — Correctif helper surface polygonale

Le test Revit a identifié une erreur Python indépendante de la géométrie :

```text
_polygon_signed_area() takes exactly 1 argument (2 given)
```

La fonction `_polygon_signed_area(points)` était utilisée comme helper pur mais n'était pas décorée en `@staticmethod`. IronPython lui transmettait donc automatiquement `self`.

Le correctif ajoute simplement `@staticmethod`.

Ce bug expliquait le fallback systématique des quatre marges après la dernière itération : le moteur n'atteignait même pas réellement la logique de fermeture des gaines.


## Prototype A.3.9 — Restauration des helpers de nettoyage

Le test Revit a remonté :

```text
'CropGeometryService' object has no attribute '_vertices_are_adjacent'
```

Il s'agit d'une régression de refactor : les helpers `_vertices_are_adjacent` et `_point_in_polygon` avaient été supprimés alors que le nettoyeur conservateur les utilisait encore.

Les deux helpers ont été restaurés et un test de contrat vérifie désormais explicitement leur présence.


## Prototype A.3.10 — Détection topologique des poches

Le moteur de crop est désormais stable, mais les tests visuels montrent que certaines gaines restent suivies par le contour, surtout lorsque la marge de présentation est faible.

La cause est que les deux lèvres d'une gaine ne sont pas toujours toutes les deux classées comme sommets concaves.

### Nouveau nettoyage

Le moteur teste toutes les paires de sommets non adjacents comme candidats de fermeture, mais ne valide un pont que si :

- la bouche reste sous le seuil configuré ;
- le pont n'intersecte aucune autre arête ;
- son milieu se situe à l'extérieur du polygone logement ;
- le polygone candidat reste simple ;
- la modification ajoute de la surface au logement ;
- l'aire ajoutée reste limitée ;
- la profondeur de la poche reste limitée.

Cette logique ne dépend plus du seul caractère concave des sommets.

### Sécurité

Si aucun candidat sûr n'est trouvé, ou si la reconstruction du contour échoue, le moteur conserve le contour d'origine. Le nettoyage des gaines ne doit donc pas pouvoir casser un crop autrement valide.

Un test supplémentaire contrôle également que tous les appels privés `self._...` du service correspondent à des méthodes réellement définies, afin d'éviter les régressions de refactor rencontrées pendant ce prototype.


## Prototype A.3.11 — Seuils de gaine élargis et diagnostic visuel

Le test visuel montre que le moteur de fermeture fonctionne sans régression, mais que les gaines du logement A003 restent trop grandes pour les seuils précédents.

Les seuils du prototype sont donc élargis de façon ciblée :

```text
Bouche maximale       : 3 500 mm
Profondeur maximale   : 2 000 mm
Aire ajoutée maximale : 5,0 m²
```

La profondeur reste volontairement limitée à 2 m afin de ne pas gommer une vraie grande forme en L.

Le résultat indique maintenant le nombre de poches effectivement comblées :

```text
Contour optimisé — N gaine(s)/retrait(s) comblé(s)
```

Ce diagnostic permet de distinguer deux cas :

- `N = 0` : la gaine n'est pas détectée par la logique de poche ;
- `N > 0` mais la gaine reste visible : la poche fermée n'est pas celle attendue ou le seuil doit être ajusté.


## Prototype A.3.12 — Offset natif après nettoyage

Le dernier test Revit a confirmé que la construction de marge par union booléenne 3D peut échouer sur le contour nettoyé avec le message Revit relatif aux imprécisions géométriques entre solides.

Le moteur applique désormais l'ordre suivant :

```text
Contour extérieur
      ↓
Nettoyage des petites gaines
      ↓
Essai CurveLoop.CreateViaOffset
      ├─ succès → contour final
      └─ échec
           ↓
buffer 3D par bandes + caps
           ↓
fallback rectangle si nécessaire
```

Cette stratégie réutilise l'offset natif seulement **après simplification du contour**, ce qui évite le problème initial rencontré sur le contour brut.

Validation demandée : reprendre A003 avec 20 / 50 / 200 / 500 mm et vérifier si le résultat reste en `Contour optimisé` sans erreur booléenne.


## Prototype A.3.13 — Marge 100 % 2D

Le test Revit a montré que le buffer booléen 3D restait instable dès qu'il était utilisé comme fallback, avec le message :

```text
Failed to perform a Boolean operation for the two solids
```

La décision est donc de **supprimer complètement les booléens 3D de la construction de marge**.

### Nouveau pipeline

```text
Contour nettoyé
      ↓
Essai CreateViaOffset
      ├─ succès → marge obtenue
      └─ échec
           ↓
simplification adaptative de petites concavités
           ↓
nouvel essai CreateViaOffset
      ├─ succès → marge obtenue
      └─ échec → rectangle de secours
```

La simplification adaptative ne supprime que des sommets concaves et n'est acceptée que si :

- le pont reste limité ;
- la profondeur locale reste limitée ;
- l'aire ajoutée reste faible ;
- le polygone reste simple.

Elle ajoute donc de l'espace à l'enveloppe au lieu de couper dans le logement.

### Conséquence

L'étape `Construction de la marge robuste` ne doit plus pouvoir remonter une erreur `BooleanOperationsUtils`.

La validation Revit doit être rejouée sur A003 à 20 / 50 / 200 / 500 mm.


## Prototype A.3.14 — Fermeture des gaines alignée sur les murs

Le test visuel suivant montre que la détection des gaines fonctionne, mais que
certains ponts directs entre deux lèvres créent des segments biaisés. Ces
diagonales sont géométriquement valides mais ne correspondent pas à la lecture
architecturale souhaitée du plan.

### Nouveau principe

Le moteur relève maintenant les murs droits qui bornent les pièces du logement.
Les limites de Room étant lues au centre des murs, chaque segment est décalé de
la moitié de l'épaisseur du mur vers le côté opposé à la pièce. Ce segment
représente donc le **chant opposé du mur**, côté gaine ou extérieur.

Lorsqu'une petite poche est détectée, la fermeture essaie en priorité :

```text
Lèvre A
   ↓ projection perpendiculaire
chant opposé du mur ───────────────
   ↑                         ↑
projection A             projection B
                             ↓
                           Lèvre B
```

Le contour ajouté est donc composé de segments guidés par le mur : deux
raccords perpendiculaires et un segment parallèle au chant du mur. Un pont
direct n'est conservé en secours que s'il prolonge déjà une direction locale
du contour ; une nouvelle diagonale arbitraire est refusée.

### Garde-fous

- seuls les murs droits sont utilisés comme guides dans ce prototype ;
- le guide doit être proche des deux lèvres ;
- sa direction doit rester proche de celle de la bouche de la poche ;
- les projections ne peuvent dépasser le segment de mur que de 600 mm ;
- profondeur, bouche et aire ajoutée restent limitées par les seuils A.3.11 ;
- le polygone final doit rester simple ;
- en cas de doute, le contour précédent est conservé.

Le diagnostic ajoute le nombre de fermetures réellement alignées sur un mur :

```text
Contour optimisé — N gaine(s)/retrait(s) comblé(s) — M fermeture(s) alignée(s) sur mur
```

### Validation Revit demandée

Reprendre le logement montré lors du test du 2 octobre 2026 et vérifier en
priorité les zones de gaines qui produisaient des biais. Tester les marges
20 / 50 / 200 / 500 mm.

Résultat attendu :

- les gaines restent prises en compte ;
- les fermetures suivent un chant de mur voisin au lieu d'une diagonale libre ;
- aucune vraie forme en L du logement n'est supprimée ;
- le crop reste en `Contour optimisé` ;
- aucune régression sur les vues dépendantes.
