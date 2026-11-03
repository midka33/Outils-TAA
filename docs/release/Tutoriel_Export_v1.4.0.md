# Tutoriel — Export

**Outils TAA v1.4.0 — Autodesk Revit 2025.4 / pyRevit 5.x / Windows**

## 1. Objet

**Export** organise les mises en page Revit dans une arborescence de dossiers et publie les fichiers **PDF**, **DWG** ou les deux. Les réglages et la structure restent associés au projet Revit concerné.

Un dossier peut être un simple conteneur de sous-dossiers, contenir des feuilles, ou combiner les deux. La fenêtre n'utilise plus le mot « carnet » pour désigner les dossiers.

## 2. Trois zones dans une seule fenêtre

Ouvrir **Outils TAA > Export**.

- **À gauche — Mises en page Revit** : explorateur des feuilles disponibles dans le projet.
- **Au centre — Arborescence de publication** : dossiers et feuilles à publier.
- **À droite — Réglages de publication** : formats, qualité, profils, destination et noms de fichiers.

Le bouton **◀ Feuilles / ▶ Feuilles** masque ou réaffiche l'explorateur de gauche. La séparation verticale permet d'ajuster sa largeur, conservée pour les prochaines ouvertures.

## 3. Chercher et ajouter des mises en page

1. Créer un dossier avec **Nouveau dossier**, ou sélectionner un dossier existant.
2. Dans l'explorateur de gauche, chercher une feuille par **numéro** ou **nom**.
3. Utiliser les regroupements par numéro/nom/paramètre et, si nécessaire, un **filtre de paramètre et de valeur**.
4. Cocher **Non ajoutées uniquement** pour masquer les feuilles déjà utilisées dans la publication.
5. Sélectionner plusieurs feuilles avec **Ctrl**, **Maj** ou **Ctrl+A**.
6. Cliquer sur **Ajouter (N)**, double-cliquer une feuille ou la glisser vers le dossier cible.

**Principe important :** l'ajout depuis la liste de gauche **copie une référence de feuille** dans la publication. Il ne supprime pas la feuille Revit et ne la retire pas des autres dossiers. Une même feuille peut figurer dans différents dossiers ; un doublon dans un même dossier est ignoré.

## 4. Organiser les dossiers

- Double-cliquer un dossier pour l'ouvrir ou le refermer.
- Glisser une feuille ou un dossier **à l'intérieur de l'arborescence centrale** pour le déplacer ou changer son ordre.
- Utiliser **Ctrl / Maj** pour sélectionner plusieurs lignes avant une opération compatible.
- Pour renommer : sélectionner le dossier et cliquer sur **Renommer**, utiliser **F2**, ou son **clic droit > Renommer**.
- Pour supprimer : sélectionner la ou les lignes, puis cliquer sur **Supprimer**. La commande retire les références de la publication, jamais les feuilles du projet Revit.
- Le dossier **Général** est protégé. Les déplacements créant un cycle dans l'arborescence sont refusés.
- Un dossier vidé de ses mises en page reste présent jusqu'à sa suppression explicite.

Le renommage et les déplacements conservent les paramètres de publication associés au dossier.

## 5. PDF et DWG : réglages indépendants

Sélectionner le dossier parent si les mêmes réglages doivent s'appliquer à plusieurs sous-dossiers.

**PDF** : cocher **Publier** ; choisir :
- **Combiné** : un PDF regroupant les feuilles de chaque dossier publié ;
- **Séparé** : un PDF par mise en page.

La qualité PDF est réglable en DPI. L'icône de paramètres donne accès aux options avancées.

**DWG** : cocher **Publier** ; sélectionner la **Configuration DWG Revit**. Le bouton **Actualiser** recharge les configurations. L'engrenage ouvre les paramètres DWG natifs après fermeture de la fenêtre Export.

Les options **Fusionner les vues et les liens dans le DWG** et **Forcer les couleurs vraies** restent disponibles. Le moteur choisit automatiquement une stratégie adaptée au nombre de feuilles ; le livrable métier reste **un DWG par mise en page**.

