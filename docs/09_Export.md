# Outils TAA – Outil Export

**Version :** 1.4  
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

Le paramètre `Sous-titre` est une **convention de projet**, pas une contrainte structurelle de l'outil.

### 4.2 Carnet manuel

L'utilisateur peut créer un carnet manuellement en donnant un nom, en sélectionnant les feuilles et/ou vues à publier, puis en enregistrant le carnet.

Un carnet manuel enregistré est un **objet persistant** et peut être réutilisé lors des publications suivantes.

### 4.3 Carnet manuel temporaire

L'utilisateur peut constituer une sélection ponctuelle sans l'enregistrer.

### 4.4 Réutilisation et évolution du projet

Les carnets manuels persistants doivent pouvoir être réutilisés même lorsque le modèle Revit a évolué.

Les éléments doivent conserver des identifiants et métadonnées permettant leur résolution ultérieure, notamment `unique_id`, `sheet_id`, `élément_type`, `sheet_number` et `sheet_name`.

Un élément introuvable doit être signalé explicitement à l'utilisateur.

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

---

## 5. Périmètre fonctionnel V1

La première version doit couvrir :

1. détection des feuilles ;
2. choix par l'utilisateur du paramètre de regroupement ;
3. création automatique de carnets par valeur de paramètre ;
4. création manuelle de carnets par sélection ;
5. enregistrement et réutilisation des carnets manuels ;
6. détection des éléments manquants ;
7. affichage et sélection des carnets ;
8. choix du dossier de destination ;
9. export PDF combiné par carnet ;
10. export PDF séparé par feuille ;
11. export DWG combiné par carnet ;
12. export DWG séparé par feuille ;
13. création automatique des dossiers nécessaires ;
14. système de modèles de nommage ;
15. nettoyage et sécurisation des noms ;
16. suivi de progression ;
17. gestion des erreurs ;
18. rapport final de publication.

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
Formats + modes + nommage + destination
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
Formats + modes + nommage + destination
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
Formats + modes + nommage + destination
        ↓
Publication
```

---

## 7. Carnets et documents

Un carnet peut contenir des feuilles (`ViewSheet`) et l'architecture doit permettre d'étendre ultérieurement la prise en charge des vues (`View`).

Pour la V1, la publication PDF/DWG est prioritairement centrée sur les **feuilles Revit**, car elles correspondent au concept de mise en page destiné à la publication.

L'ordre des feuilles doit être déterministe ; par défaut, il est basé sur le numéro de feuille Revit.

Une feuille sans valeur pour le paramètre sélectionné doit être identifiée explicitement.

---

## 8. Export PDF

La V1 propose deux modes de publication PDF :

- **PDF combiné** : un seul PDF contenant toutes les feuilles du carnet ;
- **PDF séparés** : un PDF par feuille du carnet.

### 8.1 PDF combiné

```text
Exports/
├── PRO.pdf
├── DCE.pdf
└── APS.pdf
```

### 8.2 PDF séparés

```text
Exports/
├── PRO/
│   ├── A101.pdf
│   ├── A102.pdf
│   └── A103.pdf
└── DCE/
    ├── A201.pdf
    └── A202.pdf
```

Les dossiers nécessaires sont créés automatiquement lorsque l'option est activée.

### 8.3 Nommage

Les deux modes PDF utilisent le même système de modèles de nommage.

Pour un PDF combiné, les variables de feuille doivent avoir une valeur homogène dans le carnet ; sinon un conflit est signalé.

Pour un PDF séparé, les variables de feuille sont évaluées sur la feuille concernée.

### 8.4 Moteur PDF

L'export utilise en priorité le **moteur PDF natif de Revit** et ne dépend pas inutilement d'un logiciel PDF externe.

Un carnet vide est signalé et ne génère pas silencieusement un PDF vide.

---

## 9. Export DWG

La V1 propose deux modes de publication DWG :

- **DWG combiné** : un seul fichier DWG pour plusieurs feuilles du carnet ;
- **DWG séparés** : un fichier DWG par feuille.

### 9.1 Faisabilité API Revit 2025.4

L'API Revit 2025 expose :

```csharp
Document.Export(
    string folder,
    string name,
    ICollection<ElementId> views,
    DWGExportOptions options)
