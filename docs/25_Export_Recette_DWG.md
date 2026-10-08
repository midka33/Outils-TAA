# Recette — Export DWG automatique, Revit 2025.4 / pyRevit 5.x

**Tous les scénarios ci-dessous sont À TESTER dans Revit.**  
Les tests Python ne valident ni WPF réel, ni les DWG produits, ni le comportement
effectif des XRefs dans le build Revit de l'agence.

La PR #19 reste en Draft jusqu'à validation utilisateur.

## Installer la branche de test

Dans Git Bash, depuis le dépôt utilisé par pyRevit :

```bash
git status
git fetch origin
git switch feature/export-dwg-settings
git pull --ff-only origin feature/export-dwg-settings
```

Puis recharger pyRevit ou redémarrer Revit 2025.4.

Préparer un projet de test avec :

- au moins deux feuilles ;
- une feuille contenant plusieurs vues ;
- un lien Revit visible ;
- une image raster ;
- au moins un carnet ;
- si possible un dossier/sous-dossier de publication ;
- une configuration DWG native identifiable.

Utiliser un dossier de destination vide pour chaque essai important.

## TEST-DWG-UX-01 — Lisibilité sans scroll obligatoire

Ouvrir Export sur un écran 1920 × 1080.

Faire le test à :

- 100 % de scaling Windows ;
- 125 % de scaling Windows si utilisé à l'agence.

### Attendu

Sans devoir scroller dans l'usage normal, l'utilisateur doit pouvoir accéder à :

- PDF ;
- DWG ;
- configuration DWG Revit ;
- fusion vues/liens ;
- couleurs vraies ;
- destination ;
- nommage ;
- « Créer un dossier au nom du carnet » ;
- Options avancées ;
- résumé ;
- Aperçu ;
- Publier.

Les anciens contrôles **Par feuille / Lot Revit** ne doivent plus être visibles.

Le ScrollViewer peut rester disponible uniquement si la fenêtre est réduite ou si
l'espace écran réel est insuffisant.

## TEST-DWG-UX-02 — Dossier carnet avec PDF + DWG

Cocher :

> Créer un dossier au nom du carnet

Publier un carnet en PDF combiné + DWG avec plusieurs feuilles.

### Attendu

```text
Destination/
└── NomCarnet/
    ├── PDF/
    │   └── NomCarnet.pdf
    └── DWG/
        ├── feuille 1.dwg
        ├── feuille 2.dwg
        └── annexes éventuelles
```

Aucun PDF/DWG/PNG/JPG de ce carnet ne doit être déposé directement à la racine de
la destination, hors comportement externe Revit explicitement constaté et documenté.

## TEST-DWG-UX-03 — PDF seul

Avec la case dossier du carnet cochée, publier en PDF seul.

Tester PDF combiné puis PDF séparé.

### Attendu

Dans les deux cas :

```text
Destination/NomCarnet/PDF/
```

Le mode PDF ne doit plus décider si le dossier du carnet existe.

## TEST-DWG-UX-04 — DWG seul

Avec la case dossier du carnet cochée, publier en DWG seul.

### Attendu

Tous les DWG et ressources auxiliaires produites dans le cadre de cet export doivent
être regroupés sous :

```text
Destination/NomCarnet/DWG/
```

## TEST-DWG-UX-05 — Stratégie automatique invisible

Sélectionner plusieurs feuilles dans un carnet.

### Attendu UI

Aucun choix :

```text
Par feuille
Lot Revit
```

ne doit apparaître.

### Attendu fonctionnel

Le plugin doit envoyer les feuilles dans une stratégie automatique sans demander
de décision technique à l'utilisateur.

Le rapport et l'aperçu doivent parler de stratégie **Automatique**, pas d'un faux
« DWG combiné ».

## TEST-DWG-UX-06 — Plusieurs feuilles = plusieurs DWG

Publier deux feuilles en DWG.

### Attendu

- deux DWG de feuille sont produits par Revit dans un lot natif ;
- Outils TAA les rapproche ensuite des deux feuilles ;
- chaque DWG principal est renommé selon le modèle TAA ;
- le mot natif « Feuille » ne doit pas apparaître dans les noms finaux sauf s'il
  fait réellement partie du modèle TAA ;
- l'aperçu affiche les deux noms finaux avant publication ;
- le rapport affiche les deux chemins finaux réellement livrés ;
- aucune attente d'un DWG unique ne doit être créée par l'interface.

## TEST-DWG-UX-07 — Fusion des vues/liens

Sur une feuille contenant plusieurs vues et si possible un lien Revit :

1. exporter avec **Fusionner les vues et les liens dans le DWG** décoché ;
2. exporter dans un autre dossier avec la case cochée.

### Relevé

Comparer :

- nombre de DWG ;
- liste des XRefs ;
- géométrie des vues ;
- géométrie du lien ;
- liens imbriqués éventuels.

### Attendu

Le changement doit correspondre au comportement réel de `MergedViews` dans Revit
2025.4. Le résultat réel est à consigner ; aucune validation préalable n'est présumée.

## TEST-DWG-UX-08 — Ressources raster

Exporter une feuille contenant une image raster avec fusion activée.

### Attendu

