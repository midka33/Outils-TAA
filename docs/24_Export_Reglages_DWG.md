# Export — configurations DWG, vues et liens

Statut : implémenté et testé hors Revit ; **recette Revit 2025.4 en attente**.
Branche : `feature/export-dwg-settings`, issue de main v1.0.2 (`b2b6da4`).
Aucune validation du rendu, des XRefs ou de l'ouverture native dans Revit n'est revendiquée.

## Trois réglages distincts

| Réglage | Rôle | Valeur par défaut |
|---|---|---|
| Configuration DWG Revit | Base native : calques, couleurs, lignes, hachures, textes, unités, coordonnées, solides, version et autres propriétés | Vide : nouvelles options Revit |
| Sortie : Par feuille / Lot Revit | Organisation des appels, noms/préfixes et destinations TAA | Par feuille |
| Fusionner les vues et les liens dans le DWG | `DWGExportOptions.MergedViews`, indépendant du mode de sortie | Activé |

`SEPARATE` reste un appel par feuille, avec son nom et le sous-dossier de carnet
si demandé. `COMBINED`, désormais libellé **Lot Revit**, reste un appel avec tous
les identifiants et le préfixe du carnet, dans le dossier parent. Ces valeurs
persistées, les modèles de noms, les chemins, l'ordre et les périmètres ne changent pas.
Le lot natif ne fusionne pas plusieurs feuilles indépendantes en un seul DWG.

## Analyse API et limites de vérification

L'explication Autodesk *MergedViews and Exporting to a Single DWG* précise le cas
d'une feuille contenant plusieurs vues : `False` produit des DWG de vues référencés
par le DWG de feuille ; `True` intègre les vues au DWG de feuille. Cette explication
lève l'ambiguïté de l'ancien commentaire « fusion via XRefs » du service TAA.
Le réglage est associé à l'option native des vues sur feuilles et liens ; les liens
Revit imbriqués doivent être vérifiés par la recette sur les projets de l'agence.

Le guide API Autodesk **2025** confirme que `PostCommand` ne s'exécute qu'après
le retour du contexte API. La référence publique Autodesk du membre
`ExportOptionsExportSetupsDWGOrDXF` consultée est celle de **2026**, pas une preuve
binaire de 2025.4. La référence API Autodesk spécifique 2025.4 n'était pas accessible
pendant cette analyse. Le code vérifie donc réellement l'existence du membre dans
l'API chargée, son identifiant et `CanPostCommand` avant fermeture, puis à nouveau
avant publication de la commande. Le test Revit 2025.4 reste obligatoire.

Sources primaires consultées :

