# Outils TAA v1.4.0 — Export : explorateur de feuilles et publication PDF/DWG

**Date :** 3 novembre 2026  
**Cible :** Autodesk Revit 2025.4 · pyRevit 5.x · Windows  
**Périmètre de cette version :** module **Export**. Les comportements métier des modules **Calculs des pièces** et **Plans de vente V1.1** restent ceux de la v1.3.0.  
**Intégration :** [PR #39](https://github.com/midka33/Outils-TAA/pull/39), fusionnée dans `main` le 3 novembre 2026.

## Nouveautés Export

- **Explorateur des mises en page** à gauche de l'arborescence de publication : volet escamotable, largeur réglable et mémorisée, recherche instantanée, filtres d'utilisation, regroupement par numéro, nom et paramètres Revit.
- **Sélection multiple** Ctrl/Maj/Ctrl+A et ajout de feuilles par bouton, double-clic, menu contextuel ou glisser-déposer.
- **Dossiers de publication uniques** : une feuille peut être ajoutée à plusieurs dossiers, sans doublon au sein d'un même dossier ; son ajout depuis l'explorateur ne la retire pas d'un dossier existant.
- **Réorganisation** des feuilles et des dossiers par glisser-déposer, avec conservation de l'ordre et protection contre les cycles.
- **Renommage** d'un dossier existant via le bouton visible « Renommer », F2 ou son menu contextuel ; les feuilles, sous-dossiers et réglages sont conservés.
- **Terminologie** simplifiée : « dossier de publication » remplace « carnet » dans l'interface. Nouveau jeton de nommage PDF `{nom_dossier}` ; l'ancien `{carnet}` reste lisible pour les configurations antérieures.
- **Organisation des livrables** : deux cases indépendantes et héritables, « Créer ce dossier dans la sortie » et « Créer un sous-dossier par format (PDF et DWG) ». Les quatre combinaisons sont prises en charge, avec respect du comportement des anciennes configurations.
- **Publication récursive** : les dossiers parent sans feuilles restent visibles mais ne deviennent plus des cibles vides bloquant l'export de leurs sous-dossiers.
- **Prévisualisation et rapport** cohérents avec les chemins et noms réellement générés.

## Validation réelle Revit 2025.4

L'utilisateur a confirmé le **3 novembre 2026** les six campagnes suivantes :

| Test | Périmètre | Résultat |
|---|---|---|
| EXPORT-01 | Publication réelle multi-dossiers : **5 PDF combinés et 16 DWG**, chemins et rapport | Validé |
| EXPORT-02 | Renommage, conservation des feuilles/sous-dossiers/réglages, réouverture | Validé |
| EXPORT-03 | Suppression ciblée de feuilles/dossiers et protections | Validé |
| EXPORT-04 | Ajout multiple, glisser-déposer, ordre, absence de doublons, persistance | Validé |
| EXPORT-05 | Réglages hérités, surcharges, retour à l'héritage et aperçu | Validé |
| EXPORT-06 | Redémarrage complet de Revit, persistance des réglages, séparation entre projets | Validé |

La première campagne s'appuyait sur le dossier `A2000 Plan des façades`, contenant cinq sous-dossiers, soit **21 livrables**.

**Tests automatisés :** 375 tests Export hors Revit et contrôle du ruban réussis sur la branche de la PR #39. Le workflow de release relance aussi les suites Calculs des pièces, Plans de vente, Export et ruban **sur le commit exact à publier**, puis valide le ZIP avant la création de la release.

Cette recette reflète les scénarios confirmés par l'utilisateur ; elle n'affirme pas que toutes les variantes possibles du moteur Revit ont été rejouées manuellement.

## Compatibilité et limites

- Compatibilité confirmée : **Revit 2025.4 / pyRevit 5.x / Windows**.
- Les anciens profils et modèles `{carnet}` restent pris en charge, sans réinitialisation des dossiers ni changement automatique de leurs destinations.
- La publication des seules feuilles modifiées reste **hors périmètre V1** et fait partie des pistes V2.
- La publication PDF en arrière-plan n'est pas activée : aucune progression artificielle n'est affichée pendant les appels Revit qui ne rapportent pas leur avancement.
- Les éventuelles ressources DWG externes générées par Revit suivent les limites de ses configurations natives.
- Les modules **Plans de vente V1.1** et **Calculs des pièces** ne reçoivent pas de nouvelle fonctionnalité dans cette release.

## Installation sans droits administrateur

La release fournit :
- `Outils-TAA_v1.4.0.zip` — extension pyRevit complète ;
- `INSTALLER_Outils_TAA_v1.4.0.cmd` — installateur utilisateur vérifiant le SHA-256 du ZIP et sauvegardant la version précédente ;
- `SHA256SUMS.txt` — empreintes de contrôle ;
- trois tutoriels utilisateur associés à la version.

**Pour installer :** fermer Revit, exécuter `INSTALLER_Outils_TAA_v1.4.0.cmd` depuis la release GitHub, puis relancer Revit (ou recharger pyRevit). L'installation utilise `%APPDATA%\pyRevit\Extensions\OutilsTAA.extension` ; aucun droit administrateur n'est requis.

La publication effective de la release et la validité des sommes SHA-256 doivent être vérifiées depuis [GitHub Releases](https://github.com/midka33/Outils-TAA/releases/tag/v1.4.0).

## Documentation

- [Guide Export](Tutoriel_Export_v1.4.0.md)
- [Guide Calculs des pièces](Tutoriel_Calculs_Pieces_v1.4.0.md)
- [Guide Plans de vente](Tutoriel_Plans_de_Vente_v1.4.0.md)
- [Bilan de recette et préparation](Preparation_Export_v1.4.0.md)
- [Spécification courante Export](../09_Export.md)
