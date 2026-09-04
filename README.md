# Outils TAA

Suite d'outils métier développée pour **Autodesk Revit 2025.4** avec **pyRevit 5.x**.

## Objectifs

- Automatiser les tâches répétitives.
- Standardiser les processus de production.
- Améliorer la qualité des livrables.
- Fournir une base logicielle modulaire et maintenable.

## Modules

| Module | Statut |
|---|---|
| **Export** | 🚧 En développement |
| **Calculs des pièces** | 🚧 Migration |
| **Contrôle** | 📋 Planifié |
| **Annotation** | 📋 Planifié |
| **Utilitaires** | 📋 Planifié |

## Historique des noms

Pour conserver la traçabilité du projet :

- **Export** est le nom actuel du module historiquement appelé `PublisherAI`.
- **Calculs des pièces** est le nom actuel du module historiquement appelé `RoomCalculator`.

Les anciens noms ne doivent plus être utilisés pour désigner les modules dans le code, l'interface ou la documentation courante.

## Compatibilité

- Autodesk Revit 2025.4
- pyRevit 5.x

## Structure

```text
Outils-TAA/
├── docs/
├── OutilsTAA.extension/
├── AI_INSTRUCTIONS.md
└── README.md
```

## Documentation

La documentation complète est disponible dans le dossier `docs/`.

### Instructions pour les IA et agents de développement

Toute IA, tout agent de code ou assistant intervenant sur le repository doit commencer par consulter **`AI_INSTRUCTIONS.md`**.

Ce fichier définit notamment le workflow obligatoire avant modification et avant commit, ainsi que la procédure de capitalisation des bugs dans `docs/11_BUGS_Prevention_Registry.md`.

La spécification de référence du module **Export** est disponible dans `docs/09_Export.md`.

## Licence

Le repository contient le fichier `LICENSE` qui définit les conditions d'utilisation du projet.
