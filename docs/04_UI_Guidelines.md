# Outils TAA – Developer Handbook

## Chapitre 04 — UI Guidelines

**Version :** 1.0  
**Statut :** Référence  
**Cible :** Revit 2025.4 / pyRevit 5.x  
**Interface :** WPF  
**Langue :** Français  
**Année :** 2026  

---

# 1. Objectif du document

Ce document définit les règles de conception des interfaces utilisateur des outils **Outils TAA**.

L’objectif est de garantir que tous les outils développés dans la suite possèdent :

- une identité visuelle commune ;
- une interface simple à comprendre ;
- des comportements cohérents ;
- une bonne lisibilité ;
- une hiérarchie visuelle claire ;
- une utilisation adaptée au travail quotidien des architectes et BIM managers ;
- une intégration naturelle dans l’environnement Autodesk Revit.

Les outils Outils TAA doivent donner l’impression d’appartenir à une seule application, même lorsqu’ils ont été développés à des moments différents ou par des développeurs différents.

---

# 2. Principes fondamentaux

Toute interface Outils TAA doit respecter les principes suivants :

> **Simple — Claire — Rapide — Cohérente — Prévisible**

Une interface ne doit pas chercher à impressionner visuellement.

Elle doit avant tout permettre à l'utilisateur d'accomplir rapidement une tâche.

La priorité est toujours donnée à :

1. la compréhension ;
2. la lisibilité ;
3. l'efficacité ;
4. la réduction du nombre d'actions ;
5. la cohérence entre les outils.

---

# 3. Identité visuelle Outils TAA

L'identité graphique des outils repose sur une interface majoritairement neutre avec l'utilisation ponctuelle de la couleur de l'agence.

La couleur principale de l'agence est :

```text
RGB : 250, 100, 31
HEX : #FA641F
```

Cette couleur constitue la couleur d'accent principale du design system Outils TAA.

Nom interne recommandé :

```text
TAA Orange
```

---

# 4. Couleur principale

## 4.1 TAA Orange

```text
Nom : TAA Orange
RGB : 250 / 100 / 31
HEX : #FA641F
```

Cette couleur doit permettre d'identifier immédiatement les actions importantes et les éléments appartenant à l'identité Outils TAA.

Elle peut notamment être utilisée pour :

- les boutons d'action principale ;
- les indicateurs de sélection ;
- les éléments actifs ;
- certaines icônes ;
- les barres de progression ;
- les éléments graphiques d'identité ;
- les accents visuels ;
- les liens ou commandes interactives.

---

# 5. Ne pas surutiliser l'orange

La couleur TAA Orange ne doit pas devenir la couleur dominante de toute l'interface.

Une fenêtre entièrement orange serait :

- fatigante visuellement ;
- difficile à lire ;
- peu adaptée à une utilisation professionnelle prolongée ;
- moins efficace pour identifier les actions réellement importantes.

L'orange doit être utilisé comme une **couleur d'accent**.

Principe recommandé :

```text
80 à 90 % de couleurs neutres
10 à 20 % maximum de couleur d'accent
```

---

# 6. Palette de couleurs recommandée

La palette Outils TAA doit rester volontairement réduite.

## Couleur d'accent principale

```text
TAA Orange
#FA641F
RGB(250,100,31)
```

## Fond principal clair

```text
#F7F7F7
```

ou :

```text
#FFFFFF
```

## Fond secondaire

```text
#EFEFEF
```

## Bordures

```text
#D9D9D9
```

## Texte principal

```text
#252525
```

## Texte secondaire

```text
#666666
```

## Texte désactivé

```text
#A0A0A0
```

---

# 7. Couleurs fonctionnelles

Certaines couleurs peuvent être utilisées indépendamment de l'identité TAA pour transmettre une information fonctionnelle.

## Succès

```text
Vert
```

Utilisation :

- opération terminée ;
- validation réussie ;
- données conformes.

---

## Avertissement

```text
Orange / jaune
```

Lorsque l'orange TAA est déjà utilisé comme couleur d'identité, le contraste entre l'identité et les avertissements doit rester suffisamment clair.

Les avertissements peuvent utiliser une variante plus jaune ou une icône spécifique.

---

## Erreur

```text
Rouge
```

Utilisation :

- opération impossible ;
- donnée incorrecte ;
- erreur Revit ;
- paramètre manquant ;
- résultat bloquant.

---

## Information

```text
Bleu
```

Utilisation :

- information complémentaire ;
- aide contextuelle ;
- message non bloquant.

---

# 8. Hiérarchie visuelle

L'utilisateur doit comprendre immédiatement :

- où il se trouve ;
- ce qu'il doit renseigner ;
- quelle est l'action principale ;
- quelles sont les actions secondaires ;
- si une erreur empêche l'exécution.

Chaque fenêtre doit donc posséder une hiérarchie visuelle claire.

Exemple :

```text
Titre

Description courte

Section 1
[ paramètres ]

Section 2
[ paramètres ]

--------------------------------

[ Annuler ]          [ Lancer ]
```

---

# 9. Structure générale d'une fenêtre

Une fenêtre Outils TAA devrait idéalement être organisée en cinq zones.

```text
┌──────────────────────────────────────┐
│ TITRE                                │
│ Description courte                   │
├──────────────────────────────────────┤
│                                      │
│ PARAMÈTRES PRINCIPAUX                │
│                                      │
│ OPTIONS                              │
│                                      │
│ RÉSULTATS / INFORMATIONS             │
│                                      │
├──────────────────────────────────────┤
│ Annuler                  Action       │
└──────────────────────────────────────┘
```

