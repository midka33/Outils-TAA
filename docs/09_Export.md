# Outils TAA – Outil Export

**Version :** 3.0  
**Statut :** Spécification fonctionnelle de référence et cible d'évolution  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Année :** 2026

---

## 1. Vision

**Export** est le gestionnaire de publications des **Outils TAA**.

L'objectif est de proposer dans Revit une expérience proche du **Publisher d'Archicad**, sans chercher à reproduire son interface à l'identique : même logique de dossiers, carnets, mises en page, réglages persistants, sélection du périmètre, nommage et publication reproductible.

> **Export n'est pas seulement un exporteur PDF/DWG : c'est un gestionnaire de publications.**

La cible fonctionnelle est une utilisation aussi naturelle que possible :

```text
Dossier
└── Carnet
    ├── Mise en page 01
    ├── Mise en page 02
    └── Mise en page 03
```

L'utilisateur doit pouvoir :

- parcourir ses publications dans une arborescence ;
- sélectionner un carnet pour publier tout son contenu ;
- sélectionner une mise en page pour ne publier que celle-ci ;
- conserver les réglages de publication avec le carnet ;
- choisir les règles de nommage des fichiers ;
- prévisualiser les livrables avant de les créer ;
- publier rapidement un même carnet plusieurs fois au cours du projet ;
- retrouver une organisation stable même lorsque le projet Revit évolue.

---

## 2. Principes directeurs

### 2.1 Séparer « quoi publier » et « comment publier »

Le modèle fonctionnel repose sur deux questions distinctes :

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
- stratégie de collision.

Cette séparation est fondamentale pour rester proche du fonctionnement Publisher.

### 2.2 Les réglages sont persistants

Les réglages associés à un carnet doivent être enregistrés avec lui. Une fermeture de Revit ou une nouvelle session ne doit pas obliger l'utilisateur à reconfigurer sa publication.

### 2.3 La sélection doit être contextuelle

La sélection dans l'arborescence définit directement le périmètre de publication :

```text
Sélection d'une mise en page → publier cette mise en page
Sélection d'un carnet       → publier tout le carnet
Sélection d'un dossier      → publier les carnets du dossier
```

Les fonctions de sélection multiple pourront compléter ce comportement, mais ne doivent pas rendre obligatoire une logique de cases à cocher pour l'usage courant.

### 2.4 L'arborescence est le point central de l'interface

L'écran principal doit fonctionner comme un explorateur de publications :

```text
Arborescence                     Réglages / aperçu
────────────────────             ─────────────────────
📁 DCE                           Carnet : DCE
  📦 Plans                       PDF : ☑ Combiné
    📄 A101 – RDC                DWG : ☑ Séparé
    📄 A102 – R+1                Nom : ...
  📦 Coupes                      Destination : ...
    📄 A201 – Coupe AA
```

---

## 3. Modèle métier cible

```text
PublicationProfile
├── PublicationFolder[]
│   └── PublicationSet[]
│       └── PublicationNode[]
│           └── PublicationItem
├── NamingSettings
├── OutputSettings
└── ExecutionSettings
```

### 3.1 PublicationFolder

Un dossier organise les carnets dans l'interface et peut, selon les réglages, organiser également la sortie physique.

Un dossier possède au minimum :

```text
id
name
parent_id
persistent
```

### 3.2 PublicationSet

Un `PublicationSet` représente un carnet logique.

```text
id
name
source
items / nodes
folder_id
publication_settings
persistent
```

Le carnet est l'objet principal de configuration d'une publication.

### 3.3 PublicationNode

Un nœud représente un niveau de l'arborescence :

```text
FOLDER
SHEET
VIEW
```

La cible prioritaire est :

```text
Dossier → Carnet → Mise en page
```

Les niveaux supplémentaires ne doivent être ajoutés que lorsqu'ils apportent une réelle valeur fonctionnelle.

### 3.4 PublicationItem

Un élément résolu reste indépendant de sa source :

```text
unique_id
sheet_id
item_type
sheet_number
sheet_name
parameter_value
source_path
```

Le moteur de publication travaille sur les éléments résolus, jamais directement sur les règles de sélection.

