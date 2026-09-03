# Outils TAA – Outil Export

**Version :** 1.5  
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

Export doit proposer :

1. **Automatique par paramètre** : l'utilisateur choisit le paramètre Revit servant au regroupement. `Sous-titre` peut être proposé par défaut selon les conventions TAA, mais ne doit jamais être imposé par le code.
2. **Sélection manuelle** : l'utilisateur crée un carnet et sélectionne directement les feuilles et, lorsque le périmètre le permet, les vues à publier.
3. **Sélection temporaire** : une sélection ponctuelle peut être publiée sans être enregistrée.

Ces méthodes doivent produire le même objet métier `PublicationSet`. Le moteur de publication ne doit pas dépendre de la manière dont le carnet a été créé.

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

Le paramètre `Sous-titre` est une convention de projet, pas une contrainte structurelle de l'outil.

### 4.2 Carnet manuel

L'utilisateur peut créer un carnet manuellement en donnant un nom, en sélectionnant les feuilles et/ou vues à publier, puis en enregistrant le carnet.

### 4.3 Carnet manuel temporaire

Une sélection ponctuelle peut être utilisée sans être enregistrée.

### 4.4 Réutilisation et évolution du projet

Les carnets manuels persistants doivent pouvoir être réutilisés lorsque le modèle Revit a évolué.

Les éléments doivent conserver des identifiants et métadonnées permettant leur résolution ultérieure, notamment `unique_id`, `sheet_id`, `élément_type`, `sheet_number` et `sheet_name`.

Un élément introuvable doit être signalé explicitement à l'utilisateur.

### 4.5 Carnet = configuration, publication = exécution

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

La première version couvre :

1. détection des feuilles ;
2. choix du paramètre de regroupement ;
3. création automatique de carnets par valeur ;
4. création manuelle de carnets ;
5. enregistrement et réutilisation des carnets ;
6. détection des éléments manquants ;
7. affichage et sélection des carnets ;
8. choix du dossier de destination ;
9. export PDF combiné par carnet ;
10. export PDF séparé par feuille ;
11. export DWG combiné par carnet ;
12. export DWG séparé par feuille ;
13. création automatique des dossiers nécessaires ;
14. **choix de l'organisation des dossiers d'export** ;
15. système de modèles de nommage ;
16. nettoyage et sécurisation des noms ;
17. suivi de progression ;
18. gestion des erreurs ;
19. rapport final de publication.

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
Formats + modes + organisation + nommage + destination
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
Formats + modes + organisation + nommage + destination
        ↓
