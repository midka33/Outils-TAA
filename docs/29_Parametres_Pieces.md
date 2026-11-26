# Outils TAA — Paramètres des pièces (développement V1)

**État :** bêta WPF/Revit avec deux fenêtres dédiées ; 973 tests automatisés
réussis (87 avertissements), saisie clavier Revit à confirmer et grisage
de sélection toujours ouvert.
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

**Retour de rechargement du 23/11 :** `Commandes.stack` a été ignoré car
`Numeroter` existait déjà dans la session Revit ; les anciens grands boutons
sont restés affichés. Les identifiants internes ont été remplacés par
`TAA_NumeroterPieces` et `TAA_ModifierTextePieces` sans changer les libellés.
Pour évaluer cette correction, fermer **toutes** les fenêtres Revit, rouvrir
Revit puis vérifier le ruban. L'affichage compact n'est pas encore validé.
Voir également BUG-PARAM-003.

## Troisième retour UI — fenêtres séparées (23 novembre 2026)

L'utilisateur revient sur le choix précédent d'une fenêtre commune : **deux
fenêtres WPF distinctes sont désormais demandées et implémentées**, l'une
réservée à Numéroter, l'autre à Modifier le texte. Chaque bouton ouvre directement
sa fenêtre, sans commutateur de mode. Les deux fenêtres conservent les mêmes
services Revit, moteurs purs, aperçu et confirmation transactionnelle.

La colonne des options est davantage compactée : marges verticales de libellés
de 8/3 px, saisies à 26 px, listes à 28 px et commandes à 30 px. Les deux
fichiers XAML sont `ui/numbering_parameters.xaml` et
`ui/text_parameters.xaml`. `room_parameters_window.py` reste le contrôleur
commun et reçoit le mode initial immuable à l'ouverture.

**BUG-PARAM-004 persistant dans la précédente livraison :** la saisie n'a
toujours pas fonctionné sous Revit. Un focus clavier explicite est désormais
demandé au premier rendu WPF et les anciennes préférences vides ne remplacent
plus les valeurs par défaut de numérotation. **Cela reste une hypothèse de
correction, à tester en Revit ; la cause racine exacte n'est pas confirmée.**

## Renommage multiple — sélection puis éditeur en trois colonnes

**Décision utilisateur du 23 novembre 2026 :** pour la commande Modifier le
texte, ouvrir deux fenêtres successives :

1. `ui/rename_selection.xaml` : choisir **Pièces** ou **Familles** ; pour les
   familles, choisir les **paramètres d'instance** ou les **paramètres de type** ;
   sélectionner le périmètre (sélection actuelle, vue active, projet entier),
   cocher les éléments visés puis sélectionner le paramètre texte modifiable.
2. `ui/rename_editor.xaml` : trois colonnes simultanées (**liste des éléments**,
   **opération**, **aperçu avant/après**), avec boutons de validation et
   possibilité de décocher des éléments avant actualisation de l'aperçu.

**Retour de recette du 26/11/2026 :** le renommage fonctionne selon l'utilisateur.
Dans la liste de la deuxième fenêtre, la colonne précédemment nommée
« Élément » présente désormais **la valeur du paramètre de destination choisi
à l'étape 1**, avec son nom en en-tête ; la première colonne de l'aperçu suit
la même convention. Les éléments restent associés en interne à leur `UniqueId`
pour garantir que le changement de présentation ne modifie pas la cible des
transactions. Un paramètre manquant est marqué « (paramètre absent) » ; une
valeur texte vide est affichée « (vide) ». Ce nouveau rendu doit être contrôlé
dans Revit, sans étendre la validation précédente à cette révision.
Contrôles disponibles dans l'environnement courant : **10 contrats statiques
WPF réussis**, compilation Python du contrôleur réussie ; la suite `pytest`
complète n'a pas pu être relancée (module absent). Le dernier résultat de
suite complète avant cette modification reste **976 tests réussis**.

**Retour utilisateur Revit du 23/11 :** la fenêtre **Numéroter les pièces**
est confirmée fonctionnelle ; aucune modification de ce module n'est nécessaire
pour la présente étape.

Le renommage propose désormais **quatre opérations distinctes** :

- **Ajouter** : insertion au début ou à la fin, avec séparateur facultatif et
  option pour éviter un ajout répété ;
