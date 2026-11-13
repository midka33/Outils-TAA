# Outils TAA — Cotation automatique et Étiquetage automatique

**État : bêta en validation Revit ; pièces témoins 2238 et 2240 validées, mode appartement nouvellement développé et à recetter.**
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


### Recherche dans GeometryInstance des rails filants — recette 2238

**Retour Revit du 22/10/2026 :** `2 garde-corps retenu(s)` ; puis `1 rail(s) filant(s), 0 aretes inspectees, 0 reference(s) candidate(s)`. Les deux cotations 3,12 et 3,62 m existent toujours grâce aux reperes 2D non associatifs.

**Point technique :** le parcours precedent ne visitait que les `DB.Solid` au premier niveau de la geometrie d'un TopRail / HandRail. Les solides places dans une `GeometryInstance` etaient ignores. Cette hypothese est coherente avec les zero aretes observees, mais la structure du vrai composant 2238 n'est pas encore verifiee.

**Changement de la beta :** la geometrie des seuls TopRail et HandRail deja selectionnes est analysee aussi dans les `DB.GeometryInstance` (deux niveaux au maximum). L'API `GetSymbolGeometry()` **sans argument** restitue la geometrie originale et les references Revit exploitables ; les points sont transformes dans le repere maquette avec `GeometryInstance.Transform.OfPoint`. **Ne pas employer** `GetInstanceGeometry()` ni `GetSymbolGeometry(Transform)` pour construire une cote : ces methodes retournent une copie dont les References ne sont pas valables pour la creation d'une cote native.

Les protections sont conservees : maximum deux garde-corps, maximum 64 objets geometriques par rail, profondeur deux instances, et **120 aretes examinees au total**. Une geometrie absente, inaccessible, trop complexe ou une reference non acceptee laisse le fallback 2D. L'option de detail est `Medium` pour les composants filants uniquement. Aucun parcours de la geometrie du garde-corps parent n'est retabli.

**Nouveau rapport :** chaque rail examine indique le nombre d'instances, de symboles, de solides directs et de solides symboliques trouves, puis le total des aretes et references candidates. Le journal persistent signale toujours `GUARDRAIL_COMPONENT_BEFORE` et `GUARDRAIL_COMPONENT_AFTER`.

**Recette sur copie** : supprimer uniquement les deux anciennes cotes de 2238, actualiser la branche et redemarrer Revit, puis coter la seule piece 2238. Verifier les nouvelles lignes de rapport et les cotes 3,12 / 3,62 m ; masquer les separations tout en gardant visibles garde-corps et reperes 2D ; controler l'absence de doublons a la relance.

- [ ] REV-ANN-57 — Rapport 2238 indiquant la nature effective de la geometrie du rail filant (Solid / GeometryInstance).
- [ ] REV-ANN-58 — Cote appuyee sur une reference symbolique native effectivement acceptee par Revit, si disponible.
- [ ] REV-ANN-59 — Validation de la stabilite Revit et des cotes masquees / remises visibles sur copie de maquette.


### Nouvelle règle métier des annexes extérieures — tolérance de modèle (22/10/2026)

**Décision métier :** pour une pièce désignée `loggia`, `balcon`,
`terrasse` ou `jardin`, ou classée `Int/Ext = Ext`, les références
de cotation doivent être sélectionnées dans l'ordre suivant :

1. **Faces finies de murs existants** qui délimitent l'annexe.
2. **Arêtes géométriques natives des garde-corps Revit**, sur les
   limites sans mur, si orientation et couverture correspondent
   réellement à la limite extérieure. Ne jamais coter sur l'axe
   théorique du chemin de garde-corps.
3. **Petite ligne de détail 2D de 5 mm**, dernier recours indépendant
   des séparations de pièces, non associatif.

Pour ces annexes, les arêtes de dalle **ne sont plus utilisées
comme référence de substitution**, contrairement au comportement
de Plans de vente conservé sur la branche `main`. Cette règle
spécifique de Cotation automatique remplace la hiérarchie
`mur / dalle / garde-corps / 2D` décrite dans les chapitres
antérieurs pour **les annexes extérieures seulement**. Les pièces
intérieures gardent leurs règles précédentes.

**Tolérance de rattrapage géométrique :** une séparation de pièce peut
être décalée de 35 mm par rapport au vrai garde-corps du projet 2238.
Au lieu d'imposer partout la tolérance stricte de 20 mm, Cotation
automatique accepte pour les annexes extérieures un **écart maximal de
50 mm**, tout en conservant l'écart angulaire maximal de **3°** et le
recouvrement minimal de **60 %**. L'écart mesuré est indiqué dans
le rapport ; au-delà de 20 mm, le rapport demande explicitement un
**contrôle manuel** du nu et de la valeur. La cote doit suivre
**la vraie référence Revit**, pas reproduire artificiellement la
largeur calculée entre les séparations ; sa valeur peut donc différer
de 3,12 m ou 3,62 m dans une loggia dont les limites sont décalées.

**Protection :** ce relâchement de tolérance n'est jamais appliqué
aux pièces intérieures. Les garde-corps lointains, biaisés, trop courts
ou non cotables restent refusés. Les limites de sélection et de
géométrie des garde-corps, le journal de crash et le mode diagnostic
**une seule pièce hors groupe par essai** restent actifs.

**Nouveau diagnostic :** quand aucune arête n'est admissible, le
rapport indique le meilleur écart réel, l'angle, le pourcentage de
recouvrement et les motifs du rejet. Aucun objet géométrique
supplémentaire n'est analysé pour ce diagnostic.

**Recette Revit sur copie de maquette :**
- [ ] REV-ANN-60 : loggia 2238, supprimer les deux anciennes cotes et
      relancer sur une pièce après mise à jour de la branche.
- [ ] REV-ANN-61 : constater si une arête native de garde-corps est
      retenue avec un écart environ 35 mm et identifier le **nu réellement
      coté**. Si la valeur diffère de l'ancienne cote, vérifier la
      mesure réelle et ne pas imposer l'ancienne valeur.
- [ ] REV-ANN-62 : masquer les séparations tout en gardant visible
      le garde-corps ou le repère de détail : les cotes doivent rester.
- [ ] REV-ANN-63 : relancer sans créer de doublon ; vérifier le fichier
      `%TEMP%\\OutilsTAA_Annotations_crashtrace.log` si incident.


### Correction du filtre amont des garde-corps de 2238 — 22 octobre 2026

**Nouvel essai utilisateur :** deux dimensions produites, une cote
manuelle supplémentaire indique un écart d'environ **0,04 m**
entre séparation et garde-corps. Le rapport indique
`aucun garde-corps avec chemin suffisamment proche des limites a coter
(ou recherche ambigue)`. Cette sortie ne démontre pas qu'aucun ouvrage
ne correspond ; l'ancien filtre ne distinguait pas une absence
géométrique d'un excès de candidats.

**Cause dans le moteur précédent :** il arrêtait tous les candidats
dès que plus de **deux garde-corps** longeaient au moins une des
limites sélectionnées. En supprimant la substitution par dalle
pour les annexes extérieures, davantage de séparations ont été
présentées au filtre ; un garde-corps pertinent pouvait alors être
écarté avec tous les autres.

**Modification bêta :** les chemins `Railing.GetPath()` sont désormais
classés **indépendamment pour chaque limite** ; au maximum un garde-corps
par limite et deux ouvrages au total accèdent aux géométries natives.
Lorsque les deux meilleurs scores sur une même limite se suivent à
moins de **25 mm**, cette limite est ambiguë et le repère 2D est
conservé (l'autre limite peut encore être cotée nativement).
La marge **500 mm** pour présélectionner le *chemin* ne doit pas
être confondue avec la tolérance **50 mm maximum** pour sélectionner
l'*arête native* d'une annexe extérieure. Cette dernière reste
soumise au critère d'angle maximal 3° et au recouvrement d'au moins 60 %.

**Nouveau rapport détaillé :** le module signale
`filtrage GC : N chemin(s) dans la piece, M limite(s),
P correspondance(s), A ambigue(s), plus proche D mm, statut S`.
Les valeurs de `S` distinguent `selected`, `no_match`,
`ambiguous`, `partial_ambiguity`, `path_budget` et
`rail_budget`. Aucun solide supplémentaire n'est lu pour
produire ces compteurs.

**Recette ciblée Revit 2025.4 (sur copie uniquement)** :
- [ ] REV-ANN-64 — Supprimer manuellement les deux anciennes cotes
      de 2238, mettre à jour la branche puis relancer une fois
      le mode une vue / une pièce.
- [ ] REV-ANN-65 — Fournir la ligne `filtrage GC` et vérifier la
      présence d'un garde-corps réellement retenu (ou l'ambiguïté
      détaillée).
