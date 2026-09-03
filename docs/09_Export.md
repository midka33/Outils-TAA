# Outils TAA – Outil Export

**Version :** 1.2  
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
12. système de modèles de nommage des livrables ;
13. nettoyage et sécurisation des noms ;
14. suivi de progression ;
15. gestion des erreurs ;
16. rapport final de publication.

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
Formats + nommage + destination
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
Formats + nommage + destination
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
Formats + nommage + destination
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

Le nom du PDF est généré à partir du **modèle de nommage actif**. Si aucun modèle spécifique n'est configuré, le comportement par défaut reste le nom du carnet après nettoyage.

Le système de nommage est décrit à la section 10.

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

Le système de nommage doit pouvoir être réutilisé ultérieurement pour les DWG, mais la V1 expose prioritairement les modèles de nommage pour les PDF combinés.

---

## 10. Système de modèles de nommage

### 10.1 Objectif

Export doit permettre à l'utilisateur de définir **comment les fichiers produits sont nommés**, sans imposer une convention unique.

Le système doit notamment permettre de construire le nom d'un PDF combiné à partir de données issues :

- du **projet Revit** ;
- de la **feuille / mise en page Revit** ;
- du **carnet de publication** ;
- du **paramètre utilisé pour constituer le carnet** ;
- de paramètres personnalisés disponibles dans le modèle.

Exemple :

```text
{Projet:NuméroProjet}_{Carnet}_{Feuille:Phase}_{Feuille:Indice}
```

peut produire :

```text
23045_DCE_ARCHITECTE_DCE_A.pdf
```

Le nommage doit être déterministe et reproductible.

### 10.2 Principe des modèles

Un modèle est une combinaison de **texte fixe** et de **variables**.

Exemple :

```text
{Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet}_{Projet:NomProjet}
```

Le modèle est enregistré comme une configuration de publication et peut être réutilisé.

Le système doit éviter que l'utilisateur ait à connaître la syntaxe interne des variables : l'interface doit proposer une liste de paramètres insérables.

### 10.3 Sources de données disponibles

Les variables sont réparties par portée.

#### Projet

Valeurs provenant des informations du projet Revit, par exemple :

```text
{Projet:NomProjet}
{Projet:NuméroProjet}
{Projet:Adresse}
```

La liste exacte dépend des paramètres réellement disponibles dans le projet.

#### Feuille / mise en page

Valeurs provenant de la `ViewSheet` utilisée pour le carnet, par exemple :

```text
{Feuille:Numéro}
{Feuille:Nom}
{Feuille:Phase}
{Feuille:Indice}
```

L'interface doit également pouvoir proposer les paramètres personnalisés accessibles sur les feuilles.

#### Carnet

Valeurs propres au carnet :

```text
{Carnet}
{Carnet:Nom}
{Carnet:Source}
```

#### Paramètre de regroupement

Pour un carnet automatique :

```text
{ParamètreCarnet}
```

Cette variable correspond à la valeur qui a servi à constituer le carnet.

Pour un carnet manuel, elle reste vide ou non disponible.

### 10.4 Gestion des paramètres de feuille dans un PDF combiné

Un PDF combiné contient plusieurs feuilles. Un paramètre de feuille peut donc avoir des valeurs différentes d'une feuille à l'autre.

Export ne doit **jamais choisir silencieusement la première valeur rencontrée**.

Lorsqu'une variable provenant des feuilles est utilisée dans le nom d'un PDF combiné :

```text
Toutes les feuilles ont la même valeur
        ↓
Valeur utilisée
```

ou :

```text
Les feuilles ont des valeurs différentes
        ↓
CONFLIT
        ↓
L'utilisateur doit résoudre le conflit
```

La résolution peut notamment consister à :

- utiliser une autre variable ;
- modifier le modèle ;
- homogénéiser les valeurs des feuilles ;
- remplacer la variable par une valeur fixe.

Le comportement par défaut doit privilégier la sécurité plutôt qu'un résultat potentiellement faux.

### 10.5 Paramètres absents ou vides

Si une variable n'existe pas dans le contexte courant ou si sa valeur est vide, Export doit l'identifier explicitement.

Selon le type de variable, l'outil peut :

- signaler une erreur bloquante avant publication ;
- proposer une valeur de remplacement ;
- utiliser une valeur par défaut explicitement configurée.

Il ne doit pas générer un nom ambigu sans avertissement.

### 10.6 Nettoyage du résultat

Après résolution du modèle, le résultat final passe systématiquement par `FilenameService`.

Le service doit gérer :

- caractères interdits Windows ;
- espaces en début ou fin ;
- noms réservés Windows ;
- longueur excessive ;
- caractères spéciaux ;
- séparateurs indésirables ;
- collisions avec des fichiers existants.

