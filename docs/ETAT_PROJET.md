# Outils TAA — État de reprise du développement

## Nouveau chantier indépendant — Paramètres des pièces (23/11/2026)

**Retour de premier essai Revit (23/11) :** les deux boutons échouent à l'import
`System.Data.DataTable` sous IronPython (`ImportError: No module named Data`).
Correctif local : chargement explicite de l'assembly avant import ; boutons
déplacés dans `Commandes.stack` pour l'affichage compact demandé. Recette des
deux commandes et contrôle visuel du ruban **à refaire après publication**.
Registre : `docs/bugs/PARAMETRES.md`.

**Retour de Reload du 23/11 :** pyRevit ignore `Commandes.stack` avec
`The name already exists:Numeroter` ; anciens boutons encore visibles.
Correction locale : commandes renommées en interne pour éviter la collision
avec la session précédente. **Test après fermeture complète et réouverture
de Revit toujours en attente ; aucune validation visuelle acquise.**
Suite de non-régression locale : **971 tests réussis, 87 avertissements**.

**Deuxième retour Revit du 23/11 :** ruban compact confirmé après redémarrage.
Nouvelle itération locale : destination par défaut « N° Appartement », opération
texte « Remplacer », attributs explicites des zones de saisie et lignes d'aperçu
compactes. Le grisé des pièces déjà cliquées dans la vue Revit reste à concevoir
et à valider. Pas de validation clavier WPF après changement.
Tests de cette itération : **973 réussis, 87 avertissements** hors Revit.

**Troisième retour UI du 23/11 :** l'utilisateur demande désormais deux fenêtres
distinctes et confirme que les champs de numérotation restent non saisissables.
Deux XAML spécifiques créés, contrôleur métier partagé, réglages gauche
resserrés, tentative de correction du focus clavier. À confirmer dans Revit.
Suite automatisée après cette refonte : **973 tests réussis, 87 avertissements**.

**Décision suivante du 23/11 — Renommage multiple :** deux étapes WPF, dont
la deuxième comporte trois colonnes. Sélection pièces/familles puis choix
instance/type pour les familles. Ajout d'un service Revit de renommage générique
et d'un moteur de formatage littéral restreint. Recette Revit en attente ;
types de familles et saisie clavier restent des points sensibles.
Après cette étape : **975 tests automatisés réussis, 87 avertissements**.

**Retour Revit du 23/11 :** l'utilisateur confirme que la fenêtre **Numéroter
les pièces** est bonne ; la conserver intacte. Dans le renommage, la catégorie
mixte Ajouter/Supprimer est scindée en **quatre opérations de premier niveau** :
Ajouter, Supprimer, Remplacer, Formater. Recette des nouvelles options WPF à faire.
Suite de non-régression : **976 tests réussis, 87 avertissements** hors Revit.

**Retour utilisateur du 26/11 :** fonctionnement du renommage confirmé.
Amélioration UI demandée : remplacer l'affichage « Élément » par la valeur
du paramètre choisi à l'étape 1 dans la liste et l'aperçu du renommage.
Identifiants `UniqueId` préservés pour la sélection et l'écriture ; recette
de ce nouvel affichage encore à effectuer dans Revit.

**Demande du 26/11 — mode Formater :** ajout d'une liste des paramètres lisibles
disponibles sur les éléments sélectionnés et insertion de jetons liés aux ID
Revit (`{param_...}`). Résolution des valeurs par élément lors de l'aperçu,
sans modifier le paramètre cible ; recette WPF/Revit attendue.
Contrôles : 11 contrats WPF en exécution directe et formatage pur validés,
compilation Python réussie. `pytest` absent : suite complète non relancée.

**Correction ergonomique du 26/11 :** le champ FORMAT doit montrer le nom des
paramètres et non leur ID. Alias affichés `{Nom du paramètre}` résolus à partir
des identifiants internes ; doublons homonymes suffixés `(2)`, `(3)` pour éviter
les choix implicites. Recette Revit attendue.
Contrôles : 11 contrats WPF et essais ciblés d'alias réussis ; compilation
Python réussie. Suite complète indisponible (absence de `pytest`).

**Ajustement UI du 26/11 — Formater :** le sélecteur « Paramètre à insérer »
est désormais placé avant le champ FORMAT ; la ligne désactivée « Non utilisé »
est masquée dans ce mode. Les champs nécessaires aux autres opérations restent
visibles. Contrat statique ajouté ; validation visuelle dans Revit en attente.

**Valeur initiale du format (26/11) :** le paramètre de destination choisi à
l'étape 1 est présélectionné dans « Paramètre à insérer » et inséré par défaut
dans FORMAT sous son nom lisible ; repli sur `{valeur}` si absent des sources
lisibles. Recette dans Revit toujours nécessaire.

**Validation utilisateur du 26/11 :** le format par défaut affichant le
paramètre choisi à l'étape 1 fonctionne dans Revit.

**Nouvelle évolution — catégories de renommage (26/11) :** seules les catégories
« Pièces » et « Textes » sont proposées dans le premier écran. Les textes sont
des annotations `DB.TextNote` : choix de paramètre grisé, passage à l'étape 2
sans ce choix, aperçu avant/après et transaction atomique. Pour les annotations,
l'écriture passe par `TextNote.Text` ; la mise en forme locale peut être affectée,
ce qui est signalé dans l'interface. Fonctionnalités de familles retirées du
sélecteur à la demande de l'utilisateur (code de service conservé). **Recette
Revit nécessaire**, notamment annotations multi-lignes/formatées, sélection
actuelle et vue active ; la numérotation n'a pas été modifiée.

**Simplification de l'étape 1 (26/11) :** le champ « Niveau » a été retiré
de l'interface et du contrôleur : le renommage fonctionne directement sur les
instances ou les annotations textuelles. Validation WPF/Revit en attente.

**Extension des catégories (26/11) :** ajout de « Fenêtres », « Sols »,
« Plafonds », « Toits », « Murs » et « Portes » à la sélection de renommage,
en complément de « Pièces » et « Textes ». Collecte par `BuiltInCategory`
dans le périmètre choisi, exclusion des types et éléments groupés ; édition
des paramètres texte d'instance uniquement. Les notes textuelles gardent leur
édition directe. Tests de contrat ajoutés ; **recette dans Revit requise**
pour chaque catégorie et pour les paramètres propres aux familles.

**Retour utilisateur — portes/fenêtres vides (26/11) :** correction ciblée de
la collecte avec `DB.FamilyInstance` pour ces deux catégories et message
explicite lorsque le périmètre « Sélection actuelle » n'en contient pas.
Cause exacte du retour non démontrée faute de trace d'exécution Revit ; recette
sur sélection courante, vue active et projet entier toujours nécessaire.

**Diagnostic confirmé par captures Revit (26/11) :** « Collecte impossible :
Name » pour Fenêtres et Portes sur « Vue active ». Ce message désigne une
exception lors de la construction des libellés (accès direct à `Symbol.Name`),
pas une collecte nécessairement vide. Correctif : lecture des noms par
`DB.Element.Name.GetValue` et repli sur l'identifiant. Test de contrat ajouté ;
recette Revit requise.
Contrôles disponibles : 10 tests statiques WPF réussis en exécution directe,
compilation Python et `git diff --check` réussis. `pytest` absent de
l'environnement courant : pas de nouveau résultat de suite complète.

