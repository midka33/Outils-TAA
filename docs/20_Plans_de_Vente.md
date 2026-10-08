# Outils TAA — Plans de vente

## Spécification fonctionnelle et technique

**Version :** 1.19
**Statut :** Développement — Étape 06 Cotations  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x  
**Interface :** WPF — Design System Outils TAA  
**Langue :** Français  
**Date :** 2026-10-08


**Crop actuel :** voir A.3.20 — géométrie locale des pièces, sans sélection de mur.

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

Ce comportement a été retenu pour la V1 : les vues logement restent des vues dépendantes de vues principales techniques dédiées aux Plans de vente.

### Groupes de vues principales par échelle

Une vue dépendante ne doit jamais forcer un changement d'échelle sur une vue principale déjà utilisée par d'autres logements.

La V1 organise donc les vues par **groupe de compatibilité** :

```text
niveau
+ vue source de référence
+ échelle
        ↓
vue principale technique PDV
        ↓
vues dépendantes des logements
```

Exemple :

```text
PDV MASTER — Niveau 0 — 1:50
├── A001
├── A002
└── A003

PDV MASTER — Niveau 0 — 1:100
├── A004
└── A005
```

Si une échelle demandée n'a pas encore de vue principale compatible, le module duplique la vue source en **vue indépendante**, applique l'échelle demandée à cette nouvelle vue principale technique, puis crée la vue logement comme dépendante de celle-ci.

Si le groupe existe déjà, il est réutilisé. La vue source choisie par l'utilisateur n'est jamais modifiée.

La vue principale technique n'est pas destinée à être placée sur une feuille ; seules les vues dépendantes des logements le sont.

La clé V1 doit au minimum distinguer le niveau, l'échelle et la vue source de référence. Le futur **Modèle de plan de vente** ajoutera notamment le gabarit et la phase au contrat de compatibilité.

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

Pour la V1, l'objectif est volontairement simple et constant :
**deux cotes principales maximum par pièce** :

- longueur intérieure finie ;
- largeur intérieure finie.

Cette règle s'applique aussi aux pièces en L, en T ou aux géométries atypiques.
Le moteur privilégie les dimensions générales et ne cherche plus à décrire
automatiquement toutes les branches de la pièce.

Les petits décrochements, niches et retours mineurs restent filtrés.

Lorsque la géométrie nécessite des cotes complémentaires, l'utilisateur les
ajoute manuellement après génération. La cotation automatique est donc une
base de production rapide à relire, et non une cotation exhaustive.

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

## 15.1 Décision V1 — échelle explicite

Pour la V1, l'échelle est **choisie explicitement**. Le module ne cherche pas encore à déterminer automatiquement si un logement tient dans la zone disponible de la feuille.

L'utilisateur peut demander par exemple :

```text
Échelle de la vue logement
1:[ 50 ]
```

Le module ne modifie jamais l'échelle de la vue source sélectionnée.

Il recherche d'abord une vue principale technique PDV correspondant au même niveau, à la même vue source de référence et à l'échelle demandée.

- si elle existe : elle est réutilisée ;
- sinon : une nouvelle vue principale indépendante est créée depuis la vue source, puis son échelle est réglée ;
- la vue du logement est ensuite créée comme **vue dépendante** de cette vue principale technique.

Cela permet d'avoir plusieurs groupes sur un même niveau sans désynchroniser les autres logements :

```text
Niveau 0
├── groupe 1:50
│   ├── A001
│   └── A002
└── groupe 1:100
    └── A003
```

La création et la réutilisation du groupe doivent être déterministes afin de fonctionner également après fermeture/réouverture de Revit.

## 15.2 Ajustement automatique — après V1

L'ajustement automatique reste une évolution ultérieure :

```text
Échelle
● Imposée                       [1:50]
○ Ajuster automatiquement si nécessaire
```

Lorsqu'il sera activé, le moteur comparera l'emprise du crop et la zone disponible sur la feuille, puis choisira une échelle Revit autorisée. Il devra ensuite rattacher la vue logement au groupe de vue principale correspondant à cette échelle.

Aucun changement automatique d'échelle ne doit avoir lieu tant que cette option n'est pas explicitement activée.

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
- les deux lèvres doivent pouvoir se projeter à proximité sur le même chant de mur ;
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


## Prototype A.3.15 — Accepter les lèvres décalées sur un même mur

Le premier test Revit de la fermeture guidée par mur a basculé en
`Rectangle de secours` à l'étape `Construction de la marge robuste`.

### Cause identifiée

La première implémentation imposait que la corde directe entre les deux lèvres
de la poche soit presque parallèle au mur guide.

Cette condition est contradictoire avec le cas que l'on cherche à corriger :
quand les deux lèvres sont décalées l'une par rapport à l'autre, leur corde est
justement diagonale. Le mur correct pouvait donc être rejeté avant même que les
deux lèvres soient projetées sur son chant. La gaine restait alors dans le
contour et l'offset Revit pouvait échouer sur cette concavité.

### Correction

La direction de la corde entre lèvres n'est plus comparée à celle du mur.

Un mur guide est désormais accepté si :

- les deux lèvres se projettent sur la même face opposée du mur ;
- les projections restent proches du segment de mur, avec l'extension limitée
  déjà prévue ;
- le segment de face utilisé reste à l'extérieur du logement ;
- la profondeur et l'aire ajoutée restent sous les seuils ;
- le polygone candidat reste simple.

Ainsi, une bouche dont les deux lèvres sont décalées peut être remplacée par
deux raccords perpendiculaires au mur et un segment parallèle à son chant,
sans créer de diagonale libre.

Le message de fallback indique aussi désormais combien de poches avaient été
fermées avant l'échec, dont combien avec un guide mural. Ce diagnostic permet
de distinguer immédiatement un problème de détection d'un problème d'offset.


## Prototype A.3.16 — Type de mur périphérique explicite

Le test A003 a montré deux limites de la détection automatique :

- le moteur pouvait annoncer jusqu'à **50 poches fermées**, ce qui indique que
  la recherche combinatoire essayait de simplifier beaucoup trop de couples de
  sommets ;
- le calcul devenait sensiblement long avant de finir malgré tout en rectangle
  de secours.

### Choix utilisateur

Le prototype demande désormais un **type de mur périphérique** avant de créer
le contour.

La liste contient les types de murs réellement utilisés dans le projet. Pour
cette étape du prototype, un seul type est sélectionné. Une sélection multiple
pourra être ajoutée plus tard dans le modèle de plan de vente.

### Nouveau pipeline rapide

```text
Rooms du logement
      ↓
frontières de Rooms
      ↓
segments portés par le type de mur périphérique choisi
      ↓
bandes 2D représentant toute l'épaisseur de ces murs
      ↓
union Rooms + bandes périphériques
      ↓
contour extérieur
      ↓
marge
      ↓
crop
```

Les bandes ne prennent pas la longueur complète d'un mur partagé avec d'autres
logements. Elles partent du segment qui borde réellement une Room du logement
et peuvent s'étendre de 600 mm au maximum, sans dépasser les extrémités réelles
du mur. Cette extension sert à franchir une petite interruption créée par une
gaine sans étendre le crop sur un logement voisin.

### Effet sur les performances

Quand un type périphérique est fourni, la recherche générale de toutes les
paires de sommets n'est plus exécutée. Le contour est construit directement
par l'union géométrique des pièces et des bandes de murs sélectionnées.

Le diagnostic de résultat indique le nombre de murs périphériques effectivement
utilisés. En cas d'échec, le message indique également ce nombre afin de
vérifier immédiatement que le type choisi a bien été rencontré autour du
logement.

### Validation demandée

Sur A003 :

1. sélectionner le type de mur de façade / périphérique réellement utilisé ;
2. conserver la même marge que lors du test précédent ;
3. vérifier que le calcul est nettement plus rapide ;
4. vérifier que les gaines en façade sont absorbées par l'enveloppe ;
5. vérifier que le contour suit le chant extérieur du mur sélectionné ;
6. vérifier qu'il ne s'étend pas sur un logement voisin.


## Prototype A.3.17 — Mur périphérique proche, pas nécessairement limite de Room

Le test Revit suivant a retourné :

```text
Murs périphériques utilisés : 0
Aucun mur droit du type périphérique sélectionné ne borde les pièces de ce logement.
```

### Cause

La première version du sélecteur de type imposait encore une relation
topologique trop stricte : le mur choisi devait être directement le
`BoundarySegment.ElementId` d'une Room.

Dans un projet réel, un mur extérieur peut être séparé de la Room par :

- un doublage intérieur ;
- une contre-cloison ;
- une autre paroi room-bounding ;
- une limite de pièce distincte.

Le type sélectionné est donc bien le mur architectural recherché sans être
l'élément qui génère directement le contour bleu des pièces.

### Correction

Le moteur construit d'abord l'enveloppe extérieure des Rooms seules, puis
cherche dans le projet les instances du **type de mur sélectionné** situées à
proximité de cette enveloppe.

Critères actuels :

- même tranche verticale que le niveau du logement ;
- distance maximale au contour : **1 000 mm** ;
- mur et arête de contour sensiblement parallèles ;
- uniquement la portion du mur réellement en vis-à-vis du logement ;
- extension longitudinale maximale : **600 mm**.

La bande créée atteint le contour des Rooms du côté logement afin de franchir
un doublage éventuel, tout en conservant le chant opposé du mur comme limite
extérieure.

Cette recherche est linéaire sur les murs du type choisi et les arêtes du
contour. Elle ne réactive pas la recherche combinatoire des 50 poches.

### Validation A003

Sélectionner à nouveau le même type de mur périphérique. Le résultat attendu
est désormais un diagnostic avec `Murs périphériques utilisés : N`, avec
`N > 0`, puis un calcul nettement plus court que l'ancienne fermeture
automatique.


## Prototype A.3.18 — Murs périphériques du projet ou d'un lien Revit

Le test A003 après la recherche par proximité retourne encore
`Murs périphériques utilisés : 0`, alors que la façade visible est clairement
à moins de 1 000 mm du contour des pièces.

Cette situation montre que la **source du mur** doit être conservée : dans une
maquette de coordination, les Rooms peuvent être dans le projet actif alors
que les murs visibles proviennent d'un **lien Revit**.

### Sélecteur enrichi

La liste des types de murs affiche maintenant leur source :

```text
[Projet] Mur de base — ...
[Lien : Architecture.rvt] Mur de base — ...
[Lien : Structure.rvt] Mur de base — ...
```

Seuls les liens chargés sont proposés.

### Géométrie liée

Pour un type provenant d'un lien :

