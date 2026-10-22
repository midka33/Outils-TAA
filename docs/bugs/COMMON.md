# Registre des bugs — Commun

**Statut :** Référence active de développement et de non-régression  
**Cible :** Revit 2025.4 / pyRevit 5.x

Bugs transversaux communs à plusieurs modules.

Avant toute modification liée à ce périmètre, lire les fiches applicables
et exécuter les tests anti-régression cités.

---

### BUG-COMMON-002 — Fichiers temporaires suivis dans les archives source

**Symptôme :** l’archive de `main` au commit `44503dff` contient deux fichiers
`docs/09_Export_Project_Persistence*.tmp`.

**Cause racine :** ces fichiers temporaires étaient suivis par Git ; un simple
nettoyage du répertoire de travail ou une exclusion locale ne les retire pas
des archives d’une release.

**Correction :** suppression des deux fichiers suivis et ajout d’exclusions
pour temporaires et caches Python dans `.gitignore`.

**Règle préventive :** vérifier le contenu de l’archive du commit à publier,
pas seulement l’état du répertoire de travail.

**Anti-régression :** le workflow Export inspecte `git archive HEAD` et bloque
les suffixes temporaires/cache, modèles Revit, dessins DWG et MSI ; contrôle
négatif sur le commit d’origine et positif sur l’arbre préparé.

---

### BUG-COMMON-003 — Les nouveaux modules d'annotation échouent avec (Name)

**Symptôme :** Cotation et Étiquetage automatiques affichent chacun
`0 annotation(s) créée(s)` pour deux plans comportant respectivement 40 et
44 pièces. Le rapport signale
`hors groupe : annulé sans annotation isolée (Name)`.

**Cause racine :** l'adaptateur initial lisait directement `room.Name` et
`room.Level.Name` en assemblant les entrées du moteur Plans de vente.
IronPython peut lever `AttributeError: Name` sur ces éléments Revit.
Les services Plans de vente, eux, utilisaient déjà des accesseurs robustes.

**Correction :** lecture du nom de pièce via
`get_Parameter(BuiltInParameter.ROOM_NAME).AsString()`, du numéro via
`ROOM_NUMBER`, et des noms d'éléments via `Element.Name.GetValue`.
Validation de niveau avec ce même accesseur. Isolation transactionnelle par
pièce hors groupe et ajout du traceback complet au rapport.

**Règle préventive :** aucun accès direct à `Room.Name`,
`GroupType.Name`, `Level.Name` ni aux noms de styles Revit sans
l'accesseur robuste. Tout nouveau module reprenant un service validé
doit tester aussi sa couche d'adaptation et non seulement les imports.

**Anti-régression :** `tests/annotations/test_annotation_runtime_mocks.py`
simule une pièce dont `Name` lève `AttributeError("Name")` ;
`tests/annotations/test_annotation_beta_contract.py` vérifie les scripts.
Recette utilisateur dans Revit 2025.4 obligatoire.

---

### BUG-COMMON-004 — Cotations toutes rejetées après étiquetage

**Symptôme :** les 40 étiquettes du niveau 0 sont créées, mais le module Cotation ne crée aucune cote pour 40 pièces au niveau 0 et 44 pièces au niveau 1. Toutes les pièces indiquent `Aucune position de cote sans collision`.

**Cause racine :** le moteur historique choisit ensemble les deux cotations principales en minimisant les conflits, avec avertissement si une collision est inévitable. L'adaptateur bêta rejetait ensuite **toute la paire** dès qu'un seul des deux placements présentait un contact ou une sonde hors pièce ; aucune création partielle n'était possible.

**Correction :** nouveau choix géométrique pur `lib/annotations/strict_dimension_positioning.py` qui réutilise les candidats 06F de Plans de vente et accepte zéro, une ou deux cotes selon les placements réellement compatibles. Les collisions avec les étiquettes, les cotes existantes et les cotes créées dans le même appel sont éliminatoires. Le texte des cotes doit rester dans la pièce ; les sondes hors pièce sont diagnostiquées. Une orientation rejetée ne bloque pas la seconde. Le moteur de Plans de vente reste **inchangé**.

