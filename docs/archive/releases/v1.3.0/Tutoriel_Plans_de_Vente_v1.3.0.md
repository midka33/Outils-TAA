# Tutoriel — Plans de vente

**Outils TAA v1.3.0 — Plans de vente V1.1 — Autodesk Revit 2025.4 / pyRevit 5.x / Windows**

## Préparer le fichier SITE

La feuille modèle et les feuilles finales sont créées dans le fichier hôte
`SITE.rvt`.

Préparer dans SITE :

- le cartouche ;
- une ou deux vues principales sur la feuille modèle ;
- les rectangles de zones de placement ;
- les nomenclatures souhaitées ;
- éventuellement un plan de repérage ;
- le type d'étiquette de pièce à utiliser ;
- le type de cote à utiliser.

Pour les nomenclatures de pièces qui doivent lire les bâtiments liés, activer
**Inclure les éléments des fichiers liés** dans Revit.

### Important — étiquettes et cotes

Plans de vente doit trouver le type d'étiquette et le type de cote dans le
**fichier hôte SITE**.

Si la vue modèle affiche une vue liée et que l'étiquette / la cote visible
appartient uniquement au fichier lié, elle ne sert pas de modèle de type dans
cette version. Placez donc dans la vue modèle des annotations hôtes utilisant
les types attendus.

## Inclure les bâtiments liés

1. Ouvrir **Outils TAA > Plans de vente** depuis SITE.
2. Cocher **Inclure les pièces des fichiers Revit liés**.
3. Vérifier la colonne **Source** dans la liste des logements.
4. Choisir le paramètre identifiant les logements et le filtre éventuel.

Les liens doivent être chargés et liés directement dans SITE. Les liens
imbriqués ne sont pas parcourus dans cette version.

## Niveaux

Aucune préparation manuelle n'est nécessaire si un niveau du bâtiment lié
n'existe pas encore dans SITE.

Plans de vente :

- transforme l'altitude du niveau lié vers SITE ;
- réutilise un niveau SITE unique à cette altitude ;
- sinon crée un niveau `PDV_AUTO_±XX.XXX` ;
- crée une vue plan source si nécessaire.

Si plusieurs niveaux SITE existent déjà à la même altitude, corrigez cette
ambiguïté avant de relancer.

## Choisir la feuille modèle

| Feuille modèle | Résultat multi-niveaux |
|---|---|
| Une vue principale + une zone | une feuille par niveau |
| Deux vues principales + deux zones | deux niveaux sur une même feuille |

Les légendes placées sur la feuille modèle sont réutilisées sur les feuilles
générées sans dupliquer la vue Legend.

## Générer

1. Sélectionner la feuille modèle.
2. Vérifier son aperçu.
3. Choisir le style de ligne des zones principales.
4. Vérifier les options avancées et paramètres cartouche.
5. Sélectionner les logements.
6. Lancer la création.
7. Contrôler la progression puis le rapport.
8. Vérifier les vues, tags, cotes, nomenclatures et cartouches générés.

## Numéros de logements identiques

Tant qu'un numéro n'existe qu'une fois, son nom reste inchangé.

```text
A18
PDV-A18
Plan de vente - A18
```

Les identifiants internes des liens ne sont jamais ajoutés automatiquement dans
le nom.

Si le même numéro apparaît dans plusieurs sources, Plans de vente vous demande
un libellé lisible pour chaque source, par exemple :

```text
A18 - BAT A
A18 - BAT B
```

## Points à surveiller

- Vérifier que le gabarit de vue affiche correctement les liens et les phases.
- Les problèmes d'affichage d'un niveau peuvent provenir du gabarit de vue ;
  Plans de vente ne réécrit pas les réglages de visibilité / phase.
- Contrôler les cotes et références sur les géométries particulières.
- Les liens imbriqués, inclinés ou renversés verticalement sont hors périmètre.
- La mise à jour automatique d'un plan déjà généré reste hors périmètre.