1. le moteur récupère le `RevitLinkInstance` sélectionné ;
2. il collecte les murs dans le document lié ;
3. leurs points, orientations et boîtes englobantes sont transformés dans les
   coordonnées du projet hôte avec `GetTotalTransform()` ;
4. la même recherche par proximité de 1 000 mm est ensuite appliquée au
   contour extérieur des Rooms.

Le diagnostic de fallback indique maintenant explicitement la source utilisée
pour les murs.

### Validation A003

Après rechargement de pyRevit, vérifier la liste **Mur périphérique**. Si le mur
de façade appartient à un lien, sélectionner la ligne préfixée
`[Lien : ...]` correspondante plutôt que la version `[Projet]`.


## Prototype A.3.19 — Résolution robuste du type de mur hôte

La capture Revit d'A003 confirme que le mur testé est bien une instance du
projet actif :

```text
Mur de base
MUR-EXT-BET-Béton20CM
Niveau : Niveau 0A
```

Le problème n'est donc pas nécessairement lié à un lien Revit.

### Correction

Le moteur ne compare plus le `UniqueId` lu sur chaque `WallType` pendant
la boucle.

Il résout d'abord le type sélectionné dans son document source, puis conserve
son `ElementId`. Chaque mur est ensuite testé avec :

```text
wall.GetTypeId() == selected_type.Id
```

Cette méthode suit directement le contrat Revit entre une instance de mur et
son type.

### Diagnostic de filtrage

Si aucun mur n'aboutit à une bande périphérique, le message indique désormais
combien de murs franchissent chaque filtre :

```text
X instance(s) du type
Y mur(s) droit(s)
Z au bon niveau
A dans la zone
B proche(s) et parallèle(s) au contour
```

Cela permettra au prochain test A003 d'identifier précisément le filtre qui
élimine `MUR-EXT-BET-Béton20CM`, sans nouvelle supposition.

## Prototype A.3.20 — Raccords locaux sans murs périphériques (2026-10-05)

**Comportement actif de référence.** Les sections A.3.5 à A.3.19 ci-dessus
conservent l'historique des essais ; leurs recherches de paires globales,
cordes directes et stratégies de murs sont remplacées par cette section.
L'union des Rooms, le repère de vue, la normalisation en lignes, les identifiants
persistants et le secours rectangulaire sont conservés.

### Historique analysé et retrait ciblé

`96c0f15` est la référence avant les guides de murs : les poches étaient
comblées, mais par des cordes susceptibles d'être obliques. La suppression du
buffer de marge 3D (`ee730f1`) et ses correctifs restent acquises.
`405d577` et `6555a8f` introduisaient les faces guides ; `f253187` ajoutait le
choix de type, puis `57c3c4e`, `be15509` et `a79a90b` élargissaient la recherche
aux murs proches, aux liens et à la résolution des types. Ces mécanismes sont
retirés, sans revert global de la branche.

### Pipeline et responsabilité

Rooms → union géométrique temporaire → boucle extérieure → linéarisation
→ moteur local pur → validation → offset natif 2D → linéarisation → crop.

`lib/plans_vente/local_crop_geometry.py` porte les calculs sans import Revit ni
bibliothèque géométrique tierce ; syntaxe compatible IronPython 2.7.
`CropGeometryService` convertit les UV et les unités internes, reconstruit la
CurveLoop et conserve l'original si cette reconstruction échoue.

Une chaîne locale contient au moins un virage concave intérieur. Ses lèvres
sont des virages sortants après fusion des subdivisions exactement colinéaires.
Les deux supports A/B sont les arêtes immédiatement avant/après cette chaîne.
Parmi les chaînes locales sûres au même départ, la plus complète est retenue
pour éviter plusieurs fermetures partielles d'une même gaine. Pour cette chaîne,
on retient le raccord sûr ajoutant le moins de surface.

- **Colinéaires** : suppression du détour puis fusion des segments alignés.
- **Non parallèles** : intersection des droites support, comme TR ; raccourcir
  ou prolonger sans inverser A/B. Aucun segment reliant directement les lèvres.
- **Parallèles décalées** : deux projections orthogonales possibles. Le raccord
  entre supports est perpendiculaire ; les prolongements restent sur A/B.
- Supports parallèles parcourus en sens opposés : candidat rejeté.

La validation impose orientation conservée, aire ajoutée strictement positive,
polygone simple, absence de segment nul, recouvrement ou contact non adjacent.
La contenance porte sur **toutes les arêtes de l'ancien contour**, découpées
aux intersections, et pas uniquement sur ses sommets ou son aire totale.

### Seuils et performances

| Critère | Limite |
|---|---|
| Distance entre lèvres | 3 500 mm |
| Profondeur maximale de la chaîne par rapport au raccord | 2 000 mm |
| Surface ajoutée par fermeture | 5,0 m² |
| Distance intersection–chacune des lèvres / prolongement sur support | 3 500 mm |
| Chaîne inspectée | 12 arêtes au maximum |
| Balayages par appel | 2 |
| Validations complètes par appel | 128 |
| Tolérance angulaire de parallélisme | sinus ≤ 1e-9 |
| Tolérance géométrique transmise par Revit | max(ShortCurveTolerance, 1e-7 pied) |

Les supports presque parallèles qui se croisent trop loin sont rejetés.
Le test strict de colinéarité utilise 1e-9 unité de longueur ; une séparation
supérieure ne devient jamais une corde inclinée « presque alignée ».
Chaque balayage visite au plus le nombre de sommets présent au début du
balayage et inspecte au plus 11 longueurs de chaîne par départ. Il n'y a plus
50 reprises d'une recherche sur toutes les paires de sommets. Les vérifications
topologiques restent quadratiques en nombre d'arêtes, mais sont plafonnées à
128 candidats par appel. Si ce budget ou le nombre de passes est atteint,
les retraits non traités restent présents et le diagnostic le signale.

La fermeture initiale est indépendante de la marge. L'offset natif est essayé
en premier. La tentative adaptative et le nettoyage après offset emploient le
même moteur sûr : aucune suppression de sommet créant une corde oblique ne
subsiste. Le nettoyage après offset garde sa tolérance de 300 à 600 mm et une
aire maximale égale au carré de cette tolérance. Si l'offset reste impossible,
le rectangle de secours est annoncé. **Aucun booléen 3D pour la marge.**
Les booléens de l'union initiale des Rooms restent nécessaires et inchangés.

### Interface et diagnostic

Le prototype demande seulement le logement, la vue source et la marge, puis
**Créer le contour optimisé**. Aucun type de mur ni source liée à choisir.
Le sélecteur de paramètre identifiant le logement reste dans la détection.

Le résultat affiche les fermetures colinéaires, les raccords Trim/Extend et
les raccords perpendiculaires. Les compteurs ne sont incrémentés qu'après
reconstruction réussie ; ils incluent les éventuels nettoyages de marge.
Un échec indique l'étape et les compteurs déjà obtenus. Le contrôle CanHaveShape
sur la vue cible fonctionne aussi lorsque le mode contient ce diagnostic.

### Tests et validation

`tests/plans_vente/test_local_crop_geometry.py` couvre A–H : colinéaire,
intersection droite/oblique, parallèles décalées, intersection distante,
auto-intersection/contact/recouvrement, contenance malgré gain d'aire,
absence de corde arbitraire. S'ajoutent rotations, translation, inversion de
sens, changement de sommet initial, seuils, grandes formes en L, budget,
idempotence et 20 poches synthétiques.
`test_local_crop_adapter.py` exécute le véritable adaptateur avec reconstruction
CurveLoop simulée : conservation en cas d'erreur, diagnostic et fallback sur
vue incompatible. Les contrats obsolètes des murs ont été remplacés.

Résultat local : **60 tests réussis**, suite entière `tests/plans_vente`.
Ce résultat ne valide ni le temps sur A003 ni l'API/rendu Revit réel.
Le workflow `.github/workflows/plans-vente-tests.yml` exécute cette même suite
avec Python 3.11 après publication sur la branche de travail.

### Procédure manuelle A003 — Revit 2025.4 / pyRevit 5.x

1. Récupérer `feature/plans-de-vente-proto-views-crop`, copier l'extension si
   l'installation pyRevit utilise un autre dossier, puis recharger pyRevit.
2. Ouvrir Plans de vente dans la même maquette et choisir le paramètre logement.
   Lancer l'analyse et sélectionner A003 ; vérifier son nombre de pièces.
3. Choisir la même vue source que précédemment. Aucun champ de mur ne doit
   apparaître. Noter la vue source et son crop avant l'essai.
4. Entrer **20 mm**, lancer **Créer le contour optimisé**, confirmer la création.
   Chronométrer le clic jusqu'au résultat et relever le diagnostic complet.
5. Dans la vue dépendante créée, afficher/modifier le cadrage et examiner chaque
   ancienne gaine : alignement continu, angle TR ou marche perpendiculaire,
   aucune diagonale nouvelle, aucune pièce rognée, grande forme en L conservée.
6. Refaire des créations à **50, 200 et 500 mm** avec la même source. La marge
   doit fonctionner sans retour au buffer 3D. Relever tout rectangle de secours,
   étape en échec ou message de budget ; ne pas le compter comme un succès.
7. Vérifier que la vue principale n'a pas été recadrée et que chaque vue créée
   s'ouvre correctement. Refaire un essai sur une autre forme de logement.
8. Transmettre les captures de chaque gaine à 20 mm et 500 mm, les compteurs et
   temps mesurés. Les données géométriques réelles d'A003 ne sont pas disponibles
   dans les tests hors Revit : leur validation reste indispensable.


## A.3.21 — Normalisation locale des segments A/B

La validation Revit du moteur local A.3.20 montre un résultat globalement correct et
rapide, mais quelques petits décrochements peuvent subsister au bord de certaines
gaines techniques.

La cause est locale : le segment immédiatement avant ou après la chaîne de la poche
peut lui-même être un petit retour parasite. Le moteur utilisait alors ce petit segment
comme support A ou B, puis appliquait correctement la règle colinéaire / Trim-Extend /
perpendiculaire, mais sur un support trop proche de la poche.

### Correction

Avant le raccord, le moteur peut désormais absorber au maximum **deux segments de
contexte de chaque côté** de la poche détectée.

Un segment adjacent n'est absorbé que s'il est court **relativement à son contexte
local** :

- il reste sous une fraction des seuils existants de bouche et de profondeur ;
- il est nettement plus court que le segment principal situé plus loin du côté
  extérieur de la poche ;
- la recherche reste strictement locale et bornée.

Après normalisation, les règles de fermeture restent inchangées :

1. supports colinéaires → fusion ;
2. supports non parallèles → Trim/Extend à leur intersection ;
3. supports parallèles décalés → raccord perpendiculaire.

