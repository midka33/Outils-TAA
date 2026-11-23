# Outils TAA — Paramètres des pièces (développement V1)

**État :** bêta WPF/Revit implémentée et remise en conformité statique ; recette réelle en attente.
**Cible :** Revit 2025.4, pyRevit 5.x (IronPython), WPF.
**Branche :** `feature/room-parameter-tools`.

## Décision utilisateur — 23 novembre 2026

Créer un panneau **Paramètres** autonome dans `OutilsTAA.tab`, avec deux boutons :

- **Numéroter** : séquence d'un paramètre texte, ordre des clics.
- **Modifier texte** : ajout/retrait exact d'un préfixe ou suffixe.

Le panneau **Calculs** et la commande validée **Calculs des pièces** ne changent pas.
Deux fenêtres WPF autonomes utiliseront un service de prévisualisation commun.

## Travail réalisé — étape « moteur »

Les fichiers purs `lib/room_parameters/` ne dépendent ni de Revit, ni de pyRevit,
ni de WPF :

| Module | Contrat |
| --- | --- |
| `numbering_engine` | Découpe le **dernier** bloc du type demandé, génère des valeurs avec pas non nul ; ignore les clics répétés. Bloc chiffres ASCII ou lettres ASCII homogènes uniquement ; texte fixe Unicode préservé. |
| `text_transform_engine` | Ajout/suppression au début/fin, séparateur littéral, option ajout unique ; chaînes vides et suppressions produisant une chaîne vide ignorées. |
| `duplicate_checker` | Détecte les conflits entre nouvelles valeurs et valeurs non remplacées du périmètre transmis ; autorise les valeurs partagées sur demande. |

Le paramètre natif `ROOM_NUMBER` reste **protégé pour la commande Numéroter**
dans le scénario V1 envisagé ; décision définitive à confirmer avant interface.
Pas de garantie d'unicité par défaut pour les identifiants d'appartement :
les pièces d'un même logement peuvent partager leur identifiant. Le contrôle
de collision doit être une décision explicite au niveau du contrôleur.

## Intégration Revit — première implémentation

**Choix utilisateur du 23/11 : proposition 3**, avec **une seule interface** :
configuration à gauche, aperçu à droite, pas d'assistant ni de fenêtre de
confirmation supplémentaire. Deux boutons distincts du panneau Paramètres
ouvrent le même XAML, prépositionné sur Numéroter ou Modifier texte.

Le premier raccordement comprend :