- [ ] REV-ANN-66 — Si une arête est retenue, vérifier la valeur de
      cote réelle et le décalage proche des 40 mm relevés manuellement.
- [ ] REV-ANN-67 — Masquer les séparations et contrôler que les cotes
      restent visibles, puis relancer sans doublon ni crash.


### Deux garde-corps jointifs pour une seule limite — loggia 2238

**Observation Revit 2025.4 (22 octobre 2026) :** la loggia 2238 possède
**deux garde-corps successifs**, occupant approximativement la moitié
de la même limite extérieure. Le précédent rapport indiquait une
meilleure arête de **52 % de recouvrement**, **15 mm d'écart** et
**0° d'angle** ; ce tronçon était refusé car il couvrait moins que
les 60 % demandés. Les autres arêtes n'avaient pas encore été
considérées **collectivement** pour démontrer la continuité.

**Règle corrigée pour les annexes extérieures :**

1. Une référence native individuelle doit encore couvrir **60 %**
   au minimum de la limite, conformément à la règle historique.
   **Le seuil n'est pas abaissé à 50 % pour une arête isolée.**
2. Si une arête seule ne suffit pas, deux garde-corps natifs distincts
   peuvent être vérifiés ensemble : projection colinéaire à 3° près,
   chaque arête à 50 mm maximum de la limite, chaque portion à
   25 % minimum, recouvrement cumulé **90 % minimum**, raccordement
   à 100 mm maximum, décalage entre les deux rails de 20 mm maximum,
   altitude à 150 mm maximum, pas de deux arêtes quasi superposées.
3. Si le raccordement est vérifié, la cote utilise **la référence Revit
   d'un seul des deux rails**, jamais une ligne fictive calculée à
   partir de leur somme. L'autre rail prouve la continuité du bord.
   **La cote n'est pas liée aux deux rails** : le contrôle après
   modification de l'un ou de l'autre reste obligatoire.
4. Si la continuité ne peut pas être établie ou si la référence
   native est refusée, utiliser le repère 2D non associatif déjà prévu.

**Diagnostic attendu :**
`2238 : DEUX garde-corps contigus identifies : couverture commune
...%, jeu ... mm, decalage entre rails ... mm`, suivi de l'indication
de référence native utilisée. Les faces finies de murs restent
prioritaires ; la règle ne concerne que les annexes extérieures et
ne modifie pas Plans de vente stable.

**Recette sur copie de maquette :**
- [ ] REV-ANN-68 : après suppression des cotes précédentes,
      relancer sur la seule pièce 2238 ; confirmer les deux cotes et
      la création d'une référence de garde-corps au lieu du
      fallback 2D si la paire réelle satisfait les seuils.
- [ ] REV-ANN-69 : vérifier le cumul des deux tronçons dans le
      rapport (au moins 90 %, raccord de 100 mm maximum) ;
      contrôler la position du nu et la valeur réelle mesurée.
- [ ] REV-ANN-70 : masquer les séparations de pièces en conservant les
      garde-corps et repères 2D visibles, puis relancer pour
      vérifier l'absence de doublons.
- [ ] REV-ANN-71 : conserver le journal
      `%TEMP%\\OutilsTAA_Annotations_crashtrace.log` si un
      nouvel incident Revit apparaît.

**État :** correction et tests Python uniquement ; l'acceptation
des références reste à vérifier dans Revit 2025.4.


### Validation partielle des références natives — pièce 2240 (3 novembre 2026)

**Retour réel Revit 2025.4 :** cotation de **2240** sur
`Collectifs A_Niveau 1`, **2 annotations créées**, sans
message de fallback 2D. Le module détecte quatre chemins de
garde-corps, en retient deux, examine 24 arêtes natives et
retrouve huit références candidates. Il rapporte deux limites
admises sur une vraie référence d'arête : **0,0 mm / 100 %** et
**19,3 mm / 63 %**. L'utilisateur a transmis une capture ; le
contrôle précis de la position au nu intérieur et de la visibilité
après masquage des séparations reste à faire.

**Régression constatée dans le rapport :** chaque message
`arête native de garde-corps utilisée` apparaît **deux fois**,
alors que seules deux dimensions ont été produites. La cause
logicielle confirmée est une seconde résolution des candidats :
`_create_separator_proxies` ne remplissait son cache que
lorsqu'un fallback 2D était nécessaire. En l'absence de
fallback (cas 2240), `create_dimensions` relançait
`_room_boundary_candidates`, et donc les diagnostics de
sélection native.

**Correctif :** remplir le cache de candidats à chaque
premier passage, y compris pour les références entièrement
natives et les listes vides. Le second passage de cotation
consomme les mêmes références. Ce cache reste interne à une
seule exécution de pièce et est nettoyé après la transaction.
Pas de changement des seuils de géométrie ni du moteur PDV.

**Recette Revit sur copie :**
- [ ] REV-ANN-72 — Nettoyer les cotes de l'essai 2240 et
      relancer une seule fois : **deux cotes et seulement deux
      messages d'arêtes natives**, sans fallback 2D.
- [ ] REV-ANN-73 — Contrôler que les deux cotes mesurent le nu
      intérieur attendu et ne se superposent pas avec des cotes
      préexistantes.
- [ ] REV-ANN-74 — Masquer temporairement les séparations de
      pièces, conserver visibles les garde-corps et confirmer
      que les deux cotes restent visibles.
- [ ] REV-ANN-75 — Deuxième lancement sans doublon.
- [ ] REV-ANN-76 — Reprendre la loggia 2238 (deux garde-corps
      contigus) séparément ; son comportement **n'est pas validé**
      par l'essai 2240.

Voir BUG-COMMON-019. Ce correctif a été testé hors Revit,
sa recette dans Revit 2025.4 reste indispensable.


### Règle de sélection entre plusieurs garde-corps — 3 novembre 2026

**Règle métier validée :** lorsqu'il existe plusieurs garde-corps
susceptibles de délimiter une annexe extérieure, choisir la
**référence géométriquement admissible la plus proche** de la
limite de pièce. Si deux candidats ont une distance identique
à **1 mm près**, retenir celui dont le segment de garde-corps
est **le plus long**. Cette comparaison s'effectue après les
contrôles d'alignement, de recouvrement et de référence native
Revit, et non à la place de ces contrôles.

L'ordre est appliqué à la présélection des chemins
`Railing.GetPath`, à la sélection des arêtes natives réelles,
et au choix du rail de référence lorsqu'une paire de
garde-corps **contigus** a été validée. Le second rail de la
paire vérifie la continuité, mais **la cote n'est associative
qu'à la première arête native** : surveiller les deux ouvrages
après modification. Une arête seule ne peut toujours pas
être choisie si son recouvrement est inférieur à 60 % ;
deux arêtes successives restent soumises aux règles de
continuité et couverture totale >=90 %.

Cette règle **remplace** le rejet automatique des scores
presque égaux à 25 mm documenté sous BUG-COMMON-017.
Les candidats plus éloignés ne deviennent pas préférés en
raison de leur longueur. Les budgets de géométrie et le
mode de diagnostic à une seule pièce sont inchangés.

**Tests de recette Revit sur copie :**
- [ ] REV-ANN-77 — Deux garde-corps parallèles : celui dont le
      nu est le plus proche de la limite gagne, même si l'autre
      est plus long.
- [ ] REV-ANN-78 — Deux garde-corps à distance égale
      (tolérance 1 mm) : le plus long fournit la référence.
- [ ] REV-ANN-79 — Deux tronçons successifs sur la même limite
      de 2238 : vérifier la continuité et confirmer quel rail
      est référencé ; contrôler la valeur de cote au nu réel.
- [ ] REV-ANN-80 — Masquer les séparations en conservant les
      garde-corps visibles ; vérifier la stabilité et l'absence
      de cotes doublées au second lancement.

Voir **BUG-COMMON-020**. Tests Python automatisés requis et
validation native Revit 2025.4 encore à effectuer.


**Préservation de la limite composée 2238 :** afin de ne pas
perdre le second tronçon lors de la présélection, un garde-corps
supplémentaire peut être examiné **seulement si son chemin complète
la portion du garde-corps prioritaire** sur une même limite
(couverture totale >=90 %, raccord <=100 mm, décalage latéral
entre rails <=20 mm). Il ne suffit pas d'être le deuxième plus
proche : il doit contribuer à la continuité. Pour les deux
directions de cote dont une limite est composée, le budget est
**trois garde-corps natifs maximum**, sans augmenter le plafond
total de **120 arêtes examinées**. Le filtre peut refuser et
revenir au repère 2D si plus d'ouvrages sont nécessaires.

