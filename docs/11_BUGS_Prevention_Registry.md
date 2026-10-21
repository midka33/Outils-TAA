# Outils TAA — Registre des bugs

**Statut :** Point d’entrée obligatoire  
**Cible :** Revit 2025.4 / pyRevit 5.x

Le registre détaillé n’est plus monolithique. Il est réparti par périmètre afin
de limiter le bruit documentaire et de rendre les règles anti-régression plus
faciles à consulter.

## À lire avant toute modification

1. Lire l’index : [`docs/bugs/INDEX.md`](bugs/INDEX.md).
2. Lire le registre du module concerné :
   - [Export](bugs/EXPORT.md)
   - [Calculs des pièces](bugs/CALCULS.md)
   - [Plans de vente](bugs/PLANS_DE_VENTE.md)
   - [Commun](bugs/COMMON.md)
   - [Tests et livraison](bugs/TESTS.md)
3. Identifier les règles préventives applicables.
4. Prévoir et exécuter le contrôle anti-régression associé.

## Cycle obligatoire

```text
Bug
↓
Reproduction
↓
Cause racine
↓
Correction
↓
Règle préventive
↓
Test / contrôle anti-régression
↓
Capitalisation dans le registre du module
```

Une correction significative ne doit pas être considérée comme terminée tant que
sa cause racine, son test anti-régression et sa capitalisation ne sont pas traités.

Ce fichier est conservé à son emplacement historique pour que les anciennes
références restent valides.
