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


---

### BUG-COMMON-013 — Trop de garde-corps près de la Room 2238 : fallback 2D systématique

**Symptôme de la recette Revit (22/10/2026) :** la loggia 2238 est cotée
3,12 m et 3,62 m sans crash, mais le rapport indique :
`plus de deux garde-corps proches ; recherche native ignoree par securite`
suivi de `reperes 2D utilises a la place des separations de piece`.
Le filtre n'a donc même pas tenté les références natives du garde-corps
susceptible de délimiter la loggia.

**Cause racine :** `_nearby_guardrail_edges` comptait les garde-corps
dont la **bbox intersectait toute la pièce** (marge 150 mm) et annulait
la recherche dès le troisième. Ce filtre large peut inclure des
garde-corps de loggias voisines ou de côtés différents, sans indiquer
s'ils suivent réellement **les deux limites à coter**.

**Correction :** faire une présélection légère de garde-corps visibles
par bbox, puis appeler `Railing.GetPath()` (API Revit 2025.4) et
comparer leurs segments en XY **aux seules séparations retenues dans
les deux dimensions principales**. Critères de présélection souples :
tolérance de 500 mm autour de la limite, angle maximum 12°, overlap
minimum 30 %. Jusqu'à 2 garde-corps réellement proches de ces
limites passent ensuite à la recherche géométrique native, inchangée
(écart maximum de 20 mm / angle 3° / recouvrement 60 %).
Le **chemin de garde-corps n'est jamais utilisé comme référence de
cote** ; seules les `Edge.Reference` du solide Revit sont candidates.

**Règles de sécurité :** maximum 24 garde-corps au filtre bbox, 80
segments de chemin et 2 garde-corps retenus ; ensuite maximum 120
arêtes examinées. Chemin indisponible, limite ambiguë ou budget
dépassé => aucun nouveau parcours de solides, fallback 2D
non associatif inchangé. Mode diagnostic une vue / une pièce maintenu.

**Règle préventive :** distinguer les objets dans l'emprise d'une
pièce et les objets réellement **colinéaires à la limite mesurée**.
Filtrer en plan avant d'extraire leurs solides et appliquer les
budgets géométriques au nombre d'objets **examinés**. Ne jamais
substituer la référence native par une courbe de chemin non
côtable. Une sortie de test où le fallback est déclenché doit
identifier si c'est par ambiguïté ou absence d'arête exploitable.

**Anti-régression :** `tests/annotations/test_guardrail_reference_policy.py`
(4 objets dans la bbox, 1 chemin pertinent ; 2 pertinents ;
3 réellement pertinents => fallback ; angles et proximité
rejetés ; budget chemin), doubles
`test_annotation_runtime_mocks.py`, workflows Annotations, Plans de
vente, Export et Calculs. Recette native à refaire pour la pièce
2238 sur copie en confirmant le rapport et la visibilité des cotes
après masquage des séparations. **Non validé dans Revit après correction.**


---

### BUG-COMMON-014 — 120 aretes de garde-corps examinees avant la reference utile

**Symptome :** cotation 2238 : deux garde-corps retenus par leur chemin, puis budget de 120 aretes atteint et repli 2D.

**Cause :** la geometrie complete du garde-corps comprend des composants repetitifs, notamment des poteaux et barreaux, qui consomment la limite d'analyse avant les rails filants.

**Correction :** utiliser les elements natifs TopRail et GetHandRails uniquement, et leurs solides directs avec references Revit originales. Ne pas inspecter les solides de l'element Railing parent. Conserver la limite de 120 aretes et le repli 2D lorsqu'aucune reference fiable n'est disponible.

**Prevention :** reduire les objets analyses plutot qu'augmenter le budget d'API Revit apres un crash ; ne pas utiliser les references issues de GetInstanceGeometry pour creer des cotes.

**Test anti-regression :** test_2238_quatre_gc_dans_bbox_un_seul_garde_corps_sonde controle que seule la geometrie du TopRail est interrogee ; suites CI et validation dans Revit 2025.4.


---

### BUG-COMMON-015 — Rail filant trouve, mais aucune arete examinee sur la loggia 2238

**Symptome observe dans Revit (22/10/2026) :** deux annotations creees ; deux garde-corps retenus par leur chemin ; un rail filant trouve, puis `0 aretes inspectees, 0 references candidates`. Les cotes utilisent encore des reperes 2D.

**Cause technique du blocage (code) :** la recherche ne parcourait que les objets `DB.Solid` directement retournes par `get_Geometry()`. Tout objet `DB.GeometryInstance` etait ignore. La sortie `0 aretes` est compatible avec une geometrie encapsulee, mais la structure reelle du rail 2238 n'est pas encore confirmee par un diagnostic Revit.

**Correction :** traiter les `GeometryInstance` des seuls TopRail/HandRail retenus via `GetSymbolGeometry()` **sans transformation** pour preserver les references de geometrie originales. Appliquer `GeometryInstance.Transform.OfPoint` aux seuls points de comparaison dans la maquette, sans substituer les References. Profondeur maximale de deux instances, 64 objets geometriques par rail et 120 aretes examinees au total ; option de detail Medium. Ne jamais employer `GetInstanceGeometry()` ou `GetSymbolGeometry(Transform)` pour les references de cotation, puisque ces surcharges retournent des copies.

**Prevention :** verifier les niveaux de geometrie Revit (Solid direct / GeometryInstance) avant de conclure a l'absence d'aretes. Pour une cote Revit, conserver les references issues de la geometrie originale ; faire les transformations sur des points de calcul uniquement. Limiter l'exploration et conserver le fallback non associatif en cas d'incertitude.

**Tests anti-regression :** `test_symbole_rail_geometrie_native_transformee_et_reference_preservee`, `test_symboles_imbriques_appliquent_transformations_dans_bon_ordre`, `test_budget_objets_et_profondeur_limites_avant_extraction_lourde`, plus les suites Annotations, Plans de vente, Export et Calculs. La validation native de Revit 2025.4 reste obligatoire et doit confirmer les geometries symboliques et l'acceptation des references de cote.


---

### BUG-COMMON-016 — Une loggia décotée de 35 mm par rapport au garde-corps retombe en 2D

**Symptôme et exemple :** sur la loggia 2238 du niveau 1, quatre arêtes
natives de rail filant sont désormais détectées, mais aucune n'est
associée aux cotes. L'utilisateur signale une différence réelle de
**35 mm entre la séparation de pièce et le garde-corps**, liée à une
approximation de modélisation. Le test strict historique rejetait toute
arête distante de plus de 20 mm. Le fait que les quatre arêtes soient
rejetées pour cette raison précise reste à confirmer avec le nouveau
diagnostic par arête.

