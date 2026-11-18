# Outils TAA v1.5.0 — Dossiers automatiques et amélioration du travail en équipe

**Release du 17 novembre 2026** · **Autodesk Revit 2025.4** · **pyRevit 5.x** · Windows.

Cette version étend Outils TAA avec des dossiers de publication qui suivent les paramètres des mises en page Revit, une configuration d'Export partageable entre collaborateurs et une fenêtre **À propos** pour identifier la version installée.

## Nouveauté principale — Export : dossiers automatiques

Depuis le panneau **Mises en page Revit**, cliquer sur **Dossier auto** pour créer un dossier alimenté par les feuilles qui correspondent à **un paramètre et une valeur** (par exemple `Phase du projet = PRO`). Un **deuxième paramètre** peut créer des sous-dossiers (par exemple `Sous-titre`).

- **Aperçu avant création** : nombre de feuilles, nombre de sous-dossiers et effectif de chacun.
- **Actualisation** à l'ouverture d'Export, au clic **Actualiser** et avant aperçu/publication. Les nouvelles feuilles Revit répondant à la règle sont intégrées automatiquement.
- **Repère visuel** : icône turquoise spécifique aux dossiers/sous-dossiers automatiques ; icône orange habituelle pour les dossiers manuels.
- **Figer le dossier entier** : convertir toute l'arborescence en manuel.
- **Figer un seul sous-dossier** : conserver uniquement sa liste de feuilles tandis que les autres sous-dossiers restent automatiques.
- **Rendre ce sous-dossier automatique** : retrouver sa composition calculée depuis Revit, avec une confirmation explicite de remplacement des modifications manuelles de ce sous-dossier.
- Les règles et conversions sont persistantes, y compris après fermeture/réouverture. Elles n'écrivent pas dans les paramètres des feuilles Revit.

**Important :** les sous-dossiers calculés ne sont pas un duplicata automatique de l'organisation native du navigateur de projet Revit. Les paramètres de sélection et de regroupement sont choisis dans l'outil.

## Export : configuration collaborative

La configuration des dossiers de publication et de leurs réglages PDF/DWG peut être **partagée entre utilisateurs du même projet central** via un fichier JSON situé à côté de la maquette centrale.

- Indication **Configuration : Partagée** ou **Locale** et chemin utilisé.
- Bouton **Actualiser** pour relire les changements effectués depuis un autre poste.
- Gestion des sauvegardes et des conflits d'écriture pour éviter l'écrasement silencieux d'une configuration déjà modifiée.
- Import explicite possible d'une ancienne configuration Export, avec aperçu et contrôles.
- Les préférences strictement personnelles ne sont pas nécessairement partagées.
- Aucune sauvegarde des réglages de publication dans le modèle RVT.

La validation complète **en simultané sur deux postes Windows/SMB** n'est pas documentée comme terminée ; tester les droits et les verrouillages avec le réseau de l'agence avant déploiement collectif.

## Bouton « À propos » — version de la suite

Un bouton **À propos**, premier panneau à gauche dans l'onglet **OutilsTAA** de Revit, ouvre une fenêtre donnant la **version exacte de la suite installée**. Le même dialogue reste accessible dans la fenêtre Export.

- Version annoncée pour ce paquet : **1.5.0 — stable**.
- Icône harmonisée avec l'orange des autres modules.
- Version lue dans `OutilsTAA.extension/version.json`, sans connexion Internet ni GitHub.

## Calculs des pièces — ergonomie et gestion des groupes

- Parcours de revue et de confirmation plus lisible pour les sommes par appartement et les **variantes**.
- Gestion plus prudente des paramètres de pièces liés aux **groupes Revit**, avec contrôles avant écriture, compte rendu et retour arrière en cas d'incohérence.
- Lorsque les valeurs doivent différer entre occurrences, le paramètre peut devenir durablement variable entre groupes ; vérifier cet effet global dans Revit avant de confirmer.
- Le choix manuel d'**unité de sortie** a été retiré de la fenêtre principale : les conversions restent déterminées automatiquement par les types de paramètres.
- Les cas complexes d'alignement uniforme des groupes conservent des protections et peuvent nécessiter une intervention manuelle dans Revit. Cette version ne garantit pas une uniformisation forcée de tous les groupes.

## Plans de vente

Le module Plans de vente **V1.1**, y compris le fonctionnement avec fichiers liés et les options livrées en v1.4.1, est conservé. Cette release n'introduit **pas** de nouvelle fonctionnalité de Plans de vente.

## Installer ou mettre à jour

1. **Fermer entièrement Revit**.
2. Télécharger **`Outils-TAA_v1.5.0.zip`** dans les fichiers de cette release.
3. Identifier le chemin de l'extension **`OutilsTAA.extension`** réellement chargée par pyRevit. **Sauvegarder** son contenu avant toute modification.
4. Extraire le ZIP, puis remplacer le contenu de l'extension existante par le dossier **`OutilsTAA.extension`** de l'archive, dans **le même emplacement**. Éviter de créer une seconde copie de l'extension qui pourrait être chargée en parallèle.
5. Redémarrer Revit, ouvrir l'onglet **OutilsTAA**, puis **À propos** : la version doit indiquer **1.5.0 — stable**.

**Installation d'agence centralisée :** lorsque pyRevit utilise une extension partagée sur un serveur, réaliser la mise à jour **sur cette copie réseau**, conformément à la procédure `docs/26_Deploiement_Agence.md`, après sauvegarde et vérification des droits. Ne pas installer une copie utilisateur concurrente.

**Fichiers livrés :** une archive ZIP de l'extension et les trois tutoriels **Export**, **Calculs des pièces** et **Plans de vente**. Les archives « Source code » sont affichées automatiquement par GitHub et ne constituent pas le paquet d'installation recommandé.

**Intégrité :** le ZIP a été contrôlé par **SHA-256** durant la publication ; GitHub affiche son empreinte à côté du fichier.

## Compatibilité, qualité et limites

- Compatible : **Revit 2025.4 / pyRevit 5.x**, Windows, scripts IronPython/WPF ; sans Dynamo.
- Dossiers manuels et configurations existantes conservés ; le stockage Export reste au **schéma JSON 8**.
- Les campagnes de gel individuel, de réversibilité et d'actualisation des dossiers automatiques ainsi que la fenêtre À propos ont été confirmées sous Revit 2025.4 par l'utilisateur.
- La qualification en réseau multi-postes, la mise à jour manuelle depuis le ZIP sur un poste Windows cible et les cas Revit complexes du module Calculs restent à contrôler sur les maquettes/environnements concernés.
- Cette release ne contient pas les modules futurs en préparation (cotations, étiquetage, légendes, giration des véhicules).

**Historique :** [différences depuis v1.4.1](https://github.com/midka33/Outils-TAA/compare/v1.4.1...v1.5.0).