Tous les garde-fous existants restent obligatoires : aire ajoutée positive et limitée,
contenance de l'ancien contour, polygone simple, extension maximale et budget de
validations.

### Performance

La normalisation n'effectue aucune recherche globale. Elle regarde au maximum deux
segments supplémentaires avant A et deux après B.

Constante :

```text
MAX_CONTEXT_SEGMENTS = 2
```

### Diagnostic

Le diagnostic Revit indique maintenant également :

```text
N segment(s) parasite(s) absorbé(s)
```

Cette information doit permettre de vérifier sur A003 que les deux petits retours
résiduels sont réellement intégrés à la chaîne de la poche avant raccord.

## Validation V1 du détourage — 2026-10-05

Le détourage est considéré **validé pour la V1** après les essais Revit 2025.4 du moteur local A.3.20/A.3.21.

Décision :

- conserver le moteur local actuel comme comportement de référence ;
- ne plus remettre en cause l'algorithme général pour traiter des cas isolés ;
- accepter comme limite connue V1 que certaines **gaines palières** puissent encore demander une correction manuelle ;
- traiter ce cas particulier dans une évolution ultérieure afin de ne pas déstabiliser le moteur validé.

La V1 privilégie donc un contour fiable et rapide sur les cas courants plutôt qu'une automatisation totale de tous les cas de gaine.


## A.4 — Échelle et groupes de vues principales

Dernier sous-objectif de l'Étape 03.

### Comportement retenu

La vue source sélectionnée sert uniquement de **référence de duplication**. Elle n'est jamais modifiée.

Pour chaque combinaison :

```text
vue source + niveau + échelle
```

le module utilise une vue principale technique dédiée :

```text
PDV MASTER - <niveau> - 1-<échelle> - <identifiant source>
```

Lors de la première création, la vue source est dupliquée avec
`ViewDuplicateOption.Duplicate`, puis l'échelle est appliquée à cette copie.
Les vues logement sont créées avec `ViewDuplicateOption.AsDependent` depuis
cette vue principale technique.

Les créations suivantes avec la même source, le même niveau et la même échelle
réutilisent la vue principale existante. Une autre échelle crée un autre groupe.

Les vues `PDV MASTER` sont exclues de la liste des vues sources proposées afin
d'éviter les chaînes de masters.

### Interface V1

Le prototype expose un champ **Échelle 1:**. Il reprend par défaut l'échelle de
la vue source choisie et accepte une valeur explicite telle que `50` ou
`1:50`.

Aucun calcul automatique d'échelle n'est effectué en V1.

### Contrôles hors Revit

Les tests couvrent :

- normalisation `50` / `1:50` ;
- rejet des échelles invalides ;
- nom déterministe d'un groupe par niveau, échelle et source ;
- duplication indépendante de la vue principale ;
- création de la vue logement en dépendante du master ;
- exclusion des masters de la liste des sources.

### Validation finale Étape 03 — Revit 2025.4

Validation utilisateur confirmée le **5 octobre 2026** dans Revit 2025.4 / pyRevit 5.x.

Points validés :

- création d'un master technique à 1:50 ;
- réutilisation du même master pour un second logement compatible ;
- création d'un master distinct à 1:100 ;
- conservation de la vue source d'origine sans changement d'échelle ni de crop ;
- vues logement correctement dépendantes du master correspondant ;
- crops logement conformes ;
- aucun problème de chargement ou d'utilisation signalé.

**Étape 03 — Vues et crop : VALIDÉE V1.**

Le développement peut désormais passer à **l'Étape 04 — Nomenclatures et repérage**.


## Clôture Étape 03 — 2026-10-05

L'Étape 03 est considérée comme terminée pour la V1.

Acquis :

- vues dépendantes validées ;
- vue source préservée ;
- détourage automatique validé V1 ;
- limite connue documentée sur certaines gaines palières ;
- marge de crop opérationnelle ;
- groupes `PDV MASTER` séparés par source / niveau / échelle ;
- réutilisation d'un master compatible ;
- création d'un nouveau master lorsqu'une autre échelle est demandée ;
- échelle explicite en V1 ;
- 71 tests Plans de vente réussis en CI avant validation Revit.

L'ajustement automatique de l'échelle à la feuille reste hors V1.

**Prochaine étape officielle : Étape 04 — Nomenclatures et repérage.**


### Dette de robustesse V1 — validation finale du crop selon la marge

Un essai Revit 2025.4 du **5 octobre 2026** a montré qu'un logement peut encore
échouer pour certaines valeurs de marge alors que le détourage fonctionne avec
d'autres valeurs.

Message observé :

```text
Le contour calculé n'est pas accepté par Revit comme crop.
```

Exemple constaté pendant la validation : vue logement à **1:100** avec une marge
de **50 mm**. Ce cas ne remet pas en cause la validation fonctionnelle de
l'Étape 03 pour la V1, mais il constitue une **dette de robustesse à consolider**.

La cause technique identifiée est un trou dans le fallback actuel :
`apply_to_view()` utilise le rectangle de secours lorsque la vue cible ne peut
pas recevoir un crop non rectangulaire, mais si
`IsCropRegionShapeValid(selected_loop)` rejette directement le contour optimisé,
le service lève encore une erreur au lieu d'essayer ce rectangle de secours.

Décision V1 :

- ne pas rouvrir maintenant le moteur géométrique validé ;
- conserver ce cas dans le registre de bugs ;
- poursuivre l'Étape 04 ;
- lors de la passe de consolidation, tenter le rectangle de secours si le
  contour optimisé est rejeté au contrôle final Revit, puis poursuivre le
  diagnostic géométrique des marges problématiques ;
- ne pas considérer la correction manuelle ponctuelle d'un crop comme une
  régression bloquante de la V1 tant que le logement peut être généré par une
  autre marge ou corrigé manuellement.

Cette dette devra être traitée avant la stabilisation finale de la V1.


## Ouverture Étape 04 — Nomenclatures et repérage

Branche de travail : `feature/plans-de-vente-stage04-schedules-location`.

L'Étape 04 est découpée en trois sous-étapes afin de conserver des prototypes
Revit testables et indépendants.

### 04A — Nomenclatures intérieure et extérieure

La V1 utilise **deux nomenclatures modèles choisies par l'utilisateur** :

- nomenclature modèle intérieure ;
- nomenclature modèle extérieure.

Ces nomenclatures modèles restent la source de vérité pour la présentation et
pour la distinction métier intérieur / extérieur. Le plugin ne doit pas coder
en dur une liste de noms de pièces comme `Balcon`, `Terrasse` ou `Loggia`.

Pour un logement sélectionné, le module doit :

1. dupliquer la nomenclature modèle ;
2. conserver ses champs, tris, mise en forme et filtres métier existants ;
3. identifier le champ correspondant au paramètre logement déjà choisi lors de
   l'analyse ;
4. remplacer ou ajouter uniquement le filtre de logement ;
5. appliquer la valeur du logement ;
6. nommer la copie de manière déterministe ;
7. ne jamais modifier la nomenclature modèle.

Si une nomenclature modèle ne contient pas le champ nécessaire au filtre
logement, l'opération doit être bloquée avec un diagnostic clair.

### 04B — Plan de repérage

Le plan de repérage partira d'une vue plan de référence configurable. La V1 doit
permettre de choisir :

- la vue source de repérage ;
- le gabarit à appliquer lorsque pertinent ;
- le style/type de surbrillance du logement.

La vue de repérage générée doit mettre en évidence le logement sans modifier la
vue source.

### 04C — Placement

L'Étape 04 doit produire des éléments prêts à être placés sur une feuille :
nomenclature intérieure, nomenclature extérieure et vue de repérage.

Le placement définitif et la composition complète avec cartouche, vue logement,
légendes et paramètres seront raccordés à l'Étape 07 — Assemblage feuille.
L'Étape 04 doit néanmoins préparer des rôles et points d'ancrage stables afin
que ce raccordement ne dépende pas d'une détection implicite.

### Ordre de développement

```text
04A Nomenclatures
        ↓
validation Revit
        ↓
04B Plan de repérage
        ↓
validation Revit
        ↓
04C Contrat de placement / ancrages
        ↓
Étape 04 validée
```


## Prototype 04A — Nomenclatures filtrées par logement

Implémentation préparée sur `feature/plans-de-vente-stage04-schedules-location`.

### Comportement

Après l'analyse des logements, l'interface propose uniquement les nomenclatures Revit qui :

- sont des `ViewSchedule` duplicables ;
- ne sont pas des vues gabarits ;
- ne sont pas déjà des nomenclatures générées `PDV_...` ;
- contiennent réellement le champ correspondant au paramètre logement choisi.

L'identification du champ privilégie l'identité stable du paramètre :

- GUID pour un paramètre partagé ;
- identifiant de paramètre intégré Revit ;
- identifiant de définition pour un paramètre projet ;
- nom seulement pour un descripteur qui ne possède aucune identité plus stable.

Pour le logement `A001`, les deux copies sont nommées :

```text
PDV_A001_INT
PDV_A001_EXT
```

Les caractères interdits dans un nom de vue Revit sont neutralisés.

### Conservation du modèle

Chaque nomenclature modèle est dupliquée avec `ViewDuplicateOption.Duplicate`.
La copie conserve donc les champs, tris, mise en forme et filtres métier du modèle.

Le service repère les filtres qui utilisent le champ logement :

- s'il en existe un, il est remplacé par `paramètre logement = <valeur logement>` ;
- s'il en existe plusieurs sur ce même champ, un seul filtre d'égalité est conservé ;
- s'il n'en existe aucun, le filtre d'égalité est ajouté ;
- les filtres portant sur les autres champs ne sont pas modifiés.

Si le champ logement n'est pas présent ou n'est pas filtrable par valeur, l'opération est refusée avant duplication.

### Sécurité V1

La nomenclature modèle n'est jamais modifiée.

Si `PDV_<logement>_INT` ou `PDV_<logement>_EXT` existe déjà, le prototype bloque la création au lieu de générer silencieusement un doublon. La logique de mise à jour des éléments existants reste réservée à l'Étape 08.

Les deux nomenclatures sont créées dans une transaction courte commune : un échec sur l'une annule la paire.

### Validation Revit 2025.4 — à effectuer

1. choisir le paramètre logement et lancer l'analyse ;
2. sélectionner un logement ;
3. sélectionner une nomenclature modèle intérieure et une extérieure ;
4. cliquer **Créer les nomenclatures** ;
5. vérifier la création de `PDV_<logement>_INT` et `PDV_<logement>_EXT` ;
6. vérifier que champs, tris, formatage et filtres métier sont identiques aux modèles ;
7. vérifier que seul le filtre logement vaut la valeur du logement sélectionné ;
8. vérifier que les nomenclatures modèles sont inchangées ;
9. relancer sur le même logement et vérifier que la collision est bloquée ;
10. vérifier qu'une nomenclature ne contenant pas le paramètre logement n'est pas proposée.