Publication
```

---

## 7. Carnets et documents

Un carnet peut contenir des feuilles (`ViewSheet`) et l'architecture doit permettre d'étendre ultérieurement la prise en charge des vues (`View`).

Pour la V1, la publication PDF/DWG est prioritairement centrée sur les **feuilles Revit**.

L'ordre des feuilles doit être déterministe ; par défaut, il est basé sur le numéro de feuille Revit.

Une feuille sans valeur pour le paramètre sélectionné doit être identifiée explicitement.

---

## 8. Export PDF

La V1 propose deux modes :

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

### 8.3 Nommage

Les deux modes PDF utilisent le même système de modèles de nommage.

Pour un PDF combiné, les variables de feuille doivent avoir une valeur homogène dans le carnet ; sinon un conflit est signalé.

Pour un PDF séparé, les variables de feuille sont évaluées sur la feuille concernée.

### 8.4 Moteur PDF

L'export utilise en priorité le **moteur PDF natif de Revit**.

Un carnet vide est signalé et ne génère pas silencieusement un PDF vide.

---

## 9. Export DWG

La V1 propose deux modes :

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

Cette méthode accepte une collection de plusieurs vues dans un même appel. Toutes les vues doivent être valides et exportables.

`DWGExportOptions` expose également :

```csharp
bool MergedViews { get; set; }
```

Cette propriété permet le comportement de fusion documenté par Revit, notamment via des XRefs.

**Conclusion : le DWG combiné est techniquement réalisable dans la V1.**

### 9.2 Définition du DWG combiné

Export distingue :

1. plusieurs vues/feuilles envoyées dans un même appel d'export ;
2. la fusion des vues via `MergedViews`.

Export ne doit pas promettre une reproduction exacte d'un fichier AutoCAD multi-layout tant que le comportement réel n'a pas été validé sur les feuilles du projet.

La V1 définit donc le **DWG combiné** comme un livrable unique issu de plusieurs feuilles/vues Revit, avec le comportement de fusion déterminé par les options Revit sélectionnées.

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

### 9.5 Paramètres DWG Revit

Revit 2025 expose `ExportDWGSettings`, qui stocke dans le document les configurations DWG/DXF enregistrées. Export doit privilégier la **réutilisation des configurations DWG enregistrées dans Revit** plutôt que de dupliquer leurs paramètres.

La préférence fonctionnelle retenue pour Export reste **DWG True Color**, sous réserve de la configuration Revit sélectionnée.

### 9.6 Validation

Avant un DWG combiné, Export vérifie que toutes les feuilles/vues sont exportables.

### 9.7 Création des dossiers

Le dossier transmis à `Document.Export` doit exister. Export crée donc les dossiers nécessaires avant l'appel API.

### 9.8 Nommage

Le système de nommage est utilisable pour les DWG combinés et séparés.

Pour un DWG combiné, les variables de feuille suivent les mêmes règles de conflit que pour un PDF combiné.

---

## 10. Système de modèles de nommage

### 10.1 Objectif

Export permet de définir comment les fichiers produits sont nommés, sans imposer une convention unique.

### 10.2 Variables

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

### 10.3 Conflits

Un livrable combiné ne doit jamais prendre silencieusement la première valeur d'un paramètre de feuille. Une différence entre les feuilles génère un conflit à résoudre.

### 10.4 Nettoyage

Le résultat final passe par `FilenameService` pour gérer les caractères interdits, noms réservés, longueurs et collisions.

### 10.5 Prévisualisation

L'interface affiche un aperçu du nom produit. En mode combiné, elle signale également les conflits.

### 10.6 Architecture

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

## 11. Organisation des dossiers d'export

La destination sélectionnée constitue la racine de publication.

La V1 permet à l'utilisateur de choisir entre **deux organisations équivalentes**, sans modifier la logique métier de publication.

### 11.1 Type de fichier → Carnet

```text
Exports/
├── PDF/
│   ├── DCE/
│   │   └── DCE.pdf
│   └── PRO/
│       └── PRO.pdf
│
└── DWG/
    ├── DCE/
    │   ├── A101.dwg
    │   ├── A102.dwg
    │   └── A103.dwg
    └── PRO/
        ├── A201.dwg
        └── A202.dwg
```

Cette organisation place d'abord les formats. Elle est particulièrement adaptée lorsque les PDF et DWG doivent être transmis ou traités séparément.

### 11.2 Carnet → Type de fichier

```text
Exports/
├── DCE/
│   ├── PDF/
│   │   └── DCE.pdf
│   └── DWG/
│       ├── A101.dwg
│       ├── A102.dwg
│       └── A103.dwg
│
└── PRO/
    ├── PDF/
    │   └── PRO.pdf
    └── DWG/
        ├── A201.dwg
        └── A202.dwg
```

Cette organisation place d'abord le carnet. Elle est particulièrement adaptée lorsque le carnet constitue l'unité principale de transmission ou d'archivage.

### 11.3 Modes d'export compatibles

L'organisation des dossiers est indépendante du mode d'export :

| Format | Mode | Compatible |
|---|---|---|
| PDF | Combiné | Oui |
| PDF | Séparé | Oui |
| DWG | Combiné | Oui |
| DWG | Séparé | Oui |

Il est donc possible, par exemple, de produire un PDF combiné et des DWG séparés tout en utilisant la même organisation de dossiers.

### 11.4 Paramètre d'architecture

La structure doit être représentée par une valeur explicite :

```text
OutputStructure
├── BY_FILE_TYPE
└── BY_PUBLICATION_SET
```

Le service de gestion des chemins construit les dossiers à partir de cette configuration. Les services PDF et DWG ne doivent pas créer eux-mêmes leur propre arborescence.

### 11.5 Exemple avec PDF combiné et DWG combiné

**Type de fichier → Carnet**

```text
Exports/
├── PDF/
│   ├── DCE/
│   │   └── DCE.pdf
│   └── PRO/
│       └── PRO.pdf
└── DWG/
    ├── DCE/
    │   └── DCE.dwg
    └── PRO/
        └── PRO.dwg
