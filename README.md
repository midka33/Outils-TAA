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
| **Export** | Workflow de publication validé dans Revit 2025.4, y compris PR #22 et #23 |
| **Calculs des pièces** | Fonctions livrées en v1.0.3 ; résolution interactive des divergences de groupes hors périmètre |
| **Plans de vente** | V1.1 fichiers liés — livrée avec Outils TAA v1.3.0 |
| **Carnets de menuiseries extérieures** | 🧩 Préparation — production automatisée des carnets de mise en page des menuiseries extérieures |
| **Plans de repérage** | 🧩 Préparation — génération automatisée des plans de repérage et de leurs mises en page |
| **Cotation automatique** | ⚠️ Bêta suspendue en masse après crash Revit — diagnostic limité à une vue / une pièce hors groupe ; aucune validation de stabilité |
| **Étiquetage automatique** | 🧪 Bêta sur branche de test — vues multiples, types choisis, groupes de détails attachés à valider dans Revit |
| **Légendes automatiques** | 📋 Planifié — génération de légendes depuis le gabarit d’une vue ou les couleurs des pièces, avec légende partagée entre plusieurs vues et échelle identique à la vue de référence |
| **Contrôle** | 📋 Planifié |
| **Annotation** | 📋 Planifié |
| **Utilitaires** | 📋 Planifié |

## Plans de vente V1.1 — fichiers Revit liés

La V1.1, livrée dans **Outils TAA v1.3.0**, permet de lancer Plans de vente
depuis un fichier hôte / SITE tout en utilisant les pièces des liens Revit
directs chargés.

Le workflow validé dans Revit 2025.4 couvre notamment la création automatique
des niveaux SITE manquants, les vues et crops, le repérage, les nomenclatures,
le cartouche, les étiquettes et les cotations lorsque leurs types existent dans
le fichier hôte.

Les identifiants techniques des liens restent internes. Un numéro logement
unique conserve son nom métier ; en cas de doublon réel entre plusieurs sources,
l'utilisateur choisit le libellé de différenciation.

Limites de la V1.1 : liens imbriqués hors périmètre ; types d'étiquette et de
cote disponibles dans SITE ; nomenclatures modèles configurées pour inclure les
éléments des fichiers liés.

Voir `docs/20_Plans_de_Vente.md` et la recette de release
`docs/release/Preparation_Plans_de_Vente_V1.1_Liens.md`.

## Modules d'annotations automatiques (bêta)

Une première version non validée dans Revit est préparée sur la branche
[`feature/annotations-automatiques-beta`](https://github.com/midka33/Outils-TAA/tree/feature/annotations-automatiques-beta).
Elle réutilise les moteurs Plans de vente sans modifier leur comportement.
La recette et les limitations figurent dans [`docs/21_Annotations_Automatiques.md`](docs/21_Annotations_Automatiques.md).

**Sécurité (22/10/2026) :** après une fermeture brutale de Revit, la cotation en masse est désactivée dans la bêta. Ne tester que sur une copie de projet ; le bouton Cotation exige une seule pièce et conserve un journal dans `%TEMP%\OutilsTAA_Annotations_crashtrace.log`. Les groupes attachés et l'exploration des dalles de niveaux voisins sont temporairement suspendus. **Ne pas fusionner dans `main` avant diagnostic et recette.**

## Guide utilisateur

- [Export — tutoriel](docs/release/Tutoriel_Export_v1.3.0.md)
- [Calculs des pièces — tutoriel](docs/release/Tutoriel_Calculs_Pieces_v1.3.0.md)
- [Plans de vente — tutoriel](docs/release/Tutoriel_Plans_de_Vente_v1.3.0.md)
- [Index de la documentation](docs/INDEX.md)

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

La documentation courante est indexée dans [`docs/INDEX.md`](docs/INDEX.md). Les documents historiques sont conservés sous `docs/archive/`.

### Instructions pour les IA et agents de développement

Toute IA, tout agent de code ou assistant intervenant sur le repository doit commencer par consulter **`AI_INSTRUCTIONS.md`**.

Ce fichier définit notamment le workflow obligatoire avant modification et avant commit, ainsi que la procédure de capitalisation des bugs dans `docs/11_BUGS_Prevention_Registry.md`.

La spécification de référence du module **Export** est disponible dans `docs/09_Export.md`.

La spécification de référence du module **Plans de vente** est disponible dans `docs/20_Plans_de_Vente.md`.

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