---

# 10. Titre de fenêtre

Le titre doit être :

- court ;
- explicite ;
- cohérent avec le nom de l'outil.

Exemples :

```text
PublisherAI
```

```text
RoomCalculator
```

```text
Contrôle des pièces
```

Éviter :

```text
Outil permettant de calculer automatiquement les valeurs des pièces
```

---

# 11. Description de l'outil

Sous le titre, une phrase courte peut expliquer la fonction de l'outil.

Exemple :

```text
Calcule une valeur à partir des paramètres des pièces sélectionnées.
```

Cette description ne doit généralement pas dépasser deux lignes.

---

# 12. Titres de sections

Les paramètres doivent être regroupés par fonction.

Exemple :

```text
Source

Paramètre à analyser
[ Surface ▼ ]

Destination

Paramètre à renseigner
[ Surface calculée ▼ ]
```

Éviter de placer tous les contrôles dans une même zone sans organisation.

---

# 13. Séparateurs

Les séparateurs doivent être utilisés avec modération.

Préférer :

- l'espacement ;
- les titres de section ;
- les groupes visuels.

aux successions de bordures.

Une interface avec trop de cadres devient visuellement lourde.

---

# 14. Espacement

Les marges et espacements doivent être cohérents.

Valeurs recommandées :

```text
4 px   → micro-espacement
8 px   → espacement standard
12 px  → espacement intermédiaire
16 px  → espacement entre groupes
24 px  → séparation importante
32 px  → grandes sections
```

Les valeurs multiples de **4 px** doivent être privilégiées.

---

# 15. Marges générales

Une fenêtre doit conserver une marge intérieure suffisante.

Recommandation :

```text
Padding fenêtre : 16 à 24 px
```

Éviter qu'un bouton ou un texte soit collé au bord de la fenêtre.

---

# 16. Alignement

Les éléments doivent suivre des axes d'alignement clairs.

Privilégier :

- les alignements à gauche ;
- les colonnes régulières ;
- les largeurs cohérentes.

Exemple :

```text
Paramètre source      [ Surface          ▼ ]
Paramètre cible       [ Surface calculée ▼ ]
Méthode               [ Somme            ▼ ]
```

---

# 17. Largeur des libellés

Lorsque plusieurs champs sont affichés verticalement, conserver une largeur homogène pour les libellés.

Cela améliore fortement la lisibilité.

---

# 18. Bouton principal

Chaque fenêtre doit idéalement posséder **une seule action principale**.

Exemples :

```text
Publier
```

```text
Calculer
```

```text
Analyser
```

```text
Exporter
```

```text
Appliquer
```

Le bouton principal utilise la couleur :

```text
#FA641F
```

---

# 19. Texte du bouton principal

Le texte placé sur un bouton TAA Orange doit présenter un contraste suffisant.

Couleur recommandée :

```text
#FFFFFF
```

Exemple :

```text
┌───────────────────┐
│     PUBLIER       │
└───────────────────┘
```

Fond :

```text
#FA641F
```

Texte :

```text
#FFFFFF
```

---

# 20. Bouton secondaire

Les actions secondaires doivent rester visuellement discrètes.

Exemples :

```text
Annuler
```

```text
Fermer
```

```text
Réinitialiser
```

```text
Parcourir
```

Style recommandé :

```text
Fond : transparent ou gris très clair
Texte : gris foncé
Bordure : gris
```

---

# 21. Hiérarchie des boutons

Ordre recommandé :

```text
[ Annuler ]                  [ Action principale ]
```

L'action principale est placée à droite.

Cette disposition doit être conservée autant que possible dans toute la suite Outils TAA.

---

# 22. Nombre de boutons

Éviter d'afficher trop de boutons simultanément.

Lorsque plus de quatre ou cinq actions sont disponibles, envisager :

- un menu ;
- une liste d'actions ;
- un bouton contextuel ;
- des sections ;
- des onglets.

---

# 23. Boutons destructifs

Une action supprimant ou modifiant fortement des données ne doit pas utiliser la même apparence qu'une action normale.

Exemples :

```text
Supprimer
```

```text
Écraser
```

```text
Réinitialiser les données
```

Une couleur rouge ou une confirmation explicite peut être utilisée.

---

# 24. États des boutons

Un bouton doit posséder plusieurs états graphiques.

```text
Normal
Hover
Pressed
Disabled
Focused
```

Le changement d'état doit rester subtil.

---

# 25. État Hover du bouton principal

Pour le bouton TAA Orange, l'état Hover peut utiliser une variante légèrement plus sombre.

Exemple recommandé :

```text
Normal : #FA641F
Hover  : #E85819
Pressed: #D84F12
```

Ces valeurs peuvent être adaptées dans le fichier de ressources central du thème.

---

# 26. État Disabled

Un bouton indisponible ne doit pas sembler cliquable.

Exemple :

```text
Fond : #D8D8D8
Texte : #8A8A8A
```

Le bouton principal ne doit pas rester orange lorsqu'il est désactivé.

---

# 27. Champs texte

Les champs texte doivent être simples et lisibles.

Recommandation :

```text
Hauteur : 28 à 32 px
```

Ils doivent afficher clairement :

- la valeur ;
- le focus ;
- l'état désactivé ;
- l'état d'erreur.

---

# 28. Focus

