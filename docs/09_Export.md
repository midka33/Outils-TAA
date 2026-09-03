# Outils TAA – Outil Export

**Version :** 1.1  
**Statut :** Spécification fonctionnelle de référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Année :** 2026

---

## 1. Objectif

**Export** est l'outil de publication des documents Revit des **Outils TAA**.

Son objectif est de proposer dans Revit un fonctionnement proche du **Publisher d'Archicad** : préparer une publication, organiser des carnets, sélectionner les carnets à produire, lancer l'export et obtenir une arborescence de fichiers cohérente et reproductible.

> **Export n'est pas seulement un exporteur PDF/DWG : c'est un gestionnaire de publications.**

---

## 2. Principe général

Un **carnet de publication** est une collection persistante ou temporaire de documents à publier.

Export doit proposer deux méthodes principales pour constituer un carnet :

1. **Automatique par paramètre** : l'utilisateur choisit lui-même le paramètre Revit servant au regroupement. `Sous-titre` peut être proposé comme valeur par défaut selon les conventions TAA, mais ne doit jamais être imposé par le code.
2. **Sélection manuelle** : l'utilisateur crée un carnet et sélectionne directement les feuilles et, lorsque le périmètre le permet, les vues à publier.

Ces deux méthodes doivent produire le même objet métier `PublicationSet`. Le moteur de publication ne doit pas dépendre de la manière dont le carnet a été créé.

Exemple de regroupement automatique :

```text
Paramètre choisi : Phase de publication

A101 → PRO
A102 → PRO
A103 → DCE
A104 → DCE
A105 → APS
```

Résultat :

```text
PRO → A101, A102
DCE → A103, A104
APS → A105
```

---

## 3. Philosophie Publisher

L'expérience recherchée s'inspire du Publisher d'Archicad :

- publications organisées en carnets ;
- documents regroupés dans chaque carnet ;
- carnets enregistrables et réutilisables ;
- réglages reproductibles ;
- sélection des carnets à publier ;
- noms et dossiers prévisibles ;
- publication relançable rapidement ;
- résultat clairement identifiable ;
- erreurs explicitement signalées.

L'objectif n'est pas de reproduire l'interface d'Archicad à l'identique, mais d'en reprendre les **principes de workflow** adaptés à Revit.

---

## 4. Carnets de publication

### 4.1 Carnet automatique par paramètre

L'utilisateur peut choisir le paramètre Revit utilisé pour constituer les carnets.

Le service doit pouvoir proposer les paramètres pertinents des feuilles, notamment les paramètres texte exploitables pour un regroupement.

Exemple :

```text
Paramètre : Sous-titre

DCE → A101, A102, A103
PRO → A201, A202
```

Le paramètre `Sous-titre` est une **convention de projet**, pas une contrainte structurelle de l'outil.

### 4.2 Carnet manuel

L'utilisateur peut créer un carnet manuellement en :

1. donnant un nom au carnet ;
2. sélectionnant les feuilles et/ou vues à publier ;
3. enregistrant le carnet ;
4. le réutilisant lors des publications suivantes.

Un carnet manuel enregistré est un **objet persistant**. Il ne doit pas être recréé à chaque lancement d'Export.

Exemple :

```text
Carnet : DCE Architecte
Source : Sélection manuelle

A101
A102
A103
A201
A301
```

Lors d'une publication ultérieure, l'utilisateur peut simplement sélectionner `DCE Architecte` et relancer l'export.

### 4.3 Carnet manuel temporaire

L'utilisateur peut également constituer une sélection ponctuelle sans l'enregistrer.

Ce mode est destiné aux publications exceptionnelles et ne crée pas de configuration persistante.

### 4.4 Réutilisation et évolution du projet

Les carnets manuels persistants doivent pouvoir être réutilisés même lorsque le modèle Revit a évolué.

Il ne faut donc pas dépendre exclusivement d'un `ElementId`, susceptible de ne plus être valable. Les éléments d'un carnet doivent conserver des identifiants et métadonnées permettant leur résolution ultérieure, notamment :