- **Supprimer** : suppression exacte au début ou à la fin, avec séparateur ;
- **Remplacer** : remplacement de toutes les occurrences littérales ;
- **Formater** : composition avec les jetons explicites
  `{valeur}`, `{index}` et `{famille}`.

**Amélioration du 26/11 — paramètres disponibles dans Formater :**
la colonne Opération affiche, uniquement en mode **Formater**, une liste
des paramètres **texte présents** sur les éléments sélectionnés, y compris
les paramètres en lecture seule utilisables comme sources. Le bouton
« Insérer dans le format » ajoute un jeton stable, par exemple
`{param_954978}` pour le paramètre Revit d'ID `954978` ; les identifiants
natifs négatifs utilisent `{param_m...}`. Les valeurs de ces jetons sont
lues **individuellement sur chaque élément** lors de la prévisualisation.
Si un paramètre référencé manque sur un élément, le modèle est rejeté avec
un message d'erreur plutôt que d'insérer silencieusement une autre valeur.
Le paramètre de destination reste celui choisi à l'étape 1 ; la liste du
mode Formater ne modifie pas cette destination.
Contrôles hors Revit de cette itération : **11 contrats WPF réussis**,
cas positif et rejets de jetons invalides vérifiés, compilation Python
réussie. Suite `pytest` complète indisponible dans l'environnement courant
(`No module named pytest`) ; aucune nouvelle validation Revit annoncée.

Les autres jetons, conversions et spécificateurs de format sont refusés ;
le résultat vide est ignoré. L'éditeur réutilise
`room_parameters.text_transform_engine` et le nouveau moteur pur
`room_parameters.format_engine`. Les services Revit sont isolés dans
`services/text_rename_service.py` ; toute écriture est effectuée dans une
transaction unique avec vérification des valeurs de départ et rollback.

Suite après séparation des opérations : **976 tests réussis,
87 avertissements** hors Revit. Les quatre modes doivent être vérifiés en WPF.

Les types de familles sont **dédupliqués par UniqueId** lors de la collecte
(plusieurs occurrences ne provoquent pas plusieurs écritures sur le type).
Un avertissement signale qu'une modification de paramètre de type concerne
toutes ses occurrences dans la maquette, même celles hors du périmètre initial.
Les éléments de groupes sont exclus pour la sélection des instances.
Le nom propre de la famille ou du type n'est **pas** directement renommé : la
V1 agit exclusivement sur les **paramètres texte modifiables** disponibles.

**Statut :** implémentation locale, test de contrats et moteurs hors Revit.
Recette Revit et ergonomie WPF encore ouvertes, en particulier focus clavier,
collecte des familles, portée réelle des paramètres de type et annulation.
Suite complète : **975 tests réussis et 87 avertissements** hors Revit.

## Retours UI — deuxième essai Revit du 23 novembre 2026

- **Ruban compact : validé visuellement par l'utilisateur après fermeture et réouverture de Revit.** Le correctif de renommage interne du commit local suivant reste une précaution non nécessaire à cette validation.
- **Champs de saisie :** l'utilisateur ne peut modifier ni les valeurs initiales/pas de numérotation, ni le texte/séparateur. Propriétés WPF explicites d'édition, de focus et de contraste ajoutées ; **cause non confirmée et nouvelle recette Revit impérative** (BUG-PARAM-004).
- **Destination par défaut :** « N° Appartement » sélectionné si le paramètre texte existe et est modifiable ; sinon première option disponible. Ce défaut ne change pas les valeurs des autres paramètres.
- **Modification de texte :** nouvelle opération « Remplacer un texte ». Les deux champs deviennent « Texte à rechercher » et « Remplacer par ». Remplace toutes les occurrences littérales du texte recherché, avec possibilité de remplacer par une chaîne vide tant que le résultat complet n'est pas vide. Contrôle dans l'aperçu avant transaction.
- **Compacité :** champs et listes de gauche ramenés à 28 px, lignes de l'aperçu de droite à 19 px, en-têtes à 24 px.
- **Sélection ordonnée :** les pièces cliquées plusieurs fois restent dédupliquées (comportement existant). L'atténuation graphique/grisage *dans la vue Revit* n'est pas encore implémentée ; il faut définir un mécanisme de surbrillance temporaire compatible Revit et réversible avant écriture.

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
