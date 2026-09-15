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

## Règle de sécurité du stockage

Le fichier JSON externe est une donnée **scopée au projet**. Il contient obligatoirement `project_identity` dès sa première écriture métier.

Un fichier existant qui appartient à un autre projet, ou qui ne possède pas encore de `project_identity`, n'est jamais adopté silencieusement par le projet courant. Export repart alors sur une structure neuve contenant uniquement `Général`.

Cette règle empêche une ancienne persistance globale ou une ancienne clé de session de faire réapparaître `DCE`, `APD`, `DPC`, etc. dans un nouveau `Projet1`.

## Migration des anciennes données

Une ancienne persistance peut être migrée automatiquement uniquement lorsqu'elle est rattachable sans ambiguïté au document courant, c'est-à-dire lorsque le document possède un chemin de fichier ou un chemin de modèle central correspondant à l'ancienne clé.

Les anciennes données provenant d'un document non enregistré ne sont **jamais** migrées automatiquement : leur attribution à un nouveau projet ne peut pas être déterminée de manière fiable.

## Dossiers

Les dossiers sont des données persistantes **du projet**, et non des données globales de l'utilisateur.

Un nouveau projet sans configuration existante commence donc avec :

```text
Général
```

Les dossiers tels que `DCE`, `APD`, `DPC`, etc. ne sont visibles que s'ils ont été créés ou migrés pour le projet courant.

## Test fonctionnel obligatoire — TEST-25

### Projet A

1. Créer un projet Revit A.
2. Ouvrir Export.
3. Créer `DCE`, `APD` et un carnet.
4. Fermer complètement Revit.

### Projet B

1. Créer un nouveau projet Revit B.
2. Ouvrir Export.
3. Vérifier que **seul `Général`** apparaît.
4. Fermer puis relancer Revit.
5. Rouvrir Export et vérifier à nouveau que seul `Général` apparaît.

### Retour au projet A

1. Ouvrir le projet A.
2. Ouvrir Export.
3. Vérifier que `DCE`, `APD` et le carnet du projet A sont restaurés.

Ce scénario valide la séparation entre deux projets et couvre `BUG-EXPORT-017`.