Branche locale `feature/room-parameter-tools`, issue de `main` au commit
`149df13bb818f44fa7c17aca6973bf3e47eaa69f` (v1.5.0).
Décision utilisateur : nouveau panneau **Paramètres** avec deux boutons
indépendants **Numéroter** et **Modifier texte** ; préserver **Calculs des pièces**.
Moteurs métier purs créés (`lib/room_parameters`) et **20 tests ciblés réussis**
hors Revit ; **965 tests de la suite complète réussis** (87 avertissements).
Documentation : `docs/29_Parametres_Pieces.md`.
**Point d'arrêt demandé : conception des interfaces WPF** — présenter trois
approches, recueillir le choix avant d'implémenter le XAML.
**Suite du 23/11 :** utilisateur a choisi la proposition 3 et demandé une seule
fenêtre sans parcours en plusieurs fenêtres. Première implémentation des deux
boutons et d'un XAML commun avec prévisualisation et confirmation intégrées.
Le raccordement Revit/WPF reste **non testé en condition réelle** ; première
suite de raccordement : **968 tests hors Revit réussis**.

**Audit de conformité du 23/11 :** charte WPF commune raccordée,
services Revit séparés du code-behind, icônes ajoutées, préférences locales,
logs et résumé d'exécution intégrés ; contrôle de doublons réévalué après
exclusions. Suite complète : **969 tests automatisés réussis** ; aucune
recette dans Revit. Détails et limites : `docs/29_Parametres_Pieces.md`.
`main` inchangée ; branche non fusionnée.


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


## BUG-COMMON-031 — Cotation groupée en biais : deux longueurs de murs presque parallèles (13 novembre 2026)

**Recette utilisateur — Revit 2025.4, vue `Niveau 1`, `Groupe 1`, 4 pièces :** **8 annotations créées** et rattachées sans exception ; marqueur `2026-11-13-group-dimensions-01`. Les pièces **12, 13, 14 et 15** indiquent toutes **0 axe entre faces opposées**. Le moteur emploie le repli `length_references` : mesures des **longueurs de murs**, pas des largeurs entre deux nus opposés. La capture montre notamment des cotes suivant deux longs murs de directions voisines et des chevauchements texte/témoins. **Rattachement technique du groupe confirmé ; qualité et signification géométrique des cotes NON VALIDÉES.** Le libellé `DIAGNOSTIC 2247` apparaît sur ces pièces car il était historiquement codé en dur ; ce n'est pas leur identité.

**Cause :** `DimensionService._fallback_length_indexes` (moteur Plans de vente inchangé) fournit des candidats de secours par directions puis autorise d'autres longueurs, dont certaines proches angulairement. Dans une pièce biaise sans faces opposées parallèles, deux créations peuvent correspondre à deux longueurs quasi parallèles plutôt qu'à deux orientations principales indépendantes. Revit ne peut pas produire une cote linéaire native entre deux faces non parallèles en les considérant comme une paire parallèle.

**Correction bêta ciblée, code Annotations uniquement :** module pur `lib/annotations/group_length_axes.py` (`17a2cad`) et surcharge de `GenericDimensions._fallback_length_indexes` sur les **groupes seulement** (`37511c5`). Lorsque les faces opposées sont absentes, sélection de deux longueurs de murs disposant de deux références natives sur des axes séparés d'au moins **30°**, classement selon **produit des longueurs × ouverture angulaire**. Avec une paire de faces déjà reconnue, une seule longueur complémentaire peut être retenue dans une direction distincte. Si seule une orientation est disponible : créer au plus **une cote**, plutôt que fabriquer artificiellement deux cotes de même direction. La politique d'origine s'applique sans changement aux pièces hors groupe et aux Plans de vente.

**Diagnostic renforcé :** marqueur `2026-11-13-group-dimensions-02`, avertissement explicite `GROUPE / SECOURS LONGUEURS DE MURS` précisant qu'une longueur de mur n'est **pas une largeur mesurée entre deux nus opposés**, et suppression du libellé spécifique `DIAGNOSTIC 2247` dans la ligne générique. Les chevauchements restent signalés et nécessitent un contrôle graphique.

**Tests ajoutés :** `tests/test_annotations_group_length_axes.py` (`4777e74`) : pièces trapézoïdales analogues, quasi-parallèles, 1 paire native, référence non éligible, et cas d'une seule direction. **Tests automatisés non exécutés dans cette intervention ; validation Revit de la correction en attente.**

**Recette prudente :** repartir d'une **copie de test précédant la création des groupes `TAA - Cotations`**, sinon le module réutilise les détails attachés existants et produit 0 nouvelle cote. Ne jamais supprimer le **groupe de modèle** pour retester. Dans `Niveau 1`, sélectionner la même occurrence du groupe, contrôler la direction, les valeurs, les nus finis, le nombre de cotes par pièce et la non-régression des étiquettes ; vérifier ensuite la seconde occurrence du groupe seulement si le premier résultat est correct. **La PR #37 reste en brouillon.**


## BUG-COMMON-032 — Cotation traversant deux pièces via extrémités du mur entier (13 novembre 2026)

**Reproduction utilisateur en Revit 2025.4 :** sur `Niveau 1`, `Groupe 1`, 4 pièces, la révision `2026-11-13-group-dimensions-02` crée 8 annotations. L'image prouve qu'une cote affichée **« 7 »** mesure le mur au-delà de la pièce visée et couvre **deux pièces**. Le total 8/8 ne vaut **pas** validation de l'exactitude des cotations. La correction précédente (angle de 30° entre directions) était insuffisante : elle ne borne pas la longueur effective entre références.

**Cause vérifiée dans le code :** le moteur Plans de vente utilise des `length_references` d'extrémités prises sur la géométrie du **mur physique entier** (arêtes verticales de ses faces). Quand un même mur borde deux pièces, `BoundarySegment` de chaque pièce est plus court que le mur. La cote Revit peut donc mesurer la longueur du mur **sur plusieurs pièces**, même si le segment numérique et la ligne de cote sont dessinés au droit d'une seule pièce. L'angle des directions ne remédie pas à ce défaut de références.

**Correction ciblée sur l'adaptateur Annotations en mode groupe (non validée dans Revit) :**
- **Ne plus conserver aucun `length_references` issu des extrémités du mur physique** pour les cotes de secours en groupe.
- Pour chaque limite retenue, créer **deux petits `DetailCurve` de 5 mm** perpendiculaires au segment et **centrés sur les deux extrémités exactes du `Room.GetBoundarySegments` de la pièce**. Utiliser leurs `GeometryCurve.Reference` pour la dimension native Revit. Cette cote est **non associative aux ouvrages**, et mesure une **longueur de limite propre à la pièce**, qui n'est pas forcément une distance entre faces opposées.
- Avant `_attach`, relire `Dimension.References` et `Dimension.Value` : exiger les deux repères de la **même limite de la même pièce** et un écart maximal de **5 mm** avec la longueur de cette limite ; vérifier que `Dimension.Origin` est dans **la pièce concernée** par `Room.IsPointInRoom`.
- En cas de valeur fausse, référence croisée ou centre hors pièce : **rollback du `TransactionGroup` complet**, sans laisser de cote ni repère 2D orphelin.
- La sélection des deux orientations d'au moins 30° reste une politique de choix **après** sécurisation de la mesure. Les faces réellement opposées continuent à exploiter les références natives lorsque disponibles. Le moteur stable Plans de vente et la cotation hors groupe ne changent pas.

**Marqueur de version :** `2026-11-13-group-room-boundary-03`. **Commits bêta :** `3730394` (géométrie), `c4a5afe` (repères locaux), `2bc4e2d` (contrôle bloquant de valeur et pièce), `6537030` (diagnostic). **Test anti-régression ajouté** : `tests/test_annotations_group_room_boundary.py` (commit `bb03770`) avec scénario mur 7,20 m / limite de pièce 4,30 m et vérification du code de production par objets factices. **Tests non exécutés, validation Revit non effectuée.**

