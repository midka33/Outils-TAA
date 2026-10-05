# Export — Tutoriel utilisateur

**Outils TAA · Revit 2025.4 · pyRevit 5.x**

Version du guide : 5 octobre 2026 — préparation de la V1.

Ce guide décrit l'interface actuelle et le correctif de publication par sélection
multiple livré avec ce document. Son fonctionnement a été confirmé par l’utilisateur dans Revit le
5 octobre 2026 après essai de la branche de la PR #11. La recette détaillée reste
un support de vérification avant release.

## 1. Première publication, pas à pas

Exemple : publier trois plans en PDF et en DWG.

1. Ouvrez le projet Revit, puis cliquez sur la grande icône du panneau **Export**
   dans l'onglet **Outils TAA**.
2. Dans l'arborescence à gauche, sélectionnez **Général**, ou créez un dossier
   avec **Nouveau dossier**, puis sélectionnez-le.
3. Cliquez sur **Ajouter / gérer…**, choisissez **Manuel**, puis donnez un nom
   au carnet, par exemple `Plans architecte`.
4. Cliquez sur **Sélectionner les feuilles dans Revit** et choisissez les trois
   feuilles. Laissez cochée **Enregistrer le carnet pour les prochaines sessions**,
   puis cliquez sur **Ajouter le carnet**.
5. Cliquez sur le carnet dans l'arborescence. À droite, choisissez le profil
   **PDF + DWG** : PDF combiné et DWG séparés.
6. Renseignez **Destination** avec le bouton dossier ou en saisissant un chemin.
7. Dans **Nom du fichier**, saisissez par exemple `{carnet}-{numero}`.
   L'extension PDF/DWG est ajoutée par l'outil. Pour le PDF combiné, le numéro
   utilisé est celui de la première feuille du périmètre.
8. Vérifiez le **Résumé de la publication**, en bas : un carnet, trois mises en
   page et les formats PDF + DWG.
9. Cliquez sur **Aperçu…** pour contrôler les fichiers et leurs chemins, puis
   fermez cet aperçu.
10. Cliquez sur **Publier le carnet « Plans architecte »**, contrôlez l'aperçu de
    confirmation, puis cliquez sur **Confirmer et publier**.
11. Lisez le **Rapport de publication** et contrôlez les fichiers produits.

L'aperçu ouvert par **Aperçu…** sert uniquement à consulter. Le bouton **Publier**
ouvre un aperçu avec confirmation avant de démarrer les exports.

## 2. Comprendre l'arborescence

| Élément | Rôle | Effet d'une publication |
|---|---|---|
| Dossier | Organiser les carnets et porter des réglages communs | Inclut ses carnets et ceux de ses sous-dossiers |
| Carnet | Regrouper des mises en page | Inclut toutes les mises en page du carnet |
| Mise en page | Une feuille Revit du carnet | Inclut seulement cette feuille |

Une même feuille peut appartenir à plusieurs carnets. Chaque carnet garde son
propre nommage, ses formats et sa destination.

Pour réorganiser les éléments persistants, utilisez le glisser-déposer. Le repère
indique une insertion avant/après un élément ou à l'intérieur d'un dossier.
L'ordre des feuilles dans le carnet est l'ordre de publication ; sélectionner
les feuilles dans un autre ordre ne change pas cet ordre.

Un double-clic sur un carnet ouvre la liste de ses mises en page. **Supprimer**
retire les carnets/dossiers sélectionnés de l'organisation d'Export, après
confirmation ; les feuilles du projet Revit sont conservées. Un dossier non vide
est protégé si son contenu n'est pas lui-même sélectionné pour suppression.

## 3. Créer les carnets selon votre besoin

Dans **Ajouter / gérer…**, trois modes sont proposés :

