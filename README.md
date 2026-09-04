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

## Règle obligatoire de synchronisation du projet

Toute modification du code ou du comportement du projet doit être accompagnée d'une vérification de la documentation et de la roadmap.

### Documentation

Lorsqu'une modification :

- ajoute une fonctionnalité ;
- supprime une fonctionnalité ;
- modifie un comportement ;
- modifie une règle métier ;
- modifie le parcours utilisateur ;
- modifie les paramètres, options, formats d'entrée ou de sortie ;
- modifie les règles de publication/export ;
- ou modifie une architecture ou un contrat technique important ;

l'IA ou le développeur doit mettre à jour la documentation de référence correspondante dans `docs/` dans le même travail.

### Roadmap

Après chaque modification significative, vérifier **`ROADMAP.md`** et la roadmap spécifique de l'outil concerné.

La roadmap doit être mise à jour lorsque la modification :

- réalise une fonctionnalité prévue ;
- transforme une fonctionnalité prévue en fonctionnalité réalisée ;
- change le périmètre d'une étape ;
- ajoute une nouvelle intention ou un besoin fonctionnel ;
- rend une étape obsolète ;
- fait apparaître une nouvelle étape ou une dépendance ;
- ou modifie significativement l'ordre ou la priorité des développements.

Il ne faut pas attendre la fin d'une phase complète : **l'état de la roadmap doit rester représentatif de l'état réel du repository**.

### Règle de synchronisation

```text
Modification
    ↓
Code
    ↓
Tests
    ↓
Documentation concernée
    ↓
Roadmap concernée
    ↓
Vérification de cohérence
    ↓
Commit
```

Une modification fonctionnelle n'est pas considérée comme terminée si le code, la documentation et la roadmap ne sont plus cohérents.

Pour les modifications purement internes sans impact fonctionnel, la documentation et la roadmap doivent néanmoins être vérifiées ; elles ne sont mises à jour que si l'architecture, le contrat, la maintenance ou l'état d'avancement du projet sont concernés.

Cette règle complète les consignes obligatoires de **`AI_INSTRUCTIONS.md`**.

## Licence

Le repository contient le fichier `LICENSE` qui définit les conditions d'utilisation du projet.