Lorsqu'un champ possède le focus, une bordure utilisant TAA Orange peut être utilisée.

Exemple :

```text
BorderBrush = #FA641F
```

Cela renforce l'identité graphique sans surcharger l'interface.

---

# 29. ComboBox

Les listes déroulantes sont particulièrement adaptées aux paramètres Revit.

Exemples :

```text
Paramètre source
[ Surface ▼ ]
```

```text
Catégorie
[ Pièces ▼ ]
```

La largeur doit permettre de lire les valeurs les plus fréquentes sans troncature excessive.

---

# 30. Valeur par défaut

Lorsque cela est possible, les interfaces doivent proposer une valeur par défaut logique.

L'objectif est de réduire le nombre d'actions nécessaires avant le lancement de l'outil.

---

# 31. CheckBox

Les cases à cocher sont adaptées aux options binaires.

Exemple :

```text
☑ Inclure les feuilles masquées
```

Les formulations négatives doivent être évitées.

Préférer :

```text
☑ Inclure les feuilles masquées
```

à :

```text
☑ Ne pas exclure les feuilles masquées
```

---

# 32. RadioButton

Utiliser les boutons radio lorsqu'une seule option peut être choisie parmi plusieurs.

Exemple :

```text
○ Toutes les pièces
● Pièces sélectionnées
○ Pièces de la vue active
```

---

# 33. Listes

Lorsqu'un outil manipule de nombreux éléments Revit, utiliser des listes claires permettant :

- la sélection multiple ;
- la recherche ;
- éventuellement le tri ;
- éventuellement le filtrage.

---

# 34. Listes avec cases à cocher

Pour PublisherAI et les outils similaires, un système de listes avec cases à cocher est recommandé.

Exemple :

```text
☑ Carnet APS
☑ Carnet DCE
☐ Carnet Commercial
☑ Carnet Synthèse
```

---

# 35. Sélection globale

Lorsqu'une liste comporte de nombreux éléments, proposer :

```text
Tout sélectionner
Tout désélectionner
```

Ces actions peuvent être représentées par des boutons secondaires discrets.

---

# 36. Recherche dans les listes

À partir d'une dizaine ou quinzaine d'éléments, un champ de recherche peut améliorer fortement l'utilisation.

Exemple :

```text
Rechercher...
```

Le filtrage doit idéalement être instantané.

---

# 37. DataGrid

Utiliser un DataGrid lorsque plusieurs informations doivent être comparées.

Exemple :

```text
Nom           Niveau     Surface       État
------------------------------------------------
Séjour        RDC        25,40 m²      ✓
Cuisine       RDC        10,20 m²      ✓
Chambre 01    R+1        12,10 m²      !
```

---

# 38. Informations essentielles uniquement

Les tableaux ne doivent pas afficher toutes les propriétés disponibles dans Revit.

Afficher uniquement les informations utiles à la décision de l'utilisateur.

---

# 39. Icônes

Les icônes doivent rester :

- simples ;
- reconnaissables ;
- homogènes ;
- cohérentes avec l'action.

Éviter les styles mélangés entre les outils.

---

# 40. Style des icônes

Privilégier :

- pictogrammes simples ;
- formes géométriques ;
- faible niveau de détail ;
- épaisseur de trait cohérente.

Éviter les icônes réalistes ou décoratives.

---

# 41. Couleur des icônes

Les icônes standards peuvent être :

```text
gris foncé
```

Les icônes actives ou principales peuvent utiliser :

```text
TAA Orange
#FA641F
```

---

# 42. Icônes pyRevit

Les icônes affichées dans le ruban pyRevit doivent partager une identité graphique commune.

Une stratégie recommandée consiste à utiliser :

- formes simples ;
- fond neutre ;
- accent orange TAA ;
- symboles facilement identifiables à petite taille.

---

# 43. Logo TAA

Le logo de l'agence ne doit pas nécessairement être affiché dans chaque fenêtre.

Une surutilisation du logo peut alourdir les interfaces.

L'identité doit principalement être assurée par :

- la couleur ;
- les espacements ;
- les composants ;
- la typographie ;
- la structure commune.

---

# 44. Typographie

Les interfaces WPF doivent utiliser une police facilement disponible sous Windows.

Police recommandée :

```text
Segoe UI
```

Elle est particulièrement adaptée à l'environnement Windows et Revit.

---

# 45. Taille des textes

Recommandations indicatives :

```text
Titre principal        18–22 px
Titre de section       14–16 px
Texte normal           12–14 px
Texte secondaire       11–12 px
Informations mineures  10–11 px
```

Éviter les textes trop petits.

---

# 46. Gras

Le gras doit servir à structurer l'information.

Utilisation recommandée :

- titres ;
- valeurs importantes ;
- avertissements ponctuels.

Éviter de mettre tous les textes en gras.

---

# 47. Majuscules

Éviter les textes entièrement en majuscules dans les interfaces.

Préférer :

```text
Paramètres d'export
```

à :

```text
PARAMÈTRES D'EXPORT
```

Les majuscules peuvent éventuellement être utilisées ponctuellement pour de très petits labels.

---

# 48. Ton rédactionnel

Les textes affichés doivent être :

- courts ;
- directs ;
- professionnels ;
- compréhensibles par un utilisateur non développeur.

---

# 49. Terminologie

Utiliser en priorité le vocabulaire métier employé dans Revit et dans l'agence.

Exemples :

```text
Feuille
Vue
Pièce
Paramètre
Nomenclature
Famille
Type
Occurrence
Sous-projet
```