Le nettoyage ne doit pas modifier silencieusement une variable avant sa résolution ; il intervient sur le **nom final**.

### 10.7 Extension du fichier

L'extension `.pdf` est ajoutée par le service d'export et ne doit pas être saisie dans le modèle.

Exemple :

```text
Modèle : {Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet}
Résultat : 23045_DCE_DCE.pdf
```

### 10.8 Prévisualisation

L'interface doit afficher un **aperçu du nom produit** avant publication.

Exemple :

```text
Modèle
[ {Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet} ]

Aperçu
23045_DCE_ARCHITECTE_DCE.pdf
```

L'aperçu doit être calculé sur le carnet sélectionné et permettre de détecter immédiatement les variables absentes ou en conflit.

### 10.9 Modèles enregistrés

Les modèles de nommage peuvent être enregistrés et réutilisés.

Exemple :

```text
Modèles

● TAA – Standard PDF
  {Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet}

○ Dossier consultation
  {Projet:NuméroProjet}_{Carnet}_DCE

○ Publication client
  {Projet:NomProjet}_{Carnet}_{Projet:NuméroProjet}
```

La configuration du modèle peut être associée à une publication ou conservée comme préférence réutilisable.

### 10.10 Architecture du nommage

La logique de génération doit être séparée de l'export PDF.

Architecture cible :

```text
PublicationSet
      ↓
FilenameTemplateService
      ↓
Résolution des variables
      ↓
Détection des conflits / valeurs absentes
      ↓
FilenameService
      ↓
Nom de fichier sécurisé
      ↓
PdfExportService
```

`FilenameTemplateService` est responsable de la compréhension du modèle et de la résolution des variables.

`FilenameService` reste responsable de la sécurité du nom final.

`PdfExportService` ne doit pas contenir de logique de nommage métier.

---

## 11. Organisation et nommage

La destination sélectionnée constitue la racine de publication.

Le nommage doit garantir :

- lisibilité ;
- compatibilité Windows ;
- suppression des caractères interdits ;
- gestion des espaces ;
- gestion des noms réservés ;
- comportement déterministe ;
- gestion des collisions.

La logique de sécurisation doit être isolée dans un `FilenameService` et ne doit pas être dupliquée dans les services PDF/DWG.

La génération des noms à partir d'un modèle relève de `FilenameTemplateService`.

La V1 privilégie la sécurité : ne pas écraser silencieusement un livrable existant.

---

## 12. Interface utilisateur

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

La configuration du nommage doit être accessible sans alourdir l'interface principale.

Concept V1 :

```text
┌──────────────────────────────────────────────────────┐
│ EXPORT                                               │
│ Gestion et publication des carnets                   │
│                                                      │
│ CARNETS                                              │
│                                                      │
│ Paramètre : [ Sous-titre                    ▼ ]      │
│                                                      │
│ ☑ PRO                 Automatique   24 feuilles     │
│ ☑ DCE                 Automatique   18 feuilles     │
│ ☐ APS                 Automatique   12 feuilles     │
│                                                      │
│ ★ DCE Architecte    Manuel enregistré  5 feuilles   │
│ ⚠ Ancien carnet      1 élément manquant              │
│                                                      │
│ [ + Nouveau carnet ] [ Modifier ] [ Supprimer ]     │
│                                                      │
│ FORMATS                                              │
│ ☑ PDF                 ☑ DWG                          │
│                                                      │
│ NOM DU PDF                                           │
│ [ {Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet} ]│
│ [ Insérer un paramètre ▼ ]                           │
│ Aperçu : 23045_DCE_DCE.pdf                           │
│                                                      │
│ DESTINATION                                          │
│ [ D:\Projet\Exports                       ] [ ... ] │
│                                                      │
│ Annuler                                   [ EXPORTER ]│
└──────────────────────────────────────────────────────┘
```

L'utilisateur doit pouvoir :

1. choisir un modèle existant ;
2. créer/modifier un modèle ;
3. insérer un paramètre projet ;
4. insérer un paramètre de feuille/mise en page ;
5. insérer une information du carnet ;
6. insérer la valeur du paramètre de regroupement ;
7. visualiser un aperçu ;
8. enregistrer le modèle pour une utilisation ultérieure.

L'interface de création/modification d'un carnet manuel doit permettre la sélection multiple des feuilles et leur affichage dans l'ordre de publication.

---

## 13. Progression et erreurs

La publication doit afficher une progression compréhensible : nombre d'éléments, carnet ou feuille en cours, étape PDF/DWG et erreurs éventuelles.

Avant l'export PDF, les modèles de nommage doivent être validés pour tous les carnets sélectionnés.

Les erreurs doivent être remontées explicitement : dossier inaccessible, chemin invalide, fichier existant, échec PDF/DWG, feuille invalide, paramètre absent, valeur vide, conflit de paramètre de feuille, élément manquant d'un carnet enregistré, erreur Revit ou annulation utilisateur.