```text
unique_id
sheet_id
élément_type
sheet_number
sheet_name
```

Lors du chargement d'un carnet :

```text
Élément enregistré
        ↓
Recherche dans le modèle courant
        ↓
Élément retrouvé ?
   ├── Oui → valide
   └── Non → élément manquant
```

Un élément introuvable doit être signalé explicitement à l'utilisateur. Il ne doit jamais disparaître silencieusement du carnet.

L'interface doit permettre d'identifier les éléments manquants et, à terme, de mettre à jour le carnet enregistré.

### 4.5 Carnet = configuration, publication = exécution

La création d'un carnet et son export sont deux responsabilités distinctes.

```text
Carnet enregistré
      ↓
Résolution des éléments
      ↓
PublicationItem[]
      ↓
Moteur de publication
      ↓
PDF + DWG
```

Le moteur de publication reçoit une collection normalisée de `PublicationItem`. Il ne doit pas avoir à connaître l'origine du carnet : paramètre, sélection manuelle ou autre méthode future.

---

## 5. Périmètre fonctionnel V1

La première version doit couvrir :

1. détection des feuilles ;
2. choix par l'utilisateur du paramètre de regroupement ;
3. création automatique de carnets par valeur de paramètre ;
4. création manuelle de carnets par sélection ;
5. enregistrement et réutilisation des carnets manuels ;
6. détection des éléments manquants dans les carnets persistants ;
7. affichage et sélection des carnets ;
8. choix du dossier de destination ;
9. export d'un PDF combiné par carnet ;
10. export d'un DWG par feuille ;
11. création d'un dossier par carnet pour les DWG ;
12. nettoyage et sécurisation des noms ;
13. suivi de progression ;
14. gestion des erreurs ;
15. rapport final de publication.

La V1 doit rester volontairement simple et fiable.

---

## 6. Workflow

### Création automatique

```text
Ouverture d'Export
        ↓
Choix du paramètre
        ↓
Lecture des feuilles
        ↓
Regroupement par valeur
        ↓
Carnets proposés
        ↓
Sélection des carnets
        ↓
Formats + destination
        ↓
Publication
```

### Création manuelle

```text
Ouverture d'Export
        ↓
Nouveau carnet
        ↓
Nom du carnet
        ↓
Sélection des feuilles / vues
        ↓
Enregistrement du carnet
        ↓
Formats + destination
        ↓
Publication
```

### Réutilisation

```text
Carnets enregistrés
        ↓
Sélection d'un carnet
        ↓
Résolution des éléments
        ↓
Vérification des éléments manquants
        ↓
Formats + destination
        ↓
Publication
```

L'utilisateur doit pouvoir comprendre ce qui va être publié avant de lancer l'opération.

---

## 7. Carnets et documents

Un carnet peut contenir des feuilles (`ViewSheet`) et l'architecture doit permettre d'étendre ultérieurement la prise en charge des vues (`View`).

Pour la V1, la publication PDF/DWG est prioritairement centrée sur les **feuilles Revit**, car elles correspondent au concept de mise en page destiné à la publication.

L'ordre des feuilles dans un PDF doit être déterministe ; par défaut, il est basé sur le numéro de feuille Revit.

Les valeurs utilisées pour les noms de carnets contenant des espaces ou caractères spéciaux doivent être nettoyées pour pouvoir être utilisées comme noms de fichiers et dossiers.

Une feuille sans valeur pour le paramètre sélectionné doit être identifiée explicitement. Elle ne doit jamais disparaître silencieusement.

---

## 8. Export PDF

La V1 produit **un PDF combiné par carnet**.

Exemple :

```text
Exports/
├── PRO.pdf
├── DCE.pdf
└── APS.pdf
```

L'export doit utiliser en priorité le **moteur PDF natif de Revit** et ne doit pas dépendre inutilement d'un logiciel PDF externe.