Éviter le vocabulaire informatique lorsqu'un terme métier existe.

---

# 50. Messages utilisateur

Préférer :

```text
Aucune feuille n'a été sélectionnée.
```

à :

```text
Error: collection sheetList returned null.
```

Les détails techniques appartiennent aux logs.

---

# 51. Messages de succès

Les confirmations doivent être courtes.

Exemple :

```text
Export terminé.
```

ou :

```text
42 feuilles ont été exportées.
```

Éviter les boîtes de dialogue inutiles lorsque le résultat est déjà visible dans la fenêtre.

---

# 52. Messages d'erreur

Un message d'erreur doit expliquer :

1. ce qui s'est passé ;
2. éventuellement pourquoi ;
3. ce que l'utilisateur peut faire.

Exemple :

```text
Impossible de lancer le calcul.

Le paramètre « Surface calculée » est en lecture seule.
Sélectionnez un autre paramètre de destination.
```

---

# 53. Messages d'avertissement

Les avertissements doivent être utilisés lorsqu'une opération reste possible mais comporte un risque ou une limitation.

Exemple :

```text
3 pièces ne possèdent pas le paramètre sélectionné.
Elles seront ignorées.
```

---

# 54. Boîtes de confirmation

Les confirmations doivent être réservées aux opérations ayant un impact significatif.

Exemple :

```text
Cette opération va modifier 248 pièces.

Continuer ?
```

Boutons :

```text
[ Annuler ] [ Continuer ]
```

---

# 55. Progression

Une opération nécessitant plusieurs secondes doit fournir une indication visuelle de progression lorsque cela est techniquement possible.

Exemple :

```text
Analyse des pièces...

████████████████░░░░  78 %

196 / 248
```

---

# 56. ProgressBar

La barre de progression peut utiliser :

```text
TAA Orange
#FA641F
```

Cette utilisation renforce naturellement l'identité graphique.

---

# 57. Texte de progression

Lorsque possible, afficher l'étape en cours.

Exemple :

```text
Export de la feuille A101...
```

ou :

```text
Analyse des pièces : 196 / 248
```

---

# 58. Annulation

Pour les opérations longues, un bouton :

```text
Annuler
```

doit être envisagé.

L'annulation doit intervenir proprement sans laisser le modèle Revit dans un état incohérent.

---

# 59. Interface pendant le traitement

Lorsqu'un traitement est lancé :

- les contrôles pouvant modifier les paramètres doivent être désactivés ;
- le bouton principal doit être désactivé ;
- la progression doit être visible ;
- une annulation peut rester disponible.

---

# 60. États vides

Une interface ne doit pas afficher une grande zone vide sans explication.

Exemple :

```text
Aucune feuille disponible.

Modifiez les filtres ou ouvrez un projet contenant des feuilles.
```

---

# 61. Tooltips

Les Tooltips doivent uniquement compléter une information.

Ils ne doivent pas être indispensables à la compréhension de l'interface.

Exemple :

```text
Inclut également les feuilles dont le paramètre « À publier » est désactivé.
```

---

# 62. Informations avancées

Les options rarement utilisées ne doivent pas encombrer l'interface principale.

Elles peuvent être regroupées dans :

```text
Options avancées
```

avec un panneau repliable.

---

# 63. Progressive disclosure

Principe recommandé :

> Afficher d'abord ce qui est nécessaire. Afficher le reste uniquement lorsque l'utilisateur en a besoin.

Cette règle est particulièrement importante pour les outils comportant de nombreux paramètres.

---

# 64. Fenêtres modales

Utiliser une fenêtre modale lorsque l'utilisateur doit terminer ou annuler une opération avant de retourner dans Revit.

Éviter cependant les successions de fenêtres modales.

---

# 65. Taille des fenêtres

Les fenêtres doivent être dimensionnées en fonction du contenu.

Éviter :

- les fenêtres gigantesques pour trois paramètres ;
- les fenêtres minuscules nécessitant trop de scroll ;
- les dimensions fixes empêchant l'adaptation.

---

# 66. Taille minimale

Les fenêtres complexes peuvent définir :

```text
MinWidth
MinHeight
```

afin de garantir que l'interface reste utilisable.

---

# 67. Redimensionnement

Lorsque l'outil contient :

- des listes ;
- des tableaux ;
- des logs ;
- des résultats ;

la fenêtre devrait généralement pouvoir être redimensionnée.

---

# 68. ScrollViewer

Le défilement doit être réservé aux contenus qui peuvent réellement devenir longs.

Ne pas utiliser un ScrollViewer pour masquer un mauvais dimensionnement initial.

---

# 69. Responsive WPF

Même si WPF n'est pas une interface Web, les composants doivent s'adapter intelligemment au redimensionnement.

Privilégier :

```text
Grid
Auto
*
```

plutôt que des dimensions entièrement fixes.

---

# 70. Grid plutôt que Canvas

Pour les interfaces Outils TAA, privilégier :

```xml
<Grid>
```

et les layouts adaptatifs.

Éviter :

```xml
<Canvas>
```

pour les interfaces standard.

Les positionnements absolus sont difficiles à maintenir.

---

# 71. Styles centralisés

Les styles ne doivent pas être recréés dans chaque fenêtre.

Créer un système centralisé de ressources WPF.

Exemple :

```text
resources/
└── ui/
    ├── Colors.xaml
    ├── Buttons.xaml
    ├── Inputs.xaml
    ├── Typography.xaml
    └── Theme.xaml
```

