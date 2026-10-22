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
