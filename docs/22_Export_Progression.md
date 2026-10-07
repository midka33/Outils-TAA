# Export — Fenêtre de progression de publication

**Statut :** implémentation sur `feature/export-progress-ui`, recette Revit requise avant fusion
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Module :** Export  
**Date :** 7 octobre 2026

---

## 1. Objectif

Lorsqu'une publication PDF est lancée depuis **Outils TAA > Export**, l'utilisateur
doit disposer d'un retour visuel continu entre le début et la fin de l'opération.

La fenêtre de progression doit répondre immédiatement aux questions suivantes :

- la publication a-t-elle bien démarré ?
- quel est le pourcentage global d'avancement ?
- quel carnet est en cours ?
- quelle feuille / quel fichier est en cours lorsque cette information est réellement connue ?
- quelle étape du pipeline est en cours ?
- combien d'unités de travail sont déjà terminées ?

La progression doit aller de **0 à 100 %**, être monotone et atteindre 100 % uniquement
lorsque les traitements demandés sont réellement terminés.

---

## 2. Référence visuelle

![Maquette de la fenêtre de progression Export](assets/export_progression_mockup.svg)

La maquette est une **référence d'intention graphique**. Elle ne doit pas conduire à
inventer des informations que l'API Revit ne fournit pas.

Principes visuels :

- fenêtre WPF dédiée, cohérente avec la charte Outils TAA ;
- fond clair ;
- Segoe UI ;
- accent principal **TAA Orange UI `#FD8B5A`** ;
- grand titre **Export PDF en cours** ;
- pourcentage numérique fortement visible ;
- barre horizontale de 0 à 100 % ;
- informations de contexte lisibles sans ouvrir le rapport final ;
- quatre étapes visuelles possibles : Préparation, Export, Assemblage/Livraison,
  Finalisation.

---

## 3. Contenu minimal de la fenêtre

La première implémentation doit afficher au minimum :

```text
Export PDF en cours

[██████████████░░░░░░░]  68 %

Carnet :
Plans de vente - Bâtiment A

Élément en cours :
A-103 - Niveau 1

Traitement :
17 / 25 unités

Étape :
Export PDF
```

Le libellé **Élément en cours** doit rester générique : selon le mode de publication,
il peut correspondre à une feuille, un carnet, un fichier PDF ou une opération native
Revit.

---

## 4. Phases fonctionnelles

Le pipeline visuel cible comporte quatre phases :

### 4.1 Préparation

Exemples :

- validation des réglages ;
- résolution des feuilles ;
- création / vérification des dossiers ;
- calcul des noms de fichiers ;
- préparation du plan de progression.

### 4.2 Export PDF

Appels natifs Revit et opérations directement liées à la génération des PDF.

### 4.3 Assemblage / livraison

Cette phase couvre uniquement les opérations qui existent réellement dans le mode
courant :

- rapprochement / renommage des PDF générés nativement ;
- déplacement vers le dossier final ;
- assemblage lorsque le mode combiné ou la chaîne de livraison l'exige.

Le libellé doit pouvoir devenir **Livraison des fichiers** si aucun assemblage réel
n'est effectué.

### 4.4 Finalisation

Exemples :

- contrôle des fichiers produits ;
- consolidation du rapport ;
- enregistrement de l'historique de publication ;
- fermeture de la fenêtre de progression ;
- ouverture du rapport final.

---

## 5. Règles de calcul du pourcentage

### 5.1 Pas de faux progrès

La barre ne doit jamais être une animation décorative présentée comme un pourcentage
réel.

Le pourcentage doit provenir d'un **plan d'unités de travail connues** avant ou pendant
l'exécution.

Exemples d'unités :

- préparation d'un carnet ;
- appel d'export PDF d'un carnet ;
- livraison de fichiers ;
- traitement d'un carnet suivant ;
- finalisation.

### 5.2 Progression globale

Pour une publication de plusieurs carnets, le pourcentage représente l'ensemble de la
sélection, pas seulement le carnet courant.

Une structure métier dédiée doit pouvoir exposer au minimum :

```text
phase
current
total
percent
carnet_name
item_label
message
```

### 5.3 PDF combiné

Un PDF combiné peut être produit par **un seul appel natif Revit pour plusieurs
feuilles**. Si Revit ne fournit pas de progression exploitable à l'intérieur de cet
appel, Outils TAA ne doit pas simuler artificiellement une progression feuille par
feuille.

Dans ce cas :