---

## 4. Sources des carnets

Export conserve les modes existants :

### 4.1 Par paramètre

L'utilisateur choisit le paramètre Revit servant à générer les carnets.

`Sous-titre` peut être proposé par défaut selon les conventions TAA, mais ne doit jamais être imposé par le code.

### 4.2 Manuel persistant

L'utilisateur crée un carnet et sélectionne ses mises en page.

### 4.3 Manuel temporaire

Une sélection ponctuelle peut être publiée sans être enregistrée.

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

---

## 5. Arborescence Publisher TAA

### 5.1 Structure cible

La structure principale retenue est volontairement simple :

```text
Dossier
└── Carnet
    ├── Mise en page
    ├── Mise en page
    └── Mise en page
```

Des sous-dossiers internes aux carnets pourront être ajoutés ensuite lorsque le besoin de publication par sous-ensemble sera stabilisé.

### 5.2 Dossier

Le dossier sert à :

- organiser les carnets ;
- faciliter la navigation ;
- permettre une publication par groupe de carnets ;
- éventuellement définir des réglages hérités ;
- éventuellement définir une partie de l'organisation de sortie.

### 5.3 Carnet

Le carnet est sélectionnable comme une unité de publication.

Un clic sur un carnet doit afficher ses réglages persistants et son contenu.

### 5.4 Mise en page

Une mise en page est sélectionnable individuellement.

Un clic sur une mise en page doit permettre :

- de l'identifier ;
- de voir le carnet parent ;
- de connaître les formats activés ;
- de publier uniquement cette mise en page.

### 5.5 Sélection et action contextuelle

Le bouton principal doit refléter la sélection :

```text
Aucune sélection
→ Publier… désactivé ou message d'information

Carnet sélectionné
→ Publier le carnet « DCE »

Mise en page sélectionnée
→ Publier la mise en page « A101 »

Dossier sélectionné
→ Publier le dossier « DCE »
```

L'interface doit éviter de demander à l'utilisateur de comprendre un état interne de `PublicationScope` pour effectuer une action simple.

### 5.6 Sélection multiple

Une évolution permettra :

- `Ctrl + clic` pour plusieurs éléments ;
- `Shift + clic` pour une plage lorsque le contrôle WPF le permet proprement ;
- publication de plusieurs carnets ;
- publication de plusieurs mises en page.

La sélection multiple ne doit pas casser la logique de sélection simple.

---

## 6. Réglages persistants du carnet

Chaque carnet doit pouvoir mémoriser ses réglages de publication.

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

Une destination de profil ou de dossier pourra ensuite être héritée et remplacée au niveau du carnet.

### 6.4 Organisation de sortie

Le carnet pourra choisir ou hériter d'une structure :

```text
Type de fichier → Carnet
Carnet → Type de fichier
Carnet → sous-dossiers internes
```

### 6.5 Persistance

Une modification des réglages d'un carnet persistant doit être sauvegardée automatiquement ou explicitement selon le comportement final de l'interface, mais ne doit jamais être perdue silencieusement.

---

## 7. Nommage des fichiers — objectif Publisher

Le nommage ne doit plus être un simple champ texte sans aide.

L'utilisateur doit pouvoir construire une règle de nommage à partir de variables.

### 7.1 Variables minimales

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

### 7.2 Paramètres Revit

Le moteur doit permettre à terme :

```text
{parametre:NomDuParametre}
```

Exemples :

```text
{parametre:Sous-titre}
{parametre:Phase}
```

### 7.3 Exemple

```text
{projet}_{carnet}_{numero}_{nom}
```

pourrait produire :

```text
TAA_DCE_A101_Plan RDC.pdf
```

### 7.4 Éditeur de nommage

L'interface cible doit proposer :

- un champ de modèle ;
- une liste de variables disponibles ;
- l'insertion d'une variable par clic ou double-clic ;
- une prévisualisation en temps réel ;
- l'affichage des variables indisponibles ;
- la sécurisation des caractères interdits par Windows ;
- la détection des noms identiques.

### 7.5 Différence selon le mode

Le nom final doit être calculé selon le livrable réel.

Par exemple :

