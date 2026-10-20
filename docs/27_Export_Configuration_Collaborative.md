# Export V1.2 — Configuration collaborative par projet

**Issue :** #25  
**Branche :** `feature/export-v1.2-collaborative-config`  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x / Windows / partage SMB  
**Statut :** résolveur central/UNC et couche JSON sûre implémentés hors Revit ; CarnetRepository pas encore raccordé  
**Principe :** aucune écriture dans le modèle Revit pour sauvegarder la configuration partagée.

## 1. État actuel constaté

Le module Export utilise aujourd'hui une persistance **locale par poste** :

```text
%APPDATA%\Outils-TAA\Export\Projects\<project_key>_carnets.json
```

Le chemin est calculé dans le smartbutton Export, puis transmis à
`CarnetRepository`.

Le repository conserve actuellement le **schéma JSON 8** et contient notamment :

- `project_identity` ;
- dossiers `PublicationFolder` ;
- dossiers de publication historiques `PublicationSet` ;
- ordre d'arborescence ;
- références de feuilles via `UniqueId` ;
- réglages PDF/DWG et héritage.

### Identité projet actuelle

`project_identity.py` utilise actuellement en priorité une identité embarquée
dans le document Revit par **Extensible Storage**. Si nécessaire,
`ensure_project_identity()` crée un `DataStorage` dans une transaction Revit.

Cette stratégie reste utile pour la persistance locale historique, mais elle ne
doit pas être requise pour la configuration collaborative : deux utilisateurs
ouvrant des copies locales du même central doivent trouver la même configuration
sans avoir à modifier ou synchroniser le modèle.

### Écriture JSON actuelle

`CarnetRepository._write()` utilise aujourd'hui :

1. écriture dans `.tmp` ;
2. suppression de l'ancien JSON ;
3. renommage du temporaire.

Cette séquence laisse une fenêtre sans fichier cible et n'apporte ni verrou SMB
ni contrôle de révision. Deux utilisateurs peuvent donc écraser silencieusement
les changements de l'autre.

### Données volontairement séparées

Ne sont pas incluses dans le futur JSON partagé V1.2 :

- historique `MODIFIED_ONLY`, actuellement local et encore hors workflow stable ;
- cache temporaire d'aller-retour vers les réglages DWG ;
- livrables PDF/DWG ;
- profils intégrés du code.

Les **profils personnalisés globaux utilisateur** restent locaux dans un premier
temps. Les références aux presets DWG Revit et les réglages appliqués aux dossiers
restent, eux, dans la configuration projet partagée.

## 2. Chemin partagé cible

Pour un modèle central Revit sur partage Windows :

```text
\\SERVEUR\PROJETS\PROJET_ARCHITECTURE\
  Projet_Central.rvt
  OutilsTAA\
    export.json
    export.lock
    backups\
      export_YYYYMMDD_HHMMSS_revision-N.json
```

Le nom `export.lock` peut rester présent sur disque : le verrou réel est le
**handle exclusif SMB**, pas l'existence du fichier.

## 3. Résolution du modèle central

### 3.1 Modèle partagé

Ordre de résolution :

1. vérifier que le document est partagé ;
2. appeler `Document.GetWorksharingCentralModelPath()` ;
3. convertir avec
   `ModelPathUtils.ConvertModelPathToUserVisiblePath()` ;
4. normaliser le chemin Windows ;
5. lorsqu'une lettre de lecteur réseau est utilisée, tenter de la convertir en
   UNC depuis `HKCU\Network\<lettre>\RemotePath` ;
6. dériver `<dossier central>\OutilsTAA\export.json`.

Une copie locale du même central conduit donc au même chemin partagé.

### 3.2 Central inaccessible

Si le central est résolu mais que le dossier réseau est indisponible ou interdit :

- ne jamais modifier `export.json` ;
- afficher clairement **Mode local de secours** ;
- utiliser la persistance locale existante ;
- ne jamais recopier automatiquement cette configuration locale vers le serveur
  lors du retour réseau.

### 3.3 Projet non partagé / détaché / non enregistré

Pour V1.2 :

- projet non partagé enregistré : mode local ;
- projet non enregistré : mode local ;
- projet détaché sans central exploitable : mode local ;
- ACC / BIM 360 : hors périmètre.

Aucune écriture automatique à côté d'un fichier Revit non partagé n'est prévue
dans cette version.

## 4. Identité du stockage partagé

L'identité collaborative ne doit pas dépendre de l'identité Extensible Storage
locale.

Le JSON partagé porte une identité basée sur le chemin central canonique :