La priorité proximité puis longueur détermine toujours **la
Reference native utilisée** ; le second garde-corps sert à
valider la continuité géométrique et ne devient pas associatif
à la cote. Les seuils de contrôle des arêtes natives restent
distincts de ceux des chemins de présélection.


### Correctif de la présélection du deuxième tronçon — loggia 2238

**Retour du 3 novembre 2026 :** le rapport voit **3 chemins de
garde-corps et 3 correspondances pour 2 limites**, mais n'en
retient que deux pour la géométrie native. Une première cote
repose sur une arête native à 100 % ; une seconde reste en
2D, l'arête native inspectée ne couvrant que 52 % de la limite.

**Problème :** le préfiltre n'autorisait un deuxième tronçon que
si `Railing.GetPath()` du premier occupait moins de 60 % de
la limite. La longueur de ce chemin peut différer de celle de
l'arête réelle du TopRail qui fournit la référence de cotation.
Le deuxième tronçon était donc potentiellement rejeté trop tôt.

**Correction du préfiltre :** retenir le garde-corps principal
selon **distance puis longueur à égalité (1 mm)**, puis
éventuellement **un deuxième candidat distinct** de la même
limite pour inspection de ses arêtes natives, même si le
chemin du premier semble couvrir la limite entièrement.

**Ce n'est PAS encore une validation de continuité :**
seul le contrôle des **vraies arêtes de TopRail/HandRail**
peut établir que les deux ouvrages sont effectivement
successifs, alignés et couvrent ensemble >=90 % de la
limite, avec un raccord suffisamment proche. Le rapport
annonce donc un `second tronçon à vérifier sur les arêtes`,
puis éventuellement `DEUX garde-corps contigus identifies`
si et seulement si le test natif est concluant.
Au-delà de trois garde-corps à examiner ou de 120 arêtes,
le module revient au repère 2D ; le mode diagnostic sur
une pièce demeure.

**Recette 2238 :**
- [ ] REV-ANN-81 : sur copie, enlever les cotes de l'essai,
      actualiser Git et redémarrer Revit ; lancer sur la seule 2238.
- [ ] REV-ANN-82 : regarder si **3 garde-corps** sont explorés,
      et si le troisième fournit une arête native pertinente.
- [ ] REV-ANN-83 : distinguer « candidat supplémentaire »
      de « paire contiguë validée » ; contrôler le recouvrement
      cumulé, le vrai nu et la cote réelle.
- [ ] REV-ANN-84 : masquer les séparations sans masquer les
      garde-corps, et contrôler les deux cotes.
- [ ] REV-ANN-85 : deuxième lancement sans doublon ni plantage.

Voir **BUG-COMMON-021**. Aucun résultat Revit natif de
cette nouvelle présélection n'a encore été obtenu.


### Troisieme garde-corps sans rail filant accessible — test 2238

**Observation utilisateur (3 novembre 2026) :** le rapport annonce
3 garde-corps retenus, mais seulement **2 rails filants** inspectes.
Un rail natif couvre toute la premiere limite ; la meilleure
arete de la seconde ne couvre que **52 %**, et le deuxieme
troncon n'est toujours pas trouve.

**Diagnostic renforce :** pour chacun des garde-corps candidats,
le rapport indique desormais son **ElementId**, son TopRail,
le nombre de mains courantes, et, lorsqu'aucun rail filant
n'est accessible, le nombre de lisses non continues du
`RailingType.RailStructure`. Cela permet de distinguer un
garde-corps sans TopRail, un composant indisponible et un
type de garde-corps possedant des lisses non continues.

**Recherche native de secours, exceptionnellement :** quand
un seul garde-corps candidat sans filant declare une lisse
non continue, l'adaptateur tente de lire les solides
**directs** du seul `Railing` parent, avec
`Options.ComputeReferences`. Il n'examine aucun
`GeometryInstance` de balustres, ni les objets de
garde-corps voisins. Cette operation reste limitee a
**16 objets directs**, **48 aretes**, **12 references
candidates**, et conserve le plafond global de **120
aretes**. Les references doivent etre natives et leur
segment suffisamment proche de la limite.
En cas d'echec, aucun faux lien n'est invente :
le repli 2D demeure et le rapport precise pourquoi.

**Restriction apres le crash passe :** cette analyse d'un
parent Railing peut etre plus couteuse qu'une lecture
isolee de TopRail ; elle n'est appliquee qu'a un seul
garde-corps de type compatible, en mode diagnostic
**une piece / une vue**, sur copie de maquette.

**Recette REV-ANN-86 a REV-ANN-89 :**
- [ ] REV-ANN-86 — Relancer uniquement 2238 apres suppression
      des cotes precedentes, sur copie et apres mise a jour Git.
- [ ] REV-ANN-87 — Lire le detail des IDs des trois GC :
      confirmer si le troisieme n'a pas de rail filant,
      et si son type declare une lisse non continue.
- [ ] REV-ANN-88 — Si une lisse non continue est trouvee,
      verifier si elle apporte la reference du second troncon,
      et si les deux portions couvrent >=90 % de la limite.
- [ ] REV-ANN-89 — Controle du vrai nu, de la valeur des
      deux cotes, de leur visibilite lorsque les separations
      sont masquees, de l'absence de doublon et de crash.

Voir BUG-COMMON-022. Non valide en environnement Revit natif
au moment de ce changement.


### Couverture cumulée par chemins et référence native unique — 2238

**Nouvelle règle de cotation des annexes extérieures :** deux
garde-corps successifs peuvent fournir **ensemble la preuve de
couverture d'une limite**, même si un seul possède une arête native
exploitable par l'API Revit. L'objectif est de résoudre le cas de
2238 où une arête cotable couvre 52 % et le deuxième garde-corps
représente les 48 % restants.

La décision est **découpée en deux vérifications indépendantes** :

1. **Couverture de la limite** : examiner les segments de
   `Railing.GetPath()` des seuls garde-corps présélectionnés
   (3 éléments maximum). Il faut deux ouvrages distincts,
   des portions successives et non superposées, une **union
   projetée de 90 % minimum**, chaque portion >=25 %,
   angle <=3°, raccord <=100 mm et décalage latéral entre
   chemins <=20 mm. Une addition brute de longueurs n'est
   pas suffisante : deux garde-corps superposés sur la même
   moitié ne satisfont pas la règle. Un chemin entièrement
   superposé avec un deuxième demi-chemin ne permet pas non
   plus de certifier deux portions successives.
2. **Référence native de la cote** : une seule des deux
   portions doit fournir une `Edge.Reference` native
   exploitable, avec une arête parallèle (<=3°), à **50 mm
   maximum** de la limite et couvrant au moins 25 %.
   Elle doit provenir du garde-corps participant à la
   preuve de couverture, et correspondre à son propre
   chemin. Si plusieurs arêtes sont disponibles, choisir
   la plus proche de la limite, puis la plus longue en
   cas d'égalité de distance (1 mm).

Le module utilise **l'arête native pour la valeur Revit
de cotation** : il n'utilise jamais `GetPath()` comme
référence et ne force pas l'ancienne valeur issue des
séparations décalées. La cote n'est associative qu'au
garde-corps qui fournit cette arête. Le second garde-corps
n'est qu'un **contrôle de continuité** et toute évolution
de son tracé impose une vérification de la cote.

**Sécurité et performance :** pour les annexes extérieures,
l'analyse des solides du garde-corps **parent** sans rail
filant est remplacée par ce contrôle de couverture à
partir des chemins déjà lus. Le diagnostic d'ID et de
type de rail est conservé. Les limites existantes restent
fixées à trois garde-corps présélectionnés, 80 tronçons
de chemin, 120 arêtes natives (TopRail/HandRail) ; pas
d'extension du parcours de la géométrie parent.
Les pièces intérieures et Plans de vente conservent
leur comportement actuel. En cas d'échec d'une des
conditions, le repère 2D non associatif reste le secours.

**Exemple de message attendu si les deux chemins sont
valides :** `2238 : DEUX chemins de garde-corps alignes
couvrent 100% de la limite (jeu 0 mm). Cote associee
UNIQUEMENT a l'arete native du GC ...`.

**Essais Revit 2025.4 indispensables sur copie** :
- [ ] REV-ANN-90 — Loggia 2238 : retirer les deux cotes
      de l'essai précédent, mettre à jour la branche et
      relancer sur une seule pièce.
- [ ] REV-ANN-91 — Vérifier l'union réelle des chemins
      (>=90 %), le bon nu du garde-corps et la valeur
      native de la seconde cote. Si les chemins se
      superposent au lieu de se compléter, le repli 2D
      est la décision attendue.
- [ ] REV-ANN-92 — Masquer `Séparations de pièces`
      en conservant les garde-corps visibles : les
      cotes référencées au garde-corps doivent rester.