```

Cette méthode accepte une **collection de plusieurs vues** dans un même appel. Toutes les vues doivent être valides et exportables. citeturn0search0turn0search8

`DWGExportOptions` expose également :

```csharp
bool MergedViews { get; set; }
```

Cette propriété indique si les vues doivent être fusionnées dans un seul fichier via des XRefs et elle est disponible dans l'API Revit 2025.x. citeturn0search7turn0search13

**Conclusion : le DWG combiné est techniquement réalisable dans la V1.**

### 9.2 Définition du DWG combiné

Export doit distinguer deux notions :

1. **plusieurs vues/feuilles envoyées dans un même appel d'export** ;
2. **fusion des vues via `MergedViews`**, qui peut s'appuyer sur des XRefs.

Le second comportement est celui que l'API Revit documente explicitement comme une fusion de vues. citeturn0search13

Export ne doit pas promettre une reproduction exacte d'un fichier AutoCAD multi-layout tant que le comportement réel n'a pas été validé sur les feuilles du projet.

La V1 doit donc définir le **DWG combiné** comme un livrable unique issu de plusieurs feuilles/vues Revit, avec le comportement de fusion déterminé par les options Revit sélectionnées.

### 9.3 DWG combiné par carnet

```text
Carnet DCE
├── A101
├── A102
├── A103
└── A104
        ↓
Document.Export(..., [A101, A102, A103, A104], options)
        ↓
DCE.dwg
```

Le nom du fichier est généré par le système de modèles de nommage.

### 9.4 DWG séparés

```text
Exports/
├── DCE/
│   ├── A101.dwg
│   ├── A102.dwg
│   └── A103.dwg
└── PRO/
    ├── A201.dwg
    └── A202.dwg
```

Ce mode utilise un appel d'export par feuille.

### 9.5 Paramètres DWG Revit

Revit 2025 expose `ExportDWGSettings`, qui stocke dans le document Revit des configurations DWG/DXF enregistrées. L'API permet notamment de lister les configurations et de récupérer leurs `DWGExportOptions`. citeturn0search6turn0search9

Export doit privilégier la **réutilisation des configurations DWG enregistrées dans Revit** plutôt que de dupliquer leurs paramètres.

La préférence fonctionnelle retenue pour Export reste **DWG True Color**, sous réserve de la configuration Revit sélectionnée.

### 9.6 Validation

Avant un DWG combiné, Export vérifie que toutes les feuilles/vues sont exportables. L'API indique que les vues doivent être imprimables/exportables. citeturn0search0

### 9.7 Création des dossiers

Le dossier transmis à `Document.Export` doit exister. Export crée donc les dossiers nécessaires avant l'appel API. citeturn0search0

### 9.8 Nommage

Le système de nommage est utilisable pour les DWG combinés et séparés.

Pour un DWG combiné, les variables de feuille suivent les mêmes règles de conflit que pour un PDF combiné.

---

## 10. Système de modèles de nommage

### 10.1 Objectif

Export permet de définir comment les fichiers produits sont nommés, sans imposer une convention unique.

Le système permet de construire les noms à partir du projet Revit, de la feuille/mise en page, du carnet, du paramètre de regroupement et des paramètres personnalisés disponibles.

### 10.2 Principe

Un modèle combine texte fixe et variables.

```text
{Projet:NuméroProjet}_{Carnet}_{ParamètreCarnet}
```

### 10.3 Sources

Projet :

```text
{Projet:NomProjet}
{Projet:NuméroProjet}
{Projet:Adresse}
```

Feuille :

```text
{Feuille:Numéro}
{Feuille:Nom}
{Feuille:Phase}
{Feuille:Indice}
```

Carnet :

```text
{Carnet}
{Carnet:Nom}
{Carnet:Source}
```

Regroupement :

```text
{ParamètreCarnet}
```

### 10.4 Conflits

Un livrable combiné ne doit jamais prendre silencieusement la première valeur d'un paramètre de feuille. Une différence entre les feuilles génère un conflit à résoudre.

### 10.5 Paramètres absents ou vides

Une variable absente ou vide doit être identifiée explicitement et traitée selon la politique du modèle.

### 10.6 Nettoyage

Le résultat final passe par `FilenameService` pour gérer les caractères interdits, noms réservés, longueurs et collisions.

### 10.7 Extension

L'extension est ajoutée par le service d'export et ne doit pas être saisie dans le modèle.

### 10.8 Prévisualisation

L'interface affiche un aperçu du nom produit. En mode combiné, elle signale également les conflits.

### 10.9 Modèles enregistrés

Les modèles peuvent être enregistrés et réutilisés.

### 10.10 Architecture

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
Nom sécurisé
      ↓
PdfExportService / DwgExportService
```

