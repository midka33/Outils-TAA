# Registre des bugs Outils TAA — Index

**Statut :** Référence active de développement et de non-régression  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x

Le registre monolithique a été découpé afin qu'un agent ou développeur ne charge
que les règles correspondant au module sur lequel il travaille.

## Fichiers actifs

- [Export](EXPORT.md) — 52 fiches.
- [Calculs des pièces](CALCULS.md) — 6 fiches.
- [Plans de vente](PLANS_DE_VENTE.md) — 27 fiches.
- [Commun](COMMON.md) — 9 fiches transversales.
- [Tests et livraison](TESTS.md) — 5 fiches.

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

Avant toute modification de code, consulter ce fichier puis le registre du
module concerné. Une correction significative n'est pas terminée tant que son
test anti-régression et sa capitalisation ne sont pas traités.

## Identifiants historiques sans fiche détaillée dans l'ancien registre

- `BUG-COMMON-001`
- `BUG-REVIT-001`
- `BUG-ROOMCALC-001`
- `BUG-TEST-001`
- `BUG-UI-001`

Ces identifiants sont conservés pour la traçabilité. Ne pas leur inventer une
cause ou une correction sans retrouver une source historique explicite.
