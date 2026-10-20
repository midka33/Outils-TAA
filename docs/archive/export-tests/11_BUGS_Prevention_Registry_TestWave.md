# Complément de capitalisation — Vague de tests Export

Ce document complète `docs/11_BUGS_Prevention_Registry.md` pour la vague de corrections Export menée après TEST-04.

## BUG-EXPORT-019 — Prévisualisation du nommage affichant `—`

**Symptôme :** la zone de prévisualisation du nom de fichier reste sur `—`, alors que le modèle de nommage est renseigné.

**Cause racine :** `ExportWindow._update_filename_preview()` appelait `FilenameService.preview()`, mais ce contrat n'était plus implémenté par `FilenameService`. L'exception était absorbée par un `except Exception`, ce qui masquait la cause et produisait silencieusement `—`.

**Correction :** ajout de `FilenameService.preview()`, utilisant le même moteur `resolve()` que la génération réelle des noms.

**Règle préventive :** ne jamais absorber silencieusement une erreur de prévisualisation sans conserver un mécanisme de diagnostic ; la prévisualisation doit réutiliser le moteur de résolution de l'export réel.

**Anti-régression :** tester les variables intégrées et `{parametre:Sous-titre}` dans l'interface Export.

## BUG-EXPORT-020 — Métadonnées de feuille persistées obsolètes après renommage dans Revit

**Symptôme :** après modification du numéro ou du nom d'une feuille dans Revit, Export réaffiche l'ancienne valeur lors de la session suivante.

**Cause racine :** les carnets persistants conservaient `sheet_number` et `sheet_name` comme métadonnées d'affichage et l'arborescence les utilisait directement sans resynchronisation avec le document Revit courant.

**Correction :** ajout de `CarnetController.refresh_persistent_metadata()`, exécuté au chargement d'Export. La synchronisation utilise `UniqueId`, actualise le numéro et le nom, et conserve strictement l'ordre métier du carnet.

**Règle préventive :** `UniqueId` est la référence durable ; les libellés de feuille doivent être considérés comme des métadonnées rafraîchissables.

**Anti-régression :** renommer une feuille dans Revit, fermer/réouvrir Export et vérifier que le nouveau numéro/nom apparaît sans réordonner le carnet.

## BUG-EXPORT-021 — Ergonomie du glisser-déposer non conforme à l'usage Windows

**Symptôme :** la sélection multiple pouvait nécessiter de conserver Ctrl/Maj pendant toute l'opération de déplacement ; le déplacement après un carnet cible était également difficile car seul le dépôt « avant » était représenté.

**Cause racine :** la sélection et le payload de drag-and-drop restaient trop dépendants de l'état clavier pendant le déplacement, et le moteur de dépôt ne distinguait pas les zones avant/après du carnet cible.

**Correction :** gel du payload au clic de départ, ajout d'un dépôt `AFTER` selon la position verticale du pointeur, indicateur visuel inférieur et conservation des dossiers ouverts lors du rafraîchissement après déplacement.

**Règle préventive :** l'état métier d'une opération de drag-and-drop doit être capturé au début du geste ; l'état du clavier pendant le mouvement ne doit pas modifier la sélection déjà constituée.

**Anti-régression :** sélectionner avec Ctrl/Maj puis relâcher les touches avant de glisser ; déposer un carnet dans la moitié basse d'un autre carnet ; vérifier que les dossiers précédemment ouverts restent ouverts.

## TEST-16 — Export DWG

Le service de publication conserve désormais le contexte exact d'un échec DWG : exception Revit éventuelle, nombre de vues, configuration sélectionnée, True Color et mode combiné/séparé. Cette amélioration est volontairement couplée à une nouvelle validation Revit 2025.4 : un retour `False` de `Document.Export` ne doit plus être présenté comme une simple « erreur 1 » sans diagnostic.