---

## 11. Organisation et nommage

La destination sélectionnée constitue la racine de publication.

### PDF combiné + DWG combiné

```text
Exports/
├── DCE.pdf
├── DCE.dwg
├── PRO.pdf
└── PRO.dwg
```

### PDF séparé + DWG séparé

```text
Exports/
├── DCE/
│   ├── A101.pdf
│   ├── A101.dwg
│   ├── A102.pdf
│   └── A102.dwg
└── PRO/
    ├── A201.pdf
    └── A201.dwg
```

La structure exacte doit rester configurable sans dupliquer la logique de création des dossiers.

La V1 privilégie la sécurité : ne pas écraser silencieusement un livrable existant.

---

## 12. Interface utilisateur

L'interface respecte les UI Guidelines Outils TAA : WPF, simple, claire, rapide, prévisible et accent TAA **RGB (250, 100, 31) / #FA641F**.

Concept V1 :

```text
┌──────────────────────────────────────────────────────┐
│ EXPORT                                               │
│                                                      │
│ CARNETS                                              │
│ ☑ PRO                 Automatique   24 feuilles     │
│ ☑ DCE                 Automatique   18 feuilles     │
│ ★ DCE Architecte      Manuel         5 feuilles     │
│                                                      │
│ FORMATS                                              │
│ ☑ PDF                 ☑ DWG                          │
│                                                      │
│ PDF   Mode : ○ Combiné  ○ Séparé                    │
│ DWG   Mode : ○ Combiné  ○ Séparé                    │
│       Configuration : [ TAA – DWG True Color ▼ ]   │
│                                                      │
│ NOMMAGE                                               │
│ [ {Projet:NuméroProjet}_{Carnet} ]                  │
│                                                      │
│ DESTINATION                                          │
│ [ D:\Projet\Exports                       ] [ ... ] │
│ ☑ Créer automatiquement les dossiers                │
│                                                      │
│ Annuler                                   [ EXPORTER ]│
└──────────────────────────────────────────────────────┘
```

L'utilisateur doit pouvoir choisir les modes combiné/séparé indépendamment pour PDF et DWG.

---

## 13. Progression et erreurs

La publication affiche le carnet en cours, le format, le mode, la feuille en cours lorsque pertinent et les erreurs éventuelles.

Avant publication, Export valide les carnets, éléments manquants, modèles, conflits, dossiers, exportabilité des feuilles et configuration DWG.

---

## 14. Résultat de publication

`PublicationResult` expose au minimum :

```text
success
exported_pdf_count
exported_dwg_count
skipped_count
errors
output_directory
```

Les compteurs peuvent distinguer les livrables combinés et séparés.

Exemple :

```text
Publication terminée
PDF combinés : 3
PDF séparés : 54
DWG combinés : 3
DWG séparés : 54
Éléments ignorés : 1
Erreurs : 0
Destination : D:\Projet\Exports
```

---