- [ ] REV-ANN-93 — Confirmer qu'une deuxième exécution
      ne duplique aucune cote et ne déclenche aucun crash.
- [ ] REV-ANN-94 — Pièce 2240 : vérifier que les deux
      références natives et les diagnostics non doublés
      restent inchangés.

Voir **BUG-COMMON-023**. Tests Python hors Revit possibles,
validation native dans Revit 2025.4 **non encore effectuée**.


### Retour après BUG-COMMON-023 — pièce 2238 (3 novembre 2026)

L'utilisateur a relancé **après** le correctif BUG-COMMON-023. Rapport :
2 annotations dans `Collectifs A_Niveau 1`, pièce 2238 hors groupe,
**3 GC présélectionnés**, 2 TopRail accessibles, 24 arêtes inspectées,
8 références candidates, et un troisième GC sans TopRail (4 lisses non
continues). Une limite reçoit une **arête native** (100 % de recouvrement,
écart 0 mm). La seconde limite conserve le repli 2D : meilleure arête
à **15 mm**, angle 0°, mais seulement **52 %** de recouvrement.

**Conclusion : la correction 023 n'est pas validée sur 2238.** Le rapport
ne montre pas de succès `DEUX chemins de garde-corps alignes` :
aucune preuve géométrique complète n'a pu être associée à la seconde cote.
Il serait incorrect d'abaisser le seuil de 60 % ou d'en déduire que les
deux garde-corps se suivent réellement, car le rapport n'indique ni leurs
intervalles projetés ni leur éventuelle superposition.

**Correctif de diagnostic BUG-COMMON-024 (sans changement de cotation) :**
lorsqu'une limite extérieure échoue à la sélection native et au fallback
de continuité, la bêta imprime maintenant :
- IDs de la meilleure paire de garde-corps ;
- position des portions de chaque chemin (pourcentage début-fin de la limite) ;
- couverture par **union**, superposition, jeu et décalage ;
- raison précise du rejet : chevauchement >10 %, couverture <90 %,
  raccord >100 mm, écart latéral >20 mm, angle, portion trop courte,
  extrémité non couverte, ou chemins compatibles sans arête native associable.

Les chemins sont **déjà extraits** et le diagnostic ne lit aucun solide
ni élément supplémentaire. Les plafonds restent à 3 GC, 80 segments,
120 arêtes ; aucun changement des `Reference` Revit ni de la logique
de repli 2D. Ce résultat ne valide **pas** l'associativité de la seconde
cote et ne modifie pas Plans de vente.

**Recette ciblée suivante (sur copie du modèle)** :
- [ ] REV-ANN-95 — Mettre à jour `feature/annotations-automatiques-beta`,
      supprimer les cotes et repères 2D précédents de 2238 et relancer
      uniquement la pièce 2238.
- [ ] REV-ANN-96 — Transmettre la ligne
      `2238 : diagnostic continuité GC ...` et le rapport complet ; décider
      à partir des **portions réellement projetées** si les deux chemins
      sont successifs, superposés ou disjoints.
- [ ] REV-ANN-97 — Si les chemins sont géométriquement compatibles mais
      la référence native rejetée, examiner la correspondance rail/parent
      et la position du nu avant toute nouvelle correction.
- [ ] REV-ANN-98 — Vérifier la pièce 2240 (deux références natives) sans
      nouveaux repères 2D ni messages dupliqués, puis la stabilité sur un
      second lancement.

**Statut : diagnostic ajouté sur la branche bêta ; test utilisateur
Revit du diagnostic en attente.** Voir BUG-COMMON-024.


### Récupération bêta des axes de garde-corps décalés — 2238 (3 novembre 2026)

**Rapport utilisateur post-BUG-COMMON-024 :** trois garde-corps détectés.
Les chemins des GC `8951804` et `16141871` couvrent ensemble
**100 %** de la seconde limite de la pièce **2238** : l'un
**52–100 %**, l'autre **0–52 %**, sans trou ni superposition.
Leur implantation latérale diffère toutefois de **33 mm**,
ce qui dépasse le seuil courant de **20 mm**. L'axe le plus
éloigné est à 58 mm de la séparation ; une vraie arête native
est à **0 mm** et couvre **52 %** de cette même séparation.
L'ancienne décision `decalage_lateral` expliquait donc le
repli 2D, mais ne constituait pas à elle seule la preuve
que les **nus réels** diffèrent de 33 mm.

**Exception d'essai encadrée — BUG-COMMON-025 :** le mode
diagnostic bêta permet maintenant de récupérer l'arête native,
sans assouplir la règle ordinaire, uniquement si **tous** les
points suivants sont respectés :
- chemins longitudinaux distincts, du même côté de la
  séparation, angle <=3°, union >=98 %, superposition <=2 % ;
- raccordement longitudinal <=10 mm ;
- décalage entre axes dans ]20 ; 40] mm et distance de
  chaque axe à la séparation <=60 mm ;
- arête native d'un des deux garde-corps à <=5 mm de la
  séparation, parallèle, couvrant >=25 % et réellement liée
  au bon parent `TopRail` ou `HandRail` ;
- aucun dépassement des budgets existants : 3 GC,
  80 segments de chemins et 120 arêtes.

Une nouvelle ligne du rapport doit signaler :
`RECUPERATION BETA du GC malgre axes decales de 33 mm`.
**La cote ne devient pas associative aux deux garde-corps** :
elle reste uniquement associée au rail fournissant
l'`Edge.Reference` native.

**Attention :** la tolérance sur les axes ne garantit **pas**
l'alignement des faces ni du nu intérieur. Ce cas ne doit pas
être déclaré validé avant vérification manuelle sur copie,
à l'échelle du modèle, de la valeur réelle de la cote,
de l'alignement des deux nus et de la stabilité de la cote
lorsqu'on masque les séparations de pièces.

**Recette à effectuer :**
- [ ] REV-ANN-99 — Mettre à jour la branche bêta, supprimer
      les cotes précédentes de la loggia 2238, recharger pyRevit
      et relancer uniquement cette pièce en vue
      `Collectifs A_Niveau 1`.
- [ ] REV-ANN-100 — Confirmer une ligne `RECUPERATION BETA`,
      deux cotes de longueur réellement correcte, et **aucun
      repère 2D** utilisé pour la seconde limite ; si l'API
      Revit refuse la référence, conserver le diagnostic.
- [ ] REV-ANN-101 — Vérifier que les **nus intérieurs réels des
      deux garde-corps** sont alignés. S'ils sont décalés,
      ne pas considérer la cote produite comme correcte.
- [ ] REV-ANN-102 — Masquer les séparations de pièces,
      vérifier les cotes, relancer une deuxième fois (absence
      de doublons/crash), puis contrôler la pièce 2240.
- [ ] REV-ANN-103 — Seulement après les vérifications ci-dessus,
      décider de conserver, modifier ou retirer cette exception
      bêta avant la fusion éventuelle.

**État :** code et tests hors Revit réalisés. **Validation Revit
en attente**, et les axes `GetPath()` ne sont jamais pris pour
une référence géométrique de cote.


### Retour réel Revit après BUG-COMMON-025 — référence native récupérée (3 novembre 2026)

**Rapport utilisateur reçu après la récupération bêta :** `Cotation automatique - version beta`, vue `Collectifs A_Niveau 1`, pièce **2238** seule, **2 annotations créées**. Trois GC préfiltrés ; deux rails filants inspectés, 24 arêtes analysées et huit références candidates.

- **Première limite :** `arete native de garde-corps utilisee`, écart 0,0 mm et recouvrement **100 %**.
- **Seconde limite :** `arete native de garde-corps utilisee`, écart 0,0 mm et recouvrement **52 %**.
- **Récupération confirmée par Revit :** `RECUPERATION BETA du GC malgre axes decales de 33 mm`, décalage maximal 58 mm, union **100 %**, superposition **0 %**, arête native à 0 mm.
- **Deux chemins reconnus :** couverture 100 %, jeu 0 mm ; la cote ne référence **que le GC 16141871**, qui possède le TopRail 16141873. Le garde-corps complémentaire **8951804** ne pilote pas cette cote.
- **Aucune ligne de repli 2D signalée** dans ce rapport. Deux avertissements identiques de proximité d'équipement restent présents (probablement un par cote ; aucune preuve à ce stade d'un défaut du diagnostic).

**Conclusion vérifiable :** **REV-ANN-99** (nouvel essai ciblé) et **le volet récupération native de REV-ANN-100** sont confirmés par le rapport. La récupération fonctionne dans Revit 2025.4 avec les seuils expérimentaux de BUG-COMMON-025. Le diagnostic n'apporte aucune preuve sur la **justesse de la longueur affichée**, l'alignement des **nus intérieurs réels**, la persistance de la cote après masquage des séparations, l'absence de doublons après une deuxième exécution ou l'absence d'incident sur 2240.