**Cause racine démontrée par le code :** le seuil fixe
`FLOOR_EDGE_TOLERANCE_MM = 20` était aussi appliqué aux garde-corps
des annexes extérieures, sans tolérance distincte pour la divergence
entre la Room et un ouvrage réellement construit. De plus, les
arêtes de dalle étaient essayées avant les garde-corps dans le
fallback des séparations, alors que la règle métier demandée pour
les annexes est **mur → garde-corps → 2D**.

**Correction (bêta Cotation automatique uniquement) :**
- reconnaître les loggias, balcons, terrasses et jardins par
  `ROOM_NAME`, ou la valeur `Ext` du paramètre projet `Int/Ext` ;
- sur ces espaces uniquement, ignorer les arêtes de dalle comme
  substitution des limites extérieures : garder les faces finies des
  murs en priorité, les arêtes natives de garde-corps ensuite, puis
  les repères 2D non associatifs en dernier recours ;
- autoriser un **rattrapage maximal de 50 mm** pour l'appariement du
  garde-corps à une séparation, sous réserve que l'angle reste <=3°
  et le recouvrement >=60 %. Pour les pièces intérieures, rester à
  **20 mm** ;
- quand une référence est sélectionnée, indiquer dans le rapport
  l'écart effectivement mesuré ; au-delà de 20 mm, imposer une
  vérification manuelle du nu réel et de la **valeur native Revit**.
  Ne jamais remplacer la valeur vraie de la cote par la valeur
  calculée à partir de la séparation décalée ;
- quand aucun candidat n'est retenu, rapporter l'écart, l'angle,
  le recouvrement et les motifs du rejet à partir des références
  déjà examinées, sans parcours géométrique supplémentaire.

**Règle préventive :** distinguer tolérance de correspondance entre
géométries et valeur de la cote réelle. Un rattrapage de modélisation
ne doit pas modifier artificiellement une cote et ne doit jamais
s'étendre aux pièces intérieures ou à des ouvrages éloignés ;
ne pas relâcher les contraintes d'orientation/recouvrement.

**Tests anti-régression :** `test_tolérance_extérieure_rattrape_35mm_sans_relacher_les_angles`,
`test_decalage_de_65mm_reste_interdit_sur_annexe`,
`test_loggia_2238_ne_parcourt_pas_les_dalles_avant_garde_corps`,
`test_loggia_2238_garde_corps_ecarte_35mm_devient_reference_native`,
`test_interieur_garde_corps_ecarte_35mm_ne_remplace_pas_separation`.
Les suites Annotations, Plans de vente, Export et Calculs doivent
rester au vert ; **la référence Revit native et les nouvelles valeurs
réelles n'ont pas encore été vérifiées dans Revit 2025.4**.


---

### BUG-COMMON-017 — Le filtrage de garde-corps revient en 2D après passage aux annexes sans dalle

**Symptôme dans Revit 2025.4 :** loggia 2238, deux cotes créées, mais le
rapport indique `aucun garde-corps avec chemin suffisamment proche des
limites a coter (ou recherche ambigue)`, suivi du fallback 2D. Une
cote manuelle utilisateur montre environ **0,04 m** de décalage entre la
séparation de pièce et l'ouvrage. Le précédent lancement avait trouvé
deux garde-corps proches, douze arêtes et quatre références natives
candidates. L'ancien message ne permettait pas de distinguer manque
de correspondance, ambiguïté ou dépassement du budget.

**Cause racine du filtrage, démontrée par le code :** la sélection
`select_guardrails_by_path` annulait **toute** la recherche dès que
plus de deux garde-corps avaient un chemin colinéaire à **n'importe
laquelle** des séparations candidates. La nouvelle règle de priorité
des annexes (mur / garde-corps / 2D) examine davantage de séparations
qu'avant ; elle peut donc accroître les correspondances et provoquer
un abandon même lorsqu'un garde-corps clairement meilleur suit une
limite donnée. La raison exacte observée sur 2238 sera confirmée
par les compteurs du prochain rapport.

**Correction bêta :** sélectionner au plus **un garde-corps par
limite de cotation**, classé par le score géométrique du moteur PDV,
sans dépasser **deux garde-corps** à extraire au total. Si deux
garde-corps ont des scores quasi identiques (écart de score <=25 mm),
rejeter **cette limite** comme ambiguë plutôt que de choisir un nu
arbitraire. L'autre limite, si non ambiguë, peut encore être étudiée ;
celle rejetée garde son fallback 2D. Conserver la marge de
présélection sur chemins de 500 mm sans l'employer comme
tolérance des **arêtes natives**, limitée à 50 mm sur annexe.
Les budgets 24 garde-corps bbox / 80 segments de chemin / 2 garde-corps
retenus / 120 arêtes restent identiques.

**Diagnostic :** afficher dans le rapport le nombre de chemins
explorés, de limites, de correspondances, de limites ambiguës,
l'écart du chemin le plus proche et le statut distinct
`selected`, `no_match`, `ambiguous`, `path_budget`,
`rail_budget` ou `partial_ambiguity`. Ne parcourir aucun
solide de plus pour émettre ces métriques.

**Règle préventive :** ne jamais imposer un plafond global de
candidats avant de les classer **par cible**. Distinguer la
présélection des ouvrages de la validation des arêtes et donner
un motif de refus explicite, plutôt qu'un avertissement ambigu.

**Tests anti-régression :** `test_trois_garde_corps_proches_mais_un_seul_nu_clairement_meilleur`,
`test_ex_aquo_sur_la_meme_limite_est_refuse_avec_diagnostic`,
`test_deux_limites_et_plus_de_deux_gc_seuls_les_meilleurs_sont_examines`,
`test_garde_corps_une_limite_ambigue_autre_claire_autorisee` et les
suites CI Annotations, PDV, Export, Calculs. Validation sur une
copie de maquette Revit 2025.4, pièce 2238, impérative avant levée
du mode diagnostic.


---

### BUG-COMMON-018 — Une limite d'annexe est partagée entre deux garde-corps d'environ 50 %

**Retour réel Revit (loggia 2238, 22/10/2026) :** le diagnostic retrouve
deux garde-corps, 24 arêtes et 8 références natives. Une limite
accepte une arête à 100 % de couverture. Pour l'autre, la meilleure
arête couvre **52 %**, décalée de **15 mm** et parfaitement parallèle,
mais échouait au seuil de **60 %**. La capture utilisateur confirme
deux garde-corps **successifs**, chacun occupant à peu près la moitié
de cette limite. Le moteur jugeait à tort chaque garde-corps
séparément, comme s'il devait couvrir toute la longueur.

**Cause racine :** `select_guardrail_edge` calculait uniquement
`overlap_ratio` de **chaque arête individuelle**. Un garde-corps
parfaitement valide de 52 % était donc rejeté, sans rechercher le
second ouvrage qui complète la limite. Un simple abaissement du
seuil à 50 % pour toute annexe aurait permis de choisir un rail
isolé non représentatif de la limite.

