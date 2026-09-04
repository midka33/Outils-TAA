# Outils TAA – Outil Export

**Version :** 4.0  
**Statut :** Spécification fonctionnelle de référence et cible d'évolution  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Année :** 2026

---

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

### 2.3 La sélection est contextuelle

La sélection dans l'arborescence définit directement le périmètre de publication :

```text
Sélection d'une mise en page → publier cette mise en page
Sélection d'un carnet       → publier tout le carnet
Sélection d'un dossier      → publier les carnets du dossier et de ses sous-dossiers
```

Le bouton principal reflète le contexte courant afin de rendre l'action immédiatement compréhensible.

### 2.4 L'arborescence est le point central de l'interface

L'écran principal fonctionne comme un explorateur de publications :

```text
Arborescence                     Réglages / aperçu
────────────────────             ─────────────────────
📁 DCE                           Carnet : Plans
  📦 Plans                       PDF : ☑ Combiné
    📄 A101 – RDC                DWG : ☑ Séparé
    📄 A102 – R+1                Nom : ...
  📦 Coupes                      Destination : ...
    📄 A201 – Coupe AA
```

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

## 5. Arborescence Publisher TAA

### 5.1 Structure

```text
Dossier
├── Carnet
│   ├── Mise en page
│   └── Mise en page
└── Carnet
```

Les dossiers peuvent être imbriqués.

### 5.2 Gestion des dossiers

Le gestionnaire doit permettre de :

- créer un dossier ;
- sélectionner un dossier ;
- créer un carnet directement dans le dossier sélectionné ;
- déplacer ultérieurement un carnet vers un autre dossier ;
- conserver l'identité et les réglages du carnet lors du déplacement ;
- publier tous les carnets d'un dossier, y compris ceux de ses sous-dossiers.

### 5.3 Gestion de l'ordre

L'utilisateur peut modifier l'ordre des carnets par glisser-déposer.

L'ordre est stocké via `sort_order` et restauré à la réouverture.

### 5.4 Carnet

Le carnet est sélectionnable comme une unité de publication.

Un clic sur un carnet affiche ses réglages effectifs et son contenu.

### 5.5 Mise en page

Une mise en page est sélectionnable individuellement.

Un clic sur une mise en page permet de :

- l'identifier ;
- voir le carnet parent ;
- connaître les formats activés ;
- publier uniquement cette mise en page.

### 5.6 Action contextuelle

```text
Aucune sélection
→ action de publication inactive ou information

Carnet sélectionné
→ Publier le carnet « DCE »

Mise en page sélectionnée
→ Publier la mise en page

Dossier sélectionné
→ Publier le dossier « DCE »
```

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
DWG : combiné / séparé
```

### 6.2 Configuration DWG

Le carnet peut mémoriser le nom d'une configuration DWG native Revit.

Le réglage **Couleur vraie / True Color** reste une préférence TAA lorsque l'option est réellement disponible dans la configuration utilisée.

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
PDF + DWG combinés
```

Un profil peut être sélectionné puis appliqué à un carnet.

Le profil définit notamment :

