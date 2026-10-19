# Plans de vente V1.1 — recette des pièces liées

**Date :** 19 octobre 2026

**Branche :** `feature/plans-de-vente-linked-rooms`

**Base :** `main`, `78da6d557ed88418fe4b1e07d77a66d97a2fba5a`

**Suivi :** issue #27 ; PR à conserver en **Draft**

**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x / Windows

**Statut :** développement et tests hors Revit ; **recette Revit non effectuée**.

Cette V1.1 désigne la version du **module**. Aucun tag produit, aucune nouvelle
release Outils TAA ni fusion dans main n'est autorisé avant validation utilisateur.
La release stable précédente reste Outils TAA v1.2.0 / Plans de vente V1.

## Préparer le projet de recette

Travailler sur une copie de SITE.rvt avec BATIMENT_A.rvt, BATIMENT_B.rvt et
BATIMENT_C.rvt liés directement. Fermer Revit avant de changer de branche puis
le relancer, afin de recharger tous les modules Python.

- SITE contient la feuille modèle, le cartouche, les zones explicites, les types
  d'étiquettes et de cotes ainsi que les nomenclatures modèles.
- Prévoir un logement 101 dans SITE et dans A/B, puis deux instances du même
  bâtiment avec des translations/rotations différentes.
- SITE doit avoir un **niveau et une vue de plan** pour chaque altitude de niveau
  liée transformée. Le rapprochement est fait sur `ProjectElevation` dans le
  repère SITE, tolérance 1 mm. Un nom identique ne suffit pas ; aucune création
  automatique de niveaux ou de vues de production n'est réalisée.
- Les vues/gabarits SITE doivent afficher les liens et les bonnes phases.
  Conserver les réglages Revit habituels de visibilité, phase et correspondance
  des phases ; le module ne les réécrit pas.
- Configurer le même paramètre logement (de préférence partagé, même GUID) et
  les paramètres Bâtiment / Typologie dans chaque fichier.
- Sur les nomenclatures de pièces du modèle, cocher le réglage natif
  **Inclure les éléments des fichiers liés**. Le champ logement doit être
  présent et filtrable. Donner un **Nom d'instance de lien** non vide, distinct
  pour chaque instance d'un même fichier, dans les propriétés Revit.
- Prévoir des nomenclatures intérieure/extérieure avec filtres métier,
  regroupements et totaux ; noter les surfaces de référence par logement.

## Utilisation attendue

