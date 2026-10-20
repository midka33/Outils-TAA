# Export — recette de progression Revit 2025.4

**Statut : à exécuter par l'utilisateur avant fusion de la PR #19.**  
**Branche :** `feature/export-dwg-settings`.

Les tests automatisés valident le contrat logiciel, mais pas les événements réellement
émis par Revit 2025.4 ni le rendu WPF.

## Préparer le test

Fermer Revit, puis dans le dépôt utilisé par pyRevit :

```bash
git status
git fetch origin
git switch feature/export-dwg-settings
git pull --ff-only origin feature/export-dwg-settings
```

Redémarrer Revit 2025.4 et utiliser un carnet assez volumineux pour observer la
progression.

## Contrôles communs

Pendant toute publication :

- départ à 0 % ;
- progression monotone ;
- jamais plus de 100 % ;
- 100 % uniquement à la fin ;
- carnet et étape courante visibles ;
- aucune estimation de temps fictive ;
- aucune seconde publication possible pendant la première ;
- fermeture de la fenêtre de progression avant le rapport final.

Quand Revit émet une progression native exploitable, la barre doit avancer pendant
`Document.Export`. Si Revit n'émet rien pour une opération donnée, la barre peut
rester stable : **aucune progression artificielle ne doit être inventée**.

Pendant une livraison contrôlée par Outils TAA, le compteur doit en revanche être
exact :

```text
A1102 — Bât A - Niveau 2
3 / 5 mises en page
```

## TEST-PROGRESS-01 — PDF combiné

Publier un carnet de plusieurs feuilles en PDF combiné.

### Attendu

- le fichier final utilise le nom de carnet prévu par le moteur de nommage ;
- il ne reprend pas automatiquement le nom de la première feuille ;
- la barre peut évoluer pendant l'appel si Revit émet `ProgressChanged` ;
- sinon elle reste stable sans faux compteur de feuilles ;
- 100 % seulement après finalisation.

## TEST-PROGRESS-02 — PDF séparés

Publier plusieurs feuilles en PDF séparés.

### Attendu

- un seul appel natif peut être conservé ;
- pendant le natif, utiliser seulement la progression réellement fournie par Revit ;
- pendant le rapprochement/livraison, afficher chaque mise en page réellement livrée ;
- le compteur passe réellement de `1 / N` à `N / N mises en page` ;
- les noms et chemins finaux restent conformes à l'aperçu.

## TEST-PROGRESS-03 — DWG multiple

Publier au moins cinq feuilles en DWG.

### Attendu

- un seul lot natif Revit est utilisé pour les plusieurs feuilles ;
- si Revit émet `ProgressChanged`, la barre avance pendant le natif ;
- après le retour natif, phase **Livraison DWG** ;
- chaque DWG renommé/livré fait avancer le compteur ;
- la feuille correspondante est visible ;
- compteur exact `X / N mises en page`.

## TEST-PROGRESS-04 — PDF + DWG

Publier plusieurs feuilles en PDF + DWG.

### Attendu

La progression globale ne repart jamais à zéro :

```text
Préparation
→ Export PDF
→ Livraison PDF si nécessaire
→ Export DWG
→ Livraison DWG
→ Finalisation
→ 100 %
```

## TEST-PROGRESS-05 — Plusieurs carnets / sélection Ctrl-Maj

Tester plusieurs carnets puis une sélection partielle de feuilles.

### Attendu

- un seul pourcentage global ;
- changement de carnet sans remise à zéro ;
- périmètre aperçu = périmètre publié ;
- compteur détaillé relatif au traitement réellement en cours.

## TEST-PROGRESS-06 — Dossier récursif

Publier un dossier contenant plusieurs carnets et sous-dossiers.

### Attendu

- progression globale couvrant tout le périmètre ;
- chemins et héritage inchangés ;
- aucun 100 % prématuré.

## TEST-PROGRESS-07 — Erreur / rollback

Provoquer uniquement dans une copie de test une erreur de livraison ou de destination.

### Attendu

- diagnostic conservé ;
- pas de faux succès ;
- restauration des fichiers lorsque le mécanisme de rollback s'applique ;
- fenêtre de progression fermée proprement ;
- rapport final avec erreur ;
- pas d'historique de succès pour le carnet en échec.

## TEST-PROGRESS-08 — Abonnements Revit

Faire plusieurs publications successives, puis Reload pyRevit.

### Attendu

- pas de callback doublé ;
- pas de progression parasite après la publication ;
- pas de crash ;
- aucun handler `ProgressChanged` résiduel après la fin d'un export.

## TEST-PROGRESS-09 — Rendu WPF

À 1920 × 1080, tester le scaling Windows réellement utilisé à l'agence, notamment
100 % et 125 %.

### Attendu

- pourcentage lisible ;
- feuille courante non tronquée de manière bloquante ;
- `X / Y mises en page` lisible ;
- aucune superposition de texte ;
- fenêtre réactive autant que le permet l'appel Revit synchrone.

## Relevé

| Test | Résultat / observations |
|---|---|
| TEST-PROGRESS-01 | À exécuter |
| TEST-PROGRESS-02 | À exécuter |
| TEST-PROGRESS-03 | À exécuter |
| TEST-PROGRESS-04 | À exécuter |
| TEST-PROGRESS-05 | À exécuter |
| TEST-PROGRESS-06 | À exécuter |
| TEST-PROGRESS-07 | À exécuter |
| TEST-PROGRESS-08 | À exécuter |
| TEST-PROGRESS-09 | À exécuter |

Après les essais, ne fusionner la PR #19 qu'après validation explicite du comportement
réel dans Revit 2025.4.