---

# 72. Colors.xaml

La couleur TAA doit être définie une seule fois.

Exemple :

```xml
<Color x:Key="TAAOrangeColor">#FA641F</Color>

<SolidColorBrush
    x:Key="TAAOrangeBrush"
    Color="{StaticResource TAAOrangeColor}" />
```

---

# 73. Couleurs secondaires centralisées

Exemple :

```xml
<Color x:Key="TextPrimaryColor">#252525</Color>
<Color x:Key="TextSecondaryColor">#666666</Color>
<Color x:Key="BackgroundColor">#F7F7F7</Color>
<Color x:Key="BorderColor">#D9D9D9</Color>
```

Puis :

```xml
<SolidColorBrush
    x:Key="TextPrimaryBrush"
    Color="{StaticResource TextPrimaryColor}" />
```

---

# 74. Style du bouton principal

Exemple conceptuel :

```xml
<Style x:Key="PrimaryButtonStyle"
       TargetType="Button">

    <Setter Property="Background"
            Value="{StaticResource TAAOrangeBrush}" />

    <Setter Property="Foreground"
            Value="White" />

    <Setter Property="Padding"
            Value="16,8" />

    <Setter Property="MinHeight"
            Value="32" />

</Style>
```

Le style complet devra également gérer :

- Hover ;
- Pressed ;
- Disabled ;
- Focus.

---

# 75. Ne pas coder les couleurs directement

Éviter :

```xml
Background="#FA641F"
```

dans chaque fenêtre.

Préférer :

```xml
Background="{StaticResource TAAOrangeBrush}"
```

Cela permet de modifier le design system globalement.

---

# 76. Composants communs

Lorsque plusieurs outils utilisent les mêmes composants, ceux-ci doivent être mutualisés.

Exemples :

```text
PrimaryButton
SecondaryButton
SearchBox
ParameterSelector
ProgressPanel
MessagePanel
SectionHeader
EmptyState
```

---

# 77. Composants Revit spécifiques

Certains composants peuvent être développés spécifiquement pour les usages Revit.

Exemples :

```text
ParameterSelector
CategorySelector
ViewSelector
SheetSelector
FamilySelector
LevelSelector
WorksetSelector
```

Ils doivent présenter le même comportement dans tous les outils.

---

# 78. ParameterSelector

Le sélecteur de paramètres devrait pouvoir gérer :

- nom du paramètre ;
- type de donnée ;
- lecture seule ;
- paramètre instance/type ;
- éventuellement paramètre partagé.

L'utilisateur ne devrait pas avoir à comprendre les détails de l'API Revit.

---

# 79. Indication lecture seule

Lorsqu'un paramètre ne peut pas être modifié, l'interface doit le signaler.

Exemple :

```text
Surface
Lecture seule
```

ou le retirer directement de la liste lorsqu'il s'agit d'un paramètre de destination.

---

# 80. Validation instantanée

Lorsque possible, vérifier les saisies avant de lancer le traitement.

Exemple :

```text
Paramètre source : Surface
Paramètre cible : —
```

Le bouton :

```text
Calculer
```

reste désactivé.

---

# 81. État valide

Lorsque toutes les conditions nécessaires sont réunies :

```text
Calculer
```

devient actif avec le style TAA Orange.

---

# 82. État d'erreur dans un champ

Une erreur de saisie doit être visible près du champ concerné.

Exemple :

```text
Chemin d'export
[C:\Projet\...]

⚠ Le dossier n'existe pas.
```

Éviter de signaler toutes les erreurs uniquement après avoir cliqué sur le bouton principal.

---

# 83. Interface de PublisherAI

PublisherAI est susceptible de devenir l'un des outils les plus complets de la suite.

Sa structure recommandée est :

```text
┌───────────────────────────────────────────────┐
│ PublisherAI                                   │
│ Publication de carnets PDF et DWG             │
├───────────────────────────────────────────────┤
│                                               │
│ CARNETS                                       │
│                                               │
│ ☑ APS                                         │
│ ☑ DCE                                         │
│ ☐ Commercial                                  │
│                                               │
│ [Tout sélectionner] [Tout désélectionner]     │
│                                               │
├───────────────────────────────────────────────┤
│ OPTIONS                                       │
│                                               │
│ ☑ Exporter PDF                                │
│ ☑ Exporter DWG                                │
│ ☑ Fusionner les PDF                           │
│                                               │
│ Dossier                                       │
│ [ C:\Projet\Exports            ] [Parcourir]  │
│                                               │
├───────────────────────────────────────────────┤
│ Progression                                   │
│ ███████████████░░░░ 75 %                      │
│ Export de A103...                             │
├───────────────────────────────────────────────┤
│ [Annuler]                           [Publier]  │
└───────────────────────────────────────────────┘
```

Le bouton **Publier** utilise TAA Orange.

La barre de progression peut également utiliser TAA Orange.

---

# 84. Interface de RoomCalculator

Structure recommandée :

```text
┌───────────────────────────────────────────────┐
│ RoomCalculator                                │
│ Calcul des paramètres de pièces               │
├───────────────────────────────────────────────┤
│                                               │
│ PIÈCES                                        │
│                                               │
│ ● Toutes les pièces                           │
│ ○ Pièces sélectionnées                        │
│ ○ Pièces de la vue active                     │
│                                               │
│ CALCUL                                        │
│                                               │
│ Paramètre source                              │
│ [ Surface ▼ ]                                 │
│                                               │
│ Opération                                     │
│ [ Somme ▼ ]                                   │
│                                               │
│ Paramètre destination                         │
│ [ Surface totale ▼ ]                          │
│                                               │
├───────────────────────────────────────────────┤
│ 248 pièces seront analysées.                  │
├───────────────────────────────────────────────┤
│ [Annuler]                          [Calculer]  │
└───────────────────────────────────────────────┘
```