```text
PDF combiné
→ {carnet}.pdf

PDF séparé
→ {numero}_{nom}.pdf

DWG séparé
→ {numero}_{nom}.dwg
```

La règle de nommage doit donc pouvoir distinguer le contexte `carnet` et `mise en page`.

### 7.6 Architecture

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

## 8. Héritage des réglages

La cible à moyen terme est :

```text
Profil
  ↓
Dossier
  ↓
Carnet
  ↓
Sous-dossier / mise en page
```

Chaque niveau peut :

- hériter ;
- surcharger ;
- revenir à l'héritage.

Une valeur héritée doit être distinguable visuellement d'une valeur explicitement définie.

La logique d'héritage doit être centralisée dans un `SettingsResolver` et ne doit pas être reproduite dans les exporteurs PDF/DWG.

---

## 9. Profils de publication

Un profil représente une procédure réutilisable.

Exemples :

```text
PC
DP
PRO
DCE
EXE
DOE
CONSULTATION
ARCHIVES
```

Un profil peut contenir plusieurs carnets et des réglages communs.

Le profil ne doit pas remplacer les carnets : il orchestre leur utilisation.

```text
Profil DCE
├── Carnet Plans
├── Carnet Coupes
└── Carnet Façades
```

Les profils sont une étape ultérieure au socle Publisher, mais le modèle doit être conçu pour les accueillir sans refonte.

---

## 10. Prévisualisation avant publication

Avant de produire un fichier, Export doit pouvoir présenter un aperçu de ce qui va être fait.

### 10.1 Informations minimales

```text
Sélection
Carnet
Mise(s) en page
Format
Mode
Nom final
Destination
```

### 10.2 Contrôles

La prévisualisation doit signaler :

- élément manquant ;
- configuration absente ;
- nom invalide ;
- collision ;
- destination inaccessible ;
- conflit de variables ;
- carnet vide.

### 10.3 Principe

La prévisualisation et la publication réelle doivent utiliser les mêmes services de résolution.

```text
Résolution
   ├──→ Prévisualisation
   └──→ Publication
```

Il ne doit pas exister un calcul simplifié du nom ou du contenu uniquement pour l'aperçu.

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

Le modèle cible conserve :

```text
ENTIRE_SET
SELECTED_ITEMS
SELECTED_NODES
```

et prépare :

```text
MODIFIED_ONLY
```

### 12.1 Règle utilisateur

Le périmètre technique doit être traduit par une action simple dans l'interface :

```text
Carnet sélectionné → ENTIRE_SET
Mise en page sélectionnée → SELECTED_ITEMS
Dossier sélectionné → descendants du dossier
```

### 12.2 Publication des éléments modifiés

`MODIFIED_ONLY` ne doit être activé qu'après mise en place d'un état de publication fiable permettant de comparer les exécutions.

---

## 13. PDF

Le PDF utilise en priorité le moteur PDF natif de Revit 2025.4.

Deux modes sont conservés :

- combiné ;
- séparé.

Export ne doit pas recréer artificiellement un « profil PDF Revit » si Revit ne fournit pas cet objet dans son API.

Les réglages effectivement exposés par l'API Revit doivent être vérifiés sur la version cible avant implémentation.

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

La destination est la racine de publication.

Les structures prévues sont :

```text
Exports/
├── PDF/
│   ├── DCE/
│   └── PRO/
└── DWG/
    ├── DCE/
    └── PRO/
```

ou :

```text
Exports/
├── DCE/
│   ├── PDF/
│   └── DWG/
└── PRO/
    ├── PDF/
    └── DWG/
```

Une structure interne au carnet peut également être reproduite si l'utilisateur l'active.

Un service unique `OutputPathService` doit construire les chemins. Les exporteurs PDF/DWG ne doivent pas construire leur propre arborescence.

---

## 16. Collisions et écrasement

La stratégie doit être explicite :

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

### 17.1 Usage quotidien

```text
Ouvrir Export
   ↓
Parcourir l'arborescence
   ↓
Sélectionner un carnet ou une mise en page
   ↓
Vérifier / modifier les réglages persistants
   ↓
Prévisualiser
   ↓
Publier
   ↓
Consulter le rapport
```

