# Recette — réglages DWG, Revit 2025.4 / pyRevit 5.x

**Tous les scénarios ci-dessous sont À TESTER dans Revit.**
Les tests Python simulés ne valident ni WPF, ni l'API réelle, ni les DWG produits.
La PR reste en draft ; fusion et release attendent la validation de l'utilisateur.

## Installer la branche de test

Dans Git Bash, depuis le dépôt utilisé par pyRevit :

```bash
git status
git fetch origin
git switch feature/export-dwg-settings
git pull --ff-only origin feature/export-dwg-settings
```

Si la branche n'existe pas encore localement, `git switch` la crée normalement à
partir du suivi distant ; sinon utiliser
`git switch --track origin/feature/export-dwg-settings`.
En cas de fusion en cours ou de modifications locales, résoudre/sauvegarder ce
travail avant de changer de branche ; ne pas utiliser de reset forcé.
Recharger pyRevit, ou redémarrer Revit 2025.4. Vérifier le dépôt chargé et noter
le commit retourné par `git rev-parse --short HEAD`.

Préparer une copie de projet avec : une feuille contenant au moins deux vues,
une seconde feuille, un lien Revit visible, une image raster, deux carnets et un
dossier/sous-dossier. Créer une configuration native « TAA - DCE » avec calques,
unités, coordonnées, version DWG et couleurs reconnaissables. Utiliser un dossier
vide distinct par essai afin de distinguer fichiers produits et anciens fichiers.
Disposer d'une visionneuse DWG capable de lister les XRefs (AutoCAD si disponible).

## Scénarios obligatoires

| ID | Manipulation | Résultat attendu / relevé à fournir |
|---|---|---|
| TEST-DWG-SETUP-01 | Choisir « TAA - DCE », décocher « Forcer les couleurs vraies », exporter une feuille. Refaire avec la case cochée. | Preset chargé ; vérifier calques, lignes, hachures, textes, unités, coordonnées, solides/version. Couleurs natives préservées décoché, surcharge TrueColor coché. Noter le rendu réel. |
| TEST-DWG-SETUP-02 | Même feuille à deux vues, sortie Par feuille, fusion décochée, destination vide. | DWG de feuille et DWG de vues/XRefs lorsque applicable. Relever les noms et la liste des références dans la visionneuse. |
| TEST-DWG-SETUP-03 | Même feuille, même preset, fusion cochée, autre destination vide. | Vues incorporées au DWG de feuille ; comparer au test 02. Ne pas compter les images comme des vues fusionnables. |
| TEST-DWG-SETUP-04 | Publier deux feuilles avec les quatre combinaisons Par feuille/Lot Revit × fusion activée/désactivée. | Case de fusion indépendante du mode. Par feuille conserve noms et sous-dossier ; Lot Revit conserve préfixe et dossier parent, produit plusieurs DWG. Vérifier ordre et rapport, qui affiche le répertoire du lot. |
| TEST-DWG-SETUP-05 | Créer un carnet temporaire, réordonner ses feuilles, sélectionner plusieurs éléments avec Ctrl/Maj, cliquer sur l'engrenage. | Export se ferme ; fenêtre native de configuration DWG/DXF visible et utilisable, aucun blocage ni fenêtre cachée. Fermer la fenêtre native puis rouvrir Export : carnet temporaire, ordre, réglages, sélection et branches dépliées restaurés. Refaire en annulant les réglages natifs. |
| TEST-DWG-SETUP-06 | Depuis l'engrenage, créer « TAA - DCE sans XRef », fermer puis rouvrir Export ; cliquer aussi Actualiser. Renommer/supprimer un preset sélectionné. | Nouveau preset disponible automatiquement à la réouverture et après Actualiser. La sélection valide reste inchangée. Le nom supprimé reste affiché : export en erreur explicite, sans remplacement silencieux. Choisir ensuite un preset existant. |
| TEST-DWG-SETUP-07 | Enregistrer/appliquer un profil avec fusion désactivée sur un carnet ; rétablir son héritage, puis surcharger le dossier parent, le sous-dossier et le carnet. | Valeurs effectives et origine cohérentes. False doit rester False. Modifier la case ne fige pas les autres champs hérités. Le profil reste une application de valeurs, selon le fonctionnement existant. |
| TEST-DWG-SETUP-08 | Sauver les réglages fusion False sur un carnet persistant et True sur un dossier ; fermer/reouvrir Revit et le projet. | Valeurs persistantes et héritage restaurés. Ne pas attendre de persistance permanente des carnets temporaires. |
| TEST-DWG-SETUP-09 | Sur une copie sauvegardée du stockage Export et du profil personnalisé, retirer seulement `dwg_merge_views` puis rouvrir Export. Tester les deux anciens modes DWG. | Fusion activée par défaut ; autres réglages, destinations, carnets et profils préservés. Ouverture seule sans réécriture. Un changement du dossier doit encore être hérité par le carnet. |
| TEST-DWG-SETUP-10 | PDF + DWG, deux carnets de destinations différentes, puis dossier complet et sélection Ctrl/Maj de feuilles ; tester PDF combiné et séparé. | Même périmètre dans résumé/aperçu/publication ; PDFs identiques en noms, ordre et options. Progression 0–100 % cohérente, sans 100 % avant le dernier travail ; rapport final utilisable. Tester aussi un refus/échec DWG. |
| TEST-DWG-SETUP-11 | Feuille avec lien Revit visible ; exporter fusion désactivée puis activée dans deux dossiers vides. | Relever les fichiers, XRefs et géométries du lien pour chaque état, y compris liens imbriqués si présents. Confirmer le comportement effectif de 2025.4 ; aucune validation préalable présumée. |
| TEST-DWG-SETUP-12 | Feuille contenant une image raster, fusion activée puis désactivée. | Relever toutes les ressources externes. Vérifier la présence de l'image dans la visionneuse avec ses ressources. Le rapport prévient des annexes possibles, sans promettre un DWG autonome. |

Compléter le test 05 sur deux projets ouverts : aucun carnet temporaire ni sélection
ne doit passer d'un projet à l'autre. Contrôler la lisibilité de la zone DWG à la
taille minimale de fenêtre et avec la mise à l'échelle Windows utilisée à l'agence.

Pour chaque test, consigner : build Revit exact, version pyRevit, commit, preset,
mode de sortie, état fusion et couleurs, nombre de feuilles, dossier vide utilisé,
liste des fichiers/XRefs, capture avant/après et erreurs éventuelles. Résultat :
**OK / Échec / Non testé**, avec commentaire ; garder les DWG et annexes pour comparaison.

## Vérification hors Revit

Depuis la racine du dépôt :

```bash
python -m pytest tests OutilsTAA.extension/OutilsTAA.tab/Export.panel/tests --ignore=tests/calculation --ignore=tests/plans_vente --import-mode=importlib -q
```

Cette suite couvre Export, y compris les contrats DWG, le handler de
case, les hooks actifs, les chemins, les tests PDF et la progression existants.
Elle ne constitue pas une recette Revit. Le nombre final exécuté est consigné dans
la PR ; voir [l'analyse technique](24_Export_Reglages_DWG.md).
