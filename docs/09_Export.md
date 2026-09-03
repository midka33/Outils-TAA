# Outils TAA – Outil Export

**Version :** 1.0  
**Statut :** Spécification fonctionnelle de référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Année :** 2026

---

## 1. Objectif

**Export** est l'outil de publication des documents Revit des **Outils TAA**.

Son objectif est de proposer dans Revit un fonctionnement proche du **Publisher d'Archicad** : préparer une publication, sélectionner les carnets à produire, lancer l'export et obtenir une arborescence de fichiers cohérente et reproductible.

> **Export n'est pas seulement un exporteur PDF/DWG : c'est un gestionnaire de publications.**

---

## 2. Principe général

Les feuilles Revit sont regroupées en **carnets de publication** à partir du paramètre de feuille **Sous-titre**.

Exemple :

```text
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

Chaque valeur distincte de `Sous-titre` constitue donc un carnet identifiable et publiable.

---

## 3. Philosophie Publisher

L'expérience recherchée s'inspire du Publisher d'Archicad :

- publications organisées en carnets ;
- documents regroupés dans chaque carnet ;
- réglages reproductibles ;
- sélection des carnets à publier ;
- noms et dossiers prévisibles ;
- publication relançable rapidement ;
- résultat clairement identifiable ;
- erreurs explicitement signalées.

L'objectif n'est pas de reproduire l'interface d'Archicad à l'identique, mais d'en reprendre les **principes de workflow** adaptés à Revit.

---

## 4. Périmètre fonctionnel V1

La première version doit couvrir :

1. détection automatique des feuilles ;
2. lecture du paramètre `Sous-titre` ;
3. regroupement des feuilles par carnet ;
4. affichage et sélection des carnets ;
5. choix du dossier de destination ;
6. export d'un PDF combiné par carnet ;
7. export d'un DWG par feuille ;
8. création d'un dossier par carnet pour les DWG ;
9. nettoyage et sécurisation des noms ;
10. suivi de progression ;
11. gestion des erreurs ;
12. rapport final de publication.

La V1 doit rester volontairement simple et fiable.

---

## 5. Workflow

```text
Ouverture d'Export
        ↓
Identification des feuilles
        ↓
Lecture de Sous-titre
        ↓
Regroupement en carnets
        ↓
Sélection des carnets
        ↓
Choix des formats
        ↓
Choix de la destination
        ↓
Validation
        ↓
Export PDF
        ↓
Export DWG
        ↓
Organisation des fichiers
        ↓
