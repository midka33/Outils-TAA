# Outils TAA – Outil Export

**Version :** 2.0  
**Statut :** Spécification fonctionnelle de référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Année :** 2026

---

## 1. Objectif

**Export** est l'outil de publication des documents Revit des **Outils TAA**.

Son objectif est de proposer dans Revit un fonctionnement proche du **Publisher d'Archicad** : préparer une publication, organiser des carnets, sélectionner les carnets à produire, lancer l'export et obtenir une arborescence de fichiers cohérente, reproductible et réutilisable.

> **Export n'est pas seulement un exporteur PDF/DWG : c'est un gestionnaire de publications.**

La V2 renforce cette philosophie avec :

- des carnets persistants et évolutifs ;
- des liens dynamiques entre carnets et documents Revit ;
- une hiérarchie interne dans les carnets ;
- des profils de publication réutilisables ;
- des réglages hérités avec possibilité de surcharge ;
- plusieurs périmètres de publication ;
- une gestion complète de l'exécution ;
- un rapport détaillé et traçable de chaque publication ;
- une architecture extensible à d'autres formats futurs.

---

## 2. Philosophie Publisher

L'expérience recherchée s'inspire des principes du Publisher d'Archicad :

- publications organisées en carnets ;
- carnets persistants et réutilisables ;
- liens entre organisation du projet et publication ;
- hiérarchie de dossiers ;
- réglages reproductibles ;
- sélection des carnets ou sous-ensembles à publier ;
- formats et destinations configurables ;
- nommage automatisé ;
- publication relançable rapidement ;
- suivi de progression ;
- résultat clairement identifiable ;
- erreurs explicitement signalées.

L'objectif n'est **pas** de reproduire l'interface d'Archicad à l'identique. Export reprend les principes de workflow et les adapte au fonctionnement de Revit.

### 2.1 Principe fondamental de la V2

Un carnet ne doit plus être considéré uniquement comme une liste figée de feuilles.

Il peut représenter une **règle de publication** :

```text
Projet Revit
    ↓
Source du carnet
    ↓
Résolution dynamique
    ↓
Arborescence du carnet
    ↓
Périmètre de publication
    ↓
Profil de publication
    ↓
Livrables PDF / DWG / futurs formats
```

Cela permet par exemple qu'une nouvelle feuille `A104` correspondant aux règles du carnet DCE soit automatiquement intégrée au prochain export, sans devoir modifier manuellement le carnet.

---

## 3. Modèle métier V2

L'architecture V2 distingue explicitement les objets suivants :

```text
PublicationProfile
        │
        ├── PublicationSet[]
        │       │
        │       ├── PublicationSource
        │       ├── PublicationNode[]
        │       └── PublicationSettings
        │
        ├── OutputSettings
        ├── NamingSettings
        └── ExecutionSettings
```

### 3.1 PublicationProfile

Le **profil de publication** représente une configuration complète et réutilisable.

Il peut contenir :

- un ou plusieurs carnets ;
- les formats à produire ;
- les modes combiné/séparé ;
- la destination ;
- l'organisation des dossiers ;
- les modèles de nommage ;
- les configurations DWG Revit ;
- les règles de résolution des carnets ;
- le périmètre de publication ;
- les comportements d'écrasement/collision ;
- les paramètres d'exécution.

Le profil est la **configuration**. La publication est l'**exécution** de cette configuration.

### 3.2 PublicationSet

Un `PublicationSet` représente un carnet logique.

Il contient notamment :

```text
id
name
source
nodes
settings
persistent
```

### 3.3 PublicationNode

Un `PublicationNode` représente un élément de l'arborescence interne du carnet.

Un nœud peut être :

- un dossier ;
- une feuille ;
- une vue lorsque le périmètre de publication l'autorise.

Il permet de reproduire une organisation telle que :

```text
DCE
├── Plans
│   ├── A101
│   ├── A102
│   └── A103
├── Coupes
│   ├── A201
│   └── A202
└── Façades
    ├── A301
    └── A302
```

