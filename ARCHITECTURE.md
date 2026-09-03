# Architecture Outils TAA

## Objectif

Outils TAA est une suite modulaire de commandes pyRevit pour Revit 2025.4. Le dépôt sépare explicitement la documentation, l'infrastructure commune et les modules métier.

## Structure cible

```text
Outils-TAA/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── ROADMAP.md
├── SECURITY.md
├── docs/
│   ├── 01_Vision_Philosophie.md
│   ├── 02_Architecture_Generale.md
│   ├── 03_Standards_Developpement.md
│   ├── 04_UI_Guidelines.md
│   ├── 05_Internal_API.md
│   ├── 06_AI_Development_Guide.md
│   ├── 07_Git_Workflow.md
│   ├── 08_Testing.md
│   ├── 09_Export.md
│   └── 10_Calculs_Pieces.md
└── OutilsTAA.extension/
    ├── OutilsTAA.tab/
    │   ├── Export.panel/
    │   ├── Calculs.panel/
    │   ├── Controle.panel/
    │   ├── Annotation.panel/
    │   └── Utilitaires.panel/
    ├── lib/
    │   └── common/
    └── resources/
```

## Règles d'architecture

1. L'UI ne contient pas de logique métier.
2. Les services métier ne dépendent pas de WPF.
3. L'accès à l'API Revit est isolé dans des services/adaptateurs dédiés.
4. Les modules métier ne se dépendent pas entre eux.
5. Les fonctionnalités transverses vivent dans `lib/common`.
6. Une classe = une responsabilité principale.
7. Les modèles métier restent indépendants de l'UI.
8. Les transactions Revit sont courtes, explicites et centralisées autant que possible.
9. Les noms fonctionnels sont français et stables : `Export`, `Calculs des pièces`.
10. Les noms techniques de fichiers et dossiers utilisent ASCII et underscores lorsque cela améliore la robustesse du chargement pyRevit.

## Dépendances autorisées

```text
UI ───────► Services métier ───────► Revit adapters
  │                 │
  └────────► Common ◄┘
```

Un service métier peut utiliser `common`, mais `common` ne doit jamais importer un module métier.

## Infrastructure commune

`lib/common` constitue l'API interne minimale :

- `logger`
- `settings`
- `dialogs`
- `parameter_utils`
- `revit_utils`
- `collector_utils`
- `selection_utils`
- `transaction`
- `progress`
- `file_utils`
- `unit_utils`
- `exceptions`

Toute nouvelle fonction transversale doit d'abord être évaluée pour intégration dans cette API avant de créer un utilitaire local.

## Modules

### Export

Responsable de la préparation et de la publication des carnets PDF/DWG. Son moteur de publication reçoit des objets métier normalisés et ne dépend pas de la manière dont le carnet a été créé.

Architecture métier cible :

```text
PublicationProfile
        │
        ▼
PublicationSet
        │
        ├── PublicationSource
        ├── PublicationNode
        └── PublicationItem
                │
                ▼
        Publication Engine
          ├── PDF exporter
          └── DWG exporter
```

### Calculs des pièces

Responsable des calculs et traitements liés aux pièces. Il doit rester indépendant d'Export et partager uniquement l'infrastructure commune.

### Contrôle / Annotation / Utilitaires

Les futurs modules suivent exactement les mêmes règles : UI mince, services métier isolés, accès Revit encapsulé et réutilisation de `common`.

## Persistance

Les préférences globales et les données persistantes d'application doivent être séparées des données du projet Revit. Les identifiants Revit persistants ne doivent pas reposer exclusivement sur `ElementId` lorsque les données doivent survivre aux sessions.

## Compatibilité

Cible officielle : Revit 2025.4 + pyRevit 5.x. Toute évolution architecturale doit préserver cette contrainte sauf décision explicite documentée.

## Source de vérité

Les spécifications détaillées des modules sont dans `docs/`. `docs/09_Export.md` est la source de vérité fonctionnelle pour Export.
