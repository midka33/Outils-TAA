# Préparation de la release v1.1.0

**État au 13 octobre 2026 : proposition, aucune release ni aucun tag créé.**

## Référence et version

- Dépôt : `midka33/Outils-TAA`.
- `main` contrôlé : `44503dff9415a17978a77c72a358ea8025a82c48`.
- Arbre : `52386f9a6450e554615c2e2aefc247d484da8238`.
- Dernière release publiée : **v1.0.3**, le 8 octobre 2026.
- Proposition : **v1.1.0**, évolution MINOR selon les règles SemVer de
  `docs/07_Git_Workflow.md`, car des fonctionnalités compatibles sont ajoutées.

Inventaire complet des releases publiées et des tags existants lors du contrôle :

| Tag | Commit |
|---|---|
| v1.0.0 | `09daa928190a943368e3fe680818ffe1e72fd6b0` |
| v1.0.1 | `e1e4b85c341289cf70e67c8a1fcfc610bfb7337d` |
| v1.0.2 | `b2b6da4070984d73d786f7ec515e2c111674be60` |
| v1.0.3 | `0d4987afbe9bc5756bd91c8a33bcae043874d57a` |

Aucune ancienne release ni aucun tag ne doit être remplacé. Vérifier à nouveau
la disponibilité de v1.1.0 au moment de publier.

## Vérifications effectuées

Les consignes `AI_INSTRUCTIONS.md`, le workflow Git, la documentation Export et
les règles pertinentes du registre des bugs ont été consultés.