### 3.4 PublicationItem

Le document résolu doit rester indépendant de sa source :

```text
PublicationItem
├── unique_id
├── sheet_id
├── item_type
├── sheet_number
├── sheet_name
├── parameter_value
└── source_path
```

Le moteur de publication travaille sur des `PublicationItem[]` résolus et non directement sur les règles de sélection.

---

## 4. Sources de carnets

Export V2 conserve les trois modes de création existants et ajoute les liens dynamiques.

### 4.1 Automatique par paramètre

L'utilisateur choisit le paramètre Revit servant au regroupement.

`Sous-titre` peut être proposé par défaut selon les conventions TAA, mais ne doit jamais être imposé par le code.

### 4.2 Sélection manuelle persistante

L'utilisateur crée un carnet, sélectionne les documents, puis enregistre le carnet.

### 4.3 Sélection manuelle temporaire

Une sélection ponctuelle peut être publiée sans être enregistrée.

### 4.4 Source dynamique

Une source dynamique définit une règle permettant de recalculer le contenu du carnet à chaque publication.

La source doit pouvoir reposer sur des critères tels que :

- paramètre Revit ;
- valeur de paramètre ;
- catégorie ;
- numéro de feuille ;
- phase ;
- ensemble de paramètres ;
- règle combinée ;
- structure ou groupe de documents lorsque l'information est disponible dans Revit.

L'outil ne doit pas limiter l'architecture à `Sous-titre`.

### 4.5 Source fixe ou dynamique

```text
PublicationSource
├── mode
│   ├── PARAMETER
│   ├── MANUAL
│   ├── TEMPORARY
│   └── DYNAMIC
│
├── parameter_name
├── parameter_value
└── rule_definition
```

### 4.6 Résolution dynamique

Avant chaque publication :

```text
Règle dynamique
      ↓
Recherche dans le modèle Revit
      ↓
Résultats
      ↓
Application de la hiérarchie du carnet
      ↓
PublicationItem[]
```

Une nouvelle feuille correspondant à la règle doit être intégrée automatiquement.

Une feuille qui ne correspond plus à la règle doit être retirée de la résolution, sans modifier l'historique du carnet.

### 4.7 Éléments manquants

Pour un carnet fixe, un élément introuvable doit être signalé.

Pour un carnet dynamique, Export distingue :

- élément attendu mais introuvable ;
- élément nouvellement détecté ;
- élément ne correspondant plus à la règle ;
- élément ignoré volontairement par une surcharge utilisateur.

---

## 5. Hiérarchie interne des carnets

### 5.1 Objectif

Un carnet peut contenir sa propre arborescence logique indépendamment de l'organisation physique des fichiers.

Exemple :

```text
DCE
├── 01_Plans
│   ├── Plans RDC
│   ├── Plans R+1
│   └── Plans R+2
├── 02_Coupes
├── 03_Façades
└── 04_Détails
```

### 5.2 Avantages

La hiérarchie permet :

- de rendre les carnets lisibles ;
- de publier un sous-ensemble ;
- d'appliquer des réglages à un niveau précis ;
- de préparer des arborescences de sortie ;
- de conserver une organisation stable malgré l'évolution du projet.

### 5.3 Séparation hiérarchie logique / sortie physique

La hiérarchie du carnet ne doit pas être obligatoirement identique à l'arborescence de fichiers.

L'utilisateur peut choisir si les dossiers internes du carnet sont :

- uniquement organisationnels ;
- reproduits dans les dossiers de sortie ;
- utilisés seulement pour appliquer des réglages.

### 5.4 Types de nœuds

```text
PublicationNodeType
├── FOLDER
├── SHEET
└── VIEW
```

Les vues ne sont utilisables que lorsque leur export et le format choisi sont compatibles.

---

## 6. Profils de publication

### 6.1 Objectif

Un **PublicationProfile** doit permettre de mémoriser une procédure complète de publication.

