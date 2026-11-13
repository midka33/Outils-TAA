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

## Décision d'architecture cible — mutualisation des moteurs (05/11/2026)

**Décision utilisateur confirmée :** à terme, **Plans de vente**, **Cotation automatique** et **Étiquetage automatique** doivent utiliser **les mêmes moteurs communs de cotation et d'étiquetage**, et non trois implémentations distinctes.

- Extraire progressivement la logique géométrique, de recherche de références Revit, de placement et de collisions dans des services partagés, avec des interfaces stables.
- Conserver des adaptateurs et politiques propres à chaque outil (vues de plans de vente, vues ordinaires, groupes, réglages et contraintes graphiques) : mutualiser le moteur ne signifie pas uniformiser tous les comportements.
- **Ne pas refactoriser immédiatement la bêta** : achever d'abord les recettes en cours (dont REV-ANN-124) et protéger Plans de vente V1.1 par des tests de non-régression.
- La migration des services de Plans de vente vers la bibliothèque commune est **une étape future à planifier et tester** ; elle n'est ni implémentée ni validée par cette décision.

## Résultats Revit — Cotation et Étiquetage (05/11/2026)

- **Cotation auto / REV-ANN-124 :** l'utilisateur confirme **24 annotations créées pour 12 pièces** après récupération de la branche bêta. Résultat numérique atteint ; contrôle des valeurs, de la seconde exécution sans doublon et des non-régressions toujours à documenter avant clôture complète.
- **Étiquetage auto / Collectifs A_Niveau 1 :** **44 pièces hors groupe détectées**, **37 annotations créées**, **7 placements rejetés**. Erreur répétée : `ValueError: Aucune position interieure sans chevauchement.` dans l'adaptateur `GenericRoomTags._place_one_tag()` (`Annotations.panel/services/annotations_service.py`, ligne 89), appelé par `PlansDeVente.panel/services/room_tag_service.py`. Les échecs de placement sont isolés ; d'autres étiquettes ont été créées.
- **Cause immédiate confirmée par lecture du code :** l'adaptateur bêta exige une étiquette entièrement intérieure et sans collision ; si `fully_inside` est faux ou `collision` vrai, il lève `ValueError`. **Cause géométrique exacte des sept refus non identifiée** : dimensions des pièces, cotes présentes et candidats de placement à diagnostiquer.
- **Prochaine action :** améliorer, uniquement dans l'adaptateur Étiquetage, la remontée de diagnostics par pièce (identifiant, candidats, collision ou débordement), puis proposer une recherche de positions supplémentaires sans chevauchement. Conserver intact le comportement Plans de vente et tester les non-régressions. Ne pas déclarer Étiquetage validé.

## Décision et correctif Étiquetage auto — 05/11/2026

**Décision métier :** une étiquette doit être créée dans chaque pièce qui possède un point d'ancrage intérieur valide, même si le texte chevauche des éléments ou déborde graphiquement ; l'utilisateur assurera ensuite les ajustements de lisibilité. Ne pas appliquer cette règle au module Plans de vente sans décision explicite.

**Implémenté sur `feature/annotations-automatiques-beta` :** suppression du refus de collision dans l'adaptateur `GenericRoomTags`, commit `71ff96a3a75ac85c9b59449ec610fb2e3aa9207f` ; documentation de branche actualisée dans `docs/21_Annotations_Automatiques.md`, commit `6aa916f4327f2f1a291f149185925d39fd60835b`. Moteur d'étiquetage Plans de vente non modifié. **Validation Revit des 44 pièces encore en attente ; tests automatisés non exécutés dans cette intervention.**

## Recette Étiquetage — 44 pièces (05/11/2026)

**Retour de test utilisateur sous Revit 2025.4, module Étiquetage automatique bêta :** vue `Collectifs A_Niveau 1`, **44 pièces détectées (0 en groupe)**, **44 étiquettes créées**. Le précédent résultat de 37/44 est résolu sur ce cas après suppression du refus systématique des collisions dans l'adaptateur.

**Avertissements acceptés par décision métier :** emprise graphique débordante pour les pièces 2222, 2223, 2250, 2252 ; collision non résolue et meilleure position intérieure conservée pour 2249, 2251, 2252, 2253. Ces avertissements n'empêchent pas la création ; l'utilisateur repositionne les étiquettes illisibles.

**Statut précis :** génération 44/44 **validée sur cette vue**, pas validation globale du module. Reste à tester : étiquettes existantes / seconde exécution sans doublons, plusieurs vues, groupes de modèle et non-régression Plans de vente. Ne pas confondre validation de cette recette et fusion de la PR #37.

