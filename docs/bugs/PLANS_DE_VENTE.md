# Registre des bugs — Plans de vente

**Statut :** Référence active de développement et de non-régression  
**Cible :** Revit 2025.4 / pyRevit 5.x

Bugs spécifiques au module Plans de vente.

Avant toute modification liée à ce périmètre, lire les fiches applicables
et exécuter les tests anti-régression cités.

---

### BUG-PDV-001 — Crop logement incliné dans une vue orientée

**Symptôme :** le prototype crée correctement une vue dépendante et englobe le logement, mais le rectangle de crop peut apparaître légèrement incliné par rapport à l'écran de la vue.

**Cause racine :** l'emprise était calculée dans les axes globaux X/Y du modèle. Une vue Revit possède son propre repère d'affichage ; ses axes écran sont exposés par `View.RightDirection` et `View.UpDirection`.

**Correction :** projeter les points de contour des pièces dans le repère de la vue, calculer et agrandir l'emprise en coordonnées `u/v`, puis reconstruire les coins XYZ avant `SetCropShape`.

**Règle préventive :** toute géométrie destinée à être alignée visuellement dans une vue doit être calculée dans le repère de cette vue, et non supposée alignée sur les axes globaux du modèle.

**Anti-régression :** test pur d'un `ViewFrame` tourné à 45°, contrôle statique de l'utilisation de `RightDirection` / `UpDirection`, puis validation réelle dans Revit 2025.4 sur une vue orientée.

### BUG-PDV-002 — Contour optimisé rejeté par le crop Revit

**Symptôme :** les trois cas de test du contour logement optimisé basculent en `Rectangle de secours`.

**Cause structurelle identifiée :** le moteur transmettait au `ViewCropRegionShapeManager` une boucle issue directement de l'union géométrique et de `CurveLoop.CreateViaOffset`. Ces boucles peuvent contenir des arcs, courbes tessellées ou autres courbes non linéaires. Or un crop non rectangulaire Revit n'accepte qu'une seule boucle fermée sans auto-intersection composée de **segments droits non nuls** dans un plan parallèle à la vue.

**Correction :** linéariser la boucle extérieure par tessellation puis reconstruction en `Line.CreateBound`, supprimer les doublons / sommets quasi colinéaires, appliquer la marge sur cette boucle droite, puis linéariser une seconde fois avant `IsCropRegionShapeValid`. Ajouter un diagnostic par étape afin qu'un éventuel échec restant indique précisément s'il provient de l'union, de l'extraction, de l'offset ou de la validation Revit.

**Règle préventive :** ne jamais envoyer directement une géométrie de pièce, de face ou un résultat d'offset à `SetCropShape`. Le contrat final doit être normalisé explicitement en boucle de segments droits et contrôlé par `IsCropRegionShapeValid`.

**Anti-régression :** tests statiques imposant la linéarisation avant et après l'offset, l'utilisation de `Line.CreateBound` et le diagnostic d'étape ; revalidation dans Revit 2025.4 sur les trois logements déjà testés.

### BUG-PDV-003 — Capacité non rectangulaire testée sur la mauvaise vue

**Symptôme :** après le correctif de linéarisation, le prototype affiche directement « Cette vue Revit n'autorise pas un crop non rectangulaire » avant même la création de la vue dépendante.

**Cause racine :** `CanHaveShape` était contrôlé pendant le calcul géométrique sur la **vue source**. Cette vue peut être pilotée par un Scope Box ou une autre contrainte de cadrage, alors que la forme finale doit être appliquée à la **nouvelle vue dépendante**. Le test de capacité était donc fait sur le mauvais objet.

**Correction :** séparer la validation géométrique de la capacité de la vue. Le moteur calcule le contour sans exiger `CanHaveShape` sur la source. Après création de la vue dépendante, `apply_to_view` vérifie `CanHaveShape` sur la cible. Si un Scope Box est affecté et que son paramètre est modifiable, il est retiré uniquement sur la nouvelle vue puis la capacité est réévaluée. Si la cible reste incompatible, le rectangle de secours est utilisé avec un avertissement explicite.

**Règle préventive :** toute capacité API liée à l'élément qui recevra une modification doit être évaluée sur l'élément cible final, jamais sur un objet utilisé seulement comme référence de calcul.

**Anti-régression :** test statique garantissant l'absence de `CanHaveShape` dans `build_optimized_crop`, sa présence dans `apply_to_view`, la gestion de `VIEWER_VOLUME_OF_INTEREST_CROP` et la disponibilité d'un fallback rectangulaire.

