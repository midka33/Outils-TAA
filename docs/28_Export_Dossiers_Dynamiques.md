# Export — Dossiers dynamiques de mises en page (spécification V1)

**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x.  
**Statut :** première implémentation sur la PR #55 (Draft). Les tests automatisés sont exécutés par la CI ; recette Revit 2025.4 encore nécessaire avant fusion.  
**Base :** Outils TAA v1.4.1 et code `main` courant.  
**Objectif :** réemployer les paramètres et l'organisation du navigateur de projet Revit dans les dossiers de publication Export, sans duplication manuelle.

## Implémentation actuelle (branche PR #55)

- Nouveau bouton **Dossier automatique** dans la barre de l'arborescence, ouvrant l'assistant de création en mode Automatique.
- Règle de sélection **paramètre = valeur exacte**, et sous-dossiers facultatifs par un second paramètre.
- Calcul de listes de feuilles en mémoire lors de la construction du TreeView et avant aperçu ou publication ; mise à jour des feuilles sources à l'actualisation.
- Groupes virtuels à identifiants stables. Aucun enregistrement JSON des modifications automatiques de feuilles.
- Clic droit sur le dossier automatique **Rendre ce dossier manuel** : fige les feuilles et groupes en une mutation atomique du repository.
- Le champ facultatif `source.group_parameter` est compatible avec le **schéma JSON 8** ; le stockage partagé utilise la couche `_mutate` pour la conversion.
- Suppression, renommage et glisser-déposer des sous-dossiers virtuels interdits ; le contenu automatique doit être figé avant un reclassement manuel.
- **Limite :** copie exacte de l'organisation native du navigateur Revit via `BrowserOrganization` non implémentée dans cette première version. Les paramètres de sélection et de groupe doivent être explicitement choisis.
- **Limite :** les changements sont pris en compte à l'ouverture et à l'actualisation, pas par un écouteur permanent Revit.
- **Sécurité :** les paramètres de même nom sur une feuille déclenchent une erreur au lieu de sélectionner un paramètre ambigu.

## 1. Création

Action « Nouveau dossier automatique » dans l'arborescence Export :

- Nom du dossier (libre).
- Paramètre de feuille de sélection (liste issue du document Revit).
- Valeur à retenir (liste distincte ; comparaison explicite « égale à »).
- Option « Créer automatiquement des sous-dossiers selon un paramètre » (facultative) et sélection du second paramètre.
- Aperçu du nombre de feuilles trouvées et des sous-dossiers qui seraient créés avant confirmation.

Exemple : dossier `A5000 Carnet de repérages DEP`, filtre `Carnet = A5000`, sous-dossiers par `Sous-carnet` : A / B / C. Les paramètres et valeurs sont choisis par l'utilisateur : ne jamais déduire les groupes du préfixe du numéro de feuille.

## 2. Contrat de recalcul

- Au lancement d'Export et sur action « Actualiser », relire les feuilles Revit courantes et reconstruire la liste des correspondances.
- Une nouvelle feuille qui satisfait la règle entre alors automatiquement dans le dossier approprié ; un changement de valeur peut la déplacer ou la retirer de **ce dossier dynamique uniquement**.
- Aucun événement Revit permanent en arrière-plan pour la V1 ; la mise à jour est automatique lors de l'ouverture/actualisation, avant l'aperçu et avant la publication pour éviter de publier une liste périmée.
- Identifier les feuilles par `UniqueId` ; ne jamais écrire les paramètres ni la structure du navigateur de Revit.
- En cas de paramètre supprimé, de lecture impossible ou de documents indisponibles, conserver la dernière configuration, signaler un état non résolu et **bloquer la publication dynamique**, plutôt que traiter le résultat vide comme une suppression.
- Les feuilles sans valeur de regroupement ont un comportement explicite : placer dans un sous-dossier « Sans valeur » (configurable ultérieurement), sans les perdre silencieusement.
- Ne jamais déplacer, renommer ou effacer les dossiers manuels adjacents pendant le recalcul.

## 3. Conversion en manuel

Action explicite « Rendre ce dossier manuel » avec confirmation.