## Étiquetage auto — deuxième lancement (05/11/2026)

Sur `Collectifs A_Niveau 1`, 44 pièces hors groupe détectées, **0 nouvelle étiquette créée** au second passage ; 44 messages génériques « annotations deja presentes ou vues non cotables ». Ceci est **compatible avec l'absence de doublons** après le premier passage à 44/44, mais l'état des étiquettes visibles et de leur association à chaque pièce n'a pas été confirmé explicitement. **Ne pas déclarer un test anti-doublons intégralement validé sur la base du seul compteur 0.** Améliorer ultérieurement le diagnostic « déjà présente » vs « impossible / vue non admissible », avec formulation spécifique à l'étiquetage.

## Validation Revit — anti-doublons Étiquetage auto (05/11/2026)

**Confirmation explicite de l'utilisateur :** après un premier lancement ayant créé **44 étiquettes pour 44 pièces** dans `Collectifs A_Niveau 1`, le deuxième lancement a créé **0 annotation supplémentaire**, et **les 44 étiquettes initiales sont toujours visibles**. **Test anti-doublons validé sur cette vue**, sans suppression des étiquettes existantes. Ne pas extrapoler aux groupes de modèle, aux autres vues ou aux autres types d'étiquettes non testés.

Amélioration non bloquante à prévoir : remplacer le message répété « annotations deja presentes ou vues non cotables » par une indication spécifique et comptabilisée (« étiquette déjà présente »), distincte des vrais refus.

## Développement groupes de modèle — sécurisation initiale (05/11/2026)

**Objectif :** étiqueter les pièces appartenant à un groupe de modèle avec des groupes de détails attachés, réutilisables sur les occurrences. La cotation en groupe reste volontairement désactivée après un crash antérieur ; ne pas la réactiver sans protocole de validation distinct.

**Implémenté sur la branche bêta :** vérifications renforcées de `_attach()` après `Document.Create.NewGroup` : rejet d'un résultat invalide ou ambigu, exigence d'un seul nouveau type de groupe de détails, et vérification d'une instance `Group.IsAttached` dont `AttachedParentId` correspond au groupe initial. En cas de doute, levée d'exception et rollback des transactions afin de protéger le groupe de modèle. Commit code : `ef8ff7f5c0496282a32456df1a77fe656330e52e`.

**Statut exact :** correction de sécurité implémentée, **aucun test automatisé ni test Revit exécuté** sur cette modification. L'API `NewGroup` mixte peut ne pas rattacher des détails à un groupe de modèle déjà existant ; les garde-fous peuvent donc refuser l'opération, ce qui est attendu tant que la faisabilité n'est pas prouvée. **Aucune fonctionnalité groupe déclarée validée.**

**Recette prioritaire sur une COPIE de maquette :** un groupe modèle ne contenant qu'une ou deux pièces, lancer d'abord **Étiquetage auto** ; vérifier absence de modification du groupe d'origine, création effective d'un groupe de détails attaché et possibilité d'afficher ce type sur une autre occurrence. Après une relance, aucun doublon. En cas de refus, collecter le rapport complet ; ne pas supprimer ou dégrouper l'original. La recette cotation en groupe est séparée et suspendue.

## Déploiement agence — décision et observation du 12/11/2026

**Méthode de référence confirmée par l'utilisateur :** le dossier `OutilsTAA.extension` est hébergé en une copie commune sur le serveur de l'agence. Chaque poste possède Revit/pyRevit et référence l'emplacement réseau de l'extension dans ses chemins pyRevit. Les mises à jour de l'extension sont opérées **sur le serveur** ; l'installateur CMD des releases n'est pas utilisé pour la distribution quotidienne et reste une alternative.

**Observation de déploiement :** après ajout du chemin réseau pendant une session Revit déjà ouverte, le ruban Outils TAA ne s'affiche pas immédiatement ; après redémarrage, il apparaît. Les postes équipés de pyRevit 7.0.0 semblent charger les outils, mais aucune recette complète 7.0.0 n'est consignée. Revit 2023 est également installé sur certains postes, où apparaît l'avertissement pyRevit `Ambiguous host product "23.1.10.4"` ; ne pas le traiter comme un bug Outils TAA confirmé.

**Statut :** procédure documentée uniquement ; aucun changement de code ni du package d'installation, aucun test automatisé ni test supplémentaire Revit effectué dans cette mise à jour. Les faits terrain sont déclaratifs ; les précautions opérationnelles (maintenance, sauvegarde, redémarrage et retour arrière) restent à éprouver lors du prochain déploiement.