Une erreur ne doit pas être masquée.

---

## 14. Résultat de publication

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

## 15. Architecture cible

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
│   ├── publication_result.py
│   └── filename_template.py
├── services/
│   ├── export_service.py
│   ├── sheet_service.py
│   ├── view_service.py
│   ├── publication_builder_service.py
│   ├── publication_storage_service.py
│   ├── pdf_export_service.py
│   ├── dwg_export_service.py
│   ├── filename_template_service.py
│   └── filename_service.py
└── README.md
```

### Responsabilités principales

**SheetService** : collecte les feuilles et expose les paramètres utilisables pour le regroupement et le nommage.

**ViewService** : gère les vues lorsque leur prise en charge est nécessaire.

**PublicationBuilderService** : construit un carnet depuis un paramètre ou une sélection manuelle et produit une collection normalisée de `PublicationItem`.

**PublicationStorageService** : enregistre, charge, met à jour et supprime les carnets persistants ; il gère également la résolution des éléments enregistrés et le signalement des éléments manquants.

**FilenameTemplateService** : interprète un modèle de nommage, résout les variables selon leur portée, détecte les valeurs absentes et les conflits et produit le nom logique du livrable.

**FilenameService** : nettoie et sécurise le nom final avant écriture sur disque.

**PdfExportService** : utilise l'API PDF native de Revit et produit le PDF du carnet à partir du nom fourni par le système de nommage.

**DwgExportService** : exporte une feuille en DWG et applique les paramètres centralisés.

**ExportService** : orchestre validation, résolution des carnets, validation du nommage, export, progression et résultat.

L'interface ne contient pas la logique métier.

---

## 16. Modèles métier

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
filename_template_id
```

Représente un carnet de publication. Un carnet persistant peut être réutilisé sans reconstruire sa sélection.

### `FilenameTemplate`

```text
id
name
template
scope
extension
fallback_policy
```

Représente un modèle de nommage enregistré.

Exemple :

```text
id : taa_standard_pdf
name : TAA – Standard PDF
template : {Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet}
scope : PDF_COMBINED
extension : pdf
fallback_policy : ERROR
```

Le modèle doit être indépendant du service d'export afin de pouvoir être réutilisé pour d'autres livrables à terme.

---

## 17. Persistance

Les carnets manuels persistants doivent être enregistrés séparément des simples préférences d'interface.

Les modèles de nommage enregistrés doivent également être persistants afin d'être réutilisables d'une publication à l'autre.

La persistance doit notamment pouvoir conserver :

```text
PublicationSet
  ├── id
  ├── name
  ├── source
  ├── items
  ├── persistent
  └── filename_template_id

FilenameTemplate
  ├── id
  ├── name
  ├── template
  ├── scope
  └── fallback_policy
```

Le système doit permettre de modifier un modèle sans modifier rétroactivement les fichiers déjà publiés.

Une publication utilise la configuration du modèle au moment de son exécution.

---

## 18. Tests

### Carnets

Tester :

- même valeur de paramètre ;
- valeurs différentes ;
- valeur vide ;
- espaces ;
- caractères spéciaux ;
- carnet manuel ;
- persistance ;
- élément manquant ;
- résolution après modification du projet.

### PDF

Tester :

- un carnet ;
- plusieurs carnets ;
- carnet vide ;
- une feuille ;
- plusieurs feuilles ;
- modèle par défaut ;
- modèle avec paramètres projet ;
- modèle avec paramètres de feuille ;
- modèle avec paramètre de regroupement ;
- conflit entre valeurs de feuilles ;
- paramètre absent ;
- valeur vide ;
- caractères interdits ;
- nom réservé Windows ;
- longueur excessive ;
- collision avec un fichier existant ;
- réutilisation d'un modèle enregistré ;
- interruption de publication.

### DWG

Tester :

- une feuille ;
- plusieurs feuilles ;
- plusieurs carnets ;
- création des dossiers ;
- nommage ;
- caractères spéciaux ;
- fichier existant ;
- échec d'export.

### `FilenameTemplateService`

Tester notamment :

```text
{Carnet}
{Projet:NuméroProjet}
{Feuille:Numéro}
{ParamètreCarnet}
```

et les cas :

- variable inconnue ;
- variable vide ;
- paramètre absent ;
- plusieurs valeurs différentes dans un carnet ;
- modèle vide ;
- texte fixe uniquement ;
- caractères interdits ;
- collision ;
- modèle valide mais résultat invalide après résolution.

### `PublicationResult`

Tester :

```text
success
exported_pdf_count
exported_dwg_count
skipped_count
errors
output_directory
```

### Revit / pyRevit