Exemples :

```text
PRO
DCE
PC
DP
EXE
DOE
```

Un profil peut contenir plusieurs carnets.

### 6.2 Contenu

Un profil peut mémoriser :

```text
PublicationProfile
├── Carnets
├── Formats
├── Modes d'export
├── Destination
├── Organisation des dossiers
├── Nommage
├── Configuration DWG
├── Périmètre
├── Règles de collision
└── Paramètres d'exécution
```

### 6.3 Réutilisation

Le profil doit pouvoir être relancé plusieurs fois dans le même projet.

Les profils doivent être persistants et indépendants de la session Revit.

### 6.4 Versionnement

Un profil doit posséder une version de schéma :

```text
schema_version
```

Une évolution du format de stockage ne doit pas rendre silencieusement les anciens profils invalides.

Une migration explicite doit être prévue lorsque nécessaire.

---

## 7. Héritage et surcharge des réglages

### 7.1 Principe

Les réglages doivent pouvoir être définis à plusieurs niveaux :

```text
Profil
  ↓
Carnet
  ↓
Dossier interne
  ↓
Document
```

Chaque niveau peut :

- hériter du niveau supérieur ;
- conserver la valeur héritée ;
- remplacer explicitement cette valeur.

### 7.2 Exemple

```text
Profil DCE
PDF = activé
DWG = activé
DWG config = TAA_TrueColor

Carnet Plans
    hérite de PDF/DWG

Dossier Détails
    PDF = activé
    DWG = désactivé
```

### 7.3 Règle d'architecture

Les services d'export ne doivent pas implémenter eux-mêmes la logique d'héritage.

Un service dédié doit produire les réglages finaux :

```text
SettingsResolver
      ↓
PublicationSettings finales
      ↓
PdfExportService / DwgExportService
```

### 7.4 Surcharge explicite

Une valeur héritée et une valeur surchargée doivent être distinguables dans le modèle et dans l'interface.

L'utilisateur doit pouvoir revenir à `Hériter` sans supprimer la valeur du niveau supérieur.

---

## 8. Périmètre de publication

La V2 introduit un périmètre explicite.

### 8.1 Publication complète

```text
ENTIRE_SET
```

Tous les documents résolus du carnet sont publiés.

### 8.2 Sélection

```text
SELECTED_ITEMS
```

L'utilisateur choisit les éléments à publier parmi ceux du carnet.

### 8.3 Sélection d'un sous-dossier

```text
SELECTED_NODES
```

L'utilisateur peut publier uniquement un dossier interne du carnet et ses descendants.

### 8.4 Jeu de publication

Export peut mémoriser une sélection temporaire ou persistante appelée **jeu de publication**.

Ce concept est volontairement propre à Export et ne prétend pas être un équivalent natif du Transmittal Set d'Archicad.

```text
PublicationScope
├── ENTIRE_SET
├── SELECTED_ITEMS
└── SELECTED_NODES
```

### 8.5 Publication modifiée depuis la dernière exécution

La V2 prépare également le concept :

```text
MODIFIED_ONLY
```

Il ne doit pas être implémenté en assimilant simplement une modification Revit à une modification de livrable.

Pour être fiable, Export devra conserver un état de publication permettant de comparer :

- les éléments publiés ;
- leur état au moment de la publication ;
- les paramètres utilisés ;
- le profil ;
- le contenu du carnet ;
- les fichiers produits.

Cette fonctionnalité peut donc nécessiter un mécanisme de snapshot ou de hash métier.

---

## 9. Workflow V2

### 9.1 Création d'un carnet dynamique

```text
Ouverture d'Export
        ↓
Nouveau carnet
        ↓
Nom du carnet
        ↓
Choix de la source
        ↓
Définition de la règle
        ↓
Prévisualisation des résultats
        ↓
Organisation interne
        ↓
Enregistrement
```

### 9.2 Création d'un profil

