# Tutoriel — Export

**Release 1.0.3 — Revit 2025.4 / pyRevit 5.x**

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
5. Réorganiser les feuilles dans l'ordre souhaité.
6. Les carnets persistants restent disponibles lors des prochaines utilisations sur le projet.

## Réglages PDF
- **Publier** active ou désactive le PDF.
- **Combiné** produit un PDF global pour le carnet.
- **Séparé** produit un PDF par mise en page.
- La qualité PDF est réglable directement dans Outils TAA.

Pour un PDF combiné, le nom est désormais résolu au niveau du **carnet** : les variables propres à une feuille ne reprennent plus automatiquement la première mise en page.

## Réglages DWG
La configuration DWG native de Revit reste la source principale des réglages.

Dans Outils TAA :
- choisir la **Configuration DWG Revit** ;
- utiliser l'engrenage pour accéder aux réglages DWG natifs de Revit ;
- **Fusionner les vues et les liens dans le DWG** pilote le comportement des XRefs de vues/liens ;
- **Forcer les couleurs vraies** conserve la surcharge TAA historique si nécessaire.

Le choix technique **Par feuille / Lot Revit** n'est plus affiché.

Outils TAA choisit automatiquement la stratégie :
- une feuille : appel simple ;
- plusieurs feuilles : lot natif Revit pour de meilleures performances.

Le résultat métier reste **un DWG par feuille**.

Après un export en lot, Outils TAA rapproche les DWG natifs avec les feuilles, puis les renomme selon le modèle TAA. Les suffixes natifs Revit tels que « Feuille » ne doivent donc plus apparaître dans les noms finaux.

## Dossiers de sortie
Si **Créer un dossier au nom du carnet** est coché :

```text
Destination/
└── Nom du carnet/
    ├── PDF/
    │   └── fichiers PDF
    └── DWG/
        ├── fichiers DWG
        └── fichiers auxiliaires éventuels
```

Cette structure est indépendante du mode PDF et de la stratégie technique DWG.

Les images raster, XRefs ou autres fichiers auxiliaires que Revit ne peut pas incorporer peuvent encore être produits ; ils restent regroupés dans le dossier **DWG**.

## Prévisualiser et publier
1. Ouvrir **Aperçu**.
2. Vérifier les carnets, feuilles, noms de fichiers et destinations.
3. Vérifier les collisions éventuelles.
4. Confirmer la publication.
5. La fenêtre de progression s'ouvre avant les traitements longs.
6. À la fin, la fenêtre se ferme puis le rapport final s'ouvre.

## Progression
La progression globale reste comprise entre **0 et 100 %**.

Pendant un appel natif Revit :
- si Revit fournit une progression réelle, la barre l'utilise ;
- sinon elle reste temporairement stable au lieu de simuler une fausse progression.

Pendant les traitements contrôlés par Outils TAA, par exemple le renommage/livraison des DWG, l'interface peut afficher :

```text
Mises en page :
3 / 5
```

La fenêtre de progression conserve une taille fixe pendant toute l'opération.

## Bonnes pratiques
- Enregistrer/synchroniser le projet avant une publication importante.
- Vérifier l'aperçu avant de publier.
- Utiliser un carnet persistant et un profil pour les diffusions répétitives.
- Si des PNG/JPG apparaissent avec les DWG, vérifier s'ils proviennent d'images raster présentes dans Revit.
- En cas d'échec, consulter le rapport final : il reste la source de vérité sur les fichiers réellement produits.