### 17.2 Gestion des carnets

Une fenêtre dédiée conserve la création et la gestion des carnets :

```text
Par paramètre
Manuel
Temporaire
Dynamique
```

Cette fenêtre ne doit pas surcharger l'écran principal de publication.

### 17.3 Publication d'un carnet

```text
Sélection carnet
      ↓
Résolution du carnet
      ↓
Réglages persistants
      ↓
Périmètre ENTIRE_SET
      ↓
Validation
      ↓
Prévisualisation
      ↓
Publication
```

### 17.4 Publication d'une mise en page

```text
Sélection mise en page
      ↓
Carnet parent
      ↓
Héritage des réglages du carnet
      ↓
Périmètre SELECTED_ITEMS
      ↓
Validation
      ↓
Prévisualisation
      ↓
Publication
```

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
  ├── SettingsResolver
  ├── FilenameTemplateService
  ├── ValidationService
  ├── OutputPathService
  ├── PdfExportService
  ├── DwgExportService
  ├── ExecutionService
  └── PublicationReportService
        ↓
Revit API / Common TAA
```

Principes :

- une responsabilité par classe ;
- aucune logique métier complexe dans les fenêtres WPF ;
- aucun chemin de sortie construit dans les exporteurs ;
- aucun réglage DWG dupliqué inutilement ;
- persistance indépendante de la session ;
- accès Revit centralisé ;
- exceptions explicites ;
- journalisation structurée.

---

## 19. Persistance

Les carnets, dossiers et profils persistants doivent être stockés dans un format versionnable et migrable.

Les données doivent permettre de reconstruire fidèlement :

- l'identité ;
- le nom ;
- le dossier parent ;
- la source ;
- les éléments ;
- les réglages ;
- le modèle de nommage ;
- la version du schéma.

Les `UniqueId` Revit doivent être privilégiés pour les références intersessions. Un élément supprimé ne doit pas être remplacé silencieusement.

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
- chemin ;
- nom final ;
- statut ;
- durée ;
- message.

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
Publication
```

Une erreur critique doit bloquer la publication concernée.

---

## 22. Tests et non-régression

Les tests suivent `docs/08_Testing.md` et le registre global `docs/11_BUGS_Prevention_Registry.md`.

Toute modification du module Export doit notamment vérifier :

- chargement WPF/XAML dans Revit 2025.4 ;
- navigation de l'arborescence ;
- sélection carnet ;
- sélection mise en page ;
- publication du bon périmètre ;
- persistance des réglages ;
- résolution des carnets ;
- nommage ;
- PDF ;
- DWG ;
- collisions ;
- rapport.

Avant chaque commit de code, le registre global des bugs doit être consulté conformément à `08_Testing.md`.

---

## 23. Compatibilité

Cible officielle :

- Revit **2025.4** ;
- pyRevit **5.x** ;
- IronPython compatible avec l'environnement pyRevit utilisé.

Toute API non garantie doit être validée dans l'environnement réel.

---

## 24. Roadmap de développement

L'évolution est volontairement découpée pour permettre une validation progressive dans Revit.

### Étape 01 — Sélection contextuelle Publisher

**Objectif :** supprimer la dépendance à la sélection par cases à cocher pour l'usage courant.

À réaliser :

1. sélectionner un carnet dans l'arborescence ;
2. sélectionner une mise en page dans l'arborescence ;
3. identifier le périmètre courant ;
4. publier le carnet entier lorsqu'un carnet est sélectionné ;
5. publier uniquement la mise en page lorsqu'une mise en page est sélectionnée ;
6. adapter dynamiquement le bouton de publication et les informations affichées ;
7. conserver la possibilité de publier plusieurs carnets via une sélection dédiée ultérieurement.

**Critère de validation :** un clic sur un carnet ou une mise en page suffit à déterminer ce qui sera publié, sans ambiguïté.

### Étape 02 — Éditeur de nommage Publisher

À réaliser :

- variables ;
- insertion assistée ;
- aperçu ;
- règles différentes combiné/séparé ;
- paramètres Revit ;
- validation des noms ;
- persistance du modèle.