```text
Nouveau profil
        ↓
Sélection des carnets
        ↓
Formats
        ↓
Modes combiné / séparé
        ↓
Organisation des dossiers
        ↓
Nommage
        ↓
Configurations Revit
        ↓
Périmètre
        ↓
Règles d'exécution
        ↓
Enregistrement
```

### 9.3 Publication

```text
Profil
  ↓
Résolution des carnets
  ↓
Résolution des règles dynamiques
  ↓
Construction de l'arborescence
  ↓
Résolution des réglages hérités
  ↓
Résolution du périmètre
  ↓
Validation
  ↓
Prévisualisation des livrables
  ↓
Publication
  ↓
Rapport
```

---

## 10. Périmètre fonctionnel V1 conservé

La V2 conserve les fonctions V1 :

1. détection des feuilles ;
2. choix du paramètre de regroupement ;
3. création automatique de carnets par valeur ;
4. création manuelle de carnets ;
5. enregistrement et réutilisation ;
6. détection des éléments manquants ;
7. sélection des carnets ;
8. choix du dossier de destination ;
9. PDF combiné ;
10. PDF séparé ;
11. DWG combiné ;
12. DWG séparé ;
13. création automatique des dossiers ;
14. organisation `Type de fichier → Carnet` ;
15. organisation `Carnet → Type de fichier` ;
16. modèles de nommage ;
17. nettoyage des noms ;
18. progression ;
19. gestion des erreurs ;
20. rapport final.

---

## 11. Export PDF

La V2 conserve deux modes :

- **PDF combiné** : un seul PDF pour plusieurs documents ;
- **PDF séparés** : un PDF par document.

Le moteur PDF utilise en priorité le **moteur PDF natif de Revit**.

### 11.1 PDF combiné

```text
DCE.pdf
```

Le contenu est ordonné selon l'ordre déterministe du carnet.

### 11.2 PDF séparés

```text
DCE/
├── A101.pdf
├── A102.pdf
└── A103.pdf
```

### 11.3 Hiérarchie interne

Lorsque l'option est activée, les dossiers internes du carnet peuvent être reproduits :

```text
DCE/
├── Plans/
│   ├── A101.pdf
│   └── A102.pdf
└── Coupes/
    └── A201.pdf
```

### 11.4 Carnet vide

Un carnet vide doit être signalé et ne doit pas générer silencieusement un PDF vide.

---

## 12. Export DWG

La V2 conserve :

- **DWG combiné** ;
- **DWG séparé**.

### 12.1 API Revit 2025.4

L'API Revit expose :

```csharp
Document.Export(
    string folder,
    string name,
    ICollection<ElementId> views,
    DWGExportOptions options)
```

`DWGExportOptions` expose également :

```csharp
bool MergedViews { get; set; }
```

La fusion via `MergedViews` peut notamment utiliser des XRefs.

### 12.2 Limite fonctionnelle importante

Export ne doit pas promettre une reproduction exacte d'un fichier AutoCAD multi-layout tant que le comportement réel n'a pas été validé sur les feuilles du projet.

Le DWG combiné est donc défini comme un livrable unique issu de plusieurs feuilles/vues Revit, avec le comportement de fusion déterminé par les options Revit sélectionnées.

### 12.3 Configurations DWG Revit

Revit 2025 expose `ExportDWGSettings` pour les configurations DWG/DXF enregistrées dans le document.

Export doit privilégier leur réutilisation plutôt que de dupliquer les paramètres dans l'outil.

La préférence fonctionnelle TAA reste **DWG True Color**, sous réserve de la configuration Revit sélectionnée.

### 12.4 Validation

Avant publication :

- vérifier que les documents sont exportables ;
- vérifier que la configuration DWG existe ;
- vérifier que la destination est accessible ;
- vérifier les collisions ;
- vérifier les noms.

---

## 13. Système de modèles de nommage

### 13.1 Variables Projet

```text
{Projet:NomProjet}
{Projet:NuméroProjet}
{Projet:Adresse}
```

### 13.2 Variables Feuille

