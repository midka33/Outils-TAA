# Sécurité

Outils TAA est un outil local pyRevit destiné à l'environnement Revit 2025.4.

## Principes

- Ne jamais stocker de secrets, mots de passe ou jetons dans le dépôt.
- Ne pas journaliser de données sensibles inutilement.
- Les chemins et paramètres utilisateur doivent être validés avant utilisation.
- Les fichiers générés doivent être écrits uniquement dans les destinations explicitement choisies.
- Toute erreur d'export doit être remontée sans masquer son origine.

## Signalement

Pour un problème de sécurité, ouvrir une issue privée si le mécanisme GitHub approprié est disponible ; sinon contacter directement le mainteneur du dépôt avant toute divulgation publique.
