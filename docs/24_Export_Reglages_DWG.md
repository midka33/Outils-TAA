# Export — configurations DWG, vues, liens et stratégie automatique

**Statut :** implémenté et testé hors Revit ; **recette Revit 2025.4 en attente**.  
**Branche :** `feature/export-dwg-settings`.  
Aucune validation du rendu WPF, des XRefs ou de l'ouverture native dans Revit n'est
revendiquée avant la recette utilisateur.

## 1. Choix réellement exposés à l'utilisateur

Le bloc DWG ne présente plus de choix technique « Par feuille / Lot Revit ».

Les choix utilisateur sont uniquement :

| Réglage | Rôle | Défaut |
|---|---|---|
| Publier DWG | Active la sortie DWG | Oui |
| Configuration DWG Revit | Preset natif Revit : calques, lignes, hachures, unités, version, etc. | Réglages Revit par défaut |
| Fusionner les vues et les liens dans le DWG | Pilote `DWGExportOptions.MergedViews` | Oui |
| Forcer les couleurs vraies | Surcharge `Colors` avec `ExportColorMode.TrueColor` | Oui |

La stratégie d'appel à Revit est un détail d'implémentation et n'est plus présentée
comme un réglage métier.

## 2. Stratégie DWG automatique

Le résultat métier attendu reste :

```text
1 feuille Revit = 1 DWG
```

Le moteur choisit automatiquement :

```text
1 feuille
→ 1 appel Revit simple
→ 1 DWG

plusieurs feuilles
→ 1 appel Revit avec toutes les feuilles dans un dossier temporaire
→ Revit produit 1 DWG par feuille avec son nom natif
→ Outils TAA associe chaque DWG à sa feuille
→ renommage selon le modèle TAA
→ livraison dans NomCarnet/DWG/
```

Le lot natif sert à réduire le nombre d'appels à l'API. Il ne fusionne pas plusieurs
feuilles en un seul DWG.

Les noms natifs produits par Revit ne sont plus considérés comme les noms finaux.
Le rapprochement se fait de manière conservatrice à partir du numéro de feuille,
avec le nom de feuille comme désambiguïsation. Le code ne dépend pas du mot
« Feuille » ajouté par certaines localisations/version de Revit.

Si une association est ambiguë ou impossible, la livraison échoue explicitement :
Outils TAA ne renomme jamais un DWG au hasard. Les fichiers temporaires sont
conservés pour diagnostic.

L'ordre des identifiants reste celui du périmètre métier transmis à
`Document.Export`, dans une `List[ElementId]` .NET typée.

### Compatibilité `dwg_mode`

Le champ historique `dwg_mode` reste accepté dans `PublicationSettings.FIELDS`
et peut encore être lu/réécrit dans les anciens JSON afin de ne pas casser les
stockages existants.

En revanche :

- il n'apparaît plus dans l'interface ;
- il ne fait plus partie des champs actifs de l'héritage UI ;
- il n'est plus enregistré dans les nouveaux profils ;
- il n'influence plus le nombre d'appels DWG, les chemins ou `MergedViews`.

## 3. Fusion des vues et liens

`MergedViews` est indépendant de la stratégie d'appel.

```text
Fusion activée
→ MergedViews = True

Fusion désactivée
→ MergedViews = False
```

Le comportement visé est celui du réglage natif Revit relatif aux vues placées sur
les feuilles et aux références externes.

Les images raster et certaines ressources peuvent rester externes. Outils TAA ne
promet donc jamais « aucun XRef » ni « un DWG totalement autonome ».

## 4. Configuration DWG native Revit

La liste est lue avec :

```python
DWGExportOptions.GetPredefinedSetupNames(document)
```

Le preset sélectionné est chargé avec :

```python
DWGExportOptions.GetPredefinedOptions(document, setup_name)
```

Après chargement, Outils TAA ne surcharge que :

| Propriété | Condition |
|---|---|
| `MergedViews` | toujours, à partir de `dwg_merge_views` |
| `Colors` | uniquement si « Forcer les couleurs vraies » est coché |

Toutes les autres propriétés du preset restent celles de Revit.

Un preset supprimé ou renommé n'est jamais remplacé silencieusement par un autre :
l'export doit signaler explicitement l'erreur.

## 5. Accès aux réglages DWG natifs

Le bouton engrenage ouvre la commande native Revit de configuration DWG/DXF.

Séquence retenue :

1. vérifier que la commande est disponible et postable ;
2. sauvegarder l'état temporaire utile d'Export ;
3. fermer la fenêtre WPF modale ;
4. rendre la main à Revit ;
5. poster la commande native ;
6. après fermeture des réglages Revit, l'utilisateur rouvre Export ;
7. les presets sont relus et l'état temporaire est restauré.