**Recette :** partir d'une **copie antérieure aux groupes `TAA - Cotations` du précédent essai**, sans supprimer le groupe de modèle original. Sur `Niveau 1`, choisir `Groupe 1` et vérifier les valeurs dans **chaque pièce** et les textes ; contrôler le nouveau diagnostic `LONGUEUR LOCALE PIECE` et `COTE LOCALE VERIFIEE`. Si Revit refuse la cote à partir des courtes DetailCurve, **ne pas masquer cet échec par le retour aux références du mur entier** : la solution restera à développer, sans valider 8/8 sur fausses mesures. Second lancement et occurrence voisine seulement après mesures exactes. PR #37 maintenue en brouillon.

## Calculs des pièces — conflits entre groupes et variantes (16 novembre 2026)

**Sujet :** rapport utilisateur d'environ 898 écritures annulées ; restauration de l'alignement du paramètre `Surface logement` ayant détecté 9 éléments à réaligner. Conflit d'écriture confirmé, impact causal précis des variantes non démontré.

**Branche :** `fix/calculs-group-conflicts-design-options` ; **PR #56** en brouillon, vers `main` ; pas de fusion.

**Règles métier demandées :**
1. Si plusieurs occurrences d'un même type de groupe exigent des valeurs différentes, demander à l'utilisateur s'il souhaite conserver durablement les valeurs variables ou maintenir l'alignement en choisissant une valeur de référence parmi les résultats calculés pour chaque type de groupe. Aucun choix implicite.
2. Conserver le périmètre de calcul habituel (toutes les pièces du projet) ; indiquer les variantes détectées et le nombre de pièces issues de chacune. Le module lit les valeurs `Area` produites par Revit, sans changer la géométrie ni choisir une vue.

**Implémentation :** diagnostics `calculation_diagnostics.py` ; logique de choix et garde-fous dans `room_calculation_workflow.py` ; interface `calculs_window.py` ; test `test_group_decisions.py` ; documentation module `docs/10_Calculs_Pieces.md` ; registre `BUG-CALCULS-007`. L'uniformisation est refusée si une occurrence porte plusieurs regroupements avec des totaux distincts ; le rollback reste actif.

**Validation automatisée :** GitHub Actions PR #56, commit `062b5267790f6dbb8aedd8528a48b5f0520b04b9` : **88 passed** pour `python -m pytest tests/calculation -q` (run 43862479754) ; suite **Export verte** (run 43862479763). Un premier run avait échoué à cause de la mention textuelle `ActiveView` dans un commentaire, corrigée avant cette validation.

**Validation Revit :** **non effectuée**. Ne pas fusionner sans test sur copie de maquette : (a) groupes identiques et résultats différents, (b) choix variable, (c) choix aligné avec valeur référence, (d) annulation et Undo, (e) groupes à plusieurs appartements, (f) variantes principales et secondaires, (g) fonctionnement historique sans conflits. Contrôler aussi le nombre de pièces et les valeurs affichées.

**Action suivante :** déployer uniquement la branche sur un chemin pyRevit de test, jamais à la place de l'extension partagée stable ; tester d'abord les groupes de référence sur une copie du RVT et comparer `Surface logement` avant/après.

## Reprise Calculs des pièces — variante B200 et charte TAA (16 novembre 2026)

**Retour utilisateur Revit :** la version précédente de la PR #56 mélangeait les pièces de solutions de conception distinctes dans une même somme lorsque la clé de regroupement était identique (ex. `B200`). Les boîtes de dialogue pyRevit génériques tronquaient les textes et ne respectaient pas la charte graphique.

**Décision corrigée :** il ne s'agit pas de filtrer les pièces par la vue active. Le module collecte les pièces du projet et calcule indépendamment les surfaces par **clé métier + scénario de variante** : modèle principal et variantes principales réunis dans le scénario de référence, chaque variante secondaire isolée. Le numéro `B200` peut ainsi produire plusieurs résultats sans mélange. La logique de conflit et de choix d'alignement des paramètres par groupes reste active.

**Implémentation sur `fix/calculs-group-conflicts-design-options` :** `calculation_diagnostics.variant_group_key` ; raccordement avant agrégation dans `room_calculation_workflow.py` ; fenêtres WPF `calculation_decision.xaml`/`calculation_decision_window.py` ; `calculs_window.py` raccordée aux fenêtres TAA. L'option de collecte par vue active introduite pendant l'analyse a été supprimée avant livraison.

**Validation automatisée :** GitHub Actions `tests/calculation` **90 tests réussis** sur commit `91dc988e02acd84c619405aafa88e57045fbfd81` (run 43890452365) ; suite Export également réussie (run 43890452374). Le registre `BUG-CALCULS-007` et `docs/10_Calculs_Pieces.md` sont à jour. Un commit documentaire complémentaire suit les tests.

**Validation Revit 2025.4 :** **en attente**, malgré le retour initial démontrant que la version antérieure était chargée. Test requis sur copie RVT : deux appartements `B200` distincts dans deux variantes, vérifier deux sommes distinctes et écritures correspondantes ; confirmer l'affichage et l'annulation des dialogues WPF TAA ; contrôler modèle principal, variante principale et variantes secondaires, puis groupes alignés.

## Calculs des pièces — confirmation des variantes séparées (16 novembre 2026)

**Décision :** lorsque le même numéro d'appartement apparaît dans plusieurs scénarios de variantes, conserver les surfaces indépendantes et afficher **une confirmation WPF TAA** avant toute écriture ; ne pas proposer d'addition des variantes dans ce parcours. Aucune demande si un seul scénario est concerné.