### BUG-PDV-004 — `CreateViaOffset` échoue au-delà d'une petite marge

**Symptôme :** sur les logements testés, le contour optimisé fonctionne avec une marge de **20 mm**, mais bascule en rectangle de secours à partir d'environ **25 mm**. Le diagnostic indique : `Application de la marge : Revit n'a pas réussi à décaler le contour du logement avec la marge demandée.`

**Cause :** `CurveLoop.CreateViaOffset` doit décaler chaque arête puis retailler les courbes adjacentes pour reconstruire une boucle continue. Sur un contour concave comportant de petits décrochements, une augmentation de la marge peut provoquer des intersections / inversions locales que Revit ne sait pas résoudre. L'échec dépend donc de la géométrie et peut apparaître brutalement à quelques millimètres près. L'API documente qu'un `InvalidOperationException` est levé lorsque la boucle ne peut pas être offsetée.

**Correction :** ne plus utiliser `CurveLoop.CreateViaOffset` pour la marge du plan de vente. Construire une dilatation géométrique robuste par union booléenne : surface du logement + bandes rectangulaires de largeur `2 × marge` autour des arêtes + raccords octogonaux autour des sommets. L'octogone est circonscrit au rayon demandé afin de garantir au moins la marge souhaitée. La boucle extérieure de l'union devient ensuite le crop.

**Règle préventive :** une fonction d'offset topologique Revit ne doit pas être le mécanisme unique pour une marge importante sur un polygone concave métier. Préférer un buffer géométrique robuste dont les changements de topologie sont absorbés par une union booléenne.

**Anti-régression :** vérifier que le service n'utilise plus `CreateViaOffset`, qu'il construit bandes + raccords, puis tester dans Revit 2025.4 des marges 20, 25, 100 et 500 mm sur logements rectangulaire, en L et irrégulier.

### BUG-PDV-005 — Artefacts de marge et décrochements dus aux gaines sans pièce

**Symptôme :** le contour optimisé fonctionne à 20, 50, 200 et 500 mm, mais des facettes / renflements apparaissent dans les angles aux grandes marges. Le contour suit également certains petits retraits liés à des gaines techniques dépourvues de pièce, ce qui donne une enveloppe graphiquement trop détaillée pour un plan de vente.

**Cause :** les raccords octogonaux utilisés pour simuler la dilatation deviennent visuellement perceptibles quand la marge augmente. Par ailleurs, l'union exacte des pièces considère comme significatif tout décrochement de l'enveloppe, même lorsqu'il provient d'un vide technique non destiné à structurer le cadrage graphique.

**Correction :** remplacer les raccords octogonaux par des carrés alignés sur le repère de la vue afin d'obtenir des angles francs. Ajouter ensuite une passe de nettoyage des petits détours rectangulaires en U. La tolérance graphique est bornée entre 300 et 600 mm et varie avec la marge afin de gommer les petites gaines / retraits sans aplatir les grandes formes en L.

**Règle préventive :** distinguer le contour géométrique exact d'un logement de son enveloppe graphique de cadrage. Pour un plan de vente, la seconde doit pouvoir simplifier de petits accidents qui n'apportent aucune information de composition.

**Anti-régression :** tests statiques sur raccords carrés, suppression des petits U et bornes de nettoyage ; validation Revit 2025.4 sur le même logement aux marges 20, 50, 200 et 500 mm.

### BUG-PDV-006 — Le crop entre dans les gaines sans pièce

**Symptôme :** après amélioration des raccords de marge, les angles deviennent propres mais le contour continue à rentrer dans certaines gaines techniques dépourvues de pièce.

**Cause :** le moteur se basait sur l'union exacte des pièces. Une gaine sans Room apparaît donc comme une poche concave du polygone logement. Le nettoyage précédent ne reconnaissait que des motifs simples en U de quatre points et ne couvrait pas les gaines dont le contour comporte davantage de sommets.

**Correction :** fermer les petites poches concaves **avant** la construction de la marge. Le moteur détecte les sommets concaves, teste des ponts directs entre paires de sommets, rejette les ponts qui croisent le contour, puis n'accepte le remplissage que si la bouche, la profondeur et l'aire ajoutée restent sous des seuils conservateurs. Les grandes formes en L doivent donc rester intactes.

Seuils du prototype :
- bouche maximale : 1 500 mm ;
- profondeur maximale : 1 500 mm ;
- aire ajoutée maximale : 2,0 m².

**Règle préventive :** le contour de crop doit être une enveloppe graphique métier, pas l'union brute des Rooms. Les petits vides techniques sans pièce doivent pouvoir être comblés de façon contrôlée avant marge.

**Anti-régression :** test statique garantissant que la fermeture des gaines précède le buffer, plus validation Revit sur le logement A003 utilisé pendant les prototypes.

### BUG-PDV-007 — Les petites marges révèlent encore les gaines

**Symptôme :** après les premiers correctifs, les gaines sont moins visibles à grande marge mais restent encore suivies par le crop lorsqu'on utilise une petite marge.

**Cause :** la détection des poches reposait sur des paires de sommets classés concaves. Selon le sens de la boucle et la géométrie exacte d'une gaine, les deux points qui forment sa bouche ne sont pas nécessairement tous les deux identifiés comme concaves. La grande marge masquait partiellement le défaut, ce qui donnait l'impression que le nettoyage dépendait de la marge.

**Correction :** détecter les poches indépendamment de la marge. Le moteur teste désormais toutes les paires de sommets non adjacents sous des seuils conservateurs. Un pont n'est accepté que s'il ne coupe aucune arête, passe par une zone extérieure au polygone, augmente légèrement l'aire et remplit une poche limitée en bouche, profondeur et surface.

Seuils du prototype :
- bouche maximale : 2 000 mm ;
- profondeur maximale : 2 000 mm ;
- aire remplie maximale : 3,0 m².

**Règle préventive :** la simplification de l'enveloppe métier doit être calculée avant la marge de présentation. Une gaine jugée négligeable doit disparaître de la même manière à 20 mm et à 500 mm.

**Anti-régression :** test statique de l'analyse de toutes les paires de sommets, du test point-dans-polygone et de l'ordre fermeture des gaines → marge robuste ; validation Revit sur A003 aux marges 20/50/200/500 mm.

### BUG-PDV-008 — Nettoyage trop agressif des gaines provoque un fallback systématique

**Symptôme :** après généralisation de la détection des petites poches, les quatre marges testées basculent en `Rectangle de secours`.

**Cause :** le nettoyeur testait toutes les paires de sommets non adjacents. Il pouvait produire un polygone auto-intersectant ou topologiquement incorrect avant même la construction de la marge.

**Correction :** revenir à une stratégie conservatrice : ne traiter que des poches locales limitées entre deux sommets concaves proches, limiter le nombre de sommets de la chaîne remplacée, vérifier le point de pont, contrôler les intersections et valider la simplicité du polygone avant de l'accepter. Si le nettoyage reste douteux, conserver le contour d'origine plutôt que faire échouer tout le crop optimisé.

**Règle préventive :** une simplification graphique ne doit jamais être plus fragile que la géométrie de base. Tout nettoyage doit être optionnel et réversible vers le contour original.

**Anti-régression :** vérifier qu'un échec du nettoyage ne peut pas provoquer à lui seul un fallback rectangle, et rejouer A003 aux marges 20/50/200/500 mm.

### BUG-PDV-009 — Helper de surface polygonale appelé comme méthode d'instance

**Symptôme :** tous les essais passent immédiatement en `Rectangle de secours` avec l'erreur `_polygon_signed_area() takes exactly 1 argument (2 given)` à l'étape « Fermeture des petites gaines et retraits ».

**Cause :** `_polygon_signed_area(points)` avait été définie sans `@staticmethod` mais appelée via `self._polygon_signed_area(...)`. IronPython injectait donc implicitement `self` en premier argument.

**Correction :** déclarer explicitement `_polygon_signed_area` en `@staticmethod`.

**Règle préventive :** tout helper pur placé dans une classe de service doit être explicitement décoré en `@staticmethod` lorsqu'il ne consomme ni `self` ni `cls`.

**Anti-régression :** test statique imposant le décorateur `@staticmethod` sur `_polygon_signed_area`.

### BUG-PDV-010 — Helpers de nettoyage supprimés pendant un refactor

**Symptôme :** tous les essais passent en `Rectangle de secours` avec l'erreur `'CropGeometryService' object has no attribute '_vertices_are_adjacent'`.

**Cause :** lors du remplacement de l'algorithme de fermeture des gaines, les helpers `_vertices_are_adjacent` et `_point_in_polygon` ont été supprimés du fichier alors que la nouvelle méthode continuait à les appeler.

**Correction :** restaurer les deux helpers et ajouter un test de contrat vérifiant explicitement leur présence.

**Règle préventive :** après tout remplacement de bloc important dans un service Python, vérifier les appels `self._...` contre la liste des méthodes réellement définies avant commit.

**Anti-régression :** test statique sur les deux helpers et contrôle automatique des méthodes privées appelées lors des prochains refactors.

### BUG-PDV-011 — Les lèvres d'une gaine ne sont pas toujours des sommets concaves

**Symptôme :** après sécurisation du moteur, le contour optimisé fonctionne mais continue à suivre certaines gaines techniques, notamment avec une petite marge.

**Cause :** le nettoyeur conservateur supposait qu'une poche de gaine était bornée par deux sommets concaves. Ce n'est pas garanti : selon le sens du contour et la forme exacte de la gaine, l'un ou les deux sommets de la bouche peuvent être convexes ou neutres.

**Correction :** tester toutes les paires de sommets non adjacents, mais avec des garde-fous stricts : pont court, aucune intersection avec le contour, milieu du pont situé à l'extérieur du polygone, polygone candidat simple, aire ajoutée positive et limitée, profondeur limitée. Le nettoyage reste réversible vers le contour d'origine en cas de doute.

**Règle préventive :** ne pas déduire la sémantique « gaine / poche extérieure » uniquement de la concavité locale d'un sommet. Utiliser la topologie globale du polygone et la variation d'aire.

**Anti-régression :** test statique du parcours de toutes les paires de sommets et test générique vérifiant que chaque appel `self._...` correspond à une méthode réellement définie.

### BUG-PDV-012 — Buffer 3D instable après nettoyage du contour

**Symptôme :** le crop optimisé retombe en rectangle de secours à l'étape `Construction de la marge robuste`, avec une erreur `BooleanOperationsUtils` signalant des imprécisions géométriques entre solides.

**Cause :** après fermeture de certaines poches techniques, le contour est plus simple mais la construction de marge par bandes + caps extrudés peut créer des solides avec faces ou arêtes presque coïncidentes. Les booléens 3D Revit deviennent alors instables.

**Correction :** essayer en priorité `CurveLoop.CreateViaOffset` sur le contour **déjà nettoyé**, puis ne conserver le buffer 3D par booléens qu'en secours. L'offset natif avait échoué auparavant sur le contour brut à cause des micro-concavités ; après nettoyage, il peut à nouveau être viable et produit des angles propres sans opérations booléennes.

**Règle préventive :** préférer l'opération géométrique la plus simple une fois le contour métier stabilisé. Les booléens 3D ne doivent pas être utilisés par défaut lorsqu'une opération 2D native peut suffire.

**Anti-régression :** test statique garantissant que l'offset natif est essayé avant le buffer booléen.

### BUG-PDV-013 — Le fallback booléen 3D reste instable

**Symptôme :** malgré la priorité donnée à `CreateViaOffset`, le moteur retombe encore sur `BooleanOperationsUtils` pour la marge et échoue avec le message Revit `Failed to perform a Boolean operation for the two solids`.

**Cause :** le simple fait de conserver le buffer 3D comme second choix réintroduit une branche connue comme instable sur des solides quasi coplanaires. Le moteur de marge pouvait donc encore échouer exactement de la même manière qu'avant.

**Correction :** supprimer complètement les booléens 3D de l'étape de marge. La marge est désormais 100 % 2D : essai d'offset natif sur le contour nettoyé, puis simplification adaptative de petites concavités et nouvel essai d'offset. Si aucun contour 2D valide n'est obtenu, le niveau supérieur utilise directement le rectangle de secours.

**Règle préventive :** une stratégie déjà identifiée comme instable ne doit pas rester cachée comme fallback par défaut. Les fallbacks doivent être plus simples et plus sûrs que le chemin principal.

**Anti-régression :** test de contrat vérifiant l'absence de `BooleanOperationsUtils` dans `_buffer_outward` et l'ordre offset natif → simplification adaptative.

### BUG-PDV-014 — Fermeture de gaine par pont diagonal

**Symptôme :** le moteur détecte et comble certaines gaines, mais la fermeture
relie directement deux lèvres dont les positions ne sont pas parfaitement en
vis-à-vis. Le crop crée alors un segment biaisé sans rapport avec une arête de
mur réelle.

**Cause :** la fermeture des poches utilisait la distance minimale entre deux
sommets comme critère principal. Un pont direct pouvait donc être valide
topologiquement tout en introduisant une nouvelle direction diagonale dans le
dessin.

**Correction :** relever les murs droits qui bornent les Rooms, calculer leur
face opposée à la pièce à partir de `Wall.Orientation` et `Wall.Width`, puis
utiliser ces faces comme guides de fermeture. Les lèvres sont projetées
perpendiculairement sur le guide et reliées le long du chant du mur. Un pont
direct n'est autorisé en secours que s'il est déjà parallèle à une direction
locale du contour.

**Règle préventive :** une simplification de crop destinée à un plan
architectural ne doit pas créer une direction graphique nouvelle uniquement
parce qu'elle est topologiquement plus courte. Lorsqu'une fermeture correspond
à un vide bordé par des murs, la géométrie construite doit privilégier les
directions et faces de ces murs.

**Anti-régression :** test de contrat sur la collecte des faces opposées, le
pont guidé par mur et le refus des ponts directs créant une direction oblique ;
validation Revit sur le logement de référence aux marges 20 / 50 / 200 / 500 mm.

### BUG-PDV-015 — Le filtre d'angle rejette le mur qui devait supprimer le biais

**Symptôme :** après l'introduction des fermetures guidées par mur, le logement
de référence bascule en `Rectangle de secours` à l'étape
`Construction de la marge robuste`.

**Cause :** le premier filtre exigeait que la corde entre les deux lèvres de la
poche soit presque parallèle au mur guide. Or, lorsque les lèvres sont
décalées, cette corde est précisément diagonale. Le bon mur était donc rejeté,
la poche restait non simplifiée et `CurveLoop.CreateViaOffset` pouvait encore
échouer sur la concavité.

**Correction :** supprimer la comparaison d'angle entre la corde des lèvres et
le mur. Les lèvres sont projetées indépendamment sur une même face opposée de
mur. La validité repose ensuite sur la proximité au guide, la position
extérieure du segment, l'aire ajoutée, la profondeur et la simplicité du
polygone.

**Règle préventive :** un filtre géométrique ne doit pas tester comme condition
d'entrée la propriété que l'algorithme a justement pour objectif de corriger.
Pour une fermeture guidée, valider le guide et les projections plutôt que la
corde brute entre les points.

**Anti-régression :** test de contrat garantissant l'absence de filtre
`mouth_vector / parallel_sin` dans `_wall_aligned_bridge_paths`, présence
des projections sur le mur et validation Revit sur A003.

### BUG-PDV-016 — Détection automatique trop large : 50 fermetures et calcul lent

**Symptôme :** sur A003, la fenêtre de diagnostic indique
`50 poche(s), dont 50 alignée(s) sur mur` avant un échec de marge. Le calcul
est sensiblement long.

**Cause :** la fermeture automatique parcourt les paires de sommets du contour
et les compare aux guides de murs. Sur un logement complexe, beaucoup de
couples peuvent satisfaire les garde-fous successifs. La boucle de sécurité
atteint alors sa limite de 50 modifications, avec un coût combinatoire élevé,
sans garantir une enveloppe architecturale plus pertinente.

**Correction :** permettre à l'utilisateur de choisir explicitement le type de
mur périphérique. Pour ce chemin, les segments de ce type qui bordent les
Rooms sont convertis en bandes 2D de largeur égale à l'épaisseur du mur puis
unis aux Rooms avant extraction du contour. La recherche combinatoire des
poches est entièrement ignorée lorsque ce type explicite est fourni.

**Règle préventive :** lorsqu'une information métier fiable est disponible
(type de mur périphérique), la privilégier à une inférence géométrique globale
coûteuse. Une optimisation ne doit pas parcourir tout le graphe des sommets si
un sous-ensemble architectural explicite permet de construire directement
l'enveloppe.

**Anti-régression :** tests de contrat sur le sélecteur WPF, la transmission du
`UniqueId` du type, l'union des bandes de murs aux Rooms et le contournement
de `_close_small_recesses` dans le chemin explicite ; validation Revit A003
sur le temps de calcul et le contour obtenu.

### BUG-PDV-017 — Le mur périphérique choisi n'est pas la limite directe de Room

**Symptôme :** le type de mur périphérique est bien sélectionné mais le
diagnostic retourne `Murs périphériques utilisés : 0` et
`Aucun mur droit du type périphérique sélectionné ne borde les pièces`.

**Cause :** la première implémentation ne considérait que
`BoundarySegment.ElementId`. Elle supposait donc que le mur périphérique
sélectionné était directement room-bounding. Cette hypothèse est fausse dès
qu'un doublage, une contre-cloison ou une autre limite de pièce se trouve entre
la Room et le mur extérieur.

**Correction :** calculer d'abord le contour extérieur des Rooms puis rechercher
toutes les instances du type choisi à proximité de ce contour. Les candidats
doivent être proches et sensiblement parallèles à une arête extérieure. Seule
la portion en vis-à-vis du logement est transformée en bande, étendue côté
Room pour franchir un doublage et côté opposé jusqu'au mur.

**Règle préventive :** distinguer proximité architecturale et relation
topologique Revit. Un élément métier « périphérique » ne doit pas être supposé
être l'élément qui porte directement le `BoundarySegment` d'une Room.

**Anti-régression :** test de contrat garantissant que le collecteur explicite
utilise `FilteredElementCollector` + proximité au `room_outer_loop` et ne
dépend plus de `segment.ElementId`; validation Revit sur A003 avec le même
type de mur.

### BUG-PDV-018 — Les murs périphériques d'un lien Revit sont invisibles au moteur

**Symptôme :** la recherche par proximité retourne toujours
`Murs périphériques utilisés : 0` alors que le mur visible est clairement
à moins de 1 000 mm du contour des Rooms.

**Cause :** le sélecteur et le collecteur ne parcouraient que le document hôte.
Un mur affiché dans la vue peut cependant appartenir à un `RevitLinkInstance`.
Dans ce cas, son type et ses instances ne sont pas accessibles via un
`FilteredElementCollector` du projet actif.

**Correction :** exposer dans le sélecteur les types de murs du projet et des
liens Revit chargés, avec une source explicite. Pour une source liée, collecter
dans `GetLinkDocument()` puis transformer points, vecteurs et plage Z dans le
repère hôte avec `GetTotalTransform()` avant le test de proximité.

**Règle préventive :** toute géométrie visible dans une vue de coordination ne
doit pas être supposée appartenir au document actif. Les sélections de types
doivent conserver l'identité de leur document source.

**Anti-régression :** tests de contrat sur `RevitLinkInstance`,
`GetLinkDocument`, les clés `HOST|...` / `LINK|...` et la transformation
des murs liés ; validation Revit A003 en choisissant explicitement la source
affichée dans la liste.

### BUG-PDV-019 — Mur hôte visible mais aucune instance du type n'est retenue

**Symptôme :** Revit montre directement une instance hôte du type
`MUR-EXT-BET-Béton20CM` au niveau du logement, alors que le moteur retourne
toujours zéro mur périphérique.

**Cause potentielle isolée :** le collecteur comparait le texte `UniqueId` du
`WallType` de chaque instance avec la clé de sélection. Ce détour est inutile
et rend le diagnostic impossible lorsque le filtre échoue avant la géométrie.

**Correction :** résoudre une seule fois le `WallType` sélectionné dans le
document source et comparer son `ElementId` à `wall.GetTypeId()`. Ajouter
des compteurs après chaque filtre : type, courbe droite, niveau, zone 2D et
proximité/parallélisme.

**Règle préventive :** pour relier une instance Revit à son type, utiliser
prioritairement `GetTypeId()` et l'identité d'élément Revit. Les identifiants
textuels servent à sérialiser une sélection, pas à répéter le test de type sur
toutes les instances.

**Anti-régression :** test de contrat sur `GetTypeId()`, résolution du type
par `Document.GetElement(uniqueId)` et présence du diagnostic par étapes ;
validation Revit sur A003.

### BUG-PDV-020 — Raccords arbitraires et recherche globale des poches

**Symptôme :** gaines comblées par des biais, puis collecte de murs complexe et
jusqu'à 50 fermetures avec temps de calcul excessif.
**Cause :** fermeture fondée sur des paires globales de sommets et des cordes,
puis projection sur des murs externes au contour ; validations d'aire ne
prouvant pas la contenance. La marge adaptative pouvait recréer une diagonale
en supprimant un sommet concave, même après correction du premier nettoyage.
**Correction :** moteur pur local `local_crop_geometry.py` ; chaîne bornée à
12 arêtes, supports immédiatement voisins, colinéarité / TR / perpendiculaire.
Murs, types, bandes, faces guides et liens retirés de ce sous-module. Contenance
sur toutes les arêtes, simplicité avec contacts et recouvrements, seuils
3,5 m / 2 m / 5 m², extension maximale 3,5 m, deux passes et 128 validations.
Les chemins de nettoyage de marge utilisent le même moteur ; conservation de
l'original si reconstruction impossible. Les règles historiques BUG-PDV-006 à
011 et 014 à 019 relatives aux paires globales et murs sont remplacées par celle-ci.
**Règle préventive :** ni gain d'aire ni sommets contenus ne garantissent qu'un
candidat ne coupe pas le logement. Contrôler les arêtes complètes et tester
le chemin de secours autant que le chemin principal. Ne pas réintroduire le
buffer 3D de marge (BUG-PDV-013).
**Tests :** `test_local_crop_geometry.py` (A–H, sens/rotation, seuils, 20 poches,
budget), `test_local_crop_adapter.py` (conservation/reconstruction/diagnostic),
contrats sans murs et suite `tests/plans_vente`. A003 reste à valider dans Revit.

### BUG-PDV-021 — Diagnostic suffixé court-circuitant CanHaveShape

**Symptôme identifié dans le code :** dès qu'un compteur était ajouté au mode
« Contour optimisé », sa comparaison exacte échouait et le contrôle de capacité
non rectangulaire de la vue cible pouvait être sauté.
**Cause :** `mode == "Contour optimisé"` mélangeait statut et texte de diagnostic.
**Correction :** test du préfixe du mode conservant les diagnostics détaillés.
**Règle préventive :** les diagnostics ne doivent jamais désactiver un garde-fou.
**Test :** vraie méthode `apply_to_view` avec vue incapable et mode suffixé ;
le rectangle de secours est appliqué. Contrôle réel Revit toujours requis.

### BUG-PDV-022 — Petits segments résiduels utilisés comme supports A/B

**Symptôme :** le moteur local ferme correctement les gaines et reste rapide, mais
quelques petits décrochements persistent à proximité immédiate de certaines poches.

**Cause :** le segment immédiatement avant ou après la chaîne détectée peut lui-même
être un petit retour appartenant visuellement à la poche. Il était alors utilisé comme
support A ou B. Le raccord était géométriquement valide mais s'appuyait sur un segment
trop local, laissant un résidu.

**Correction :** normaliser localement A/B avant raccord. Au maximum deux segments
adjacents peuvent être absorbés de chaque côté lorsqu'ils sont courts relativement au
contexte local. Les règles colinéaire / Trim-Extend / perpendiculaire et tous les
garde-fous de contenance restent inchangés. Le diagnostic compte les segments absorbés.

**Règle préventive :** une chaîne de poche doit être distinguée de ses supports
structurels. Avant de raccorder, vérifier localement que A/B ne sont pas eux-mêmes des
petits retours parasites. Ne jamais remplacer cette normalisation bornée par une
simplification globale du polygone.

**Anti-régression :** tests purs sur absorption gauche, droite, segment court
structurel, limite de deux segments et cas complet avec deux lèvres résiduelles ;
test adaptateur sur le diagnostic des segments absorbés.

### BUG-PDV-023 — Crop optimisé rejeté selon certaines marges sans fallback final

**Symptôme :** selon la marge saisie, Revit affiche
`Le contour calculé n'est pas accepté par Revit comme crop.` et la création
du prototype échoue. Un cas a été confirmé le 2026-10-05 à l'échelle 1:100
avec une marge de 50 mm.