Les tests d'intégration doivent couvrir :

- collecte réelle des feuilles ;
- lecture des paramètres projet ;
- lecture des paramètres de feuille ;
- lecture du paramètre de regroupement ;
- résolution des carnets persistants ;
- export PDF ;
- export DWG ;
- transactions lorsque nécessaires.

### Interface

Tester :

- ouverture ;
- fermeture ;
- paramètres obligatoires ;
- sélection des carnets ;
- création/modification d'un modèle ;
- insertion d'un paramètre ;
- aperçu du nom ;
- affichage des conflits ;
- bouton d'export actif/inactif ;
- progression ;
- annulation ;
- erreurs ;
- persistance des réglages.

### Validation manuelle

Pour chaque publication :

- vérifier que le PDF est lisible ;
- vérifier l'ordre des feuilles ;
- vérifier le nom du PDF ;
- vérifier que les valeurs affichées dans le nom correspondent au projet ;
- vérifier que les DWG sont correctement générés ;
- vérifier l'arborescence de sortie.

---

## 19. Scénarios d'acceptation

### Scénario A – Carnet automatique

L'utilisateur choisit un paramètre Revit.

Export crée les carnets correspondant aux différentes valeurs.

Le PDF de chaque carnet est nommé selon le modèle sélectionné.

### Scénario B – Carnet manuel persistant

L'utilisateur crée `DCE Architecte`, sélectionne cinq feuilles et enregistre le carnet.

Lors d'une nouvelle ouverture d'Export, le carnet est toujours disponible.

### Scénario C – Paramètre projet dans le nom

Le modèle est :

```text
{Projet:NuméroProjet}_{Carnet}
```

Le projet possède `NuméroProjet = 23045`.

Le carnet `DCE Architecte` produit :

```text
23045_DCE Architecte.pdf
```

### Scénario D – Paramètre de feuille homogène

Le modèle est :

```text
{Carnet}_{Feuille:Phase}
```

Toutes les feuilles du carnet possèdent `Phase = DCE`.

Résultat :

```text
DCE Architecte_DCE.pdf
```

### Scénario E – Conflit de paramètre de feuille

Le modèle utilise `{Feuille:Phase}` mais les feuilles du carnet contiennent `DCE`, `PRO` et `APS`.

Export détecte le conflit et bloque la publication tant que l'utilisateur n'a pas choisi une solution.

### Scénario F – Paramètre de regroupement

Le carnet a été créé automatiquement avec `Sous-titre`.

Le modèle utilise :

```text
{Projet:NuméroProjet}_{ParamètreCarnet}
```

Le carnet `DCE` produit :

```text
23045_DCE.pdf
```

### Scénario G – Modèle enregistré

L'utilisateur crée le modèle `TAA – Standard PDF`, l'enregistre, ferme Export puis le réutilise lors d'une publication ultérieure.

### Scénario H – Élément manquant

Un carnet persistant contient une feuille supprimée du projet.

Export signale l'élément manquant avant la publication et ne le retire pas silencieusement du carnet.

---

## 20. Principes de conception à respecter

1. **Le paramètre `Sous-titre` n'est jamais obligatoire.**
2. **Un carnet manuel persistant doit être réutilisable.**
3. **Un carnet est une configuration ; une publication est une exécution.**
4. **Le nommage est configurable et ne doit pas être codé en dur.**
5. **Les paramètres projet et feuille peuvent être utilisés dans les modèles de nommage.**
6. **Un conflit de valeurs de feuille ne doit jamais être résolu silencieusement.**
7. **Le nettoyage du nom final reste centralisé dans `FilenameService`.**
8. **La résolution du modèle reste séparée de l'export PDF/DWG.**
9. **Les configurations persistantes doivent être indépendantes des préférences visuelles de l'interface.**
10. **Le résultat doit être déterministe, explicite et reproductible.**

---

## 21. Résumé

Export doit fournir un workflow de publication proche de la philosophie du Publisher d'Archicad, adapté à Revit.

Le système repose sur :

```text
Sources de publication
        ↓
Carnets automatiques ou manuels
        ↓
Carnets persistants réutilisables
        ↓
PublicationItem[]
        ↓
Modèle de nommage
        ↓
Résolution des paramètres
        ↓
Sécurisation du nom
        ↓
PDF + DWG
        ↓
Rapport de publication
```

Le nom du PDF n'est donc plus limité au nom du carnet. Il peut être construit à partir d'un **modèle configurable**, utilisant les informations du projet Revit, des feuilles/mises en page, du carnet et du paramètre ayant servi à créer le carnet.

Cette architecture permet de faire évoluer ultérieurement le même système de nommage vers les DWG, les dossiers, les sous-dossiers ou d'autres formats de publication sans remettre en cause le moteur de publication.
