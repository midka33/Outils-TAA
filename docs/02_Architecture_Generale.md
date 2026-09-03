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
└── lib/
    └── common/
```

Les noms affichés à l'utilisateur sont :

- **Export**
- **Calculs des pièces**
- **Contrôle**
- **Annotation**
- **Utilitaires**

Les noms de dossiers pyRevit restent volontairement sans accents afin de respecter les conventions techniques : `Controle.panel` et `Calculs.panel`.

## Structure des modules

Les modules métier peuvent être organisés par responsabilités :

```text
<Module>.panel/
├── models/
├── services/
├── ui/
└── README.md
```

Les commandes pyRevit (`*.pushbutton`) et leurs scripts d'entrée seront ajoutés sous le module concerné lorsque la fonctionnalité sera implémentée.

## Bibliothèque commune

```text
lib/common/
├── __init__.py
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

La bibliothèque commune constitue le socle technique partagé. Elle ne doit pas dépendre des modules métier.

## Principes

- Une responsabilité par classe.
- Pas de duplication.
- Réutiliser `lib/common`.
- Séparer UI, logique métier et accès Revit.
- Les noms fonctionnels affichés dans l'interface sont en français.
- Les identifiants techniques utilisent des noms ASCII, sans espaces ni accents.
- Les imports doivent utiliser les chemins techniques réellement présents dans le repository.
- Un module métier ne doit pas importer un composant supprimé, renommé ou appartenant à un ancien chemin.
- Les composants communs doivent rester indépendants des composants métier.
