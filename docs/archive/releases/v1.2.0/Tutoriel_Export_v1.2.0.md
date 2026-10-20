# Tutoriel — Export

**Release 1.2.0 — Revit 2025.4 / pyRevit 5.x**

## Objectif
L'outil **Export** organise et publie les feuilles Revit en PDF et/ou DWG.

## Organisation et sélection

Les dossiers et les anciens carnets ont la même présentation dans l’arborescence.
Un dossier peut contenir des mises en page et des sous-dossiers.

1. Ouvrir **Outils TAA > Export**.
2. Créer ou sélectionner un dossier, puis ajouter les feuilles avec **Ajouter / gérer…**.
3. Réorganiser les éléments par glisser-déposer : haut de ligne pour insérer avant,
   centre pour déposer dedans, bas pour insérer après. Les dossiers ouverts et
   fermés sont acceptés ; le survol ouvre un dossier fermé.
4. Utiliser Ctrl/Maj pour sélectionner plusieurs dossiers ou mises en page.
5. Vérifier le périmètre dans l’aperçu avant de publier la sélection.

La hiérarchie et les réglages des dossiers persistants sont conservés à la
réouverture. Les anciennes configurations sont migrées automatiquement.
Les mises en page peuvent être déplacées vers un dossier nouvellement créé ;
les dossiers source devenus vides restent présents.

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

## Nommage PDF et DWG

Le champ **Nommage DWG** reste visible. Par défaut, il suit le nommage PDF et
reste grisé. Cocher **Nommage DWG indépendant du PDF** pour saisir une règle
spécifique. En PDF combiné, le nommage DWG devient automatiquement indépendant.
Les deux règles sont héritées et enregistrées avec les paramètres du dossier.
Contrôler les noms résolus dans **Aperçu** avant de publier.

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