---

# 85. Thème clair

Le thème clair constitue la référence principale pour Outils TAA.

Palette recommandée :

```text
Fond principal       #FFFFFF
Fond secondaire      #F7F7F7
Fond contrôle        #FFFFFF
Texte principal      #252525
Texte secondaire     #666666
Bordure               #D9D9D9
Accent TAA           #FA641F
```

---

# 86. Mode sombre

La compatibilité avec un thème sombre peut être envisagée à terme.

Cependant, les couleurs ne doivent pas être codées directement dans les fenêtres.

Un système de ressources centralisées permettra de créer ultérieurement :

```text
Theme.Light.xaml
Theme.Dark.xaml
```

sans réécrire les interfaces.

---

# 87. Compatibilité avec Revit

Les interfaces ne doivent pas chercher à reproduire exactement le style natif de Revit.

Elles doivent toutefois rester compatibles avec son environnement :

- sobriété ;
- densité raisonnable ;
- composants connus ;
- comportement Windows standard.

Une interface trop éloignée du langage visuel des logiciels professionnels peut perturber l'utilisateur.

---

# 88. Densité de l'information

Les outils BIM contiennent souvent beaucoup de données.

L'objectif n'est donc pas de créer des interfaces excessivement aérées comme sur certaines applications mobiles.

Il faut trouver un équilibre entre :

```text
lisibilité
```

et :

```text
densité d'information
```

---

# 89. Limiter le nombre d'étapes

Une tâche fréquente doit nécessiter le moins d'étapes possible.

Exemple :

```text
Ouvrir outil
↓
Choisir paramètres
↓
Lancer
```

Éviter :

```text
Ouvrir outil
↓
Page 1
↓
Suivant
↓
Page 2
↓
Suivant
↓
Page 3
↓
Valider
```

sauf si un assistant en plusieurs étapes est réellement nécessaire.

---

# 90. Mémorisation des préférences

Lorsqu'un utilisateur utilise régulièrement le même outil, celui-ci peut mémoriser :

- paramètres sélectionnés ;
- dossier d'export ;
- options d'export ;
- taille de fenêtre ;
- filtres ;
- dernières valeurs utilisées.

Ces paramètres doivent utiliser le système commun défini dans :

```text
lib/common/settings.py
```

---

# 91. Ne pas mémoriser aveuglément

Certaines valeurs sont spécifiques à un projet Revit.

La persistance doit distinguer :

```text
Préférences utilisateur
```

et :

```text
Informations du projet
```

afin d'éviter de restaurer une valeur invalide dans un autre projet.

---

# 92. Feedback immédiat

Chaque action utilisateur doit produire un feedback visible.

Exemples :

```text
bouton activé
```

```text
élément sélectionné
```

```text
progression lancée
```

```text
message affiché
```

L'utilisateur ne doit jamais se demander :

> Est-ce que mon clic a fonctionné ?

---

# 93. Performance perçue

Même lorsqu'un calcul prend du temps, une interface réactive donne une sensation de meilleure performance.

Afficher rapidement :

```text
Analyse en cours...
```

est préférable à une fenêtre figée plusieurs secondes.

---

# 94. Éviter le blocage de l'interface

Lorsque techniquement possible, les opérations longues doivent permettre au système d'actualiser l'interface.

Attention cependant aux contraintes propres à l'API Revit et à son modèle d'exécution.

La stabilité du modèle reste prioritaire sur l'animation de l'interface.

---

# 95. Fenêtres d'aide

Les outils complexes peuvent proposer :

```text
?
```

ou :

```text
Aide
```

L'aide doit rester distincte du flux principal de l'outil.

---

# 96. Documentation contextuelle

Pour une option complexe, une courte explication peut être affichée sous le contrôle.

Exemple :

```text
Fusionner les PDF
Crée un fichier PDF unique pour chaque carnet.
```

Le texte secondaire doit être moins visible que le libellé principal.

---

# 97. Ordre de tabulation

Les contrôles doivent être accessibles dans un ordre logique avec la touche :

```text
Tab
```

L'ordre doit suivre le sens de lecture de l'interface.

---

# 98. Raccourcis clavier

Lorsque cela est pertinent :

```text
Entrée
```

peut déclencher l'action principale.

```text
Échap
```

peut fermer ou annuler une fenêtre.

Ces comportements doivent être utilisés avec prudence lorsqu'une opération pourrait modifier beaucoup d'éléments.

---

# 99. Accessibilité des couleurs

Une information ne doit jamais être transmise uniquement par une couleur.

Éviter :

```text
Vert = correct
Rouge = erreur
```

sans autre indication.

Ajouter également :

```text
✓ Correct
```

```text
⚠ Attention
```

```text
✕ Erreur
```

---

# 100. Contraste

Le contraste texte/fond doit toujours rester suffisant.

Le TAA Orange :

```text
#FA641F
```

doit principalement être utilisé :

- sur fond clair ;
- comme fond associé à du texte blanc lorsque la lisibilité est suffisante ;
- pour des indicateurs graphiques.