| Mode | Utilisation | Manipulation |
|---|---|---|
| **Par paramètre** | Regrouper les feuilles selon un paramètre, par exemple Sous-titre | Choisir le paramètre, cocher les carnets à ajouter, puis **Ajouter les carnets sélectionnés** |
| **Manuel** | Constituer un carnet avec les feuilles de votre choix | Donner un nom, sélectionner les feuilles, conserver la case d'enregistrement pour le réutiliser |
| **Temporaire** | Préparer un envoi ponctuel | Donner un nom et choisir les feuilles ; le carnet n'est pas conservé après fermeture de la fenêtre |

Sélectionnez d'abord le dossier de destination dans l'arborescence : les nouveaux
carnets seront ajoutés à cet emplacement. Dans le mode par paramètre,
**Actualiser** recalcule la liste proposée avant l'ajout.

## 4. Publier plusieurs mises en page sélectionnées

Exemple : le carnet contient `A01`, `A02`, `A03`, `A04`, mais vous souhaitez
publier uniquement `A01` et `A03`.

1. Développez le carnet pour afficher ses feuilles.
2. Cliquez sur `A01`.
3. Maintenez **Ctrl** et cliquez sur `A03`. Les deux lignes sont sélectionnées.
4. Le bouton devient **Publier la sélection**. Le résumé doit annoncer
   **1 carnet et 2 mises en page prévues**.
5. Cliquez sur **Aperçu…** et vérifiez le périmètre, les noms et les destinations.
6. Cliquez sur **Publier la sélection**, puis **Confirmer et publier**.

| Réglage PDF du carnet | Résultat pour A01 + A03 |
|---|---|
| **Séparé** | Deux PDF, un pour A01 et un pour A03 |
| **Combiné** | Un PDF contenant uniquement A01 puis A03 |

**Attention au nom du PDF combiné :** une sélection partielle utilise le modèle
de nommage du carnet. Elle peut donc remplacer un PDF complet déjà présent sous
le même nom. Pour un envoi partiel à conserver séparément, choisissez une autre
destination ou un nom distinct, puis vérifiez l'avertissement de fichier existant.

Pour sélectionner une plage, cliquez sur la première feuille, puis maintenez
**Maj** en cliquant sur la dernière, dans le même carnet. **Ctrl + clic** sur une
ligne sélectionnée la retire du périmètre. Si vous retirez toutes les lignes,
la publication est désactivée.

## 5. Publier plusieurs carnets, ou une sélection mixte

Pour publier deux carnets complets, cliquez sur le premier puis faites
**Ctrl + clic** sur le second. Cliquez sur **Publier la sélection**.

Vous pouvez aussi sélectionner des feuilles appartenant à différents carnets,
ou un carnet complet et certaines feuilles d'un autre carnet.

Les règles sont les suivantes :

- Chaque carnet utilise ses propres réglages effectifs et sa destination.
- En PDF combiné, il y a un PDF par carnet concerné, contenant les feuilles de
  ce carnet incluses dans le périmètre. Les carnets ne sont pas fusionnés entre eux.
- Si un carnet et certaines de ses feuilles sont sélectionnés ensemble, le
  carnet entier est publié une seule fois.
- Un dossier sélectionné inclut ses descendants ; sélectionner aussi ces
  descendants ne les publie pas une seconde fois.
- Une feuille présente dans deux carnets reste une publication dans chacun des
  deux carnets. Une collision de chemins entre ces livrables bloque la confirmation.

Le panneau **Réglages de publication** indique l'élément actif auquel les réglages
s'appliquent. La sélection multiple ne réalise pas une modification groupée des
réglages. Pour préparer un réglage commun, utilisez le dossier parent ; pour un
réglage particulier, sélectionnez d'abord le carnet seul.

## 6. Régler les formats et le nommage

### PDF

Cochez **Publier** dans la ligne PDF, puis choisissez **Combiné** ou **Séparé**.
Le champ **Qualité** règle la résolution en DPI. Le bouton à droite ouvre
**Paramètres PDF** : traitement vectoriel/raster et options de masquage des
limites de cadrage, zones de définition, plans de référence, etc.

Cliquez sur **Appliquer** pour valider ce dialogue. L'export en arrière-plan est
indisponible en V1 : Export attend la fin de la création pour vérifier les fichiers.

