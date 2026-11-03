# Outils TAA v1.3.0 — Plans de vente V1.1 / fichiers Revit liés

Outils TAA v1.3.0 étend **Plans de vente** aux logements dont les pièces se
trouvent dans des fichiers Revit liés, tout en générant les livrables dans le
fichier hôte SITE.

## Nouveautés Plans de vente

- Option **Inclure les pièces des fichiers Revit liés** et colonne Source.
- Identité fiable par instance de lien + numéro logement.
- Crop, repérage, tags et cotations adaptés aux coordonnées / références liées.
- Nomenclatures natives isolées par fichier et instance.
- Création automatique des niveaux SITE manquants et des vues plan sources nécessaires.
- Aucun suffixe technique `-L<id>` dans les noms visibles.
- Si plusieurs sources portent le même numéro, l'utilisateur choisit le libellé de différenciation.
- Les légendes du modèle sont replacées sans dupliquer la vue Legend.

## Validation

Le workflow représentatif a été validé par l'utilisateur dans Autodesk Revit
2025.4 avec pyRevit 5.x le 20 octobre 2026, depuis un fichier SITE utilisant des
bâtiments liés.

Les étiquettes de pièces et les cotes ont été confirmées lorsque leurs types sont
présents dans le fichier hôte SITE.

La publication reste conditionnée aux CI de la PR, puis aux quatre contrôles du
SHA exact fusionné dans `main`, ainsi qu'au contrôle du ZIP de distribution.

## Limites connues

- liens directs chargés uniquement ;
- liens imbriqués et transformations verticalement inclinées / renversées hors périmètre ;
- les types d'étiquette et de cote doivent exister dans SITE : une annotation seulement visible via une vue liée ne fournit pas encore le type ;
- les nomenclatures de pièces modèles doivent inclure les éléments des fichiers liés ;
- mise à jour automatique des plans existants hors périmètre.

## Export et Calculs des pièces

Aucun changement métier n'est introduit dans ces deux modules par cette release.

## Installation / mise à jour

1. Fermer Revit.
2. Lancer **INSTALLER_Outils_TAA_v1.3.0.cmd**.
3. Relancer Revit ou utiliser Reload dans pyRevit.

L'installation utilisateur reste sans droit administrateur dans
`%APPDATA%\pyRevit\Extensions\OutilsTAA.extension` et sauvegarde la version
précédente avant remplacement.