L'étape 1 propose **Inclure les pièces des fichiers Revit liés**, décoché par
défaut à chaque ouverture. Décoché : chemin V1 hôte. Coché : hôte et liens
chargés directs, avec colonne **Source** (fichier et numéro d'instance).
Le changement d'option relance l'analyse et remplace sa sélection précédente.
Les liens déchargés ou inexploitables sont signalés dans le statut et le rapport.

Le numéro affiché et la valeur du cartouche restent `101`. Les noms techniques
vues/feuilles/nomenclatures des sorties liées ajoutent `-L<id instance>` pour
éviter les collisions. L'identité métier utilise le **UniqueId de l'instance +
numéro logement** ; les références de pièces conservent aussi le UniqueId source.
Deux sources ne sont jamais regroupées à partir de leur seul numéro.

## Campagne Revit à remplir

Aucune ligne ci-dessous n'est considérée comme validée par les tests simulés.

| Test | Manipulation | Résultat attendu | Statut |
|---|---|---|---|
| 01 | Option décochée ; comparer au même modèle avec v1.2.0 | Même population, vues, crop, tags, cotes, nomenclatures et cartouche hôte | À tester |
| 02 | Cocher puis décocher | Hôte + liens puis uniquement hôte ; aucun logement lié résiduel | À tester |
| 03 | SITE/A/B contiennent 101 ; filtrer Bâtiment | Trois logements distincts ; seules les pièces de la source sélectionnée | À tester |
| 04 | Générer un mono-niveau lié A | Feuille complète dans SITE, aucune écriture dans A | À tester |
| 05a | Duplex B, modèle à une vue | Une feuille par niveau, mêmes totaux globaux du duplex sur chaque feuille | À tester |
| 05b | Duplex B, modèle à deux vues | Bas puis haut selon altitude, échelle commune, zones et absence de superposition | À tester |
| 06 | Tags liés ; répéter avec même pièce dans deux instances | Tags natifs liés à la bonne instance ; placement intérieur et collisions contrôlés | À tester |
| 07 | Cotes entre murs, puis limites séparatrices/sols | Cotes natives mesurant la largeur/longueur attendue ; aucun témoin au mauvais bâtiment | À tester |
| 08 | Repérage avec lien déplacé et tourné | Zone remplie alignée avec le bon logement dans SITE | À tester |
| 09 | Nomenclatures de A/101 et B/101, puis seconde instance de A | Aucun mélange ; filtres int/ext, colonnes, unités, regroupements et totaux conservés | À tester |
| 10 | Cartouche + surfaces du duplex | 101 sans suffixe technique, bâtiment/typologie source, étages corrects ; sommes natives exactes | À tester |
| 11 | C déchargé | A/B et SITE utilisables ; avertissement C, pas de plantage | À tester |
| 12 | Lot SITE + A + B, dont un modèle/source incorrect | Source/logement/étape lisibles ; rollback du logement en erreur, suivants traités | À tester |
| 13 | Deux instances du même fichier, rotation 90°, translation XYZ | Deux lignes distinctes ; crop, tags, cotes et repérage aux bonnes coordonnées | À tester |
| 14 | Lien symétrisé horizontalement, vue SITE tournée | Géométrie et dimensions correctes, pas de double transformation | À tester |
| 15 | Niveau source renommé, même altitude SITE | Vue sélectionnée par altitude ; nom source conservé dans les données logement | À tester |
| 16 | Niveau SITE absent ou deux niveaux à même altitude | Erreur explicite avant génération ; jamais choix arbitraire par nom | À tester |
| 17 | Désactiver inclusion des liens sur la nomenclature modèle | Erreur demandant le réglage natif ; aucune feuille partielle conservée | À tester |
| 18 | Même nom d'instance pour deux liens du même fichier | Erreur de source ambiguë ; aucun tableau trompeur | À tester |
| 19 | Paramètre de projet local homonyme non partagé | Rapprochement seulement si unique ; doublon refusé ; paramètres partagés par GUID strict | À tester |
| 20 | Export puis Calculs des pièces | Fonctionnement inchangé ; aucun fichier métier de ces modules modifié | À tester |

Pour chaque échec : joindre le rapport, le nom du fichier et de l'instance,
le logement, l'étape, une capture et la disposition/rotation du lien.
Pour les cotes, vérifier **valeur mesurée et références**, pas seulement leur présence.

## Limites et décisions de stabilité

- Liens directs uniquement. Les liens imbriqués ne sont pas parcourus ; leurs
  instances n'ont pas une référence directe exploitable depuis SITE pour les tags
  et cotes de cette version. Lier directement le bâtiment à traiter.
- Liens inclinés ou retournés verticalement : ignorés avec avertissement.
  Rotations horizontales, translations XYZ et symétries horizontales : adaptations
  présentes, validation Revit obligatoire.
- Aucune copie des pièces dans SITE et aucune modification d'un document lié.
- Les références liées de murs/sols/séparateurs sont converties par
  `Reference.CreateLinkReference`. Si Revit refuse une référence, le rapport
  signale la cote absente/partielle ; aucune cote de détail fictive ne la remplace.
- Deux cotes principales maximum par pièce, comme V1 ; contrôler les géométries
  atypiques, les arcs, les limites portées par un lien imbriqué et les séparateurs
  masqués. Une limite d'un lien imbriqué n'est pas cotée comme un mur hôte.
- Les tableaux restent des nomenclatures natives Revit. Les deux filtres source
  (fichier + instance) sont appliqués aux **copies**, en plus du filtre logement.
  Leurs champs ajoutés sont masqués ; styles, tris, unités, totaux et filtres
  métier sont conservés. Les anciens filtres source sont remplacés.
- Une nomenclature de pièces non filtrable par logement bloque la sortie liée.
  Les autres catégories de nomenclatures restent reproduites selon V1.
- En mode liens, les copies de nomenclatures des logements **hôtes** excluent les
  liens pour ne pas mélanger SITE/101 et BATIMENT/101. Option décochée, les
  réglages historiques ne sont pas modifiés.
- Les surfaces habitables/annexes continuent de provenir des nomenclatures et de
  leurs filtres métier. Aucun nouveau classement automatique intérieur/extérieur
  ni nouvelle écriture de surfaces dans les fichiers source n'est ajouté.
- Les noms d'instance natifs doivent permettre un filtrage non ambigu ; à défaut
  le module s'arrête pour le logement concerné avec une consigne de correction.
- La création et la mise à jour des plans existants restent distinctes ; V1.1
  ne met pas à jour automatiquement les plans déjà générés.

## Contrôles hors Revit

La suite `tests/plans_vente/test_linked_rooms.py` exécute les adaptations réelles
avec des objets simulant les frontières Revit : regroupement, désactivation,
collecte/caches, transformations et inverse, crop, création de tag, références
et création de cote, paramètres, multi-niveaux, filtres natifs de nomenclature,
callbacks et erreurs. Les tests V1 sont conservés ; seuls les trois contrats
textuels du numéro de build UI suivent le nouveau build `linked-rooms-v1.1`.

```bash
PYTHONPATH=OutilsTAA.extension/lib python -m pytest tests/plans_vente -q
python -m pytest tests/calculation -q
python -m pytest tests OutilsTAA.extension/OutilsTAA.tab/Export.panel/tests --ignore=tests/calculation --ignore=tests/plans_vente --import-mode=importlib -q
```

La CI Calculs est aussi déclenchée pour les PR touchant Plans de vente. Le
workflow existant de packaging peut construire un artefact sur la PR ; ses
étapes de publication sont exclues sur les PR. Ne pas déclencher une release.

## Références API consultées

- Autodesk, [Revit Links — références liées](https://help.autodesk.com/cloudhelp/2018/ENU/Revit-API/Revit_API_Developers_Guide/Advanced_Topics/Linked_Files/Revit_Links.html) : `GetLinkDocument`, instance et `CreateLinkReference`.
- Autodesk, [Working with ViewSchedule](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Views/View_Types/TableView/ViewSchedule/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Views_View_Types_TableView_ViewSchedule_Working_with_ViewSchedule_html.html) : champs natifs RevitLinkInstance/RevitLinkType et filtres masqués.
- Autodesk, [NewRoomTag](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/9847aafe-42f9-fe8e-5229-c491add7ec46.htm) et [LinkElementId à deux identifiants](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/f8cebb9e-d6d5-28a3-5a53-8d3fe71346aa.htm).

Les pages 2025 correspondantes n'étaient pas accessibles depuis l'environnement
de développement. Les contrats documentés dans les versions adjacentes étayent
l'adaptation ; ils ne remplacent pas l'exécution des cas ci-dessus dans **2025.4**.

## Autorisation de fusion

- [ ] CI de la tête de PR réussie (Plans de vente, Export, Calculs).
- [ ] Recette Revit 2025.4 ci-dessus confirmée par l'utilisateur.
- [ ] Limites acceptées et rapport de recette conservé dans la PR.
- [ ] Passage Ready et fusion uniquement après cette confirmation.