**Vérifications restant obligatoires, sur copie de maquette :**
- [x] **REV-ANN-100 — complément :** utilisateur confirme les deux valeurs correctes et l'absence de repères 2D substitutifs sur la loggia 2238.
- [x] **REV-ANN-101 :** utilisateur confirme que les **nus intérieurs physiques** des GC 16141871 et 8951804 sont alignés malgré le décalage de 33 mm de leurs axes.
- [x] **REV-ANN-102 — partie 2238 :** deux cotes toujours visibles avec `Séparations de pièces` masquées, deuxième lancement sans doublon ni plantage, selon confirmation utilisateur.
- [x] **REV-ANN-102 — non-régression 2240 :** validée le 5 novembre 2026 : deux références natives, contrôle des dimensions/nus, visibilité sans séparations, seconde exécution sans doublon ni crash ; écart de 19,3 mm sur la deuxième arête native, recouvrement 63 %.
- [ ] **REV-ANN-103 :** décision de généralisation / maintien bêta après la non-régression sur 2240 et les autres scénarios critiques.

**Décision :** conserver le **mode diagnostic une pièce/une vue** et **ne pas fusionner dans `main`** sur la seule base de ce rapport. L'associativité native identifie une référence réelle, mais ne garantit pas l'associativité à la totalité de deux ouvrages successifs.


### Confirmation complémentaire de la recette 2238 — 3 novembre 2026

L'utilisateur a répondu **« tout est ok »** aux quatre vérifications proposées après le rapport BUG-COMMON-025 :

1. **Valeurs mesurées :** les deux cotes de la pièce 2238 correspondent aux dimensions intérieures réelles de la loggia.
2. **Nus intérieurs :** alignement physique des deux garde-corps 16141871 et 8951804 confirmé, malgré des axes `Railing.GetPath()` décalés de 33 mm.
3. **Visibilité :** les deux cotes demeurent visibles après masquage de la catégorie **Séparations de pièces**.
4. **Deuxième exécution :** absence de doublon et de plantage rapportée.

**Bilan : BUG-COMMON-025 validé fonctionnellement sur la loggia 2238 en Revit 2025.4.** La preuve repose sur le retour utilisateur et le journal précédent ; aucune capture ou mesure géométrique indépendante n'est archivée. La cote partielle ne reste associative qu'au **GC 16141871**, pas au GC 8951804. La solution demeure **bêta** : la non-régression **2240 a ensuite été validée le 5 novembre 2026**, mais les autres configurations de garde-corps et la recette globale restent nécessaires avant un éventuel merge dans `main`.


### Non-régression après BUG-COMMON-025 — pièce 2240 (5 novembre 2026)

**Retour utilisateur :** validation des contrôles 1, 2, 4 et 5, puis transmission du rapport correct pour la pièce **2240** (le premier rapport copié concernait encore 2238). Vue `Collectifs A_Niveau 1`, une pièce hors groupe, deux annotations créées.

- 3 garde-corps candidats retenus parmi 4 chemins de pièces ; 2 TopRail accessibles et un GC sans TopRail (type à 4 lisses non continues), 24 arêtes examinées, 8 références candidates.
- **Première limite :** arête native de garde-corps retenue, écart **0 mm**, recouvrement **100 %**.
- **Deuxième limite :** arête native retenue par la règle **normale** (aucune ligne `RECUPERATION BETA`), écart **19,3 mm**, recouvrement **63 %** (au-dessus de 60 %). L'écart est la distance entre arête native et limite de pièce, **pas** une erreur déduite sur la valeur de cote ; l'utilisateur a confirmé les dimensions et les nus.
- **Deux cotes visibles** lorsque les séparations de pièces sont masquées, et **aucun doublon ni plantage** au second lancement d'après l'utilisateur.
- **Aucune ligne de repli 2D** dans le rapport fourni ; aucun message de récupération par axes décalés pour 2240.

**Résultat : REV-ANN-102 — non-régression sur 2240 VALIDÉE (5/5).** Avec 2238 validée, le traitement expérimental BUG-COMMON-025 n'a pas perturbé cette configuration auparavant fonctionnelle. **Ne pas assimiler ce résultat à une validation globale de cotation automatique** : les pièces atypiques, la génération multi-pièces, la gestion des groupes et les autres scénarios de risques de la recette bêta restent ouverts. La cote sur deux garde-corps successifs demeure associative à une seule arête native, sans garantie de mise à jour si l'autre garde-corps change.


## Nouvelle étape bêta — cotation de toutes les pièces d'UN appartement (5 novembre 2026)

**Objectif :** valider un appartement à la fois avant de rétablir
un éventuel traitement sur toute une vue. Le mode diagnostic **une pièce**
reste disponible et les groupes Revit, le multi-vues, l'ensemble du niveau
et le traitement de masse restent désactivés pour la cotation.

### Utilisation

1. Sur **une copie sauvegardée du projet**, ouvrir le plan d'étage
   Revit contenant le logement, puis **Outils TAA > Annotations > Cotation auto**.
2. Choisir **« Un appartement dans cette vue (bêta, 12 pièces max.) »**.
3. Sélectionner le **paramètre d'instance des pièces qui porte l'identifiant
   de l'appartement**. Le programme n'invente pas le numéro de logement en
   lisant le numéro des pièces ; il présente des paramètres dont les valeurs
   sont partagées par plusieurs pièces visibles dans cette vue.
4. Choisir la valeur exacte de ce paramètre, par exemple `101`.
   Si cet identifiant est utilisé dans plusieurs bâtiments et qu'un
   paramètre bâtiment est détecté (`Bâtiment`, `Immeuble`, `Bloc`),
   sélectionner également la valeur du bâtiment.
5. **Vérifier la liste nominative des pièces affichée avant la cotation.**
   Ne pas confirmer si elle comporte une pièce d'un autre appartement,
   oublie une pièce nécessaire, ou mélange plusieurs bâtiments.
6. Sélectionner le type de cote et le style de lignes 2D de repli,
   puis confirmer l'essai. Le rapport indique la progression **pièce
   par pièce** et le nombre d'annotations créées pour chacune.

### Limites de sécurité et garanties

- **Une vue de plan à la fois**, **2 à 12 pièces visibles** portant
  strictement le même identifiant appartement. Le traitement refuse
  le périmètre vide, une sélection d'une seule pièce, ou plus de
  12 pièces au lieu de modifier silencieusement toute la vue.
- Les **pièces incluses dans un groupe Revit** sont refusées :
  aucun groupe de détails attachés n'est tenté. Aucun fichier lié n'est
  utilisé, et aucune pièce en dehors de la vue sélectionnée n'est traitée.
- Une **liste exacte des pièces** est présentée en prévisualisation ;
  un second dialogue demande confirmation après le choix du style.
- **Une transaction Revit isolée par pièce** : le succès d'une pièce
  est conservé si une pièce suivante provoque une exception. La pièce
  en erreur est annulée, puis le traitement des pièces restantes est
  interrompu à titre préventif (marqueur `ARRET PREVENTIF` dans le rapport).
- La protection contre les doubles cotations demeure fondée sur les
  références natives déjà cotées et les repères 2D existants.
- Les garde-corps successifs conservent le contrôle BUG-COMMON-025 ;
  sur ces ouvrages, la cote peut être associative à **un seul** garde-corps.
- Un crash natif Revit ne peut pas être empêché par une exception Python :
  **copie du projet et sauvegarde préalable impératives**.
  Journal de crash : `%TEMP%\OutilsTAA_Annotations_crashtrace.log`.

### Recette Revit 2025.4 — appartement témoin

- [ ] **REV-ANN-104** — Une vue, paramètre logement et numéro corrects ;
  la prévisualisation montre toutes et uniquement les pièces du logement.
- [ ] **REV-ANN-105** — Appartement de 3 à 8 pièces hors groupe :
  cotation pièce par pièce, jusqu'à deux directions principales par pièce ;
  valeurs et nus finis conformes, aucun chevauchement avec les annotations
  ou les équipements.
- [ ] **REV-ANN-106** — Relancer sans enlever les cotes : aucune nouvelle
  cote doublée, pas de plantage et pas de duplication de repères 2D.
- [ ] **REV-ANN-107** — Étiquettes existantes : aucun chevauchement avec
  les textes de cote ; contrôle d'une chambre, d'un WC et d'une loggia.
- [ ] **REV-ANN-108** — Appartement comprenant une pièce en groupe :
  refus explicite **avant toute création** ; aucune modification des groupes.
