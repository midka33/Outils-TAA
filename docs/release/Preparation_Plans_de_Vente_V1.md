# Plans de vente — préparation de la V1

**Branche de release :** `release/plans-de-vente-v1`  
**Cible :** Autodesk Revit 2025.4 + pyRevit 5.x  
**Build UI :** `stage09-rc17-progress-stages`  
**Date :** 2026-10-16
**Version produit :** v1.2.0 — ajout compatible après v1.1.0 (MINOR SemVer).
**Statut :** CI PR validée, recette finale Revit validée, V1 prête à livrer.

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

## CI hors Revit

Validation automatique sur la PR #26 :

- Plans de vente : **259 tests réussis** ;
- Calculs des pièces : **succès** ;
- Export : **succès** ;
- contrat ruban Export : **succès**.

Aucune modification de code métier Export / Calculs n'est présente dans le diff.

## Validation finale confirmée

Le 16 octobre 2026, l’utilisateur a confirmé la réussite des cinq scénarios
TEST-REL-PDV-01 à 05 sur la branche propre, ainsi que la fenêtre de progression
et les nouvelles icônes. Cette validation réelle vient de ses essais dans Revit
2025.4 ; l’agent ne dispose pas de Revit et ne revendique pas leur exécution.

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

## Intégration et livraison

La PR #26 est la seule branche à fusionner. L’ancienne branche Stage09 n’est pas
fusionnée. La base contrôlée est `09dd1fd07a44ef387f33e72f65ddb69b493f11f8`.
La tête initiale de PR `adff633e30e8a7a436e55d4d164c3f0efa76eba2` contient cette
base sans retard et ses quatre contrôles sont réussis.

Les workflows Plans de vente, Calculs et ruban Export sont également déclenchés
sur `main`, afin de vérifier le commit réellement livré. Le nouveau workflow
`publish-v1.2.0.yml` reprend le ZIP + CMD utilisateur de v1.0.3 et conserve le
script d’installation, avec uniquement la substitution de version/URL.
Il inclut désormais les trois modules et retire tests, caches et temporaires
du ZIP distribué. Le package est construit et contrôlé sur la PR avant fusion.

Après fusion, la publication est automatique uniquement si les quatre workflows
sur le SHA exact de `main` sont réussis, que `main` n’a pas avancé et que le tag
`v1.2.0` est absent. Une ancienne release n’est jamais écrasée. Un échec stoppe
la livraison. La publication effective est attestée par la release GitHub et
le résultat du workflow, et non par la seule présence de ces notes préparées.

Livrables : ZIP contenant `OutilsTAA.extension`, trois tutoriels, `LICENSE` et
`LISEZ_MOI.txt` ; installateur CMD ; tutoriels séparés et sommes SHA-256.
Les archives source automatiques GitHub restent distinctes du ZIP utilisateur.
