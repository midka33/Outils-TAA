# Outils TAA – Outil Export

**Version :** 4.3
**Statut :** Spécification fonctionnelle de référence et cible d'évolution  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Année :** 2026

---

## Périmètre V1 — décision du 2026-09-30

L'option « Publier uniquement les mises en page nouvelles ou modifiées » est retirée.
La V1 publie toutes les mises en page du périmètre choisi (feuille, carnet ou dossier),
sous réserve des contrôles habituels. Les collisions de fichiers restent signalées.
Les anciennes valeurs `modified_only=true` sont ignorées au chargement et ne sont
plus sérialisées comme réglages actifs ; aucun nettoyage manuel n'est nécessaire.
L'historique technique est conservé mais ne réduit plus le contenu à publier.
Le modèle expose `modified_only=False` en lecture seule pour les intégrations Stage 07
encore présentes. La case XAML et ses handlers/synchronisations sont supprimés.
Les services de filtrage isolés restent disponibles pour une éventuelle V2.
Le retour de l'option sera étudié **après finalisation et sortie de la V1** : voir `ROADMAP.md`.

## Sélection multiple — correctif du 2026-10-05

`Ctrl + clic` sélectionne plusieurs feuilles et/ou carnets ; `Maj + clic`
sélectionne une plage (feuilles du même carnet). Le résumé, **Aperçu…** et
**Publier la sélection** utilisent le même périmètre. Une désélection explicite
vide désactive la publication ; la navigation clavier retrouve la sélection native.

Les feuilles sont regroupées par carnet dans leur ordre métier. Un carnet/dossier
sélectionné inclut son contenu entier et prime sur ses descendants sélectionnés,
sans doublon dans un même carnet. Une feuille dans deux carnets reste deux livrables.
Chaque carnet conserve ses réglages, son héritage et sa destination ; les copies
de publication ne modifient jamais le contenu persistant du carnet.
Un PDF combiné contient seulement les feuilles retenues de son carnet, sans fusion
entre carnets. Un sous-ensemble peut remplacer un PDF complet du même nom :
l'avertissement de fichier existant reste visible dans l'aperçu.

Les réglages à droite restent ceux de l'élément actif nommé dans ce panneau,
sans édition groupée implicite. Les collisions entre les fichiers de la sélection
sont contrôlées avant confirmation. Un aperçu global et un rapport global couvrent
la sélection complète. Les destinations distinctes restent indiquées dans le rapport.

Contrat technique : `publication_selection.publication_targets` est le constructeur
métier indépendant de WPF ; `ExportWindow._publication_targets` est le point de
raccordement commun au résumé, à l'aperçu et au handler de publication. Le gestionnaire
Ctrl/Maj notifie explicitement la fenêtre, car l'événement natif WPF est intercepté.
Le handler natif `Tree_SelectedItemChanged` reste propriétaire du chargement des réglages ;
la surcouche de sélection de dossier devenue redondante est retirée.

Voir [le tutoriel utilisateur](20_Export_Tutoriel.md) et
[la recette Revit](21_Export_Recette_Selection_Multiple.md).
**Statut : 212 tests Python réussis ; fonctionnement de la sélection multiple
confirmé par l’utilisateur dans Revit le 2026-10-05 sur la branche de la PR #11.**
La recette détaillée MS-01 à MS-10 reste distincte de cette validation fonctionnelle.

## Héritage récursif des réglages

Les valeurs sont résolues propriété par propriété : carnet, dossier immédiat,
puis dossiers parents du plus proche au plus éloigné, profil et valeurs par défaut.
Une surcharge locale explicite (y compris `False`) reste prioritaire. Les champs à
`None` héritent ; les réglages effectifs affichés ne sont pas persistés comme surcharges.
La sélection d'un sous-dossier affiche aussi ses valeurs héritées. Le panneau indique le nom du dossier fournissant chaque groupe de réglages.
Sur un sous-dossier possédant des surcharges, « Revenir à l’héritage du parent »
efface uniquement ses réglages locaux, après clic explicite, et sauvegarde ce choix.
Les réglages des descendants ne sont pas effacés. Une modification
ultérieure du parent s'applique aux descendants sans surcharge de ce champ.

## Publication d'un dossier — arborescence des livrables

La destination effective de chaque carnet reste la racine de sortie. Lorsqu'un
dossier est publié, son nom et les sous-dossiers jusqu'au carnet sont reproduits
sous cette racine. Seule la branche sélectionnée est reproduite : publier directement
`Architecture` ne rajoute pas son parent `DCE`.

Lorsque **Créer un dossier au nom du carnet** est activé, l'organisation est
indépendante du mode PDF et de la stratégie technique DWG :

```text
Destination/
└── Nom du carnet/
    ├── PDF/
    │   └── fichiers PDF
    └── DWG/
        └── fichiers DWG et ressources auxiliaires éventuelles
```

Cette structure s'applique au PDF combiné comme séparé, et aux exports DWG d'une
ou plusieurs feuilles. Lorsqu'elle est désactivée, les fichiers sont écrits
directement dans la destination issue de l'arborescence de publication.

Les modèles de nommage restent appliqués. Les noms des dossiers sont sécurisés pour
Windows. Aucun dossier n'est créé pendant l'aperçu ou après annulation.
`PublicationPreviewService` et `PublicationService` utilisent le même calcul de
chemin via `publication_paths.py`.

## Interface V1 — charte TAA

Les fenêtres de publication, ajout des carnets, consultation des feuilles, aperçu et
rapport utilisent le thème commun `resources/ui/Theme.xaml` : Segoe UI, fonds clairs,
accent orange pastel, sélection pêche et pictogrammes vectoriels.
Les actions et le périmètre fonctionnel restent ceux de la V1 ; les maquettes ne
réintroduisent pas les options différées en V2. Validation graphique et non-régression Revit 2025.4 confirmées le 2026-10-01 ; voir `docs/18_Export_Charte_UI_V1.md`.

## Progression de publication — implémentation à valider dans Revit

Après confirmation de l'aperçu, une fenêtre dédiée affiche une progression globale
**de 0 à 100 %**, le carnet courant, l'opération réelle, le nombre d'unités traitées
et la phase. Charte TAA : Segoe UI, fond clair, accent `#FD8B5A`.

Le plan couvre tous les carnets : préparation, appel PDF, livraison des PDF séparés,
DWG éventuel, historique et rapport. Il ne repart pas à zéro entre deux carnets.
Les modes PDF combiné et séparé conservent chacun **un seul appel natif par carnet**.
Pendant cet appel, « Export PDF Revit » reste affiché et la valeur peut rester fixe.
Le compteur indique des unités, sans simuler des feuilles ni un temps restant.

La fenêtre se ferme avant le rapport existant ; en cas d'exception fatale, elle
signale l'interruption et restaure la fenêtre Export. Il n'y a pas d'annulation
ni d'export déplacé sur un thread de fond. 100 % signifie que toutes les unités
ont été traitées, y compris celles classées en échec/non exécutées après erreur :
le rapport reste la source de vérité sur les succès et les fichiers.

`PublicationProgress` est indépendant de WPF. Le reporter optionnel traverse
`CarnetController`, `PublicationBatchService`, `PublicationService` et
`PdfExportService`. Les hooks Stage 07 du smartbutton et les fonctions de repli
sont raccordés. Les noms, destinations, sélections et règles d'historique sont conservés.