- la barre progresse jusqu'au début de l'appel ;
- l'état affiche clairement **Export PDF Revit en cours…** ;
- le pourcentage peut rester stable pendant l'appel bloquant ;
- il reprend après le retour de l'API.

Si l'API Revit 2025.4 fournit un événement de progression fiable pour cet export,
il peut être raccordé après validation réelle dans Revit.

### 5.4 PDF séparés

Le code actuel peut lancer plusieurs feuilles dans un seul appel natif PDF séparé.
La même règle s'applique : ne pas afficher `17 / 25 feuilles` comme une progression
réelle si l'application ne connaît pas effectivement la feuille en cours.

Le compteur doit alors être nommé **unités** ou refléter exactement les événements
disponibles.

---

## 6. Réactivité de l'interface

L'interface de progression doit être affichée **avant** le premier traitement long.

Les mises à jour doivent se faire sur le thread UI WPF en respectant les contraintes
de l'API Revit.

Il est interdit de déplacer les appels Revit dans un thread de fond non autorisé
uniquement pour rendre la fenêtre fluide.

Si un appel natif Revit bloque temporairement le thread, la fenêtre doit au minimum
être mise à jour juste avant l'appel puis immédiatement après son retour.

Toute stratégie utilisant les événements de progression de Revit doit :

- être limitée à la durée de la publication ;
- s'abonner avant l'opération concernée ;
- se désabonner systématiquement dans un `finally` ;
- ne pas polluer les autres commandes Revit.

---

## 7. Annulation

Un bouton **Annuler** peut être présent uniquement si son comportement est sûr.

Règle :

> Ne jamais promettre une annulation immédiate au milieu d'un appel natif Revit si
> cet appel n'est pas interruptible par l'API.

Une première version peut :

- masquer le bouton Annuler ;
- ou proposer une annulation coopérative **après l'unité Revit en cours**.

L'annulation ne doit jamais laisser un état incohérent, un rapport faux ou un historique
enregistré comme publication réussie.

---

## 8. Temps restant

La maquette conceptuelle affiche un temps restant, mais cette information est
**optionnelle**.

Ne pas l'implémenter dans la première version sauf si elle est calculée à partir de
mesures suffisamment fiables.

Un faux compte à rebours est interdit.

---

## 9. Architecture attendue

La progression ne doit pas être codée directement dans tous les services.

Architecture cible :

```text
UI Export
   ↓
Publication Progress Window
   ↓
Progress callback / reporter
   ↓
PublicationBatchService
   ↓
PublicationService
   ↓
PdfExportService
```

Le code métier doit pouvoir publier sans fenêtre WPF pour rester testable hors Revit.

Les services reçoivent donc un reporter/callback optionnel, par exemple :

```python
progress.report(
    phase="PDF",
    current=3,
    total=10,
    carnet_name="Plans DCE",
    item_label="Export PDF Revit",
)
```

Le choix exact du nom des classes reste à l'implémentation, mais les responsabilités
doivent rester séparées.

---

## 10. Intégration au workflow existant

La fenêtre apparaît après :

```text
Aperçu
   ↓
Confirmation utilisateur
   ↓
Fenêtre de progression
   ↓
Publication réelle
   ↓
100 %
   ↓
Fermeture progression
   ↓
Rapport final
```

Elle doit fonctionner pour :

- une mise en page ;
- un carnet ;
- une sélection multiple ;
- un dossier et ses sous-dossiers ;
- PDF seul ;
- PDF + DWG, si la progression globale est ensuite étendue aux deux formats.

La priorité de la première implémentation est **PDF**.

---

## 11. États de fin

### Succès

```text
100 %
Publication terminée
```

La fenêtre peut rester visible très brièvement ou se fermer directement avant
l'ouverture du rapport final.

### Succès partiel

La progression atteint 100 % si toutes les unités prévues ont été traitées, même si
certaines produisent une erreur métier. Le rapport final reste la source de vérité
sur les succès/échecs.

### Erreur fatale

La fenêtre affiche brièvement :

```text
Publication interrompue
```

puis le rapport ou le dialogue d'erreur existant prend le relais.

---

## 12. Tests attendus

Tests hors Revit :

- calcul monotone de 0 à 100 ;
- aucune valeur < 0 ou > 100 ;
- plusieurs carnets ;
- publication PDF seule ;
- callback absent : aucune régression du moteur existant ;
- erreur sur une unité ;
- annulation coopérative si elle est implémentée ;
- contrats XAML et handlers ;
- aucune dépendance WPF dans le moteur métier pur.

Recette Revit 2025.4 :