**Statut : VALIDÉ dans Revit 2025.4 le 5 octobre 2026.**


### Paramètre logement par défaut

À l'ouverture de Plans de vente, le sélecteur **Paramètre identifiant le logement** cherche en priorité le paramètre partagé nommé exactement :

```text
N° Appartement
```

Le critère `SHARED_GUID` est obligatoire : un paramètre projet ou un paramètre par nom portant le même libellé ne doit pas être préféré au paramètre partagé.

Si ce paramètre partagé est présent, il est sélectionné automatiquement. S'il n'existe pas dans le projet, le premier paramètre texte disponible reste sélectionné afin de ne pas bloquer l'outil.

Ce choix ne lance pas automatiquement l'analyse ; l'utilisateur conserve le contrôle du bouton **Analyser les logements**.


## Prototype 04B — Plan de repérage

Le prototype 04B crée une vue de repérage indépendante sans modifier la vue source.

### Principe V1

Pour un logement sur un seul niveau :

```text
Vue plan source
      ↓ Duplicate
PDV_<logement>_REP
      +
gabarit optionnel
      +
zones remplies sur les pièces du logement
```

Le nom est déterministe, par exemple `PDV_A001_REP`.

### Configuration utilisateur

L'interface permet de choisir :

- la vue plan source du niveau du logement ;
- un gabarit de plan d'étage, ou **Conserver la vue source** ;
- un type de `FilledRegionType` pour la surbrillance.

Les vues générées `PDV_...` ne sont pas reproposées comme vues sources, afin d'éviter les duplications en chaîne.

### Surbrillance

Le plan de repérage utilise désormais **une seule zone remplie globale pour tout
le logement**.

Le contour est construit par le moteur géométrique de l'Étape 03 avec une marge
de `0 mm`. Ce moteur travaille sur les limites de pièces au centre des murs,
réunit les pièces puis extrait l'enveloppe extérieure du logement. La zone
remplie passe ainsi **par-dessus les cloisons intérieures**, au lieu de laisser
une coupure entre chaque pièce.

```text
pièces du logement
        ↓
moteur de contour global Étape 03
        ↓
enveloppe extérieure — marge 0 mm
        ↓
1 seule FilledRegion
```

Le rectangle de secours du moteur de crop n'est volontairement pas utilisé pour
le repérage : si l'enveloppe globale fiable ne peut pas être calculée, la
création est bloquée afin d'éviter de surligner une partie extérieure au
logement.

La V1 met en évidence toute l'emprise du logement ; elle ne tente pas encore de
distinguer graphiquement intérieur et extérieur dans le plan de repérage.

### Sécurité

- la vue source n'est jamais modifiée ;
- le gabarit n'est appliqué qu'à la copie ;
- la création de la vue et de toutes les zones remplies est regroupée dans une transaction courte ;
- si `PDV_<logement>_REP` existe déjà, la création est bloquée jusqu'à la logique de mise à jour de l'Étape 08 ;
- le prototype V1 attend actuellement un logement sur un seul niveau.

### Validation Revit 2025.4 — à effectuer

1. analyser les logements puis sélectionner un logement ;
2. choisir une **Vue source** de repérage du bon niveau ;
3. choisir **Conserver la vue source** ou un gabarit de plan ;
4. choisir un type de **Zone remplie** ;
5. cliquer **Créer le plan de repérage** ;
6. vérifier la création de `PDV_<logement>_REP` ;
7. vérifier que la vue source d'origine est inchangée ;
8. vérifier que le gabarit choisi est appliqué uniquement à la copie ;
9. vérifier qu'il existe **une seule zone remplie** couvrant tout le logement,
   y compris les cloisons intérieures ;
10. vérifier que la zone suit bien l'enveloppe extérieure du logement sans
    devenir un simple rectangle ;
11. relancer sur le même logement et vérifier que la collision de nom est bloquée.

**Statut : VALIDÉ dans Revit 2025.4 le 5 octobre 2026.**


### Correctif 04B — libellés des zones remplies

Lors du premier essai Revit 2025.4, les types de zones remplies étaient bien
collectés mais leurs libellés apparaissaient vides dans la ComboBox.

Cause : limitation connue d'IronPython sur la propriété `Name` des
sous-classes de `ElementType`.

Le service lit désormais les noms par `Element.Name.GetValue(...)`.
Voir **BUG-PDV-024**.

**Correctif des libellés validé dans Revit 2025.4 le 5 octobre 2026.**


### Validation finale 04B — 2026-10-05

Validation utilisateur confirmée dans Revit 2025.4 / pyRevit 5.x.

Points validés :

- noms des types de zones remplies correctement affichés ;
- duplication de la vue source sans modification de l'original ;
- création de `PDV_<logement>_REP` ;
- gabarit optionnel appliqué uniquement à la copie ;
- création d'une **seule zone remplie globale** ;
- enveloppe continue du logement ;
- cloisons intérieures recouvertes par la surbrillance ;
- contour global issu du moteur géométrique de l'Étape 03 à marge nulle ;
- absence de rectangle de secours implicite.

**04B — Plan de repérage : VALIDÉ V1.**

Prochaine sous-étape : **04C — contrat de placement / ancrages**.


## Prototype 04C — Contrat de placement et ancrages

L'Étape 04 ne place toujours aucun élément sur une feuille. Elle définit
désormais un **contrat métier explicite** que l'Étape 07 utilisera pour
l'assemblage.

### Rôles stables

Chaque élément produit reçoit un rôle fonctionnel indépendant de son nom Revit :

| Élément | Rôle | Type de placement | Ancrage |
|---|---|---|---|
| Vue logement | `MainView` | `Viewport` | `main_view` |
| Plan de repérage | `LocationView` | `Viewport` | `location_view` |
| Nomenclature intérieure | `InteriorSchedule` | `Schedule` | `interior_schedule` |
| Nomenclature extérieure | `ExteriorSchedule` | `Schedule` | `exterior_schedule` |

Le nom Revit reste utile à l'utilisateur, mais il ne doit plus servir à deviner
le rôle lors de l'assemblage.

### Artefact de placement

Chaque résultat de création transporte désormais :

```text
HousingKey
Role
ElementUniqueId
ElementName
PlacementKind
AnchorKey
```

Le `UniqueId` Revit est utilisé dans le contrat courant plutôt qu'un
`ElementId` volatile.

Les services renvoient directement ces métadonnées au moment où ils créent
l'élément :

- vue logement → un artefact `MainView` ;
- plan de repérage → un artefact `LocationView` ;
- paire de nomenclatures → deux artefacts
  `InteriorSchedule` / `ExteriorSchedule`.

Cela évite qu'un futur contrôleur recherche des vues par préfixe de nom pour
déterminer leur fonction.

### Ancrages

Les ancrages de 04C sont des **identifiants sémantiques**, pas encore des
coordonnées papier.

```text
main_view
location_view
interior_schedule
exterior_schedule
```

L'Étape 07 associera ces identifiants aux coordonnées réelles d'un
**Modèle de plan de vente / feuille modèle**.

Aucune coordonnée XYZ n'est codée en dur dans l'Étape 04.

### Validation du contrat

`HousingPlacementContract` garantit pour un logement :

- un seul artefact par rôle ;
- un seul artefact par ancrage ;
- cohérence logement / rôle / type de placement / ancrage ;
- présence d'un `UniqueId` et d'un nom d'élément.

La persistance durable de `GeneratedBy`, `HousingKey`, `TemplateId` et
`Role` dans le projet Revit reste volontairement réservée à l'Étape 08.

**04C ne nécessite pas de validation graphique Revit**, car il n'effectue aucune
opération de placement ni transaction supplémentaire. Sa validation repose sur
les tests du contrat et sur les résultats déjà validés de 04A/04B.


## Clôture Étape 04 — 2026-10-05

L'Étape 04 est considérée comme terminée pour la V1.

### 04A — Nomenclatures

Validé dans Revit 2025.4 :

- duplication des modèles INT / EXT ;
- conservation de la mise en forme, tris et filtres métier ;
- filtre logement appliqué sur le paramètre choisi ;
- modèles source inchangés ;
- collisions bloquées.

### 04B — Plan de repérage

Validé dans Revit 2025.4 :

- vue source préservée ;
- gabarit optionnel ;
- type de zone remplie configurable ;
- une zone remplie globale ;
- cloisons intérieures recouvertes ;
- contour global fidèle au logement.

### 04C — Contrat de placement

Validé hors Revit :

- rôles stables ;
- `UniqueId` des éléments ;
- types de placement explicites ;
- ancrages sémantiques ;
- absence de coordonnées de feuille codées en dur ;
- contrôle des doublons de rôle/ancrage.

La suite Plans de vente compte **92 tests hors Revit réussis** au moment de cette
clôture.

**Étape 04 — Nomenclatures et repérage : VALIDÉE V1.**

Le placement réel sur feuille reste volontairement réservé à l'Étape 07.


## Ouverture Étape 05 — Étiquettes de pièces

Branche : `feature/plans-de-vente-stage05-room-tags`.

### Prototype 05A — placement automatique

La V1 propose un type de `RoomTagType` et une vue logement dépendante générée
par l'Étape 03.

L'API Revit 2025 vérifiée pour ce prototype est :

- `Document.Create.NewRoomTag(LinkElementId, UV, ElementId)` ;
- `Room.IsPointInRoom(XYZ)` ;
- `RoomTag.RoomTagType` ;
- `SpatialElementTag.TagHeadPosition`.

Le prototype ne place jamais les étiquettes dans la vue source ou dans un
`PDV MASTER`. Il cible uniquement une vue dépendante
`PDV PROTO - <logement> - ...`.

### Recherche du point intérieur

Pour chaque pièce :

1. lire le contour fini de la pièce ;
2. prendre la boucle extérieure la plus grande ;
3. calculer son centroïde géométrique ;
4. tester le centre de bounding box ;
5. conserver le point de localisation Revit comme autre candidat ;
6. générer une grille de candidats centrée sur la pièce ;
7. accepter uniquement les candidats pour lesquels
   `Room.IsPointInRoom(...)` est vrai.

Une fois l'étiquette créée, son emprise graphique réelle est vérifiée via son
bounding box dans la vue.

Le moteur privilégie :

```text
pas de collision
      +
bounding box entièrement dans la pièce
      +
position la plus centrale possible
```

Si aucune position ne permet de garder toute l'étiquette dans la pièce, le
centre reste obligatoirement intérieur à la pièce et un avertissement est
retourné.

### Anti-collision V1

Le prototype évite :