```text
{Feuille:Numéro}
{Feuille:Nom}
{Feuille:Phase}
{Feuille:Indice}
```

### 13.3 Variables Carnet

```text
{Carnet}
{Carnet:Nom}
{Carnet:Source}
```

### 13.4 Variables de profil

```text
{Profil}
{Profil:Nom}
```

### 13.5 Paramètre de regroupement

```text
{ParamètreCarnet}
```

### 13.6 Conflits

Un livrable combiné ne doit jamais prendre silencieusement la première valeur rencontrée.

Si une variable n'a pas une valeur homogène, Export doit :

1. détecter le conflit ;
2. l'afficher ;
3. empêcher la publication automatique si le conflit rend le nom ambigu ;
4. proposer une résolution explicite.

### 13.7 Architecture

```text
FilenameTemplateService
        ↓
VariableResolver
        ↓
ConflictDetector
        ↓
FilenameService
        ↓
Nom sécurisé
```

---

## 14. Organisation des dossiers d'export

La destination constitue la racine de publication.

### 14.1 Type de fichier → Carnet

```text
Exports/
├── PDF/
│   ├── DCE/
│   └── PRO/
└── DWG/
    ├── DCE/
    └── PRO/
```

### 14.2 Carnet → Type de fichier

```text
Exports/
├── DCE/
│   ├── PDF/
│   └── DWG/
└── PRO/
    ├── PDF/
    └── DWG/
```

### 14.3 Hiérarchie interne optionnelle

```text
Exports/
└── DCE/
    ├── PDF/
    │   ├── Plans/
    │   └── Coupes/
    └── DWG/
        ├── Plans/
        └── Coupes/
```

### 14.4 Paramètre d'architecture

```text
OutputStructure
├── BY_FILE_TYPE
└── BY_PUBLICATION_SET
```

Un service unique `OutputPathService` est responsable de la construction des chemins.

Les services PDF et DWG ne doivent pas créer leur propre arborescence.

### 14.5 Sécurité

Export doit :

- créer les dossiers manquants ;
- sécuriser les noms ;
- détecter les collisions ;
- ne pas écraser silencieusement un livrable ;
- signaler toute impossibilité d'écriture.

---

## 15. Gestion des collisions et stratégie d'écrasement

La stratégie doit être explicite dans le profil.

```text
CollisionPolicy
├── ASK
├── SKIP
├── OVERWRITE
└── RENAME
```

`OVERWRITE` ne doit jamais être implicite.

Pour chaque collision, le rapport doit indiquer :

- fichier existant ;
- action choisie ;
- nouveau nom éventuel ;
- résultat.

---

## 16. Gestion de l'exécution

La V2 formalise l'exécution comme un objet métier :

```text
PublicationExecution
├── id
├── profile_id
├── started_at
├── completed_at
├── status
├── progress
├── items
└── report
```

### 16.1 États

```text
ExecutionStatus
├── PREPARING
├── VALIDATING
├── RUNNING
├── PAUSING
├── PAUSED
├── CANCELLING
├── CANCELLED
├── COMPLETED
└── FAILED
```

### 16.2 Progression

L'interface doit afficher au minimum :

- progression globale ;
- carnet courant ;
- document courant ;
- format courant ;
- nombre de livrables réussis ;
- nombre d'erreurs ;
- nombre d'éléments ignorés.

### 16.3 Annulation

L'utilisateur doit pouvoir demander l'arrêt d'une publication.

L'annulation doit être coopérative et respecter les limites de l'API Revit.

Un livrable déjà finalisé doit rester identifiable comme produit avant l'annulation.

### 16.4 Pause

La V2 réserve un état `PAUSED`.

La possibilité réelle de suspendre une opération dépend des points de contrôle disponibles dans l'API Revit et dans les services d'export.

Il ne faut pas simuler une pause si l'opération Revit en cours ne peut pas être interrompue proprement.

---

## 17. Rapport de publication

Chaque exécution doit produire un rapport structuré.