### Étape 03 — Prévisualisation de publication

À réaliser :

- liste exacte des livrables ;
- noms finaux ;
- destinations ;
- collisions ;
- erreurs et avertissements ;
- validation avant exécution.

### Étape 04 — Sélection multiple et publication par dossier

À réaliser :

- Ctrl ;
- Shift ;
- sélection de plusieurs carnets ;
- publication d'un dossier ;
- publication d'un ensemble de mises en page.

### Étape 05 — Héritage et profils

À réaliser :

- réglages au niveau dossier ;
- profils ;
- surcharge ;
- retour à l'héritage ;
- versionnement.

### Étape 06 — Dynamique avancé

À réaliser :

- règles combinées ;
- prévisualisation de résolution ;
- détection des nouveaux éléments ;
- diagnostic des éléments retirés ;
- exclusions explicites.

### Étape 07 — Historique et « modifiés uniquement »

À réaliser après stabilisation des étapes précédentes :

- historique ;
- état de publication ;
- comparaison ;
- snapshots ou hash métier ;
- `MODIFIED_ONLY`.

### Étape 08 — Extensibilité

Préparer sans priorité immédiate :

- vues publiables ;
- IFC ;
- autres formats ;
- automatisations complémentaires.

---

## 25. Critères de réussite de la cible Publisher TAA

Export sera considéré comme ayant atteint sa cible lorsque l'utilisateur pourra :

1. ouvrir une arborescence de publications claire ;
2. sélectionner un carnet et publier tout son contenu ;
3. sélectionner une mise en page et publier uniquement celle-ci ;
4. conserver les réglages du carnet entre les sessions ;
5. définir une règle de nommage assistée ;
6. prévisualiser les fichiers avant publication ;
7. publier PDF et DWG selon les configurations Revit appropriées ;
8. gérer les collisions explicitement ;
9. organiser les carnets par dossiers ;
10. utiliser des carnets fixes ou dynamiques ;
11. réutiliser des profils de publication ;
12. suivre les résultats dans un rapport ;
13. préparer ultérieurement la publication des seuls éléments modifiés.

> **La réussite d'Export se mesure à la qualité du workflow de publication, pas uniquement à la capacité de produire un PDF ou un DWG.**

---

## 26. Règles fonctionnelles non négociables

1. Le moteur de publication ne dépend pas directement du mode de création du carnet.
2. Une sélection fixe ne doit pas être confondue avec une règle dynamique.
3. Le carnet est l'unité persistante principale de configuration.
4. La sélection d'une mise en page doit pouvoir réduire le périmètre à cette seule mise en page.
5. Les réglages persistants ne doivent jamais être perdus silencieusement.
6. Les réglages hérités sont résolus avant l'appel aux exporteurs.
7. Les exporteurs ne construisent jamais l'arborescence de sortie.
8. Une collision ne doit jamais être résolue silencieusement.
9. Un élément manquant ne doit jamais être remplacé silencieusement par un autre.
10. Prévisualisation et publication utilisent les mêmes services de résolution.
11. La validation est indépendante de l'interface.
12. Les configurations natives Revit sont réutilisées lorsqu'elles sont réellement disponibles via l'API cible.
13. Les comportements Revit non garantis sont documentés et testés.
14. Les erreurs reproductibles sont capitalisées dans `11_BUGS_Prevention_Registry.md`.
15. Avant toute modification de code et avant chaque commit, le registre global des bugs est consulté.

---

## 27. État d'implémentation

La base actuelle contient déjà :

- arborescence Dossier → Carnet → Mise en page ;
- dossiers persistants ;
- carnets persistants ;
- fenêtre dédiée de gestion des carnets ;
- consultation des mises en page ;
- réglages PDF/DWG persistants au niveau carnet ;
- configuration DWG native ;
- True Color ;
- destination persistante ;
- modèle de nommage initial ;
- publication PDF/DWG combinée ou séparée ;
- filtrage des carnets liés au projet Revit courant ;
- rapport de publication ;
- registre global des bugs et procédure de non-régression.

Les éléments décrits dans la roadmap mais non encore implémentés doivent être considérés comme **cible**, et non comme comportement déjà garanti.