Le nom du PDF est dérivé du nom du carnet après nettoyage.

Un carnet vide ne doit pas générer silencieusement un PDF vide ; il est signalé dans le rapport.

---

## 9. Export DWG

La V1 produit **un DWG par feuille**.

Les DWG sont regroupés dans un dossier portant le nom du carnet :

```text
Exports/
├── PRO/
│   ├── A101.dwg
│   └── A102.dwg
├── DCE/
│   ├── A103.dwg
│   └── A104.dwg
└── APS/
    └── A105.dwg
```

Les paramètres DWG doivent être centralisés. La préférence fonctionnelle retenue pour Export est **DWG True Color**.

---

## 10. Organisation et nommage

La destination sélectionnée constitue la racine de publication.

Le nommage doit garantir :

- lisibilité ;
- compatibilité Windows ;
- suppression des caractères interdits ;
- gestion des espaces ;
- gestion des noms réservés ;
- comportement déterministe ;
- gestion des collisions.

La logique doit être isolée dans un `FilenameService` et ne doit pas être dupliquée dans les services PDF/DWG.

La V1 privilégie la sécurité : ne pas écraser silencieusement un livrable existant.

---

## 11. Interface utilisateur

L'interface respecte les **UI Guidelines Outils TAA** :

- WPF ;
- simple ;
- claire ;
- rapide ;
- prévisible ;
- peu de paramètres inutiles ;
- accent TAA **RGB (250, 100, 31) / #FA641F**.

L'interface doit permettre de distinguer clairement :

- les carnets automatiques ;
- les carnets manuels enregistrés ;
- les carnets manuels temporaires ;
- les éléments manquants d'un carnet enregistré.

Concept V1 :

```text
┌─────────────────────────────────────────────────┐
│ EXPORT                                          │
│ Gestion et publication des carnets              │
│                                                 │
│ CARNETS                                         │
│                                                 │
│ Paramètre : [ Sous-titre              ▼ ]       │
│                                                 │
│ ☑ PRO                 Automatique   24 feuilles │
│ ☑ DCE                 Automatique   18 feuilles │
│ ☐ APS                 Automatique   12 feuilles │
│                                                 │
│ ★ DCE Architecte    Manuel enregistré  5 feuilles│
│ ⚠ Ancien carnet      1 élément manquant         │
│                                                 │
│ [ + Nouveau carnet ] [ Modifier ] [ Supprimer ]│
│                                                 │
│ FORMATS                                         │
│ ☑ PDF                 ☑ DWG                     │
│                                                 │
│ DESTINATION                                     │
│ [ D:\Projet\Exports                  ] [ ... ] │
│                                                 │
│ Annuler                              [ EXPORTER ]│
└─────────────────────────────────────────────────┘
```

L'interface de création/modification d'un carnet manuel doit permettre la sélection multiple des feuilles et leur affichage dans l'ordre de publication.

---

## 12. Progression et erreurs

La publication doit afficher une progression compréhensible : nombre d'éléments, carnet ou feuille en cours, étape PDF/DWG et erreurs éventuelles.

Les erreurs doivent être remontées explicitement : dossier inaccessible, chemin invalide, fichier existant, échec PDF/DWG, feuille invalide, paramètre absent, valeur vide, élément manquant d'un carnet enregistré, erreur Revit ou annulation utilisateur.

Une erreur ne doit pas être masquée.

---

## 13. Résultat de publication

Le résultat est représenté par `PublicationResult` et expose au minimum :

```text
success
exported_pdf_count
exported_dwg_count
skipped_count
errors
output_directory
```

Exemple :

```text
Publication terminée
PDF exportés : 3
DWG exportés : 54
Éléments ignorés : 1
Erreurs : 0
Destination : D:\Projet\Exports
```

---

## 14. Architecture cible

Export respecte la séparation **UI / logique métier / accès Revit**.