**Validation : 257 tests Python réussis ; recette Revit 2025.4 encore requise.**
Voir [la spécification et l'implémentation](22_Export_Progression.md) et
[la recette de progression](23_Export_Recette_Progression.md).

## Ruban Revit — bouton Export graphique seul

Le ruban distingue quatre notions qui ne doivent pas être confondues :

- **nom interne de commande** : `Export` ; le bundle est `Export.smartbutton` uniquement pour disposer du hook pyRevit d'initialisation ;
- **titre visible du PushButton** : métadonnée `title` de `bundle.yaml` ;
- **tooltip** : métadonnée `tooltip` de `bundle.yaml` ;
- **nom du panneau** : dossier `Export.panel`, qui reste affiché « Export ».

Sans métadonnée spécifique, pyRevit dérivait le titre visible du bouton du nom `Export`.
Le panneau est lui aussi nommé `Export`, d’où le double affichage.

Une première tentative avec `title: " "` a été rejetée au rechargement par Revit
(`The value cannot be empty. Parameter name: text`) : pyRevit/Revit normalise cette
valeur comme un texte vide lors de la création du `PushButtonData`.

Le correctif final conserve donc un vrai titre API `Export` et masque uniquement son
rendu visuel après création du bouton. Pour disposer du hook pyRevit prévu à cet effet,
le bundle devient `Export.smartbutton` tout en conservant le même nom de commande
`Export`, le même script métier et le même panneau. Son `__selfinit__` récupère le
`RibbonButton` Autodesk.Windows et applique `ShowText = False` ; `ShowImage` reste actif.

Ce changement de type de bundle n'est pas un renommage fonctionnel : le basename
`Export` reste inchangé et le script exécuté au clic reste le même. Le tooltip est
conservé dans `bundle.yaml`.

L’icône reste issue d’une source SVG, sans texte, avec :

- orange de marque `#FA641F` ;
- pictogramme blanc ;
- symbole d’export agrandi dans le canevas ;
- rendus 16 × 16, 32 × 32 et 96 × 96 ;
- `icon.png` et `icon.dark.png` fournis au bundle.

La validation finale a été confirmée dans Revit 2025.4 le 1er octobre 2026 après rechargement de pyRevit : aucun défaut de chargement, icône seule dans le bouton, panneau « Export » conservé, tooltip fonctionnel et module Export ouvert normalement au clic.

## 1. Vision

**Export** est le gestionnaire de publications des **Outils TAA**.

L'objectif est de proposer dans Revit une expérience proche du **Publisher d'Archicad**, sans chercher à reproduire son interface à l'identique : même logique de dossiers, carnets, mises en page, réglages persistants, sélection du périmètre, nommage et publication reproductible.

> **Export n'est pas seulement un exporteur PDF/DWG : c'est un gestionnaire de publications.**

La structure fonctionnelle retenue est :

```text
Dossier
├── Carnet A
│   ├── Mise en page 01
│   ├── Mise en page 02
│   └── Mise en page 03
└── Carnet B
    ├── Mise en page 01
    └── Mise en page 02
```

L'utilisateur doit pouvoir :

- parcourir ses publications dans une arborescence ;
- créer et gérer des dossiers persistants ;
- créer des carnets persistants, temporaires ou issus d'un paramètre ;
- placer les carnets dans le dossier choisi ;
- réorganiser les carnets par glisser-déposer ;
- sélectionner un carnet pour publier tout son contenu ;
- sélectionner une mise en page pour ne publier que celle-ci ;
- sélectionner un dossier pour publier récursivement ses carnets et sous-dossiers ;
- sélectionner plusieurs carnets et les déplacer ensemble ;
- conserver les réglages de publication avec le carnet ;
- hériter de réglages définis au niveau dossier ;
- utiliser des profils de publication ;
- choisir explicitement le **Set / Dossier** de publication ;
- choisir un **Carnet** précis ou l'ensemble des carnets du Set / Dossier ;
- choisir le **périmètre de publication** : tout le contenu, révision courante ou sélection de mises en page ;
- choisir les règles de nommage des fichiers ;
- prévisualiser les livrables avant de les créer ;
- publier PDF et DWG selon les configurations retenues ;
- obtenir un rapport de publication ;
- retrouver une organisation stable même lorsque le projet Revit évolue.

---

## 2. Principes directeurs

### 2.1 Séparer « quoi publier » et « comment publier »

Le modèle fonctionnel repose sur deux questions distinctes.

**QUOI ?**

- dossier ;
- carnet ;
- mise en page ;
- sélection de mises en page ;
- source fixe ou dynamique.

**COMMENT ?**

- PDF / DWG ;
- combiné / séparé ;
- configuration native Revit ;
- destination ;
- organisation des dossiers ;
- nommage ;
- stratégie de collision ;
- profil ;
- héritage.

Cette séparation est fondamentale pour rester proche du fonctionnement Publisher.

### 2.2 Les réglages sont persistants

Les réglages associés à un carnet persistant sont enregistrés avec lui. Une fermeture de Revit ou une nouvelle session ne doit pas obliger l'utilisateur à reconfigurer sa publication.

Un réglage peut être :

- défini explicitement au niveau du carnet ;
- hérité du dossier parent ;
- fourni par un profil lors de son application.

Une valeur effective héritée ne doit pas être enregistrée automatiquement comme surcharge locale.

### 2.3 Le contexte et le périmètre de publication sont explicites

La sélection dans l'arborescence sert à naviguer, inspecter et sélectionner des éléments, mais elle ne définit pas toujours à elle seule ce qui sera publié.

Le contexte de publication est défini par quatre choix visibles dans l'interface :

```text
Profil
  ↓
Set / Dossier
  ↓
Carnet
  ↓
Périmètre
```

Le **Set / Dossier** définit l'ensemble de publication dans lequel l'utilisateur travaille.

Le **Carnet** définit le carnet concerné. L'interface doit également permettre de choisir **Tous les carnets** du Set / Dossier lorsque ce périmètre est pertinent.

Le **Périmètre** définit ensuite les mises en page réellement publiées :

- **Tout le contenu** : toutes les mises en page du carnet choisi, ou de tous les carnets si « Tous les carnets » est sélectionné ;
- **Révision courante** : uniquement les mises en page correspondant à la révision courante dans le contexte choisi ;
- **Sélection** : uniquement une ou plusieurs mises en page sélectionnées dans l'arborescence.

La sélection multiple en mode **Sélection** utilise `Ctrl + clic` et `Shift + clic` lorsque l'implémentation WPF le permet.

Le résumé de publication et le bouton principal doivent permettre de comprendre le périmètre actif avant toute exécution.

### 2.4 L'arborescence est le point central de l'interface

L'écran principal fonctionne comme un explorateur de publications.

La structure visuelle cible comporte une ligne de contexte en haut, puis deux zones principales :

```text
Profil [DCE ▼]   Set / Dossier [DCE Architecture ▼]   Carnet [Plans DCE ▼]
Périmètre :  ● Tout le contenu   ○ Révision courante   ○ Sélection

Arborescence de publication        Réglages contextuels
───────────────────────────        ─────────────────────
📁 DCE Architecture               Carnet : Plans DCE
  📁 Plans                        Destination : ...
    ◇ Plans DCE                   PDF : Combiné par carnet
      PDF A101 – RDC              DWG : True Color
      DWG A102 – R+1              Informations
      PDF DWG A103 – R+2          Options avancées
```

L'arborescence doit rester le composant dominant de la fenêtre. Les réglages sont contextuels et secondaires.

La sélection d'un dossier, carnet ou d'une mise en page se fait directement sur la ligne. Les cases à cocher ne servent pas à sélectionner les éléments de l'arborescence.

Les sélecteurs **Profil**, **Set / Dossier**, **Carnet** et **Périmètre** doivent rester visibles sans ouvrir une fenêtre secondaire.

### 2.5 La sélection multiple complète la sélection simple

La sélection simple reste le comportement principal.

La sélection multiple permet notamment :

- `Ctrl + clic` pour sélectionner plusieurs carnets ;
- `Shift + clic` pour sélectionner une plage lorsque le comportement WPF le permet ;
- déplacer plusieurs carnets ensemble vers un dossier ;
- déplacer plusieurs carnets ensemble avant un carnet cible.

La sélection multiple ne doit pas casser la logique de sélection simple.

### 2.6 Le glisser-déposer fait partie du modèle d'organisation

Le TreeView doit permettre de réorganiser visuellement l'arborescence :

```text
Carnet → Dossier       = déplacement dans le dossier cible
Carnet → Carnet        = insertion avant le carnet cible
Carnet(s) → Dossier    = déplacement groupé en fin de dossier
Carnet(s) → Carnet     = insertion groupée avant le carnet cible
Mise en page → Carnet  = ajout à la fin du carnet
Mise en page → feuille = insertion avant la feuille cible
```

L'ordre affiché dans un carnet doit respecter l'ordre métier enregistré dans sa source, et non être automatiquement recalculé par numéro de feuille ou nom.

Le glisser-déposer doit empêcher les opérations incohérentes, notamment le dépôt d'un élément sur lui-même ou sur un élément faisant partie du même groupe déplacé.

---

## 3. Modèle métier

```text
PublicationProfile
├── PublicationFolder[]
│   └── PublicationSet[]
│       └── PublicationItem[]
├── NamingSettings
├── OutputSettings
└── ExecutionSettings
```

### 3.1 PublicationFolder

Un dossier organise les carnets dans l'interface et peut porter des réglages héritables.

Un dossier possède notamment :

```text
id
name
parent_id
persistent
publication_settings
```

Les dossiers sont persistants et peuvent être utilisés comme périmètre de publication.

### 3.2 PublicationSet

Un `PublicationSet` représente un carnet logique.

```text
id
name
source
items
folder_id
sort_order
publication_settings
persistent
```

Le carnet est l'unité persistante principale de configuration d'une publication.

### 3.3 PublicationItem

Un élément de carnet correspond notamment à une mise en page Revit.

Les références durables doivent privilégier `UniqueId`. L'`ElementId` courant est résolu au moment de l'utilisation.

Le moteur de publication travaille sur les éléments résolus, jamais directement sur les règles de sélection.

### 3.4 Ordre des éléments

L'ordre d'un carnet est une propriété métier persistée.

```text
sort_order
```

L'interface ne doit pas trier automatiquement les mises en page par numéro ou par nom après chargement si cela détruit l'ordre défini par l'utilisateur.

---

## 4. Sources des carnets

Export conserve les modes suivants.

### 4.1 Par paramètre

L'utilisateur choisit le paramètre Revit servant à générer les carnets.

`Sous-titre` peut être proposé par défaut selon les conventions TAA, mais ne doit jamais être imposé par le code.

### 4.2 Manuel persistant

L'utilisateur crée un carnet et sélectionne ses mises en page. Le carnet est enregistré et peut être placé dans le dossier choisi.

### 4.3 Manuel temporaire

Une sélection ponctuelle peut être publiée sans être enregistrée comme carnet persistant.

Ce mécanisme est notamment utilisé lorsqu'une mise en page sélectionnée seule doit être publiée en conservant les réglages effectifs du carnet parent.

### 4.4 Dynamique

Une règle peut recalculer le contenu d'un carnet à chaque publication.

Les critères pourront notamment utiliser :

- paramètre ;
- valeur de paramètre ;
- numéro de mise en page ;
- phase ;
- catégorie ;
- combinaison de critères ;
- autres informations disponibles de manière fiable dans Revit.

### 4.5 Persistance de la source

La sauvegarde doit conserver le mode d'origine et toutes les informations nécessaires à la reconstruction de la source.

```text
PublicationSource
├── mode
├── parameter_name
├── parameter_value
└── rule_definition
```

Une sauvegarde ne doit jamais transformer silencieusement un carnet issu d'un paramètre en carnet manuel.

### 4.6 Filtrage par projet Revit courant

Les carnets persistants doivent être filtrés contre le document Revit actuellement ouvert.

Un carnet ou une mise en page provenant d'un autre projet ne doit pas être publié comme s'il appartenait au document courant.

---

## 5. Arborescence Export

### 5.1 Structure

```text
Dossier
├── Carnet
│   ├── Mise en page
│   └── Mise en page
└── Carnet
```

Les dossiers peuvent être imbriqués.

### 5.2 Gestion des dossiers / Sets

Le gestionnaire doit permettre de :

- créer un dossier ;
- sélectionner explicitement un **Set / Dossier** dans le sélecteur de contexte ;
- créer un carnet directement dans le dossier sélectionné ;
- déplacer ultérieurement un carnet vers un autre dossier ;
- conserver l'identité et les réglages du carnet lors du déplacement ;
- publier tous les carnets d'un dossier, y compris ceux de ses sous-dossiers lorsque le mode choisi l'autorise.

Le terme **Set / Dossier** désigne dans l'interface le niveau d'organisation servant de contexte de publication. Il reste représenté par une icône de dossier simple.

### 5.3 Gestion de l'ordre

L'utilisateur peut modifier l'ordre des carnets par glisser-déposer.

L'ordre est stocké via `sort_order` et restauré à la réouverture.

### 5.4 Carnet

Le carnet est sélectionnable comme une unité de publication.

Un sélecteur **Carnet** doit permettre de choisir :

- un carnet précis du Set / Dossier actif ;
- **Tous les carnets** du Set / Dossier actif lorsque l'utilisateur souhaite publier ou filtrer plusieurs carnets avec le même périmètre.

Un clic sur un carnet dans l'arborescence affiche ses réglages effectifs et son contenu sans imposer automatiquement le périmètre de publication.

Le sélecteur Carnet et la sélection dans l'arborescence doivent rester synchronisés de manière prévisible.

### 5.5 Mise en page

Une mise en page est sélectionnable individuellement.

Un clic sur une mise en page permet de :

- l'identifier ;
- voir le carnet parent ;
- connaître les formats activés ;
- publier uniquement cette mise en page.

### 5.5.1 Règles visuelles des éléments

La représentation graphique de l'arborescence doit permettre de comprendre immédiatement le type d'élément et, pour les mises en page, le format d'export prévu.

Règles :

- **Dossier** → icône de dossier simple ;
- **Carnet** → icône de carnet simple ;
- **Mise en page PDF uniquement** → pictogramme PDF à la place de l'icône de feuille générique ;
- **Mise en page DWG uniquement** → pictogramme DWG à la place de l'icône de feuille générique ;
- **Mise en page PDF + DWG** → deux pictogrammes PDF et DWG côte à côte ;
- aucun badge PDF/DWG supplémentaire ne doit être ajouté au dossier ou au carnet pour répéter la même information ;
- le panneau de réglages à droite ne doit pas afficher de logos PDF/DWG décoratifs ou redondants.

La sélection active doit être indiquée par un traitement visuel discret : fond légèrement teinté et accent TAA Orange. L'information de sélection ne doit pas dépendre uniquement de la couleur.

Les pictogrammes de format servent à informer rapidement l'utilisateur ; les valeurs détaillées restent accessibles dans le panneau de réglages.

### 5.5.2 Sélection sans cases à cocher

L'arborescence n'utilise pas de cases à cocher pour choisir ce qui sera publié.

Le mode **Sélection** utilise directement la sélection des lignes :

- clic simple → élément courant ;
- `Ctrl + clic` → ajout/retrait dans une sélection multiple ;
- `Shift + clic` → sélection d'une plage lorsque l'implémentation le permet.

Lorsque le périmètre actif est **Tout le contenu** ou **Révision courante**, la sélection dans l'arborescence reste disponible pour naviguer et consulter les propriétés, mais elle ne réduit pas silencieusement le périmètre.

Une CheckBox reste réservée aux véritables options binaires des réglages, pas à la sélection des éléments de publication.

### 5.6 Action contextuelle et résumé

L'action principale doit refléter le contexte complet : Set / Dossier, Carnet et Périmètre.

Exemples :

```text
Set : DCE Architecture
Carnet : Plans DCE
Périmètre : Tout le contenu
→ Publier le carnet « Plans DCE »

Set : DCE Architecture
Carnet : Tous les carnets
Périmètre : Révision courante
→ Publier la révision courante du Set « DCE Architecture »

Set : DCE Architecture
Carnet : Plans DCE
Périmètre : Sélection
3 mises en page sélectionnées
→ Publier 3 mises en page
```

La barre de résumé inférieure doit afficher au minimum :

```text
Profil • Set / Dossier • Carnet • Périmètre • nombre de mises en page • formats
```

L'utilisateur doit pouvoir comprendre exactement ce qui sera publié avant de cliquer sur **Publier**.

### 5.7 Publication d'un dossier

La sélection d'un dossier déclenche une publication multiple :

```text
Dossier sélectionné
      ↓
Recherche récursive des carnets
      ↓
Résolution des réglages de chaque carnet
      ↓
Prévisualisation globale
      ↓
Validation
      ↓
Publication de chaque carnet
      ↓
Rapport global
```

Chaque carnet conserve sa propre destination et ses propres réglages effectifs. Une différence de configuration entre carnets ne doit jamais être masquée par l'agrégation.

---

## 6. Réglages persistants du carnet

Chaque carnet persistant mémorise ses réglages de publication lorsqu'ils sont définis localement.

### 6.1 Formats

```text
PDF : activé / désactivé
PDF : combiné / séparé
DWG : activé / désactivé
DWG : fusion des vues/liens activée / désactivée
```

### 6.2 Configuration DWG

Le carnet peut mémoriser le nom d'une configuration DWG native Revit.

La case **Forcer les couleurs vraies** surcharge `Colors` avec `ExportColorMode.TrueColor`. Décochée, elle conserve les couleurs du preset. La case **Fusionner les vues et les liens dans le DWG** pilote séparément `MergedViews`, activée par défaut.

### 6.3 Destination

Le carnet peut mémoriser son dossier de publication.

La destination peut également être héritée du dossier parent.

### 6.4 Nommage

Le modèle de nommage peut être mémorisé au niveau carnet ou hérité du dossier.

### 6.5 Modification d'un seul réglage

Une modification d'un contrôle ne doit sauvegarder que le champ réellement modifié.

Une valeur affichée parce qu'elle est héritée ne doit pas devenir une surcharge locale simplement parce qu'un autre réglage a été modifié.

---

## 7. Profils de publication

Les profils de publication sont implémentés comme mécanisme de configuration réutilisable.

Exemples de profils :

```text
PDF + DWG
PDF seul
PDF séparés
DWG seul
PDF combiné + DWG
```

Un profil peut être sélectionné puis appliqué à un carnet.

Le profil définit notamment :

```text
pdf_enabled
pdf_mode
dwg_enabled
dwg_setup_name
dwg_true_color
dwg_merge_views
```

### 7.1 Principe important

Le profil ne remplace pas les réglages propres au carnet concernant :

- la destination ;
- le modèle de nommage ;
- l'organisation métier du carnet.

L'application d'un profil produit des valeurs concrètes dans les paramètres de publication du carnet.

### 7.2 Profils personnalisés

L'interface permet de sauvegarder et supprimer des profils personnalisés.

Le stockage des profils doit rester indépendant de la persistance des carnets.

---

## 8. Héritage des réglages

L'héritage implémenté suit actuellement :

```text
Profil
  ↓
Dossier
  ↓
Carnet
```

Le niveau mise en page n'est pas un niveau de persistance autonome des réglages ; une publication de mise en page seule utilise les réglages effectifs de son carnet parent.

### 8.1 Principe

Chaque champ héritage peut être :

- défini au dossier ;
- surchargé au carnet ;
- remis à l'héritage.

Une valeur héritée doit être identifiable visuellement.

### 8.2 Retour à l'héritage

Le carnet dispose d'une action permettant de supprimer ses surcharges locales et de revenir aux réglages du dossier.

Cette action doit remettre les champs héritables à leur état non défini localement, et non recopier les valeurs effectives du dossier dans le carnet.

### 8.3 Résolution centralisée

La résolution est centralisée dans `SettingsResolver`.

```text
Profil
  ↓
Dossier
  ↓
Carnet
  ↓
Réglages effectifs
  ↓
Publication / Prévisualisation
```

Les exporteurs PDF/DWG ne doivent pas implémenter leur propre logique d'héritage.

---

## 9. Nommage des fichiers

L'utilisateur peut construire une règle de nommage à partir de variables.

### 9.1 Variables

```text
{carnet}
{numero}
{nom}
{nom_complet}
{projet}
{date}
{indice}
{dossier}
```

### 9.2 Paramètres Revit

Dans **Options avancées**, le champ de recherche filtre une liste construite à
l'ouverture de la fenêtre à partir du document actif. Elle contient les variables
intégrées, l'union des paramètres accessibles de toutes les feuilles et les
paramètres de **Informations sur le projet**. Les paramètres natifs, partagés et
personnalisés sont proposés, même vides ou en lecture seule. Les paramètres de
famille/type du cartouche ne sont pas des paramètres de feuille et ne sont pas
inclus dans ce catalogue.

Choisir un résultat puis **Insérer** ajoute sa variable à la position du curseur
(ou remplace le texte sélectionné) dans le modèle de nommage. Les libellés
« Feuille » et « Informations sur le projet » distinguent les deux sources.

```text
{feuille:Numéro de feuille}
{info_projet:Nom du projet}
{info_projet:Numéro du projet}-{feuille:Numéro de feuille}
```

Les noms exacts dépendent des paramètres présents et de la langue de Revit :
utiliser le sélecteur pour insérer le nom réel. Les modèles historiques
`{parametre:NomDuParametre}` restent compatibles et lisent la feuille.
`{projet}` conserve le titre du fichier Revit ; il est distinct de
`{info_projet:Nom du projet}`.

Les paramètres de feuille utilisent la feuille exportée en mode séparé et la
première feuille du carnet, dans son ordre, en mode combiné. Les paramètres des
informations sur le projet sont communs à toutes les feuilles.
Une valeur absente, vide ou ambiguë est signalée dans les variables non résolues ;
aucun homonyme n'est choisi arbitrairement. Les valeurs numériques utilisent le
texte formaté par Revit lorsqu'il existe ; zéro est une valeur valide.

Si plusieurs paramètres ont le même nom dans une source, le sélecteur insère
`{feuille_id:...}` ou `{info_projet_id:...}` avec une identité durable : identifiant
natif négatif, GUID partagé ou UniqueId de la définition de paramètre du projet.
Cette dernière identité reste liée au document ; elle n'est pas portable dans
un autre projet. Aucun ElementId positif n'est enregistré dans un modèle.
Les noms contenant des accolades utilisent également cette forme.
La lecture du modèle ne modifie aucun paramètre Revit.

Le catalogue et la lecture appartiennent à `services/naming_parameters.py` ;
`FilenameService` reste le point de résolution commun à l'aperçu et aux exports
PDF/DWG. La recherche et l'insertion sont des handlers canoniques d'`ExportWindow`,
sans injection de doublons par la couche de prévisualisation.

Validation hors Revit : **205 tests Python exécutés avec succès**, dont 10 cas ajoutés
pour le catalogue, les sources, les homonymes, les identités durables, les accents,
les valeurs typées/vides et l'insertion au curseur.

**Validation Revit 2025.4 : confirmée par l'utilisateur le 2026-10-01.**
Le sélecteur a été testé avec les paramètres de feuille et les Informations sur le projet,
ainsi que le workflow de nommage/export associé. Les anciens modèles restent compatibles.

### 9.3 Éditeur

Dans la fenêtre principale, « Aperçu du nom » affiche le nom sécurisé sans
extension, calculé par le même service que la prévisualisation de publication.
Il utilise la feuille sélectionnée, ou la première feuille du carnet si le carnet
est sélectionné, et le dossier parent. Les variables non résolues et erreurs
sont visibles ; une erreur technique ne doit pas être remplacée par un simple tiret.

L'interface propose :

- champ de modèle ;
- liste de variables ;
- insertion assistée ;
- prévisualisation ;
- détection des variables indisponibles ;
- sécurisation des caractères interdits par Windows ;
- détection des noms identiques.

### 9.4 Contexte du livrable

Le nom final est calculé selon le contexte réel :

```text
PDF combiné
→ contexte carnet

PDF séparé
→ contexte mise en page

DWG séparé
→ contexte mise en page
```

Le service de nommage est commun à la prévisualisation et à la publication.
Les réglages effectifs, y compris le modèle hérité du dossier, sont transmis sur
une copie de publication ; les surcharges persistantes du carnet restent intactes.

Pour les PDF séparés, Revit exporte toutes les feuilles en une seule opération
`Combine=False` dans un sous-dossier temporaire de la destination. Une règle
native explicite `taa_` + numéro de feuille permet d'associer les fichiers sans
dépendre de leur ordre. Chaque PDF attendu doit exister et être non vide avant
livraison sous le nom TAA annoncé. Les noms en doublon (casse Windows comprise)
dans un carnet bloquent la publication ; utiliser par exemple `{carnet}-{numero}`.
Les caractères interdits dans un nom Windows (par exemple `PC 09*`) sont
sécurisés pour le nom temporaire et le nom TAA. Après export, les PDF natifs
sont associés aux feuilles par une clé unique qui ignore la ponctuation que
Revit peut nettoyer. Si deux numéros deviennent ambigus ou si les fichiers
produits ne correspondent pas, l'export est signalé en erreur et les PDF
temporaires sont conservés pour diagnostic. La maquette reste inchangée.

Les fichiers existants sont sauvegardés le temps du remplacement. En cas d'échec,
une restauration est tentée et le rapport indique le dossier temporaire conservé,
ainsi que tout échec de restauration. Un export échoué ne fournit aucun chemin
comme livré. Aucun paramètre de feuille n'est modifié pour le nommage.
La validation du moteur natif reste à effectuer dans Revit 2025.4.

### 9.5 Architecture

```text
FilenameTemplateService
        ↓
VariableResolver
        ↓
ConflictDetector
        ↓
FilenameService
        ↓
Nom sécurisé
```

---

## 10. Prévisualisation avant publication

La prévisualisation est désormais une étape obligatoire du workflow de publication implémenté.

Avant de produire les fichiers :

```text
Sélection
   ↓
Résolution
   ↓
Prévisualisation
   ↓
Confirmation
   ↓
Publication
```

### 10.1 Informations affichées

La prévisualisation présente notamment :

- carnet ;
- mise en page ;
- format ;
- mode combiné/séparé ;
- nom final ;
- destination ;
- statut.

### 10.2 Contrôles

La prévisualisation doit détecter ou signaler :

- feuille manquante ;
- feuille non imprimable ;
- carnet vide ;
- configuration absente ;
- destination manquante ou inaccessible ;
- nom invalide ;
- variable inconnue ou indisponible ;
- collision entre livrables ;
- fichier déjà existant ;
- absence de format activé.

### 10.3 Multi-carnets

Pour une publication de dossier, la prévisualisation est globale mais chaque ligne conserve :

```text
Carnet
Mise en page
Format
Nom final
Chemin complet
Statut
```

Si plusieurs destinations sont utilisées, elles doivent rester visibles individuellement.

### 10.4 Principe architectural

Prévisualisation et publication utilisent les mêmes services de résolution.

```text
              ┌──→ Prévisualisation
Résolution ───┤
              └──→ Publication
```

Il ne doit pas exister un calcul simplifié du nom, de la destination ou du contenu uniquement pour l'aperçu.

---

## 11. Sources dynamiques et évolution du projet

Une publication dynamique doit pouvoir suivre l'évolution du modèle.

```text
Règle
 ↓
Résolution Revit
 ↓
Nouvelles mises en page détectées
 ↓
Contenu du carnet mis à jour
 ↓
Publication
```

Export doit distinguer :

- nouvel élément détecté ;
- élément attendu mais introuvable ;
- élément retiré de la règle ;
- élément exclu volontairement.

Pour un carnet fixe, un élément supprimé doit rester identifiable comme manquant et ne doit jamais être remplacé silencieusement par un autre élément portant le même numéro.

---

## 12. Contexte et périmètres de publication

Le moteur doit distinguer le **contexte de publication** du **filtre de périmètre**.

### 12.1 Contexte

Le contexte est défini par :

```text
Profil
Set / Dossier
Carnet = carnet précis | Tous les carnets
```

Le Set / Dossier et le Carnet déterminent l'espace dans lequel le périmètre est évalué.

### 12.2 Périmètres exposés à l'utilisateur

Trois choix doivent être disponibles :

```text
Tout le contenu
Révision courante
Sélection
```

#### Tout le contenu

- carnet précis → toutes les mises en page de ce carnet ;
- Tous les carnets → toutes les mises en page des carnets du Set / Dossier concerné.

Le libellé peut être contextualisé dans l'interface en **Tout le carnet** ou **Tous les carnets** pour rendre l'action plus explicite.

#### Révision courante

Le mode **Révision courante** filtre le contexte actif pour ne conserver que les mises en page rattachées à la révision courante.

La définition technique exacte de « révision courante » doit s'appuyer sur les données de révision réellement disponibles dans Revit 2025.4 et être validée dans Revit avant implémentation définitive. Aucun rapprochement par texte ou nom de feuille ne doit être utilisé comme substitut silencieux.

Le nombre de mises en page concernées doit être visible avant publication.

#### Sélection

Le mode **Sélection** publie uniquement une ou plusieurs mises en page sélectionnées dans l'arborescence.

La sélection multiple doit respecter le contexte Set / Dossier + Carnet actif et ne doit pas inclure silencieusement des éléments hors contexte.

### 12.3 Modèle interne cible

Le modèle de périmètre cible doit pouvoir représenter explicitement :

```text
ENTIRE_SCOPE
CURRENT_REVISION
SELECTED_ITEMS
```

Les constantes historiques `ENTIRE_SET`, `SELECTED_ITEMS` et `SELECTED_NODES` peuvent rester supportées pendant la transition interne, mais l'interface ne doit pas exposer une terminologie ambiguë.

`MODIFIED_ONLY` reste une évolution distincte et ne doit pas être confondu avec **Révision courante**.

```text
MODIFIED_ONLY
```

correspond à un filtrage basé sur l'état de publication ou les modifications détectées depuis une exécution précédente.

### 12.4 Publication multiple

Lorsque **Tous les carnets** est sélectionné, chaque carnet est résolu indépendamment, notamment pour :

- héritage ;
- destination ;
- nommage ;
- PDF/DWG ;
- collisions.

Le filtre de périmètre actif est ensuite appliqué à chaque carnet dans le contexte retenu.

### 12.5 Résumé obligatoire avant publication

Avant publication, l'interface doit afficher une synthèse du type :

```text
Profil : DCE
Set : DCE Architecture
Carnet : Plans DCE
Périmètre : Révision courante
12 mises en page
PDF + DWG
```

Cette synthèse doit être cohérente avec la prévisualisation et avec le périmètre réellement transmis au moteur.

## 13. PDF

Le PDF utilise en priorité le moteur PDF natif de Revit 2025.4.

Deux modes sont conservés :

- combiné ;
- séparé.

Les réglages effectivement exposés par l'API Revit doivent être vérifiés sur la version cible avant toute nouvelle option.

---

## 14. DWG

La configuration native Revit reste la base des options : liste par
`DWGExportOptions.GetPredefinedSetupNames`, chargement par `GetPredefinedOptions`.
TAA surcharge seulement `MergedViews` et, si demandé, `Colors` (True Color).
Une configuration native devenue indisponible reste mémorisée et provoque une
erreur explicite à l'export, sans remplacement silencieux.

La stratégie d'appel DWG est désormais **automatique et invisible pour
l'utilisateur** :

- une seule feuille → appel Revit simple ;
- plusieurs feuilles → un seul appel natif Revit contenant les identifiants ordonnés ;
- Revit produit néanmoins un DWG par feuille ; un lot d'appel n'est pas un DWG unique.

Le champ historique `dwg_mode` reste lisible dans les anciens stockages pour assurer
la compatibilité, mais il n'influence plus l'exécution et n'est plus exposé dans l'UI.

La case **Fusionner les vues et les liens dans le DWG** reste indépendante de cette
stratégie. Cochée, `MergedViews=True` ; décochée, `MergedViews=False` et références
externes lorsque applicable. Le défaut demandé est True, aussi pour les anciens
réglages sans champ `dwg_merge_views`. Images et autres annexes peuvent subsister.

L'engrenage ferme Export avant de poster la commande de configurations DWG/DXF
native. Fermer celle-ci puis rouvrir Export : liste rechargée, carnets temporaires
et sélection restaurés dans le même document/session. **Actualiser** relit aussi
la liste sans modifier les surcharges héritées. La disponibilité réelle du membre
API est vérifiée au clic ; l'ouverture native reste à valider dans Revit 2025.4.

L'aperçu précise preset et références. Pour plusieurs feuilles, il annonce la
stratégie automatique et le nombre de DWG attendus ; le rapport affiche le dossier
réel lorsque les noms finaux sont déterminés par Revit.
Analyse, surcharges et limites : [24_Export_Reglages_DWG.md](24_Export_Reglages_DWG.md).
Recette non encore validée : [25_Export_Recette_DWG.md](25_Export_Recette_DWG.md).

---

## 15. Organisation des dossiers de sortie

La destination est la racine de publication de chaque carnet.

Le service `OutputPathService` doit construire les chemins de sortie.

Les exporteurs PDF/DWG ne doivent pas construire leur propre arborescence.

Une publication multi-carnets doit respecter les destinations propres à chaque carnet.

---

## 16. Collisions et écrasement

La stratégie cible reste :

```text
ASK
SKIP
OVERWRITE
RENAME
```

`OVERWRITE` ne doit jamais être implicite.

Chaque collision doit être visible dans la prévisualisation et dans le rapport.

---

## 17. Workflow cible complet

### 17.1 Publication par sélection de mises en page

```text
Profil
      ↓
Set / Dossier
      ↓
Carnet
      ↓
Périmètre = Sélection
      ↓
Sélection d'une ou plusieurs mises en page
      ↓
SELECTED_ITEMS
      ↓
Résolution des réglages effectifs
      ↓
Validation
      ↓
Prévisualisation
      ↓
Confirmation
      ↓
Publication
```

### 17.2 Publication de tout le contenu

```text
Profil
      ↓
Set / Dossier
      ↓
Carnet précis ou Tous les carnets
      ↓
Périmètre = Tout le contenu
      ↓
Résolution du ou des carnets
      ↓
Réglages effectifs
      ↓
ENTIRE_SCOPE
      ↓
Validation
      ↓
Prévisualisation
      ↓
Confirmation
      ↓
Publication
```

### 17.3 Publication de la révision courante

```text
Profil
      ↓
Set / Dossier
      ↓
Carnet précis ou Tous les carnets
      ↓
Périmètre = Révision courante
      ↓
Résolution des mises en page du contexte
      ↓
Filtrage CURRENT_REVISION
      ↓
Validation
      ↓
Prévisualisation
      ↓
Confirmation
      ↓
Publication
```

Si aucune mise en page n'appartient à la révision courante, l'interface doit l'indiquer clairement et empêcher une publication vide involontaire.

### 17.4 Organisation par glisser-déposer

```text
Sélection d'un ou plusieurs carnets
      ↓
Glisser
      ↓
Indicateur visuel de destination/insertion
      ↓
Déplacement repository
      ↓
Réindexation de l'ordre
      ↓
Rafraîchissement de l'arborescence
```

Le déplacement doit être persistant.

---

## 18. Architecture logicielle cible

```text
UI WPF
  ↓
Application / ViewModels
  ↓
Publication Services
  ├── PublicationProfileService
  ├── PublicationFolderService
  ├── PublicationSetService
  ├── PublicationResolver
  ├── PublicationTreeService
  ├── PublicationTreeDragDrop
  ├── SettingsResolver
  ├── FilenameTemplateService
  ├── ValidationService
  ├── OutputPathService
  ├── PdfExportService
  ├── DwgExportService
  ├── PublicationBatchService
  ├── ExecutionService
  └── PublicationReportService
        ↓
Revit API / Common TAA
```

### 18.1 Responsabilités importantes

- une responsabilité par classe ;
- aucune logique métier complexe dans les fenêtres WPF ;
- aucun chemin de sortie construit dans les exporteurs ;
- aucun réglage DWG dupliqué inutilement ;
- persistance indépendante de la session ;
- accès Revit centralisé ;
- exceptions explicites ;
- journalisation structurée ;
- prévisualisation et publication fondées sur les mêmes résolutions.

### 18.2 Glisser-déposer WPF

Le TreeView WPF ne fournit pas nativement la sélection multiple. L'implémentation utilise donc un état de sélection explicite et un `DataObject` WPF avec format de données explicite pour transporter les éléments déplacés.

L'indicateur de dépôt doit permettre de distinguer visuellement :

- déplacement dans un dossier ;
- insertion avant un carnet ;
- ajout dans un carnet ;
- insertion avant une mise en page.

---

## 19. Persistance

Les carnets, dossiers et profils persistants doivent être stockés dans un format versionnable et migrable.

Les données doivent permettre de reconstruire fidèlement :

- l'identité ;
- le nom ;
- le dossier parent ;
- l'ordre ;
- la source ;
- les éléments ;
- les réglages locaux ;
- le modèle de nommage ;
- la version du schéma.

Les `UniqueId` Revit doivent être privilégiés pour les références intersessions.

Un élément supprimé ne doit pas être remplacé silencieusement.

L'ordre des carnets dans les dossiers et l'ordre des mises en page dans les carnets sont des informations persistantes et doivent survivre à une fermeture/réouverture.

---

## 20. Exécution et rapport

Chaque publication est une exécution structurée.

```text
PREPARING
VALIDATING
RUNNING
COMPLETED
FAILED
CANCELLED
```

Le rapport doit indiquer au minimum :

- profil ou contexte ;
- carnet ;
- mise en page ;
- format ;
- mode ;
- chemin complet ;
- nom final ;
- statut ;
- durée ;
- message.

Pour une publication de dossier, le rapport doit permettre d'identifier le résultat de chaque carnet et de chaque livrable.

Les échecs partiels doivent rester traçables.

Le rapport affiche intégralement les erreurs et avertissements globaux dans une
zone en lecture seule, sélectionnable et défilante en bas de fenêtre. Ce texte
reste accessible même si l'échec n'a produit aucune ligne de livrable. Une ligne
en échec ne doit jamais afficher « Export terminé ». Les lignes utilisent leur
propre nom de carnet et le champ `path` transmis par l'orchestrateur.

---

## 21. Validation

Avant toute publication :

- résolution des éléments ;
- éléments manquants ;
- exportabilité ;
- configuration PDF/DWG ;
- destination ;
- création des dossiers ;
- nommage ;
- collisions ;
- cohérence des réglages ;
- périmètre.

```text
Résolution
   ↓
Validation
   ↓
Prévisualisation
   ↓
Confirmation
   ↓
Publication
```

Une erreur critique doit bloquer la publication concernée.

Pour une publication multiple, une erreur sur un carnet ne doit pas masquer les erreurs ou réussites des autres carnets.

---

## 22. Tests et non-régression

Les tests suivent `docs/08_Testing.md` et le registre global `docs/11_BUGS_Prevention_Registry.md`.

Toute modification du module Export doit notamment vérifier :

- chargement WPF/XAML dans Revit 2025.4 ;
- navigation de l'arborescence ;
- création et sélection de dossier ;
- création d'un carnet dans le dossier sélectionné ;
- filtrage par projet courant ;
- sélection d'un carnet ;
- sélection d'une mise en page ;
- sélection multiple ;
- choix du Profil ;
- choix du Set / Dossier ;
- choix d'un Carnet précis ;
- choix « Tous les carnets » ;
- périmètre Tout le contenu ;
- périmètre Révision courante ;
- périmètre Sélection avec une et plusieurs mises en page ;
- synchronisation du résumé de publication avec le contexte et le périmètre actifs ;
- absence de publication hors du Set / Dossier ou du Carnet actif ;
- absence de cases à cocher pour la sélection des éléments de l'arborescence ;
- sélection visible par traitement de ligne ;
- pictogramme PDF pour une mise en page PDF uniquement ;
- pictogramme DWG pour une mise en page DWG uniquement ;
- deux pictogrammes côte à côte pour une mise en page PDF + DWG ;
- absence de pictogrammes PDF/DWG décoratifs dans le panneau de réglages ;
- glisser-déposer d'un carnet vers un dossier ;
- glisser-déposer avant un carnet ;
- conservation de l'ordre après réouverture ;
- publication du bon périmètre ;
- publication récursive d'un dossier ;
- persistance des réglages ;
- héritage dossier → carnet ;
- retour à l'héritage ;
- application d'un profil ;
- résolution des carnets ;
- nommage ;
- prévisualisation ;
- PDF ;
- DWG ;
- collisions ;
- rapport ;
- absence d'erreurs de handlers WPF lors du workflow complet.

Avant chaque modification de code et avant chaque commit, le registre global des bugs doit être consulté conformément à `08_Testing.md`.

Tout bug significatif doit être capitalisé dans `11_BUGS_Prevention_Registry.md`.

---

## 23. Compatibilité

Cible officielle :

- Revit **2025.4** ;
- pyRevit **5.x** ;
- IronPython compatible avec l'environnement pyRevit utilisé.

Toute API non garantie doit être validée dans l'environnement réel.

---

## 24. État d'implémentation

### Implémenté et validé dans le workflow actuel

- arborescence Dossier → Carnet → Mise en page ;
- dossiers persistants ;
- création d'un carnet dans le dossier sélectionné ;
- carnets persistants et temporaires ;
- carnets générés par paramètre ;
- filtrage des carnets selon le projet Revit courant ;
- sélection contextuelle dossier/carnet/mise en page ;
- publication d'un carnet entier ;
- publication d'une mise en page seule ;
- réglages PDF/DWG persistants au niveau carnet ;
- configurations DWG natives ;
- True Color ;
- destination persistante ;
- éditeur de nommage avec variables et paramètres Revit ;
- profils de publication et profils personnalisés ;
- héritage dossier → carnet ;
- surcharge locale par champ ;
- retour à l'héritage ;
- prévisualisation avant publication ;
- contrôles de cohérence et collisions dans la prévisualisation ;
- publication récursive d'un dossier ;
- prévisualisation globale d'une publication multiple ;
- respect des destinations propres à chaque carnet ;
- rapport de publication ;
- glisser-déposer des carnets ;
- sélection multiple `Ctrl` / `Shift` ;
- déplacement groupé ;
- insertion avant un carnet ;
- réorganisation persistante des carnets ;
- conservation de l'ordre des mises en page dans un carnet ;
- mécanisme anti-régression et registre global des bugs.

### Limites actuelles

- la nouvelle barre de contexte **Profil / Set / Dossier / Carnet / Périmètre** est une cible UI/UX à raccorder au XAML ;
- le mode **Révision courante** doit encore être implémenté et validé avec les données de révision Revit 2025.4 ;
- le choix **Tous les carnets** dans le sélecteur Carnet est une cible à intégrer au workflow de publication ;
- `MODIFIED_ONLY` n'est pas encore implémenté ;
- les règles dynamiques avancées restent une cible ;
- les niveaux supplémentaires de l'arborescence ne sont pas prioritaires ;
- les comportements API Revit non garantis doivent toujours être validés dans Revit 2025.4 réel ;
- une couche de compatibilité existe actuellement autour de certains handlers historiques de `ExportWindow` et devra être simplifiée lors d'une refactorisation UI ultérieure.

---

## 25. Roadmap restante

### Refonte UI/UX Export

À appliquer au XAML actuel avant de considérer la nouvelle interface comme implémentée :

- barre de contexte visible avec **Profil**, **Set / Dossier**, **Carnet** et **Périmètre** ;
- possibilité de choisir un carnet précis ou **Tous les carnets** ;
- trois périmètres : **Tout le contenu**, **Révision courante**, **Sélection** ;
- résumé inférieur affichant clairement le contexte actif, le nombre de mises en page et les formats ;
- arborescence principale à gauche et réglages contextuels à droite ;
- suppression des cases à cocher utilisées pour la sélection de l'arborescence ;
- sélection simple et multiple par ligne ;
- dossier et carnet avec leurs pictogrammes simples ;
- pictogrammes PDF/DWG portés uniquement par les mises en page selon leur format effectif ;
- deux pictogrammes côte à côte lorsqu'une mise en page produit PDF + DWG ;
- suppression des pictogrammes PDF/DWG redondants dans le panneau de réglages ;
- bouton **Publier** comme action principale mise en avant en TAA Orange ;
- validation du rendu réel dans Revit 2025.4.

### Étape 07 — Historique et « modifiés uniquement »

Le socle, la prévisualisation et le raccordement simple/multiple sont implémentés.
Restent la validation Revit 2025.4 et la consolidation ultérieure de la surcouche
`stage07`. Les correctifs de préparation TEST-14 sont testés hors Revit : nommage
PDF séparé, héritage du modèle et instance unique du glisser-déposer.
Voir `17_Export_Preparation_TEST14.md` et la roadmap racine.

### Étape 08 — Dynamique avancé

À réaliser :

- règles combinées ;
- prévisualisation de résolution ;
- détection des nouveaux éléments ;
- diagnostic des éléments retirés ;
- exclusions explicites.

### Étape 09 — Extensibilité

Préparer sans priorité immédiate :

- vues publiables ;
- IFC ;
- autres formats ;
- automatisations complémentaires.

---

## 26. Critères de réussite de la cible Export

Export sera considéré comme ayant atteint sa cible lorsque l'utilisateur pourra :

1. choisir explicitement un Profil, un Set / Dossier, un Carnet précis ou Tous les carnets, puis un périmètre Tout le contenu / Révision courante / Sélection ;
2. ouvrir une arborescence de publications claire, sans cases à cocher de sélection, où les mises en page indiquent visuellement leur format PDF, DWG ou PDF + DWG ;
3. créer et organiser des dossiers ;
4. créer un carnet directement dans le dossier choisi ;
5. réorganiser les carnets par glisser-déposer ;
6. sélectionner plusieurs carnets et les déplacer ensemble ;
7. sélectionner un carnet et publier tout son contenu ;
8. sélectionner une ou plusieurs mises en page et publier uniquement cette sélection ;
9. sélectionner un dossier et publier récursivement ses carnets ;
10. publier uniquement les mises en page de la révision courante dans le contexte choisi ;
11. conserver les réglages du carnet entre les sessions ;
12. hériter des réglages d'un dossier et revenir à l'héritage ;
13. appliquer un profil de publication ;
14. définir une règle de nommage assistée ;
15. prévisualiser les fichiers avant publication ;
16. publier PDF et DWG selon les configurations Revit appropriées ;
17. gérer les collisions explicitement ;
18. organiser les carnets par dossiers et conserver leur ordre ;
19. utiliser des carnets fixes ou dynamiques ;
20. suivre les résultats dans un rapport ;
21. préparer ultérieurement la publication des seuls éléments modifiés.
> **La réussite d'Export se mesure à la qualité du workflow de publication, pas uniquement à la capacité de produire un PDF ou un DWG.**

---

## 27. Règles fonctionnelles non négociables

1. Le moteur de publication ne dépend pas directement du mode de création du carnet.
2. Une sélection fixe ne doit pas être confondue avec une règle dynamique.
3. Le carnet est l'unité persistante principale de configuration.
4. La sélection d'une mise en page doit pouvoir réduire le périmètre à cette seule mise en page.
5. La sélection d'un dossier doit publier récursivement les carnets descendants.
6. Les réglages persistants ne doivent jamais être perdus silencieusement.
7. Une modification d'un champ ne doit pas transformer les autres valeurs héritées en surcharges locales.
8. Les réglages hérités sont résolus avant l'appel aux exporteurs.
9. Les exporteurs ne construisent jamais l'arborescence de sortie.
10. Une collision ne doit jamais être résolue silencieusement.
11. Un élément manquant ne doit jamais être remplacé silencieusement par un autre.
12. Prévisualisation et publication utilisent les mêmes services de résolution.
13. La validation est indépendante de l'interface.
14. Les configurations natives Revit sont réutilisées lorsqu'elles sont réellement disponibles via l'API cible.
15. Les comportements Revit non garantis sont documentés et testés.
16. L'ordre manuel des carnets et mises en page est une donnée persistante.
17. Le glisser-déposer doit respecter les règles de destination et d'insertion définies par l'interface.
18. Les erreurs reproductibles sont capitalisées dans `11_BUGS_Prevention_Registry.md`.
19. Avant toute modification de code et avant chaque commit, le registre global des bugs est consulté.
20. Le Set / Dossier, le Carnet et le Périmètre sont des notions distinctes et ne doivent pas être déduits silencieusement les uns des autres.
21. Le mode Révision courante est distinct de MODIFIED_ONLY.
22. En mode Sélection, seules les mises en page explicitement sélectionnées dans le contexte actif sont publiées.

---

## 28. Correspondance avec les étapes réalisées

```text
Étape 01 → Sélection contextuelle Export                 ✅
Étape 02 → Éditeur de nommage Export                     ✅
Étape 03 → Profils de publication                            ✅
Étape 04 → Héritage dossier → carnet                        ✅
Étape 05 → Prévisualisation                                 ✅
Étape 06 → Publication multiple par dossier                 ✅
             + sélection multiple / drag-and-drop           ✅
             + ordre persistant                              ✅

Étape 07 → Historique / MODIFIED_ONLY                       ⏳
Étape 08 → Dynamique avancé                                  ⏳
Étape 09 → Extensibilité                                     ⏳
```

Cette section doit être maintenue à jour à chaque changement de comportement significatif du module Export.

## Compléments de la fenêtre principale — 2026-10-01

- Le menu « Dossier » du panneau de réglages est retiré. Il déplaçait un carnet ;
  cette opération reste disponible par glisser-déposer dans l'arborescence.
- Ctrl / Maj permettent de sélectionner plusieurs carnets ou dossiers puis de
  les supprimer avec une confirmation commune listant les noms. Les carnets de
  session sont aussi sélectionnables. Les dossiers sont supprimés du plus profond
  au parent, seulement s'ils sont vides ; les contenus non sélectionnés et Général
  sont conservés. Un bilan indique les éléments conservés ou en erreur. La commande
  ne supprime jamais de feuilles Revit. Les feuilles du carnet ne sont pas des cibles
  de cette commande. La sélection multiple ne change pas le périmètre de publication.
- Les mises en page affichent une feuille PDF rouge, DWG bleue ou les deux selon
  les réglages effectifs du carnet, y compris l'héritage de tous ses parents.
  Sans format actif, une feuille neutre avec infobulle reste visible.
- Le pied de fenêtre indique dossier, carnet, périmètre, nombre d'occurrences de
  mises en page prévues, formats et résolutions PDF. Le dossier inclut ses descendants ;
  une feuille seule compte pour une occurrence. Les éléments sans format sont
  signalés à part. L'aperçu reste responsable de valider disponibilité et exportabilité.
  Aucune taille de fichier n'est estimée. Les profils étant des préréglages copiés,
  le résumé n'annonce pas de lien permanent avec un profil.
- La qualité PDF propose 72, 144, 300, 600, 1200, 2400, 3600 ou 4000 DPI, avec
  300 par défaut. Le champ `pdf_quality` est héritable, surchargeable et enregistré
  dans les carnets, dossiers et profils ; les anciens documents héritent du défaut.
  Il est transmis au convertisseur existant `PDFExportQualityType` pour les exports
  combinés et séparés. Il règle la résolution, sans forcer la rastérisation.
- Le bouton Export du ruban reçoit l'icône orange feuille/export de la charte,
  livrée dans `icon.png` et `icon.dark.png`, avec source SVG dans les ressources.
  Recharger pyRevit après mise à jour pour reconstruire le ruban.

Les services `publication_overview.py` et `publication_tree_delete.py` portent les
calculs de résumé et la suppression sans dépendance WPF. L'intégration conserve
le handler canonique de suppression ; `ExportWindow` assure le rendu et son actualisation.

## Interface compacte et paramètres PDF — 2026-10-01

La fenêtre s'ouvre en 1320 × 760 unités WPF (minimum 1060 × 620), en conservant
Segoe UI 13 px. Profil et héritage sont compacts, la provenance complète des champs
reste en infobulle. PDF et DWG utilisent des rangées avec retour à la ligne ; modes
combiné/séparé et True Color sont conservés. Destination et modèle de nommage sont
accessibles directement. Les variables se trouvent dans « Options avancées »,
replié initialement. Le défilement reste un secours. Le résumé, Aperçu et Publier
restent fixes. Aperçu ouvre le contrôle des livrables sans bouton de confirmation ;
Publier conserve le passage par l'aperçu puis la confirmation existante.

La destination saisie au clavier est maintenant enregistrée à la perte de focus,
comme la destination choisie par Parcourir. Aucun autre réglage n'est enregistré
comme surcharge lors de cette action.

La case **« Créer un dossier au nom du carnet »** pilote
`separate_carnet_subfolder` (héritable, True par défaut), mais son sens n'est plus
lié à « séparé/combiné ». Cochée, elle crée toujours `NomCarnet/PDF` et
`NomCarnet/DWG`. Décochée, elle retire ces dossiers de format/carnet tout en
conservant les sous-dossiers de l'arborescence de publication. Le même calcul de
chemin est utilisé par l'aperçu et l'export réel. Cette préférence de destination
n'est pas incluse dans les profils techniques PDF/DWG.

Le bouton de configuration PDF ouvre « Paramètres PDF », organisé en Options et
Traitement vectoriel/raster. Les huit champs booléens du contrat `pdf_options.py`
sont héritables, persistants et inclus dans les profils personnalisés. Les anciens
profils appliquent les valeurs par défaut TAA pour ces nouveaux champs. Le dialogue
ne sauvegarde que les champs réellement modifiés après Appliquer ; Annuler ou fermer
ne modifie rien. Rétablir les valeurs par défaut prépare une saisie, sans sauvegarde
avant Appliquer. Le vectoriel reste le défaut ; il n'empêche pas Revit de rastériser
les vues qui l'exigent. La qualité DPI principale reste raccordée à ExportQuality.

| Option | Propriété publique PDFExportOptions | Défaut TAA |
|---|---|---|
| Liens en bleu | ViewLinksInBlue | False |
| Masquer plans de référence/construction | HideReferencePlane | True |
| Masquer étiquettes non référencées | HideUnreferencedViewTags | False |
| Bords masquant les lignes coïncidentes | MaskCoincidentLines | False |
| Masquer zones de définition | HideScopeBoxes | True |
| Masquer limites de cadrage | HideCropBoundaries | True |
| Demi-teinte par lignes fines | ReplaceHalftoneWithThinLines | False |
| Traitement raster forcé | AlwaysUseRaster | False |

La présence de chaque propriété est contrôlée sur l'API réellement chargée avant
l'affichage du dialogue. Un contrôle indisponible est désactivé ; aucun substitut
fictif n'est envoyé à l'exporteur. Une valeur non prise en charge différente du défaut produit une
erreur explicite. Le masquage des lignes coïncidentes est désactivé dans le dialogue
en traitement raster, tout en conservant sa valeur pour un retour au vectoriel.

**Arrière-plan : limitation V1 d'intégration, pas absence de l'API.**
`SetExportInBackground` existe dans l'API native, mais le flux TAA actuel attend les
PDF pour les vérifier, les renommer et les livrer. La case est donc désactivée et
expliquée. L'exporteur demande explicitement un traitement synchrone lorsqu'il
dispose de la méthode. Activer l'arrière-plan nécessite un suivi de fin des tâches,
un rapport différé et une livraison sécurisée adaptés ; ce travail est reporté.

Les pictogrammes PDF/DWG ont le libellé dans la feuille à coin plié. L'icône Export
est redessinée depuis le SVG en orange UI, plus grande dans son carré transparent,
sans texte dessiné. PNG 16/32/96 px fournis, bundle pyRevit en 96 px clair/sombre.
Le nom du bouton reste affiché par pyRevit ; le nom du panneau Export est distinct.

Référence des membres publics : documentation Autodesk PDFExportOptions,
https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/e4236fc8-f8e7-fc74-1b81-9e3a4d9e966b.htm
Cette référence publiée décrit l'API 2026 ; le contrôle de présence est donc aussi
réalisé à l'exécution sur Revit 2025.4. L'environnement de développement ne contient
pas sa DLL et ne permet pas de certifier l'exécution réelle des membres.

## Réglages DWG indépendants — 2026-10-07

Ajout de `dwg_merge_views` nullable/héritable à tous les niveaux. `None` continue
d'hériter ; la résolution applique True sans réécrire les anciens JSON. L'UI ne
sauvegarde que le champ modifié. Les profils personnalisés conservent False.
Les hooks du smartbutton, le batch dossier et le chemin de secours transmettent
la même valeur. Les réglages PDF et la progression existante sont inchangés.
La stratégie DWG n'est plus un choix utilisateur : une feuille utilise un appel
simple, plusieurs feuilles un lot natif Revit. L'ancien `dwg_mode` est conservé
uniquement pour la lecture des stockages historiques. L'interface a été compactée
pour respecter la cible Full HD : les réglages courants doivent rester visibles sans
défilement vertical obligatoire à 1920 × 1080 ; le ScrollViewer reste un secours.

Statut : tests hors Revit uniquement ; validation utilisateur Revit 2025.4 attendue.
