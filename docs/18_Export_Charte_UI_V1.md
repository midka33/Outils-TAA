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

## Validation dans Revit — clôturée le 2026-10-01

| Test | Vérification | État |
|---|---|---|
| UI-01 | Ouvrir les cinq fenêtres sans erreur XAML, thèmes et pictogrammes visibles. | OK |
| UI-02 | Réduire/agrandir ; vérifier champs, boutons et défilement à 100 %, 125 % et 150 % Windows. | OK |
| UI-03 | Parcourir au clavier avec Tab ; activer boutons et cases ; contrôler focus et états désactivés. | OK |
| UI-04 | Sélection simple/Ctrl/Maj, drag-and-drop et conservation de l'arbre développé. | OK |
| UI-05 | Profils, héritage DCE/Plan/A405 et retour au parent ; contrôler les champs affichés. | OK |
| UI-06 | Aperçu, annulation, PDF/DWG combinés et séparés ; rapport et diagnostic d'erreur copiable. | OK |

Le socle fonctionnel a été validé par l'utilisateur le 2026-09-30 (TEST-44 et profils
P1–P4 inclus). La finition graphique et les tests UI ont été validés par l'utilisateur le 2026-10-01.
Le nettoyage de stage07 reste un travail distinct ; cette refonte ne le réalise pas.

## Compléments après retour utilisateur — 2026-10-01

Les six points de la fenêtre principale sont implémentés : retrait du déplacement
par menu Dossier, suppression multiple de conteneurs, pictogrammes PDF/DWG effectifs,
icône Export du ruban, résumé de périmètre, qualité PDF héritée et persistée.
Le détail fonctionnel est dans `09_Export.md`. Cette seconde passe touche aussi
le modèle de réglages, les profils et la transmission de la qualité au moteur PDF.

Contrôles supplémentaires : héritage/profils/anciens réglages de qualité ; huit
résolutions dans les deux modes PDF ; suppression groupée, annulation, protection
des dossiers et carnets de session ; actualisation des icônes et du résumé sur les
vraies méthodes UI exécutées avec doubles. **173 tests Python réussis hors Revit.**

| Test | Vérification dans Revit | État |
|---|---|---|
| UI-07 | Menu Dossier absent ; déplacement par glisser-déposer disponible. | OK |
| UI-08 | Ctrl/Maj puis Supprimer : plusieurs carnets et dossiers, annulation, dossier non vide, Général, session et navigation clavier. | OK |
| UI-09 | Modifier PDF/DWG au parent puis surcharger/revenir à l'héritage ; icônes des feuilles actualisées sans replier l'arbre. | OK |
| UI-10 | Recharger pyRevit : pictogramme orange du bouton Export en thème clair et sombre. | OK |
| UI-11 | Résumé pour dossier imbriqué, carnet, feuille, formats mixtes et désactivés ; fenêtre réduite. | OK |
| UI-12 | Qualité 144/600 DPI, sauvegarde/réouverture/profil/héritage ; exporter combiné puis séparé. | OK |

Référence packaging : https://docs.pyrevitlabs.io/reference/pyrevit/extensions/
Les captures fournies guident les icônes et le résumé ; le poids estimé et les
champs non disponibles dans le modèle V1 ne sont pas simulés.

## Passe compacte — 2026-10-01

Le suivi courant est dans `19_Export_UI_Compacte_PDF.md` : réglages compacts,
héritage sur une ligne, dialogue PDF, icônes corrigées et 195 tests Python réussis.
Les validations visuelles et fonctionnelles ont été confirmées dans Revit 2025.4 le 2026-10-01.
Les étapes précédentes sont conservées ci-dessus comme historique, sans les
présenter comme des validations graphiques effectuées.

## Clôture de la passe nommage — 2026-10-01

Le sélecteur filtrable des paramètres de feuilles et des **Informations sur le projet**
a été testé dans Revit 2025.4 et confirmé fonctionnel par l'utilisateur.
La branche peut être fusionnée dans `main`.
## Correctif ruban Export — validation ciblée

| Test | Vérification dans Revit 2025.4 | État |
|---|---|---|
| UI-13 | Recharger pyRevit : icône Export visible, aucun texte sous l’icône, panneau « Export » conservé, tooltip fonctionnel, clic ouvrant le module. | À tester |

Le correctif ne renomme ni `Export.pushbutton` ni `Export.panel`. La validation réelle du ruban reste obligatoire avant fusion dans `main`.

