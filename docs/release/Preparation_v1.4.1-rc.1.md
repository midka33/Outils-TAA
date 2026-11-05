# Recette — Outils TAA v1.4.1-rc.1

**Base prévue :** `main`, après fusion PR #48 (`3d47147efc6332ebb6a188482b936481a8302243`). **Statut : préparation seulement**.

## Tests à vérifier avant publication du candidat
- [ ] Exécuter les tests automatisés Export, contrat ruban, Calculs des pièces et Plans de vente sur le **SHA final** de la candidate.
- [ ] Vérifier que l'archive ZIP contient seulement l'extension attendue, sans fichiers de développement.
- [ ] Produire et vérifier les sommes SHA-256 de ZIP, installateur CMD et tutoriels.
- [ ] Tester le CMD sans élévation sur un poste Windows de recette ; sauvegarder la version installée.
- [ ] Vérifier la version et les fichiers de la release GitHub ; tag sur le SHA final testé, et non sur une branche Draft.

## Recette Revit 2025.4 / pyRevit 5.x

| ID | Module | Test | Statut |
|---|---|---|---|
| RC-01 | Export | PDF combiné + DWG : entrer `{numero}-TEST-{nom}`, sortir du champ, rouvrir Export ; vérifier aperçu et fichiers DWG. | À tester |
| RC-02 | Export | Ajouter A101 dans A puis A102 dans B ; aucune sélection résiduelle ni A101 dans B. | **Validé utilisateur 2026-11-05** |
| RC-03 | Export | Renommer/renuméroter A101 dans Revit, fermer puis rouvrir Export ; nouveaux libellés dans l'explorateur et le dossier, publication maintenue. | **Validé utilisateur 2026-11-05** |
| RC-04 | Plans de vente | Les 4 listes montrent les choix SITE ; choisir des valeurs explicites et créer une feuille mono-niveau. | À tester |
| RC-05 | Plans de vente | Options avancées : enregistrer puis fermer/réouvrir ; projet A conserve ses choix, projet B reste indépendant ; vérifier retour à A. | À tester |
| RC-06 | Plans de vente | Feuille modèle sans repérage : avertissement métier lisible sans `NoneType.view` ; feuille réellement invalide : motif bloquant affiché. | À confirmer sur candidat |
| RC-07 | Non-régression | PDF/DWG publication, Calculs des pièces et génération simple Plans de vente. | À tester |

**Les historiques TEST-01 à TEST-30 sont tous validés et ne figurent pas dans la recette à refaire.**

## Règles
La candidate ne doit pas intégrer les PR #30 ou #49 tant qu'elles ne sont pas fusionnées volontairement. Aucun nouveau schéma de réglages individuels par feuille n'est inclus.

Un test automatisé vert ne remplace pas une recette API Revit/WPF sur poste réel.