**Référence :** [`docs/26_Deploiement_Agence.md`](26_Deploiement_Agence.md). **Prochain contrôle :** recette de mise à jour/retour arrière sur poste pilote ; matrice Revit 2025.4 + pyRevit 5.x / 7.0.0, sans modifier les fonctionnalités métier validées.


## Retour de recette des groupes — refus NewGroup et correctif (12 novembre 2026)

**Rapport utilisateur :** `Niveau 0` : 8 pièces dont 8 en groupe, aucune hors groupe ; `Groupe 1` et `Groupe 2` : refus `Resultat NewGroup ambigu : groupe de modele protege`, 0 annotation créée, traitement annulé sans annotation isolée.

**Diagnostic :** exception levée par le contrôle de l'adaptateur, pas une exception Revit directe. Le test `created.GetTypeId() == original_type` était trop strict : il ne démontre pas une altération du modèle groupé.

**Correctif ciblé sur la branche :** suppression de ce seul rejet d'égalité de type (commit `1eb32ce35798a545a9f155b4e3626f4eb0a6b0eb`) ; contrôle du groupe d'origine, de l'unicité du type de détails attachés et de son parent maintenus. Aucune modification du moteur Plans de vente, ni réactivation de la cotation dans les groupes.

**Statut : implémenté, tests automatisés non exécutés, recette Revit non réalisée pour cette révision.** Reprendre le même test sur une **copie de la maquette**, et fournir le rapport ; en cas de succès vérifier les groupes d'origine inchangés, la présence de détails attachés et la visibilité dans une seconde occurrence.


## Second retour Revit sur les groupes — 12 novembre 2026

**Reproduction :** vue `Niveau 0`, 8 pièces dont 8 dans `Groupe 1` et `Groupe 2`, 0 nouvelle étiquette. Le correctif précédent aboutissait à `RuntimeError: NewGroup a retourne le groupe initial : creation de details non prouvee.` dans `_attach()`, avec annulation des deux transactions.

**Diagnostic confirmé :** `Document.Create.NewGroup` retourne une instance de groupe de modèle lorsque des éléments de modèle et des annotations sont associés (guide Autodesk Revit API). L'égalité de l'identifiant retourné avec celui du groupe initial **n'est pas une preuve suffisante d'échec**. En revanche, ce retour ne prouve pas non plus la création d'un groupe de détails attaché.

**Correction expérimentale (branche `feature/annotations-automatiques-beta`) :** commit `5635fd5d2c59e3b09dfab15720ed21c257b64103`. Ne plus rejeter le seul retour du groupe initial ; vérifier à la place (1) l'invariance du type et des membres du groupe modèle, (2) la création d'un seul nouveau type de détails attachés, (3) l'existence d'une instance `Group.IsAttached` reliée au parent attendu via `AttachedParentId`, (4) l'appartenance de **toutes les nouvelles étiquettes** au groupe de détails. Recherche des groupes attachés au niveau du document pour éviter d'exclure ceux non encore visibles dans la vue. En cas de preuve manquante, rollback des opérations.

**Vérifications statiques ciblées :** présence du contrôle de parent, des membres, du rollback et de l'exigence d'un type unique ; absence du rejet direct sur `created.Id == group.Id`. Cela ne remplace **ni pytest ni la recette Revit**.

**Recette à refaire sur une copie de la maquette :** mettre la branche à jour, relancer Étiquetage auto sur `Niveau 0`, vérifier que les huit pièces sont étiquetées dans des groupes de détails attachés à `Groupe 1` et `Groupe 2`, que les groupes d'origine sont intacts et que la réutilisation sur une deuxième occurrence fonctionne. Si un nouveau garde-fou bloque, fournir le rapport complet et ne pas contourner les contrôles. **Cotation dans les groupes toujours désactivée ; Plans de vente non modifié.**


## BUG-COMMON-030 — TypeError ElementId/int lors du rattachement des groupes (13 novembre 2026)

**Retour Revit 2025.4 :** Étiquetage auto sur `Niveau 0`, 8 pièces dans `Groupe 1` et `Groupe 2`, 0 étiquette créée. Les deux unités sont annulées dans `_attach()` par `TypeError: expected ElementId, got int` lors de `self.doc.GetElement(next(iter(new_ids))).Id`.

**Cause certaine :** la différence d'ensembles `new_ids = available - previous` utilise des valeurs Python `int` issues de `id_value()`. `Document.GetElement` exige un `DB.ElementId`, pas un entier. L'exécution franchissait les contrôles du groupe initial et trouvait exactement un nouveau type attaché avant cet appel.

