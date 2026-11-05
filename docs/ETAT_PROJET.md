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
| **Cotation automatique — outil autonome** | `docs/21_Annotations_Automatiques.md`, PR #37 | Bouton `Cotation auto` du panneau Annotations, réutilise `dimension_service.py` et la géométrie Plans de vente via adaptateurs. Bêta non fusionnée ; BUG-COMMON-028 en attente de recette Revit. |\n| **Étiquetage automatique — outil autonome** | `docs/21_Annotations_Automatiques.md`, PR #37 | Bouton `Étiquetage auto` distinct, réutilise `room_tag_service.py` de Plans de vente ; sélection du type d'étiquette. Bêta non fusionnée, recette autonome à poursuivre. |\n| **Légendes automatiques** | Spécification à préciser | Planifié dans le README : légendes issues des gabarits / couleurs de pièces, partagées entre vues, échelle de référence. |
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

## Reprise Annotations — conversation transmise le 05/11/2026

**Branche de développement :** `feature/annotations-automatiques-beta` ; PR #37 en brouillon. Ne pas fusionner dans `main` avant les recettes Revit.

- **BUG-COMMON-025 / loggia 2238 : validé par l'utilisateur dans Revit 2025.4.** Deux cotes natives ; valeurs correctes ; nus intérieurs alignés ; cotes visibles avec séparations de pièces masquées ; deuxième exécution sans doublon ni plantage. Rapport : deux chemins successifs couvrant 100 %, sans superposition, jeu 0 mm et décalage latéral 33 mm. La seconde cote n'est associative qu'à l'arête du garde-corps 16141871, non au garde-corps complémentaire 8951804.
- **Loggia 2240 : non-régression à effectuer.** Attendu : deux cotes natives correctes et visibles, sans recours 2D, ni doublons au second passage.
- **BUG-COMMON-028 / appartement de 12 pièces : non validé dans Revit.** Le dernier essai décrit dans la documentation de branche produisait 23 cotes sur 24, avec une seule cote pour la chambre 2247 lorsqu'elle était traitée au sein de l'appartement. Le correctif `2026-11-05-apartment-room-dedup-04` emploie `Dimension.Origin` et `Room.IsPointInRoom` pour éviter que des cotes voisines bloquent la chambre. **472 tests automatisés réussis selon la documentation de la branche**, mais recette REV-ANN-124 encore ouverte.
- **Prochaine action :** tester REV-ANN-124 sur copie de la maquette : 24 cotes sur 12 pièces si aucune n'est préexistante, vérifier 2,62 m et 3,33 m pour 2247, contrôler la non-régression des 11 autres pièces et l'absence de doublons à la deuxième exécution. Un compteur de créations sur maquette déjà cotée n'est pas un total de cotes présentes.

**Provenance :** conversation fournie par l'utilisateur et `docs/21_Annotations_Automatiques.md` consulté sur la branche bêta. Les validations ne sont pas étendues à des cas non testés.

## Clarification architecture — 05/11/2026

La PR #37 développe **deux outils autonomes distincts**, `Cotation auto` et `Étiquetage auto`, dans le panneau `Annotations`, à partir des moteurs déjà employés par **Plans de vente**. Ils disposent de boutons et de parcours indépendants, partagent certains adaptateurs et une bibliothèque géométrique. Les services d'origine de Plans de vente ne sont pas modifiés par la bêta d'après `docs/21_Annotations_Automatiques.md` sur la branche de développement. Les tests BUG-COMMON-025 et BUG-COMMON-028 décrits ci-dessus concernent **Cotation auto**, et ne constituent pas une validation générale de l'outil **Étiquetage auto**. Les deux outils restent en développement et nécessitent des recettes distinctes avant fusion.