Revit peut produire des fichiers auxiliaires lorsque certaines ressources externes ne sont pas incorporables.

## 6. Deux options de classement des fichiers

Dans **Organisation des fichiers**, les deux cases sont **indépendantes** :

1. **Créer ce dossier dans la sortie** : ajoute le nom du dossier publié au chemin.
2. **Créer un sous-dossier par format (PDF et DWG)** : ajoute les sous-dossiers `PDF/` et `DWG/`, même si la première case est désactivée.

Exemple pour un dossier `A2100_Façades_Collectif_A`, après les éventuels dossiers parents :

| Créer le dossier publié | Séparer les formats | Chemins utilisés |
|---|---|---|
| Oui | Oui | `A2100_Façades_Collectif_A/PDF/`, `A2100_Façades_Collectif_A/DWG/` |
| Oui | Non | `A2100_Façades_Collectif_A/` (PDF et DWG ensemble) |
| Non | Oui | `PDF/`, `DWG/` |
| Non | Non | Dossier parent directement |

Seuls les formats effectivement activés produisent leurs fichiers. Le mode **PDF combiné/séparé** ne change pas le classement.

Les anciens réglages qui ne comportaient qu'une case conservent leurs chemins tant que le nouveau choix n'est pas explicitement modifié.

## 7. Nommage des livrables

Les champs **Nommage PDF** et **Nommage DWG** permettent des modèles de noms.

- `{nom_dossier}` : nom du dossier **publié**.
- `{dossier}` : nom de son **dossier parent**.
- `{numero}` et `{nom}` : numéro et nom de mise en page.
- Des variables supplémentaires de feuille ou d'informations de projet sont insérables via **Options avancées**.

Le jeton historique `{carnet}` reste accepté en lecture et représente la même chose que `{nom_dossier}` ; ne l'utiliser que dans les anciens modèles déjà enregistrés.

En **PDF combiné**, le nom général du PDF provient du dossier. Le nommage des DWG devient automatiquement indépendant pour produire un nom par feuille ; sinon la case **Nommage DWG indépendant du PDF** permet de choisir cette règle.

## 8. Profils, héritage et enregistrement

Les réglages définis sur un dossier parent sont transmis à ses descendants **sauf surcharge**.

- Modifier une valeur dans un sous-dossier ne change pas le parent ni les autres sous-dossiers.
- **Revenir à l'héritage** efface les surcharges du dossier actif.
- Un profil permet de mémoriser un ensemble de réglages pour des publications répétitives.
- L'arborescence, les noms, les feuilles et les réglages persistants sont conservés après fermeture complète de Revit et ne se mélangent pas entre projets.

## 9. Aperçu et publication réelle

1. Sélectionner un dossier ou un ensemble de dossiers à publier.
2. Cliquer sur **Aperçu** et vérifier **Dossier**, feuilles, formats, noms et **chemins de sortie**.
3. Corriger les éventuelles erreurs bloquantes. Les dossiers sans feuilles propres n'empêchent pas la publication de leurs descendants.
4. Cliquer sur **Publier**, vérifier l'aperçu de confirmation et lancer.
5. Contrôler le rapport final et, si nécessaire, ouvrir le dossier de destination.

**Exemple validé :** publication du dossier parent `A2000 Plan des façades` avec cinq sous-dossiers : **5 PDF combinés et 16 DWG** (21 fichiers) sans erreur bloquante.

## 10. Progression et limites

La progression reflète les étapes contrôlées ou les événements de progression effectivement fournis par Revit. La barre ne prétend pas connaître la durée d'un export natif qui ne fournit aucun avancement.

La publication des **seules feuilles modifiées** est reportée en V2. Le **PDF en arrière-plan** n'est pas activé en V1.4.0.

Pour une livraison officielle, enregistrer/synchroniser le modèle, choisir une destination de test si nécessaire et contrôler le rapport plutôt que de supposer qu'un dossier vide représente une publication.

**Références :** `docs/09_Export.md`, `docs/09_Export_Project_Persistence.md`, `docs/24_Export_Reglages_DWG.md`, `docs/release/Notes_v1.4.0.md`.