### 17.1 Informations générales

```text
Profil
Date / heure
Projet
Utilisateur
Destination
```

### 17.2 Résultats

Pour chaque livrable :

```text
Carnet
Document(s)
Format
Mode
Chemin
Nom
Statut
Durée
Message
```

### 17.3 Statuts

```text
SUCCESS
WARNING
SKIPPED
FAILED
CANCELLED
```

### 17.4 Résolution dynamique

Le rapport doit également permettre de comprendre les changements de contenu :

- documents nouvellement détectés ;
- documents retirés de la règle ;
- documents introuvables ;
- documents exclus par surcharge.

### 17.5 Traçabilité

Le rapport doit être suffisamment précis pour permettre de comprendre pourquoi un document a été ou n'a pas été publié.

---

## 18. Historique des publications

La V2 prévoit un historique associé aux profils.

Il doit permettre de retrouver :

- quand une publication a été lancée ;
- quel profil a été utilisé ;
- quelle version du profil était active ;
- quels carnets ont été résolus ;
- quels fichiers ont été produits ;
- quelles erreurs sont survenues.

L'historique ne remplace pas le rapport de publication : il en conserve les informations essentielles pour les comparaisons futures.

---

## 19. Détection des modifications depuis la dernière publication

Cette fonction est préparée en V2 mais doit être conçue comme un mécanisme de **suivi d'état de publication**.

### 19.1 État mémorisé

Pour chaque document publié, Export peut mémoriser :

```text
unique_id
sheet_number
sheet_name
relevant_parameters
profile_id
profile_version
publication_time
output_name
```

### 19.2 Comparaison

Lors d'une nouvelle publication :

```text
État précédent
      ↓
Nouvelle résolution
      ↓
Comparaison
      ↓
Nouveau / Modifié / Inchangé / Supprimé
```

### 19.3 Prudence

Une simple date de modification d'élément ne suffit pas à déterminer si un livrable PDF/DWG est réellement différent.

Une implémentation fiable pourra nécessiter un snapshot des informations pertinentes ou un hash métier.

---

## 20. Validation avant publication

Avant toute exécution, Export doit effectuer une phase de validation indépendante de l'export réel.

### 20.1 Contrôles

- profil valide ;
- carnet valide ;
- documents résolus ;
- éléments manquants ;
- documents non exportables ;
- configuration PDF/DWG ;
- destination accessible ;
- dossiers créables ;
- noms valides ;
- conflits de nommage ;
- collisions ;
- cohérence des réglages hérités ;
- cohérence du périmètre.

### 20.2 Principe

```text
Résolution
    ↓
Validation
    ↓
Blocage si erreur critique
    ↓
Publication
```

L'outil ne doit pas commencer une publication importante avant d'avoir détecté les erreurs structurelles prévisibles.

---

## 21. Architecture logicielle

L'architecture V2 doit rester conforme aux standards Outils TAA.

```text
UI WPF
  ↓
Application / ViewModels
  ↓
Publication Services
  ├── PublicationProfileService
  ├── PublicationSetService
  ├── PublicationResolver
  ├── PublicationTreeService
  ├── SettingsResolver
  ├── ValidationService
  ├── FilenameTemplateService
  ├── OutputPathService
  ├── PdfExportService
  ├── DwgExportService
  ├── ExecutionService
  └── PublicationReportService
        ↓
Revit API / Common TAA
```

### 21.1 Principes

- une responsabilité par classe ;
- aucune logique métier dans les fenêtres WPF ;
- aucun accès Revit direct depuis les modèles de stockage ;
- aucun chemin construit directement dans les exporteurs ;
- aucun paramètre DWG dupliqué inutilement ;
- réutilisation de `lib/common` ;
- opérations Revit centralisées dans des services dédiés ;
- gestion explicite des exceptions ;
- journalisation structurée.

---

## 22. Persistance

Les carnets et profils persistants doivent être stockés dans un format versionnable et migrable.

