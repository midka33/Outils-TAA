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
| **Règle des 1/6 — surfaces vitrées** | Diagnostic V0.1 intégré à la branche de développement ; validation Revit 2025.4 à réaliser |
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

## Diagnostic des baies / règle des 1/6 (en développement)

Module de contrôle des surfaces des baies pour les **maisons individuelles** et les **bâtiments de logements collectifs**, cible **Revit 2025.4 / pyRevit 5.x**.

Objectif : comparer la surface des baies mesurée en tableau à un objectif de **1/6 de la surface habitable (SHAB)**, en distinguant le contrôle à l'échelle du bâtiment et les bilans par logement. L'analyse réglementaire doit aussi gérer les éventuelles modalités alternatives applicables au projet. Le calcul ne doit pas être présenté comme une preuve automatique de conformité RE2020.

Périmètre fonctionnel prévu :

- Collecter les pièces du projet actif et, si sélectionnés, des liens Revit directs chargés ; regrouper par bâtiment et numéro de logement.
- Lire les surfaces habitables pertinentes, en contrôlant leur périmètre et en évitant d'assimiler systématiquement la surface brute des pièces Revit à la SHAB.
- Le diagnostic inventorie les familles `FEN-EXT` et `PORFEN-EXT` et exclut **par défaut les lanterneaux et familles/types MRX (murs-rideaux)** ; ces exclusions sont configurables pour l'inspection, tracées dans un CSV séparé et restent systématiquement hors du futur calcul réglementaire. Les dimensions nominales, brutes et de tableau ne sont pas encore certifiées.
- Éviter le double comptage des ouvertures et signaler les baies à vérifier (local desservi, paroi extérieure, doublons, identifiant de logement, lien).
- Produire un bilan des surfaces exigées, recensées et manquantes, ainsi qu'un rapport exportable avec avertissements.
- Prévoir un fonctionnement **en lecture seule** lors du diagnostic ; toute écriture future dans des paramètres Revit sera optionnelle et explicitement confirmée.

**État au 22 octobre 2026 :** le diagnostic V0.1 (bouton, analyse, CSV et tests) est intégré à cette branche ; il n'est pas encore validé dans Revit. La branche de travail [`feature/calculs-regle-1-6-baies`](https://github.com/midka33/Outils-TAA/tree/feature/calculs-regle-1-6-baies) sert aux essais, corrections et à la revue. Le diagnostic a été exécuté en Revit 2025.4 : après correction des accès WPF et des noms de familles, une extraction de 1 349 éléments sans alerte a été obtenue le 22 octobre 2026. **Le filtre par préfixes et les statuts de façade sont désormais validés sur capture Revit 2025.4 (416 occurrences, 18 types, aucune alerte).** L'export CSV avec ce filtre, les liens et les dimensions en tableau doivent encore être validés. Voir `docs/27_Diagnostic_Baies.md`.

## Guide utilisateur

- [Export — tutoriel](docs/release/Tutoriel_Export_v1.3.0.md)
- [Calculs des pièces — tutoriel](docs/release/Tutoriel_Calculs_Pieces_v1.3.0.md)
- [Plans de vente — tutoriel](docs/release/Tutoriel_Plans_de_Vente_v1.3.0.md)
- [Diagnostic des baies — guide et limites](docs/27_Diagnostic_Baies.md)
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