**Correction bêta Annotations :**
- Conserver **60 %** de recouvrement pour accepter une arête seule,
  y compris à l'extérieur.
- Lorsqu'aucune arête seule n'atteint ce seuil sur une annexe,
  comparer **deux arêtes natives de garde-corps distincts** (pas
  deux lignes du même élément) et vérifier :
  projection sur la limite ; angle <=3° ; écart de chaque arête
  <=50 mm ; chaque portion couvre >=25 % ; couverture **cumulée
  continue >=90 %** ; vide éventuel <=100 mm ; superposition
  mutuelle <=10 % ; décalage latéral mutuel <=20 mm ; différence
  d'altitude <=150 mm. Tous les seuils restent à valider sur
  maquette, sans augmenter le budget des solides Revit.
- Si cette continuité est avérée, conserver comme référence de cote
  **une vraie `Edge.Reference` Revit** (celle de l'une des deux
  arêtes, la plus longue). La deuxième référence sert à
  **confirmer la continuité**, mais n'est **pas associative** à la
  cote ; tout changement de l'un ou l'autre garde-corps appelle un
  contrôle manuel. Si les deux portions ne se complètent pas,
  conserver le fallback 2D.
- Signaler dans le rapport couverture cumulée, jeu, décalage entre
  ouvrages et limite de l'associativité.

**Règle préventive :** distinguer couverture d'une arête individuelle
et **union de deux tronçons construits**. Ne jamais affaiblir
globalement un seuil de sécurité à partir d'un cas composé.
Ne pas fabriquer de référence virtuelle ou de cote de longueur
à partir de la somme des rails : seule une référence native
réellement admissible est transmise à Revit.

**Anti-régression :** tests de la politique pure (52 %+48 % qui se
raccordent ; portion isolée rejetée ; deux éléments identiques ou
superposés rejetés ; trou de 150 mm, décalage de 30 mm, couverture
incomplète ou altitude différente rejetés) et tests doubles du
service de référence Revit. Suites Annotations, PDV, Export et
Calculs à contrôler. Recette impérative dans Revit 2025.4,
sur copie de la loggia 2238 ; aucun comportement natif n'est
présumé validé par ces tests hors Revit.


---

### BUG-COMMON-019 — Deux cotes natives, quatre messages identiques sur la pièce 2240

**Symptôme observé dans Revit 2025.4 (retour utilisateur) :**
lancement de Cotation automatique sur **2240**, niveau 1, avec
**2 annotations créées**, sans repli de détail 2D. Deux arêtes de
garde-corps admissibles sont diagnostiquées :
**0,0 mm / 100 %** et **19,3 mm / 63 %**. Pourtant chacune des
deux lignes d'avertissement est répétée **deux fois**.
La répétition du diagnostic ne prouve pas la présence de quatre
dimensions. La vérification de l'absence de cotation préexistante
superposée reste un contrôle visuel distinct.

**Cause racine confirmée par lecture du code :**
`AnnotationService._create_separator_proxies` lance
`GenericDimensions._room_boundary_candidates` pour préparer
les références, puis `DimensionService.create_dimensions` rappelle
ce service. L'adaptateur renseignait `proxy_candidates` **seulement
si une séparation nécessitait la création d'un repère 2D**.
Pour 2240, dont les références sont toutes natives, aucun repère
n'était créé, le cache restait vide et la résolution des garde-corps
était exécutée deux fois. Les messages sont ajoutés à chaque
résolution. Cette double exécution n'est pas nécessaire et rallonge
les appels API Revit, même lorsque l'extraction des arêtes est cachée.

**Correction limitée à la bêta :** mémoriser la liste de candidats
et ses références natives dans `proxy_candidates[room.UniqueId]`
**dans tous les cas**, qu'un repère 2D ait été créé ou non. Le moteur
de cotation consomme exactement ces références sans nouvelle
résolution. Le cache est limité à la TransactionGroup d'une pièce
et vidé dans `_run_unit.finally`. Aucun seuil de garde-corps, aucune
géométrie Revit, aucun service PDV et aucun mode multi-vues modifié.

**Règle préventive :** dès qu'un adaptateur calcule des références
Revit en pré-traitement, les transmettre au moteur suivant même
si aucun objet supplémentaire n'a été créé. Une décision de
mise en cache ne doit pas dépendre de la création d'un fallback
2D. Ne pas supprimer simplement les avertissements en doublon
sans corriger la double exécution.

**Tests anti-régression :**
`test_2240_cotes_natives_cachees_sans_doubler_diagnostics`
(aucune ligne 2D, références natives mémorisées, un seul
diagnostic par arête), `test_cache_references_vide_evite_une_nouvelle_recherche`
et tests existants de références 2D. Suite Annotations + PDV et
workflows transversaux à vérifier. **Dans Revit**, relancer 2240
sur copie après retrait des cotes du précédent essai, contrôler
deux cotes seulement et deux lignes de référence native seulement.


---

### BUG-COMMON-020 — Plusieurs garde-corps : choix non conforme à proximité puis longueur

**Règle métier explicite (3 novembre 2026) :** lorsqu'une limite de
loggia, terrasse, balcon ou jardin longe plusieurs garde-corps,
la **référence admissible la plus proche de cette limite** est
prioritaire. Si les distances sont identiques ou quasi équivalentes
(écart <=1 mm pour absorber les approximations numériques Revit),
prendre **le garde-corps / la référence la plus longue**.

**Cause racine :** la présélection des garde-corps se fondait sur
`segment_match_metrics.score` (score combiné distance et recouvrement)
et rejetait les candidats dont les scores étaient proches à moins
de 25 mm comme « ambigus ». La sélection native utilisait également
ce score mixte. Dans un cas à plusieurs ouvrages, un garde-corps
plus long mais plus éloigné pouvait l'emporter sur le plus proche
ou bloquer complètement la sélection.

**Correction bêta :** introduire une comparaison unique
distance minimale, puis longueur à distance égale. L'égalité
fonctionnelle est fixée à **1 mm** dans l'adaptateur Revit,
et évaluée par rapport à la distance minimale globale (pas
de chaînage cumulatif de petites tolérances). Appliquer la
même règle à (1) la présélection des chemins `Railing.GetPath`,
(2) la sélection d'une `Edge.Reference` native et (3) la
désignation de la référence parmi deux garde-corps dont la
continuité est préalablement validée. Une égalité de distance
n'entraîne plus à elle seule un fallback 2D.

**Limites de sécurité :** cette règle ne dispense jamais des critères
préalables d'admissibilité (proximité maximale 50 mm pour une annexe,
angle <=3°, recouvrement individuel >=60% ou paire contiguë couvrant
>=90%, existence de vraie référence native). Le second garde-corps
d'une paire contiguë ne devient pas associatif à la cote, puisqu'une
seule arête native est référencée. Aucun plafond d'inspection de
géométrie n'est relevé. Le mode diagnostic une seule pièce reste actif.