```json
{
  "schema_version": 8,
  "storage_revision": 12,
  "project_identity": "CENTRAL:\\\\SERVEUR\\PROJETS\\PROJET_ARCHITECTURE\\Projet_Central.rvt"
}
```

Le chemin est normalisé sans tenir compte de la casse Windows.

Une différence d'identité bloque l'adoption silencieuse du JSON.

## 5. Révision et conflits

Le schéma métier reste **8**. La V1.2 ajoute des métadonnées compatibles avec les
anciens lecteurs :

- `storage_revision` : entier croissant ;
- `last_write_id` : GUID d'écriture ;
- `last_write_utc` : date informative ;
- `last_write_user` et `last_write_machine` : diagnostic uniquement.

Chaque instance du repository mémorise la révision qu'elle a chargée.

Avant toute mutation :

1. acquérir le verrou exclusif ;
2. relire le JSON partagé ;
3. comparer sa révision à la révision connue ;
4. si elle diffère : lever un conflit explicite ;
5. sinon appliquer la mutation sur la dernière version lue ;
6. incrémenter `storage_revision` ;
7. écrire de façon résistante ;
8. mettre à jour la révision connue ;
9. libérer le verrou.

La stratégie est volontairement conservatrice : toute modification externe depuis
la dernière lecture oblige l'utilisateur à **Actualiser** avant d'enregistrer.

## 6. Verrouillage SMB

Le verrou doit utiliser un handle de fichier exclusif Windows/.NET :

```text
FileMode.OpenOrCreate
FileAccess.ReadWrite
FileShare.None
```

sur `export.lock`.

Avantages :

- exclusivité gérée par le serveur SMB ;
- fermeture automatique du handle en cas de crash du processus ;
- pas de suppression automatique d'un prétendu verrou « périmé » ;
- le fichier `export.lock` peut rester présent sans bloquer les sessions futures.

Acquisition :

- essais courts pendant une durée limitée ;
- au-delà du délai : message « configuration en cours de modification par un
  autre utilisateur » ;
- aucune écriture sans verrou.

## 7. Écriture résistante et sauvegardes

Sous verrou :

1. écrire un fichier temporaire **dans le même dossier** que `export.json` ;
2. fermer et forcer le flush ;
3. relire et valider le JSON temporaire ;
4. si `export.json` existe :
   utiliser `System.IO.File.Replace(temp, export.json, backup)` ;
5. pour une première création :
   utiliser `File.Move(temp, export.json)` ;
6. ne jamais faire `remove(export.json) + rename(temp)` ;
7. conserver les **20 sauvegardes les plus récentes**.

Si `File.Replace` échoue, l'ancien fichier doit rester intact et l'opération est
signalée en erreur.

## 8. Migration locale vers partagé

Lorsqu'aucun `export.json` partagé n'existe :

- détecter la configuration locale du projet courant ;
- si elle contient autre chose que la structure vide, proposer :
  **Importer ma configuration locale dans la configuration partagée ?**
- l'import est explicite ;
- le fichier local n'est pas supprimé ;
- l'identité est convertie vers l'identité centrale ;
- la création partagée passe par verrou + sauvegarde + validation ;
- si une configuration partagée apparaît entre-temps, l'import est abandonné et
  un conflit est signalé.

Aucune fusion automatique de deux configurations divergentes n'est prévue.

## 9. Interface

La fenêtre Export doit afficher en permanence un état de stockage compact :

```text
Configuration : Partagée
\\SERVEUR\...\OutilsTAA\export.json
Révision : 12
[ Actualiser ]
```

ou :

```text
Configuration : Locale — serveur indisponible
[ Réessayer / Actualiser ]
```

### Actualiser

Le bouton doit :

- relire le stockage ;
- reconstruire l'arborescence ;
- conserver autant que possible la sélection par identifiants persistants ;
- recharger les réglages ;
- mettre à jour la révision connue ;
- ne publier ni modifier le modèle Revit.

### Conflit

Si une mutation détecte une autre révision :

- annuler la mutation ;
- afficher un message explicite ;
- proposer de recharger ;
- ne jamais effectuer de merge silencieux.

## 10. Refactorisation du repository

Le repository actuel possède plusieurs méthodes écrivant directement après leur
propre `_read()`.

La V1.2 doit centraliser toutes les mutations dans un chemin unique, par exemple :

```text
_mutate(callback)
   ↓
acquire lock
   ↓
read latest
   ↓
check revision
   ↓
callback(data)
   ↓
validate
   ↓
increment revision
   ↓
atomic replace
   ↓
release lock
```