```text
Export.pushbutton/
├── script.py
├── ui/
│   ├── export_window.xaml
│   ├── export_window.py
│   ├── publication_editor.xaml
│   └── publication_editor.py
├── models/
│   ├── publication_set.py
│   ├── publication_item.py
│   ├── publication_source.py
│   └── publication_result.py
├── services/
│   ├── export_service.py
│   ├── sheet_service.py
│   ├── view_service.py
│   ├── publication_builder_service.py
│   ├── publication_storage_service.py
│   ├── pdf_export_service.py
│   ├── dwg_export_service.py
│   └── filename_service.py
└── README.md
```

### Responsabilités principales

**SheetService** : collecte les feuilles et expose les paramètres utilisables pour le regroupement.

**ViewService** : gère les vues lorsque leur prise en charge est nécessaire.

**PublicationBuilderService** : construit un carnet depuis un paramètre ou une sélection manuelle et produit une collection normalisée de `PublicationItem`.

**PublicationStorageService** : enregistre, charge, met à jour et supprime les carnets persistants ; il gère également la résolution des éléments enregistrés et le signalement des éléments manquants.

**FilenameService** : nettoie et sécurise les noms.

**PdfExportService** : utilise l'API PDF native de Revit et produit le PDF du carnet.

**DwgExportService** : exporte une feuille en DWG et applique les paramètres centralisés.

**ExportService** : orchestre validation, résolution des carnets, export, progression et résultat.

L'interface ne contient pas la logique métier.

---

## 15. Modèles métier

### `PublicationItem`

```text
unique_id
sheet_id
item_type
sheet_number
sheet_name
parameter_value
```

Représente un document publiable et les informations nécessaires à sa résolution.

### `PublicationSource`

```text
mode
parameter_name
parameter_value
```

Représente l'origine du carnet :

- `PARAMETER` ;
- `MANUAL` ;
- éventuellement `TEMPORARY` pour une sélection non enregistrée.

### `PublicationSet`

```text
id
name
items
source
output_directory
persistent
```

Représente un carnet de publication. Un carnet persistant peut être réutilisé d'une publication à l'autre.

### `PublicationResult`

```text
success
exported_pdf_count
exported_dwg_count
skipped_count
errors
output_directory
```

Représente le résultat de publication.

---

## 16. Persistance des carnets

Les carnets manuels enregistrés doivent être stockés via un mécanisme de persistance adapté à Export, distinct de la logique d'export elle-même.

La persistance doit conserver au minimum :

- identifiant du carnet ;
- nom ;
- mode/source ;
- éléments sélectionnés ;
- identifiants permettant leur résolution ;
- métadonnées utiles à l'affichage et au diagnostic.

Les carnets automatiques par paramètre peuvent être recalculés à partir du modèle et n'ont pas nécessairement besoin d'être stockés comme des sélections figées.

Les carnets manuels enregistrés, eux, doivent rester disponibles entre deux publications.

Le stockage ne doit pas modifier silencieusement le modèle Revit.

---

## 17. API commune et Revit

Export doit réutiliser les composants existants de `lib/common` lorsqu'ils couvrent le besoin : logger, settings, dialogs, revit_utils, file_utils, collector_utils, progress et exceptions.

La publication est principalement une opération de lecture et d'export. Les transactions Revit ne doivent être utilisées que lorsqu'elles sont réellement nécessaires.

---

## 18. Paramètres persistants

Les paramètres utiles peuvent être conservés via le système `settings` commun, notamment :

- dernier dossier de destination ;
- derniers formats sélectionnés ;
- paramètre de regroupement choisi ;
- préférences d'affichage si pertinent.

Les carnets manuels enregistrés constituent une persistance métier distincte : ils doivent être gérés par `PublicationStorageService` et non confondus avec les simples préférences d'interface.

---

## 19. IA

Export ne nécessite pas d'intelligence artificielle.

Les opérations de regroupement, résolution, nommage, sélection, export et organisation sont déterministes et doivent rester basées sur des règles explicites.

---

