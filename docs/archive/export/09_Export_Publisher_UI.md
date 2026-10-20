# Export — Architecture Publisher

**Cible :** Revit 2025.4 / pyRevit 5.x

## Objectif

L'interface Export adopte une logique proche du Publisher d'Archicad : l'utilisateur travaille dans une arborescence persistante plutôt que dans une simple liste de carnets.

```text
Export
├── Général
│   ├── ☑ PC — Architecture
│   │   ├── A101 — Plan RDC
│   │   └── A201 — Coupe AA
│   └── ☐ PC — Dossier administratif
└── DCE
    └── ☑ DCE — Architecture
```

## Hiérarchie actuelle

La V1 de cette évolution implémente trois niveaux visibles :

- **Dossier** : organisation persistante des carnets ;
- **Carnet** : publication sélectionnable ;
- **Mise en page** : contenu du carnet.

Les dossiers peuvent être créés depuis Export. Un carnet peut être déplacé d'un dossier à un autre depuis le panneau de réglages.

## Réglages persistants

Chaque carnet possède ses propres réglages enregistrés dans le dépôt JSON :

- PDF activé / désactivé ;
- PDF combiné / séparé ;
- DWG activé / désactivé ;
- DWG combiné / séparé ;
- configuration DWG Revit ;
- Couleur vraie ;
- dossier de destination ;
- modèle de nommage.

Ainsi, publier un carnet ne dépend plus d'un réglage global temporaire de la fenêtre.

## Sélection

La case à cocher placée devant chaque carnet définit son inclusion dans la prochaine publication.

Les commandes **Tout sélectionner** et **Tout désélectionner** permettent de préparer rapidement une publication multiple.

Les carnets affichés restent limités aux carnets contenant au moins une mise en page du projet Revit actuellement ouvert.

## Compatibilité avec l'ancien stockage

Le repository passe au schéma 2. Les anciens carnets sont automatiquement placés dans le dossier `Général` et conservent leurs informations existantes.

## Évolution prévue

Cette première étape prépare les fonctions suivantes sans les imposer au modèle actuel :

1. sous-dossiers imbriqués ;
2. profils de publication ;
3. héritage des réglages dossier → carnet ;
4. surcharge explicite des réglages ;
5. publication d'un dossier complet ;
6. organisation avancée des sorties ;
7. résolution dynamique des carnets.

La séparation entre modèle, repository, contrôleur et interface doit être conservée pour permettre ces évolutions sans réécrire le moteur PDF/DWG.