```

**Carnet → Type de fichier**

```text
Exports/
├── DCE/
│   ├── PDF/
│   │   └── DCE.pdf
│   └── DWG/
│       └── DCE.dwg
└── PRO/
    ├── PDF/
    │   └── PRO.pdf
    └── DWG/
        └── PRO.dwg
```

### 11.6 Sécurité

La création des dossiers est automatique.

Export doit :

- créer les dossiers manquants ;
- ne pas écraser silencieusement un livrable existant ;
- détecter les collisions de noms ;
- sécuriser les noms de dossiers et fichiers ;
- signaler clairement toute impossibilité de création ou d'écriture.

---

## 12. Interface utilisateur

L'interface respecte les UI Guidelines Outils TAA : WPF, simple, claire, rapide, prévisible et accent TAA **RGB (250, 100, 31) / #FA641F**.

La configuration V1 doit permettre de choisir indépendamment :

- les carnets à publier ;
- PDF activé/désactivé ;
- PDF combiné/séparé ;
- DWG activé/désactivé ;
- DWG combiné/séparé ;
- configuration DWG Revit ;
- **organisation des dossiers : `Type de fichier → Carnet` ou `Carnet → Type de fichier`** ;
- modèle de nommage ;
- dossier racine de destination.

La prévisualisation doit refléter immédiatement la structure choisie.

---

## 13. Services principaux

L'architecture V1 doit rester modulaire :

```text
ExportWindow
      ↓
ExportViewModel
      ↓
PublicationService
      ├── PublicationSetResolver
      ├── FilenameTemplateService
      ├── OutputPathService
      ├── PdfExportService
      └── DwgExportService
```

`OutputPathService` est responsable de l'arborescence et reçoit notamment :

```text
root_directory
output_structure
publication_set
file_type
```

Les services PDF/DWG demandent un chemin de sortie au `OutputPathService` au lieu de construire eux-mêmes les dossiers.

---

## 14. Modèles métier

### PublicationItem

```text
unique_id
sheet_id
item_type
sheet_number
sheet_name
parameter_value
```

### PublicationSource

```text
mode
parameter_name
parameter_value
```

Modes :

```text
PARAMETER
MANUAL
TEMPORARY
```

### PublicationSet

```text
id
name
items
source
output_directory
persistent
filename_template_id
```

### PdfPublicationOptions

```text
mode
create_subfolder
output_structure
```

### DwgPublicationOptions

```text
mode
create_subfolder
output_structure
revit_setup_name
merged_views
```

### OutputStructure

```text
BY_FILE_TYPE
BY_PUBLICATION_SET
```

---

## 15. Nommage et chemins

La génération d'un livrable suit ce flux :

```text
PublicationSet
      ↓
OutputPathService
      ↓
Structure de dossiers
      ↓
FilenameTemplateService
      ↓
FilenameService
      ↓
Nom sécurisé + extension
      ↓