- PDF combiné ;
- PDF séparé ;
- un carnet ;
- plusieurs carnets ;
- dossier récursif ;
- sélection multiple ;
- publication suffisamment longue pour observer la fenêtre ;
- rapport final inchangé ;
- pas de crash au Reload pyRevit ;
- pas d'abonnement Revit résiduel après publication.

---

## 13. Critères d'acceptation

La fonctionnalité est considérée validée lorsque :

1. la fenêtre s'ouvre avant l'export long ;
2. la barre commence à 0 % et finit à 100 % ;
3. la valeur ne recule jamais ;
4. le carnet et l'étape courante sont visibles ;
5. aucun faux numéro de feuille / faux temps restant n'est affiché ;
6. la publication existante produit exactement les mêmes fichiers qu'avant ;
7. les erreurs et le rapport restent inchangés ;
8. le comportement est validé dans Revit 2025.4 ;
9. les tests automatisés existants restent verts.


## 14. Implémentation du 7 octobre 2026 — à valider dans Revit

### Chaîne réellement raccordée

Le smartbutton installe toujours les hooks Stage 07 via `_install_stage07_hooks` :

- sélection de feuilles/carnets → `_preview_then_publish_single` → confirmation →
  `_publish_targets_stage07` → `CarnetController.publish` → `PublicationService` ;
- dossier récursif → `_preview_then_publish_folder_stage07` → confirmation →
  `PublicationBatchService` → `PublicationService` ;