- [Autodesk : MergedViews et export d'une feuille](https://blog.autodesk.io/mergedviews-and-exporting-to-a-single-dwg/)
- [Autodesk : option native vues/liens et MergedViews](https://blog.autodesk.io/api-access-to-export-views-on-sheets-and-links-as-external-references-settings-in-exporting-revit-fi/)
- [Guide API Revit 2025 : Commands](https://help.autodesk.com/cloudhelp/2025/CHS/Revit-API/files/Revit_API_Developers_Guide/Advanced_Topics/Revit_API_Revit_API_Developers_Guide_Advanced_Topics_Commands_html.html)
- [Référence Autodesk 2026 : PostableCommand](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/f6ccdc1b-6ac3-9c49-d0bb-8a7d1877eab0.htm)
- [Autodesk : images exportées comme ressources externes](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Is-it-possible-to-export-to-DWG-file-without-images-as-references-from-Revit.html)
- [pyRevit : get_envvar / set_envvar](https://docs.pyrevitlabs.io/reference/pyrevit/script/)

Les images raster ne sont pas incorporées par cette case. D'autres ressources
peuvent rester externes. Il n'existe donc aucune promesse « un seul fichier » ou
« aucun XRef garanti ». Les tests Python vérifient les contrats et les valeurs
transmises, pas le contenu d'un fichier produit par Revit.

## Audit des surcharges du preset

La liste provient toujours de `DWGExportOptions.GetPredefinedSetupNames(document)`.
Le preset sélectionné est chargé par `GetPredefinedOptions(document, setup_name)`.
Un nom absent ou supprimé reste visible et mémorisé ; un export avec ce nom échoue
explicitement, sans repli silencieux sur d'autres réglages.

| Propriété DWG | Surcharge TAA après chargement |
|---|---|
| `MergedViews` | Toujours : valeur effective de `dwg_merge_views` |
| `Colors` | Seulement si « Forcer les couleurs vraies » est coché : `ExportColorMode.TrueColor` |
| Toute autre propriété et tables du preset | Conservées |

Le comportement historique True Color reste activé par défaut, pour ne pas modifier
les couleurs livrées. Décocher la case préserve exactement `Colors` du preset,
y compris un choix de couleurs par vue. `TrueColor` n'est pas remplacé par
`TrueColorPerView`. L'ancien `except: pass` a été supprimé : une surcharge de couleurs
impossible devient une erreur DWG dans le rapport. Sans preset, Revit fournit ses
options par défaut, auxquelles s'appliquent les mêmes surcharges explicites.
Aucun preset natif enregistré n'est modifié par l'export ; seule l'instance des
options retournée à TAA est adaptée.

## Héritage et compatibilité

`dwg_merge_views` est un champ de `PublicationSettings.FIELDS` :
`None` = hériter, `True` = fusion, `False` = références externes.
Le résolveur existant traite défaut → profil → dossiers ancêtres → carnet.
Les profils intégrés et nouveaux profils appliquent True par défaut ; un profil
personnalisé peut enregistrer False. Dans l'UI actuelle, appliquer un profil copie
ses valeurs dans le carnet sélectionné, comme pour les autres options (pas de liaison
permanente au profil).

La migration est additive, à la lecture : un ancien JSON sans ce champ donne
`None` dans le dossier/carnet/profil lu, puis True au niveau du défaut résolu.
Aucune réécriture n'a lieu à l'ouverture et aucune surcharge héritée n'est figée.
Les autres champs restent inchangés ; le schéma des carnets reste 6 et celui des
profils 1, compatibles avec un champ nullable supplémentaire. Enregistrer un carnet
sérialise ce champ comme les autres, y compris sa valeur `null` d'héritage.

**Changement volontaire pour les anciens exports séparés :** auparavant, le mode
séparé imposait `MergedViews=False`. Sans nouveau champ, il résout maintenant True,
conformément au défaut demandé. Décocher la case rétablit les références externes
sans modifier noms, destinations ou mode de sortie.

## Fenêtre native et retour

1. Le bouton engrenage vérifie le membre API, `LookupPostableCommandId` et
   `CanPostCommand`. Une incompatibilité laisse Export ouvert avec un diagnostic.
2. Il sauvegarde l'état temporaire : carnets non persistants, ordre de leurs feuilles,
   réglages, sélection multiple, élément actif et branches dépliées. Si cette
   sauvegarde échoue, Export reste ouvert et l'erreur est affichée/journalisée.
3. Il ferme réellement la fenêtre Export (`Close`). Le smartbutton récupère la main
   **après** `ShowDialog`, appelle `UIApplication.PostCommand`, puis termine.
4. Revit peut alors ouvrir sa fenêtre native. Aucun second dialogue Export n'est
   ouvert pendant cette commande ; aucun timer, abonnement Idling ou remplacement
   `AddInCommandBinding.Executed` n'est utilisé.
5. Fermer les réglages Revit, puis **rouvrir Export avec le bouton du ruban**.
   Les configurations sont relues automatiquement et l'état temporaire est restauré.
   Le bouton **Actualiser** permet aussi une relecture explicite de la liste.

Le cache est un JSON temporaire, avec un simple chemin dans les envvars pyRevit.
Sa clé associe le stockage du projet, le processus Revit et le document ouvert.
Aucun objet Revit/WPF n'est conservé entre exécutions. Le fichier est supprimé après
restauration réussie. Ce cache sert uniquement à l'aller-retour DWG ; les carnets
persistants continuent d'utiliser le dépôt normal. Un arrêt de Revit avant le retour
peut laisser un fichier temporaire orphelin ; il n'est pas restauré dans une autre
session. Les carnets temporaires ne deviennent pas des carnets permanents.

`CanPostCommand` vérifie la possibilité de poster, pas la disponibilité future de
la commande. Une exception immédiate est affichée/journalisée. Si Revit refuse
ultérieurement l'exécution, il peut ne fournir aucun retour API : rouvrir Export
récupère tout de même la sélection et permet de réessayer. La réouverture manuelle
évite de présumer la fin du dialogue natif par un événement non fiable.

## Workflow réellement actif et rapport

`Export.smartbutton/script.py` installe `_install_stage07_hooks` : publication
simple/multiple via `_publish_targets_stage07`, dossier via
`_preview_then_publish_folder_stage07` et `PublicationBatchService`.
Les hooks actifs, l'intégration de secours et `CarnetController` transmettent tous
`dwg_merge_views` jusqu'à `PublicationService` puis `DwgExportService.export`.
`Document.Export` reçoit toujours une `List[ElementId]` .NET ordonnée.

L'aperçu indique la configuration et l'état des références. Un lot de plusieurs feuilles
est annoncé comme un **préfixe** dont Revit détermine les noms finaux. Le rapport
conserve sa structure ; sa ligne de lot de plusieurs feuilles présente le répertoire réel
au lieu d'un chemin DWG supposé. Aucun faux fichier n'est ajouté à `files` ou à
l'historique pour ce lot. Les annexes ne sont pas inventoriées : un avertissement
précise qu'elles peuvent subsister, sans affirmer leur présence effective.
Les vérifications de collisions ne peuvent pas couvrir les suffixes natifs et annexes.

Les appels PDF, leur moteur, leur nommage et le plan de progression 0–100 % ne sont
pas modifiés. Recette détaillée : [25_Export_Recette_DWG.md](25_Export_Recette_DWG.md).
