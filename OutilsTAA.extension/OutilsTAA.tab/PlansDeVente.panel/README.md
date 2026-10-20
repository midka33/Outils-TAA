# Plans de vente V1.1

Module Outils TAA pour Autodesk Revit 2025.4 / pyRevit 5.x.

La V1 historique a été livrée dans Outils TAA v1.2.0. La V1.1 ajoute la
génération depuis les pièces de fichiers Revit liés directs et a été validée
par l'utilisateur dans Revit 2025.4 le 20 octobre 2026. Elle prépare la release
Outils TAA v1.3.0.

Le module génère vues, crops, étiquettes, cotations, repérages, nomenclatures,
légendes et feuilles depuis une feuille modèle. Les niveaux SITE nécessaires aux
logements liés sont créés automatiquement lorsqu'ils sont absents.

Les identifiants techniques des instances de lien restent internes. Un numéro
logement unique conserve son nom métier ; en cas de doublon entre plusieurs
sources, l'utilisateur choisit le libellé de différenciation.

Condition connue de la V1.1 : les types d'étiquette de pièce et de cote doivent
être disponibles dans le fichier hôte SITE. Une annotation seulement visible à
travers une vue liée ne permet pas encore au module de choisir son type.

Référence : `docs/20_Plans_de_Vente.md`.
Guide : `docs/release/Tutoriel_Plans_de_Vente_v1.3.0.md`.
Recette : `docs/release/Preparation_Plans_de_Vente_V1.1_Liens.md`.

Hors périmètre : liens imbriqués, mise à jour automatique des plans existants,
plus de deux vues principales sur une même feuille et optimisation des très
grands lots.