**Correction ciblée, commit `826a02db8efe401367c4be37d1b8e54c4258f403` :** construire `available_type_ids = {id_value(element_id): element_id for element_id in group.GetAvailableAttachedDetailGroupTypeIds()}`, utiliser les clés entières pour la différence d'ensembles, puis récupérer le vrai `ElementId` avec `available_type_ids[next(iter(new_ids))]`. Contrôles du parent, des membres et de rollback conservés.

**Prévention :** toute conversion d'un `DB.ElementId` en entier doit être réservée aux comparaisons/logs ; conserver l'objet natif pour les API Revit qui attendent `ElementId`.

**Anti-régression :** test stdlib `tests/test_annotations_attached_group_elementid.py` ajouté au commit `a841b597948112f5e69742c591698462dc3a59e6` : extrait les affectations réelles de `_attach()` et vérifie avec un faux `Document.GetElement` strict qu'un `ElementId` natif est transmis. **Test non exécuté dans cet environnement ; validation réelle Revit en attente.**

**Recette :** sur copie de maquette, relancer les deux groupes de la vue `Niveau 0` ; vérifier la création des étiquettes, leur appartenance effective à un groupe de détails attachés et la conservation des groupes de modèle. Ne pas fusionner la PR #37 avant validation. Le moteur Plans de vente est inchangé, cotation groupée toujours suspendue.


## Validation Revit — Étiquetage dans deux groupes de modèle (13 novembre 2026)

**Rapport utilisateur sous Revit 2025.4 après le correctif `ElementId` (`826a02db8efe401367c4be37d1b8e54c4258f403`) :** commande `Étiquetage automatique - version beta`, vue **`Niveau 0`**, **8 pièces détectées**, **8 pièces dans des groupes de modèle**, **0 hors groupe**, **8 annotations créées**. **Aucune erreur bloquante.** Une seule réserve de présentation sur la **pièce 27** : emprise graphique de l'étiquette partiellement hors pièce, acceptée selon la règle métier (ancrage intérieur, repositionnement manuel autorisé).

**Validation confirmée :** le traitement groupé produit les **8 étiquettes attendues** pour les deux groupes précédemment identifiés (`Groupe 1` et `Groupe 2`) dans cette vue, sans exception signalée. **Ne pas surinterpréter :** le rapport de création ne démontre pas visuellement la réutilisation sur une autre occurrence du groupe, l'intégrité structurelle vérifiée par l'utilisateur, ni l'absence de doublons au deuxième lancement. Les contrôles de sécurité implémentés dans `_attach()` restent actifs ; à vérifier dans la maquette et lors d'une seconde exécution.

**Recettes restantes :** afficher les détails attachés sur une **autre occurrence de chaque groupe** ; vérifier le regroupement et les étiquettes dans cette occurrence ; relancer `Étiquetage automatique` pour confirmer la réutilisation sans doublons et l'intégrité des groupes modèles. **Cotation dans les groupes toujours non validée / désactivée en bêta**. **Plans de vente non modifié.** PR #37 à maintenir en brouillon.


## Validation Revit — relance au même endroit des groupes attachés (13 novembre 2026)

**Retour utilisateur, Revit 2025.4 :** deuxième exécution du module **Étiquetage automatique** dans la **même vue** `Niveau 0` et sur les **mêmes occurrences de groupes** que lors du test précédent. Rapport : **8 pièces détectées, 8 en groupe, 0 hors groupe ; 0 nouvelle annotation** ; messages explicites `Groupe 1 : details attaches reutilises.` et `Groupe 2 : details attaches reutilises.`. Aucune exception signalée.

**Validé dans ce périmètre :** l'outil reconnaît les groupes de détails attachés qu'il a créés et ne recrée pas d'étiquettes sur les **mêmes occurrences, dans la même vue**, lors du second lancement. La création initiale 8/8 avait été validée dans le test précédent.

**Toujours en attente :** vérification visuelle des étiquettes sur une **autre occurrence** de chaque groupe de modèle, contrôles d'intégrité des groupes et cotation automatique dans les groupes. Ne pas confondre deuxième lancement au même endroit et propagation/réutilisation sur une occurrence distincte. Pas de fusion PR #37 sur ce seul résultat.


## Recette Revit — seconde occurrence des groupes, Niveau 1 (13 novembre 2026)

**Retour utilisateur sous Revit 2025.4 :** test du module **Étiquetage automatique** sur une **seconde occurrence** dans la vue `Niveau 1` (distincte de la recette initiale sur `Niveau 0`). Rapport : **8 pièces**, toutes dans des groupes de modèle, **0 étiquette nouvellement créée** ; `Groupe 1 : details attaches reutilises.` et `Groupe 2 : details attaches reutilises.`. **Aucune erreur signalée.**