**Règle préventive :** ne pas employer un score composite ou un
rejet d'égalité arbitraire lorsque l'utilisateur a défini une
hiérarchie de comparaison explicite. Le meilleur candidat est
sélectionné *après* les contrôles d'admissibilité et selon une
distance mesurée dans la même unité pour tous les ouvrages.

**Tests anti-régression :** nouvelles variantes de
`test_reference_native_plus_proche_devant_une_arete_plus_longue`,
`test_reference_native_meme_distance_choisit_plus_longue`,
`test_reference_native_egalite_un_millimetre_choisit_plus_longue`,
`test_reference_egale_distance_en_chaine_ne_change_pas_distance_de_base`,
`test_deux_gc_contigus_reference_le_plus_proche_meme_si_plus_court`
et tests de présélection par chemin sur trois garde-corps et deux
limites. Les suites CI doivent réussir. **Validation native Revit
2025.4 toujours requise**, particulièrement sur 2238.


**Préservation des limites composées (2238) :** la présélection reste
au plus un garde-corps prioritaire par limite selon proximité puis
longueur. Si ce garde-corps seul couvre moins de 60 %, un **second
garde-corps distinct** peut être ajouté exceptionnellement au
parcours natif **uniquement si leurs chemins démontrent une
continuité** (couverture cumulée >=90 %, raccord <=100 mm,
écart latéral mutuel <=20 mm). Cette preuve par chemins ne
constitue jamais une référence de cote : les `Edge.Reference`
restent contrôlées par le moteur natif. Pour couvrir deux
directions dont une composée, le budget de garde-corps examinés
passe de **2 à 3 maximum**, en conservant le plafond total
inchangé de **120 arêtes examinées**. Si plus de trois rails
sont requis, fallback 2D au lieu d'augmenter l'exploration.
Tests : `test_loggia_2238_une_limite_complete_et_deux_rails_suivants`,
`test_ne_pas_chercher_second_rail_si_pas_de_continuite`,
`test_complement_de_rail_refuse_si_decales_30mm`,
`test_companion_ne_fait_pas_depassement_silencieux_du_budget`.


---

### BUG-COMMON-021 — 2238 : second tronçon éliminé avant contrôle des arêtes natives

**Symptôme (retour Revit 2025.4) :** sur 2238, rapport de
`3 chemin(s), 2 limite(s), 3 correspondance(s)`, mais
`0 second(s) tronçon(s) complémentaire(s)`. Seulement **2 garde-corps**
sont inspectés (24 arêtes, 8 références natives candidates). Une cote
est native (recouvrement 100 %) et l'autre retombe en 2D car
l'arête restante couvre **52 %** de sa limite.

**Cause racine dans le code :** le préfiltre
`select_guardrails_by_path` ne cherchait un second garde-corps
que si le **chemin GetPath du premier** couvrait moins de 60 %.
Or la longueur de ce chemin n'est pas nécessairement celle de
l'arête TopRail effectivement utilisable pour la cote.
Un chemin de 100 % peut correspondre à une arête native de 52 %.
Le second ouvrage est alors exclu avant l'analyse des références
natives ; le test sur la paire ne peut pas s'exécuter.
La structure géométrique exacte du troisième garde-corps de
2238 reste à confirmer au prochain test Revit.

**Correction :** conserver la sélection prioritaire du garde-corps
le plus proche (puis plus long à égalité), et garder en supplément
le candidat distinct suivant lorsqu'il existe pour une limite,
sans considérer son chemin comme preuve de contiguïté.
L'extraction native reste bornée à **3 garde-corps au total** et
**120 arêtes au total**. La vérification stricte de la continuité,
du décalage, du raccord et de la couverture >=90 % est effectuée
**uniquement sur les Edge.Reference natives**. Au-delà du budget,
conserver le fallback 2D et ne pas choisir arbitrairement un
sous-ensemble de quatre garde-corps.
Le rapport précise que le deuxième tronçon est **à vérifier**
sur les arêtes et n'est pas déjà validé.

**Prévention :** ne jamais transformer un critère de géométrie de
présélection (Railing.GetPath) en décision définitive sur la longueur
de l'arête native. Différencier candidat retenu pour inspection et
continuité attestée par des arêtes cotables.

**Anti-régression :** `test_loggia_2238_chemin_entier_arrete_native_demie_garde_second_gc`,
`test_candidat_supplémentaire_seul_ne_suffit_pas_a_coter`,
`test_companion_ne_fait_pas_depassement_silencieux_du_budget`,
plus les tests précédents de deux tronçons jointifs et les suites
CI Annotations, Plans de vente, Export et Calculs. **Test natif
dans Revit 2025.4 obligatoire** : deuxième tronçon réellement
sélectionné puis preuve de continuité native, ou fallback documenté.


---

### BUG-COMMON-022 — Trois garde-corps présélectionnés, mais seulement deux rails filants inspectés (2238)

**Symptôme Revit 2025.4 (3 novembre 2026) :** 2238, deux cotes
créées ; `3 garde-corps retenu(s) par leur chemin` mais seulement
`2 rail(s) filant(s), 24 arêtes inspectées, 8 références candidates`.
La première cote utilise une arête native (100 %), la deuxième
retombe en 2D car la meilleure référence atteint 52 % de
recouvrement. Le nouveau préfiltre BUG-COMMON-021 fonctionne,
mais n'offre aucune arête supplémentaire exploitable.

**Cause racine dans le code :** l'extraction native n'utilisait
que `Railing.TopRail` et `Railing.GetHandRails()`. Le troisième
garde-corps est présélectionné, mais n'est pas identifié dans le
diagnostic par son ElementId et ne fournit aucun élément filant
supplémentaire. Sa configuration Revit reste inconnue sans
diagnostic : absence de TopRail, HandRail non résolu, rail dupliqué,
ou type contenant une `RailStructure` non continue.
La documentation API Autodesk distingue les composants continus
directement accessibles du `Railing` et les lisses non continues
définies dans `RailingType.RailStructure`.

**Correction :** journaliser pour chacun des 3 garde-corps
sélectionnés son **ElementId**, l'ElementId de TopRail ou son
absence, le nombre de HandRail accessibles, et si aucun composant
continu n'est résolu, le nombre de lisses non continues de son
`RailingType.RailStructure.GetNonContinuousRailCount()`.
En l'absence de composant filant, sonder uniquement **un** parent
Railing dont le type déclare une lisse non continue. Cette recherche
utilise les solides natifs **directs** uniquement, ne traverse pas
les `GeometryInstance` de balustres, borne à **16 objets**, **48
arêtes** et **12 références** ; elle n'emploie que
`Edge.Reference` et exige que le segment soit assez proche
et parallèle à une séparation de la pièce. Si l'API échoue,
si plusieurs parents sont concernés ou si le budget est dépassé,
abandonner ses arêtes et garder le fallback 2D, sans supprimer
les arêtes natives déjà trouvées sur les rails filants.
Le budget global de 120 arêtes demeure inchangé et le mode
diagnostic reste limité à une pièce.