- boutons `Numeroter.pushbutton` et `ModifierTexte.pushbutton` ;
- interface `Parametres.panel/ui/room_parameters.xaml` et contrôleur associé ;
- sélection ordonnée par clic pour numéroter (fenêtre temporairement cachée
  pendant l'interaction Revit), collecte par sélection/vue/projet pour texte ;
- tableau avant/après avec sélection individuelle et doublons signalés ;
- case de confirmation dans la fenêtre, signature des réglages vérifiée ;
- transaction unique avec vérification des valeurs de départ et rollback ;
- exclusion des groupes et protection du numéro natif pour les deux commandes.

**Limite importante :** aucune exécution WPF ni sélection par clic n'a encore
été testée dans Revit. Le schéma `Hide()` → sélection → `Show()` sur une fenêtre
modale requiert une recette sur copie de RVT avant usage en production.

## Retour Revit initial — 23 novembre 2026

L'utilisateur confirme que les deux boutons de la bêta publiée échouent au
chargement sur `ImportError: No module named Data` dans IronPython. Correctif
proposé : `clr.AddReference("System.Data")` avant l'import `DataTable` ;
aucun succès Revit encore confirmé pour cette révision.

Sur demande de présentation, les commandes passent dans
`Parametres.panel/Commandes.stack/` (deux petits boutons superposés avec
icônes et libellés d'une ligne). Les chemins calculés dans les points d'entrée
sont adaptés au niveau de dossier supplémentaire. Référence : documentation
pyRevit sur les bundles `.stack`.

Voir `docs/bugs/PARAMETRES.md` pour BUG-PARAM-001 et BUG-PARAM-002.

Contrôle après correctifs : **971 tests automatisés réussis hors Revit**, dont
les tests statiques du `.stack`, du chargement de `System.Data` et des chemins
des deux points d'entrée. **Validation réelle Revit toujours en attente.**
**Mise en conformité du 23/11 :** services Revit extraits dans
`services/room_parameter_edit_service.py` (collecte, paramétrage, préparation,
collisions, écriture) ; code-behind WPF limité au parcours et à l'affichage.
La fenêtre charge `resources/ui/taa_theme.xaml` par le service commun ; le
bouton principal utilise `TAAPrimaryButton`, les boutons secondaires le style
commun. Icônes dédiées SVG/PNG ajoutées aux deux boutons.

Les préférences utilisateur non spécifiques au projet sont mémorisées via
`JsonSettingsStore` dans le dossier applicatif local ; aucun identifiant de
paramètre n'est réutilisé entre deux projets. Journalisation via
`common.logger`. Le compte-rendu de la dernière écriture (modifiées,
exclues, ignorées, paramètre) est présenté dans la même fenêtre.
Les collisions sont recalculées à partir des seules lignes cochées : une
ligne exclue reste prise en compte comme valeur existante.

Limites toujours ouvertes :

- **aucun test Revit** du `Hide()`/`Show()` modal et des handlers WPF ;
- pas de test d'interface à l'échelle 100/125/150 % sur écran 27 pouces ;
- progression visuelle des longues opérations à ajouter si la recette montre
  un temps de traitement perceptible ;
- logs communs branchés mais configuration de sortie persistante non vérifiée ;
- rapport synthétique intégré, pas encore d'export de rapport ;
- scénario réel de travail collaboratif, verrouillage et groupes à tester.

## Contrôles de raccordement et étapes restantes

1. Compléter les icônes claires/sombres et la charte WPF.
2. Vérifier la sélection ordonnée, vue active et projet entier dans Revit.
   Ne pas modifier `Calculs.panel/services/room_collector_service.py` : son
   contrat validé porte exclusivement sur toutes les pièces du projet.
3. Réutiliser `RoomParameterService` / `RoomParameterDescriptor` pour les identités
   techniques, sans choisir silencieusement par nom lorsqu'il est ambigu.
4. Préparer les modifications sur les `UniqueId`, confirmer les valeurs AVANT/APRÈS,
   exclure les valeurs read-only et les pièces liées. Pièces groupées exclues
   tant que la gestion des groupes n'a pas été explicitement validée.
5. Vérifier les anciennes valeurs puis écrire dans une **transaction unique** ;
   rollback complet en cas d'échec. Ne pas supprimer les avertissements Revit.
6. Ajouter un rapport et une persistance isolée dans `common.settings`.
7. Tester dans Revit 2025.4 / pyRevit 5.x, puis tester les non-régressions Calculs.

## Historique des propositions d'interface

Trois propositions ont été présentées ; l'utilisateur a choisi la troisième,
avec une fenêtre unique pour toutes les étapes :

1. **Assistant guidé** : paramètre → opération → sélection → aperçu → validation.
2. **Fenêtre compacte** : réglages et tableau AVANT/APRÈS visibles ensemble.
3. **Fenêtre à deux panneaux** : configuration à gauche, aperçu à droite ;
   sélection ordonnée via retour explicite dans Revit.

Décisions conservatoires provisoires : numéro natif protégé pour les deux
commandes, groupes exclus, texte : sélection/vue/projet ; numérotation : clics.

## Statut des validations

- Moteur métier : implémenté ; tests dans `tests/test_room_parameter_engines.py`.
- Commandes pyRevit et WPF : **première implémentation, non validée dans Revit**.
- Services Revit : adaptateur contenu dans le contrôleur de fenêtre, à séparer
  après validation du parcours réel.
- Tests automatisés ciblés : **20 réussis** (`python -m pytest
  tests/test_room_parameter_engines.py -q`, 23/11/2026, hors Revit).
- Suite complète de non-régression : **965 réussis**, 87 avertissements
  (dépréciations de dépendances et `datetime.utcnow` existant),
  `python -m pytest -q` le 23/11/2026.
- Après raccordement des deux boutons et du XAML commun : **968 réussis**,
  87 avertissements non bloquants (`python -m pytest -q`, 23/11/2026).
  Le test d'ordre du ruban a été actualisé pour déclarer le panneau Parametres.
- Mise en conformité statique : **969 réussis**, 87 avertissements ;
  le test WPF vérifie le thème commun et la séparation du service d'écriture.
- Tests dans Revit : **non exécutés** ; aucune validation Revit revendiquée.
- `main` et modules validés : **non modifiés**.