### 22.1 Identifiants Revit

Les éléments ne doivent pas dépendre uniquement d'un `ElementId` persistant entre sessions.

La résolution doit privilégier des identifiants et métadonnées adaptés, notamment :

```text
unique_id
sheet_id
item_type
sheet_number
sheet_name
```

### 22.2 Élément supprimé

Un élément supprimé doit apparaître comme manquant et ne doit pas être remplacé silencieusement par un autre élément portant le même numéro.

### 22.3 Évolution du modèle

Les changements de nom ou de numéro doivent être visibles dans le diagnostic de résolution lorsque la correspondance n'est plus certaine.

---

## 23. Extensibilité des formats

La V2 doit conserver une architecture permettant d'ajouter ultérieurement d'autres formats :

```text
PublicationFormat
├── PDF
├── DWG
├── IFC
├── BIMX / autres
└── FUTURS
```

Le fait de préparer l'architecture ne signifie pas que tous ces formats doivent être implémentés en V2.

Chaque format doit disposer d'un service spécialisé derrière une abstraction commune de publication.

---

## 24. Compatibilité Revit / pyRevit

### Cible

- Revit **2025.4** ;
- pyRevit **5.x**.

Toute API utilisée doit être vérifiée sur la version cible.

Les comportements non garantis par l'API doivent être marqués comme tels dans la documentation et validés par des tests d'intégration.

---

## 25. Tests V2

### 25.1 Carnets

Tester :

- carnet automatique ;
- carnet manuel ;
- carnet temporaire ;
- carnet dynamique ;
- règle sans résultat ;
- ajout automatique d'une feuille ;
- retrait d'une feuille ne correspondant plus à la règle ;
- élément supprimé ;
- changement de numéro ;
- caractères spéciaux.

### 25.2 Hiérarchie

Tester :

- dossiers imbriqués ;
- déplacement d'un document ;
- publication d'un dossier uniquement ;
- reproduction de l'arborescence dans les fichiers ;
- hiérarchie uniquement logique.

### 25.3 Profils

Tester :

- création ;
- sauvegarde ;
- rechargement ;
- version ;
- migration ;
- profil incomplet ;
- plusieurs carnets dans un profil.

### 25.4 Héritage

Tester :

- héritage simple ;
- surcharge ;
- retour à héritage ;
- conflit entre niveaux ;
- suppression d'un réglage parent.

### 25.5 Périmètres

Tester :

- totalité ;
- sélection ;
- sous-dossier ;
- jeu de publication ;
- modification depuis dernière publication lorsque la fonctionnalité est activée.

### 25.6 PDF / DWG

Tester :

- combiné ;
- séparé ;
- carnet vide ;
- document non exportable ;
- configuration DWG absente ;
- True Color ;
- `MergedViews=false` ;
- `MergedViews=true` ;
- collisions ;
- destination inexistante ;
- destination non accessible.

### 25.7 Exécution

Tester :

- progression ;
- annulation ;
- échec partiel ;
- erreur critique ;
- rapport final ;
- reprise d'une publication après erreur.

### 25.8 Validation externe

Les livrables doivent être contrôlés dans les logiciels cibles ou compatibles lorsque cela est pertinent, notamment pour les DWG.

---

## 26. Interface utilisateur V2

L'interface doit rester conforme aux guidelines TAA :

- WPF ;
- simple ;
- lisible ;
- rapide ;
- prévisible ;
- couleur agence orange `RGB(250,100,31)` / `#FA641F`.

### 26.1 Écran principal proposé

```text
┌─────────────────────────────────────────────┐
│ EXPORT                                      │
├─────────────────────────────────────────────┤
│ Profil : [ DCE ▼ ]      [Nouveau] [Modifier]│
├─────────────────────────────────────────────┤
│ Carnets                                     │
│ ☑ DCE                                       │
│ ☑ Plans                                     │
│ ☐ Coupes                                    │
├─────────────────────────────────────────────┤
│ Résolution                                  │
│ 42 documents   2 nouveaux   1 manquant      │
├─────────────────────────────────────────────┤
│ Formats                                     │
│ ☑ PDF   ☑ DWG                               │
├─────────────────────────────────────────────┤
│ Destination : [................] [Parcourir]│
├─────────────────────────────────────────────┤
│ [ Prévisualiser ]             [ Publier ]   │
└─────────────────────────────────────────────┘
```