### DWG

Cochez **Publier** dans la ligne DWG. Choisissez le mode, une configuration DWG
Revit dans la liste et, si souhaité, **Couleur vraie**.

Le DWG combiné s'appuie sur le mode natif Revit `MergedViews`. Il ne correspond
pas à une fusion PDF : contrôlez les fichiers DWG et les éventuelles références
externes livrées dans votre configuration. Pour un DWG par feuille, utilisez
**Séparé**.

### Destination et noms

| Champ ou option | Fonction |
|---|---|
| **Destination** | Dossier de sortie effectif du carnet |
| **Nom du fichier** | Texte fixe et variables, sans extension à ajouter manuellement |
| **Créer un sous-dossier pour ce carnet** | Range les exports séparés dans un dossier portant le nom du carnet |
| **Options avancées** | Recherche et insertion des variables et paramètres Revit |

Exemples : `{carnet}` pour un PDF combiné, `{numero}-{nom}` pour des fichiers
séparés, `{carnet}-{numero}` pour distinguer les feuilles de chaque carnet.

Dans **Options avancées**, recherchez une variable, sélectionnez-la, puis cliquez
sur **Insérer**. Les paramètres de feuille et les informations sur le projet
sont proposés séparément. Dans un export combiné, les variables de feuille sont
résolues à partir de la première feuille du périmètre.

Les caractères interdits dans les noms de fichiers sont remplacés. Vérifiez
l'aperçu : deux noms différents dans Revit peuvent aboutir au même nom sécurisé.

Lors de la publication d'un **dossier**, les dossiers et sous-dossiers de
l'arborescence sélectionnée sont reproduits sous la destination effective de
chaque carnet. Une publication directe de carnet ou de feuilles utilise sa
destination, avec le sous-dossier du carnet si cette option est active en mode séparé.

## 7. Réutiliser des réglages : héritage et profils

Un carnet reprend les réglages de son dossier lorsqu'aucune valeur locale ne les
remplace. Les sous-dossiers reprennent eux-mêmes ceux de leurs parents.

Exemple : réglez le dossier `DCE` en PDF combiné + DWG séparés. Ses carnets
héritent de ces valeurs. Si vous désactivez le DWG uniquement sur le carnet
`Notices`, ce carnet conserve son exception.

**Revenir à l'héritage** efface les réglages locaux du niveau actif. Cette action
ne remet pas à zéro les réglages des autres carnets ou des sous-dossiers.

Le champ **Profil** applique des réglages techniques prédéfinis au carnet actif.
**Enregistrer…** permet de créer un profil personnel. Les profils conservent
les formats et options techniques PDF/DWG ; la destination et le modèle de
nommage restent à régler séparément.

## 8. Lire l'aperçu et le rapport

Avant confirmation, vérifiez : le nombre de livrables, les formats, les noms,
les chemins complets et les avertissements. Le nombre de fichiers diffère du
nombre de feuilles : deux feuilles en PDF combiné donnent un seul PDF.

| Message ou situation | Vérification à faire |
|---|---|
| Destination manquante | Renseigner la destination du carnet ou de son dossier parent |
| Mise en page introuvable/non imprimable | Vérifier la feuille dans le projet actif |
| Collision de noms | Changer le nommage ou les destinations pour obtenir des chemins distincts |
| Fichier déjà présent | Vérifier que son remplacement est bien souhaité |
| Variable non résolue | Contrôler le paramètre choisi et sa valeur sur les feuilles |
| Erreur PDF/DWG dans le rapport | Lire et copier le diagnostic complet, puis vérifier les fichiers réellement produits |

**Annuler** dans l'aperçu de confirmation ne lance aucun export. Après publication,
le rapport présente les résultats et les erreurs. Un échec sur un carnet n'annule
pas les fichiers déjà produits par les autres carnets.

La V1 publie tout le périmètre sélectionné à chaque lancement. Elle ne propose
pas de filtre « uniquement les mises en page nouvelles ou modifiées ».