---

# 101. Résolutions d'écran

Les interfaces doivent rester utilisables sur les configurations courantes de l'agence.

Éviter les fenêtres nécessitant obligatoirement de très grandes résolutions.

Prendre en compte le scaling Windows et les écrans haute résolution.

---

# 102. DPI

WPF permet une bonne gestion des DPI lorsqu'il est correctement utilisé.

Éviter les interfaces basées sur :

- des images contenant du texte ;
- des placements pixel-perfect rigides ;
- des tailles fixes excessives.

---

# 103. Images et illustrations

Les illustrations doivent rester rares dans les outils métiers.

Elles peuvent être utiles pour :

- expliquer une sélection ;
- visualiser une orientation ;
- expliquer un système constructif ;
- présenter un aperçu avant traitement.

Elles ne doivent pas servir uniquement à décorer.

---

# 104. Aperçu

Lorsqu'un résultat peut être prévisualisé avant modification du modèle, cette possibilité doit être privilégiée.

Exemple :

```text
248 pièces seront modifiées.

Surface totale : 4 892,40 m²
```

avant :

```text
[ Appliquer ]
```

---

# 105. Interfaces de contrôle qualité

Pour les outils de contrôle, utiliser une hiérarchie de résultats claire.

Exemple :

```text
✓ 184 éléments conformes
⚠ 12 avertissements
✕ 3 erreurs
```

Le nombre total doit être immédiatement visible.

---

# 106. Filtrer les résultats

Les interfaces de contrôle peuvent permettre :

```text
Tous
Erreurs
Avertissements
Conformes
```

Le filtre actif peut utiliser TAA Orange comme accent.

---

# 107. Interaction avec Revit

Lorsqu'un résultat correspond à un élément Revit, envisager des actions telles que :

```text
Sélectionner
Afficher
Zoomer
```

afin d'éviter que l'utilisateur ait à rechercher manuellement l'élément.

---

# 108. Double-clic

Un double-clic dans une liste peut éventuellement :

```text
sélectionner l'élément dans Revit
```

ou :

```text
ouvrir la vue correspondante
```

uniquement si ce comportement est intuitif et documenté.

---

# 109. Menus contextuels

Ils peuvent être utilisés pour des actions secondaires telles que :

```text
Sélectionner dans Revit
Copier l'identifiant
Ouvrir la vue
Afficher les propriétés
```

Les actions principales doivent rester visibles sans menu contextuel.

---

# 110. Fenêtre de logs

Les logs techniques ne doivent pas être affichés par défaut.

Une section avancée peut éventuellement proposer :

```text
Afficher les détails
```

pour les utilisateurs BIM ou développeurs.

---

# 111. Niveaux d'information

L'interface doit distinguer :

```text
Utilisateur standard
```

et :

```text
Informations techniques
```

Le premier niveau doit rester compréhensible par tous les utilisateurs.

---

# 112. Organisation des fichiers WPF

Structure recommandée :

```text
tool/
├── script.py
├── ui/
│   ├── MainWindow.xaml
│   ├── MainWindow.py
│   └── viewmodels/
├── models/
├── services/
└── resources/
```

Les ressources communes restent dans la bibliothèque générale Outils TAA lorsque plusieurs outils les utilisent.

---

# 113. Architecture MVVM

Pour les interfaces complexes, une architecture inspirée de MVVM peut être utilisée.

Structure :

```text
View
↓
ViewModel
↓
Services
↓
Revit API
```

L'objectif n'est pas d'appliquer MVVM de manière dogmatique.

L'objectif est de maintenir une séparation claire entre :

- présentation ;
- état ;
- logique métier ;
- accès Revit.

---

# 114. Code-behind

Le code-behind doit principalement gérer les interactions directement liées à la vue.

Éviter d'y placer :

- calculs complexes ;
- accès massif à Revit ;
- logique métier ;
- gestion des fichiers métier.

---

# 115. Design system centralisé

À terme, Outils TAA doit disposer de son propre mini design system.

Exemple :

```text
resources/ui/
├── Colors.xaml
├── Typography.xaml
├── Buttons.xaml
├── Inputs.xaml
├── Lists.xaml
├── DataGrid.xaml
├── Messages.xaml
└── Theme.xaml
```

---

# 116. Tokens graphiques

Certaines valeurs doivent devenir des constantes communes.

Exemple :

```text
AccentColor
TextPrimaryColor
TextSecondaryColor
BackgroundPrimaryColor
BackgroundSecondaryColor
BorderColor

SpacingXS
SpacingS
SpacingM
SpacingL
SpacingXL

ControlHeight
CornerRadius
```

---

# 117. Corner Radius

Les interfaces doivent rester modernes mais sobres.

Recommandation :

```text
CornerRadius : 3 à 6 px
```

Éviter les boutons extrêmement arrondis typiques d'interfaces mobiles.

---

# 118. Ombres

Les ombres doivent être utilisées très modérément.

Elles peuvent servir à mettre en évidence :

- une boîte flottante ;
- une fenêtre secondaire ;
- un menu.

Éviter les ombres lourdes sur tous les composants.

---

# 119. Bordures

Une bordure doit servir à structurer ou signaler un état.

Elle ne doit pas entourer systématiquement chaque bloc.

---

# 120. Style Outils TAA recherché

L'identité générale doit tendre vers :

```text
Professionnel
Technique
Minimal
Lisible
Contemporain
Architectural
```

et éviter :