- les étiquettes de pièces déjà présentes dans la vue ;
- les étiquettes créées plus tôt dans le même logement.

Une marge graphique de sécurité de 10 mm est appliquée entre bounding boxes.

Le service accepte déjà une liste `exclusion_boxes`. L'Étape 06 pourra y
injecter les futures zones réservées aux cotations sans modifier le moteur de
placement des étiquettes.

La V1 bloque une nouvelle génération si une pièce du logement possède déjà une
étiquette dans la vue. La mise à jour / repositionnement d'étiquettes existantes
reste réservée à l'Étape 08.

### Validation Revit 2025.4 — à effectuer

1. créer ou sélectionner une vue logement dépendante ;
2. choisir un type d'étiquette ;
3. cliquer **Créer les étiquettes** ;
4. vérifier qu'une étiquette est créée pour chaque pièce du logement ;
5. vérifier le type d'étiquette ;
6. contrôler une pièce rectangulaire ;
7. contrôler une pièce en L ou concave ;
8. vérifier qu'une étiquette trop proche d'un bord est déplacée vers une autre
   position intérieure lorsque possible ;
9. vérifier que deux étiquettes ne se superposent pas lorsque des positions
   alternatives existent ;
10. relancer sur la même vue et vérifier que les doublons sont bloqués.

**Statut : VALIDÉ dans Revit 2025.4 le 7 octobre 2026.**


### Correctif Étape 05 — libellés des types d'étiquettes

Le premier essai Revit 2025.4 de l'Étape 05 a montré que les
`RoomTagType` étaient bien présents dans la ComboBox mais avec des lignes
vides.

Le service utilise désormais une lecture renforcée du nom de type et de famille
avec les paramètres système Revit `SYMBOL_NAME_PARAM` et
`SYMBOL_FAMILY_NAME_PARAM`, en complément de `Element.Name.GetValue`.

Voir **BUG-PDV-025**.

**À retester dans Revit 2025.4.**


#### Correctif renforcé BUG-PDV-025

Le premier correctif n'a pas suffi dans le projet réel : les éléments de la
ComboBox restaient présents mais sans texte.

La deuxième passe utilise explicitement `ALL_MODEL_TYPE_NAME` et
`ALL_MODEL_FAMILY_NAME`, normalise tous les textes et garantit en dernier
recours un libellé `Type d'étiquette #<ElementId>`.

L'interface indique également le nombre de types chargés.

**À retester dans Revit 2025.4.**


#### Correctif UI définitif — liste de chaînes simples

Après un deuxième essai réel, les types étaient bien chargés et disposaient
d'un libellé de secours, mais `DisplayMemberPath="Label"` continuait à produire
des lignes blanches dans WPF.

La ComboBox **Type étiquette** ne passe donc plus par un objet Python exposé au
binding WPF. Son `ItemsSource` est maintenant une liste de chaînes simples.
Le candidat Revit correspondant est retrouvé par l'index sélectionné.

Ce changement isole définitivement l'affichage du comportement de réflexion
IronPython/WPF.

**À retester dans Revit 2025.4.**


#### Correction racine du collector RoomTagType

Le compteur `0 type(s) d'étiquette disponible(s)` a permis d'isoler le
problème réel : le service utilisait `OfClass(RoomTagType)`.

Le collector est remplacé par :

```text
FamilySymbol
+ OST_RoomTags
+ WhereElementIsElementType
```

La validation du type sélectionné utilise également la classe parente
`FamilySymbol` et la catégorie `OST_RoomTags`.

L'interface distingue maintenant :

- une **erreur de collecte API**, dont le message est conservé et affiché ;
- un **vrai zéro**, signifiant qu'aucune famille d'étiquette de pièce n'est
  chargée dans le document hôte ;
- un nombre positif de types utilisables.

**À valider dans Revit 2025.4.**


#### Correctif création — collector des RoomTag existants

Après correction de la collecte des types, le premier clic sur
**Créer les étiquettes** a révélé le même piège API sur les instances :
`OfClass(RoomTag)` est refusé par Revit.

Le contrôle anti-doublon collecte désormais les instances via :

```text
SpatialElementTag
+ OST_RoomTags
+ WhereElementIsNotElementType
```

Voir **BUG-PDV-026**.

**À retester dans Revit 2025.4.**


#### Correctif runtime — service d'étiquettes rechargé

Un nouvel essai a montré le message de l'ancien `OfClass(RoomTag)` alors que
ce collector n'existait plus dans la branche active.

Pour supprimer toute ambiguïté entre code Git et code exécuté :

- `_existing_room_tags()` filtre désormais uniquement par
  `OST_RoomTags`, sans aucun `OfClass` ;
- `room_tag_service` est rechargé explicitement au lancement du bouton ;
- les erreurs affichent le build
  `stage05-room-tags-category-only-v3`.

Voir **BUG-PDV-027**.

**À retester dans Revit 2025.4.**


## Clôture Étape 05 — 2026-10-07

Validation utilisateur confirmée dans **Revit 2025.4 / pyRevit 5.x**.

Points validés :

- collecte des types d'étiquettes de pièces via `FamilySymbol + OST_RoomTags` ;
- affichage fiable des types dans la ComboBox ;
- création d'une étiquette par pièce dans la vue logement dépendante ;
- type d'étiquette choisi par l'utilisateur ;
- recherche de points intérieurs par `Room.IsPointInRoom(...)` ;
- repositionnement possible lorsque l'emprise déborde ou entre en collision ;
- anti-doublon sur les étiquettes déjà présentes ;
- tête d'étiquette maintenue dans le volume de la pièce avec le `probe_z` validé ;
- moteur validé : `stage05-room-tags-probe-z-v4`.

Le correctif final remplace la réutilisation de `TagHeadPosition.Z` par le
`probe_z` déjà contrôlé dans la pièce, puis revalide le point avant d'affecter
`TagHeadPosition`.

**Étape 05 — Étiquettes de pièces : VALIDÉE V1.**

La suite se poursuit avec **Étape 06 — Cotations**.

## Ouverture Étape 06 — Cotations

Branche de travail prévue : `feature/plans-de-vente-stage06-dimensions`.

Objectif V1 :

1. proposer un type de cote configurable ;
2. cibler une vue logement dépendante générée par Plans de vente ;
3. rechercher deux dimensions principales par pièce ;
4. privilégier les faces finies opposées ;
5. ignorer les petits décrochements qui ne décrivent pas la dimension générale ;
6. créer des cotes Revit associatives ;
7. préparer des zones d'exclusion réutilisables par le moteur d'étiquettes.

Le premier prototype 06A doit être volontairement testable sur des pièces
simples avant d'élargir la robustesse aux pièces en L, murs composés,
cloisons et murs non orthogonaux.


## Prototype 06A — Deux cotations principales

Implémentation préparée sur
`feature/plans-de-vente-stage06-dimensions`.

### Périmètre du premier prototype

Pour un logement sélectionné, l'interface propose :

- une vue logement dépendante `PDV PROTO - <logement> - ...` ;
- un type de cote linéaire du document ;
- l'action **Créer les cotations**.

Le prototype travaille sur les limites de pièce en
`SpatialElementBoundaryLocation.Finish`.

Pour chaque pièce, il :

1. conserve la boucle extérieure principale ;
2. conserve les segments droits portés par des murs ;
3. recherche sur ces murs la face latérale finie la plus proche via
   `HostObjectUtils.GetSideFaces(...)` ;
4. regroupe les limites par direction ;
5. écarte les micro-segments relativement à leur propre famille de direction ;
6. retient les deux paires de faces opposées les plus représentatives ;
7. crée deux cotes linéaires associatives avec des `Reference` Revit réelles.

La géométrie de sélection des deux axes est isolée dans
`lib/plans_vente/dimension_geometry.py` afin d'être testable hors Revit.

### Filtrage des petits décrochements

Le seuil est calculé par famille de directions et non par rapport au plus long
mur de la pièce.

Ce choix est important pour qu'un couloir très long conserve malgré tout sa
dimension transversale, tout en permettant d'écarter un petit segment de niche
ou de décrochement.

### Sécurité du prototype

Le prototype 06A est volontairement strict :

- uniquement des limites droites portées par des murs ;
- uniquement des faces latérales Revit exploitables comme références ;
- deux paires fiables obligatoires par pièce ;
- si une pièce du logement ne fournit pas deux axes fiables, la création est
  bloquée avant transaction ;
- les cotes sont créées dans une transaction courte commune.

Les arcs, séparateurs de pièces, poteaux et géométries atypiques seront élargis
après validation du contrat de base.

### Validation Revit 2025.4 — à effectuer

1. sélectionner un logement possédant une vue logement dépendante ;
2. choisir un type de cote linéaire ;
3. cliquer **Créer les cotations** ;
4. vérifier la création de **deux cotes par pièce** ;
5. vérifier que les cotes utilisent le type choisi ;
6. déplacer légèrement un mur et vérifier que la cote reste associative ;
7. vérifier que les références correspondent aux faces intérieures finies ;
8. tester une pièce rectangulaire ;
9. tester un couloir long et étroit ;
10. tester une pièce avec petit décrochement et vérifier que le décrochement ne
    devient pas la dimension principale.

**Statut : À valider dans Revit 2025.4.**


## Prototype 06B — Pièces non orthogonales et résultat partiel

Premier retour Revit 2025.4 du prototype 06A :

- les pièces rectangulaires produisent correctement leurs deux cotations ;
- les pièces qui ne fournissent pas deux familles de murs parallèles étaient refusées.

Le moteur 06B étend donc le comportement sans abandonner la priorité aux dimensions intérieures finies.

### Stratégie de cotation

Ordre de priorité par pièce :

```text
2 familles de faces parallèles fiables
        ↓
2 cotes entre faces finies

1 seule famille parallèle fiable
        ↓
1 cote entre faces finies
+
1 longueur dominante de mur en secours

aucune famille parallèle fiable
        ↓
jusqu'à 2 longueurs de murs dominantes,
sur des directions différentes
```

La cote de longueur de secours recherche d'abord des références d'extrémité Revit sur la courbe. Si elles ne sont pas disponibles, elle recherche les arêtes verticales de la face finie correspondant aux extrémités de la limite de pièce.

La ligne de cote est décalée vers l'intérieur de la pièce lorsque `Room.IsPointInRoom(...)` permet d'identifier le bon côté.

### Tolérance aux pièces atypiques

Une pièce atypique ne bloque plus la cotation du logement entier.

Chaque pièce est traitée dans une transaction courte indépendante. Le résultat distingue :

- pièce complète : 2 cotes ;
- pièce partielle : 1 cote ;
- pièce ignorée : 0 cote.