**Cause racine :** le fallback rectangulaire existe lorsque la vue cible ne
supporte pas les crops non rectangulaires, mais il n'est pas utilisé lorsque
`ViewCropRegionShapeManager.IsCropRegionShapeValid(selected_loop)` rejette le
contour optimisé après construction de la marge. Le service lève alors une
erreur au lieu d'essayer le `fallback_curve_loop`.

**Correction planifiée :** lors de la passe de consolidation de l'Étape 03,
si le contour optimisé échoue au contrôle final, valider puis appliquer le
rectangle de secours avant de déclarer un échec. Conserver en parallèle le
diagnostic du contour optimisé afin d'identifier les marges/topologies qui
produisent une boucle non acceptée.

**Règle préventive :** tout chemin de génération d'un crop optimisé doit avoir
un fallback final contrôlé au point exact où Revit valide la boucle. Un fallback
présent uniquement sur un test de capacité amont n'est pas suffisant.

**Anti-régression :** ajouter un test adaptateur où
`CanHaveShape=True`, le contour optimisé est refusé par
`IsCropRegionShapeValid`, mais le rectangle de secours est accepté ; vérifier
que le rectangle est appliqué et qu'un avertissement remplace l'exception.
Rejouer ensuite dans Revit les marges 20 / 50 / 200 / 500 mm sur les logements
de référence.