Rapport de publication
```

L'utilisateur doit pouvoir comprendre ce qui va être publié avant de lancer l'opération.

---

## 6. Carnets et feuilles

Deux feuilles ayant le même `Sous-titre` appartiennent au même carnet.

Une feuille sans `Sous-titre` doit être identifiée explicitement et ne doit jamais disparaître silencieusement. En V1, elle est signalée avant publication.

Les valeurs contenant espaces ou caractères spéciaux doivent être nettoyées pour pouvoir être utilisées comme noms de fichiers et dossiers.

L'ordre des feuilles dans un PDF doit être déterministe ; par défaut, il est basé sur le numéro de feuille Revit.

---

## 7. Export PDF

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

## 8. Export DWG

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

## 9. Organisation et nommage

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

## 10. Interface utilisateur

L'interface respecte les **UI Guidelines Outils TAA** :

- WPF ;
- simple ;
- claire ;
- rapide ;
- prévisible ;
- peu de paramètres inutiles ;
- accent TAA **RGB (250, 100, 31) / #FA641F**.

Concept V1 :

```text
┌──────────────────────────────────────────────┐
│ EXPORT                                       │
│ Publication des feuilles du projet           │
│                                              │
│ CARNETS                                      │
│ ☑ PRO                         24 feuilles    │
│ ☑ DCE                         18 feuilles    │
│ ☐ APS                         12 feuilles    │
│                                              │
│ FORMATS                                      │
│ ☑ PDF                                        │
│ ☑ DWG                                        │
│                                              │
│ DESTINATION                                  │
│ [ D:\Projet\Exports             ] [ ... ]   │
│                                              │
│ Annuler                         [ EXPORTER ] │
└──────────────────────────────────────────────┘
```

---

## 11. Progression et erreurs

La publication doit afficher une progression compréhensible : nombre d'éléments, carnet ou feuille en cours, étape PDF/DWG et erreurs éventuelles.

Les erreurs doivent être remontées explicitement : dossier inaccessible, chemin invalide, fichier existant, échec PDF/DWG, feuille invalide, `Sous-titre` absent, erreur Revit ou annulation utilisateur.

Une erreur ne doit pas être masquée.

---

## 12. Résultat de publication

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

## 13. Architecture cible

Export respecte la séparation **UI / logique métier / accès Revit**.

```text
Export.pushbutton/
├── script.py
├── ui/
│   ├── export_window.xaml
│   └── export_window.py
├── models/
│   ├── publication_set.py
│   ├── publication_item.py
│   └── publication_result.py
├── services/
│   ├── export_service.py
│   ├── sheet_service.py
│   ├── pdf_export_service.py
│   ├── dwg_export_service.py
│   └── filename_service.py
└── README.md
```

### Responsabilités principales

**SheetService** : collecte les feuilles, lit `Sous-titre`, crée les carnets et garantit un ordre déterministe.

**FilenameService** : nettoie et sécurise les noms.

**PdfExportService** : utilise l'API PDF native de Revit et produit le PDF du carnet.

**DwgExportService** : exporte une feuille en DWG et applique les paramètres centralisés.

**ExportService** : orchestre validation, export, progression et résultat.

L'interface ne contient pas la logique métier.

---

## 14. Modèles métier

### `PublicationItem`

```text
sheet_id
sheet_number
sheet_name
subtitle
```

Représente une feuille publiable.

### `PublicationSet`

```text
name
items
output_directory
```

Représente un carnet de publication.

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

## 15. API commune et Revit

Export doit réutiliser les composants existants de `lib/common` lorsqu'ils couvrent le besoin : logger, settings, dialogs, revit_utils, file_utils, collector_utils, progress et exceptions.

La publication est principalement une opération de lecture et d'export. Les transactions Revit ne doivent être utilisées que lorsqu'elles sont réellement nécessaires.

---

## 16. Paramètres persistants

Les paramètres utiles peuvent être conservés via le système `settings` commun, notamment :

- dernier dossier de destination ;
- derniers formats sélectionnés ;
- sélection des carnets si pertinent.

Ils ne doivent jamais modifier silencieusement le modèle Revit.

---

## 17. IA

Export ne nécessite pas d'intelligence artificielle.

Les opérations de regroupement, nommage, sélection, export et organisation sont déterministes et doivent rester basées sur des règles explicites.

---

## 18. Tests

Les tests suivent `docs/08_Testing.md` et couvrent notamment :

- `Sous-titre` identique, différent, vide, avec espaces ou caractères spéciaux ;
- un ou plusieurs carnets ;
- une ou plusieurs feuilles ;
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

## 19. Critères d'acceptation V1

```text
Modèle Revit 2025.4
        ↓
Plusieurs feuilles
        ↓
Plusieurs valeurs de Sous-titre
        ↓
Ouverture d'Export
        ↓
Détection correcte des carnets
        ↓
Sélection de plusieurs carnets
        ↓
PDF + DWG
        ↓
Choix du dossier
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

Aucune feuille sélectionnée ne doit disparaître silencieusement et aucun fichier ne doit être produit dans un emplacement inattendu.

---

## 20. Évolutions possibles

Après validation de la V1, pourront être ajoutés :

- PDF individuel par feuille ;
- sélection individuelle des feuilles ;
- profils de publication enregistrés ;
- conventions de nommage avancées ;
- plusieurs destinations ;
- paramètres DWG avancés ;
- fusion DWG de plusieurs feuilles ;
- historique des publications ;
- journal détaillé ;
- réexécution des éléments en erreur.

Ces fonctions ne doivent pas complexifier inutilement la V1.

---

## 21. Terminologie officielle

Le nom utilisateur officiel de l'outil est :

> **Export**

Les anciennes références à **PublisherAI** dans les documents historiques doivent progressivement être remplacées par **Export**. Le nouveau code et l'interface utilisateur doivent utiliser exclusivement le nom **Export**.

---

## 22. Résumé

```text
Feuilles Revit
      ↓
Sous-titre
      ↓
Carnets
      ↓
Sélection
      ↓
PDF + DWG
      ↓
Nommage
      ↓
Organisation
      ↓
Rapport
```

La priorité est donnée à la **fiabilité**, à la **simplicité d'utilisation**, à la **reproductibilité** et à la **compatibilité Revit 2025.4 / pyRevit 5.x**.