Les avertissements indiquent les pièces pour lesquelles une cote de secours n'a pas pu être créée.

### Validation Revit 2025.4 — à effectuer

1. reprendre le logement du premier test 06A ;
2. vérifier que les pièces rectangulaires conservent leurs deux cotes ;
3. vérifier qu'une pièce avec une seule paire de murs parallèles reçoit une cote entre faces et une cote de longueur ;
4. vérifier qu'une pièce sans paire parallèle tente deux longueurs dominantes ;
5. vérifier qu'une pièce non résolue ne bloque pas les autres pièces ;
6. contrôler visuellement que les longueurs correspondent bien aux limites finies attendues ;
7. déplacer un mur et vérifier l'associativité des cotes créées.

**Statut : À valider dans Revit 2025.4.**


## Correctif 06C — références d'extrémité et limite courbe

Retour Revit sur le logement B213 : 4 pièces analysées, 4 cotes créées,
2 pièces correctement cotées et 2 pièces sans cote.

Le plan de test met en évidence deux cas qui restaient mal traités :

- une pièce dont une limite extérieure est courbe ;
- une pièce non orthogonale avec mur biais.

Deux causes ont été corrigées.

### 1. Une paire parallèle ne nécessite pas quatre segments droits

Le moteur géométrique exigeait au minimum quatre segments droits avant de
chercher une paire parallèle. Cette contrainte était trop forte : une pièce
avec trois limites droites et une limite courbe peut parfaitement fournir
une paire de faces finies parallèles exploitable.

Le seuil est désormais ramené à deux segments exploitables.

### 2. Références d'extrémité réelles du mur

Les courbes issues de `Room.GetBoundarySegments(...)` ne fournissent pas
toujours des références d'extrémité utilisables pour une cote associative.

Le moteur recharge maintenant la géométrie native du mur avec
`Options.ComputeReferences = True`, retrouve la face latérale finie la plus
proche de la limite de pièce, puis extrait les références des arêtes
verticales de cette face.

Cette méthode fournit des références Revit réelles pour les cotes de
longueur de secours sur les pièces non orthogonales.

Build de test : `stage06c-dimensions-compute-references-v3`.

### Validation Revit 2025.4 — à effectuer

1. reprendre le logement B213 ;
2. vérifier que les deux pièces déjà correctes conservent leurs deux cotes ;
3. vérifier que la pièce avec limite courbe reçoit au moins la cote entre
   les deux faces parallèles restantes ;
4. vérifier que la pièce avec mur biais reçoit une cote de longueur de
   secours ;
5. vérifier que les cotes restent associatives après déplacement d'un mur.

**Statut : À retester dans Revit 2025.4.**


## Correctif 06D — lignes de séparation de pièces

Un essai sur un logement réel avec pièce extérieure a montré un défaut de
positionnement des cotations au droit des lignes de séparation de pièces.

Cause : le moteur 06C ne conservait comme limites cotables que les segments
portés par des murs. Les `BoundarySegment` produits par les lignes de
séparation étaient donc ignorés, ce qui faussait la géométrie disponible
pour rechercher la largeur / longueur principale de la pièce.

Le moteur 06D traite désormais les éléments de catégorie
`OST_RoomSeparationLines` comme de vraies limites de pièce pour la recherche
des dimensions principales.

Pour ces séparations :

- la géométrie du segment de pièce est conservée ;
- `GeometryCurve.Reference` est utilisée comme référence de cote ;
- la séparation peut former une paire parallèle avec un mur ou une autre
  séparation ;
- elle n'est pas utilisée comme longueur de secours, car la courbe Revit
  peut dépasser la portion réellement utilisée par la pièce.

Build de test : `stage06d-dimensions-room-separators-v4`.

### Validation Revit 2025.4 — à effectuer

1. reprendre le logement réel comportant une pièce extérieure ;
2. vérifier que les cotes se placent désormais sur les vraies limites de la
   pièce, y compris du côté des lignes de séparation ;
3. vérifier qu'une séparation parallèle à un mur opposé produit la largeur
   attendue ;
4. vérifier que les pièces intérieures déjà validées ne régressent pas ;
5. déplacer une ligne de séparation et contrôler l'associativité de la cote.

**Statut : À retester dans Revit 2025.4.**


## Correctif 06E — substitution séparateur par bord de sol

Retour Revit sur un logement réel : les cotes de terrasse deviennent
invisibles lorsque la catégorie des lignes de séparation de pièces est
masquée dans la vue.

Le moteur 06E conserve la ligne de séparation comme géométrie de repérage,
mais cherche d'abord une arête de sol réellement superposée à cette limite.

### Hiérarchie de référence

```text
Mur
→ face finie du mur

Séparation de pièce
→ rechercher une arête de sol parallèle, proche et suffisamment superposée
→ si trouvée : utiliser Edge.Reference du sol
→ sinon : conserver GeometryCurve.Reference de la séparation en dernier recours
```

### Contrôles de fiabilité

Le bord de sol candidat doit respecter :

- tolérance angulaire : 3° ;
- distance XY maximale : 20 mm ;
- recouvrement minimal avec la limite de pièce : 60 % ;
- sol porté par le même niveau en priorité ;
- recherche de secours seulement sur un niveau voisin à moins de 500 mm ;
- arête projetée minimale : 100 mm.

La géométrie des sols est rechargée avec `Options.ComputeReferences = True`
afin d'obtenir de vraies références Revit associatives.

Un cache par niveau évite de recalculer toutes les arêtes de sol pour chaque
pièce d'un logement.

Si aucune arête fiable n'est trouvée, le moteur conserve la référence de la
séparation et ajoute un avertissement indiquant que la cote peut disparaître
si cette catégorie est masquée dans la vue.

Build de test : `stage06e-dimensions-floor-edge-substitution-v5`.

### Validation Revit 2025.4 — à effectuer

1. reprendre un logement avec terrasse / balcon délimité par séparateurs ;
2. laisser les lignes de séparation invisibles dans la vue ;
3. vérifier que les cotes restent visibles quand une arête de sol coïncide ;
4. vérifier que la cote référence bien le bord du sol et non le séparateur ;
5. déplacer le bord du sol et contrôler l'associativité ;
6. vérifier qu'une séparation sans sol correspondant produit un avertissement ;
7. vérifier qu'aucune arête de sol proche mais non superposée n'est choisie.

**Statut : À retester dans Revit 2025.4.**

**Confirmation utilisateur du 8 octobre 2026 :** le moteur 06E
`stage06e-dimensions-floor-edge-substitution-v5` est validé dans Revit 2025.4,
y compris les pièces atypiques et les terrasses avec substitution par bord de
sol. Cette confirmation clôt la recette 06E ci-dessus ; elle ne valide pas 06F.

## Prototype 06F — Placement graphique des cotations

**Build :** `stage06f-dimensions-graphic-placement-v6`

**Branche :** `feature/plans-de-vente-stage06-dimensions`

**Statut :** tests hors Revit exécutés ; rendu Revit 2025.4 à valider.

### Périmètre et conservation du moteur 06E

06F ajoute le placement après sélection des références. Les paires de faces
finies, les longueurs dominantes de secours, les limites courbes partielles et
les références de séparateurs/bords de sols restent gérées par le code 06E.
Ses seuils 3° / 20 mm / 60 % / niveau voisin 500 mm, `ComputeReferences=True`
et le cache par niveau restent inchangés. Aucun séparateur n'est réaffiché.

Le service continue à viser deux cotes associatives par pièce. Il ne déplace
pas les RoomTag, ne change pas le texte natif du type sélectionné et n'écrit
ni `TextPosition` ni `ValueOverride`. La création vise exclusivement la vue
logement dépendante `PDV PROTO - <logement> - ...` validée par le service ;
aucun réglage de la vue source n'est modifié. Les annotations des vues
principales/dépendantes partagent toutefois le comportement natif Revit :
leur visibilité dans les autres vues doit être contrôlée pendant la recette.

### Placement et priorités

`plans_vente/dimension_positioning.py` contient la géométrie pure ;
`DimensionService` collecte les données Revit et crée les cotes après le choix.
Le contour de recherche inclut les limites tessellées, y compris courbes et
trous. La contenance est testée par `Room.IsPointInRoom` au `_probe_z(room)`
intérieur, jamais à l'altitude d'un texte ou d'une ligne d'annotation.

Pour chaque cote, dix translations parallèles au maximum sont proposées :
les deux côtés à marge nominale, à demi-marge, à quart de marge, trois
positions intermédiaires et la position 06E. La portée et les références
restent identiques. Les deux cotes sont comparées conjointement, dans cet ordre :

1. emprise intérieure aux points sondés ;
2. absence de collision avec les étiquettes ;
3. absence de collision avec les cotes existantes et les textes de la paire ;
4. absence de croisement graphique résiduel dans la paire ;
5. absence de collision avec les équipements ;
6. dégagement transversal au mur, puis ordre stable des candidats.

Les collisions utilisent des rectangles orientés et un test d'axes séparateurs,
pas seulement la grande boîte englobante XY d'une cote oblique. La comparaison
des boîtes et le contrat d'exclusion réutilisent `tag_positioning.boxes_overlap`.

**Limite géométrique explicite :** deux mesures complètes entre les murs opposés
d'un rectangle, perpendiculaires et toutes deux intérieures, se croisent
nécessairement. 06F éloigne ce croisement des textes et étiquettes puis signale
`croisement résiduel des cotes ou témoins`. Il ne supprime aucune mesure utile
pour masquer ce compromis. L'absence de croisement est recherchée lorsqu'elle
est possible, notamment pour des portées partielles dans des bras distincts.

### Distances papier et emprises

Les constantes sont dans `DimensionService` et se convertissent en unités
internes via `UnitUtils`, après multiplication par `View.Scale` :

| Constante | Distance papier | À 1:50 dans le modèle |
|---|---:|---:|
| `PAPER_CLEARANCE_MM` | 6 mm | 300 mm |
| `PAPER_TEXT_WIDTH_MM` | 12 mm | 600 mm |
| `PAPER_TEXT_HEIGHT_MM` | 3 mm | 150 mm |
| `PAPER_PADDING_MM` | 0,3 mm | 15 mm |
| `PAPER_WITNESS_MM` | 1,5 mm | 75 mm |

La largeur du texte est une **réservation estimée**. La réserve transversale
s'étend de la hauteur indiquée de chaque côté de la ligne, pour protéger le
texte natif et son espacement. Les deux orientations possibles (alignement
sur la cote / horizontal dans la vue) sont réservées. Les témoins de longueur
de secours relient les extrémités de référence à la ligne décalée ; les cotes
entre faces réservent des témoins courts aux extrémités.

