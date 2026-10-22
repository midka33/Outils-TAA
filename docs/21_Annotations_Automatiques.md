# Outils TAA — Cotation automatique et Étiquetage automatique

**État : bêta de recette, non validée dans Revit.**
**Compatibilité visée : Revit 2025.4 / pyRevit 5.x.**
**Branche :** `feature/annotations-automatiques-beta`.
Ne pas fusionner dans `main` avant validation d'un projet de test.

## Objet

Deux boutons dans le panneau **Annotations** du ruban Outils TAA :

- **Cotation auto** : cotes natives par pièce (jusqu'à deux orientations principales) ;
- **Étiquetage auto** : étiquettes de pièces natives, avec sélection du type.

Les moteurs `dimension_service.py`, `room_tag_service.py` et la bibliothèque géométrique `lib/plans_vente/` sont importés depuis Plans de vente. Les contrôles spécifiques aux vues `PDV PROTO` sont adaptés uniquement par sous-classes. Aucun service Plan de vente existant n'a été modifié par cette bêta.

## Fonctionnement

1. Lancer le bouton voulu dans **Outils TAA → Annotations**.
2. Si des vues en plan ont été sélectionnées dans le navigateur Revit, elles sont reprises. Sinon, sélectionner une ou plusieurs vues en plan dans la liste.
3. Choisir un type de cote ou d'étiquette **chargé dans le document hôte**.
4. Pour les cotes, choisir le style des **petites lignes 2D de référence** ; le style est lu parmi les styles de lignes du document. Les lignes mesurent au maximum 5 mm.
5. Confirmer l'opération ; consulter le rapport pyRevit.

Les deux fonctions limitent les collisions selon leurs estimations géométriques. En l'absence d'une position satisfaisante, l'annotation doit être omise et l'échec signalé (aucune position chevauchante volontaire).

### Pièces hors groupe

Annotations normales dans la vue, sans groupe de détails.

### Pièces dans un groupe de modèle

Le service cherche un groupe de détails attaché TAA existant correspondant au bouton, et l'affiche sur l'occurrence si possible.

À défaut, il prépare des annotations pour les pièces de cette occurrence, puis **tente** un rattachement natif via l'API Revit. Il annule le traitement complet du groupe si Revit refuse l'opération ou si l'intégrité du groupe de modèle ne peut être garantie.

Pour les cotes utilisant un élément extérieur au groupe, une petite ligne de détail 2D est placée sur la limite de pièce et sert de référence à la cote. La ligne est volontairement **non associative avec le mur de façade**. La correction d'une façade déplacée relève de l'utilisateur. Aucune vérification des écarts géométriques entre occurrences n'est prévue.

Les lignes de référence candidates sont limitées aux principales directions retenues par le moteur ; les références de longueur issues de murs hors groupe sont exclues.

**Point de validation prioritaire :** l'API de création d'un groupe de détails attaché à un groupe de modèle *déjà existant* doit être testée dans Revit 2025.4. Les validations statiques ne démontrent pas ce comportement. En cas de refus, le module annule l'ensemble pour ce groupe et indique le motif.

## Périmètre / limites bêta

- Plans d'étage uniquement, et pièces du document actif visibles dans ces plans.
- Pas de pièces issues des fichiers Revit liés dans cette première recette, même si Plans de vente les prend en charge.
- Types de cotes linéaires et types d'étiquettes de pièces chargés dans le document hôte.
- Pas de déplacement des annotations manuelles existantes.
- La détection des doublons compare les paires de références de cotation déjà présentes ; une pièce partiellement cotée reste traitable.
- Les bounding boxes Revit et l'estimation des lignes de cote peuvent être conservatrices.
- Le placement des détails réutilisés entre occurrences n'est pas réoptimisé : aucun contrôle de géométrie inter-occurrences, conformément à la décision métier.
- Pas de test réel Revit 2025.4 à ce stade ; ne pas déclarer les groupes validés.

## Recette Revit à réaliser (sur copie de maquette)

- [ ] REV-ANN-01 : les deux boutons sont présents et ouvrent leur sélection.
- [ ] REV-ANN-02 : sélectionner deux vues et choisir des types distincts ; vérifier les créations.
- [ ] REV-ANN-03 : lancer Étiquetage puis Cotation ; aucun chevauchement.
- [ ] REV-ANN-04 : lancer Cotation puis Étiquetage ; aucun chevauchement.
- [ ] REV-ANN-05 : relancer chaque module ; aucune annotation doublée.
- [ ] REV-ANN-06 : pièce seule, sans groupe, vue en plan ordinaire.
- [ ] REV-ANN-07 : pièce dans un groupe, murs référencés dans le groupe, groupe de détails réellement attaché.
- [ ] REV-ANN-08 : mur de façade hors groupe ; petite ligne 2D du style choisi, cote associative à la ligne.
- [ ] REV-ANN-09 : autre occurrence du groupe, réutilisation du type de groupe de détails.
- [ ] REV-ANN-10 : erreur API groupement, annulation atomique, aucune annotation/lignes 2D isolées.
- [ ] REV-ANN-11 : vues sans pièces / gabarits / liens ; sortie explicite sans crash.
- [ ] REV-ANN-12 : non-régression Plans de vente V1.1 sur projet témoin.

## Architecture

```text
OutilsTAA.extension/
  OutilsTAA.tab/
    Annotations.panel/
      Cotation.pushbutton/
      Etiquetage.pushbutton/
      services/
        launcher.py
        annotations_service.py
    PlansDeVente.panel/
      services/ dimension_service.py, room_tag_service.py (inchangés)
  lib/plans_vente/ (inchangé)
```

Les nouveaux adaptateurs sont le premier pas vers un moteur de référence
commun ; l'extraction définitive dans une bibliothèque d'annotation autonome
est reportée après validation de cette bêta dans Revit.


## Correctif après retour du 22 octobre 2026

Les captures utilisateur montrent 40 pièces au niveau 0 et 44 au niveau 1,
mais aucune cote ni étiquette créée, avec le message `(Name)`.
Le premier adaptateur lisait directement `room.Name`, connu pour lever
`AttributeError: Name` sous IronPython.

Correctifs : paramètres `ROOM_NAME` / `ROOM_NUMBER`, noms d'éléments
via `Element.Name.GetValue`, validation de niveau fiable, traceback complet
dans le rapport, isolation des pièces non groupées pour éviter un rollback
global de tout l'étage.

**État :** tests de régression hors Revit préparés ; corrections à revalider
sur les mêmes deux vues. Le rattachement des groupes attachés reste un point
de recette séparé.

## Correctif de cotation — essai du 22 octobre 2026

**Résultat de recette :** Étiquetage auto a créé 40 étiquettes au niveau 0. Cotation auto a créé 0 cote sur les 40 pièces du niveau 0 et 44 du niveau 1, avec `Aucune position de cote sans collision` pour chaque pièce.

**Racine :** dans l'adaptateur de la bêta, un conflit détecté pour l'une des deux cotations entraînait le rejet complet du calcul par pièce, alors que Plans de vente conserve historiquement les deux cotes avec avertissement. Le nouveau module doit garantir l'absence de collision sans supprimer toute cotation réalisable.

**Comportement corrigé :** calcul des positions candidates via `plans_vente.dimension_positioning.placement_candidates`, sélection d'une ou deux cotes avec `annotations.strict_dimension_positioning.select_collision_free_placements`. Les cotes conflictuelles sont ignorées individuellement et expliquées dans le rapport ; les cotes restantes sont conservées. Le moteur Plans de vente reste identique.

**Contrôles pour la prochaine recette :**

- [ ] REV-ANN-13 : relancer la cotation après les 40 étiquettes du niveau 0 ; au moins certaines pièces doivent être cotées, sans chevauchement.
- [ ] REV-ANN-14 : relancer sur le niveau 1 ; vérifier qu'une cote peut être créée même si la seconde ne trouve pas de place.
- [ ] REV-ANN-15 : pièces 1123 et 2213 : comparer visuellement les deux directions et le rapport par orientation.
- [ ] REV-ANN-16 : vérifier qu'une seconde exécution ne duplique pas les cotes.

**Statut :** code et tests hors Revit ; validation visuelle et API Revit 2025.4 à effectuer.


## Correctif « deux grandes dimensions » — 22 octobre 2026

**Retour en Revit :** 57 cotes sur `Collectifs A_Niveau 0`, mais des cotes
paralleles et des longueurs de petits troncons de mur a la place des
deux dimensions principales de chaque piece.

**Cause :** les cotes de secours par longueur de mur de Plans de vente
etaient utilisees lorsque les cotes de faces opposees echouaient.
C'est un comportement distinct du besoin des boutons Annotations.

**Regle metier obligatoire pour Cotation automatique :**

1. Identifier les faces finies de la piece en reutilisant le service PDV.
2. Retenir la meilleure paire de faces opposees (mesure interieure).
3. Retenir la seconde plus grande portee entre faces opposees dans une autre direction, sans imposer de perpendicularite.
4. Garder les deux emprises et references d'origine, avec placement adaptatif
   sans collision avec etiquette/cote et sans texte hors piece.
5. Si aucune position fiable n'existe pour un axe, n'ajouter aucune cote
   sur cet axe, et signaler le motif. **Ne jamais basculer vers la
   longueur d'un mur ou d'un autre segment en guise de remplacement.**
6. Creer une seule cote si un seul axe exploitable reste, plutot que
   deux cotes paralleles ou approximatives.

**Perimetre :** modification seulement de l'adaptateur
`GenericDimensions` et du helper pur
`lib/annotations/principal_dimension_axes.py` ; pas de modification
de `dimension_service.py` ou de la geometrie Plans de vente.

**IMPORTANT POUR LES TESTS :** les 57 cotes deja creees par la version
precedente ne sont pas identifiees comme provenant de TAA. Elles doivent
etre supprimees manuellement / annulees **sur une copie du projet** avant
nouveau test. Ne jamais les supprimer automatiquement, pour ne pas
effacer des cotes manuelles existantes. Le module reste prudent en
presence de cotes preexistantes.

- [ ] REV-ANN-17 : apres nettoyage de la copie, une piece rectangulaire
  recoit ses deux plus grandes mesures interieures entre faces opposees (orthogonales seulement si la geometrie l'est).
- [ ] REV-ANN-18 : aucune cote de longueur de mur / petit troncon,
  meme quand la seconde direction ne peut pas etre placee.
- [ ] REV-ANN-19 : une piece avec une seule paire opposable ne recoit
  au maximum qu'une cote.
- [ ] REV-ANN-20 : aucune collision sur les 40 etiquettes deja validees ;
  les pieces complexes produisent un diagnostic plutot qu'une fausse cote.


## Precision metier : les plus grandes cotes et alignement entre pieces

**Decision utilisateur du 22 octobre 2026 (prioritaire sur les anciens prototypes)** :

- Retenir **deux plus grandes distances utiles entre faces finies opposees de chaque piece**, par ordre de portee. Ces deux directions peuvent etre obliques et ne doivent **pas obligatoirement** etre perpendiculaires.
- Reutiliser la geometrie PDV de detection des faces et l'API de cotation native. Aucune longueur isolee de mur en remplacement d'une cote de piece.
- Pour les cotes de meme orientation dans les pieces voisines, rechercher une ligne de cote **colineaire** a une cote existante de la vue ; ne jamais modifier la longueur mesuree ni les references d'origine. Un guide eloigne n'impose aucun alignement.
- Aligner seulement si la nouvelle cote est positionnable dans la piece avec un texte interieur, **sans chevauchement d'etiquettes ni d'autres cotations**. A defaut, utiliser le meilleur placement sans collision, ou omettre cette cote et expliquer pourquoi.
- Si seulement une portee est mesurable sans conflit, ne creer que cette cote. Ne pas forcer de cotations incorrectes pour atteindre deux.

**Implementation beta :** `principal_dimension_axes.py` trie les paires PDV par distance ; `dimension_alignment.py` cherche les rails de meme orientation, peut generer une position exactement colineaire au rail voisin ; `strict_dimension_positioning.py` favorise ces candidats *apres* l'elimination des collisions. `GenericDimensions._alignment_rails` lit les lignes des cotes deja posees dans la vue (y compris les cotes creees sur les pieces precedentes). Le moteur PDV n'est pas modifie.

**Parametres internes beta :** proximite maximale du guide : 25 mm sur papier a l'echelle de la vue ; tolerance de coincidence : 0,25 mm papier ; parallelisme pour le calage exact : 0,05 degre (des cotes seulement approximativement paralleles ne sont pas forcees sur un meme rail). Les nouvelles positions sont colineaires exactement avec le guide, dans les limites de precision numerique. Ces valeurs sont ajustables apres recette Revit.

**Tests Revit a faire sur une copie propre** : piece rectangulaire, piece biaise, deux pieces voisines avec cotes paralleles et guides d'alignement, variante avec etiquette bloquant le guide, et second lancement sans doublons. Retirer *manuellement* les anciennes cotes incorrectes des essais beta avant de tester, sans suppression automatique des cotes utilisateur.


## Correctif apres essai des 34 cotations — 22 octobre 2026

**Constat de recette :** sur 40 pieces de la vue `Collectifs A_Niveau 0`,
34 cotes seulement ; la plupart des pieces ne recoivent qu'une
dimension. Les messages indiquent qu'aucune position sans conflit
n'a ete trouvee, souvent avec zero collision etiquette/cote indiquee.

**Causes trouvees dans l'adaptateur :**
- Le refus general des croisements de traits de cote rend impossible
  deux portees completes dans de nombreuses pieces rectangulaires.
- Une seconde execution rejetait toute piece touchee par une bbox
  de cote existante, y compris si l'autre direction restait a coter.

**Comportement beta corrige :**
1. Autoriser le **seul croisement ponctuel de lignes** entre cotes de
   directions distinctes. Aucune superposition de textes, temoins ou
   lignes de cote colineaires n'est autorisee. Ne pas deplacer les
   references natives ni la longueur mesuree.
2. En presence d'une cote existante, bloquer son texte (position
   `Dimension.TextPosition` estimee avec marge) et bloquer les
   lignes colineaires superposees. Quand la position de texte
   native n'est pas disponible, conserver l'emprise Revit complete.
3. Detecter les paires de references deja cotees par leur representation
   stable : seules ces paires sont exclues. L'axe manquant peut etre
   ajoute lors d'un second lancement sans multiplier les doublons.
4. Conserver pour le module **Etiquetage** les obstacles de cote
   complets : les etiquettes ne passent pas sur les traits de cote.
5. Retenir au plus deux plus grandes portees de directions distinctes
   (15 degres d'ecart minimal par defaut), sans perpendicularite
   obligatoire et sans longueur de mur en secours.

**Limites / validations :** `Dimension.TextPosition` et les
references stables Revit doivent etre controles sur des cotations
reelles dans Revit 2025.4. Une bbox reste un fallback conservateur.
L'objectif est 2 cotes par piece, mais une piece sans deux placements
valides peut rester a 1 ou 0 cote plutot que recevoir un chevauchement.

**Scenario de recette** :
- [ ] REV-ANN-21 : rectangle simple non cote, apres etiquetage : obtenir les deux grandes portees, avec simple croisement de traits hors textes.
- [ ] REV-ANN-22 : lancer une seconde fois sur la meme vue : aucune cote en double.
- [ ] REV-ANN-23 : supprimer uniquement la deuxieme cote d'une piece, puis relancer : seule celle-ci est recreee.
- [ ] REV-ANN-24 : garder les cotes existantes et les etiquettes, verifier leurs textes non chevauches.
- [ ] REV-ANN-25 : verifier pour une piece biaisee qu'aucune direction artificiellement orthogonale n'est forcee.


## Correctif après essai du niveau 1 — 22 octobre 2026

**Retour :** 63 cotes créées sur 44 pièces dans `Collectifs A_Niveau 1`.
Les WC et celliers ont des cotes manquantes ; les balcons et loggias
avec séparation de pièce indiquent parfois `aucune arête de sol superposée
fiable` (2237 à 2240). Plusieurs petites pièces (2249, 2251, 2252)
indiquent `0 texte(s) dans piece` malgré une recherche complète.

**WC, celliers et petites pièces :** le texte de cote est placé dans la
pièce en priorité. Si cette position est impossible, une cote native
entre les mêmes faces finies peut être créée avec son texte
**partiellement hors de la Room**, à condition que sa représentation
estimée ne chevauche pas une étiquette ou une autre cote.
Le rapport indique `texte de cote partiellement hors piece faute de place`
et demande une vérification graphique.

**Balcons/loggias :** toujours utiliser la méthode de Plans de vente :
limite de la Room en `Finish` -> recherche d'arête réelle de dalle
superposée à la séparation -> référence native de l'arête Revit.
Le parcours expérimental de dalles sur des niveaux voisins est **désactivé** après un crash natif signalé dans Revit ; la recherche reste limitée au moteur canonique de Plans de vente. Si aucune arête valide n'existe, la séparation
reste le dernier recours historique (avec avertissement de visibilité),
et aucune fausse mesure n'est générée.

**Aucun changement dans le moteur Plans de vente validé.** L'adaptateur
des boutons Annotations est seul enrichi.

### Recette complémentaire (copie de maquette)

- [ ] REV-ANN-26 : WC/cellier de largeur inférieure au gabarit de texte ;
      placer les deux dimensions si leurs textes ne chevauchent rien.
- [ ] REV-ANN-27 : garder une étiquette ou une cote voisine qui interdit
      un placement de repli : ne jamais forcer le chevauchement.
- [ ] REV-ANN-28 : balcon dont la dalle est au même niveau : référence
      d'arête PDV inchangée.
- [ ] REV-ANN-29 : balcon dont la dalle est sur niveau proche : référence
      native d'arête retrouvée et cotation toujours visible avec les
      séparations de pièces masquées dans la vue.
- [ ] REV-ANN-30 : absence d'arête réelle dans le modèle : avertissement
      de séparation, ne pas inventer de référence ou cote fictive.
- [ ] REV-ANN-31 : vérifier que les cotes existantes ne sont pas dupliquées
      après relancement et que les groupes de détails attachés restent
      hors de la validation tant que la recette dédiée n'est pas faite.


## Arrêt de sécurité après crash Revit — 22 octobre 2026

**Incident :** Revit 2025.4 se ferme brutalement au lancement du
bouton Cotation après le correctif balcons/WC. Aucun journal de crash
n'a encore été analysé. L'extraction supplémentaire de géométrie
`_nearby_floor_edges` constitue un **suspect prioritaire**, mais la
cause du crash n'est pas confirmée.

**Mesures appliquées dans cette bêta :**

1. Retrait complet de la recherche expérimentale des solides des
   planchers rattachés à un niveau voisin. La méthode de Plans de vente
   est de nouveau l'unique propriétaire des références d'arêtes de dalle.
2. **Mode diagnostic obligatoire** : une vue et une seule pièce **hors groupe**
   explicitement sélectionnées. Les traitements de masse, multi-vues
   et les groupes de détails attachés sont bloqués pour la cotation.
   Ce garde-fou sera levé uniquement après validation réelle.
3. Avant chaque traitement de cotation, écriture d'un journal persistant
   dans `%TEMP%\OutilsTAA_Annotations_crashtrace.log`, avec l'étape,
   la vue et le numéro de la pièce. Il est flushé et fermé avant l'API
   susceptible de faire tomber le processus Revit.
4. Le repli de positionnement du texte pour les petites pièces
   reste présent dans les fonctions géométriques Python, mais doit
   être revalidé progressivement sur une copie.

**Procédure de recette à suivre :**
- [ ] Récupérer le journal Revit du crash initial
  (`%LOCALAPPDATA%\Autodesk\Revit\Autodesk Revit 2025\Journals`,
  chemin à vérifier sur le poste).
- [ ] Choisir une copie de projet, une vue et une petite pièce simple.
- [ ] Tester une seule pièce, puis transmettre le rapport pyRevit et
  le fichier `%TEMP%\OutilsTAA_Annotations_crashtrace.log`.
- [ ] Identifier la phase exacte si le processus se ferme encore.
- [ ] Recetter les balcons avec la méthode PDV sans recherche élargie.
- [ ] Revenir à un mode multi-pièces uniquement après validation et
  contrôle des risques en Revit 2025.4.

**Ne pas annoncer de correction de crash confirmée ni fusionner dans
`main` avant enquête et recette réelle.**


### Premier essai après le retrait du parcours risqué des planchers

**Retour réel Revit 2025.4 (22 octobre 2026) :** une pièce hors groupe sélectionnée dans `Collectifs A_Niveau 0`, numéro **1170** ; **2 annotations créées** dans une vue, sans crash signalé. Le rapport contient `1170 : proximite avec un equipement (controle recommande)`.

- [x] REV-ANN-32 — Une pièce, traitement de cotation terminé sans crash signalé ; deux annotations natives annoncées par pyRevit.
- [x] REV-ANN-33 — Capture de la loggia 1170 (`Collectifs A_Niveau 0`) : deux cotes perpendiculaires graphiquement cohérentes, **3,12 m × 3,62 m**, aucun recouvrement évident sur la capture. Validation des références réelles et de la pérennité à poursuivre.
- [ ] REV-ANN-34 — Examiner `%TEMP%\OutilsTAA_Annotations_crashtrace.log` : présence de `BEFORE_DIMENSION_ENGINE`, `AFTER_DIMENSION_ENGINE`, `ROOM_COMMITTED`, `RUN_END` pour la pièce 1170.
- [ ] REV-ANN-35 — Avant retour au mode multi-pièces, réessayer un autre profil de pièce sur une copie, avec la même surveillance du journal ; ne pas réactiver automatiquement la cotation multi-vues.

**Portée du résultat :** succès fonctionnel du lancement d'une pièce, non validation de la qualité graphique, de l'absence de collision, des balcons, des groupes attachés ou de la stabilité à grande échelle.


### Deuxième essai isolé après crash — loggia 2238

**Retour utilisateur du 22 octobre 2026 :** dans `Collectifs A_Niveau 1`, la cotation isolée de la pièce **2238** a créé **2 annotations**, commande terminée sans crash signalé. Le rapport contient :

- `2238 : aucune arête de sol superposée fiable n'a été trouvée pour une séparation de pièce utilisée par une cote. La cote peut disparaître si les séparations sont masquées dans la vue.`
- Deux avertissements de proximité avec un équipement.

**Distinction des preuves :** les premières captures montrent la pièce **1170 au niveau 0** (3,12 m / 3,62 m). Une capture supplémentaire a été reçue pour la pièce **2238 au niveau 1**, également cotée **3,12 m / 3,62 m**. Les deux jeux de cotes sont visuellement cohérents et sans chevauchement manifeste du texte. Cette validation visuelle ne démontre toutefois pas que les cotes 2238 restent visibles si leurs références de séparation de pièce sont masquées.

**Analyse :** le moteur canonique Plans de vente n'a pas trouvé de référence native d'arête de plancher fiable pour une limite de 2238 et a utilisé une séparation de pièce. La dimension peut alors dépendre de la visibilité de cette catégorie. La proximité d'équipement est un avertissement conservateur, pas une collision prouvée.

- [x] REV-ANN-36 — Lancement unitaire de 2238 : 2 cotes créées, aucun crash signalé.
- [x] REV-ANN-37 — **ÉCHEC confirmé par l'utilisateur :** les deux cotes de 2238 disparaissent lorsque la catégorie des séparations de pièces est masquée. Référence native de séparation incompatible avec l'objectif.
- [x] REV-ANN-38 — Capture rapprochée de 2238 examinée : 3,12 m × 3,62 m, directions distinctes, sans chevauchement évident du texte ; références de séparation à valider.
- [ ] REV-ANN-39 — Vérifier le traceur `%TEMP%\\OutilsTAA_Annotations_crashtrace.log` pour les deux essais : `ROOM_COMMITTED` et `RUN_END`, puis évaluer s'il est prudent d'élargir le diagnostic à un WC ou cellier.

**Décision :** ne pas restaurer la recherche expérimentale des solides des planchers ni le traitement multi-pièces sur la seule base de ces deux essais isolés. Le service Plans de vente stable demeure inchangé.


### Correction de la référence des loggias — test à effectuer

La disparition de **3,12 m** et **3,62 m** lors du masquage des
séparations de pièces a été reproduite par l'utilisateur sur la loggia
2238. Le problème est lié à la **référence native choisie** et pas au
positionnement graphique des cotes.

**Nouvelle stratégie bêta, sans modification de Plans de vente :**
lorsque le service canonique ne trouve ni mur ni arête de dalle
fiable et retourne une référence \`separator\`, l'adaptateur crée de
très courtes lignes de détail 2D de 5 mm au droit des limites
sélectionnées. La cotation porte alors sur
\`DetailCurve.GeometryCurve.Reference\`, pas sur
\`RoomSeparation.GeometryCurve.Reference\`. Le style graphique reste
celui choisi au lancement. Les murs et véritables arêtes de dalle
restent les références prioritaires. Aucun parcours additionnel des
solides de dalle n'est réactivé après le crash.

**Limites :** ces repères de 5 mm sont des annotations 2D de la
vue, **non associatives** à la dalle ou au mur, et doivent rester
visibles pour que la cote demeure visible. Il ne faut donc pas
masquer leur style/catégorie avec les séparations. Une correction
manuelle peut être nécessaire après changement de géométrie.
Les lignes inutilisées sont supprimées ; échec global si aucun
repère ne peut servir. Les anciennes cotes déjà placées sur des
séparations **ne sont pas automatiquement réassociées**.

**Essai ciblé sur une copie du projet :**
1. Rendre à nouveau visibles les séparations de pièces.
2. Supprimer **manuellement les deux anciennes cotes de 2238**
   (ne pas supprimer les séparations ni les étiquettes).
3. Mettre à jour la branche \`feature/annotations-automatiques-beta\`,
   redémarrer Revit, et choisir le mode diagnostic **une vue / une pièce**.
4. Refaire la cotation de 2238 avec un style de ligne 2D **visible**
   dans la vue.
5. Masquer uniquement la catégorie **Séparations de pièces**, en
   conservant visible le style de détail 2D, puis vérifier que
   les cotes **3,12 m et 3,62 m** restent toutes deux visibles.
6. Réafficher les séparations ; relancer une seconde fois pour
   contrôler l'absence de cotes en double.
7. Transmettre le rapport et le journal
   \`%TEMP%\OutilsTAA_Annotations_crashtrace.log\`.

- [ ] REV-ANN-40 — La création de cotation par référence 2D fonctionne
      dans Revit 2025.4, sans erreur ni crash.
- [ ] REV-ANN-41 — Les deux cotes de la loggia 2238 restent
      visibles lorsque les séparations de pièces sont masquées
      (et les lignes de détail visibles).
- [ ] REV-ANN-42 — La seconde exécution ne duplique pas les cotes
      déjà référencées à des lignes de détail.
- [ ] REV-ANN-43 — Une seule dimension possible ne laisse
      pas de détail 2D orphelin.


### Consolidation du moteur de références commun (bêta)

La stratégie de sélection des dalles est désormais unique, hébergée
dans `OutilsTAA.extension/lib/common/floor_reference_policy.py` et
utilisée par le service natif de **Plans de vente** ainsi que par
**Cotation automatique**. L'extraction des arêtes de solides et
`segment_match_metrics` restent les mêmes méthodes natives : aucun
second parcours indépendant des solides n'a été introduit.

- **Plans de vente** reste en mode `legacy` : mêmes supports que
  précédemment ; sa version stable sur `main` n'est pas modifiée.
- **Cotation automatique**, en mode `local`, examine uniquement les
  dalles dont les emprises XY croisent la pièce (avec 300 mm de marge),
  sur le niveau de la pièce et sur les niveaux voisins déjà retenus
  par l'altitude (tolérance de 500 mm). Maximum **6 dalles** ;
  aucune extraction géométrique si le budget est dépassé ou si la
  bbox de la pièce est indisponible. Cache distinct pour chaque Room.
- La priorité demeure **arête native de dalle**, ensuite **repère
  de détail 2D de 5 mm**, et jamais référence de séparation définitive
  pour les nouveaux essais de Cotation automatique. Les repères 2D
  sont non associatifs avec les éléments constructifs.

**Recette sur copie du projet Revit 2025.4 :**

- [ ] REV-ANN-44 : après suppression manuelle des deux anciennes cotes
      de 2238, relancer Cotation automatique en mode diagnostic (une
      seule vue, une seule pièce), sans masquer les séparations.
- [ ] REV-ANN-45 : vérifier 3,12 m et 3,62 m, puis masquer
      `Séparations de pièces` : les deux cotes doivent rester visibles.
- [ ] REV-ANN-46 : relancer une seconde fois sans doublon ;
      relever les étapes `FLOOR_CANDIDATES`, `ROOM_COMMITTED`
      et `RUN_END` dans le journal TAA.
- [ ] REV-ANN-47 : identifier si les références de 2238 sont des
      **arêtes natives** ou des **repères 2D**, notamment si le
      budget de six planchers déclenche le fallback.
- [ ] REV-ANN-48 : ne pas rouvrir les traitements multi-vues,
      multi-pièces ou groupes sans validation explicite de stabilité.

Ce changement est **non validé dans Revit** ; les tests unitaires
et CI ne remplacent pas la recette. Voir BUG-COMMON-011.


### Amélioration du fallback des loggias — garde-corps avant repère 2D

Après l'essai de 2238 (deux cotes 3,12 m / 3,62 m, références
`reperes 2D utilises`), la hiérarchie des références a été
complétée sur la branche de test :

1. **Faces finies de murs** lorsqu'elles délimitent réellement la pièce.
2. **Arête native de la dalle**, recherchée par le moteur partagé de
   Plans de vente, avec recherche locale par pièce pour Annotations.
3. **Arête native de garde-corps Revit**, uniquement si un
   `DB.Architecture.Railing` visible, proche de la pièce et avec
   une arête suffisamment colinéaire à la limite (20 mm, 3°, 60 %).
   Il ne s'agit **pas de l'axe théorique** du garde-corps ; son nu
   intérieur devra être contrôlé visuellement.
4. **Repère 2D de 5 mm** (non associatif) si les références natives
   sont indisponibles ou refusées.

**Protection contre le crash précédent :** recherche des garde-corps
limitée à la vue active, aux ouvrages situés à moins de 150 mm en plan
de l'emprise de la pièce, à deux garde-corps et à 120 arêtes
examinées. Dépassement => fallback 2D. Mode une seule pièce par
lancement maintenu. Aucune reprise du traitement en masse.

**Interprétation réglementaire :** la SHAB exclut balcons et loggias
(CCH, R.156-1) ; les loggias peuvent entrer dans la surface annexe
(arrêté du 9 mai 1995 modifié). Ces textes ne prescrivent pas
universellement le nu du garde-corps comme limite de mesurage.
Le cas échéant, la limite au nu intérieur est une règle métier
du projet à vérifier. Références :
- https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000043819221
- https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006831202

**Recette Revit 2025.4 à faire sur copie :**

- [ ] REV-ANN-49 : pièce 2238, garde-corps réellement modélisé,
      vérifier qu'une **arête native** est sélectionnée, sans
      déplacement de la cote par rapport à la limite intérieure.
- [ ] REV-ANN-50 : masquer les séparations : conserver les deux cotes
      si leur référence est une dalle, un garde-corps visible ou 2D.
- [ ] REV-ANN-51 : garde-corps absent/inexploitable : repère 2D
      conservé, sans saut silencieux vers la séparation.
- [ ] REV-ANN-52 : contrôler la stabilité Revit, la seconde
      exécution sans doublon et la présence du journal
      `%TEMP%\\OutilsTAA_Annotations_crashtrace.log`.


### Affinage du filtre garde-corps — après essai 2238 du 22/10/2026

**Retour réel :** 2 cotes natives créées (3,12 m et 3,62 m), sans
plantage signalé ; cependant la recherche garde-corps a été
abandonnée avec `plus de deux garde-corps proches`. Le module
est revenu aux `repères 2D`, signalés non associatifs.

**Explication :** le filtre comptait tous les garde-corps dont la
boîte englobante traversait la **pièce entière**. Plusieurs objets
voisins pouvaient ainsi atteindre le seuil de sécurité, sans être
pertinents pour une des deux grandes dimensions.

**Nouveau filtrage :** les garde-corps visibles passent d'abord un
filtre d'emprise XY, puis leur **trajet Revit** (`Railing.GetPath`)
est comparé **seulement aux segments de séparation choisis par le
moteur de dimensions**. Le trajet sert à présélectionner les ouvrages ;
il n'est jamais référencé pour coter. Seules les vraies arêtes des
solides des garde-corps retenus peuvent fournir une référence
native valide (`Edge.Reference`), sous les critères précis
du moteur existant. Si aucune arête fiable n'est trouvée, les
repères 2D de 5 mm restent le dernier recours.

**Protections :** 24 garde-corps au maximum après filtre d'emprise,
80 segments de chemin, puis 2 garde-corps et 120 arêtes natives
examinées au maximum. Dépassement, chemin indisponible ou doute
géométrique : fallback 2D, **sans** exploration supplémentaire
des solides. Le mode diagnostic à une seule pièce n'est pas
supprimé.

**Test requis sur copie :** la loggia 2238, ancien jeu de cotes
supprimé manuellement ; relancer Cotation automatique après mise
à jour Git, puis observer dans le rapport :
- `1 garde-corps retenu par leur chemin` ou `2 garde-corps retenus`
  si un chemin longe réellement les séparations de cette loggia ;
- `arete native de garde-corps utilisee` **seulement si** une vraie
  arête coïncide avec la limite à 20 mm, sous 3° et recouvrement
  supérieur à 60 % ; sinon `reperes 2D utilises`;
- vérifier les deux cotes après masquage de la catégorie
  `Séparations de pièces`, la visibilité du garde-corps ou du
  style des repères restant conservée ;
- deuxième lancement : pas de doublon, même si les références
  proviennent d'un garde-corps.

Cette correction n'a pas encore été exécutée dans Revit 2025.4.
Voir BUG-COMMON-013.


### Limitation du parcours des arêtes — correctif après l'essai de 2238

**Retour réel Revit :** deux cotes créées pour 2238 ; deux garde-corps
retenus par leur chemin, mais les 120 arêtes ont été examinées avant de
trouver une référence admissible. Le module est donc resté sur ses
repères 2D non associatifs.

**Cause :** le garde-corps parent peut contenir de nombreux poteaux,
barreaux et rails discontinus. L'exploration de ses solides épuise le
budget avant les grandes arêtes utiles.

**Nouvelle règle :** après filtrage par `Railing.GetPath()`, la recherche
interroge les éléments filants natifs `Railing.TopRail` et
`Railing.GetHandRails()`, et non la géométrie complète du parent.
Seuls leurs solides directs et arêtes rectilignes horizontales pourvues
d'une référence Revit originale peuvent être candidats. Pas de
`GetInstanceGeometry()` susceptible de produire des références copiées
impropres aux cotes natives. Le budget maximal reste fixé à **120
arêtes examinées** ; si les composants filants sont absents ou non
exploitables, le repère 2D demeure le secours sûr.

**Attention :** ce nouveau chemin doit encore être testé dans Revit ;
un garde-corps peut être modélisé sans rail supérieur ni main courante
accessible. Une arête native existante n'est pas nécessairement admise
comme référence de cote par Revit.

- [ ] REV-ANN-53 — Sur une copie, relancer la seule loggia 2238 et vérifier
      que le rapport indique `rail(s) filant(s), ... aretes inspectees`.
- [ ] REV-ANN-54 — Vérifier si `arete native de garde-corps utilisee`
      apparaît ; sinon confirmer que `reperes 2D utilises` reste valide.
- [ ] REV-ANN-55 — Masquer les séparations de pièces sans masquer les
      supports de cote ; contrôler la visibilité des deux cotes.
- [ ] REV-ANN-56 — Aucun doublon au second lancement et aucune fermeture
      de Revit ; conserver le diagnostic sur une seule pièce.