**Règle préventive :** dans un moteur multi-annotations, ne jamais traiter une collision d'un élément comme un échec total si les autres éléments peuvent être créés individuellement et sans collision. Prévoir une sentinelle explicite, des diagnostics par orientation et un test de création partielle.

**Anti-régression :** `tests/annotations/test_strict_dimension_positioning.py` teste le placement partiel, la non-superposition et des candidats du moteur 06F. La CI exécute aussi `tests/plans_vente`. Recette Revit à rejouer sur les pièces 1123/2213, puis les deux vues.


---

### BUG-COMMON-005 — Cotes paralleles et longueurs de murs a la place des dimensions de pieces

**Symptome :** la commande Cotation cree 57 cotes sur le niveau 0,
mais plusieurs sont paralleles dans une meme piece et mesurent de courts
troncons de murs au lieu des deux grandes dimensions interieures.
Retour utilisateur du 22 octobre 2026, avec capture et rapport.

**Cause racine :** `DimensionService.create_dimensions` du module
Plans de vente tente d'abord les paires de faces opposees (06F), puis
`_fallback_length_indexes` si une cote principale n'a pas ete produite.
Cette methode produit des dimensions le long des murs via leurs references
d'extremite. Le nouvel adaptateur strict avait conserve ce comportement :
il pouvait remplir deux positions avec des longueurs de murs paralleles.

**Correction :** uniquement dans `GenericDimensions` des nouveaux
modules, `_fallback_length_indexes` renvoie une liste vide.
`_room_boundary_candidates` reutilise les references de faces finies du
service valide, puis garde les deux paires principales de faces opposees
de plus grande portee, non necessairement perpendiculaires, via `lib/annotations/principal_dimension_axes.py`. Si une
paire n'est pas exploitable sans chevauchement, aucune cote de secours sur
un segment de mur ne la remplace. Plans de vente reste inchange.

**Regle preventive :** une cote de longueur de mur n'est pas une cote
entre faces opposees. Une exigence de deux grandes dimensions par piece
doit etre garantie lors du choix de references, avant le placement.
Ne jamais compenser une orientation principale manquante par une longueur
de mur ; les deux paires retenues doivent correspondre a deux directions distinctes, sans imposer 90 degres.

