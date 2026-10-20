# Export — Corrections de la vague de tests et ergonomie

**Cible :** Revit 2025.4 / pyRevit 5.x  
**Branche de travail :** `fix/export-test-wave`

## Périmètre

Cette vague regroupe les corrections demandées après la première campagne de tests :

- prévisualisation du nommage qui affichait `—` ;
- rafraîchissement des numéros et noms de feuilles après modification dans Revit ;
- maintien de l'ouverture des dossiers après un déplacement par glisser-déposer ;
- insertion d'un carnet avant **ou après** un carnet cible ;
- comportement de sélection multiple compatible avec un usage Windows : Ctrl/Maj sont pris en compte au clic et n'ont pas besoin de rester enfoncés pendant tout le déplacement ;
- diagnostic explicite des échecs d'export DWG.

## Règles fonctionnelles

### Prévisualisation du nommage

La prévisualisation utilise le même moteur de résolution que l'export réel. Elle ne doit pas utiliser un moteur distinct susceptible de diverger du nom effectivement produit.

Les variables intégrées et les variables `{parametre:Nom}` suivent le même mécanisme de résolution que l'export.

### Rafraîchissement des feuilles

Le `UniqueId` reste la référence durable. Le numéro et le nom affichés sont des métadonnées susceptibles d'évoluer dans Revit.

À l'ouverture d'Export :

1. les feuilles courantes du document sont récupérées ;
2. les éléments des carnets persistants sont recherchés par `UniqueId` ;
3. `sheet_number` et `sheet_name` sont actualisés ;
4. l'ordre manuel des éléments n'est pas modifié.

### Glisser-déposer

Le comportement attendu est :

```text
Ctrl + clic     → ajoute/retire un élément de la sélection
Shift + clic    → sélectionne une plage
clic simple     → sélection simple
puis glisser    → la sélection reste active même si Ctrl/Maj est relâché
```

Pour les carnets :

```text
Carnet → Dossier       → fin du dossier
Carnet → moitié haute d'un carnet → avant
Carnet → moitié basse d'un carnet → après
```

Après un déplacement, les dossiers qui étaient ouverts restent ouverts.

### DWG

Un retour `False` de `Document.Export` n'est plus transformé en message générique uniquement. Le rapport conserve le contexte : nombre de vues, configuration DWG, True Color et mode combiné/séparé.

Une exception Revit est également remontée avec son message réel.

## Tests anti-régression préparés

- `tests/test_filename_service_preview.py`
- `tests/test_carnet_controller_metadata_refresh.py`
- TEST-08 : dossier restant ouvert après déplacement
- TEST-09 : insertion d'un carnet après un carnet cible
- TEST-11 : sélection Ctrl/Maj indépendante de la durée du glisser
- TEST-22 / TEST-23 : prévisualisation du nommage
- test de rafraîchissement après renommage d'une feuille dans Revit
- TEST-16 : diagnostic DWG enrichi afin d'identifier toute condition Revit restante au prochain test réel

## Validation

Les tests Python créés dans cette vague doivent être exécutés avant de considérer le raccordement terminé. Les comportements WPF, Revit API, PDF et DWG doivent ensuite être validés dans Revit 2025.4.
