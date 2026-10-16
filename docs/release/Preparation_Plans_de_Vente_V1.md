# Plans de vente — préparation de la V1

**Branche de release :** `release/plans-de-vente-v1`  
**Cible :** Autodesk Revit 2025.4 + pyRevit 5.x  
**Build UI :** `stage09-rc17-progress-stages`  
**Date :** 2026-10-16

## Objet

Cette branche est reconstruite depuis la `main` actuelle afin d'éviter de fusionner
directement l'ancienne branche de développement Plans de vente, devenue fortement
divergente.

Le transfert contient uniquement :

- le module Plans de vente final ;
- la bibliothèque `lib/plans_vente` ;
- les tests Plans de vente ;
- la documentation et les références visuelles du module ;
- l'harmonisation des quatre icônes Calculs / Export.

Aucun fichier Python/XAML métier d'Export ou de Calculs n'est remplacé.

## Recette finale Revit

Cette recette vérifie uniquement l'intégration finale sur la branche propre.
Les validations fonctionnelles détaillées ont déjà été réalisées pendant le
développement RC15 à RC17.

### TEST-REL-PDV-01 — ouverture

- Basculer sur `release/plans-de-vente-v1`.
- Faire `git pull`.
- Recharger pyRevit.
- Ouvrir **Plans de vente**.

**Attendu :**
- ouverture sans traceback ;
- aperçu de la feuille modèle disponible ;
- choix du style de ligne des zones principales disponible ;
- bouton de création actif avec un modèle valide.

### TEST-REL-PDV-02 — logement mono-niveau

- Générer un logement mono-niveau avec un modèle à une vue principale.

**Attendu :**
- une feuille créée ;
- vue placée dans la zone explicite du modèle ;
- gabarit et échelle cohérents ;
- étiquettes, cotations, repérage et nomenclatures présents ;
- paramètres cartouche renseignés ;
- fenêtre de progression visible avec plusieurs jalons avant 100 % ;
- aucun échec dans le rapport.

### TEST-REL-PDV-03 — logement multi-niveaux

- Générer un duplex/villa avec un modèle contenant deux vues principales.

**Attendu :**
- une seule feuille ;
- deux vues aux mêmes règles d'échelle ;
- chaque vue centrée dans sa zone explicite ;
- aucune superposition ;
- surfaces habitables et annexes consolidées ;
- étage affiché sous la forme attendue, par exemple `0 / 1` ;
- progression par jalons pendant les deux niveaux ;
- aucun échec dans le rapport.

### TEST-REL-PDV-04 — lot

- Générer plusieurs logements sur un lot représentatif.

**Attendu :**
- progression globale et logement courant visibles ;
- un échec éventuel sur un logement n'interrompt pas les suivants ;
- rapport final cohérent : créés / ignorés / échecs / durée.

### TEST-REL-PDV-05 — non-régression du ruban

- Ouvrir **Calculs des pièces**.
- Ouvrir **Export**.
- Vérifier les trois icônes du ruban.

**Attendu :**
- Calculs et Export s'ouvrent normalement ;
- leur comportement métier reste celui de `main` ;
- seuls les PNG des icônes Calculs / Export ont été harmonisés ;
- les trois boutons utilisent la même palette orange.

## Critères de release

La branche peut être fusionnée dans `main` lorsque :

- la CI Plans de vente de la PR est verte ;
- TEST-REL-PDV-01 à 05 sont validés dans Revit 2025.4 ;
- le diff avec `main` ne contient aucun code métier Export / Calculs ;
- aucun bug bloquant n'est identifié.

## Hors périmètre de cette V1

- mise à jour automatique d'un plan de vente déjà généré ;
- optimisation supplémentaire des performances sur très grands lots ;
- plus de deux vues principales sur une même feuille.