- la géométrie DWG reste exploitable ;
- les éventuels PNG/JPG externes restent dans le dossier `DWG` du carnet ;
- l'outil ne promet pas que ces ressources seront intégrées au DWG ;
- le rapport peut avertir que des annexes sont possibles.

## TEST-DWG-UX-09 — Aperçu = chemins réels

Avant publication, ouvrir Aperçu.

### Attendu

Pour les PDF, les chemins doivent pointer vers :

```text
NomCarnet/PDF/
```

Pour un DWG d'une seule feuille, le chemin exact doit pointer vers :

```text
NomCarnet/DWG/nom.dwg
```

Pour plusieurs feuilles DWG, l'aperçu doit afficher **une ligne par mise en page**
avec le nom final TAA attendu dans `NomCarnet/DWG`.

Après publication, comparer ligne par ligne les chemins de l'aperçu, du rapport et
du disque. Aucun suffixe de nommage natif Revit ne doit subsister sur les DWG
principaux.

## TEST-DWG-UX-10 — Périmètres multiples

Tester successivement :

- sélection Ctrl/Maj de plusieurs feuilles ;
- plusieurs carnets ;
- publication d'un dossier avec sous-dossiers.

### Attendu

- le périmètre aperçu = le périmètre publié ;
- chaque carnet possède son propre `PDF` / `DWG` si l'option dossier est cochée ;
- aucune collision artificielle n'est signalée uniquement parce que deux lignes de
  lots DWG représentent un répertoire ;
- les vrais conflits de noms connus restent détectés.

## TEST-DWG-UX-11 — Progression 0–100 %

Publier PDF + DWG sur plusieurs feuilles.

### Attendu

- progression monotone ;
- pendant l'appel natif, la barre avance uniquement si Revit émet réellement
  `ProgressChanged` ; sinon elle peut rester stable ;
- après l'appel, la phase Livraison DWG affiche exactement `X / Y mises en page` ;
- le libellé de la mise en page courante change à chaque DWG réellement livré ;
- aucun 100 % avant la fin des opérations prévues ;
- la fenêtre se ferme avant le rapport final.

## TEST-DWG-UX-12 — Compatibilité des anciens `dwg_mode`

Sur une copie du stockage Export existant, conserver ou injecter :

```json
"dwg_mode": "SEPARATE"
```

puis refaire avec :

```json
"dwg_mode": "COMBINED"
```

### Attendu

- aucun crash à l'ouverture ;
- aucun contrôle de mode DWG n'apparaît ;
- les deux anciennes valeurs produisent la même stratégie actuelle ;
- `dwg_merge_views`, destination, profil, carnet et héritage restent préservés ;
- l'ouverture seule ne détruit pas l'ancien stockage.

## TEST-DWG-UX-12B — Nommage réel observé dans le projet agence

Utiliser le modèle de nommage réellement employé, par exemple :

```text
ALTA VERDE_TR1_ARC_TAA_{numero}_{nom}
```

avec plusieurs feuilles.

### Attendu

Pour les DWG :

```text
ALTA VERDE_TR1_ARC_TAA_A1101_<nom feuille>.dwg
ALTA VERDE_TR1_ARC_TAA_A1102_<nom feuille>.dwg
```

et **pas** :

```text
... - Feuille - A1101 - ...
```

Pour le PDF combiné, le nom doit être au niveau carnet. Les variables propres aux
feuilles ne doivent pas reprendre automatiquement A1101 ou la première feuille.

Consigner le nom exact obtenu afin de valider la règle de remplacement des variables
de feuille par le carnet.

## TEST-DWG-SETUP-13 — Configuration native Revit

Choisir un preset identifiable.

Tester avec **Forcer les couleurs vraies** décoché puis coché.

### Attendu

- les réglages natifs du preset sont conservés ;
- décoché : couleurs du preset conservées ;
- coché : True Color imposé ;
- `MergedViews` suit uniquement la case de fusion.

## TEST-DWG-SETUP-14 — Engrenage Revit

Cliquer sur l'engrenage DWG.

### Attendu

- Export se ferme proprement ;
- la fenêtre native Revit s'ouvre sans blocage ;
- après fermeture, rouvrir Export ;
- sélection, carnets temporaires et ordre sont restaurés ;
- la liste des presets est relue.

Créer ou renommer un preset et vérifier qu'**Actualiser** fonctionne également.

## Fiche de résultat

Pour chaque test, consigner :

- build exact Revit 2025.4 ;
- version pyRevit ;
- commit de branche ;
- scaling Windows ;
- preset DWG ;
- état fusion ;
- état True Color ;
- nombre de feuilles ;
- destination ;
- liste réelle des fichiers créés ;
- liste des XRefs lorsque pertinente ;
- capture avant/après ;
- résultat : **OK / Échec / Non testé**.

## Suite automatisée hors Revit

Depuis la racine du dépôt :

```bash
python -m pytest tests OutilsTAA.extension/OutilsTAA.tab/Export.panel/tests --ignore=tests/calculation --ignore=tests/plans_vente --import-mode=importlib -q
```

Cette suite doit rester verte avant recette Revit. Elle ne remplace pas le contrôle
réel de l'interface à 1920 × 1080 ni l'analyse des DWG produits.
