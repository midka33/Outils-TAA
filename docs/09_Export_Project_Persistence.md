# Export — Persistance par projet Revit

## Objectif

La configuration de publication Export est propre au projet Revit actif. Les dossiers, carnets et réglages persistants d'un projet ne doivent jamais apparaître dans un autre projet.

## Identité du projet

Export utilise un identifiant propre aux Outils TAA, stocké directement dans le document Revit avec **Extensible Storage / DataStorage**.

Cette identité est prioritaire sur :

- le nom du projet (`Projet1`, etc.) ;
- `ProjectInformation.UniqueId` ;
- un `ElementId` ;
- le hash d'une instance `Document` ;
- le chemin du fichier comme identité définitive.

Le GUID embarqué reste associé au document lors des opérations suivantes :

- projet non enregistré ;
- `Enregistrer` ;
- `Enregistrer sous` ;
- fermeture puis réouverture de Revit.

## Stockage externe

Les fichiers de persistance Export sont stockés sous :

```text
%APPDATA%\Outils-TAA\Export\Projects\
```

Le nom du fichier est dérivé de l'identité embarquée du projet.

Le JSON contient également :

```json
{
  "project_identity": "EMBEDDED:<guid>"
}
```

Le dépôt `CarnetRepository` refuse de charger un fichier dont `project_identity` ne correspond pas au document courant.

## Dossiers

Les dossiers sont des données persistantes **du projet**, et non des données globales de l'utilisateur.

Un nouveau projet sans configuration existante commence donc avec :

```text
Général
```

Les dossiers tels que `DCE`, `APD`, `DPC`, etc. ne sont visibles que s'ils ont été créés ou migrés pour le projet courant.

## Migration

Lorsqu'une ancienne version utilisait une clé de stockage différente, Export tente de migrer le fichier correspondant au document courant vers la nouvelle clé embarquée.

La migration ne doit jamais sélectionner arbitrairement un fichier appartenant à un autre projet.

## Test fonctionnel obligatoire

### Projet A

1. Créer un projet Revit A.
2. Ouvrir Export.
3. Créer `DCE`, `APD` et un carnet.
4. Fermer Revit.

### Projet B

1. Créer un nouveau projet Revit.
2. Ouvrir Export.
3. Vérifier que seuls les éléments propres au projet B sont affichés, au minimum `Général`.
4. Fermer et relancer Revit.
5. Rouvrir Export et vérifier le même résultat.

### Retour au projet A

1. Enregistrer ou rouvrir le projet A.
2. Ouvrir Export.
3. Vérifier que `DCE`, `APD` et le carnet du projet A sont restaurés.

Cette procédure constitue le scénario anti-régression de `BUG-EXPORT-017` et de `TEST-25`.