```text
Interface gadget
Interface gaming
Interface trop colorée
Interface surchargée
Interface mobile surdimensionnée
```

---

# 121. Exemple de palette complète

```text
TAA Orange
#FA641F
RGB 250 / 100 / 31

TAA Orange Hover
#E85819

TAA Orange Pressed
#D84F12

Background Primary
#FFFFFF

Background Secondary
#F7F7F7

Background Tertiary
#EFEFEF

Text Primary
#252525

Text Secondary
#666666

Text Disabled
#A0A0A0

Border
#D9D9D9
```

---

# 122. Utilisation recommandée de l'orange

## Forte priorité

```text
Bouton principal
Barre de progression
Élément sélectionné
Focus actif
```

## Priorité moyenne

```text
Icône active
Petit indicateur
Lien
Badge
```

## À éviter

```text
Grand fond de fenêtre
Grand panneau
Tous les titres
Tous les boutons
Toutes les icônes
Texte courant
```

---

# 123. Checklist UI développeur

Avant de considérer une interface comme terminée, vérifier :

```text
☐ Une action principale est clairement identifiable.

☐ Le bouton principal utilise le style commun Outils TAA.

☐ La couleur TAA Orange n'est pas surutilisée.

☐ Les champs sont correctement alignés.

☐ Les espacements sont cohérents.

☐ Les textes sont courts et compréhensibles.

☐ Les erreurs apparaissent près du problème lorsque possible.

☐ Les options non disponibles sont désactivées.

☐ Le bouton principal est désactivé si les données sont invalides.

☐ Les opérations longues affichent une progression.

☐ L'utilisateur reçoit un feedback après une action.

☐ L'interface reste utilisable avec différentes tailles de fenêtre.

☐ Les couleurs proviennent des ressources communes.

☐ Aucun code couleur majeur n'est dupliqué dans la fenêtre.

☐ L'interface ne contient pas de logique métier importante.

☐ Les contrôles respectent le vocabulaire Revit.

☐ Les informations techniques ne polluent pas l'expérience utilisateur.

☐ Les opérations destructives sont clairement identifiées.

☐ La fenêtre a été testée sur un projet réel.
```

---

# 124. Checklist de revue UI

Lors d'une revue de code ou de design :

```text
1. Comprend-on l'objectif de l'outil en moins de cinq secondes ?

2. L'action principale est-elle immédiatement visible ?

3. Peut-on supprimer une étape ?

4. Peut-on supprimer un texte ?

5. Peut-on supprimer une option de l'écran principal ?

6. Les valeurs par défaut sont-elles pertinentes ?

7. Le bouton principal peut-il être déclenché par erreur ?

8. Les erreurs sont-elles compréhensibles ?

9. L'orange TAA est-il utilisé comme accent et non comme décoration ?

10. L'outil ressemble-t-il aux autres outils Outils TAA ?
```

---

# 125. Standard minimal obligatoire

Toute nouvelle interface Outils TAA doit au minimum respecter :

```text
Segoe UI

Couleurs centralisées

TAA Orange = #FA641F

Action principale clairement identifiable

Bouton principal à droite

Bouton Annuler / Fermer secondaire

Marges cohérentes

Alignements réguliers

Messages utilisateur en français

Validation des saisies

Gestion de l'état Disabled

Pas de logique métier importante dans le XAML/code-behind

Compatibilité Revit 2025.4 / pyRevit 5.x
```

---

# 126. Règle de cohérence

Lorsqu'un choix graphique ou ergonomique existe déjà dans un outil Outils TAA, un nouvel outil doit préférer reprendre ce comportement plutôt que d'inventer une nouvelle solution.

> **La cohérence globale est plus importante que l'originalité locale.**

---

# 127. Règle de simplicité

Si deux interfaces permettent d'effectuer exactement la même tâche, privilégier celle qui :

- affiche le moins d'éléments ;
- nécessite le moins de clics ;
- nécessite le moins d'explications ;
- produit le moins d'erreurs possibles.

---

# 128. Principe directeur

Chaque écran doit permettre de répondre immédiatement à quatre questions :

```text
Où suis-je ?

Que dois-je faire ?

Que va-t-il se passer ?

Quelle action dois-je lancer ?
```

Si l'une de ces réponses n'est pas évidente, l'interface doit être simplifiée.

---

# 129. Résumé du Design System Outils TAA

```text
Couleur principale
TAA Orange
RGB(250,100,31)
#FA641F

Style
Sobre
Professionnel
Technique
Minimal

Police
Segoe UI

Layout
Grid WPF
Alignements réguliers
Espacement basé sur multiples de 4

Bouton principal
TAA Orange
Texte blanc
Position généralement à droite

Interface
Fond clair
Couleurs neutres
Orange utilisé comme accent

Architecture
XAML + logique UI
Séparation métier
Ressources graphiques mutualisées
```

---

# 130. Conclusion

Les interfaces Outils TAA doivent constituer un environnement cohérent autour des outils Revit développés par l'agence.

La couleur **TAA Orange — RGB(250,100,31) — #FA641F** constitue le principal élément d'identité visuelle, mais son efficacité repose sur une utilisation mesurée.

Le design system doit permettre à un utilisateur de reconnaître immédiatement un outil Outils TAA tout en conservant une interface professionnelle adaptée à un usage quotidien dans Revit.

L'objectif final n'est pas simplement de créer de belles fenêtres.

L'objectif est de créer des outils :

> **rapides à comprendre, simples à utiliser et cohérents entre eux.**