- PDF → `PdfExportService` → un `Document.Export` synchrone par carnet ;
- PDF séparés → rapprochement puis `deliver_named_pdfs` (contrôles, déplacements,
  restauration en cas d'erreur, nettoyage).

Les fonctions de repli de `publication_preview_integration.py` utilisent le même
cycle de progression. Les constructeurs de sélection, réglages, noms, chemins,
l'ordre des feuilles et les règles d'historique restent ceux du flux existant.

### Plan et compteur

`services/publication_progress.py` contient `PublicationProgress` et ses vues
`TargetProgress`. Le plan est figé à partir des réglages effectifs de chaque carnet,
sans les persister ni modifier leurs surcharges. Le contrat commun
`current / total / message` est enrichi avec les phases, le carnet et l'opération ;
`common/progress.py`, qui ne définit qu'une interface abstraite, reste inchangé.

| Unité | Fin effectivement observée |
|---|---|
| Préparation de chaque carnet | Réglages, candidats, validation des feuilles, dossier racine et identifiants résolus |
| PDF, si activé | Retour de l'unique appel natif, combiné **ou** séparé |
| Livraison, PDF séparés seulement | Retour du rapprochement et de la livraison transactionnelle, restauration incluse si échec |
| Groupe DWG, si activé | Retour de tous les exports DWG du carnet, sans modifier leur nombre ni leur mode |
| Finalisation de chaque carnet | Résultats agrégés et traitement de l'historique terminé |
| Rapport global | Rapport consolidé, avant affichage |

Chaque unité a le même poids. Le pourcentage mesure des **unités traitées**, pas
la durée écoulée ni le nombre de feuilles. Le compteur conserve donc « unités ».
Les libellés et la phase peuvent changer sans incrémenter ce compteur.

Exemples sans DWG :

- 1 carnet combiné : 4 unités ; 0 → 25 avant l'appel PDF → 50 après son retour
  → 75 après finalisation du carnet → 100 après consolidation du rapport ;
- 1 carnet séparé : 5 unités ; 0 → 20 → 40 → 60 après livraison → 80 → 100 ;
- 2 carnets séparés : 9 unités au total, un seul compteur global.

Le nommage PDF et les options sont préparés avant l'appel natif ; ils n'ajoutent
pas d'unité artificielle. Aucun faux numéro de feuille n'est affiché dans cet appel.
L'unité DWG est volontairement globale au carnet, même si le service effectue
plusieurs appels en mode séparé. Un export mixte n'atteint donc pas 100 % à la fin
seulement des PDF.

Une opération en échec est traitée, sans être déclarée réussie. Les opérations
empêchées sont explicitement classées **Non exécutée après erreur** (ou périmètre
vide). Le rapport conserve les erreurs réelles et l'historique reste conditionné
au succès. Un succès avec des unités non traitées ne peut pas forcer 100 %.
Une exception fatale, notamment d'historique, interrompt le plan sans compléter
les unités restantes et se propage après fermeture.

### Fenêtre et cycle de vie

`publication_progress.xaml` et `publication_progress_window.py` affichent la
fenêtre possédée par Export. `PublicationProgressSession` ouvre la fenêtre après
confirmation, émet 0 %, puis ferme dans un `finally` avant le rapport existant.
Le propriétaire est temporairement désactivé ; son état exact est restauré,
y compris après une erreur d'ouverture. Un garde interdit une seconde publication.
La croix de fermeture est neutralisée pendant le traitement.

Le callback met à jour les champs, appelle `UpdateLayout`, puis un délégué vide
via `Dispatcher.Invoke(DispatcherPriority.Loaded, Action(...))`. Les appels Revit
restent sur le thread d'origine. Il n'y a ni worker, ni timer, ni boucle DoEvents,
ni abonnement Revit. Le titre devient « Publication en cours » en DWG seul.
La phase active est soulignée ; les quatre repères sont réutilisés par carnet.
« Livraison » n'est pas activée dans le mode PDF combiné natif.

Pas d'estimation de temps et pas de bouton d'annulation dans cette version.
Pendant un appel Revit opaque, la valeur reste fixe et la fenêtre peut ne pas
répondre immédiatement aux interactions Windows. Le rafraîchissement réel WPF
et la lisibilité à différentes échelles Windows doivent être testés dans Revit.

Une défaillance du callback UI est journalisée et ajoutée aux avertissements du
rapport, puis le callback est désactivé pour ne pas interrompre une livraison ni
relancer un export. La fenêtre est tout de même fermée. Si la fermeture échoue
pendant une autre erreur, le diagnostic secondaire est journalisé et l'exception
d'origine reste propagée.

### Analyse des événements et références

La documentation publique consultée ne permet pas de garantir un événement
feuille par feuille pour le PDF natif de Revit **2025.4**. Aucun abonnement à
`ProgressChanged` ou `ViewExported` n'est donc introduit. Ce choix ne prétend pas
que Revit ne peut jamais émettre d'événement : un raccordement plus fin nécessitera
une validation explicite dans cette version et ces deux modes PDF.

Sources consultées le 7 octobre 2026 :

- [Autodesk — Export PDF Revit 2025](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-DocumentPresent/files/GUID-773AD069-024B-425E-8B9A-05D5246BDD16.htm).
- [Autodesk — export PDF en arrière-plan, nouveauté Revit 2025](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-WhatsNew/files/GUID-D2EA7A5B-95FC-49FB-974E-FA5FAC9831E4.htm).
  Le mode synchrone existant `SetExportInBackground(False)` est conservé pour
  attendre les fichiers avant livraison.
- [Autodesk — ProgressChanged, référence publique 2026](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/cabf8932-111c-6036-3d74-3d33c18260ed.htm) :
  notification lorsque des données de progression sont disponibles ; pas un contrat
  de progression PDF par feuille prouvé pour 2025.4.
- [Autodesk — ViewExported, référence publique 2026](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/0a3d3bee-957a-45e0-3779-b1b924a0ce0f.htm) :
  décrit l'export accéléré DWF ; ne justifie pas une progression PDF.
- [Microsoft — DispatcherPriority](https://learn.microsoft.com/en-us/dotnet/api/system.windows.threading.dispatcherpriority)
  et [Dispatcher.Invoke (.NET 8)](https://learn.microsoft.com/fr-fr/dotnet/api/system.windows.threading.dispatcher.invoke?view=windowsdesktop-8.0) :
  `Loaded` est après layout/render et avant la priorité d'entrée ; appel synchrone
  au dispatcher propriétaire. Cela reste à confirmer graphiquement sous pyRevit.

### Validation hors Revit

Commande exécutée :

```bash
python -m pytest tests OutilsTAA.extension/OutilsTAA.tab/Export.panel/tests --ignore=tests/calculation --ignore=tests/plans_vente --import-mode=importlib -q
```

**Résultat : 257 tests réussis**, dont 34 tests dédiés à la progression. Les tests
exécutent les hooks actifs, le contrôleur et les vrais services Python avec une API
Revit simulée. Ils couvrent les deux modes PDF, les carnets multiples, le DWG,
le callback absent/présent/défaillant, la livraison et sa restauration, les erreurs,
la fermeture avant rapport et la syntaxe/XAML. Le workflow GitHub
`export-progress-tests.yml` exécute la même suite.

**Aucun test réel Revit, WPF ou IronPython n'a été exécuté dans cet environnement.**
La [recette TEST-PROGRESS-01 à 08](23_Export_Recette_Progression.md) est à effectuer
sur la branche avant fusion. Aucune release n'est créée par cette évolution.