- [ ] **REV-ANN-109** — Deux appartements de même numéro dans deux
  bâtiments : choix explicite du bâtiment ; l'autre logement ne reçoit
  aucune annotation.
- [ ] **REV-ANN-110** — Périmètre dépassant 12 pièces et pièce absente :
  refus explicite avant création ; aucune autre vue ou pièce modifiée.
- [ ] **REV-ANN-111** — Vérifier les marqueurs `ROOM_COMMITTED`,
  `RUN_END` et `BATCH_STOP` (si un échec a été observé) et
  la non-régression des essais 2238 et 2240.

**Statut : code bêta et tests Python à vérifier en CI, essais Revit
sur appartement complet NON encore validés.** Aucune fusion dans `main`
et aucun déploiement sur la maquette de production à cette étape.


## Retour appartement complet — petites pièces et repli PDV (5 novembre 2026)

**Premier essai réel :** vue `Collectifs A_Niveau 1`,
**12 pièces hors groupe**, **18 cotes** produites dans un seul
appartement. La capture révèle que plusieurs petits WC/celliers
et dégagements n'ont qu'une cote. Le rapport donne une seule cote
pour **2247, 2249, 2251, 2252, 2253 et 2256**.

**Analyse des cinq orientations explicitement refusées :**
2249, 2251, 2252, 2253 et 2256 ont de 8 à 10 positions candidates,
dont zéro à trois avec texte entièrement intérieur. Le problème
n'est pas un défaut mesuré des références de faces : le
**filtre strict de présentation** ne trouve pas de combinaison
des deux cotes sans conflit de texte/traits, alors que la variante
Plans de vente privilégie les deux mesures en signalant les
éventuelles collisions. Pour **2247**, le rapport ne contient pas
`orientation 2 ignoree` ; la nouvelle journalisation précisera
si une seconde paire de faces opposées existe réellement.

**BUG-COMMON-026 — amélioration sur la branche bêta :**
- Le moteur Plans de vente reste la source canonique des
  **références physiques**, des positions initiales et du type
  `DimensionPlacement`. Aucun fichier de Plans de vente n'est modifié.
- Le filtre propre à Annotations accepte désormais des **croisements
  ponctuels de traits et témoins** non parallèles, jamais des
  collisions impliquant un texte.
- Seulement si le filtre précédent ne produit pas toutes les
  orientations, le module essaie au plus **4 translations
  supplémentaires par orientation**, à une ou deux hauteurs
  de texte juste **à l'extérieur** des limites de la pièce.
  Il sélectionne ces positions uniquement si elles augmentent
  le nombre de cotes et qu'elles ne touchent pas les étiquettes
  ni les textes des cotes existantes.
- Un avertissement **`REPLI PETITE PIECE`** prévient lorsque le
  placement extérieur est retenu : vérifier la lisibilité et
  les éventuelles interactions avec le logement ou le couloir
  voisin. Le moteur ne prétend pas maîtriser les collisions
  finales de typographie native Revit sans recette visuelle.
- La conservation du placement initial est obligatoire si le
  calcul complémentaire échoue ; une pièce ne perdra pas
  sa première cote du seul fait du nouveau repli.
- Un diagnostic `seulement N orientation(s) de faces opposees`
  distingue les problèmes géométriques des problèmes graphiques.

### Recette ciblée après correctif (sur copie du même appartement)

- [x] **REV-ANN-104 — premier essai :** une vue, un appartement,
  12 pièces hors groupe, 18 cotes créées, aucune autre vue traitée
  selon le rapport. Les détails de justesse/placement restent à confirmer.
- [ ] **REV-ANN-112** — Recharger la dernière branche bêta,
  **conserver les 18 cotes précédentes**, relancer le même appartement.
  Relever le nombre de cotes ajoutées et les numéros des pièces.
  Aucune duplication des 18 cotes existantes.
- [ ] **REV-ANN-113** — Contrôler les pièces 2249, 2251,
  2252, 2253 et 2256 : la seconde cote est-elle ajoutée ?
  Si repli, journal `placement complementaire petites pieces`
  et/ou `REPLI PETITE PIECE` ; valeur et nu corrects.
- [ ] **REV-ANN-114** — Si une cote est placée hors pièce :
  vérifier qu'elle reste lisible, ne heurte pas les étiquettes
  ou chiffres de cotes du couloir/des voisins, et reste visible
  après masquage des séparations de pièces.
- [ ] **REV-ANN-115** — Pour 2247, transmettre
  `seulement N orientation(s) de faces opposees` ou le
  message de refus s'il existe ; conserver une cote seulement
  si la seconde direction n'a pas deux références fiables.
- [ ] **REV-ANN-116** — Troisième lancement de contrôle
  anti-doublon, et vérifier les cotes des deux loggias déjà
  validées 2238/2240 si présentes dans le périmètre.

**Statut : 460 tests automatisés réussis avant mise à jour
documentaire. Le nouvel algorithme de petites pièces n'a PAS
encore été validé dans Revit.** La sécurité des références natives,
les transactions par pièce et les corrections de garde-corps
antérieures sont conservées.


## Deux cotes interieures et secours mur pour 2247 — 5 novembre 2026

### Retour de la seconde recette appartement

L'utilisateur a relance la cotation de `Collectifs A_Niveau 1` :
**23 annotations pour 12 pieces**, contre 18 avant le
correctif BUG-COMMON-026. Les cinq pieces 2249, 2251, 2252,
2253 et 2256 obtiennent desormais deux orientations, parfois
par un repli de placement **en dehors du contour**.
**2247 conserve une seule cote**, ce qui motive le correctif
BUG-COMMON-027.

### Regles metier retenues

- **Deux mesures par piece des qu'elles sont physiquement
  possibles**, avec Reference Revit valide et pas de seconde
  dimension artificielle.
- **Les deux lignes de cote doivent rester dans le volume en plan
  de la piece**, y compris quand le local est tres etroit.
  Le point d'ancrage du texte doit rester lui aussi dans la piece.
  Si la largeur physique du texte est trop grande, le texte peut
  deborder et se superposer : avertissement dans le rapport.
- **Les collisions sont admises en dernier recours dans les
  petites pieces**, meme avec etiquettes, cotes existantes et
  temoins. Les solutions sans collisions sont toujours prioritaires.
  Le module ne cree jamais de dimensions sur References inventees.
- **La detection de garde-corps est reservee aux limites
  selectionnees qui ne sont pas des murs**, plus precisement
  aux limites `separator` dont aucune reference de face murale
  n'est disponible. Toute piece avec uniquement des limites
  `wall` court-circuite ce sondage. Les garde-corps 2238 et 2240
  conservent leurs gardes-fous natifs.
- **Pour une piece comme 2247**, si le moteur ne trouve qu'une
  paire de faces opposees, il tente en complement une cote
  de **longueur reelle d'un mur** a partir des deux References
  natives de ses extremites, exactement comme dans Plans de
  vente. L'ancienne neutralisation systematique des secours
  de longueur du module Annotations est supprimee.
  Sans References natives fiables, le rapport conserve
  explicitement une seule cote et signale la limite du modele.

### Recette Revit a effectuer

- [ ] **REV-ANN-117** — Mettre a jour la branche beta et
  relancer sur une copie de l'appartement de 12 pieces. La
  premiere cote par piece doit etre correcte et la seconde
  apparaitre pour les six pieces cibles quand des References
  natives le permettent.
- [ ] **REV-ANN-118** — Pour 2247, verifier le rapport :
  `Recherche d'une longueur complementaire de mur`,
  puis la longueur native effectivement creee ou le message
  `aucune longueur de mur native complementaire`. Verifier
  que la cote correspond aux extremites reelles du mur.
- [ ] **REV-ANN-119** — Les deux lignes de chaque piece
  doivent rester a l'interieur, meme si les textes se
  superposent dans un petit WC, cellier ou degagement.
  Verifier les avertissements `COTATION INTERIEURE` et
  `SUPERPOSITION INTERIEURE AUTORISEE`.
- [ ] **REV-ANN-120** — Dans les pieces entourees
  exclusivement de murs, aucune ligne `filtrage GC`,
  `rail filant` ou `GC retenu` ne doit apparaitre.
  Une piece non murale type loggia doit continuer a
  utiliser ses garde-corps quand c'est necessaire.
- [ ] **REV-ANN-121** — Relancer une seconde fois pour
  confirmer l'absence de doublons, notamment sur la cote
  de longueur native de 2247 et les cinq petites pieces.

**Statut : implementation beta et tests hors Revit ; validation
de ce nouveau mode interieur et du secours 2247 dans Revit
encore en attente.** Ne pas fusionner dans `main` a ce stade.


## Diagnostiquer la version effectivement chargee — loggia et chambre 2247 (5 novembre 2026)

