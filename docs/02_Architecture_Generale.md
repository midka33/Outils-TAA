# Outils TAA – Developer Handbook
## Chapitre 02 — Architecture Générale

## Architecture du dépôt

```text
OutilsTAA/
├── README.md
├── docs/
├── OutilsTAA.extension/
└── LICENSE
```

## Architecture de l'extension

```text
OutilsTAA.extension/
├── OutilsTAA.tab/
│   ├── Publication.panel/
│   ├── Calcul.panel/
│   ├── Controle.panel/
│   ├── Annotation.panel/
│   └── Utilitaires.panel/
├── lib/
└── resources/
```

## Bibliothèque commune

```text
lib/common/
├── logger.py
├── settings.py
├── dialogs.py
├── parameter_utils.py
├── revit_utils.py
├── progress.py
└── transaction.py
```

## Principes

- Une responsabilité par classe.
- Pas de duplication.
- Réutiliser lib/common.
- Séparer UI, logique métier et accès Revit.
