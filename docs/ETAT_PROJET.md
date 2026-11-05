# Outils TAA — État de reprise du développement

**Mise à jour initiale :** 2026-11-05  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x  
**Dépôt :** `midka33/Outils-TAA`  
**Branche de référence :** `main`  
**Dernier commit consulté lors de cette initialisation :** `cebf83642a2b9c5418b84d2c6ebcc041eaa45263` — `release: publier Outils TAA v1.4.1 stable (#52)`.

> Ce fichier est un **point d'entrée de reprise**, pas un substitut à la documentation technique ni aux tests. Actualiser les faits à chaque nouvelle session. Les constats ci-dessous ont été établis par lecture de GitHub, sauf mention explicite.

## Ordre de lecture obligatoire

1. `AI_INSTRUCTIONS.md`, puis `docs/INDEX.md`.
2. `docs/11_BUGS_Prevention_Registry.md`, `docs/bugs/INDEX.md` et le registre du module.
3. Documentation fonctionnelle du module (voir ci-dessous).
4. Derniers commits, PR et issues ouvertes sur GitHub ; vérifier si la branche de travail diffère de `main`.
5. Rapports de tests et comptes rendus Revit correspondant **à la version exacte testée**.

## Modules — état de référence

| Module (nom actuel) | Document principal | Situation vérifiée / limites |
| --- | --- | --- |
| **Export** (ancien PublisherAI) | `docs/09_Export.md` | v1.4.0 documentée comme validée dans Revit pour EXPORT-01 à 06 ; nouveau commit de release **v1.4.1** présent sur `main` au 05/11/2026. Ne pas attribuer les recettes v1.4.0 à v1.4.1 sans vérification. |
| **Calculs des pièces** (ancien RoomCalculator) | `docs/10_Calculs_Pieces.md` | README consulté : fonctionnalités v1.0.3 ; résolution interactive des divergences de groupes hors périmètre. |
| **Plans de vente** | `docs/20_Plans_de_Vente.md` | V1.1 fichiers liés, livrée avec v1.3.0 et documentée comme validée dans Revit. Ne pas confondre cette validation historique avec des corrections en cours. |
| **Légendes automatiques** | Spécification à préciser | Planifié dans le README : légendes issues des gabarits / couleurs de pièces, partagées entre vues, échelle de référence. |
| **Giration des véhicules** | `docs/25_Giration_Vehicules.md`, issue #40 | Planifié, développement non commencé ; priorité au prototype d'interaction dans Revit. |
| **Autres modules** | `README.md` / `ROADMAP.md` | Carnets de menuiseries extérieures et plans de repérage en préparation ; cotation, étiquetage, contrôle, annotation, utilitaires planifiés selon le README consulté. |

## Sujet à reprendre — anomalie 23/24 cotes

**Source :** dernier message montré par l'utilisateur dans une capture d'une conversation ChatGPT devenue trop longue. **Cette information n'a pas encore été recoupée avec le rapport de test ni avec le commit spécifique.**

- Symptôme rapporté : génération de **23 cotes au lieu de 24**.
- Correction : **annoncée comme ayant passé les tests automatisés** dans la conversation précédente ; SHA et rapport exacts **non identifiés** ici.
- Vérification dans la maquette Revit : **non effectuée / non confirmée** dans la capture.
- **Statut : validation Revit en attente.**
- **Prochaine action :** retrouver la branche, le correctif et les résultats automatisés précis ; récupérer le nouveau rapport d'exécution Revit ; comparer les 24 cotes attendues aux cotes effectivement créées et contrôler les non-régressions.
- Ne pas déclarer ce bug clos sans preuve de recette Revit.

## Règles de mise à jour après étape significative

Pour chaque changement : noter **date, module, branche, commit, problème, décision, fichiers modifiés, tests automatisés (commande/résultat), recette Revit (maquette/version/résultat), régressions éventuelles, problèmes ouverts et prochaine action**.

Statuts à distinguer : **proposé → implémenté → testé automatiquement → testé dans Revit → validé**. Ne jamais sauter une étape par présomption.

Ne pas modifier le code stable ni les fonctionnalités validées sans analyse des risques de régression et accord utilisateur. Pour toute modification fonctionnelle, respecter `AI_INSTRUCTIONS.md` et actualiser la documentation du module.

## Commandes de reprise entre conversations ChatGPT

- **« Reprends le développement Outils TAA »** : relire ce fichier, les instructions du dépôt, la documentation utile et les derniers commits ; présenter l'étape réellement confirmée.
- **« Fais un point de sauvegarde du développement »** : vérifier les changements et tests puis proposer/écrire, lorsque l'accès GitHub l'autorise, la mise à jour documentaire avec commit et SHA ; ne jamais inventer une validation.

## Historique de transmission

- **2026-11-05 — Initialisation du suivi inter-conversations :** consultation du dépôt et création de ce point d'entrée. **Aucun changement de code ni test Revit effectué dans cette opération.**
