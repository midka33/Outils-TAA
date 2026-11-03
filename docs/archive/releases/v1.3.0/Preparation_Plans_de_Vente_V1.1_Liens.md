# Plans de vente V1.1 — recette finale des pièces liées

**Date :** 20 octobre 2026  
**Branche :** `feature/plans-de-vente-linked-rooms`  
**PR :** #28 vers `main`  
**Cible produit :** Outils TAA v1.3.0  
**Cible technique :** Autodesk Revit 2025.4 / pyRevit 5.x / Windows  
**Statut :** recette utilisateur validée ; intégrée et publiée dans Outils TAA v1.3.0.

## Décision de release

Le 20 octobre 2026, l'utilisateur a confirmé que la génération fonctionne
correctement sur son projet de test lorsque les types d'étiquette de pièce et de
cote sont présents dans le fichier hôte SITE, puis a explicitement autorisé la
préparation de la release.

Cette validation réelle porte sur le workflow représentatif utilisé pour la
release. Elle ne signifie pas que chaque variante extrême de la matrice de
robustesse a été rejouée manuellement.

## Workflow validé dans Revit 2025.4

- lancement de Plans de vente depuis le fichier SITE ;
- option d'inclusion des pièces des fichiers Revit liés ;
- détection des logements et affichage de leur Source ;
- création automatique d'un niveau SITE manquant à l'altitude transformée ;
- poursuite de la génération sans préparation manuelle de ce niveau ;
- création des vues et crops des logements liés ;
- repérage et nomenclatures issus des pièces liées ;
- mise en page / cartouche générés dans SITE ;
- étiquettes de pièces liées et cotations lorsque leurs types existent dans SITE ;
- noms visibles sans suffixe technique `-L<id instance>` ;
- demande d'un libellé utilisateur uniquement si plusieurs sources portent le
  même numéro logement.

## Préparation du projet

Le fichier SITE contient la feuille modèle, le cartouche, les zones de placement
et les nomenclatures modèles.

Pour les annotations :

- le **type d'étiquette de pièce** utilisé doit exister dans SITE ;
- le **type de cote** utilisé doit exister dans SITE ;
- la vue modèle doit contenir des annotations hôtes permettant au module de
  déduire ces types.

Une étiquette ou une cote visible uniquement parce que la vue affiche un
**fichier lié** appartient au document lié et n'est pas utilisée pour choisir le
type hôte dans cette V1.1.

Pour les nomenclatures de pièces, activer le réglage Revit natif
**Inclure les éléments des fichiers liés**.

## Niveaux SITE

Il n'est plus nécessaire de créer manuellement tous les niveaux correspondant
aux bâtiments liés.

Pour un niveau lié :

1. son altitude est transformée vers le repère SITE ;
2. un niveau SITE unique à cette altitude est réutilisé ;
3. s'il n'existe pas, Plans de vente crée un niveau
   `PDV_AUTO_±XX.XXX` ;
4. si aucune vue plan source exploitable n'existe sur ce niveau, le module en
   crée une ;
5. si plusieurs niveaux SITE existent déjà à la même altitude, le module bloque
   au lieu de choisir arbitrairement.

## Nommage et logements homonymes

L'identité interne reste **Source + numéro logement**, mais cette identité
technique n'est pas affichée dans les noms Revit.

Exemple nominal :

```text
A18
PDV-A18
Plan de vente - A18
```

Aucun suffixe tel que `-L5530419` n'est ajouté par défaut.

Si deux sources contiennent réellement `A18`, Plans de vente demande à
l'utilisateur le texte à ajouter, par exemple `BAT A` et `BAT B`.

## Matrice de robustesse

Les cas ci-dessous restent la référence de non-régression. Ils ne sont pas tous
revendiqués comme rejoués manuellement pendant la recette finale.

| Cas | Attendu / état pour la release |
|---|---|
| Document actif uniquement | comportement V1 conservé |
| Lien direct chargé | validé sur workflow utilisateur |
| Niveau SITE absent | création automatique validée |
| Niveau SITE ambigu | blocage explicite prévu |
| Tags liés | validés lorsque le type existe dans SITE |
| Cotes liées | validées lorsque le type existe dans SITE |
| Nomenclatures liées | workflow validé ; filtres source conservés |
| Repérage lié | workflow validé |
| Numéro logement unique | aucun suffixe technique visible |
| Numéro homonyme entre sources | dialogue de différenciation utilisateur |
| Lien déchargé | ignoré avec avertissement |
| Lien imbriqué | hors périmètre |
| Lien incliné / renversé verticalement | hors périmètre |
| Rotation / symétrie horizontale | couverte par les adaptateurs/tests ; à surveiller sur projets atypiques |
| Type de tag/cote seulement dans un lien | hors périmètre v1.3.0 : type hôte requis |

## Limites acceptées

- Liens directs uniquement.
- Aucun changement automatique des phases / visibilité des liens ou gabarits.
- Les types de tag et de cote doivent être disponibles dans SITE.
- Les références de cote refusées par l'API sont signalées ; aucune cote
  graphique fictive n'est créée.
- Mise à jour automatique des plans existants hors périmètre.
- Plus de deux vues principales sur une même feuille hors périmètre.

## Contrôles automatisés

La branche conserve les suites Plans de vente, Export, Calculs des pièces et le
contrat ruban Export. Le workflow de publication v1.3.0 reconstruit également le
ZIP utilisateur et contrôle son contenu avant toute publication.

## Autorisation d'intégration

- [x] Validation utilisateur du workflow réel Revit 2025.4.
- [x] Limites connues acceptées pour la release.
- [x] Documentation fonctionnelle / technique alignée sur le comportement final.
- [x] Préparation du workflow et des notes Outils TAA v1.3.0.
- [x] CI de la tête finale de PR #28 réussie après la préparation de release.
- [x] PR #28 fusionnée dans `main` — commit `811c314127c00c11e51634407dc2ff47792b4f88`.
- [x] CI du SHA exact de `main` réussie.
- [x] Publication automatique du tag / de la release `v1.3.0`.

La publication effective reste attestée par GitHub Actions et la release GitHub,
pas par ce document seul.
