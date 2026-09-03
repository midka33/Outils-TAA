# Outils TAA – Export : configurations d'export Revit

**Version :** 1.0  
**Complément de :** `docs/09_Export.md`  
**Cible :** Revit 2025.4 / pyRevit 5.x

---

## 1. Principe

Export doit réutiliser autant que possible les **configurations natives d'export et d'impression de Revit**, plutôt que de recréer dans son interface les réglages déjà disponibles dans Revit.

L'objectif est de conserver une logique proche du Publisher d'Archicad : le carnet définit **quoi publier**, tandis que la configuration d'export définit **comment le document est produit**.

```text
Carnet
  ↓
Documents à publier
  ↓
Format choisi
  ↓
Configuration d'export Revit
  ↓
Publication
```

Export ne doit donc pas dupliquer inutilement les réglages de qualité, de format ou de représentation déjà gérés par Revit.

---

## 2. PDF

### 2.1 Utilisation du moteur natif

La publication PDF doit utiliser en priorité le moteur PDF natif de Revit.

Lorsque Revit expose un réglage pertinent via son API, Export doit pouvoir le réutiliser ou le transmettre à l'export plutôt que de maintenir une copie indépendante de la préférence.

Les réglages concernés peuvent notamment inclure, selon ce qui est exposé par l'API Revit 2025.4 :

- format papier ;
- orientation ;
- couleur / noir et blanc ;
- vectoriel / raster lorsque disponible ;
- qualité ou résolution lorsque disponible ;
- paramètres d'impression associés aux feuilles.

**Important :** Export ne doit pas supposer que toutes les options visibles dans l'interface Revit disposent d'un équivalent API. Chaque réglage doit être vérifié contre l'API de Revit 2025.4 avant implémentation.

### 2.2 Pas de faux « profil PDF Revit »

Contrairement aux configurations DWG, Export ne doit pas présenter comme native une notion de « profil PDF Revit » si Revit ne fournit pas réellement cet objet sous cette forme.

L'application peut mémoriser sa propre configuration logique si nécessaire, mais celle-ci doit être clairement distinguée des paramètres natifs de Revit.

---

## 3. DWG

### 3.1 Réutilisation des configurations DWG Revit

Pour le DWG, Export doit privilégier les **configurations d'export DWG enregistrées dans Revit** plutôt que de recréer tous les réglages dans l'application.

La configuration sélectionnée doit notamment pouvoir contrôler, selon les capacités de l'API Revit 2025.4 :

- version AutoCAD ;
- unités ;
- correspondance des calques ;
- couleurs ;
- épaisseurs de lignes ;
- polices ;
- motifs ;
- références externes ;
- autres options natives d'export DWG.

La préférence fonctionnelle du projet reste **DWG True Color**.

### 3.2 Référence à la configuration

Un carnet ou une publication ne doit pas recopier intégralement une configuration DWG native.

Il doit plutôt conserver une **référence à la configuration Revit sélectionnée**, puis vérifier qu'elle existe encore au moment de la publication.

```text
Publication
    ↓
Référence configuration DWG
    ↓
Configuration toujours disponible ?
   ├── Oui → export
   └── Non → erreur explicite
```

Une configuration supprimée ou devenue indisponible ne doit jamais être remplacée silencieusement par une autre configuration.

---

## 4. Interface utilisateur

L'interface doit rester simple et masquer les réglages avancés lorsque ceux-ci sont déjà gérés par Revit.

Exemple cible :

```text
FORMATS

☑ PDF
   Configuration : [ Configuration PDF / impression ▼ ]

☑ DWG
   Configuration : [ TAA - DWG True Color ▼ ]
```

Pour le PDF, le libellé exact et les possibilités de sélection devront être adaptés aux réglages réellement accessibles dans l'API Revit 2025.4.

Pour le DWG, la liste doit proposer les configurations natives disponibles dans le projet.

Un accès **« Ouvrir les réglages Revit »** ou équivalent peut être prévu lorsque l'utilisateur doit modifier une configuration native plutôt que la dupliquer dans Export.

---

## 5. Séparation des responsabilités

Les réglages d'export doivent être séparés de la logique de carnet et du système de nommage.

Architecture cible :

```text
PublicationSet
      ↓
ExportConfigurationService
      ↓
┌───────────────────────────┐
│ PDF : réglages disponibles│
│ DWG : configuration Revit │
└───────────────────────────┘
      ↓
PdfExportService / DwgExportService
```

Le moteur PDF/DWG exécute l'export ; il ne doit pas contenir la logique permettant de rechercher, présenter ou persister les configurations.

Service recommandé :

```text
ExportConfigurationService
```

Responsabilités :

- détecter les configurations disponibles ;
- exposer les configurations utilisables par Export ;
- résoudre la configuration choisie ;
- vérifier sa disponibilité avant publication ;
- fournir les options à `PdfExportService` et `DwgExportService` ;
- signaler les incompatibilités API.

---

## 6. Persistance

Les préférences propres à Export et les configurations natives de Revit doivent rester distinctes.

### Préférences Export

Export peut mémoriser :

- dernier format utilisé ;
- dernière configuration sélectionnée ;
- dernier dossier de destination ;
- modèle de nommage ;
- autres préférences d'interface.

### Configurations natives Revit

Export ne doit pas recopier inutilement :

- les configurations DWG natives ;
- les réglages d'impression natifs ;
- les paramètres que Revit sait déjà conserver.

Il doit conserver une **référence** et vérifier sa validité au moment de l'utilisation.

---

## 7. Gestion des modifications

Une configuration Revit peut être modifiée après avoir été sélectionnée dans Export.

Export doit donc considérer la configuration native comme la **source de vérité** au moment de la publication.

```text
Configuration enregistrée dans Export
          ↓
Résolution dans Revit au lancement
          ↓
Configuration actuelle
          ↓
Publication avec les réglages actuels
```

L'application ne doit pas utiliser une copie obsolète des réglages.

Si une configuration n'est plus disponible, l'utilisateur doit être averti avant le lancement de l'export.

---

## 8. Relation avec le système de nommage

Le système de modèles de nommage décrit dans `docs/09_Export.md` reste indépendant des réglages d'export.

```text
Carnet
  ├── Documents
  ├── Modèle de nommage
  └── Configuration d'export
          ↓
       Publication
          ↓
    Fichier final
```

Le modèle de nommage détermine **le nom du fichier**.

La configuration d'export détermine **la manière dont le fichier est produit**.

Ces deux responsabilités ne doivent pas être mélangées.

---

## 9. Tests obligatoires

Les tests devront vérifier au minimum :

### PDF

- détection des réglages accessibles via l'API ;
- utilisation correcte des paramètres sélectionnés ;
- comportement lorsqu'un réglage n'est pas exposé par l'API ;
- cohérence avec le moteur PDF natif de Revit ;
- absence de duplication inutile des paramètres Revit.

### DWG

- détection des configurations DWG enregistrées ;
- sélection d'une configuration précise ;
- export avec cette configuration ;
- configuration supprimée ;
- configuration modifiée dans Revit ;
- conservation du choix utilisateur entre deux publications lorsque la configuration existe toujours.

### Régression

Les changements de configuration ne doivent pas modifier :

- la constitution des carnets ;
- l'ordre des feuilles ;
- les modèles de nommage ;
- la destination des fichiers ;
- le rapport de publication.

---

## 10. Principe directeur

> **Export orchestre les configurations ; Revit reste la source de vérité pour les réglages natifs d'export.**

Cette règle permet de conserver une interface simple, d'éviter les doublons et de rester cohérent avec les évolutions de Revit.