**Troisieme retour utilisateur :** la cotation des petites pieces est
maintenant INTERIEURE, avec deux dimensions pour 2249, 2251, 2252,
2253 et 2256, superpositions acceptees et averties. **23 annotations
sur 12 pieces : 2247 reste a une cote.** La capture montre une chambre
dont la largeur cotee est **2,62 m** ; la seconde direction attendue
correspond a la profondeur vers la facade. Le contour haut est marque
par le placard et la porte vers le degagement : il n'est pas etabli que
deux longues faces murales y soient simultanement referencables.

**Probleme de tracabilite :** le rapport recu ne comporte pas le message
`2247 : 1 axe(s) entre faces opposees detecte(s). Recherche d'une
longueur complementaire de mur...`, present dans le code depuis le
correctif de secours natif. Il est donc **probable** que le Revit de
ce test utilise encore un etat precedant ce correctif ou une autre
copie de l'extension. Cela ne prouve pas que le correctif fonctionne
dans la chambre : il doit etre reteste reellement.

Pour lever toute ambiguite, le rapport commence maintenant par :
`REVISION COTATION BETA : 2026-11-05-2247-native-fallback-02`.
Lorsque moins de deux paires de faces opposees sont exploitable,
une ligne supplementaire `DIAGNOSTIC 2247` indique :
nombre et nature des limites candidates (wall, separator, autres),
nombre de murs avec deux references natives d'extremites,
nombre de secours eligibles apres filtrage anti-doublon.

**Recette ciblee REV-ANN-122 :**
- [ ] Fermer completement Revit, mettre a jour le depot sur
  `feature/annotations-automatiques-beta`, puis rouvrir Revit
  2025.4 et pyRevit depuis la copie installee de l'extension.
- [ ] Lancer la cotation **sur 2247 seulement**, de preference sur une
  copie du projet, et confirmer la presence de `REVISION COTATION
  BETA : 2026-11-05-2247-native-fallback-02` dans le rapport.
- [ ] Transmettre les lignes `Recherche d'une longueur complementaire
  de mur` et `DIAGNOSTIC 2247` afin de verifier si Revit expose
  les references natives du mur utile. Si elles ne sont pas presentes,
  ne **pas** creer de fausse cote de profondeur ou decaler une ligne
  hors piece.
- [ ] Si la deuxieme cote est creee, comparer sa valeur a la profondeur
  finie entre les limites reelles de la chambre et verifier que les
  deux cotes restent a l'interieur. Relancer pour confirmer
  l'absence de doublon.

**Automatisation hors Revit :** 468 tests valides en CI sur la branche
apres ajout du marqueur de version et des diagnostics 2247.
**Statut :** 2247 encore non validee dans Revit sur cette revision.
Ne pas fusionner dans `main` avant la recette.
 

## Validation ciblee REV-ANN-122 — piece 2247 (5 novembre 2026)

**Compte-rendu Revit fourni par l'utilisateur :** une vue `Collectifs A_Niveau 1`, une piece hors groupe (2247), **2 annotations creees**. La ligne de version indique exactement `REVISION COTATION BETA : 2026-11-05-2247-native-fallback-02`. La capture montre la largeur **2,62 m** et la cote verticale **3,33 m**, toutes deux tracees dans la chambre 3.

Le rapport confirme :
- `2247 : COTATION INTERIEURE : 2 / 2 axe(s) place(s) a l'interieur (ancien choix : 1)` ;
- `SUPERPOSITION INTERIEURE AUTORISEE avec une etiquette` ;
- `SUPERPOSITION INTERIEURE AUTORISEE entre les deux cotes (texte : 0, traits/temoins : 1)` ;
- deux messages de proximite equipement et une emprise de cote proche d'une etiquette ; **aucune erreur ni cote refusee**.

**Conclusion et portee exacte :** `REV-ANN-122` est **VALIDE** pour (a) chargement de la bonne revision, (b) production de **deux cotes** dans la piece 2247 et (c) placement **interieur** avec superposition autorisee. Le journal ne contient ni `Recherche d'une longueur complementaire de mur` ni `DIAGNOSTIC 2247`, ce qui **n'est pas une erreur** : ces lignes ne sont emises que lorsque le moteur n'a pas deja obtenu deux paires de faces opposees. On **ne peut pas conclure** d'apres ce rapport que la cote verticale provient du secours d'extremite de mur. Ne pas le presenter comme verifie.

**A confirmer avant cloture globale :**
- [ ] Comparer dans le modele les valeurs **2,62 m** et **3,33 m** aux **nus interieurs finis reels** (la capture confirme l'affichage, pas un controle metrique independant).
- [ ] Relancer 2247 sans supprimer ses deux cotes : aucune cote en double.
- [ ] Relancer l'appartement complet : viser **24 cotes sur 12 pieces** seulement si chaque piece possede deux mesures valides ; verifier qu'aucune cote des onze autres pieces n'a regresse.
- [ ] Tester la visibilite de la cote si les etiquettes de piece sont masquees et controler la lisibilite de la superposition sur la chambre 3.

**Etat projet :** correction graphique 2247 validee en Revit sur cet essai cible ; **recette complete d'appartement et anti-doublons encore ouvertes**. Ne pas fusionner `feature/annotations-automatiques-beta` dans `main` sur cette seule preuve.


## Recette appartement — references partagees de 2247 (5 novembre 2026)

**Nouveau retour utilisateur :** la **meme revision**
`2026-11-05-2247-native-fallback-02` donne **2 cotes
interieures** quand 2247 est lancee seule, mais seulement
**1 cote** lorsque 2247 est la quatrieme piece d'un
appartement de 12 pieces. Total de lot : **23
annotations**, une par orientation sauf 2247.

**Risque confirme dans le code :** avant la modification,
`_existing_dimension_reference_pairs()` traitait la liste
des References de **toutes les dimensions de la vue**
comme si une paire de faces deja utilisee dans
une chambre voisine signifiait que la meme paire
etait deja cotee dans la chambre en cours.

**Correction experimentale BUG-COMMON-028 :**
`GenericDimensions._existing_dimension_reference_pairs(room)`
et `_existing_proxy_dimensions(room)` ignorent
desormais les dimensions dont la **ligne Revit**
est localisee **hors de la piece en cours**.
La methode `_dimension_ownership_in_room`
sonde `Dimension.Curve` aux fractions 20/50/80 %
et `Room.IsPointInRoom` pour determiner
l'appartenance a la piece. Un element dont
la position est **illisible** reste retenu
dans le verrou anti-doublon conservateur.
Les cotes des autres pieces ne sont jamais supprimees.

**Diagnostic beta revision :**
`2026-11-05-apartment-room-dedup-03`.
Le rapport indique `COTES DEJA PRESENTES`
(positions dans/hors piece/indeterminees)
et `CONTROLE DOUBLONS PAR PIECE`
(axes geometriques, axes deja mesures, axes retenus).
Une simulation hors Revit reproduit le cas
d'une dimension de chambre A avec les memes
References que la chambre 2247 :
la cote de A ne bloque plus la seconde
direction de 2247, mais une dimension
de 2247 bloque toujours son propre duplicata.
**471 tests hors Revit valides sur la branche beta.**

### Recette ciblee — REV-ANN-123

- [ ] Fermer Revit puis actualiser la branche
  `feature/annotations-automatiques-beta` et
  confirmer `REVISION COTATION BETA :
  2026-11-05-apartment-room-dedup-03`.
- [ ] Sur une **copie du meme projet**, lancer
  le mode **Un appartement** sur les 12
  pieces, conserver les autres cotes de
  l'appartement (ne pas les supprimer pour
  cette verification anti-doublon).
- [ ] Relever pour la chambre 2247 les
  lignes `COTES DEJA PRESENTES` et
  `CONTROLE DOUBLONS PAR PIECE`.
  Attendu : deux axes geometriques reconnus
  et aucun couple de murs de la chambre
  voisine n'empeche la deuxieme cote.
- [ ] Confirmer **deux cotes interieures** sur
  2247, dimensions en nu fini
  **2,62 m et 3,33 m** si la maquette
  n'a pas change, et **aucun nouveau doublon**
  sur les onze autres pieces.
- [ ] Relancer une deuxieme fois sans
  nettoyage de cotes et verifier
  aucune cote supplementaire ; controler
  la stabilite des loggias GC 2238/2240
  et du logement 2239.

**Statut : correctif de dedoublonnage spatial
testé automatiquement ; recette réelle
du logement encore en attente.**
Ne pas fusionner dans `main` avant
cette validation.


## BUG-COMMON-028 — preuve API du blocage et correction dedup-04 (5 novembre 2026)

