# Outils TAA — Giration des véhicules (prototype de fiabilisation)

**État : expérimental — non validé dans Revit 2025.4**  
**Branche proposée : `refactor/giration-fiabilisation`**  
**Plateforme cible : Revit 2025.4 / pyRevit 5.x / IronPython 2.7**

## Intention produit inchangée

À terme : tracé manuel en continu à la souris type Autodesk Vehicle Tracking,
véhicule choisi par l'utilisateur, respect du braquage, trajectoires de roues,
enveloppes balayées intérieure/extérieure, silhouettes et édition après
sauvegarde, sans Dynamo ni complément C# autonome.

**Attention : le prototype actuel n'est PAS équivalent à Vehicle Tracking.**

## Ce qui est développé dans cette refonte

- Cinématique du véhicule rigide à **2 essieux** selon le modèle bicyclette,
  intégration analytique des arcs à braquage constant, marche avant et marche
  arrière, essais de conformité géométrique hors Revit.
- Origine commune définie sans ambiguïté : milieu du pare-chocs **arrière** ;
  la position de l'essieu arrière est à `rear_overhang` vers l'avant.
- Point de pilotage provisoire : l'utilisateur clique le **centre de l'essieu
  arrière** voulu. Un solveur transforme ce clic en arc tangent lorsque le
  braquage disponible le permet. Les changements de cap sont ainsi contraints.
- WPF de sélection des véhicules, rappel clair du statut non certifié.
- Adaptateur Revit créant des **DetailCurves dans la vue de plan active** après
  validation. Les éléments couvrent la trajectoire de l'essieu arrière,
  les quatre trajectoires de roues, les quatre pistes des coins de carrosserie
  et les silhouettes de début/fin.
- Les traitements de sélection Revit ont lieu **après fermeture de la fenêtre
  modale** pour respecter le contexte API. Aucune API non vérifiée de capture
  continue de souris n'est employée.

## Fonctionnement du prototype

1. Charger l'extension dans un projet **de test** Revit 2025.4.
2. Ouvrir une **vue en plan** ; lancer `Outils TAA > Giration > TracerGiration`.
3. Sélectionner le véhicule et prendre connaissance de l'avertissement.
4. Choisir marche avant ou arrière pour **toute la séquence**.
5. Cliquer sur `Tracer (prototype)`.
6. Cliquer au **milieu de l'arrière de la carrosserie**, puis vers l'avant pour
   indiquer le cap initial.
7. Cliquer successivement les points que doit atteindre **l'essieu arrière**.
   Un arc incompatible avec le rayon de braquage est refusé.
8. Échap termine ; les courbes de détails sont générées dans une transaction.

Un Échap avant le premier segment annule entièrement la commande.

## Limites critiques à lever

- **Pas de suivi continu du curseur** ; prototype de test par clics seulement.
- **Pas d'enveloppe balayée unionnée** : les lignes des coins et les empreintes
  sont une approximation visualisable, **pas** les contours réel externe/interne.
- Pas de transitions réalistes du volant entre deux arcs : le changement
  instantané d'angle est un modèle simplifié.
- Pas de rayon constructeur validé : les valeurs du catalogue précédent n'ont
  pas de pièce documentaire identifiable. Les neuf exemples sont explicitement
  `verified=False`, ne doivent pas être utilisés pour une démonstration
  réglementaire, et la configuration 3-essieux a été retirée du catalogue
  simulable car ce moteur ne modélise que deux essieux.
- Pas de changement de sens en cours de commande, ni Undo interactif, ni
  modification ni persistance des trajets. Les courbes de détail restent
  ordinaires éléments Revit non regroupés.
- Pas de calques graphiques TAA particuliers, ni d'export PDF/DWG testé.
- L'ergonomie et le comportement WPF/API n'ont pas pu être testés en Revit
  depuis l'environnement de développement.

## Architecture

- `OutilsTAA.extension/lib/giration/geometry/vector2d.py` : opérations 2D.
- `.../models/vehicle.py` : fiche véhicule, rayon et validation.
- `.../services/kinematics.py` : intégration analytique, traces et empreintes.
- `.../services/manual_solver.py` : arc tangent calculé à partir d'un clic.
- `.../data/vehicles.py` : exemples **non vérifiés**.
- `.../revit/detail_graphics.py` : dessin Revit en transaction.
- `OutilsTAA.tab/Giration.panel/ui/` : dialogue WPF et chargement du thème.
- `TracerGiration.pushbutton/script.py` : point d'entrée **ASCII** compatible
  avec l'analyseur pyRevit (évite la détection d'encodage précédente).

## Tests & recette

Tests Python hors Revit : `PYTHONPATH=OutilsTAA.extension/lib python -m pytest tests/test_refactor_giration.py tests/test_manual_solver.py -q`.

Pour ne pas perturber les tests des autres modules, créer un environnement
jetable de recette et vérifier le SHA des fichiers avant la copie.

- [x] Tests Python de nouvelle cinématique exécutés hors Revit.
- [x] Contrôle statique `ast.parse` et XML XAML bien formé.
- [ ] Analyse réelle par pyRevit 5.x / IronPython 2.7.
- [ ] Fenêtre chargée avec le thème commun dans Revit 2025.4.
- [ ] Essai plan d'étage, clics, Échap, annulation, Revit transaction.
- [ ] Contrôle des positions et de l'échelle, comparaison à Vehicle Tracking.
- [ ] Test écran 27 pouces et réouverture de projet.
- [ ] Enveloppes réelles, persistance et édition.

## Prochain jalon bloquant

**P0 — pilotage continu et aperçu dynamique** par Revit API : conserver ce
prototype discret comme outil de diagnostic, sans en faire une substitution
silencieuse à l'exigence utilisateur.