## 15. Architecture cible

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
│   ├── filename_template.py
│   ├── pdf_publication_options.py
│   └── dwg_publication_options.py
├── services/
│   ├── export_service.py
│   ├── sheet_service.py
│   ├── view_service.py
│   ├── publication_builder_service.py
│   ├── publication_storage_service.py
│   ├── pdf_export_service.py
│   ├── dwg_export_service.py
│   ├── revit_export_configuration_service.py
│   ├── filename_template_service.py
│   └── filename_service.py
└── README.md
```

**SheetService** collecte les feuilles et expose les paramètres utilisables.

**PublicationBuilderService** construit les carnets et produit `PublicationItem[]`.

**PublicationStorageService** persiste les carnets et résout les éléments.

**RevitExportConfigurationService** lit les configurations d'export Revit, notamment les configurations DWG enregistrées.

**FilenameTemplateService** interprète les modèles et détecte conflits/valeurs absentes.

**FilenameService** sécurise les noms finaux.

**PdfExportService** exporte les PDF combinés ou séparés via l'API PDF native de Revit.

**DwgExportService** exporte les DWG combinés ou séparés via `Document.Export(..., ICollection<ElementId>, DWGExportOptions)`.

**ExportService** orchestre l'ensemble du processus.

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

### `PublicationSource`

```text
mode
parameter_name
parameter_value
```

Modes : `PARAMETER`, `MANUAL`, `TEMPORARY`.

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

### `FilenameTemplate`

```text
id
name
template
scope
extension
fallback_policy
```

### `PdfPublicationOptions`

```text
mode
create_subfolder
output_structure
```

`mode` : `COMBINED` ou `SEPARATE`.

### `DwgPublicationOptions`

```text
mode
create_subfolder
output_structure
revit_setup_name
merged_views
```

`mode` : `COMBINED` ou `SEPARATE`.

---

## 17. Persistance

Les carnets manuels persistants sont enregistrés séparément des préférences d'interface.

Les modèles de nommage sont également persistants.

Les références aux configurations DWG Revit sont conservées comme références de configuration et non comme une copie complète des paramètres.

Lors d'une publication, Export vérifie que la configuration référencée existe toujours. Une configuration supprimée doit être signalée et remplacée par l'utilisateur.

Une modification de la configuration native Revit doit être prise en compte lors de la prochaine publication.

---

## 18. Tests

### PDF

Tester : combiné, séparé, plusieurs carnets, carnet vide, création des dossiers, nommage, paramètres projet/feuille, conflits, collisions et interruption.

### DWG

Tester :

- une feuille en mode séparé ;
- plusieurs feuilles en mode séparé ;
- plusieurs feuilles en mode combiné ;
- plusieurs carnets ;
- configuration DWG Revit existante ;
- configuration supprimée ou modifiée ;
- création automatique des dossiers ;
- `MergedViews = false` ;
- `MergedViews = true` lorsque applicable ;
- feuille non exportable ;
- nommage ;
- fichier existant ;
- échec d'export.

### `DwgExportService`

Vérifier notamment :

```text
1 feuille + SEPARATE → 1 DWG
N feuilles + SEPARATE → N DWG
N feuilles + COMBINED → 1 DWG
```

Vérifier également que le dossier transmis à Revit existe avant `Document.Export`.

### Revit / pyRevit

Les tests d'intégration doivent couvrir collecte des feuilles, paramètres, carnets persistants, export PDF/DWG, configurations DWG, `CanBePrinted` et création des dossiers.

### Validation manuelle du DWG combiné

Pour chaque mode combiné DWG, vérifier dans AutoCAD ou un logiciel compatible :

- présence des feuilles/vues attendues ;
- structure réellement produite par Revit ;
- présence éventuelle des XRefs ;
- calques ;
- couleurs ;
- échelles et contenus graphiques ;
- nom du fichier ;
- arborescence.

Cette validation est obligatoire avant diffusion de la V1 afin de confirmer le comportement réel de `MergedViews`. citeturn0search13

### Interface

Tester ouverture, fermeture, choix PDF/DWG, choix combiné/séparé, configuration DWG, nommage, aperçu, progression, annulation, erreurs et persistance.

---

## 19. Scénarios d'acceptation

### Scénario A – Carnet automatique

L'utilisateur choisit un paramètre Revit et Export crée les carnets correspondant aux différentes valeurs.

### Scénario B – Carnet manuel persistant

L'utilisateur crée un carnet, sélectionne cinq feuilles et l'enregistre. Le carnet est disponible lors d'une publication ultérieure.

### Scénario C – PDF combiné

Un carnet de cinq feuilles est publié en mode PDF combiné et produit un seul PDF contenant les cinq feuilles dans l'ordre déterministe.

### Scénario D – PDF séparé

Le même carnet est publié en mode PDF séparé et produit un PDF par feuille.

### Scénario E – DWG combiné

Un carnet de cinq feuilles est publié en mode DWG combiné. Export transmet les cinq `ElementId` à l'API Revit avec la configuration sélectionnée.

Résultat attendu : un livrable DWG unique issu des cinq feuilles/vues, conformément au comportement de Revit et aux options de fusion sélectionnées.

### Scénario F – DWG séparé

Le même carnet produit cinq fichiers DWG, un par feuille.

### Scénario G – Configuration DWG Revit

L'utilisateur sélectionne une configuration DWG enregistrée dans Revit. Export récupère ses options et les utilise sans recréer une copie locale des réglages.

### Scénario H – Feuille non exportable

Export détecte une feuille non exportable avant l'appel API et signale précisément le problème.

### Scénario I – Paramètre projet dans le nom

Le modèle `{Projet:NuméroProjet}_{Carnet}` produit par exemple `23045_DCE.pdf`.

### Scénario J – Conflit de paramètre de feuille

Le modèle utilise `{Feuille:Phase}` alors que les feuilles ont des valeurs différentes. Export détecte le conflit et bloque le livrable combiné.

---

## 20. Principes de conception à respecter

1. **Le paramètre `Sous-titre` n'est jamais obligatoire.**
2. **Un carnet manuel persistant doit être réutilisable.**
3. **Un carnet est une configuration ; une publication est une exécution.**
4. **PDF et DWG disposent chacun d'un mode combiné ou séparé.**
5. **Le DWG combiné s'appuie sur l'API native Revit.**
6. **Le comportement réel du DWG combiné doit être validé sur les cas réels avant diffusion.**
7. **Les configurations DWG enregistrées dans Revit doivent être réutilisées plutôt que dupliquées.**
8. **Le nommage est configurable.**
9. **Les conflits de valeurs ne sont jamais résolus silencieusement.**
10. **Le nettoyage final reste centralisé dans `FilenameService`.**
11. **Les dossiers nécessaires doivent pouvoir être créés automatiquement.**
12. **Le résultat doit être déterministe, explicite et reproductible.**

---

## 21. Résumé

Export fournit un workflow de publication proche de la philosophie du Publisher d'Archicad, adapté à Revit.

```text
Sources de publication
        ↓
Carnets automatiques ou manuels
        ↓
Carnets persistants réutilisables
        ↓
PublicationItem[]
        ↓
Formats + modes de publication
        ↓
Modèle de nommage
        ↓
Résolution des paramètres
        ↓
Création des dossiers
        ↓
PDF + DWG
        ↓
Rapport de publication
```

Pour la V1 :

```text
PDF → COMBINED / SEPARATE
DWG → COMBINED / SEPARATE
```

Le **DWG combiné** est techniquement supporté par l'API Revit 2025 via `Document.Export` avec une collection de vues/feuilles. `DWGExportOptions.MergedViews` permet en outre de demander la fusion des vues via XRefs. Le résultat doit être validé sur les cas réels du projet avant diffusion. citeturn0search0turn0search13

Cette architecture conserve un moteur de publication unique tout en permettant à l'utilisateur de choisir, pour chaque format, entre un livrable combiné et des livrables séparés.