**Nouveau retour d'un appartement de 12 pieces :**
version `2026-11-05-apartment-room-dedup-03`,
toujours **23 cotes sur 24**. La chambre **2247**
annonce explicitement **2 axes geometriques**,
**1 axe suppose deja cote**, 1 axe retenu.
En amont, les **six cotes precedentes** sont
classees `a position indeterminee conservees
par securite`. Les compteurs des pieces
suivantes continuent a augmenter :
2, 4, 6, 7, 9, 11, etc. Aucune
cote de chambre voisine n'est effectivement
reconnue comme `hors piece`.

**Erreur verifiee :** la methode de detection
essayait `dimension.Curve.GetEndPoint(0/1)`.
Or la documentation officielle Revit API 2025
precise que `Dimension.Curve` est **non bornee**,
donc ne fournit pas d'extremites.
`Dimension.Origin` est le milieu de la ligne
de cote a un segment. L'ancien diagnostic
renvoyait `None` pour toutes les dimensions
et maintenait le blocage global, ce qui
explique la difference entre un lancement
2247 seule et en appartement.

**Correction sur `feature/annotations-automatiques-beta` :**
la revision passe a
`2026-11-05-apartment-room-dedup-04`.
L'anti-doublon exploite `Dimension.Origin`
en XY et le sondage `Room.IsPointInRoom`
dans **la piece cible**.
Une cote de chambre voisine est ignoree
pour cette chambre ; une cote existante
dans la meme chambre reste protegee.
Une origine illisible ou une cote
multisegment restent classees
`indeterminees` (pas de duplication
tente en l'absence de preuve).
Le secours `GetEndPoint` ne s'applique
qu'aux courbes explicitement **bornees**,
notamment les doubles hors Revit.

**Tests automatises : 472 reussis**, dont
des simulations de `Dimension.Curve`
non bornee et de chambres mitoyennes
avec references partagees.
Le module Plans de vente reste inchange.

### Recette REV-ANN-124 — derniere verification Revit

- [ ] Fermer Revit, mettre a jour la
  branche, puis relancer sur une **copie**
  du meme appartement.
- [ ] Verifier la revision
  `2026-11-05-apartment-room-dedup-04`.
- [ ] Lire pour **2247** :
  `COTES DEJA PRESENTES` avec des positions
  `d'autres pieces ignorees` si des
  chambres voisines ont deja leurs cotes,
  et `CONTROLE DOUBLONS PAR PIECE`
  avec les deux orientations correctement
  attribuees.
- [ ] Verifier **2,62 m** et **3,33 m**
  sur les bons nus finis de 2247,
  les deux cotes a l'interieur,
  ainsi que l'absence de doublons
  sur les onze autres pieces.
- [ ] Pour une copie **sans cotes**, objectif
  **24 cotes creees / 12 pieces**.
  Pour une copie **deja cotee**,
  le nombre de cotes nouvellement creees
  doit etre seulement le nombre manquant :
  le rapport ne donne PAS le cumul
  des cotes anciennes et nouvelles.
- [ ] Relancer une seconde fois
  sans effacer les cotes et verifier
  l'absence d'ajout supplementaire
  ou de crash.

**Statut : correction hors Revit validee
en tests automatisees, recette Revit
de dedup-04 encore en attente.**


## Règle métier Étiquetage automatique — placement prioritaire (5 novembre 2026)

**Décision explicite de l'utilisateur :** toute pièce possédant un point d'ancrage intérieur valide doit recevoir une étiquette, **même si l'emprise du texte dépasse la pièce ou chevauche des cotes/annotations**. La correction de la lisibilité est laissée à l'utilisateur après génération. Ce comportement concerne **Étiquetage auto dans les vues ordinaires uniquement**, et non le moteur **Plans de vente**.

**Retour Revit avant correction :** niveau `Collectifs A_Niveau 1`, 44 pièces hors groupe ; 37 étiquettes créées, 7 refusées par `ValueError: Aucune position interieure sans chevauchement.` dans `GenericRoomTags._place_one_tag`.

**Correction implémentée :** l'adaptateur `GenericRoomTags` conserve le résultat du moteur partagé `RoomTagService._place_one_tag` sans lever cette exception. Le moteur choisit la meilleure position candidate et vérifie toujours que le **point d'ancrage** est dans la pièce via `Room.IsPointInRoom` et que Revit confirme `tag.IsInRoom`. Il peut remonter des avertissements de collision et de débordement. Le code de Plans de vente n'a pas été modifié.

**Statut : implémenté, test Revit en attente ; aucun test automatisé exécuté pour ce changement dans cette intervention.**

**Recette à faire sur copie :**
- [ ] Relancer Étiquetage sur une vue équivalente avec 44 pièces **sans étiquettes préexistantes** ; viser 44 créations si les 44 pièces possèdent des candidats intérieurs valides.
- [ ] Vérifier que les étiquettes sont bien ancrées **dans leur pièce respective** ; des chevauchements ou textes débordants sont acceptés et à corriger manuellement.
- [ ] Vérifier le rapport pour les avertissements ; vérifier qu'aucune pièce n'est étiquetée dans une autre pièce.
- [ ] Vérifier l'absence de régression de **Cotation automatique** et de **Plans de vente V1.1**.

**Limite :** une pièce sans candidat intérieur valide peut toujours être refusée ; aucune étiquette ne doit être créée hors pièce pour atteindre artificiellement 44/44.

## Recette Étiquetage — 44 pièces (05/11/2026)

**Retour de test utilisateur sous Revit 2025.4, module Étiquetage automatique bêta :** vue `Collectifs A_Niveau 1`, **44 pièces détectées (0 en groupe)**, **44 étiquettes créées**. Le précédent résultat de 37/44 est résolu sur ce cas après suppression du refus systématique des collisions dans l'adaptateur.

**Avertissements acceptés par décision métier :** emprise graphique débordante pour les pièces 2222, 2223, 2250, 2252 ; collision non résolue et meilleure position intérieure conservée pour 2249, 2251, 2252, 2253. Ces avertissements n'empêchent pas la création ; l'utilisateur repositionne les étiquettes illisibles.

**Statut précis :** génération 44/44 **validée sur cette vue**, pas validation globale du module. Reste à tester : étiquettes existantes / seconde exécution sans doublons, plusieurs vues, groupes de modèle et non-régression Plans de vente. Ne pas confondre validation de cette recette et fusion de la PR #37.

## Validation Revit — anti-doublons Étiquetage auto (05/11/2026)

**Confirmation explicite de l'utilisateur :** après un premier lancement ayant créé **44 étiquettes pour 44 pièces** dans `Collectifs A_Niveau 1`, le deuxième lancement a créé **0 annotation supplémentaire**, et **les 44 étiquettes initiales sont toujours visibles**. **Test anti-doublons validé sur cette vue**, sans suppression des étiquettes existantes. Ne pas extrapoler aux groupes de modèle, aux autres vues ou aux autres types d'étiquettes non testés.

Amélioration non bloquante à prévoir : remplacer le message répété « annotations deja presentes ou vues non cotables » par une indication spécifique et comptabilisée (« étiquette déjà présente »), distincte des vrais refus.

## Développement groupes de modèle — sécurisation initiale (05/11/2026)

**Objectif :** étiqueter les pièces appartenant à un groupe de modèle avec des groupes de détails attachés, réutilisables sur les occurrences. La cotation en groupe reste volontairement désactivée après un crash antérieur ; ne pas la réactiver sans protocole de validation distinct.

**Implémenté sur la branche bêta :** vérifications renforcées de `_attach()` après `Document.Create.NewGroup` : rejet d'un résultat invalide ou ambigu, exigence d'un seul nouveau type de groupe de détails, et vérification d'une instance `Group.IsAttached` dont `AttachedParentId` correspond au groupe initial. En cas de doute, levée d'exception et rollback des transactions afin de protéger le groupe de modèle. Commit code : `ef8ff7f5c0496282a32456df1a77fe656330e52e`.

**Statut exact :** correction de sécurité implémentée, **aucun test automatisé ni test Revit exécuté** sur cette modification. L'API `NewGroup` mixte peut ne pas rattacher des détails à un groupe de modèle déjà existant ; les garde-fous peuvent donc refuser l'opération, ce qui est attendu tant que la faisabilité n'est pas prouvée. **Aucune fonctionnalité groupe déclarée validée.**

**Recette prioritaire sur une COPIE de maquette :** un groupe modèle ne contenant qu'une ou deux pièces, lancer d'abord **Étiquetage auto** ; vérifier absence de modification du groupe d'origine, création effective d'un groupe de détails attaché et possibilité d'afficher ce type sur une autre occurrence. Après une relance, aucun doublon. En cas de refus, collecter le rapport complet ; ne pas supprimer ou dégrouper l'original. La recette cotation en groupe est séparée et suspendue.


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