Les familles/types avec grands préfixes, suffixes, texte déporté ou témoins
particuliers peuvent dépasser cette estimation. Après commit, la vraie
`get_BoundingBox(view)` enrichit les réservations ; son chevauchement avec une
étiquette déclenche un avertissement de contrôle, pas une correction du texte.
Cette boîte englobante peut être conservatrice, particulièrement en vue tournée.

Dans une petite pièce, les marges diminuent avant d'accepter un conflit.
Si aucun candidat propre n'existe, la meilleure position conserve la cote utile
et un avertissement identifie l'emprise extérieure ou la collision résiduelle.
Si l'API de placement échoue, la position 06E est conservée avec sa cause dans
le rapport. Une pièce non résolue ne bloque pas les suivantes.

### Obstacles et coordination avec l'Étape 05

Une collecte par catégorie dans la vue cible récupère les boîtes visibles des
RoomTag (`OST_RoomTags`, sans `OfClass(RoomTag)`), des cotes existantes et des
équipements du document hôte : appareils sanitaires, mobilier, agencements,
équipements mécaniques, spécialisés et électriques. Les éléments explicitement
masqués et catégories masquées sont exclus ; les erreurs de collecte et boîtes
indisponibles sont signalées. Les équipements des liens ne sont pas collectés
par ce prototype. Les boîtes sont transformées en XY modèle avec leurs huit
coins ; elles ne sont pas supposées alignées sur les axes écran.

`DimensionCreationResult.exclusion_boxes` est une liste de tuples
`(min_x, min_y, max_x, max_y)` en **XY modèle, unités internes Revit**. Elle
contient uniquement les cotes des transactions réussies : emprises estimées
(ligne découpée, texte, témoins) plus boîte native lorsqu'elle est disponible.
Elle est compatible avec l'argument `exclusion_boxes` de l'Étape 05. La liste
est renvoyée au contrôleur, sans persistance ni déplacement automatique des
étiquettes ; l'orchestration de mise à jour complète reste à l'Étape 08.

### Performance et limites du prototype

Par cote : au plus dix candidats, 23 sondes de ligne/texte et six sondes de
marge par candidat ; les coordonnées répétées sont mises en cache par pièce.
Pour la paire : au plus 100 comparaisons géométriques pures, sans appel Revit
supplémentaire. Aucun objet temporaire Revit n'est créé. Les réservations des
cotes effectivement créées sont réutilisées pour les pièces suivantes et pour
les tentatives de secours après un échec de création.

Cet échantillonnage borné n'est pas une preuve de contenance de chaque point
d'une ligne ou de son texte : un très petit trou entre deux sondes peut être
manqué. Les contacts nécessaires des extrémités/témoins avec la référence ne
sont pas assimilés à une cote extérieure. Le rendu natif et le temps total,
y compris collecte de géométrie Revit, doivent être validés sur le modèle.

L'étape reste une **création**, sans mécanisme de remplacement des anciennes
cotes : ne pas relancer sur une vue déjà cotée pour comparer 06E et 06F.
Utiliser une copie de test du modèle et annuler la création précédente avant
chaque nouvel essai, en contrôlant les vues dépendantes partageant les annotations.

### Tests hors Revit exécutés le 8 octobre 2026

- Référence avant modification : 133 tests Plans de vente réussis.
- 17 nouveaux tests de géométrie : rectangle, croisement inévitable / évitable,
  étiquette centrale, petite pièce, pièce impossible, couloir, L, biais,
  terrasse, décrochement, côté libre, trou, limite courbe, témoins,
  budget et hiérarchie des priorités.
- 12 nouveaux tests du vrai service avec frontières Revit simulées : identité
  des références de sol, avertissement séparateur, probe Z à l'étage, retour
  06E sur erreur, longueur de secours, rollback, pièce suivante, échelle,
  emprise native, transformation de boîte, seuils 06E et collecte par catégorie.
  Le contrat de rechargement du module et l'absence de mutations du texte sont
  également vérifiés dans cette suite.
- Suite complète hors Revit : **445 tests réussis** avec :

```bash
PYTHONPATH=OutilsTAA.extension/lib python -m pytest tests -q --import-mode=importlib
```

Ces tests ne constituent pas une validation Revit, WPF ou IronPython réels.

### Premier test Revit 2025.4 — checklist exacte

1. Ouvrir une copie de test du modèle contenant un logement déjà validé en 06E.
   Recharger pyRevit après récupération Git. Vérifier le libellé **Étape 06F**.
2. Choisir la vue logement `PDV PROTO - <logement> - ...`, échelle **1:50**,
   portant les étiquettes 05 validées, sans anciennes cotes 06 dans cette zone.
   Conserver le même type de cote que pour le test 06E.
3. Laisser les séparateurs de pièces **masqués**, lancer **Créer les cotations**
   une seule fois et chronométrer. Vérifier dans le rapport le build
   `stage06f-dimensions-graphic-placement-v6`, les comptes et les avertissements.
4. Contrôler une pièce rectangulaire, une chambre et le séjour : deux mesures
   utiles, lignes intérieures, textes lisibles, aucune superposition avec les
   étiquettes ; un croisement nu inévitable doit être signalé et éloigné des textes.
5. Contrôler WC/SDB et couloir : marges réduites si nécessaire, équipements
   évités quand une autre place existe, aucune cote utile supprimée sans diagnostic.
6. Contrôler une pièce en L, un mur biais et une limite courbe partielle :
   les mesures restent sur les bonnes références, hors décrochements parasites ;
   inspecter aussi les témoins et les petits trous entre sondes.
7. Contrôler la terrasse : cotes visibles avec séparateurs masqués, références
   sur les bords de sol superposés ; conserver l'avertissement si seul le
   séparateur est disponible. Ne pas réafficher les séparateurs pour contourner le test.
8. Déplacer légèrement un mur coté puis un bord de sol coté dans la copie :
   vérifier la mise à jour associative des mesures, puis annuler ces déplacements.
9. Vérifier que les étiquettes n'ont pas bougé et que les réglages de la vue
   source sont inchangés. Contrôler la visibilité native des annotations dans
   la vue principale et les autres vues dépendantes.
10. Noter le temps sur un logement de **10 à 15 pièces**, le nombre de cotes
    comparé à 06E et les avertissements ; transmettre une capture du plan et
    du rapport. La réactivité réelle est un critère de validation, pas déduite des pytest.

**Validation suivante :** rejouer à 1:100 après annulation des cotes de test,
puis sur une vue tournée et un logement à l'étage. Contrôler particulièrement
les types de cote à texte large et les équipements provenant de liens.

## Correctif 06F.1 — Largeurs des entrées et couloirs

**Build :** `stage06f-circulation-widths-v7`

**Retour utilisateur du 8 octobre 2026 :** version 06F v6 acceptée sur A003,
à l'exception de l'entrée/dégagement en L. La capture du rapport indique
12 pièces analysées, 24 cotes créées et aucune pièce sans cote. Le retour
« sinon tout est bon » valide le rendu général ; les avertissements du rapport
restent des diagnostics, sans prétendre que chaque collision a été vérifiée.

### Règle ciblée

- Pour les pièces nommées **entrée, couloir, dégagement ou circulation**, y
  compris `Entrée/Dgt`, coter la largeur locale du passage. Reconnaissance par
  mots entiers, sans tenir compte des accents, de la casse ou des séparateurs ;
  abréviations acceptées : `Dgt`, `Dgtmt`, `Degt`.
- Dans une circulation en L : rechercher une largeur dans chaque direction,
  entre les faces finies qui bordent effectivement chaque branche.
- Dans un couloir droit : une largeur utile suffit. Le compteur « pièces avec
  1 cote » est normal pour ce cas ; aucune longueur n'est ajoutée pour atteindre
  artificiellement deux cotes et aucun avertissement de cote manquante n'est émis.
- Les chambres, séjours, sanitaires, cuisines, celliers et extérieurs gardent
  la sélection 06E et le placement 06F déjà validés. La forme allongée seule
  ne transforme pas une pièce en circulation.

### Sélection et placement

Le moteur pur `circulation_width_pairs` utilise les mêmes limites et les mêmes
références Revit collectées par 06E. Deux supports doivent être parallèles à 5°
près et se recouvrir longitudinalement sur une distance au moins égale à la
largeur mesurée. Les seuils de filtrage sont **600 mm de largeur** et **300 mm
minimum de recouvrement** ; ce sont des paramètres géométriques du prototype,
pas des seuils réglementaires. Ils écartent notamment les petits renfoncements.
Le classement favorise les passages dont le support longitudinal est long
relativement à leur largeur ; une seule paire est retenue par direction.

La contenance est sondée sur cinq sections, avec sept points transversaux,
au Z intérieur de la pièce. Il faut au moins deux sections voisines valides.
La recherche contrôle au maximum 40 paires (1 400 sondes, points répétés en
cache) et renvoie au plus deux largeurs. L'échantillonnage conserve les limites
connues de 06F pour de très petits trous ou décrochements entre deux sondes.

Chaque paire expose une plage locale `placement_points` issue des sections
valides. L'optimiseur 06F choisit sa position dans cette plage, tout en vérifiant
la contenance réelle et les obstacles. Il ne translate pas la cote vers l'autre
bras du L. Le choix final utilise toujours les vraies références associatives,
sans remplacer les mesures par du texte.

Si aucune largeur fiable n'est identifiée, ou si sa création échoue, le rapport
signale le problème et invite à une cotation manuelle ; le moteur ne réintroduit
pas la longueur générale comme secours. Un autre nom de pièce non reconnu
continue à utiliser la règle générale. Une entrée très courte/irrégulière dont
les supports sont fragmentés peut donc nécessiter un contrôle manuel.

### Vérification

Suite complète hors Revit : **475 tests réussis** (30 cas supplémentaires),
commande inchangée :

```bash
PYTHONPATH=OutilsTAA.extension/lib PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q --import-mode=importlib
```

Recette Revit 2025.4 à effectuer pour v7 :

1. Dans la copie de test A003, annuler la précédente création de cotes avant
   de relancer, afin de ne pas superposer deux générations. Conserver les tags,
   le type de cote et l'échelle 1:50 ; recharger pyRevit.
2. Lancer une seule création et vérifier le build `stage06f-circulation-widths-v7`.
3. Dans `Entrée/Dgt`, vérifier deux cotes transversales mesurant chacune la
   largeur réelle d'un bras du L, à la place des grandes longueurs ; contrôler
   le positionnement entre les bonnes faces finies et la lisibilité.
4. Vérifier un couloir droit : une cote de largeur, sans longueur générale.
5. Vérifier que chambres, séjour et loggia conservent leurs mesures et leur
   placement ; laisser les séparateurs masqués.