**Anti-regression :** `tests/annotations/test_principal_dimension_axes.py`
(7 x 3,5 m, plan tourne, pair non orthogonal, une seule direction),
`tests/annotations/test_annotation_runtime_mocks.py` (filtrage reel
de l'adaptateur et fallback inactif), execution de `tests/plans_vente`
et du workflow Export. Recette Revit sur copie avec suppression manuelle
des cotes erronees du test precedent avant relance.


---

### BUG-COMMON-006 — Contrainte orthogonale injustifiee et cotes non alignees

**Symptome :** une piece biaise ne peut pas recevoir ses deux plus grandes cotes si leurs orientations ne sont pas perpendiculaires. Les cotations horizontales/obliques des pieces voisines ne suivent pas une meme ligne.

**Cause racine :** le filtre initial `principal_pairs` exigeait un angle droit entre les deux familles de faces opposees ; le selecteur strict ne tenait compte que des collisions et des positions propres a chaque piece, sans guidage par les cotes deja posees.

**Correction :** trier les paires dominantes du moteur Plans de vente par **distance entre faces decroissante**, conserver les deux plus grandes de directions distinctes, sans contrainte de 90 degres. Recuperer les lignes des cotes deja presentes dans la vue ; generer, lorsque c'est possible, des positions de cote *exactement colineaires* a celles des pieces voisines de meme orientation. L'alignement n'est choisi que si l'emprise reste dans la piece et ne recouvre ni etiquette ni autre cote. Les references natives Revit demeurent inchangees. Les deux modules restent sur la branche de test, sans toucher Plans de vente.

**Regle preventive :** ne pas ajouter de contrainte geometrique absente de la demande metier. Distinguer choix de la dimension (portee maximisee) et placement graphique (alignement privilegie, collisions prioritaires).

**Anti-regression :** `tests/annotations/test_principal_dimension_axes.py` (piece biais, 2 grandes portees non orthogonales), `tests/annotations/test_dimension_alignment.py` (alignement, obstacle, voisin eloigne), `tests/annotations/test_annotation_runtime_mocks.py` (adaptateur reel simule), suite complete `tests/plans_vente` et tests Export sur GitHub Actions. Validation dans Revit 2025.4 obligatoire.


---

### BUG-COMMON-007 — Une seule cote par piece et impossibilite de completer

**Symptome :** sur `Collectifs A_Niveau 0`, 34 cotes pour 40 pieces,
la plupart n'ont qu'une des deux grandes dimensions. Le rapport indique
repetitivement `orientation ignoree : aucune position sans chevauchement`,
y compris quand `minimum 0 collision(s) etiquette, 0 cote(s)`.
Un second lancement sautait les pieces deja partiellement cotees.

**Cause racine :**
1. Le selecteur strict rejetait tout `graphic_hit` entre les deux cotes.
   Or deux lignes mesurant les portees completes d'une piece rectangulaire
   se croisent necessairement, meme quand leurs textes ne se recouvrent pas.
2. Une bbox de cote existante pouvait interdire tout le chemin de la seconde
   cote ; la selection d'une piece se fondait aussi sur la simple
   intersection des bboxes, et non sur les references effectivement cotees.

**Correction :** autoriser uniquement le croisement ponctuel des deux
traits de cotes dans le selecteur, en interdisant les chevauchements de
textes, temoins, et lignes colineaires. Pour les anciennes dimensions de
la vue, reserver leur texte (avec fallback bbox Revit si texte inaccessible)
et tester explicitement le recouvrement colineaire des traits. Reprendre
les pieces partiellement cotees et identifier les paires deja cotees par
leurs deux references natives `ConvertToStableRepresentation`, sans
considerer une bbox partagee comme une preuve de cotation. Le placement
des **etiquettes** conserve la protection de toute la bbox des cotes.

**Regle preventive :** les contraintes graphiques de cotation doivent
distinguer croisement simple de traits, overlap de textes, recouvrement
colineaire et doublon de references. Une piece partiellement annotee
reste eligible aux annotations manquantes, sans duplications.

**Anti-regression :** tests geometriques croisement/perpendicularite/texte
dans `tests/annotations/test_strict_dimension_positioning.py`, tests
de reference native + reprises dans
`tests/annotations/test_annotation_runtime_mocks.py`, tests
de colinearite dans `tests/annotations/test_dimension_alignment.py`,
CI complete Annotations + Plans de vente + Export.
Une recette Revit 2025.4 doit confirmer la position du texte et les
references effectivement retrouvees sur 2 lancements successifs.


---

### BUG-COMMON-008 — WC/celliers non cotes et arêtes de plancher absentes sur les balcons

**Symptôme :** sur `Collectifs A_Niveau 1`, l'outil crée 63 cotes pour
44 pièces. Dans de nombreux WC et celliers, une ou deux cotes manquent ; les
pièces 2249, 2251 et 2252 sont entièrement rejetées avec
`0 texte(s) dans piece` malgré des positions candidates sans collision.
Les pièces extérieures 2237–2240 signalent l'absence d'arête de plancher
superposée fiable.

**Causes racines :**
1. Le sélecteur strict imposait que les coins de toutes les enveloppes de
texte de cote (horizontal et aligné) restent dans la Room. À l'échelle
1:100, le gabarit conservateur de texte mesure plusieurs dizaines de
centimètres en modèle et ne tient pas dans certains WC. Cette exigence
n'était pas une règle métier : seules les superpositions de cotes et
d'étiquettes étaient interdites.
2. Dans la recherche PDV, `_floor_edges_for_room` examine les planchers
de niveau identique quand il en existe, au détriment des planchers d'un
niveau voisin. Une dalle de balcon rattachée au niveau voisin peut donc
être ignorée alors même que sa vraie arête est superposée à la limite.

**Correction :** garder les tests de chevauchement impératifs ; privilégier
le texte **entièrement intérieur**, mais autoriser le texte partiellement
extérieur à une petite pièce en dernier recours, avec avertissement
explicite. Rechercher en priorité la vraie arête de dalle via la méthode
PDV, puis, seulement si cette recherche échoue, inspecter les arêtes
natives des dalles rattachées à des niveaux situés dans la tolérance de
500 mm. Utiliser **les mêmes** critères PDV de recouvrement, proximité XY,
pente et niveau et les `Reference` Revit, sans remplacer une cote
par une longueur de mur. Si aucune arête exploitable n'existe, conserver
le fallback natif des séparations de pièces avec son avertissement.

**Règle préventive :** ne pas transformer une préférence graphique
(texte à l'intérieur de la pièce) en condition d'échec absolue si la
demande garantit d'abord l'absence de collision. Lorsqu'une référence
de bord de dalle est recherchée, vérifier aussi les dalles voisines
par niveau uniquement après l'échec de la recherche canonique.

**Anti-régression :** `test_petite_piece_autorise_texte_partiellement_dehors_sans_collision`,
`test_texte_interieur_reste_prioritaire_sur_le_repli_exterieur`,
`test_repli_texte_exterieur_nignore_jamais_collision_etiquette`,
`test_wc_small_room_plan_graphics_selects_fallback_without_texte_inside`,
`test_balcon_priorite_reference_arrete_de_plancher_pdv`,
`test_balcon_niveau_de_plancher_voisin_reutilise_match_pdv` et
`test_balcon_recherche_reelle_aretes_niveaux_voisins_et_cache`.
Exécuter les tests Annotations, les tests Plans de vente et Export ;
revalidation visuelle obligatoire dans Revit 2025.4.


---

### BUG-COMMON-009 — Fermeture brutale de Revit après mise à jour cotation balcons

**Symptôme :** après le correctif des WC, celliers et balcons,
l'utilisateur signale une fermeture brutale de Revit 2025.4 au
lancement de Cotation automatique. Pas de journal Revit analysé à ce
stade ; il ne faut donc pas affirmer que la cause exacte est confirmée.

**Journal du crash identifie :** `journal.0278.txt` (session ouverte
le 22/10/2026 à 08:13:22). À 13:57, le journal affiche
`65 annotation(s) creee(s)` après une cotation sur **une** vue ;
à 13:58, `63 annotation(s) creee(s)` sur **une** vue. Après
rechargement de pyRevit à 14:14:25, le dernier lancement de
`OutilsTAA / Annotations / Cotation` intervient à 14:14:42. La
confirmation indique **deux vues** ; le journal s'interrompt à
14:15:00, sans rapport final de la commande ni séquence normale de
fermeture de Revit. Les journaux `0279` et `0280` sont des
sessions parallèles encore actives à 14:26:38 et ne montrent pas
cette commande. Ce journal désigne la session de crash, **pas le
site exact de l'exception native**. Relecture contradictoire des trois journaux : dans cette session,
à 11:12 et 11:31, deux commandes sur **deux vues** ont retourné
normalement un bilan de **0 annotation créée**, sans crash. Cela démontre
que le simple passage de deux vues au lanceur ne provoque pas
systématiquement de fermeture. L'utilisateur confirme également avoir
déjà réussi à coter deux vues en une seule commande lors d'essais
antérieurs. Les sessions avec 65 puis 63 cotes créées à 13:57 et 13:58
portaient sur **une vue** chacune. La dernière tentative à 14:15
s'interrompt à la **fenêtre de confirmation** : le journal ne démontre
pas si la création de cotes a commencé. La corrélation « deux vues »
ne suffit donc pas à établir la cause. À investiguer en priorité :
changement de version rechargée entre essais, état de la maquette,
transaction/références de cote, géométrie des balcons et éventuel
crash natif. Le mode une pièce est un **garde-fou temporaire** et non
la validation d'une cause liée au multi-vues.

**Cause suspectée (non prouvée) :** le nouveau chemin
`GenericDimensions._nearby_floor_edges` introduisait un second
parcours des dalles du document, des solides natifs et de leurs arêtes.
Il se déclenchait quand la recherche habituelle de Plans de vente ne
trouvait pas de référence ; l'appel Revit natif peut ne laisser aucune
exception Python exploitable si le processus tombe. D'autres causes
(état du document, référence native, API Revit) restent possibles.

**Mesure conservatoire :** supprimer entièrement l'exploration
supplémentaire des solides et le fallback des dalles de niveaux voisins,
pour revenir à `DimensionService._matching_floor_edge_reference` de
Plans de vente (inchangé). Suspendre les cotations multi-vues,
multi-pièces et les groupes attachés. La bêta exige temporairement
la sélection d'une vue et d'une pièce hors groupe sur une **copie**.
Avant la création de cotations, le journal
`%TEMP%\OutilsTAA_Annotations_crashtrace.log` est écrit et fermé pour
préserver les dernières étapes si un crash natif se reproduit.

**Règle préventive :** ne jamais réactiver un parcours
supplémentaire de géométrie lourde native Revit après un crash
sans journal de crash, mesure de coût, limites explicites et test
sur une pièce isolée. Suspendre le traitement de masse en cas de
crash complet et documenter qu'une vérification statique ne
certifie pas la stabilité du processus Revit.

**Anti-régression :** `tests/annotations/test_crash_guard.py`
(journal écrit, absence de méthode de parcours supplémentaire,
sélection imposée) et `test_annotation_runtime_mocks.py` (moteur
canonique PDV et filtre par une pièce). Exécuter Annotations,
Plans de vente et suite Export en CI, puis demander les
journaux Revit du crash et valider sur **copie de maquette**.
**Recette utilisateur post-correctif (22 octobre 2026) :** lancement en mode diagnostique sur une seule pièce hors groupe, numéro **1170**, vue **Collectifs A_Niveau 0** : **2 annotations créées**, rapport pyRevit terminé sans fermeture signalée. Un avertissement de *proximité avec un équipement* demande une vérification visuelle ; ce n'est pas la preuve d'un chevauchement. Ce résultat confirme un essai unitaire réussi, mais ne prouve ni les bonnes valeurs/positions des deux cotes, ni la stabilité multi-pièces. Journal `OutilsTAA_Annotations_crashtrace.log` et capture du résultat encore à examiner.

Statut : crash natif **non reproduit lors de ce premier essai isolé** ; cause précise du crash initial à déterminer.


---

### BUG-COMMON-010 — Les deux cotes de la loggia 2238 disparaissent en masquant les séparations

**Symptôme réel Revit (22/10/2026) :** dans \`Collectifs A_Niveau 1\`,
les cotes de la loggia **2238** (3,12 m et 3,62 m) sont visibles tant
que les lignes de séparation sont visibles. Lorsque l'utilisateur
masque la catégorie \`Séparations de pièces\` dans la vue, **les deux
cotes disparaissent**. Les deux cotes existaient réellement avant ce test.

**Cause racine confirmée :** faute d'une arête native de dalle validée,
le moteur de cotation utilisait comme référence géométrique native
\`GeometryCurve.Reference\` de la séparation de pièce. Dans Revit,
la visibilité de la cote dépend alors de celle de l'élément référencé.
Le contrôle précédent détectait ce cas et l'avertissait mais l'acceptait.

**Correction de la bêta Annotations uniquement :** pour les cotes des
pièces hors groupe dont une face sélectionnée a \`source_kind="separator"\`,
créer en transaction des \`DetailCurve\` 2D très courtes (5 mm)
exactement sur le segment concerné, avec le style de ligne choisi par
l'utilisateur, et remplacer la référence de cotation par
\`detail.GeometryCurve.Reference\`. Les références natives de murs ou
de dalles qui ont été trouvées restent prioritaires et inchangées.
Une seule pièce par lancement reste imposée après le crash précédent.
Les lignes de substitution ne sont **pas associatives** avec les dalles
ou séparations réelles ; elles doivent être contrôlées après modification
du plan. Les détails 2D doivent rester visibles dans cette vue même
si les séparations sont masquées.

**Atomicité / anti-doublon :** si aucune cote ne référence les détails
créés, annuler l'ensemble dans la \`TransactionGroup\` plutôt que laisser
des objets orphelins. Si une seule cote est créée, supprimer les détails
de substitution inutilisés. Au second lancement, vérifier aussi
la position du petit détail + la portée de la cote déjà existante :
une référence de substitution n'est pas identique à la référence
de séparation d'origine.

**Règle préventive :** lorsqu'un élément de construction peut être
masqué mais qu'une cote doit rester visible, ne jamais accepter
silencieusement une référence géométrique de séparation de pièce
comme référence définitive. Privilégier murs/dalles natifs, puis
références de détail indépendantes avec style visible, suivi explicite
et contrôle graphique Revit. Ne pas ajouter un parcours de solides
supplémentaire après un crash non élucidé.

**Tests anti-régression :**
\`test_balcon_proxies_2d_reference_native_sans_solides_et_cleanup\`,
\`test_balcon_deux_proxies_et_seulement_une_cote_nettoie_reste\`,
\`test_balcon_aucune_dimension_references_proxies_provoque_rollback\`,
\`test_balcon_second_lancement_reconnait_cote_existante_avec_proxy\`,
suites complètes Annotations, Plans de vente et Export. **La
validation réelle indispensable** consiste à supprimer manuellement
les anciennes cotes de 2238 sur une copie, relancer la commande,
masquer les lignes de séparation et vérifier la persistance des cotes
sans masquer le style des lignes 2D. Pas de validation Revit de cette
correction tant que le nouvel essai n'a pas été fait.


---

### BUG-COMMON-011 — Une dalle de loggia pertinente ignorée par le sélecteur de niveau PDV

**Symptôme :** la loggia 2238 peut recevoir deux cotations géométriquement
correctes mais associées à des lignes de séparation ; elles disparaissent
toutes deux au masquage de la catégorie. Le moteur n'a pas retenu d'arête
de dalle native. Le cas de dalle attachée à un autre niveau est suspecté,
mais **non prouvé dans la maquette 2238**.

**Cause racine démontrée dans le code :** le service historique choisissait
`candidate_floors = same_level if same_level else nearby_level`.
Dès qu'au moins un plancher du niveau existait dans le projet, tous les
planchers des niveaux voisins, même à proximité géométrique de la Room,
étaient écartés. Le cache des arêtes était indexé par le niveau seul ;
une recherche locale par pièce ne pourrait pas le réutiliser correctement.

**Correction (sur la branche bêta exclusivement) :** extraction de la
**politique de sélection des planchers** dans
`lib/common/floor_reference_policy.py`, sans accès à l'API Revit. Le
service natif `DimensionService._floor_edges_for_room` demeure l'unique
propriétaire de l'extraction d'arêtes et réutilise cette politique :

- `mode="legacy"` utilisé par Plans de vente reproduit strictement le
  comportement et la clé de cache historiques (aucune évolution métier PDV) ;
- `mode="local"` utilisé par Cotation automatique exige le recoupement
  de la boîte XY de la Room (marge 300 mm), accepte les dalles sur même
  niveau **et** niveaux proches déjà filtrés en altitude (±500 mm),
  limite à **six planchers au total** et retourne une liste vide si le
  budget est dépassé ou si les emprises sont inconnues ;
- le cache devient **par pièce** uniquement pour Cotation automatique.
  L'extraction de géométrie native n'est **pas dupliquée**. Si aucune
  arête fiable n'est trouvée, le fallback des repères 2D existant est
  conservé, sans rendre une cote dépendante de la séparation.

**Règle préventive :** dissocier la politique pure de choix de supports
et le parcours natif de leurs solides. Pour tout adaptateur de lecture
géométrique, garantir une enveloppe XY, un budget d'objets, une
stratégie de repli sûre, une clé de cache adaptée au périmètre et
une non-régression du mode historique.

**Anti-régression :** `tests/annotations/test_floor_reference_policy.py`
(mode legacy inchangé, dalle voisine, budget, bbox inconnue, absence de
second parcours natif), `tests/annotations/test_annotation_runtime_mocks.py`
(raccordement du hook et cache par pièce), suites complètes
Annotations, Plans de vente, Export et Calculs. Les tests Python
ne prouvent pas la fiabilité du nouveau parcours en Revit : conserver
**une vue / une pièce hors groupe**, sur une copie de maquette, et
vérifier la loggia 2238 avec séparations masquées avant toute
activation du traitement en masse.

**Statut :** code partagé et suites Python testés ; comportement
de 2238 dans Revit 2025.4 encore non validé.


---

### BUG-COMMON-012 — Garde-corps omis dans l'ordre des références d'une loggia

**Symptôme :** sur la loggia 2238, Cotation automatique produit deux
dimensions 3,12 m et 3,62 m mais recourt à de petites lignes de détail
2D non associatives lorsque la dalle ne fournit pas d'arête fiable,
sans examiner un éventuel garde-corps modélisé.

**Cause racine :** la chaîne de références ne prévoyait que faces de
murs, arêtes de dalles, puis séparations de pièces et repères 2D.
La classe `DB.Architecture.Railing` n'était pas interrogée.

**Correction bêta :** entre la recherche canonique des murs/dalles et
le fallback 2D, tenter une **arête native** d'un garde-corps Revit
visible dans la vue, dont la projection XY coïncide suffisamment avec
la limite de la Room. Utiliser le même appariement géométrique que
les arêtes de dalles : écart maximal de 20 mm, angle maximal 3 degrés,
recouvrement minimal 60 %. La référence est
`Edge.Reference`, jamais la seule courbe d'axe `Railing.GetPath`,
ni une projection approximative. Si la référence native est absente
ou non exploitable, conserver le repère 2D de 5 mm comme dernier recours.

**Sécurité :** recherche sur **une seule pièce en mode diagnostic**,
garde-corps visibles dans la vue et proches de la Room (150 mm XY),
maximum 2 garde-corps et 120 arêtes examinées. Surplus ou géométrie
inaccessible => aucun nouvel élément natif inspecté, fallback 2D.
Les références proposées restent à confirmer dans Revit 2025.4 :
une géométrie renvoyée par l'API ne garantit pas à elle seule que
`NewDimension` acceptera la référence. Les cotes appuyées sur un
garde-corps peuvent devenir masquées lorsque celui-ci est masqué.

**Règle préventive :** avant d'accepter une référence non associative
sur une annexe, rechercher les véritables ouvrages construits
(corps de mur / arête de dalle / garde-corps) lorsqu'ils correspondent
géométriquement à la limite de la pièce. Ne jamais interpréter le seul
libellé « garde-corps » comme preuve qu'une face constitue la limite
réglementaire de surface annexe : l'arrêté du 9 mai 1995 modifié
inclut les loggias dans les surfaces annexes mais ne précise pas un
nu de garde-corps universel. SHAB exclut les loggias
(article R.156-1 CCH). Pour un mesurage jusqu'au nu intérieur,
la définition de limite doit être vérifiée dans les pièces du projet.

**Anti-régression :** `tests/annotations/test_guardrail_reference_policy.py`
(refus garde-corps éloigné ou oblique, priorité à l'arête fiable et
budget), `tests/annotations/test_annotation_runtime_mocks.py`
(référence de dalle inchangée, transformation d'une séparation en
arête de garde-corps, fallback sinon) et suites CI d'Annotations,
Plans de vente, Export et Calculs. À recetter dans Revit sur une
copie : loggia 2238, référence native garde-corps lorsque disponible,
cotes visibles après masquage des séparations mais garde-corps visible,
second lancement sans doublons, journal de diagnostic.
