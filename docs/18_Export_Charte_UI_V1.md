# Export V1 — Application de la charte TAA

## Périmètre réalisé — 2026-10-01

Références : `04_UI_Guidelines.md`, `assets/ui/UI_Export_Reference.jpg` et
`assets/ui/UI_Design_System_TAA.jpg`. Les maquettes donnent la direction graphique ;
les commandes présentées restent celles du périmètre V1 validé.

Les cinq fenêtres Export sont raccordées au même thème : publication principale,
ajout des carnets, consultation des feuilles, aperçu et rapport.

- Segoe UI, titres sobres et textes secondaires distincts.
- Fonds neutres, cartes blanches, bordures fines et angles de 4–5 px.
- Accent orange pastel `#FD8B5A`, orange de marque réservé au repère TAA.
- Boutons principaux identifiables ; états survol, appui, focus et désactivation.
- Texte sombre sur les boutons pastel pour conserver une bonne lisibilité.
- Cases et boutons radio avec indicateurs orange, sélection de lignes pêche et texte sombre.
- Pictogrammes vectoriels dossier/carnet/feuille dans l'arbre.
- Tableaux homogènes, lignes alternées, infobulles sur le contenu des cellules.
- Champs de destination et nommage extensibles ; insertion de variables sur une seconde ligne.
- Origine des réglages au-dessus du bouton de retour à l'héritage, sans comprimer le texte.
- Diagnostics du rapport conservés, sélectionnables et défilants.

Le thème est centralisé dans `OutilsTAA.extension/resources/ui/Theme.xaml`.
`services/taa_ui_theme.py` le charge par chemin absolu après le chargement de chaque
fenêtre, avant son affichage. Les ressources différées du XAML et les styles implicites
utilisent alors ce dictionnaire. Les couleurs du glisser-déposer proviennent du même thème.
Aucun changement des moteurs PDF/DWG, de l'héritage ou de la persistance métier.

## Vérifications réalisées

- 149 tests Python réussis hors Revit.
- XML des cinq fenêtres et du thème analysé ; ressources référencées présentes.
- Noms des contrôles, événements XAML et bindings comparés à la version fonctionnelle : conservés.
- Contrat du chargeur testé avec des doubles .NET : chemin absolu du thème et application à la fenêtre.
- Rapport d'erreur copiable et sélectionnable toujours couvert par les tests.

Ces contrôles ne chargent pas WPF et ne prouvent pas le rendu réel. L'environnement
Linux utilisé ne permet ni d'exécuter Revit ni de produire une capture WPF authentique.

## Validation dans Revit — à faire avant fusion

| Test | Vérification | État |
|---|---|---|
| UI-01 | Ouvrir les cinq fenêtres sans erreur XAML, thèmes et pictogrammes visibles. | À tester |
| UI-02 | Réduire/agrandir ; vérifier champs, boutons et défilement à 100 %, 125 % et 150 % Windows. | À tester |
| UI-03 | Parcourir au clavier avec Tab ; activer boutons et cases ; contrôler focus et états désactivés. | À tester |
| UI-04 | Sélection simple/Ctrl/Maj, drag-and-drop et conservation de l'arbre développé. | À tester |
| UI-05 | Profils, héritage DCE/Plan/A405 et retour au parent ; contrôler les champs affichés. | À tester |
| UI-06 | Aperçu, annulation, PDF/DWG combinés et séparés ; rapport et diagnostic d'erreur copiable. | À tester |

Le socle fonctionnel a été validé par l'utilisateur le 2026-09-30 (TEST-44 et profils
P1–P4 inclus). La V1 reste en finition graphique jusqu'à validation de ces tests UI.
Le nettoyage de stage07 reste un travail distinct ; cette refonte ne le réalise pas.
