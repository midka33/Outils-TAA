# Outils TAA – Developer Handbook
## Chapitre 02 — Architecture Générale

## Architecture du dépôt

```text
Outils-TAA/
├── README.md
├── docs/
├── OutilsTAA.extension/
└── LICENSE
```

## Architecture de l'extension

```text
OutilsTAA.extension/
├── OutilsTAA.tab/
│   ├── Export.panel/
│   ├── Calculs.panel/
│   ├── Controle.panel/
│   ├── Annotation.panel/
│   └── Utilitaires.panel/
├── lib/
└── resources/
```

Les noms affichés à l'utilisateur sont :

- **Export**
- **Calculs des pièces**
- **Contrôle**
- **Annotation**
- **Utilitaires**

Les noms de dossiers pyRevit restent volontairement sans accents afin de respecter les conventions techniques : `Controle.panel` et `Calculs.panel`.

## Bibliothèque commune

```text
lib/common/
├── logger.py
├── settings.py
├── dialogs.py
├── parameter_utils.py
├── revit_utils.py
├── collector_utils.py
├── progress.py
├── transaction.py
├── file_utils.py
└── exceptions.py
```

## Principes

- Une responsabilité par classe.
- Pas de duplication.
- Réutiliser `lib/common`.
- Séparer UI, logique métier et accès Revit.
- Les noms fonctionnels affichés dans l'interface sont en français.
- Les identifiants techniques utilisent des noms ASCII, sans espaces ni accents.