### BUG-PDV-024 — Noms des types de zones remplies vides dans pyRevit

**Symptôme :** la liste **Zone remplie** contient bien des éléments sélectionnables,
mais toutes les lignes sont visuellement vides dans l'interface Plans de vente.

**Cause racine :** `FilledRegionType` hérite de `ElementType`. Sous
IronPython/pyRevit, l'accès direct à `ElementType.Name` peut être illisible ou
retourner une valeur non exploitable à cause du masquage de la propriété héritée.
Le service utilisait `getattr(region_type, "Name", "")`, ce qui produisait des
libellés vides.

**Correction :** lire en priorité le nom par
`Autodesk.Revit.DB.Element.Name.GetValue(element_type)`, puis conserver
`Name` comme fallback. La même lecture est utilisée dans la liste et dans le
rapport de création.

**Règle préventive :** pour les sous-classes de `ElementType` utilisées sous
IronPython/pyRevit, ne pas supposer que `.Name` est lisible directement.
Centraliser une lecture sûre lorsque le type doit être affiché dans l'UI.

**Anti-régression :** test statique du service imposant
`Element.Name.GetValue(element_type)` pour les `FilledRegionType`, puis
validation réelle dans Revit 2025.4 de l'affichage des noms dans la ComboBox.

**Validation Revit :** confirmée le **5 octobre 2026** ; les noms des types de
zones remplies sont correctement affichés et sélectionnables.