### 26.2 Prévisualisation

Avant publication, l'utilisateur doit pouvoir voir :

- les carnets ;
- les documents ;
- la hiérarchie ;
- les fichiers qui seront créés ;
- les noms finaux ;
- les erreurs et avertissements.

---

## 27. Journalisation et diagnostic

Export doit utiliser le logger commun des Outils TAA.

Les événements importants doivent être journalisés :

- ouverture d'un profil ;
- résolution d'un carnet ;
- ajout/retrait dynamique ;
- validation ;
- début de publication ;
- création d'un fichier ;
- erreur ;
- annulation ;
- fin de publication.

Les logs ne doivent pas contenir inutilement de données sensibles ou de chemins confidentiels lorsque ceux-ci ne sont pas nécessaires au diagnostic.

---

## 28. Règles fonctionnelles essentielles V2

Les règles suivantes sont non négociables :

1. **Le moteur de publication ne connaît pas la source du carnet.**
2. **Une règle dynamique ne doit jamais être confondue avec une sélection fixe.**
3. **Un profil est une configuration, une exécution est une instance de cette configuration.**
4. **Les réglages hérités sont résolus avant l'appel aux exporteurs.**
5. **Un exporteur ne construit jamais lui-même l'arborescence de sortie.**
6. **Une collision ne doit jamais être résolue silencieusement.**
7. **Un document manquant ne doit jamais être remplacé silencieusement par un autre.**
8. **La prévisualisation doit utiliser les mêmes services de résolution que la publication réelle.**
9. **La validation doit être indépendante de l'interface.**
10. **La publication doit pouvoir produire un rapport exploitable même en cas d'échec partiel.**
11. **Les comportements Revit non garantis doivent être explicitement documentés et testés.**
12. **Les formats futurs ne doivent pas imposer de refonte du modèle métier.**

---

## 29. Roadmap V2

### V2.0 – Socle Publisher

- profils de publication ;
- carnets dynamiques ;
- hiérarchie interne ;
- périmètres de publication ;
- héritage et surcharge ;
- exécution structurée ;
- rapport détaillé ;
- PDF/DWG existants intégrés au nouveau modèle.

### V2.1 – Productivité

- historique enrichi ;
- comparaison avec publication précédente ;
- détection des documents modifiés ;
- amélioration de la prévisualisation ;
- raccourcis de publication ;
- duplication de profils/carnets.

### V2.2 – Extensibilité

- vues publiables lorsque pertinent ;
- nouveaux formats ;
- intégration éventuelle de workflows IFC ;
- règles de publication plus avancées.

---

## 30. Critère de réussite V2

Export V2 sera considéré comme ayant atteint son objectif lorsque l'utilisateur pourra :

1. créer un profil de publication ;
2. créer un carnet dynamique ;
3. organiser ce carnet en sous-dossiers ;
4. définir les formats PDF/DWG ;
5. réutiliser les configurations Revit ;
6. définir une destination et une convention de nommage ;
7. publier tout le carnet ou seulement une partie ;
8. relancer le même profil après évolution du projet ;
9. voir automatiquement les nouveaux documents correspondant aux règles ;
10. identifier les documents manquants ou modifiés ;
11. suivre l'exécution ;
12. annuler proprement une publication ;
13. obtenir un rapport précis et reproductible.

> **La réussite de la V2 ne se mesure donc plus uniquement à la capacité de produire un PDF ou un DWG. Elle se mesure à la capacité d'Export à devenir un véritable gestionnaire de publications pour Revit, inspiré du workflow Publisher d'Archicad.**