- [PR #22](https://github.com/midka33/Outils-TAA/pull/22), fusionnée le 12 octobre :
  `0bbb60b28af94cc46c52987b6497e045bb676405`, ancêtre de `main`.
- [PR #23](https://github.com/midka33/Outils-TAA/pull/23), fusionnée le 13 octobre :
  `44503dff9415a17978a77c72a358ea8025a82c48`, tête de `main` contrôlée.
- CI PR #22 : [Export](https://github.com/midka33/Outils-TAA/actions/runs/38272981112)
  et [ruban](https://github.com/midka33/Outils-TAA/actions/runs/38272981062) réussis.
- CI PR #23 : [Export](https://github.com/midka33/Outils-TAA/actions/runs/38357553360)
  et [ruban](https://github.com/midka33/Outils-TAA/actions/runs/38357553480) réussis.
- L’arbre de `main` est exactement identique à celui de la tête testée de la
  PR #23 (`d90610a77c2c7568dfb8252b9bde1f48cc098593`). Cependant, aucune exécution
  Actions ni check run n’est attaché au merge commit de `main` lui-même.
- Tests exécutés localement sur ce commit de `main` : **323 Export réussis**,
  **79 Calculs réussis**. Les commandes sont ci-dessous.
- Différence depuis v1.0.3 : 30 fichiers modifiés, dans Export, ses tests et
  la documentation. Les modules Calculs et Plans de vente n’ont pas changé.
- Compatibilité cible : **Revit 2025.4 / pyRevit 5.x**. La validation fonctionnelle
  dans Revit a été confirmée par l’utilisateur pour les PR #22 et #23. Aucun
  nouveau test Revit n’a été exécuté dans cet environnement sans Revit.
- L’archive source de `main` contient deux fichiers temporaires suivis :
  `docs/09_Export_Project_Persistence.md.tmp` et
  `docs/09_Export_Project_Persistence.tmp`. Aucun cache Python, modèle `.rvt`,
  dessin `.dwg` ou MSI n’a été trouvé dans cette archive. La recherche ciblée de
  chemins personnels et de marqueurs de secrets n’a relevé qu’un exemple de
  chemin Windows dans les standards ; elle n’équivaut pas à un audit exhaustif.

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests OutilsTAA.extension/OutilsTAA.tab/Export.panel/tests --ignore=tests/calculation --ignore=tests/plans_vente --import-mode=importlib -q
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/calculation -q
```

## Prérequis restant avant publication

La PR de préparation corrige le changelog et les documents Export, retire les
fichiers temporaires, ignore les caches et active les contrôles Export et archive
sur `main`. Elle ne modifie aucun module fonctionnel ni le système d’installation.

La consigne de livraison interdit de fusionner une branche supplémentaire :
**la PR de préparation reste donc ouverte et la release n’est pas publiée**.
Une fois ces corrections intégrées dans `main` par le mainteneur :

1. Relever le nouveau SHA de `main` et vérifier tous ses contrôles Actions.
2. Vérifier que seuls les changements documentaires et de livraison attendus
   ont été ajoutés au code fonctionnel validé.
3. Recontrôler les livrables et les tags existants ; finaliser le changelog.
4. Créer un nouveau tag sur le SHA validé et publier une release stable.
5. Vérifier le tag, le SHA, les liens et les éventuels fichiers joints.

La distribution v1.0.3 comprend un ZIP, un script CMD et des tutoriels versionnés.
Les anciens workflows de publication ont leur version fixée dans le fichier :
**ne pas les déclencher pour fabriquer v1.1.0**, car ils peuvent modifier une
ancienne release. Conserver le format et le système d’installation existants,
ne pas fabriquer de MSI et ne pas réutiliser un installateur visant v1.0.3.
Les archives source GitHub contiennent aussi les modules en développement ;
leur présence ne constitue pas une validation de ces modules.

## Notes de version proposées — à publier après levée des prérequis

### Outils TAA v1.1.0 — Arborescence Export et nommage PDF/DWG

Cette version améliore l’organisation et la publication du module **Export**.
Les évolutions des [PR #22](https://github.com/midka33/Outils-TAA/pull/22) et
[#23](https://github.com/midka33/Outils-TAA/pull/23) ont été validées par
l’utilisateur dans **Revit 2025.4 avec pyRevit 5.x**.

### Nouveautés

- Dossiers et anciens carnets utilisent une présentation commune. Des
  sous-dossiers peuvent être créés dans les dossiers existants, y compris ceux
  contenant déjà des mises en page.
- Glisser-déposer proche de l’Explorateur Windows : insertion avant ou après
  (15 % de chaque côté) et dépôt à l’intérieur (70 % au centre), sur les dossiers
  ouverts ou fermés. Déplacement multiple, ouverture au survol et défilement
  automatique facilitent la réorganisation.
- Hiérarchie conservée à la réouverture, protection contre les cycles, héritage
  des paramètres et publication récursive. Les anciennes données sont migrées
  automatiquement vers le schéma 8.
- Règle de nommage DWG distincte de celle des PDF. Le champ DWG reste toujours
  visible ; il suit le nommage PDF et reste grisé par défaut. Il peut être
  dissocié manuellement et devient automatiquement indépendant en mode PDF combiné.
- Les règles PDF/DWG bénéficient de l’héritage et de la persistance, avec lecture
  compatible des anciennes configurations.

### Corrections

- Les mises en page peuvent être déplacées vers un dossier nouvellement créé
  ainsi qu’entre dossiers.
- Un dossier devenu vide reste présent. Les sous-dossiers, leur position et leurs
  paramètres sont conservés lors des déplacements et conversions internes.

### Validation et périmètre

- Cible : **Autodesk Revit 2025.4 / pyRevit 5.x**.
- Tests hors Revit sur le code fonctionnel de référence : **323 Export** et
  **79 Calculs** réussis. Ajouter les résultats CI du commit finalement publié.
- Cette livraison porte sur Export. Les Calculs des pièces restent au périmètre
  livré en v1.0.3 ; aucune nouvelle stabilité globale n’est annoncée.
- Plans de vente et les autres outils en développement ne sont pas présentés
  comme terminés ou stables.
- Aucun installateur MSI ni changement du système d’installation.
