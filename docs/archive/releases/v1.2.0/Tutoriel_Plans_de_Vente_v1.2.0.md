# Tutoriel — Plans de vente

**Outils TAA v1.2.0 — Autodesk Revit 2025.4 / pyRevit 5.x / Windows**

## Préparer la maquette

- Les pièces sont dans la maquette principale et portent un identifiant logement.
- Préparer une feuille modèle contenant le cartouche, la ou les vues principales,
  les nomenclatures et, si souhaité, le plan de repérage.
- Régler les gabarits, échelles, types d’étiquettes et de cotes adaptés au projet.
- Dessiner directement sur la feuille modèle un rectangle fermé autour du centre
  de chaque vue principale, avec un style de ligne dédié. Ces rectangles
  définissent les zones où seront placées les vues générées.

## Choisir le modèle selon le résultat souhaité

| Feuille modèle | Résultat pour un logement multi-niveaux |
|---|---|
| Une vue principale et une zone | Une feuille par niveau |
| Deux vues principales et deux zones | Deux niveaux sur une même feuille |

Les vues d’une même feuille utilisent une échelle commune. Les échelles de repli
et la réduction automatique se règlent dans les options avancées.

## Générer les plans

1. Enregistrer le projet, puis ouvrir **Outils TAA > Plans de vente**.
2. Choisir le paramètre identifiant les logements et le filtre éventuel.
3. Sélectionner la feuille modèle et vérifier son aperçu réel.
4. Choisir le style de ligne employé pour les zones des vues principales.
5. Vérifier les paramètres logement, bâtiment, étage et typologie, les types
   d’annotations et les options avancées.
6. Sélectionner les logements à produire. Pour un premier essai sur un nouveau
   projet, commencer par un logement représentatif.
7. Lancer la création. La fenêtre de progression indique les étapes effectivement
   terminées : vues, étiquettes, cotations, repérage, nomenclatures et feuille.
8. Lire le rapport : créations, éléments ignorés, avertissements et échecs.
9. Contrôler les feuilles produites, puis utiliser **Export** pour les PDF/DWG.

## Ce que le module produit

Les vues logement avec crop, les étiquettes et cotations, le repérage configuré,
les nomenclatures présentes sur le modèle et la mise en page sont générés selon
la configuration. Les surfaces habitables et annexes sont consolidées pour les
logements multi-niveaux ; les paramètres de cartouche sont renseignés.

## Points à surveiller

- Les rectangles doivent être fermés et contenir le centre des vues modèles.
  Une configuration invalide est signalée avant la génération.
- Contrôler le rapport et le rendu des crops, cotes et étiquettes, notamment pour
  les géométries particulières ou les logements très denses.
- Une opération Revit longue peut immobiliser temporairement la progression.
- La mise à jour automatique des plans déjà générés et plus de deux vues
  principales sur une même feuille ne font pas partie de la V1.
- Les optimisations complémentaires des très grands lots sont prévues ultérieurement.