**Implémentation (PR #56, branche `fix/calculs-group-conflicts-design-options`, non fusionnée) :** diagnostic des clés de regroupement présentes dans plusieurs scénarios dans `services/calculation_diagnostics.py` ; propriété `shared_variant_apartments` et verrou `variant_separation_confirmed` dans `room_calculation_workflow.py` ; dialogue WPF TAA de confirmation dans `ui/calculs_window.py` utilisant `calculation_decision_window.py`. Annuler bloque la commande avant transaction. Les totaux séparés existants ne sont pas modifiés. Documentation `docs/10_Calculs_Pieces.md` et BUG-CALCULS-007 mis à jour.

**Tests CI :** GitHub Actions `Calculs des pièces — tests hors Revit`, run `43891349277` : **92 passed** au commit `01b9760540951190e80e10b781a40f6aaf42fa50` ; ce run inclut les nouveaux tests, les commits documentaires ultérieurs ne modifient pas le code. Vérifier le statut CI au SHA final avant validation.

**Recette Revit 2025.4 / pyRevit 5.x :** non exécutée pour cette modification. Vérifier une paire B200 dans deux variantes, affichage des deux totaux, annulation, confirmation puis écriture conservant les deux surfaces différentes, ainsi qu'un cas sans doublon de scénario. La PR reste en brouillon.

## Recette UI Calculs — boutons de confirmation masqués (16/11/2026)

**Constat utilisateur en Revit 2025.4 :** fenêtre WPF « Surfaces indépendantes par variante » ouverte pour B200 ; deux scénarios affichent chacun 35,330 m². La présence de valeurs égales n'est pas une anomalie du calcul à elle seule. Problème confirmé : boutons d'action non visibles dans la fenêtre de confirmation. Le code forçait `Height=320` lorsque la liste de choix était absente ; le récapitulatif à plusieurs lignes ne laissait plus de place au pied d'actions.

**Correction de branche PR #56 (non fusionnée) :** hauteur de la confirmation 440 unités WPF, zone de texte défilable, pied d'actions préservé, noms des variantes affichés sans « variante Variante 1 », scénario principal explicitement étiqueté « scénario de référence ». Aucune modification des totaux ni du comportement de confirmation/annulation. Tests statiques/diagnostics ajoutés dans `tests/calculation/test_group_decisions.py`.

**Tests :** dernière CI verte connue sur `c3ead4a` (92 tests Calculs). Les tests de la correction UI ne sont pas encore confirmés sur le dernier SHA de cette branche. **Recette Revit : en attente** ; vérifier les deux boutons visibles et opérationnels, absence de troncature, confirmation et annulation sans écriture.

## Calculs des pièces — redimensionnement fenêtre de décision (16 novembre 2026)

**Retour réel utilisateur Revit 2025.4 :** confirmation des variantes B200 réussie visuellement avec boutons présents ; dans la confirmation générale, l'agrandissement de la fenêtre n'étendait pas le panneau blanc de récapitulatif et laissait un grand espace gris vide.

**Cause :** `calculation_decision.xaml` attribuait `Height=Auto` à la ligne des détails et `Height=*` à la ligne des choix (masquée dans une confirmation), tandis que le `ScrollViewer` des détails avait `MaxHeight=170`. La hauteur supplémentaire était attribuée à la mauvaise ligne.

**Correction implémentée sur PR #56 en brouillon :** ligne des détails `*` et suppression de `MaxHeight=170`, ligne des choix `Auto` avec panneau limité à 180 unités WPF, pied de boutons séparé. Calculs, scénarios de variantes, valeurs et transactions inchangés. Test statique de contrat XAML ajouté dans `tests/calculation/test_group_decisions.py`.

**Tests et recette :** tests automatisés CI à vérifier sur le commit de correction ; contrôle d'affichage à refaire dans Revit 2025.4, en redimensionnant les confirmations avec et sans choix tout en gardant Annuler / Confirmer visibles. **Ne pas considérer validé avant retour utilisateur.**

## Calculs des pièces — addition optionnelle de toutes les variantes (16/11/2026)

**Besoin confirmé :** permettre de choisir entre les surfaces par variante et l'addition de toutes les surfaces, y compris celles des variantes secondaires, pour un même numéro d'appartement. Le mode séparé doit rester le défaut afin d'éviter le double comptage involontaire.

**PR #56 en brouillon, branche `fix/calculs-group-conflicts-design-options` ; main non modifiée.** Nouveau sélecteur WPF « Gestion des variantes » sur la fenêtre principale :
- séparées (défaut, inchangé) : scénario principal et chaque variante secondaire indépendants ;
- additionnées (explicite) : somme des surfaces de toutes les pièces portant le même numéro d'appartement, toutes variantes confondues. **Le résultat cumulé est écrit dans chaque pièce correspondante**, sans restriction de variante. Un avertissement détaille les totaux par variante et le cumul, puis exige une confirmation avant écriture lorsque plusieurs scénarios contribuent au même appartement. Annuler n'ouvre aucune transaction. Le filtre métier historique, les protections pour paramètres alignés par groupes et le rapport sont préservés.

**Implémentation :** `calculation.workflow_models.CalculationRequest.variant_mode`, contrôleur, `services/room_calculation_workflow.py`, fenêtre `ui/calculs_window.py`/`calculs_ui.xaml` ; hauteur initiale ajustée pour maintenir la lisibilité. Les choix ne sont pas persistés : retour au mode séparé à chaque ouverture. Tests ajoutés dans `tests/calculation/test_group_decisions.py`. Documentation `docs/10_Calculs_Pieces.md`, registre BUG-CALCULS-008.

**CI vérifiée :** commit `cc15044059a7e16c9c66edf899eddc112f602776`, run `43894637327` : **98 tests Calculs des pièces réussis** ; run `43894637619` : **Export réussi**. La correction de hauteur `b3ebe7972c14bb08b625b8783aa82025c9b73a8d` est postérieure à ces résultats et doit être couverte par les runs ultérieurs.

**Validation Revit 2025.4 :** en attente pour cette option. Tester B200 = 35,330 + 29,522 m² : en mode séparé deux résultats indépendants ; en mode addition 64,852 m² dans toutes les pièces B200, avec confirmation ; Annuler sans écriture ; vérifier conflit de groupes, Undo et absence de doublons. Ne pas fusionner avant validation.

## Calculs des pièces — revue unique avant écriture / interface épurée (16/11/2026)

**Demande utilisateur :** réduire le nombre de fenêtres de confirmation et diminuer la quantité d'informations affichées. Aucun changement de calcul métier souhaité.

**Branche de développement :** `fix/calculs-group-conflicts-design-options`, PR #56 en brouillon ; pas de fusion dans `main`.

**Implémentation :** nouvelle fenêtre `ui/calculation_review.xaml` + `ui/calculation_review_window.py` regroupant en une seule validation WPF TAA (a) nombre de pièces/totaux et destination, (b) courte indication des variantes avec avertissement si cumul, (c) choix de réglage des groupes et, si nécessaire, choix de valeur commune par type au même endroit. Le verrou de confirmation des variantes et le refus d'écriture sans décision explicite restent contrôlés par le workflow. `calculs_window.py` n'ouvre désormais qu'une seule fenêtre de validation : plus de séquences de confirmations. En cas de succès, état synthétique dans la fenêtre principale et bouton `Rapport` facultatif ; en cas d'échec, ouverture automatique du rapport. La hauteur initiale de la fenêtre principale est ramenée de 624 à 596 unités WPF pour satisfaire la règle de compacité (maximum 600) ; `ScrollViewer` conservé pour les petits écrans.

**Tests :** test statique de parcours unique et fenêtre WPF ajouté à `tests/calculation/test_group_decisions.py`. Un contrôle CI antérieur (run 43895465430) a échoué sur l'ancien `Height=624` (`1 failed, 97 passed`) ; hauteur corrigée, nouvelle CI à vérifier. Les tests automatisés ne constituent pas une validation visuelle Revit.

**Recette Revit 2025.4 :** en attente : une seule fenêtre de confirmation pour B200 séparé/cumulé, avec/sans divergence de type de groupe, choix des valeurs de référence sans fenêtre supplémentaire, annulation sans transaction, succès sans rapport imposé, bouton Rapport, erreur avec rapport affiché. Conserver la PR en brouillon jusqu'à la recette.


**Suivi CI complémentaire :** un run intermédiaire `43896244892` échouait sur deux exigences de tests : hauteur historique `624 > 600`, puis recherche obsolète de `if prepared.warnings` dans l'ancienne fenêtre. Hauteur ramenée à 596, et avertissements pertinents affichés de manière concise dans `calculation_review_window.py`, avec mise à jour du test `tests/calculation/test_ui_wiring.py`. Ces corrections sont implémentées ; **attente d'un run de tests vert au SHA final**. L'échec précédent ne doit pas être présenté comme une validation.\n

## Préparation fusion PR #56 — retour Revit et correction CI (16 novembre 2026)

**Retour utilisateur confirmé dans Revit 2025.4 / pyRevit 5.x :** « parfait ça marche très bien on peut fusionner » après test de la nouvelle interface à confirmation unique, d'informations allégées et de la gestion des variantes dans le module Calculs des pièces. Ce retour valide le parcours métier expérimenté par l'utilisateur, **sans preuve que tous les cas limites (groupes hétérogènes, cas d'erreur, Undo, modèles complexes) ont été retestés exhaustivement**.

**Correction CI préalable à fusion :** le run 43896921445 (99 tests dont 98 passés) a échoué uniquement sur le contrat UI `MinHeight <= 500` (valeur 520). Correction ciblée de `calculs_ui.xaml` : `MinHeight=500`, en maintenant `Height=596`. Aucun changement au moteur de calcul. La fusion est conditionnée à une nouvelle CI verte sur le commit de tête.

**Périmètre PR #56 :** gestion des paramètres alignés par groupes (choix explicite), séparation / addition volontaire des variantes, confirmation synthétique WPF TAA, rapport à la demande en cas de succès et rapport automatique en cas d'erreur. Documentation `docs/10_Calculs_Pieces.md` et registre `docs/bugs/CALCULS.md` mis à jour.

**Étape suivante :** vérifier tous les contrôles CI sur le dernier SHA ; fusionner PR #56 dans `main` à la demande explicite de l'utilisateur puis vérifier le SHA de fusion. Garder les cas limites en tests futurs si non couverts par la recette.

## Calculs des pièces — réglage groupes dans la fenêtre principale (16/11/2026)

**Base :** PR #56 fusionnée dans `main` (`9d2690f4cadb55105763e1ac9ab10795f34e83d5`), CI 99 tests Calculs + suites Export vertes, retour utilisateur positif sur la confirmation simplifiée.

**Recette complémentaire communiquée par l'utilisateur :** scénarios **2 à 8 du bilan des scénarios restants testés et OK dans Revit** (valeur commune par type, addition des variantes, annulation avant écriture, Ctrl+Z, destination non modifiable/erreur, groupes à plusieurs appartements, rapport facultatif). **Le scénario 1 — autorisation durable de valeurs différentes — n'est pas encore confirmé dans ce retour**. Le scénario 9 (mise en page multi-tailles de la nouvelle revue) n'est pas couvert par cette déclaration.

**Nouveau besoin :** ajouter `GESTION DES GROUPES` directement dans la fenêtre principale à la façon de `GESTION DES VARIANTES`, sans multiplier les fenêtres ni modifier les algorithmes validés.

**Implémentation sur branche `feat/calculs-group-mode-main-ui`, main non modifiée :** choix `auto` par défaut / `vary` / `uniform`, modèle de requête, contrôleur, workflow, revue WPF ; valeurs de référence dans la revue seulement si nécessaire, sécurité transactionnelle existante conservée. Tests de non-régression ajoutés. **Validation CI et Revit de cette évolution à effectuer**.

**Action suivante :** vérifier la suite de tests Calculs et Export, examiner les résultats sur GitHub puis tester la fenêtre principale, notamment la sélection vary/uniform et l'absence de confirmation supplémentaire.

## Validation utilisateur PR #57 — Gestion des groupes (16 novembre 2026)

**Retour utilisateur Revit 2025.4 / pyRevit 5.x :** « parfait ça fonctionne bien tu peux valider », à la suite de l'ajout du sélecteur **GESTION DES GROUPES** dans la fenêtre principale. Ce retour valide l'ergonomie et le fonctionnement observé du nouveau réglage, avec autorisation explicite de fusionner.

**Périmètre de preuve :** le retour valide le parcours testé mais ne fournit pas de résultats détaillés distincts pour les trois modes sur toutes les combinaisons de maquettes. Les scénarios historiques 2 à 8 ont été explicitement déclarés OK précédemment. Ne pas extrapoler à une recette exhaustive sur les cas rares.

**CI vérifiée avant fusion :** PR #57, commit `fccc4fcb8bd2d4fb352f2e60155ac3f5dabc2468` : `Calculs des pièces — tests hors Revit` réussi (run `43899824241`, 103 tests) et `Export — tests hors Revit` réussi (run `43899824194`). Aucune fusion ni modification de `main` effectuée au moment de cette note.

**Décision :** passer la PR #57 prête pour revue et fusionner dans `main`, sous réserve du contrôle GitHub de l'état mergeable, puis vérifier le commit de fusion et les contrôles de la branche principale.

## Calculs des pièces — correction fonctionnelle de gestion des groupes (16/11/2026)

**Objectif utilisateur :** (1) valeurs différentes : désactiver durablement l'alignement du paramètre destination entre groupes, puis écrire les totaux ; (2) valeur commune : traiter les membres homologues de toutes les occurrences d'un même type de groupe et conserver l'alignement, comme une édition fonctionnelle du contenu des groupes. Ne pas dégrouper / recréer.

**Implémentation sur la branche `fix/calculs-uniform-revit-groups-v2` depuis `main` `112acbf26486e9744648bd5a28a16f3b4e22dd8c` :** nouveau `services/group_member_alignment.py` s'appuyant sur l'ordre stable de `Group.GetMemberIds()`. Les pièces homologues hors périmètre filtré sont ajoutées explicitement au plan du mode commun. Exécution dans transaction unique ; comparaison post-alignement de tous les résultats et rollback si des éléments hors plan seraient modifiés ou si une valeur diffère. Les paramètres déjà variables sont réalignés sur demande explicite d'uniformisation. L'option valeurs différentes reste durable. Les confirmations et calculs des variantes sont inchangés.

**Diagnostic distinct :** lorsque le moteur produit 0 opération, un message nouveau précise les pièces sans clé métier ou sans source numérique ; ce cas n'est pas attribuable à lui seul au réglage du paramètre cible.

**Limite :** le mode d'édition interactif des groupes Revit n'est pas invoqué. Les groupes de modèle restent intacts ; la correspondance des membres est obtenue par API. Les modes dangereux continuent d'être refusés. Les cas non observés dans Revit ne sont pas validés par les seules simulations.

**Tests :** nouveaux tests de régression sur correspondances, membres hors filtre, rollback, bascule de définition et diagnostic ; CI à vérifier sur dernier commit, validation en Revit 2025.4 / pyRevit 5.x encore ouverte. **Ne pas fusionner sans recette.** La PR #58 est une correction indépendante de rapport, non fusionnée.

**Complément de sécurité et ergonomie PR #59 :** le rapport de rollback reprend la synthèse prévue par PR #58 (une cause de transaction + nombre d'écritures annulées). L'avertissement d'écritures sur les membres homologues hors filtre n'est présenté que si le mode uniforme a été retenu ; le mode Automatique qui aboutit à « valeurs différentes » ne doit pas annoncer à tort ces écritures. La revue bloque également le choix uniforme si le plan de correspondance des membres a échoué. **CI à relancer sur la tête de PR et recette Revit toujours obligatoire avant fusion.**

**CI PR #59 confirmée après correction du code :** commit `2d7441f3fddd915105f478214f8a2a587513524d`, workflow Calculs `43909807592` : **114 tests réussis** ; workflow Export `43909807563` : **réussi**. Il s'agit de tests automatisés hors Revit, pas d'une validation réelle du modèle. **Étape suivante impérative :** récupérer cette branche et vérifier sur copie du RVT les deux modes, la modification des valeurs de tous les membres homologues et le comportement après Ctrl+Z. PR #59 maintenue en brouillon.

## Retour Revit PR #59 — le mode uniforme ne tient pas après réalignement (16 novembre 2026)

**Recette réelle utilisateur :** (1) `Autoriser des valeurs différentes entre groupes` **OK**, conservé comme fonctionnalité validée dans le parcours testé ; (2) `Conserver une valeur commune` **KO**. Erreur post-alignement de `Surface logement` : élément **5630105**, attendu **380.286410009**, réel **324.979623715**. **36 écritures annulées dans une seule transaction** (rollback). Ne pas considérer la PR #59 globalement validée.

**Analyse :** `SetAllowVaryBetweenGroups(False)` entraîne un réalignement automatique de valeurs dans Revit. Le fait d'avoir écrit les membres homologues ne garantit pas que cette opération conserve les résultats préparés. Le nombre et l'ID sont extraits du rapport utilisateur ; l'origine de la valeur imposée 324.979623715 dans la maquette n'est pas encore connue.

**Modifications supplémentaires sur la PR #59 en brouillon, main inchangé :** pré-contrôle des valeurs par position des membres homologues avant transaction ; diagnostic explicite d'écrasement et du type de groupe ; tentative encadrée de `Document.Regenerate()` après écriture et avant `SetAllowVaryBetweenGroups(False)` afin de ne pas utiliser une représentation Revit non régénérée. Simulations automatisées ajoutées, mais **validation Revit toujours obligatoire** et aucune promesse que le mode uniforme fonctionne. L'option valeurs différentes reste inchangée.

**Prochain essai précis :** sur copie du même RVT, branche `fix/calculs-uniform-revit-groups-v2` actualisée, répéter le mode uniforme ; si l'ID 5630105 est encore remplacé, conserver le rapport et analyser la valeur de référence du membre dans l'éditeur de groupe Revit. Une édition de groupe automatisée non disponible dans l'API ne doit pas être simulée par une reconstruction destructive.

## Revit PR #59 — régénération insuffisante, diagnostic en deux phases (16/11/2026)

**Captures de recette :** fenêtre de validation avec **36 pièces, 9 totaux**, appartement présent dans plusieurs variantes avec séparation conservée. Sélection « Groupe 1 — 35.330 m² » (type ID `5629042`) et « Groupe 2 — 16.047 m² » (type ID `5629531`). Rapport : **0 succès, 36 annulations**, élément `5630105` forcé à `324.979623715` au lieu de `380.286410009`. La tentative `Document.Regenerate()` avant restauration échoue toujours sur cette maquette.

**État réel :** mode « valeurs différentes » validé précédemment ; mode « valeur commune » **toujours non fonctionnel sur cette maquette**. Ne pas fusionner PR #59 et ne pas qualifier la régénération de correctif validé.

**Correctif diagnostique supplémentaire sur la même branche :** capture de toutes les valeurs cibles après écriture/régénération et avant restauration, vérification immédiate ; comparaison post-restauration et message avec nom/ID de type obtenu par API ou par les conflits préparés. Tests automatisés de non-régression ajoutés. Aucune modification du comportement validé du mode valeurs différentes et maintien du rollback intégral.

**Prochaine étape Revit précise :** récupérer le dernier commit de la branche et répéter l'uniformisation sur une copie du RVT, puis relever **la valeur avant restauration**, **la valeur après restauration**, le type de groupe et l'élément. Si elles sont différentes uniquement après `False`, analyser la valeur de référence de ce membre dans l'éditeur de groupe et concevoir une stratégie distincte, plutôt que de boucler sur le même appel.

## Diagnostic Autodesk confirmé — alignement des paramètres de groupes (16/11/2026)

**Retour utilisateur dernier essai PR #59 :** 36 écritures annulées ; l'élément `5630105` du type de groupe `5629042` avait la valeur attendue `380.286410009` *après écriture ET régénération, juste avant restauration* ; il est ramené à `324.979623715` précisément lorsque `SetAllowVaryBetweenGroups(False)` est invoqué. Le rollback est correct. Régénération déjà testée : **KO**.

**Règle officielle confirmée :** [Autodesk — Create or Modify Project Parameters](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Model/files/GUID-28CBBEC2-6262-42D3-AE41-B36166E8318F.htm) : passage de paramètres variables à alignés = copie de la valeur de la première occurrence du groupe vers les membres homologues. [API](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/6f5af0cc-2ab3-153a-e07d-78fbc12aefc1.htm) : réalignement automatique pouvant modifier des éléments. La valeur `324.979623715` pourrait donc provenir de cette occurrence de référence ; il reste à le vérifier dans le RVT. **La méthode précédente ne peut garantir le choix de valeur commune arbitraire.**

**Décision de sécurité :** ne pas fusionner PR #59 ; maintenir le mode valeurs différentes validé, et protéger le rollback. Aucun recours automatique à ungroup/regroup ou écriture forcée après `False`. Reconcevoir le mode uniforme en distinguant conservation de valeurs déjà alignées et définition d'une nouvelle valeur de référence, qui requiert potentiellement l'éditeur de groupes Revit (parcours assisté), sans prétendre que la valeur choisie dans la revue est forcément retenue.

**Prochaine étape :** documenter/valider la provenance de la valeur de référence dans la première occurrence du type de groupe 5629042 ; concevoir ensuite un workflow de modification de la valeur du membre du type, avec validation explicite sur copie RVT et non-régression du mode valeurs différentes.

## Refonte encadrée du mode « valeur commune » — PR #59 (16/11/2026)

**Décision :** la PR #59 ne peut pas prétendre imposer automatiquement une nouvelle référence commune via `SetAllowVaryBetweenGroups(False)`. Les captures Revit démontrent que l'API remplace la valeur écrite selon la référence de groupe. Le mode « valeurs différentes » fonctionne sur la maquette et doit être préservé.

**Nouvelle implémentation (sur branche de PR #59, `main` inchangée) :**
1. En cas de conflit entre occurrences et d'une valeur commune demandée différente de la valeur actuelle portée par les membres du type, `RoomCalculationWorkflow.uniform_manual_guidance` construit un **guide sans modification** (type/ID, référence voulue, valeur présente, exemple pièce/groupe).
2. `CalculationReviewWindow` utilise la même modale WPF et n'autorise pas la confirmation d'écriture pour ce cas ; demander l'édition manuelle du groupe via Revit puis une relance. Le contrôleur transmet ce diagnostic.
3. Le moteur a le même garde-fou avant transaction pour des appels sans interface, afin de ne pas répéter le rollback de 36 écritures. Les situations déjà compatibles utilisent la transaction historique avec vérification des valeurs après réalignement.
4. Les algorithmes de regroupement des variantes et le mode `vary` validé n'ont pas été modifiés. Pas de reconstruction/ungroup automatique.

**Limite de portée :** cette première refonte est un **parcours assisté** pour définir une nouvelle valeur commune, pas une édition programmatique complète du groupe Revit. L'aide Autodesk sur les paramètres de projet explique que l'alignement prend la première occurrence ; elle ne démontre pas que chaque maquette accepte les autres écritures programmatiques. Contrôle post-réalignement et rollback restent obligatoires.

**Tests :** cas supplémentaires intégrés dans `test_group_decisions.py` ; exécution CI et validation de l'affichage WPF/édition manuelle réelle encore nécessaires. **PR #59 maintenue en brouillon.**

**Complément UX et sécurité :** le guide de correction manuelle affiche désormais les valeurs de surface dans l'unité lisible du module (`m²` pour une source de type aire) en utilisant le formateur déjà validé de la fenêtre. Cela évite de demander de renseigner directement une valeur interne Revit en pieds carrés. Ce formateur n'est utilisé que pour le message ; toutes les écritures automatiques gardent leur précision interne. Tests d'affichage et de transmission ajoutés. **Les tests du dernier commit doivent encore être vérifiés avant recette Revit.**

## Nouvelle décision utilisateur — information des groupes, sans sélecteur (16/11/2026)

**Demande la plus récente :** remplacer dans la fenêtre principale l'option « Gestion des groupes » par une **phrase expliquant qu'Outils TAA peut désactiver l'alignement du paramètre cible si nécessaire pour conserver les sommes**. Refus explicite du parcours d'édition manuelle du groupe.

**Implémentation sur `fix/calculs-uniform-revit-groups-v2` / PR #59 :** ligne WPF « GROUPES REVIT » avec texte explicatif à la place de `GroupModeCombo`; `group_mode="auto"` en fenêtre principale. Si les valeurs par occurrence divergent, choix d'une valeur commune par type dans la revue unique lorsque c'est sûr ; sinon écriture individuelle. Quand le choix commun exigerait une nouvelle valeur de référence que Revit écraserait en `False`, conserver automatiquement `VariesAcrossGroups=True` après écriture de la valeur commune ; prévenir avant écriture et enregistrer le changement durable dans le rapport. Si compatible, conserver le parcours historique avec restauration. Aucun groupe dégroupé/recréé.

**Statut :** correction implémentée sur branche, CI automatisée en vérification, **non validée sous Revit 2025.4** ; le mode valeurs différentes a déjà été validé en Revit sur une version antérieure et doit être recontrôlé sur cette branche. `main` inchangée ; ne pas fusionner la PR avant la recette.

## Calculs — nouvelle clarification utilisateur : écrire le vrai total, pas uniformiser (16/11/2026)

**Décision produit :** les valeurs inscrites dans `Surface logement` sont les résultats du moteur par appartement (et par variante séparée, si demandé). Aucune valeur commune arbitraire entre logements du même type de groupe. Si le paramètre de destination suit les groupes, la fenêtre annonce qu'Outils TAA **va désactiver** l'alignement durablement pour préserver ces résultats.

**Correctif sur PR #59, main intacte :** `group_mode="auto"` dans l'accueil converti en `vary` en présence de paramètre aligné sur les groupes ; aucune sélection de référence de groupe dans la revue WPF ; la fenêtre de revue ne s'affiche plus que si un appartement existe dans plusieurs variantes, afin de confirmer le mode déjà choisi. Hors variantes partagées, calcul et écriture directe. Les fonctions de test historiques du mode uniforme restent dans le moteur mais ne sont plus appelées par le parcours utilisateur actuel.

**Vérifications :** tests de non-régression adaptés à la nouvelle intention (vrais totaux distincts, absence de choix d'uniformisation, confirmation conditionnelle des variantes). Exécution CI à vérifier sur le dernier commit et validation réelle Revit à effectuer. Ne pas fusionner PR #59 sans accord.

## Calculs — recette utilisateur positive et retrait de l'unité de sortie (16 novembre 2026)

**Retour Revit 2025.4 :** « tout fonctionne bien » concernant le parcours actuel de Calculs des pièces de PR #59 (valeurs réelles par numéro d'appartement, variantes, gestion automatique du paramètre aligné, absence d'uniformisation de type). **Autorisation explicite donnée pour fusionner PR #59 dans `main`** après suppression de la ligne UNITÉ DE SORTIE.

**Dernière modification de branche :** bloc UNITÉ DE SORTIE retiré du layout. `UnitCombo` masqué pour compatibilité technique, sortie automatique (`output_unit_type_id=None`) et non restauration d'un ancien choix manuel. Aucune modification des calculs ni des traitements de groupes. Les sélections manuelles d'unités vers texte/entier ne sont plus disponibles.

**Qualification :** fonctionnement du parcours précédent **validé par utilisateur dans Revit**, suppression de ligne **implémentée** et couverte par tests automatiques, mais non re-testée sur écran Revit après modification. CI à vérifier sur tête de PR, puis PR prête et fusion dans `main`, vérification du SHA de fusion et des tests de la branche principale. Ne pas confondre tests automatisés GitHub et validation Revit.



## Export — Dossiers automatiques par paramètres (16 novembre 2026)

**Branche :** `feature/export-dossiers-dynamiques-spec` ; **PR #55 Draft**, non fusionnée. Synchronisée sur le `main` intégrant la configuration collaborative de la PR #30. Dernier état de référence : documentation `docs/28_Export_Dossiers_Dynamiques.md`.

**Implémentation :** mode de dossier automatique dans l'assistant ; règle de sélection par paramètre + valeur, sous-dossiers virtuels par second paramètre ; actualisation au rafraîchissement et avant aperçu/publication ; blocage si paramètre absent ou ambigu ; conversion explicite en manuel avec copie figée des références et sous-dossiers par mutation atomique du repository ; protections contre les opérations manuelles sur les sous-dossiers calculés. Aucune modification des paramètres ni de l'arborescence du navigateur Revit.

**Tests automatisés :** 485 tests Export réussis lors du workflow GitHub Actions `Export — tests hors Revit` sur le commit `f7e6db1e3e58edeabbfb4e3ef54428694ea2f621` ; CI collaborative et contrat ruban verts sur le même commit. Modifications suivantes purement documentaires ; vérifier la CI du dernier commit de code si la branche évolue.

**Recette Revit :** aucune validation terrain confirmée pour cette fonctionnalité. Tester DYN-01 à DYN-11 avant fusion ; spécialement changement de valeurs Revit, sous-dossiers, publication et conversion en manuel.

**Travaux non compris :** copie exacte de l'organisation native du navigateur Revit, migration de paramètres homonymes par GUID, surveillance permanente des événements Revit. Aucune release publiée.

**Prochaine action :** recette Revit 2025.4 sur la branche PR #55, correction des éventuelles anomalies et contrôle de non-régression de la version stable 1.4.1.

### PR #55 — Retour UI du 16 novembre 2026

L'utilisateur confirme que les feuilles se mettent bien à jour ; ne pas ouvrir un bug de recalcul. Trois corrections **implémentées, non validées dans Revit** : fenêtre « Dossier auto » en mode exclusif, aperçu des nombres de feuilles/sous-dossiers avec détail par groupe, icône de dossier auto/synchronisation différente des dossiers manuels. Les tests automatisés ont été étendus ; contrôle CI sur SHA final et recette Revit encore requis. Ne pas fusionner la PR Draft avant confirmation.

**Contrôle GitHub — 16/11/2026 :** 488 tests Export réussis et workflows « Export — configuration collaborative » / « Export ribbon contract » verts au commit `4111b9ca4de1be9f6d9a219a41e9170f3e23aca0`. La branche a été réalignée sur `main` (les évolutions récentes du module Calculs des pièces ont été conservées) ; recette UI sous Revit encore à confirmer.

### PR #55 — Conversion individuelle d'un sous-dossier (16 novembre 2026)

**Retour utilisateur :** la création, l'aperçu et l'actualisation des dossiers automatiques sont validés dans Revit. Nouvelle amélioration requise : figer un seul sous-dossier sans figer tous les autres.

**Implémentation :** commande contextuelle « Figer uniquement ce sous-dossier » sur chaque groupe virtuel. La copie manuelle du groupe et l'exclusion de son identifiant dans la règle dynamique du parent sont enregistrées **atomiquement** dans le JSON partagé, sans migration du schéma 8. Les autres groupes restent dynamiques. Le gel ultérieur du parent conserve les enfants déjà figés sans doublon. Tests de non-régression ajoutés.

**Validation :** tests automatisés sur commit final à vérifier ; tests Revit DYN-12 à DYN-16 non encore exécutés. PR #55 Draft, ne pas fusionner avant recette.

### PR #55 — Réversibilité sous-dossier manuel/automatique (16 novembre 2026)

**Revit validé utilisateur :** les cinq tests de gel individuel sont tous réussis ; le sous-dossier figé reste manuel, les autres se synchronisent et l'état persiste après réouverture.

**Amélioration implémentée, non encore validée Revit :** « Rendre ce sous-dossier automatique » uniquement sur les enfants précédemment figés d'un parent encore dynamique. Une mutation atomique réactive le groupe et retire son snapshot manuel ; confirmation explicite de la perte des réglages/modifications manuels propres au sous-dossier. Protections contre les suppressions de descendants, les paramètres Revit non disponibles et les états collaboratifs obsolètes. Tests unitaires ajoutés. **Ne pas fusionner #55 avant DYN-17 à DYN-20 et CI du dernier commit.**

### PR #55 — Validation finale Revit de la réversibilité (17 novembre 2026)

**Validation utilisateur confirmée :** les quatre vérifications demandées pour la réversibilité (DYN-17 à DYN-20) ont été réalisées avec succès dans Revit 2025.4 : retour du sous-dossier figé en automatique et icône associée, conservation de l'état des autres groupes sans doublon après actualisation/réouverture, dialogue de confirmation, protections des sous-dossiers enfants et absence de commande sur les dossiers manuels ordinaires. Le gel individuel (DYN-12 à DYN-16) était déjà déclaré réussi par l'utilisateur.

**Tests automatisés :** 500 tests Export réussis au commit `b4f115165600403ed7d6df55e4a32ea9299796fa` ; les workflows Export collaboratif et contrat ruban sont verts sur ce SHA. **Statut :** fonctionnalité validée dans Revit, prête à fusionner dans `main`. Aucune release supplémentaire demandée à ce stade.

### Export — Bouton À propos et version commune (17 novembre 2026)

**Demande utilisateur :** avant la prochaine release, ajouter un bouton « À propos » affichant le numéro de version de la suite Outils TAA.

**Branche :** `feat/about-version-taa` — PR dédiée. **Implémentation :** bouton dans l'en-tête d'Export ; dialogue WPF conforme à la charte TAA ; lecture locale centralisée de `OutilsTAA.extension/version.json` par `lib/common/taa_version.py`, réutilisable par les autres modules. Le dernier numéro publié confirmé reste `1.4.1`, avec canal `development` pour la copie courante (fonctionnalités non encore publiées). Pas de numéro de future release fixé ni de publication effectuée.

**Non-régression attendue :** ne changer aucun comportement Export (publication, persistance collaborative, PDF/DWG, sélection et dossiers dynamiques). Test automatisé de manifeste et contrat XAML ajouté. **État :** code proposé et enregistré sur branche ; CI / recette Revit encore à confirmer. **Prochaine action :** ouvrir le dialogue dans Revit 2025.4, valider puis préparer séparément la PR de release et le changement de numéro.

**Contrôle CI PR #60 (17 novembre 2026) :** 505 tests Export réussis au commit `cf886b14bc171c6826ad49720d5ba6e6d88db83a`. Les workflows Export collaboratif, contrat ruban et tests Calculs des pièces sont également verts. L'ajout du présent bilan est uniquement documentaire. **Recette dans Revit non encore effectuée**, PR Draft, pas de fusion ni release.


### Bouton À propos dans le ruban OutilsTAA (17 novembre 2026)

**Retour utilisateur :** la commande À propos, présente dans le code XAML d'Export, n'était pas visible dans l'onglet OutilsTAA de Revit parce qu'elle n'avait été créée que dans la fenêtre Export, pas dans le ruban pyRevit. Vérification GitHub : le fichier local contient `AboutButton`, tandis que l'interface représentée par la capture est le ruban Revit.

**Correction implémentée sur la PR #60** (`feat/about-version-taa`) : création du bouton de ruban global `OutilsTAA.tab/Informations.panel/APropos.pushbutton` (script IronPython, bundle.yaml, icon.png), qui ouvre la fenêtre À propos existante et lit la version depuis le manifeste central `version.json`. Accessible indépendamment d'Export et sans document Revit actif. Le bouton interne à Export est conservé en accès secondaire. Aucun changement des moteurs de production, de publication ou de stockage.

**Contrôles :** ajout du test `tests/test_about_ribbon_button.py` (bouton, icône, chemin d'import, absence de dépendance à un document Revit) ; CI à vérifier. **Recette dans Revit 2025.4 encore requise :** récupérer la PR #60, redémarrer/recharger pyRevit, constater le panneau Informations sur le ruban OutilsTAA, cliquer À propos, vérifier la version et la fermeture. Si le bouton est absent, comparer le chemin pyRevit chargé au répertoire Git modifié. Aucun merge/release effectué.

### Ruban OutilsTAA — demande d'alignement « À propos » au bord droit (17 novembre 2026)

**Retour Revit utilisateur :** le bouton À propos de la PR #60 est bien visible et son icône jugée conforme. Demande supplémentaire : l'ancrer systématiquement à l'extrême droite de la fenêtre Revit, au-delà de la zone vide du ruban, y compris lors du redimensionnement.

**Étude API :** la documentation Autodesk sur le ruban décrit un positionnement ordonné des panneaux de gauche à droite, sans contrat officiel d'alignement à droite pour un panneau de commande. Un bundle pyRevit garantit l'ordre des panneaux mais pas l'ancrage au bord droit de la fenêtre. Une intervention WPF interne pour ajouter un espacement dynamique serait non prise en charge et risquerait une régression lors d'un changement de résolution ou de version. Référence Autodesk : https://help.autodesk.com/view/RVT/2025/FRA/?guid=GUID-944577E2-5A10-4356-B0B6-3B81BCDA9491 ; guidelines API : https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Appendices/API_User_Interface_Guidelines/Revit_API_Revit_API_Developers_Guide_Appendices_API_User_Interface_Guidelines_Ribbon_Guidelines_html.html.

**Décision de prudence proposée :** conserver « Informations / À propos » comme dernier panneau à droite des autres outils, sans prétendre à un alignement dynamique sur le bord de l'écran. Aucune modification du code du ruban sur ce point ; pas de validation fictive d'une capacité non prise en charge. PR #60 non fusionnée, pas de nouvelle release.


### Ajustement final de la PR #60 — ordre des panneaux et couleur (17 novembre 2026)

**Précision de la demande :** l'utilisateur a corrigé sa direction : « À propos » doit être **le premier panneau, à gauche des autres modules**, et non à l'extrémité droite de l'écran. Le problème d'ancrage au bord droit n'est donc plus une demande active.

**Implémentation :** ajout de `OutilsTAA.tab/bundle.yaml` avec disposition explicite des quatre panneaux : `Informations[beforeall:]`, `Calculs`, `Export`, `PlansDeVente`. Ainsi « À propos » précède les modules existants. **Maintenance :** inscrire tout futur panneau dans cette liste pour éviter qu'il soit caché par un chargeur pyRevit traitant `layout` comme une liste exhaustive ; le test `test_about_panel_is_first_in_tab_layout_without_hiding_modules` vérifie cette règle.

**Couleur du pictogramme :** ancien fond `#FA641E` remplacé par **`#FD8B5A`**, exactement la couleur dominante du pictogramme `PlansDeVente.pushbutton/icon.png`. Forme « i » et transparence conservées. Test de non-régression sur l'asset PNG ajouté.

**État :** modifications GitHub sur PR #60, CI à vérifier sur SHA de code ; validation Revit de la nouvelle position et du pictogramme à effectuer. Aucun merge ni release.

**CI vérifiée au commit `9ff341721adea79cf45c6299ee34bd91f8de8a9d` :** 511 tests Export réussis ; workflows « Export ribbon contract », « Export — configuration collaborative » et « Calculs des pièces — tests hors Revit » verts. Ce commit documentaire final ne modifie ni code ni icône. Position à gauche et couleur de l'icône restent à confirmer dans Revit 2025.4 après rechargement. PR #60 toujours Draft, non fusionnée, aucune release.

## Publication Outils TAA v1.5.0 — 17 novembre 2026

**PR #60 :** bouton À propos et version centrale fusionnés dans main, commit `798f84b32cb928c54d0ba867d5a896717ec600fe`; présence en première position et fenêtre WPF confirmées par capture utilisateur dans Revit 2025.4.

**PR #61 :** dossier de release, manifeste `1.5.0 stable`, notes, trois tutoriels, workflow et installateur fusionnés, commit exact de main `b14ec914cc27e47c13561c54a1f9a841cb07ff10`.

**CI de préparation de la PR #61 :** 516 tests Export + 3 ruban + 125 Calculs + 301 Plans de vente, soit **945 tests réussis**. ZIP utilisateur de 214 entrées validé, manifest stable et SHA-256 du ZIP et CMD vérifiés. L'installateur v1.5.0 corrige la vérification SHA qui cherchait v1.4.0 dans l'ancienne version.

**Tag GitHub :** `v1.5.0` créé et vérifié sur **le même SHA `b14ec914cc27e47c13561c54a1f9a841cb07ff10`** (comparaison avec main : identique). Le workflow publie automatiquement la release GitHub sur main uniquement après sa propre validation. **Limite de vérification de cette session :** l'outil connecté confirme le tag et le manifeste, mais ne permet pas de lister directement les six actifs de la page de release ; ne pas inventer leur contrôle indépendant. Confirmer le ZIP, le CMD, `SHA256SUMS.txt` et les trois tutoriels sur https://github.com/midka33/Outils-TAA/releases/tag/v1.5.0 avant déploiement de masse.

**Recettes restant à effectuer :** test de l'installateur CMD sur un poste Windows, deux postes concurrents en stockage SMB collaboratif, cas complexes de groupes Revit. Aucune suppression des anciennes releases ou des branches métiers.
