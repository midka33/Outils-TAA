# Plans de vente — Références d'interface

Ces maquettes sont les références visuelles approuvées pour l'**Étape 09 —
stabilisation de l'interface V1** du module Plans de vente.

## Interface principale

![Interface principale Plans de vente](09_interface_principale.webp)

Référence fonctionnelle :

- génération de tous les logements en une seule opération ;
- filtrage optionnel par paramètre de pièce, condition et valeur ;
- choix d'une feuille modèle ;
- choix du comportement pour les logements multi-niveaux ;
- un bouton principal de création par lot ;
- résumé du modèle et du résultat attendu.

## Options avancées

![Options avancées Plans de vente](09_options_avancees.webp)

Référence fonctionnelle :

- création uniquement des logements sans plan existant ;
- choix du paramètre identifiant le logement ;
- marge de crop ;
- règle d'échelle automatique et échelles de repli ;
- paramètres de rapport et de contrôle ;
- les réglages déduits automatiquement de la feuille modèle restent en lecture
  seule tant qu'un remplacement manuel sûr n'est pas pris en charge.

## Charte graphique

L'implémentation doit réutiliser la charte commune Outils TAA :

- couleur de mise en avant Tallandier : `#FA641F`
  (`TAABrandOrangeBrush`) ;
- fond principal : `#F7F7F7` ;
- panneaux : blanc ;
- texte principal : `#252525` ;
- typographie : **Segoe UI** ;
- tailles, espacements et styles de contrôles issus des ResourceDictionary TAA.

Les maquettes servent de **référence d'intention**. Les contrôles WPF peuvent
être adaptés légèrement aux contraintes de pyRevit / Revit 2025.4, mais la
hiérarchie, les couleurs et le parcours utilisateur doivent rester cohérents
avec ces références.

## État de l'implémentation

### Étape 09A

Implémenté :

- nouvelle interface principale ;
- fenêtre Options avancées ;
- filtrage générique des logements ;
- génération par lot des logements mono-niveau ;
- saut automatique des plans déjà existants ;
- rapport de traitement.

### Étape 09B

Implémenté en **09B.1** :

- détection des logements comportant plusieurs niveaux ;
- découpage métier en sous-logements mono-niveau ;
- option « une feuille par niveau » raccordée au moteur 07D ;
- conservation de l'identifiant logement original pour les filtres de nomenclatures ;
- noms de sortie distincts par niveau afin d'éviter les collisions.

Implémenté en **09B.2** — à tester dans Revit 2025.4 :

- une feuille unique avec une vue logement par niveau ;
- vues de niveau placées côte à côte dans la zone de la vue logement modèle ;
- échelle modèle conservée tant qu'il n'y a pas de collision ;
- une seule série de nomenclatures globales au logement ;
- repérage unique basé sur le niveau bas ;
- champ Niveau du cartouche renseigné avec tous les niveaux représentés (ex. `0 / 1`).

### Aperçu de feuille

L'interface utilise maintenant une image PNG temporaire exportée directement depuis la feuille Revit choisie. La vue logement, les nomenclatures et le repérage sont mis en évidence par une surcouche. Le même principe est utilisé dans la zone « Résultat attendu » afin d'éviter les anciens schémas abstraits.
