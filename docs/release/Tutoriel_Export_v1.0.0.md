# Tutoriel — Export

**Release 1.0.0 — Revit 2025.4 / pyRevit 5.x**

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
4. Définir le modèle de nommage. Les modèles peuvent exploiter les paramètres Revit disponibles.
5. Vérifier les réglages PDF/DWG.
6. Les réglages peuvent être hérités suivant la hiérarchie **Profil → Dossier → Carnet** ; une surcharge au niveau inférieur remplace la valeur héritée.

## Prévisualiser et publier
1. Ouvrir la prévisualisation.
2. Vérifier les carnets et feuilles concernés.
3. Vérifier les noms de fichiers.
4. Vérifier les destinations.
5. Traiter les éventuelles collisions de noms.
6. Lancer la publication.
7. Consulter le rapport final pour contrôler les réussites et erreurs.

## Bonnes pratiques
- Enregistrer/synchroniser le projet avant une publication importante.
- Vérifier la prévisualisation avant de lancer l'export.
- Utiliser un carnet persistant et un profil pour les diffusions répétitives.
- En cas d'échec, consulter d'abord le rapport de publication.