Export PDF/DWG
```

La structure des dossiers et le nom du fichier sont deux responsabilités distinctes.

---

## 16. Persistance des réglages

Les préférences utilisateur doivent pouvoir être conservées, notamment :

- dernier dossier de destination ;
- organisation des dossiers ;
- dernier mode PDF ;
- dernier mode DWG ;
- dernière configuration DWG Revit ;
- modèle de nommage utilisé.

Les carnets persistants et les préférences globales ne doivent pas être confondus.

---

## 17. Gestion des erreurs

Les erreurs doivent être remontées au niveau du carnet et du livrable lorsque cela est possible.

Exemples :

- carnet vide ;
- feuille introuvable ;
- vue non exportable ;
- configuration DWG supprimée ;
- dossier inaccessible ;
- nom de fichier invalide ;
- collision de fichier ;
- échec d'export PDF ;
- échec d'export DWG ;
- annulation par l'utilisateur.

Une erreur sur un carnet ne doit pas masquer les résultats obtenus sur les autres carnets.

---

## 18. Tests V1

Les tests doivent couvrir :

### Carnets

- aucun carnet ;
- carnet vide ;
- un carnet ;
- plusieurs carnets ;
- carnet automatique ;
- carnet manuel ;
- élément manquant.

### PDF

- PDF combiné ;
- PDF séparé ;
- plusieurs feuilles ;
- conflits de nommage ;
- collision de fichier.

### DWG

- DWG combiné ;
- DWG séparé ;
- plusieurs feuilles combinées ;
- configuration DWG existante ;
- configuration supprimée ;
- `MergedViews=false` ;
- `MergedViews=true` lorsque pertinent ;
- feuille non exportable ;
- validation du résultat dans AutoCAD ou logiciel compatible, notamment pour les XRefs lorsque le mode de fusion les utilise.

### Organisation des dossiers

Tester les deux structures :

```text
BY_FILE_TYPE
BY_PUBLICATION_SET
```

et toutes les combinaisons suivantes :

- PDF combiné + DWG combiné ;
- PDF combiné + DWG séparé ;
- PDF séparé + DWG combiné ;
- PDF séparé + DWG séparé.

Vérifier :

- création des dossiers ;
- absence de doublons ;
- noms corrects ;
- extensions correctes ;
- absence d'écrasement silencieux ;
- comportement avec caractères spéciaux.

---

## 19. Scénarios d'acceptation

### Scénario A — Publication DCE standard

L'utilisateur sélectionne `DCE`, PDF combiné et DWG séparés.

Le résultat doit pouvoir être :

```text
Exports/
└── DCE/
    ├── PDF/
    │   └── DCE.pdf
    └── DWG/
        ├── A101.dwg
        ├── A102.dwg
        └── A103.dwg
```

ou, si `BY_FILE_TYPE` est sélectionné :

```text
Exports/
├── PDF/
│   └── DCE/
│       └── DCE.pdf
└── DWG/
    └── DCE/
        ├── A101.dwg
        ├── A102.dwg
        └── A103.dwg
```

### Scénario B — Publication complète

L'utilisateur sélectionne plusieurs carnets et active PDF + DWG.

L'organisation choisie doit être appliquée de manière homogène à tous les carnets et formats.

### Scénario C — Réutilisation

L'utilisateur recharge un carnet manuel enregistré, modifie uniquement l'organisation des dossiers, puis relance la publication.

Le contenu du carnet ne doit pas être modifié par ce changement.

---

## 20. Principes d'architecture à respecter

- Les carnets ne connaissent pas la structure physique des dossiers.
- Les services PDF/DWG ne construisent pas directement l'arborescence globale.
- `OutputPathService` est l'unique responsable de la construction des chemins.
- Le format de fichier et le carnet sont des dimensions indépendantes de l'organisation.
- Les réglages natifs Revit sont réutilisés lorsqu'ils existent.
- Les opérations déterministes ne doivent pas dépendre d'une IA.
- Les noms et chemins doivent être prévisibles et reproductibles.
- Toute erreur doit être explicite.

---

## 21. Résumé V1

Export V1 doit permettre :

```text
Carnets
  ↓
Sélection
  ↓
PDF → COMBINED / SEPARATE
DWG → COMBINED / SEPARATE
  ↓
Organisation des dossiers
  ├── BY_FILE_TYPE
  └── BY_PUBLICATION_SET
  ↓
Nommage configurable
  ↓
Publication
  ↓
Rapport final
```

La structure de dossiers est donc une **préférence de publication indépendante des formats et des carnets**. Elle doit pouvoir être modifiée sans modifier le contenu d'un carnet ni la logique des moteurs PDF/DWG.

---

## 22. Évolutions futures

Les évolutions possibles comprennent notamment :

- profils de publication enregistrés ;
- plusieurs structures de dossiers prédéfinies ;
- règles de nommage conditionnelles ;
- publication vers des répertoires réseau ;
- contrôle avancé des collisions ;
- historique des publications ;
- comparaison entre publication précédente et publication courante ;
- intégration avec des workflows documentaires externes.
