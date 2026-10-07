# Tutoriel — Export

**Release 1.0.2 — Revit 2025.4 / pyRevit 5.x**

## Objectif
L'outil **Export** organise et publie les feuilles Revit en PDF et/ou DWG.

## Principe
La publication suit la hiérarchie **Dossier → Carnet → Mise en page**.

- **Dossier** : niveau d'organisation pouvant contenir des carnets et des sous-dossiers.
- **Carnet** : ensemble ordonné de mises en page.
- **Mise en page** : feuille Revit incluse dans un carnet.
- **Profil** : ensemble de réglages de publication réutilisables.

## Préparer un carnet
1. Ouvrir **Outils TAA > Export**.
2. Créer ou sélectionner le dossier de publication.
3. Créer un carnet et lui donner un nom explicite.
4. Ajouter les feuilles Revit.
5. Réorganiser les feuilles dans l'ordre souhaité. La multi-sélection et le glisser-déposer permettent de déplacer plusieurs éléments.
6. Les carnets persistants restent disponibles lors des prochaines utilisations sur le projet.

## Régler la publication
1. Choisir les sorties : **PDF**, **DWG**, ou les deux.
2. Choisir le mode de sortie selon le besoin.
3. Définir le dossier de destination.
4. Définir le modèle de nommage.
5. Vérifier les réglages PDF/DWG.
6. Les réglages peuvent être hérités suivant la hiérarchie **Profil → Dossier → Carnet**.

## Prévisualiser et publier
1. Ouvrir la prévisualisation.
2. Vérifier les carnets et feuilles concernés.
3. Vérifier les noms de fichiers et les destinations.
4. Traiter les éventuelles collisions de noms.
5. Confirmer la publication.
6. Une fenêtre **Export PDF en cours** s'ouvre avec une progression globale de **0 à 100 %**.
7. Le carnet courant, l'étape et le nombre d'unités traitées sont affichés.
8. Le pourcentage peut rester temporairement fixe pendant un appel natif Revit long : c'est volontaire afin de ne pas simuler une fausse progression.
9. À la fin, la fenêtre de progression se ferme puis le rapport final s'ouvre.

## Progression — nouveauté v1.0.2
La progression représente les opérations réellement terminées sur l'ensemble de la publication.

Elle ne redémarre pas à zéro à chaque carnet.

L'outil n'invente pas une progression feuille par feuille lorsque Revit traite plusieurs feuilles dans un seul appel natif.

## Bonnes pratiques
- Enregistrer/synchroniser le projet avant une publication importante.
- Vérifier la prévisualisation avant de lancer l'export.
- Utiliser un carnet persistant et un profil pour les diffusions répétitives.
- Pendant un appel Revit long, attendre le retour de l'API même si le pourcentage reste momentanément stable.
- En cas d'échec, consulter le rapport final.