6. Déplacer légèrement un mur bordant l'entrée : vérifier la mise à jour de
   sa largeur, puis annuler. Transmettre une capture de l'entrée et du rapport.

**Statut :** correctif testé hors Revit ; validation réelle v7 encore attendue.


## Correctif 06F.2 — Priorité à la largeur locale

**Build :** `stage06f-circulation-widths-v8`

Retour Revit du 8 octobre 2026 : le correctif v7 reconnaît bien
`Entrée/Dgt` comme circulation, mais sélectionne encore les grandes portées
générales (ex. environ 2,67 m et 3,23 m) au lieu des largeurs locales des deux
bras.

### Cause

Le moteur classait les paires parallèles principalement avec le ratio
`recouvrement / largeur`. Dans une entrée/dégagement ouverte, une grande portée
peut rester entièrement dans la pièce et obtenir un meilleur ratio qu'une
largeur locale de passage. Elle était donc retenue avant la vraie largeur.

### Correction

Pour les pièces reconnues comme circulation, les candidats fiables sont
désormais testés par **largeur croissante**. Les seuils existants restent
inchangés :

- largeur minimale : 600 mm ;
- recouvrement minimal : 300 mm ;
- recouvrement au moins égal à la largeur ;
- faces parallèles à 5° près ;
- validation par `Room.IsPointInRoom` sur plusieurs sections ;
- une seule largeur par direction.

Le ratio `recouvrement / largeur` sert uniquement à départager des candidats
de largeur proche ; il ne peut plus faire gagner une grande portée générale.

Un test de régression reproduit explicitement le cas où une portée de 2,70 m
était préférée à une largeur locale de 1,20 m.

### Recette Revit 2025.4

1. Reprendre exactement la même vue de test A003.
2. Supprimer les cotes créées par v7.
3. Recharger pyRevit et vérifier le build
   `stage06f-circulation-widths-v8`.
4. Relancer les cotations.
5. Vérifier que `Entrée/Dgt` reçoit les largeurs locales des bras et non les
   portées générales de 2,67 m / 3,23 m.
6. Vérifier qu'un couloir droit conserve une seule largeur.
7. Contrôler que les autres pièces ne régressent pas.

**Statut : À valider dans Revit 2025.4.**


## Correctif 06F.3 — Détection géométrique des formes L/T

**Build :** `stage06f-branched-geometry-v9`

Retour Revit du 8 octobre 2026 : la stratégie spéciale basée sur les noms
`Entrée`, `Dgt`, `Couloir`, etc. ne décrit pas correctement le besoin
métier. Le nombre de dimensions doit dépendre de la **forme réelle de la pièce**
et non de son libellé.

### Nouvelle règle

- pièce simple / quasi rectangulaire : **2 cotes principales** ;
- pièce en L prononcé : typiquement **4 cotes utiles** ;
- pièce en T prononcé : typiquement **4 à 5 cotes utiles** ;
- autre forme concave prononcée : jusqu'à **5 cotes locales** ;
- petit décrochement ou niche : rester sur le moteur simple à 2 cotes.

Le nom de la pièce n'intervient plus dans le choix du moteur. Une chambre en L
et une entrée en L sont donc traitées de la même manière ; un couloir
rectangulaire reste une pièce simple.

### Détection de la forme

Le moteur pur reconstruit le contour fermé à partir des segments de limite puis
mesure :

1. le nombre d'**angles rentrants** ;
2. l'aire réelle du contour ;
3. l'aire de la boîte orientée selon la plus longue limite ;
4. le ratio d'aire manquante.

Une forme n'est classée L/T que si elle possède au moins un angle rentrant et
si le ratio d'aire manquante est supérieur ou égal à **12 %**. Ce seuil est un
paramètre géométrique du prototype, pas une règle réglementaire.

Cette combinaison évite qu'un petit décrochement transforme artificiellement
une pièce presque rectangulaire en pièce complexe.

### Génération des dimensions locales

Pour une forme L/T prononcée, le moteur recherche toutes les paires de limites
parallèles crédibles :

- parallélisme à 5° près ;
- dimension minimale : 600 mm ;
- recouvrement minimal : 300 mm ;
- validation de plusieurs sections par `Room.IsPointInRoom` ;
- références Revit existantes conservées ;
- maximum : 5 dimensions.

Plusieurs paires dans une même direction peuvent être conservées. Sur un L
orthogonal typique, cela permet d'obtenir :

- largeur du premier bras ;
- largeur du second bras ;
- portée générale du premier axe ;
- portée générale du second axe.

Les séparateurs de pièces, substitutions par bords de sols et faces finies du
moteur 06E restent inchangés.

### Placement graphique

Le moteur de placement 06F accepte désormais jusqu'à cinq cotes dans une même
pièce. Pour une ou deux cotes, l'optimisation exhaustive historique est
conservée. Au-delà, un choix glouton borné minimise successivement :

1. sortie de la pièce ;
2. collisions avec étiquettes ;
3. collisions avec les cotes existantes ;
4. collisions texte / autres cotes ;
5. croisements graphiques ;
6. équipements ;
7. proximité aux limites.

Cela évite une explosion de type `10^5` combinaisons pour cinq dimensions.

### Comptage du résultat

Une pièce est maintenant considérée **complètement cotée** lorsque le nombre de
cotes réellement créées atteint le nombre attendu par son moteur géométrique :

- 2/2 pour une pièce simple ;
- 4/4 ou 5/5 pour une pièce L/T selon le cas.

Le rapport ne parle donc plus systématiquement de « pièce avec 2 cotes ».

### Tests hors Revit

Les tests ajoutés couvrent notamment :

- rectangle simple ;
- petit décrochement ;
- L prononcé ;
- T prononcé ;
- L tourné ;
- indépendance vis-à-vis du nom de pièce ;
- création réelle simulée de 4 cotes sur un L ;
- placement de 4 cotes ;
- limite maximale à 5 dimensions ;
- retour partiel `3/4` si une référence échoue.

Le workflow Plans de vente est vert avec **201 tests** sur la suite
`tests/plans_vente`.

### Recette Revit 2025.4

1. supprimer les anciennes cotes de la vue de test ;
2. recharger pyRevit ;
3. vérifier le build `stage06f-branched-geometry-v9` ;
4. relancer sur le même logement ayant une entrée/dégagement en L ;
5. vérifier que la pièce reçoit environ 4 cotes décrivant réellement ses deux
   branches ;
6. vérifier qu'une chambre ou autre pièce en L reçoit le même traitement ;
7. vérifier qu'un simple couloir rectangulaire reçoit 2 cotes ;
8. vérifier qu'un petit décrochement reste ignoré ;
9. vérifier une pièce en T si disponible ;
10. déplacer un mur de branche et contrôler l'associativité.

**Statut : À valider dans Revit 2025.4.**


## Correctif 06F.4 — contour complet indépendant des références

**Build :** `stage06f-branched-full-contour-v10`

Retour Revit du 8 octobre 2026 : le build v9 produisait encore seulement les
deux grandes cotes sur l'entrée/dégagement réelle, malgré sa géométrie
visiblement concave.

### Cause

Le v9 tentait de reconnaître la forme L/T à partir de
`_room_boundary_candidates`. Or cette liste ne contient que les limites qui
ont déjà passé le filtre de **référence Revit cotable** :

- face finie de mur disponible ;
- séparateur exploitable ;
- bord de sol substituable ;
- courbe compatible.

Sur un logement réel, cette liste peut être incomplète ou ne plus former un
contour fermé, même si `Room.GetBoundarySegments(...)` décrit parfaitement
la géométrie de la pièce. La détection L/T retombait alors sur le moteur simple
à deux cotes.

### Correction v10

Deux géométries sont désormais séparées :

1. **Contour complet de forme**
   - extrait directement de `Room.GetBoundarySegments` en finition ;
   - conserve toutes les limites ;
   - tesselle également les courbes ;
   - sert uniquement à reconnaître L/T et la concavité.

2. **Limites cotables**
   - conservent les références Revit validées par 06E ;
   - servent uniquement à créer les dimensions associatives.

Une fois la forme complexe confirmée par le contour complet, le moteur recherche
les 3 à 5 paires utiles parmi les limites réellement cotables sans exiger que
celles-ci reforment à elles seules un contour fermé.

### Tests

Un test de régression reproduit explicitement :

- un contour complet en L ;
- un sous-ensemble de références Revit incomplet / non fermé ;
- la détection L/T sur le premier ;
- la génération de plusieurs dimensions sur le second.

Le workflow Plans de vente est vert avec **203 tests**.

### Recette Revit 2025.4

1. récupérer le build `stage06f-branched-full-contour-v10` ;
2. supprimer les cotes créées par v9 ;
3. relancer exactement sur le même logement ;
4. vérifier que l'entrée/dégagement ne retombe plus à 2 grandes cotes ;
5. vérifier la présence de l'avertissement
   `forme L/T prononcée détectée (... cote(s) locale(s))` ;
6. contrôler visuellement les 3 à 5 cotes obtenues avant d'affiner leur sélection.

**Statut : À valider dans Revit 2025.4.**


## Décision V1 — Deux cotations principales maximum

**Build :** `stage06f-two-principal-dimensions-v11`

Retour de production du 8 octobre 2026 : les essais de cotation automatique
spécifique aux circulations puis aux formes L/T ont montré qu'une recherche de
3 à 5 dimensions locales augmente fortement la complexité du moteur et peut
produire trop de cotes sur les logements atypiques.

Pour la V1, la règle est donc simplifiée :

- **2 cotes principales maximum par pièce** ;
- dimensions générales prioritaires ;
- faces finies et références associatives conservées ;
- substitution séparateur / bord de sol conservée ;
- placement intérieur 06F conservé ;
- aucune logique spéciale selon le nom de la pièce ;
- aucune détection L/T utilisée dans le flux Revit ;
- les cotes complémentaires sont ajoutées manuellement par l'utilisateur.

Cette décision privilégie la rapidité, la lisibilité et la stabilité de
production. L'utilisateur garde la responsabilité de la relecture finale et
peut supprimer ou compléter les cotes proposées.

Les moteurs expérimentaux de circulation et de formes L/T ont été retirés du
code actif et de la suite de tests V1.

### Recette Revit 2025.4

1. récupérer le build `stage06f-two-principal-dimensions-v11` ;
2. supprimer les anciennes cotes d'essai ;
3. relancer la cotation sur un logement simple puis sur un logement atypique ;
4. vérifier qu'aucune pièce ne reçoit plus de 2 cotes ;
5. vérifier que les terrasses conservent les références aux bords de sols ;
6. vérifier l'associativité après déplacement d'un mur ;
7. confirmer que le temps de calcul est meilleur ou au minimum stable.

**Statut : À valider dans Revit 2025.4.**
