# Export — Fenêtre de progression de publication

**Statut :** validé dans Revit 2025.4 — intégré à `main`
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Module :** Export  
**Date :** 7 octobre 2026  
**Validation réelle :** 8 octobre 2026

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


## 14. Implémentation actuelle — PR #19

**Branche :** `feature/export-dwg-settings`  
**Statut :** tests hors Revit validés ; recette Revit 2025.4 obligatoire avant fusion.

### 14.1 Principe de progression

La progression conserve un plan global d'unités métier, mais elle peut maintenant
progresser **à l'intérieur de l'unité active** lorsqu'une mesure réelle est disponible.

Deux sources sont admises :

1. **progression native Revit** pendant `Document.Export` ;
2. **progression exacte contrôlée par Outils TAA** pendant le rapprochement,
   renommage et déplacement des fichiers.

Aucune interpolation temporelle ou progression feuille par feuille inventée n'est
autorisée.

Le pourcentage reste monotone, compris entre 0 et 100, et 100 % n'est émis qu'après
la consolidation finale du rapport.

### 14.2 Progression native Revit

`services/revit_native_progress.py` contient `RevitNativeProgressBridge`.

Pendant un appel PDF ou DWG natif, le bridge s'abonne temporairement à :

```text
Document.Application.ProgressChanged
```

et relaie uniquement les informations réellement reçues :

```text
Caption
Position
UpperRange
```

`Position / UpperRange` fournit une fraction réelle de l'unité active. Le libellé
`Caption` devient l'élément/opération visible dans la fenêtre.

Règles de sécurité :

- abonnement uniquement pendant l'appel natif concerné ;
- désabonnement systématique à la sortie du contexte, y compris sur exception ;
- aucune modification du document depuis le handler ;
- une erreur du suivi de progression ne doit jamais interrompre l'export ;
- si Revit 2025.4 n'émet aucun événement utile pour un cas donné, la progression
  reste simplement stable pendant l'appel.

`ViewExported` n'est pas utilisé pour simuler une progression PDF/DWG par feuille.

### 14.3 Progression par mise en page pendant la livraison

Lorsque Outils TAA contrôle réellement la livraison, la fenêtre affiche un compteur
exact :

```text
A1102 — Bât A - Niveau 2
3 / 5 mises en page
```

Ce compteur est utilisé notamment pour :

- la livraison des PDF séparés ;
- le rapprochement, renommage et livraison des DWG d'un lot.

Le pourcentage global avance à chaque fichier effectivement livré. Il ne s'agit donc
pas d'un simple changement de texte.

Pour un DWG unique, l'étape de livraison signale explicitement `1 / 1 mise en page`.

### 14.4 Phases actuelles

Le moteur distingue :

```text
Préparation
Export PDF
Livraison PDF
Export DWG
Livraison DWG
Finalisation
```

L'interface conserve quatre repères visuels principaux :

```text
Préparation → Export → Livraison → Finalisation
```

Les phases PDF/DWG se regroupent visuellement dans Export, et les phases
`pdf_delivery` / `dwg_delivery` dans Livraison.

### 14.5 Cycle de vie WPF

`publication_progress.xaml` et `publication_progress_window.py` restent
synchrones avec Revit :

- pas de worker pour les appels API Revit ;
- pas de thread Python de fond pour `Document.Export` ;
- pas de temps restant fictif ;
- pas de bouton d'annulation prétendant interrompre un appel natif ;
- fermeture de la progression avant ouverture du rapport existant.

Le callback UI affiche soit le compteur global d'unités, soit le compteur détaillé
réel lorsqu'il est disponible.

### 14.6 Cas où la progression peut encore rester fixe

Même avec `ProgressChanged`, Outils TAA ne garantit pas que Revit fournisse une
granularité exploitable pour chaque export et chaque étape.

Donc :

- si Revit émet une progression native : la barre avance avec elle ;
- si Revit n'en émet pas : la barre reste stable pendant l'appel ;
- après retour de Revit, les traitements contrôlés par Outils TAA reprennent avec
  une progression exacte.

Cette règle évite tout faux pourcentage.

### 14.7 Stabilité de la fenêtre et sémantique du compteur

La fenêtre de progression possède une hauteur fixe. Le message de statut sous le
titre occupe une zone réservée : un changement de texte ne doit plus agrandir ou
réduire la fenêtre pendant la publication.

Les valeurs brutes `Position / UpperRange` de `ProgressChanged` restent utilisées
pour calculer la progression fractionnaire mais ne sont plus affichées comme un
compteur utilisateur. Pendant cette phase, le bloc d'avancement affiche :

```text
Avancement :
Revit travaille…
```

Lorsqu'une vraie progression métier par mise en page est disponible, le même bloc
devient :

```text
Mises en page :
3 / 5
```

Le libellé « Traitement » est donc abandonné afin d'éviter l'ambiguïté entre compteurs
techniques et compteurs métier.

### 14.7 Validation hors Revit

Commande de référence :

```bash
python -m pytest tests OutilsTAA.extension/OutilsTAA.tab/Export.panel/tests --ignore=tests/calculation --ignore=tests/plans_vente --import-mode=importlib -q
```

**Résultat actuel : 301 tests réussis hors Revit.**

Les tests couvrent notamment :

- monotonie et bornes du pourcentage ;
- fraction native `Position / UpperRange` ;
- compteur exact `X / Y mises en page` ;
- PDF combiné et séparé ;
- DWG en lot + renommage/livraison ;
- callback absent ou défaillant ;
- rollback de livraison ;
- fermeture avant rapport ;
- contrats XAML ;
- absence de dépendance WPF dans les services métier.

La recette réelle reste nécessaire pour confirmer que Revit **2025.4** émet bien
`ProgressChanged` de manière utile pendant les exports PDF/DWG utilisés par
l'agence, ainsi que la fluidité réelle de la fenêtre.

Voir : [`docs/23_Export_Recette_Progression.md`](23_Export_Recette_Progression.md).