```text
pdf_enabled
pdf_mode
dwg_enabled
dwg_mode
dwg_setup_name
dwg_true_color
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

```text
{parametre:NomDuParametre}
```

Exemples :

```text
{parametre:Sous-titre}
{parametre:Phase}
```

### 9.3 Éditeur

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

Le service de nommage doit être commun à la prévisualisation et à la publication.

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

## 12. Périmètres de publication

Le modèle conserve :

```text
ENTIRE_SET
SELECTED_ITEMS
SELECTED_NODES
```

et prépare :

```text
MODIFIED_ONLY
```

### 12.1 Traduction utilisateur

```text
Carnet sélectionné → ENTIRE_SET
Mise en page sélectionnée → SELECTED_ITEMS
Dossier sélectionné → ensemble des carnets descendants
```

### 12.2 Publication multiple

La publication d'un dossier est une agrégation de publications de carnets existants.

Chaque carnet est résolu indépendamment, notamment pour :

- héritage ;
- destination ;
- nommage ;
- PDF/DWG ;
- collisions.

### 12.3 Modifiés uniquement

`MODIFIED_ONLY` reste une évolution ultérieure. Il ne doit être activé qu'après mise en place d'un état de publication fiable permettant de comparer les exécutions.

---

## 13. PDF

Le PDF utilise en priorité le moteur PDF natif de Revit 2025.4.

Deux modes sont conservés :

- combiné ;
- séparé.

Les réglages effectivement exposés par l'API Revit doivent être vérifiés sur la version cible avant toute nouvelle option.

---

## 14. DWG

Les deux modes sont conservés :

- combiné ;
- séparé.

Export réutilise autant que possible les configurations `ExportDWGSettings` natives de Revit.

La préférence TAA est **Couleur vraie / True Color**, sous réserve de la configuration et de l'API réellement disponibles.

Une configuration native devenue indisponible ne doit jamais être remplacée silencieusement.

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

### 17.1 Publication d'une mise en page

```text
Sélection mise en page
      ↓
Carnet parent
      ↓
Résolution des réglages effectifs
      ↓
Création d'un périmètre temporaire
      ↓
SELECTED_ITEMS
      ↓
Validation
      ↓
Prévisualisation
      ↓
Confirmation
      ↓
Publication
```

### 17.2 Publication d'un carnet

```text
Sélection carnet
      ↓
Résolution du carnet
      ↓
Réglages effectifs
      ↓
ENTIRE_SET
      ↓
Validation
      ↓
Prévisualisation
      ↓
Confirmation
      ↓
Publication
```

### 17.3 Publication d'un dossier

```text
Sélection dossier
      ↓
Recherche récursive des carnets
      ↓
Résolution indépendante de chaque carnet
      ↓
Prévisualisation globale
      ↓
Confirmation
      ↓
Publication batch
      ↓
Rapport global
```

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

- `MODIFIED_ONLY` n'est pas encore implémenté ;
- les règles dynamiques avancées restent une cible ;
- les niveaux supplémentaires de l'arborescence ne sont pas prioritaires ;
- les comportements API Revit non garantis doivent toujours être validés dans Revit 2025.4 réel ;
- une couche de compatibilité existe actuellement autour de certains handlers historiques de `ExportWindow` et devra être simplifiée lors d'une refactorisation UI ultérieure.

---

## 25. Roadmap restante

### Étape 07 — Historique et « modifiés uniquement »

À réaliser après stabilisation des étapes actuelles :

- historique ;
- état de publication ;
- comparaison ;
- snapshots ou hash métier ;
- `MODIFIED_ONLY`.

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

## 26. Critères de réussite de la cible Publisher TAA

Export sera considéré comme ayant atteint sa cible lorsque l'utilisateur pourra :

1. ouvrir une arborescence de publications claire ;
2. créer et organiser des dossiers ;
3. créer un carnet directement dans le dossier choisi ;
4. réorganiser les carnets par glisser-déposer ;
5. sélectionner plusieurs carnets et les déplacer ensemble ;
6. sélectionner un carnet et publier tout son contenu ;
7. sélectionner une mise en page et publier uniquement celle-ci ;
8. sélectionner un dossier et publier récursivement ses carnets ;
9. conserver les réglages du carnet entre les sessions ;
10. hériter des réglages d'un dossier et revenir à l'héritage ;
11. appliquer un profil de publication ;
12. définir une règle de nommage assistée ;
13. prévisualiser les fichiers avant publication ;
14. publier PDF et DWG selon les configurations Revit appropriées ;
15. gérer les collisions explicitement ;
16. organiser les carnets par dossiers et conserver leur ordre ;
17. utiliser des carnets fixes ou dynamiques ;
18. suivre les résultats dans un rapport ;
19. préparer ultérieurement la publication des seuls éléments modifiés.

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

---

## 28. Correspondance avec les étapes réalisées

```text
Étape 01 → Sélection contextuelle Publisher                 ✅
Étape 02 → Éditeur de nommage Publisher                     ✅
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