**Règle préventive :** distinguer le nombre de garde-corps
sélectionnés du nombre de composants géométriques réellement
accessibles. Ne pas supposer que tout Railing possède un TopRail
ou un HandRail. Éviter un nouveau parcours global non borné
des solides et balustres après un crash Revit antérieur.
Ne pas revendiquer une référence native lorsque le composant
Revit n'en fournit pas réellement.

**Tests anti-régression :**
`test_2238_trois_garde_corps_deux_toprails_et_une_lisse_non_continue`
(une limite composée dont le troisième rail n'a pas TopRail),
`test_noncontinuous_parent_geometry_budget_et_sans_instance`
(échec sûr lorsque 49 arêtes dépassent un plafond de 48, sans
traverser la GeometryInstance), suites Annotations/Plans de vente,
Export et Calculs. **Aucun test Revit de ce correctif à ce stade** :
l'acceptation d'une arête native de lisse non continue dans
une cote Revit 2025.4 reste à contrôler sur copie.


---

### BUG-COMMON-023 — 2238 : garde-corps successifs, un seul TopRail à référence native

**Observation et besoin (3 novembre 2026) :** pour la loggia 2238,
trois garde-corps sont identifiés par leurs chemins, mais seuls deux
rails filants livrent des références natives. Une limite obtient
une arête native sur 100 % ; sur l'autre, l'arête native la plus
proche couvre 52 % et un deuxième garde-corps constitue le reste
du bord. L'ancien algorithme exigeait soit une arête de >=60 %, soit
deux **arêtes** natives jointives, donc tombait systématiquement
sur un repère 2D même lorsqu'un seul rail pouvait fournir une vraie
référence de cote.

**Cause racine :** confusion entre (a) la preuve de la continuité
constructive de la limite et (b) l'élément API nécessaire pour
coter. La continuité peut être vérifiée sur deux chemins
`Railing.GetPath()`, alors que **une seule** arête native
`Edge.Reference` est disponible. La lecture de la géométrie du
garde-corps parent était utilisée comme tentative de récupération
du second rail, malgré le risque de parcours des balustres.
Par ailleurs, l'ID d'un TopRail peut être un `ElementId` .NET
alors que les données des tests sont des entiers : toute table
de correspondance doit normaliser les clés avant comparaison.

**Correction bêta :** pour les **annexes extérieures uniquement**,
après recherche standard d'arête native individuelle >=60 % puis
vérification de deux arêtes natives, autoriser une preuve alternative
fondée sur **deux chemins de garde-corps distincts** situés sur
la même limite :
- **union des projections >=90 %** de la limite, sans additionner
  deux fois les parties superposées ;
- chaque portion >=25 %, angle <=3°, intervalle de jonction
  <=100 mm, décalage latéral entre chemins <=20 mm ;
- refus si l'un des chemins couvre déjà toute la limite alors que
  l'autre ne fait que se superposer ;
- **une vraie référence native** (TopRail / HandRail) provenant
  de **l'un des deux garde-corps**, dont l'arête est proche
  (<=50 mm), suffisamment parallèle (<=3°), couvre >=25 %
  de la limite et correspond à sa portion de chemin ;
- choix de la référence admissible la plus proche de la limite,
  puis de la plus longue à distance équivalente de 1 mm.

**Sécurité / associativité :** le chemin sert **uniquement à prouver
la couverture**, jamais à construire la référence d'une cote. La
cote Revit est associative à **une seule arête native**, pas au
deuxième garde-corps dont le chemin a validé la continuité.
Le module avertit de cette limite et impose le contrôle du nu réel
après modification de l'un ou l'autre ouvrage. Si la couverture
des deux chemins n'est pas fiable, s'ils ne sont pas contigus,
ou si aucune arête native admissible ne correspond à leur ouvrage,
repli 2D inchangé. Pas de balayage des solides du garde-corps
parent pour les annexes extérieures ; conserver le diagnostic
type/ID pour comprendre les configurations. Nombre d'ouvrages
inspectés et budgets des solides filants inchangés, mode
diagnostic sur une pièce maintenu. Plans de vente stable inchangé.

**Prévention :** séparer la **preuve de couverture** (chemins
physiques) de la **Reference API cotable** ; ne pas supposer
deux références natives nécessaires lorsqu'un ouvrage unique
suffit pour poser la cote, mais ne jamais utiliser la longueur
des chemins pour falsifier sa valeur. Normaliser les ElementId
entre IronPython / .NET et les tests Python.

**Anti-régression :** tests de deux chemins 52 % + 48 % avec une
seule arête native, superposition, couverture insuffisante, trou
de 150 mm, référence d'un garde-corps étranger, arête à >50 mm,
priorité à la plus proche, et simulation du moteur pour 2238
avec zéro lecture de géométrie parent. Exécuter les tests
Annotations + PDV, Export, Calculs, puis recetter réellement
sur une copie dans Revit 2025.4. **La référence native obtenue
par ce fallback n'a pas encore été validée dans Revit.**


---

### BUG-COMMON-024 — 2238 : refus de continuité indiagnostiquable malgré BUG-COMMON-023

**Retour Revit du 3 novembre 2026 (après correctif 023) :** le module détecte
3 garde-corps et 2 limites de la loggia 2238. Il trouve 2 TopRail et 8
références candidates sur 24 arêtes, accepte une arête native couvrant 100 %
de la première limite, mais refuse la meilleure arête de la seconde limite
(52 % de recouvrement, 15 mm de distance). Il produit toujours des repères 2D.
Le nouveau fallback par union de deux chemins n'affiche **aucune raison** de
son échec. Ce retour **invalide la réussite supposée** du correctif 023 sur
cette maquette ; le vrai motif géométrique reste à vérifier.

**Cause racine du défaut de diagnostic :** dans
`_upgrade_separator_guardrail`, l'appel à
`select_native_edge_with_path_continuity` retournait seulement une référence
native ou `None`. Le rapport n'exposait ensuite que les raisons du rejet
d'une **arête individuelle** (<60 %) et masquait les raisons du rejet de
la **preuve de continuité par chemins** (superposition, couverture <90 %,
jonction >100 mm, décalage >20 mm, mauvais angle, etc.).

**Correction sûre :** ajouter un analyseur géométrique **pur et non intrusif**
`diagnose_guardrail_path_continuity`, exécuté seulement pour une limite
extérieure dont les références natives et la preuve de continuité ont déjà
échoué. Il réutilise les chemins `GetPath` déjà en mémoire, sans lire de
géométrie Revit supplémentaire. Le rapport donne, pour la meilleure paire,
les deux IDs de garde-corps, les deux intervalles projetés sur la limite,
la couverture **par union**, la superposition réelle, le jeu, les écarts
latéraux et les causes de rejet. Si la paire géométrique était compatible,
le rapport indique plutôt l'absence de référence native associable.
Ce rapport ne remplace **jamais** la décision du moteur de cotation.

**Prudence :** une couverture de 100 % obtenue avec un chemin complet et un
deuxième chemin qui chevauche sa moitié ne prouve pas deux tronçons successifs.
Ne pas corriger ce cas en abaissant le seuil de 60 %, en additionnant deux fois
les parties superposées, ou en fabriquant une `Reference` à partir de
`GetPath`. La seconde cote demeure non associative tant qu'une preuve
géométrique fiable et une référence native Revit ne sont pas réunies.

**Anti-régression :** tests Python de la géométrie 52 % + 48 % réellement
successive, chemin complet + demi-chemin superposé (rejet malgré 100 %
d'union), deux portions superposées, trou de 150 mm, budget de garde-corps,
invariance du choix de référence, et contrat de rapport. Exécuter suites
Annotations/Plans de vente. **Recette Revit sur copie** : relancer 2238
après suppression des anciennes cotes, relever la nouvelle ligne
`diagnostic continuité GC`, puis vérifier 2240 en non-régression.
N'autoriser la cotation en masse qu'après validation de l'associativité et
du nu réel, sans crash.


---

### BUG-COMMON-025 — Loggia 2238 : chemins GC 100 % jointifs mais axes décalés de 33 mm

**Retour réel après BUG-COMMON-024 (3 novembre 2026) :**
la pièce 2238, dans `Collectifs A_Niveau 1`, produit deux annotations
mais toujours un repli 2D sur la seconde limite. Le nouveau diagnostic
sépare les garde-corps **8951804** et **16141871** :
- chemin 8951804 : **52–100 %** ; chemin 16141871 : **0–52 %** ;
- union **100 %**, superposition **0 %**, raccord **0 mm** ;
- écart entre axes `Railing.GetPath()` **33 mm** (limite standard **20 mm**) ;
- axe le plus éloigné de la limite de pièce : **58 mm** ;
- arête native du TopRail : **0 mm** de la limite et **52 %** de couverture.

**Cause précise du refus :** `decalage_lateral` uniquement. Le
traitement standard confondait ici l'alignement des **axes d'implantation**
des deux garde-corps avec une preuve du nu fini commun. Or les
`GetPath()` dépendent des réglages d'implantation des garde-corps :
leurs axes peuvent être décalés même lorsque le début et la fin des
ouvrages coïncident longitudinalement. **Ce retour seul ne prouve pas
que les nus physiques sont alignés.**

**Correction expérimentale sur la branche bêta uniquement :**
avant le dernier repli 2D et uniquement pour une annexe extérieure,
`select_native_edge_with_path_axis_offset_recovery` peut accepter
une arête native d'un des deux garde-corps si toutes les protections
suivantes sont simultanément satisfaites :

1. Deux chemins distincts, du **même côté** de la séparation de pièce.
2. Couverture longitudinale >=**98 %**, superposition <=**2 %**,
   jeu <=**10 mm**, avec angle <=**3°**.
3. Différence latérale entre axes : plus de 20 mm, mais <=**40 mm** ;
   chaque axe reste <=**60 mm** de la séparation.
4. Une **Edge.Reference Revit originale** issue d'un des deux
   garde-corps prouvant la continuité, avec écart <=**5 mm** de la
   séparation de pièce et recouvrement d'au moins **25 %**.
5. Correspondance vérifiée entre l'ID du TopRail/HandRail et son
   garde-corps parent, avec alignement de l'arête et de son chemin.

En l'absence d'une seule de ces conditions, le moteur laisse le repli
2D antérieur. Il n'assouplit pas le contrôle standard des arêtes natives
individuelles (>=60 %) ni les règles de Plans de vente. Aucun solide de
garde-corps parent sans TopRail n'est exploré, aucun budget n'est augmenté
(3 garde-corps, 80 chemins, 120 arêtes natives), et aucun `GetPath()`
n'est utilisé comme `Reference` Revit.

**Alerte impérative :** la cote créée reste **associative à UNE seule
arête native**, jamais aux deux garde-corps. Le recul des axes ne prouve
pas que le nu réel du garde-corps sans TopRail se trouve sur la même
ligne que celui de l'arête cotée. Le rapport émet
`RECUPERATION BETA du GC malgre axes decales` et impose un contrôle
manuel du **nu intérieur**, de la longueur affichée et de l'absence
de déplacement entre les deux ouvrages. Interdire une fusion dans
`main` avant cette validation Revit ; le résultat est une hypothèse
de récupération, pas une règle métier généralisée.

**Anti-régression hors Revit :** axes simulés de 25/58 mm (écart 33),
chemins 52 % + 48 %, reference native à 0 mm => récupération ;
déplacement des axes de 41 mm, axe >60 mm, référence à 6 mm,
superposition >2 %, raccord de 20 mm, axes de côtés opposés,
référence appartenant à un troisième garde-corps => refus.
Tester l'absence d'altération du traitement strict, puis valider
réellement dans Revit 2025.4 avant de lever le mode diagnostic
une pièce/une vue.


**Validation intermédiaire Revit du 3 novembre 2026 (après le correctif 025) :**
la pièce 2238 a créé deux annotations avec **deux messages de référence
native de garde-corps utilisée** : 100 % pour la première limite et
52 % pour la seconde. Le rapport contient `RECUPERATION BETA` pour
les chemins de GC décalés de **33 mm**, confirme l'union **100 %**,
la superposition **0 %** et une arête native à **0 mm**. Il ne contient
plus d'avertissement de repli par repères 2D. La cote partielle référence
**uniquement le garde-corps 16141871** et non le garde-corps complémentaire
8951804. **La récupération d'une Reference native est donc validée sur
cette configuration Revit réelle** ; la justesse des deux valeurs
affichées, l'alignement des nus intérieurs, la persistance sans séparations
et la non-régression sur 2240 restent **non vérifiés**. La fonctionnalité
ne doit pas être fusionnée dans `main` sans ces vérifications.


**Recette complémentaire utilisateur du 3 novembre 2026 : 2238 validée sur 4/4 contrôles.** Après la récupération native confirmée, l'utilisateur valide explicitement les valeurs des deux cotes, l'alignement des nus intérieurs des GC 16141871 et 8951804, la conservation des cotes avec les séparations de pièces masquées, ainsi que la seconde exécution sans doublon ni plantage. **BUG-COMMON-025 est donc validé fonctionnellement sur cette pièce de test Revit 2025.4.** Cette validation est limitée au cas 2238 ; la cote de la seconde limite demeure associative uniquement au GC 16141871 et la non-régression sur la pièce 2240 reste à effectuer avant toute généralisation ou fusion de la branche bêta dans `main`.


**Non-régression sur la pièce 2240 confirmée le 5 novembre 2026 :** 2 annotations dans `Collectifs A_Niveau 1`, 2 arêtes natives GC conservées (écart **0 mm**, recouvrement **100 %** ; écart **19,3 mm**, recouvrement **63 %**), sans `RECUPERATION BETA` ni repères 2D signalés. Contrôles utilisateur 5/5 : deux cotes créées, valeurs et nus corrects, références natives, visibilité des cotes après masquage des séparations et deuxième lancement sans doublon ni crash. L'écart de 19,3 mm désigne le décalage arête/limite de pièce, pas un écart constaté sur la dimension. **BUG-COMMON-025 validé sur 2238 et non-régression sur 2240 validée ; validation globale des autres cas toujours en attente.** Garder le module sur sa branche bêta et ne pas fusionner dans `main` à ce stade.


---

### BUG-COMMON-026 — Cotation appartement : seconde orientation omise dans les petites pièces

**Rapport utilisateur du 5 novembre 2026 — vue `Collectifs A_Niveau 1` :**
mode bêta un appartement, **12 pièces hors groupe** traitées,
**18 annotations créées** sur un maximum théorique de 24
(6 pièces avec une seule cote). Les pièces **2249, 2251,
2252, 2253 et 2256** indiquent explicitement
`orientation 2 ignoree`, avec 8 à 10 positions initiales mais
aucune combinaison compatible après le filtrage graphique.
Dans plusieurs cas **aucun texte entièrement intérieur** n'est
possible ; pourtant des positions partiellement extérieures sont
déjà autorisées. La pièce **2247** n'affiche pas d'orientation
rejetée et n'a produit qu'une cote : un seul axe de faces opposées
fiable est une hypothèse distincte à confirmer au prochain essai.
Le rapport ne démontre PAS que les six pièces possèdent toutes
deux références de faces opposées cotables.

**Différence avec le module Plans de vente :**
les deux modules utilisent la même génération de positions
`plans_vente.dimension_positioning.placement_candidates`
et les mêmes références physiques. Le moteur de Plans de vente
`select_placements` privilégie deux cotes mais accepte
des placements avec risques de collisions, signalés par avertissement.
L'adaptateur Annotations ajoute
`select_collision_free_placements`, qui refuse ces collisions,
et peut donc ne conserver qu'une cote. Revenir aveuglément à
`select_placements` sur une vue déjà annotée réintroduirait des
chevauchements de textes/étiquettes.

**Correctif bêta limité à Annotations :**
1. Accepter le **croisement ponctuel** de deux traits ou témoins
   lorsque leurs directions sont suffisamment transversales,
   comme le croisement normal des deux directions principales.
   Les parallèles et les superpositions restent interdits.
   **Toutes les collisions impliquant un texte sont refusées.**
2. Après échec du choix strict, rechercher au plus **4 positions
   supplémentaires par axe**, légèrement au-delà du contour
   de la pièce (marges bornées à une puis deux hauteurs de texte).
   La géométrie et les classes proviennent du même moteur
   `DimensionPlacement` de Plans de vente, sans toucher
   aux références de murs, sols ou garde-corps Revit.
3. Réévaluer la sélection stricte avec ces positions.
   Ne retenir le repli que si le **nombre de cotes sans collisions
   augmente** ; continuer à bloquer les étiquettes existantes
   et les textes de cotes, même en dehors de la pièce.
4. Indiquer `REPLI PETITE PIECE` et avertir d'un éventuel
   placement hors pièce, avec contrôle visuel de l'emprise
   dans l'appartement voisin/couloir. En cas de panne du nouveau
   repli, préserver les cotes réalisables par l'ancien placement.
5. Journaliser séparément une **absence de seconde direction
   géométrique** (nombre de paires de faces opposées fiables)
   afin de ne jamais créer une cote inventée sur un petit tronçon.

**Tests automatisés :** 460 tests Annotations + non-régression
Plans de vente réussis en CI sur la branche bêta au
5 novembre 2026. Le module Plans de vente et son moteur
de références n'ont pas été modifiés.

**Recette Revit en attente :** sur une **copie** de ce même
appartement, garder les 18 cotes déjà présentes et relancer
la cotation avec la branche à jour. Vérifier, pour 2249,
2251, 2252, 2253 et 2256, si des secondes cotes apparaissent
avec `placement complementaire petites pieces` ou
`REPLI PETITE PIECE`, leur **valeur**, leur **nu fini**,
leur **lisibilité hors pièce**, les **collisions réelles** et
l'absence de doublon. Pour 2247, relever le nouveau message
`seulement ... orientation(s) de faces opposees` et ne pas
fabriquer artificiellement un second axe.
Ne pas fusionner ce correctif dans `main` avant cette recette.


---

### BUG-COMMON-027 — Appartement 23/24 : deux cotes INTERIEURES, 2247 et recherche GC reservee aux limites non murales

**Retour utilisateur du 5 novembre 2026, apres BUG-COMMON-026 :**
vue `Collectifs A_Niveau 1`, 12 pieces, **23 cotations creees**
sur un objectif de 24. Les pieces 2249, 2251, 2252, 2253 et 2256
ont bien recupere leur seconde cote via `REPLI PETITE PIECE`, mais
certaines positions depassent le contour des petits locaux.
La piece **2247** ne produit toujours qu'une cote, sans message
de refus graphique de la seconde orientation.

**Exigence metier explicite :**
1. **Deux cotes par piece** des lors que Revit dispose de deux mesures
   physiques fiables. Les deux **lignes de cote et ancrages de texte
   doivent etre dans la piece**, meme dans un WC, cellier ou degagement.
2. Si le local est tres petit, les **superpositions de textes, etiquettes
   ou temoins sont acceptees** et signalees, plutot que deplacer les
   cotes hors de la piece ou supprimer la deuxieme.
3. **Ne rechercher de garde-corps que si une limite selectionnee n'est
   pas un mur Revit** et que la reference n'est pas deja satisfaisante.
   Ne pas sonder tous les garde-corps d'une vue pour un local 100 % murs.

**Correctifs sur `feature/annotations-automatiques-beta` :**
- Le nouveau `annotations/inside_dimension_positioning.py` choisit
  parmi les candidats `DimensionPlacement` d'origine Plans de vente
  **deux lignes qui passent a l'interieur** (sondes via
  `Room.IsPointInRoom`). Il choisit la combinaison avec deux cotes
  lorsqu'elle existe, puis minimise les collisions. Les risques de
  chevauchement sont affiches ; le texte peut deborder de son enveloppe
  pour une piece trop petite, mais son point d'ancrage reste a
  l'interieur. Aucun repli vers l'exterieur n'est utilise.
- Pour **2247**, le traitement entre faces finies ne trouve qu'une
  famille opposee fiable. Le service reutilise donc le **secours natif
  deja valide dans Plans de vente** : une longueur de mur decrite par
  les deux References Revit reelles de ses extremites, si elles sont
  disponibles, et si la meme cote n'existe pas deja. Le moteur Plans
  de vente n'est pas modifie. L'ancienne surcharge qui retournait
  toujours `[]` pour `_fallback_length_indexes` est supprimee.
  Si ces References natives manquent, le programme n'invente jamais
  une mesure et l'indique dans le rapport.
- `_upgrade_separator_guardrail` ne déclenche
  `_nearby_guardrail_edges` que pour une limite **non murale**
  de type separation de piece : les limites `wall` conserve
  directement la reference de face de mur et n'entrainent
  aucune extraction de rails. Les vraies aretes de sol
  (`floor_edge`) ne sont pas remplacees sans raison.

**Limites et securite :** deux lignes interieures sont preferees,
mais leur **texte peut chevaucher** une etiquette ou une autre cote
dans une piece trop petite. Il faut verifier la valeur lue et
la position des references ; ni cotation fictive, ni creation
d'une paire de faces inexistante. La procedure reste limitee a un
appartement beta, 12 pieces maximum, hors groupes et sur copie
de projet. Les tests automatises hors Revit controlent le
placement interieur, les superpositions, les pieces en L et les
References natives de longueur ; la recette graphique Revit
de 2247 reste a effectuer.

**Prochaine recette ciblée :** repartir d'une **copie sauvegardee**
du meme appartement, tester les 12 pieces, verifier **24/24 si
le mur de 2247 possede des References d'extremites valides**, puis
controler que les deux traits de chaque cote sont internes et
qu'aucun nouveau garde-corps n'a ete explore pour une piece
seulement entouree de murs. Verifier notamment les pieces
2247, 2249, 2251, 2252, 2253 et 2256 et l'absence de doublons.
Ne pas fusionner dans `main` avant validation.


**Recette ciblée sur 2247, 5 novembre 2026 — RESOLU pour la création/positionnement :** la révision effectivement chargée est `2026-11-05-2247-native-fallback-02`. Rapport Revit : **deux annotations créées** dans la chambre 3 (`Collectifs A_Niveau 1`), deux axes intérieurs selon le moteur, largeur affichée **2,62 m**, profondeur affichée **3,33 m**. Superposition de témoins autorisée (texte : 0 ; traits : 1), et emprise proche d'une étiquette signalée. **Aucune cote refusée**. Les messages de diagnostic du secours de longueur native ne figurent pas dans cette exécution : le succès des deux axes ne prouve donc **pas** que ce secours a servi ; il peut s'agir de deux paires de faces opposées. La confirmation métrique des deux nus finis, l'anti-doublon sur relance et la recette 24/24 de l'appartement entier restent ouverts. Le moteur Plans de vente est inchangé ; pas de fusion dans `main`.


---

### BUG-COMMON-028 — 2247 : deux cotes seule, une seule dans l'appartement (23/24)

**Retour utilisateur du 5 novembre 2026 :** dans la meme maquette
Revit 2025.4, la piece **2247 (Chambre 3)** cree **2 cotes
interieures** lorsqu'elle est seule (2,62 m et 3,33 m), mais
seulement **1 cote** lorsqu'elle est la quatrieme piece de
l'appartement de **12 pieces** (total 23/24). Les onze autres
pieces atteignent deux cotes. La revision du journal est
`2026-11-05-2247-native-fallback-02` dans les deux modes.
Le rapport appartement n'affiche ni exception ni refus
graphique pour 2247 : seule la ligne finale de cotation
partielle apparait.

**Cause logicielle mise en evidence (hypothese a confirmer en Revit) :**
`GenericDimensions._existing_dimension_reference_pairs()`
balayait **toutes les cotes de la vue** et considerait qu'un
couple de `Reference` Revit deja utilise interdisait cette
paire de faces pour TOUTES les autres pieces. Deux chambres
mitoyennes peuvent avoir des murs/References partagees mais
doivent posseder leurs propres cotes localisees **a
l'interieur de leur piece**. L'ordre de traitement
(2216, 2239, 2246 avant 2247) pouvait donc priver
2247 de sa seconde orientation, alors que les deux
paires de faces sont accessibles si elle est lancee seule.
Cette cause est reproductible en test hors Revit ;
la correspondance exacte des References du modele n'a
pas encore ete mesuree independamment.

**Correctif beta exclusivement Annotations :**
- Avant de retenir un couple de References comme deja
  cote, regarder la **ligne de la Dimension Revit existante**
  (`Dimension.Curve`) et tester trois points internes
  (20 %, 50 %, 80 %) dans la piece courante avec
  `Room.IsPointInRoom` a l'altitude de sondage validee.
- **Dimension entierement hors piece :** ignorer son
  couple de references dans l'anti-doublon de cette
  piece, sans supprimer ni modifier la cote voisine.
- **Dimension croisant l'interieur :** conserver
  son couple de References comme deja cote dans
  cette piece.
- **Position non lisible** (courbe absente, API
  inaccessible) : conserver l'ancien verrou global
  pour ne pas creer de doublons par approximation.
- Appliquer le meme controle spatial aux cotes
  de substitution par reperes 2D.
- Exposer au rapport les compteurs
  `COTES DEJA PRESENTES` (dans la piece,
  voisines ignorees, position indeterminee)
  et `CONTROLE DOUBLONS PAR PIECE`
  (deux axes, axes deja cotes, axes retenus).
  Nouvelle revision visible :
  `2026-11-05-apartment-room-dedup-03`.

**Anti-regression :** test de deux chambres voisines
partageant les References des murs avec une premiere
cote en chambre A, puis recherche de deux axes
en chambre B (2247), exclusion seulement d'une
cote propre a B et rejet d'un troisieme duplicata.
Une courbe Revit illisible garde le verrou conservative.
**471 tests automatises Annotations et Plans de vente
reussis** (GitHub Actions, 5 novembre 2026).

**Recette Revit en attente :**
1. Sur une copie de projet, **garder les cotes existantes**
   et relancer d'abord **2247 seule** pour confirmer
   qu'une cote existante n'est pas reproduite.
2. Sur une copie equivalentement preparee, relancer
   l'appartement complet en conservant les cotes
   deja produites ; la chambre 2247 doit retrouver
   ses deux dimensions sans reprendre celles
   des chambres voisines ni provoquer de doublons.
3. Fournir les nouvelles lignes de diagnostic
   `COTES DEJA PRESENTES` et
   `CONTROLE DOUBLONS PAR PIECE`
   pour 2247. Un total de 24/24 n'est
   pas une preuve suffisante si les valeurs ou
   les positions des cotes sont fausses.
4. Verifier les nus finis, les lignes
   interieures, les collisions acceptees et
   la non-regression des garde-corps 2239, 2238, 2240.

**Statut : correction beta testee hors Revit ;
validation du traitement appartement encore
necessaire avant fusion dans `main`.**