Cette approche évite deux dialogues modaux concurrents et ne repose ni sur un timer,
ni sur Idling, ni sur un thread de fond.

Le bouton **Actualiser** relit également les presets sans fermer Export.

## 6. Organisation des dossiers

La case est désormais libellée :

> **Créer un dossier au nom du carnet**

Lorsqu'elle est cochée :

```text
Destination/
└── Nom du carnet/
    ├── PDF/
    │   └── fichiers PDF
    └── DWG/
        ├── fichiers DWG
        └── PNG/JPG/autres annexes éventuelles
```

Ce comportement est indépendant :

- du PDF combiné ou séparé ;
- du nombre de feuilles DWG ;
- de la stratégie d'appel Revit.

Lorsqu'elle est décochée, les fichiers restent directement dans la destination issue
de l'arborescence de publication.

`publication_paths.py` est la source commune à l'aperçu et à l'exécution afin que
les chemins affichés soient les chemins réellement utilisés.

## 7. Aperçu et rapport

### Une feuille DWG

L'aperçu connaît le nom final TAA et l'affiche.

### Plusieurs feuilles DWG

Le plugin connaît désormais les **noms finaux attendus** avant l'appel Revit, car
les fichiers natifs sont renommés après export.

L'aperçu affiche donc une ligne par feuille avec :

- stratégie : **Automatique** ;
- numéro et nom de la feuille ;
- nom DWG final selon le modèle TAA ;
- chemin final dans `NomCarnet/DWG/`.

Les collisions de noms TAA sont ainsi détectables avant publication.

Le rapport final contient également une ligne par DWG principal livré, avec son
chemin réel. Les PNG/JPG/XRefs ou autres fichiers auxiliaires ne sont pas inventés
dans l'aperçu ; ils sont déplacés dans le même dossier DWG lorsqu'ils sont produits
par Revit.

Le préfixe natif Revit et ses libellés éventuels comme « Feuille » ne doivent jamais
apparaître dans le nom final d'un DWG principal.

## 8. Interface compacte

La suppression de « Par feuille / Lot Revit » réduit la hauteur du panneau.

Contrat UI :

- fenêtre cible : 1320 × 760 unités WPF ;
- Segoe UI 13 px conservé ;
- contrôles courants de 28–32 px ;
- marges verticales réduites avant toute réduction de typographie ;
- footer Résumé / Aperçu / Publier hors du ScrollViewer ;
- ScrollViewer conservé comme sécurité uniquement.

Sur un écran **1920 × 1080**, à 100 % puis 125 % de mise à l'échelle Windows, les
réglages courants doivent être accessibles sans défilement vertical obligatoire.
Ce point reste à vérifier réellement dans Revit.

## 9. Héritage et migration

`dwg_merge_views` reste nullable et héritable :

- `None` → hériter ;
- `True` → fusion ;
- `False` → références externes lorsque Revit le permet.

Un ancien JSON sans `dwg_merge_views` conserve `None` au niveau local puis résout
vers le défaut `True`, sans réécriture automatique du fichier à l'ouverture.

L'ancien `dwg_mode` peut rester présent dans le stockage, mais il est ignoré pour
le comportement actuel.

## 10. Progression

La progression 0–100 % reste fondée sur des opérations réelles.

Pendant l'appel natif DWG, `RevitNativeProgressBridge` relaie temporairement
`Application.ProgressChanged` lorsque Revit fournit des données utilisables.
Aucune progression n'est inventée si Revit reste silencieux.

Après le retour de `Document.Export`, Outils TAA contrôle le rapprochement,
renommage et déplacement. Cette phase affiche donc une progression exacte :

```text
A1101 — Bât A - Niveau 1
1 / 5 mises en page

A1102 — Bât A - Niveau 2
2 / 5 mises en page
```

Le compteur avance uniquement après livraison réelle du DWG correspondant.

## 11. Limites à valider dans Revit 2025.4

Les tests Python valident le contrat logiciel mais pas :

- le contenu réel des DWG ;
- le comportement exact des XRefs ;
- les ressources raster ;
- le rendu WPF à 100 % / 125 % ;
- la commande native de configuration dans Revit 2025.4.

La recette de référence est :
[`docs/25_Export_Recette_DWG.md`](25_Export_Recette_DWG.md).

## Sources techniques déjà utilisées pour cette évolution

- Autodesk : *MergedViews and Exporting to a Single DWG* ;
- Autodesk : réglage d'export des vues/liens comme références externes ;
- Guide API Revit 2025 : commandes postables ;
- référence `PostableCommand` consultée par l'évolution initiale ;
- documentation Autodesk sur les images raster exportées comme ressources externes.

La validation de ces comportements reste complétée par la recette réelle Revit
2025.4 : aucune documentation ne remplace le test du build réellement utilisé par
l'agence.