**Validé sur ce scénario :** le module reconnaît et réutilise les deux types de groupes de détails attachés sur cette autre occurrence/vue, sans recréer d'annotations. Cela complète la création initiale **8/8** sur Niveau 0 et la relance **0** dans la même vue.

**Limite de preuve :** ce rapport confirme la reconnaissance et l'appel à l'affichage de groupes attachés, **mais pas à lui seul le contrôle visuel de l'emplacement et de la visibilité effective des 8 étiquettes sur Niveau 1**. Ne pas déclarer ce dernier contrôle accompli sans retour explicite. Vérifier également l'intégrité du modèle et les cas de groupes atypiques si nécessaire.

**Suite :** traiter la cotation automatique dans les groupes de modèle (encore suspendue après crash historique), sur branche bêta et copie de maquette, avec non-régression sur la cotation hors groupes et le moteur stable Plans de vente. La PR #37 reste en brouillon.


## Validation Revit — visibilité sur seconde occurrence, Niveau 1 (13 novembre 2026)

**Confirmation explicite de l'utilisateur :** après la recette `Niveau 1` du module **Étiquetage automatique**, les étiquettes des deux groupes de détails attachés (`Groupe 1` et `Groupe 2`) sont **visibles et correctement positionnées sur la seconde occurrence**. Le rapport correspondant indiquait 8 pièces appartenant à des groupes, 0 nouvelle annotation créée, et la réutilisation des groupes de détails attachés pour Groupe 1 et Groupe 2.

**Statut : VALIDÉ DANS REVIT 2025.4 sur les occurrences testées.** Chaîne vérifiée : génération initiale de 8 étiquettes sur `Niveau 0`, relance sans doublons sur `Niveau 0`, reconnaissance et réutilisation sur `Niveau 1`, puis confirmation utilisateur de l'affichage correct sur la seconde occurrence. Cette validation couvre ces deux groupes et ces deux niveaux, sans généraliser à tous les cas de groupes ni à la cotation automatique dans les groupes.

**Suite :** développer et recetter séparément la cotation automatique dans les groupes (encore suspendue en bêta), en protégeant les moteurs validés et la version stable Plans de vente. Ne pas fusionner la PR #37 sur le seul fondement de cette validation.


## Développement cotation automatique par groupe — 13 novembre 2026

**Branche de développement :** `feature/annotations-automatiques-beta` ; **PR #37 brouillon** (non fusionnée). Étape suivante après validation Revit de l'étiquetage groupé sur `Niveau 0` et `Niveau 1`.

**Correction implémentée (non validée dans Revit) :** dans **Cotation automatique**, nouveau mode bêta **« Un groupe de modèle dans cette vue (12 pièces max.) »**. Le lanceur demande une seule vue, un seul groupe explicitement choisi et affiche les pièces retenues pour confirmation. Le moteur partagé de cotation Plans de vente reste inchangé. Pour les références natives extérieures au groupe, des repères 2D courts (non associatifs au mur extérieur) peuvent être créés ; les repères inutilisés sont supprimés. La réutilisation et le rattachement des groupes de détails `TAA - Cotations` emploient les garde-fous validés par Étiquetage : protection de l'intégrité du groupe de modèle, présence de toutes les cotes et repères utiles dans les détails attachés, annulation en cas de doute.

**Commits de code :** `e74bfc9` (lanceur), `6231963` (périmètre ciblé), `0b8ee07` (références et nettoyage), `09729c1` (clarification de portée). **Test automatisé ajouté** : `tests/test_annotations_group_dimensions_beta.py` (commit `f7815b9`), **mais non exécuté dans cette intervention**. La revue statique de présence des garde-fous ne vaut pas test automatique ni validation Revit.

**Recette prochaine :** sous Revit 2025.4, **sur copie sauvegardée**, tester **un seul groupe simple** en choisissant le nouveau mode, vérifier cotes natives, valeurs et nus finis, groupes d'origine inchangés et groupe de détails réellement attaché. Ensuite seulement : plusieurs pièces, façade hors groupe / repères 2D, relance sans doublons, deuxième occurrence, non-régression de cotation hors groupe 24/24, étiquetage 44/44 et étiquetage groupé. **La PR #37 reste brouillon ; aucun traitement de masse autorisé avant recette.**

**Traçabilité PR :** ce fichier est ajouté également sur la branche bêta pour satisfaire l'instruction de suivi par PR. Le fichier a été créé initialement sur `main` après la divergence de cette branche ; **vérifier un éventuel conflit de fusion de ce fichier au moment de préparer la PR**, ne pas écraser le suivi plus récent de `main`.