## 20. Tests

Les tests suivent `docs/08_Testing.md` et couvrent notamment :

### Regroupement automatique

- paramètre `Sous-titre` ;
- autre paramètre texte valide ;
- paramètre identique, différent ou vide ;
- espaces et caractères spéciaux ;
- paramètre indisponible.

### Carnets manuels

- création d'un carnet ;
- sélection d'une ou plusieurs feuilles ;
- enregistrement ;
- rechargement lors d'une publication ultérieure ;
- modification ;
- suppression ;
- carnet temporaire non enregistré ;
- élément supprimé ou introuvable ;
- résolution à partir des identifiants persistants ;
- signalement explicite des éléments manquants.

### Publication

- un ou plusieurs carnets ;
- PDF combiné ;
- DWG par feuille ;
- création des dossiers ;
- noms invalides ;
- fichiers existants ;
- dossiers absents ;
- erreurs et annulation ;
- progression et interface ;
- validation réelle des PDF et DWG dans Revit.

---

## 21. Critères d'acceptation V1

### Scénario automatique

```text
Modèle Revit 2025.4
        ↓
Choix d'un paramètre
        ↓
Regroupement automatique
        ↓
Sélection des carnets
        ↓
PDF + DWG
        ↓
Publication
        ↓
1 PDF combiné par carnet
        ↓
1 DWG par feuille
        ↓
1 dossier DWG par carnet
        ↓
Rapport final cohérent
```

### Scénario manuel

```text
Modèle Revit 2025.4
        ↓
Nouveau carnet
        ↓
Sélection manuelle des feuilles
        ↓
Enregistrement
        ↓
Publication
        ↓
Nouvelle ouverture d'Export
        ↓
Sélection du même carnet
        ↓
Résolution des feuilles
        ↓
Publication à nouveau
```

Le carnet manuel doit être réutilisable sans refaire la sélection des feuilles.

Si une feuille du carnet n'existe plus, Export doit signaler précisément l'élément manquant avant publication.

Aucune feuille sélectionnée ne doit disparaître silencieusement et aucun fichier ne doit être produit dans un emplacement inattendu.

---

## 22. Évolutions possibles

Après validation de la V1, pourront être ajoutés :

- PDF individuel par feuille ;
- sélection individuelle plus avancée ;
- profils de publication enregistrés ;
- conventions de nommage avancées ;
- plusieurs destinations ;
- paramètres DWG avancés ;
- fusion DWG de plusieurs feuilles ;
- carnet basé sur d'autres critères ;
- historique des publications ;
- journal détaillé ;
- réexécution des éléments en erreur ;
- mise à jour assistée des éléments manquants d'un carnet manuel ;
- synchronisation ou partage des carnets entre utilisateurs/projets si un besoin est confirmé.

Ces fonctions ne doivent pas complexifier inutilement la V1.

---

## 23. Terminologie officielle

Le nom utilisateur officiel de l'outil est :

> **Export**

Les anciennes références à **PublisherAI** dans les documents historiques doivent progressivement être remplacées par **Export**. Le nouveau code et l'interface utilisateur doivent utiliser exclusivement le nom **Export**.

---

## 24. Résumé

```text
                    ┌─────────────────────┐
                    │ Modèle Revit        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              ↓                                 ↓
    Paramètre choisi                    Sélection manuelle
              ↓                                 ↓
    Carnets automatiques                Carnet manuel
                                                ↓
                                          Enregistrement
                                                ↓
                                      Réutilisation ultérieure
              └────────────────┬────────────────┘
                               ↓
                     PublicationSet
                               ↓
                    PublicationItem[]
                               ↓
                       PDF + DWG
                               ↓
                    Nommage / Organisation
                               ↓
                         Rapport final
```

La priorité est donnée à la **fiabilité**, à la **simplicité d'utilisation**, à la **reproductibilité**, à la **persistance des carnets manuels** et à la **compatibilité Revit 2025.4 / pyRevit 5.x**.
