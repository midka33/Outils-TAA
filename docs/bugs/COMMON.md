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
site exact de l'exception native**. À investiguer : traitement
multi-vues, état après rechargement, coût mémoire et extraction
d'arêtes, sans attribuer prématurément la faute à la géométrie.

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
Statut : crash natif **non reproduit hors Revit** et cause
précise à déterminer.