Doivent passer par ce contrat :

- sauvegarde dossier ;
- sauvegarde dossier de publication ;
- suppression ;
- déplacement simple / multiple ;
- déplacement de feuilles ;
- toute future mutation du JSON partagé.

## 11. Services proposés

### `project_storage_resolver.py`

Responsable de :

- central Revit ;
- canonisation UNC ;
- mode partagé/local ;
- chemins `export.json`, verrou et backups ;
- diagnostic d'accessibilité.

### `shared_json_storage.py`

Responsable de :

- verrou SMB ;
- lecture validée ;
- révision ;
- remplacement atomique ;
- backups ;
- erreurs typées de concurrence/réseau/corruption.

### `carnet_repository.py`

Reste responsable du modèle métier schéma 8 et de ses mutations, mais délègue le
stockage physique à la couche précédente.

Cette séparation permet de tester la concurrence sans Revit.

## 12. Erreurs typées attendues

Prévoir au minimum :

- `StorageUnavailableError`
- `StorageAccessDeniedError`
- `StorageCorruptedError`
- `StorageLockTimeoutError`
- `ConcurrentModificationError`
- `ProjectIdentityMismatchError`

L'UI traduit ces erreurs en messages métier sans masquer la cause technique dans
les logs.

## 13. Tests hors Revit

À ajouter avant raccordement UI :

- central -> chemin partagé ;
- copie locale -> même chemin partagé ;
- lecteur mappé -> UNC lorsque la correspondance Windows existe ;
- non partagé -> local ;
- JSON schéma 8 historique sans révision -> révision initiale compatible ;
- verrou exclusif entre deux writers ;
- writer A puis writer B sur révision obsolète -> conflit ;
- deux mutations séquentielles du même repository -> révisions croissantes ;
- JSON temporaire invalide -> aucun remplacement ;
- échec de `File.Replace` -> ancien JSON conservé ;
- backup créé et rotation à 20 ;
- JSON corrompu -> erreur, pas de réinitialisation silencieuse ;
- identité projet différente -> blocage ;
- migration locale explicite ;
- apparition concurrente d'un JSON partagé pendant migration -> conflit ;
- mode local de secours sans resynchronisation automatique.

## 14. Recette Revit multi-postes

La recette COLLAB-01 à COLLAB-11 de l'issue #25 reste le contrat d'acceptation.

La fusion dans `main` est interdite avant validation réelle avec **deux postes
distincts** ouverts sur le même central Windows.

## 15. Décisions issues de l'Étape 0

- Le stockage collaboratif se fonde sur le **chemin central**, pas sur une
  transaction Extensible Storage.
- Le comportement historique local est conservé comme secours.
- Le verrouillage utilisera un **handle SMB exclusif**, et non un fichier verrou
  dont l'existence ferait foi.
- La concurrence utilisera une **révision globale optimiste**.
- Les écritures utiliseront `File.Replace` et des backups dans le même partage.
- Le schéma métier reste **8** ; les nouvelles métadonnées sont additionnelles.
- Les profils personnalisés globaux utilisateur et l'historique de publication
  restent locaux dans cette première V1.2.
- Aucun basculement local -> partagé ne provoque d'upload automatique.

## 16. Ordre de réalisation

1. ✅ Résolveur de stockage + tests.
2. ✅ Couche JSON sûre + verrou/révision/backups + tests.
3. ⏳ Refactorisation de `CarnetRepository` autour de `_mutate`.
4. ⏳ Raccordement du smartbutton sans transaction Revit en mode partagé.
5. ⏳ UI Partagé / Local + Actualiser + conflits.
6. ⏳ Migration locale explicite.
7. ⏳ Recette automatique complète.
8. ⏳ Recette Revit réelle sur deux postes.
9. ⏳ Documentation et préparation d'une release ultérieure.

### Implémentation réalisée

- `project_storage_resolver.py` : résolution du central, copie locale vers le
  même stockage, canonisation UNC des lecteurs mappés et fallback local.
- `shared_json_storage.py` : verrou SMB de production par handle .NET exclusif
  `FileShare.None`, révision optimiste, détection de conflit, écriture
  temporaire validée, `File.Replace`, backups et rotation.
- tests hors Revit : concurrence de deux writers, révision obsolète, refresh,
  verrou, corruption, identité projet, préservation du fichier existant en cas
  d'échec, création et rotation des backups.

La couche n'est volontairement **pas encore utilisée par l'UI** : le prochain
travail consiste à faire passer toutes les mutations de `CarnetRepository` par
ce contrat unique avant le raccordement du smartbutton.