### BUG-PDV-028 — Collisions d'identité et de repère avec les pièces liées

**Symptôme reproduit hors Revit :** deux instances d'un même bâtiment contenant
la pièce `r1` / logement `101` ne peuvent pas être distinguées par le seul
UniqueId de pièce ou le numéro logement. Leur géométrie brute reste aux mêmes
coordonnées malgré deux placements de lien différents.

**Cause racine :** les entrées V1 supposent un document unique ; l'id local et
la géométrie ne portent pas l'instance de lien.

**Correction :** contexte `SourceRoom` avec instance/UniqueId et transformation,
regroupement source + logement, adaptation des entrées crop/tags/cotes/repérage,
filtres natifs des nomenclatures par source et rapprochement des niveaux par
altitude transformée. Les pièces hôtes conservent le chemin V1.

**Règle préventive :** ne jamais résoudre une référence de pièce liée dans SITE,
transformer une référence géométrique brute en perdant sa référence native, ou
filtrer une nomenclature liée uniquement sur le numéro du logement. Une source
ambiguë doit être signalée avant livraison du plan.

**Anti-régression :** `tests/plans_vente/test_linked_rooms.py` : mêmes UniqueIds
et numéros, instances répétées, transformations/inverse, doublons de tags,
cotes natives liées, filtrage des nomenclatures, opt-out hôte, contexte d'erreur.
Le workflow représentatif API/WPF a ensuite été validé par l'utilisateur dans
Revit 2025.4 le 20 octobre 2026 ; les cas limites restant hors périmètre sont
listés dans `docs/release/Preparation_Plans_de_Vente_V1.1_Liens.md`.