- Résoudre le périmètre une dernière fois, puis **figer** les feuilles (et les sous-dossiers générés) en structure manuelle persistante.
- Conserver les identifiants des dossiers, l'ordre existant, les réglages PDF/DWG hérités et les surcharges.
- La conversion est unidirectionnelle dans la V1 ; retransformer un dossier manuel en automatique nécessite la définition d'une nouvelle règle et un aperçu.
- Après conversion, une nouvelle feuille Revit correspondant aux anciens critères n'est plus ajoutée.
- Ne pas modifier le navigateur Revit.

## 4. Stockage et intégrité

Le repository historique utilise le schéma JSON 8, avec `PublicationFolder` et `PublicationSet`. Le modèle `PublicationSource` possède déjà les modes `MANUAL`, `PARAMETER`, `TEMPORARY` et `DYNAMIC`, mais la résolution persistante actuelle repose sur une liste de feuilles sauvegardées.

Proposition : ajouter aux dossiers automatiques un objet de règle dédié, versionné, décrivant le mode dynamique, l'identité stable des paramètres (BuiltInParameter / GUID partagé lorsque disponible, nom de secours), les valeurs exactes, le regroupement et le statut de conversion. Garder les `items` sérialisés comme *snapshot de secours*, pas comme source d'autorité pendant le mode dynamique.

Toute modification du JSON doit être compatible avec les anciens dossiers et préserver les champs inconnus nécessaires à la future PR #30 (révisions/verrouillage). Si le schéma change, prévoir migration testée, sauvegarde préalable et rejet sûr d'un fichier de version future, sans écrasement.

**Interdiction :** écriture automatique du JSON uniquement parce que les feuilles Revit ont changé, sans mutation métier explicite. Calculer un modèle effectif en mémoire, avec persistance contrôlée. En mode collaboratif futur, utiliser le repository sûr et sa révision optimiste.

## 5. Intégration navigateur Revit

Deux modes distincts :

1. **Règle par paramètres choisis** : indépendante de la règle d'organisation active du navigateur Revit.
2. **Reprendre l'organisation actuelle du navigateur Revit** (option ultérieure / faisabilité API) : `BrowserOrganization.GetCurrentBrowserOrganizationForSheets(document)` et `GetFolderItems(sheet.Id)` existent en Revit 2025 et exposent les niveaux d'organisation et les identifiants de paramètres. Vérifier filtres, ordre, niveaux sans valeur et éventuels paramètres calculés dans Revit avant d'annoncer une copie fidèle.

Ne pas présenter le mode 1 comme une synchronisation exacte de l'organisation affichée dans Revit.

## 6. Tests de recette

- DYN-01 : dossier filtré par paramètre/valeur et ajout initial de toutes les feuilles correspondantes.
- DYN-02 : créer une nouvelle feuille correspondante dans Revit ; rouvrir Export ou Actualiser ; elle apparaît automatiquement.
- DYN-03 : changer la valeur principale d'une feuille ; elle quitte le dossier concerné, sans être supprimée du RVT ou d'un dossier manuel.
- DYN-04 : sous-dossiers construits à partir d'un second paramètre, y compris nouvelle valeur de groupe.
- DYN-05 : renommer/renuméroter une feuille ; conserver identité et montrer les libellés courants.
- DYN-06 : figer le dossier en manuel ; les feuilles et les réglages sont conservés ; nouvelles feuilles non ajoutées.
- DYN-07 : tester paramètres homonymes, vides, absents ; ne pas publier silencieusement des feuilles incorrectes.
- DYN-08 : aucun changement du navigateur de projet Revit.
- DYN-09 : compatibilité et non-régression des anciens JSON / dossiers manuels / ordre / héritage / PDF-DWG.
- DYN-10 : fermeture/réouverture, aperçu et publication identiques au périmètre dynamique résolu.
- DYN-11 : tester le maintien des champs de concurrence lorsqu'un backend partagé est activé ultérieurement.

**Recette Revit : aucune exécution confirmée à ce stade.** Ne pas fusionner la PR avant validation réelle d'un dossier automatique, de son regroupement, de son actualisation et de sa conversion en manuel.