### BUG-PDV-029 — Identifiant numérique du lien exposé dans les noms de sortie

**Symptôme :** un plan généré depuis un lien pouvait être nommé
`A18-L5530419`, et le même suffixe contaminait la feuille, les vues et les
nomenclatures.

**Cause racine :** la clé technique utilisée pour empêcher les collisions entre
sources était réutilisée comme clé de nommage visible.

**Correction :** séparer l'identité interne `Source + N° logement` de la clé
visible. Le numéro métier reste inchangé tant qu'il est unique. Si plusieurs
sources portent le même numéro, l'interface demande à l'utilisateur un libellé
lisible pour différencier les sorties.

**Règle préventive :** un `ElementId` ou identifiant interne de lien ne doit
jamais devenir un nom utilisateur par défaut. La désambiguïsation visible doit
être déclenchée uniquement par une collision réelle et rester compréhensible.

**Anti-régression :** `tests/plans_vente/test_linked_rooms.py` vérifie
l'absence du suffixe technique et la présence du dialogue de différenciation en
cas de doublon.

### BUG-PDV-030 — Niveau SITE absent bloquant un logement lié

**Symptôme :** la génération s'arrêtait avec
`niveau SITE absent ou ambigu à ...` lorsque le bâtiment lié possédait un
niveau sans équivalent déjà créé dans SITE.

**Cause racine :** une `ViewPlan` doit appartenir à un niveau du document
hôte, mais la première V1.1 imposait à l'utilisateur de préparer manuellement
tous les niveaux et vues SITE.

**Correction :** résoudre l'altitude transformée du niveau lié, réutiliser un
niveau SITE unique lorsqu'il existe, sinon créer automatiquement un niveau
`PDV_AUTO_±XX.XXX` et, si nécessaire, une vue plan source SITE. Une ambiguïté
réelle entre plusieurs niveaux déjà présents à la même altitude reste bloquante.

**Règle préventive :** l'absence d'un niveau technique hôte ne doit pas imposer
une préparation manuelle pour un workflow automatisé. Ne jamais choisir
arbitrairement entre plusieurs niveaux existants à la même altitude.

**Anti-régression :** test de `host_level_name` avec création automatique du
niveau et validation réelle dans Revit 2025.4 pendant la recette V1.1.