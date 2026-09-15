# Export — Persistance par projet Revit

## Objectif

La configuration de publication Export est propre au projet Revit actif. Les dossiers, carnets et réglages persistants d'un projet ne doivent jamais apparaître dans un autre projet.

## Identité du projet

Export utilise un identifiant propre aux Outils TAA, stocké directement dans le document Revit avec **Extensible Storage / DataStorage**.

Pour un document non enregistré, l'identité embarquée est également liée au hash de l'instance `Document` pendant la session :

```text
GUID|Document.GetHashCode()
```

Cela évite qu'un nouveau projet créé à partir d'un gabarit contenant déjà une identité Outils TAA réutilise accidentellement l'identité du gabarit. Un document non enregistré dont le GUID embarqué provient d'une autre instance reçoit donc une nouvelle identité.

Une fois le document enregistré, le GUID devient l'identité persistante du projet et n'est plus remplacé à cause du changement de hash d'instance.

Cette identité est prioritaire sur :

- le nom du projet (`Projet1`, etc.) ;
- `ProjectInformation.UniqueId` ;
- un `ElementId` ;
- le hash d'une instance `Document` comme identité persistante ;
- le chemin du fichier comme identité définitive.

## Règle de sécurité du stockage

Le fichier JSON externe est une donnée **scopée au projet**. Il contient obligatoirement `project_identity` dès sa première écriture métier.

Un fichier existant qui appartient à un autre projet, ou qui ne possède pas de `project_identity`, n'est jamais adopté silencieusement par le projet courant. Export repart alors sur une structure neuve contenant uniquement `Général`.

Cette règle empêche une ancienne persistance globale ou une ancienne clé de session de faire réapparaître `DCE`, `APD`, `DPC`, etc. dans un nouveau `Projet1`.

## Gabarits Revit

Un gabarit peut contenir des données Extensible Storage copiées dans les nouveaux projets. L'identité Outils TAA ne doit donc pas être considérée comme valide pour un nouveau document non enregistré uniquement parce qu'un GUID est présent.

Le contrôle est :

```text
Document non enregistré
        ↓
GUID embarqué présent ?
        ↓
hash du GUID == hash du Document ?
        ├── oui → conserver l'identité de la session
        └── non → générer une nouvelle identité
```

Ainsi, deux nouveaux projets `Projet1` issus du même gabarit ne partagent pas leur stockage Export.

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

1. Créer un nouveau projet Revit B à partir du même gabarit éventuel.
2. Ouvrir Export.
3. Vérifier que **seul `Général`** apparaît.
4. Fermer puis relancer Revit.
5. Créer/ouvrir le projet B et vérifier à nouveau que seul `Général` apparaît.

### Retour au projet A

1. Ouvrir le projet A.
2. Ouvrir Export.
3. Vérifier que `DCE`, `APD` et le carnet du projet A sont restaurés.

### Cas complémentaire — deux `Projet1` dans la même session

1. Créer deux nouveaux projets non enregistrés avec le même nom `Projet1`.
2. Ouvrir Export sur chacun.
3. Créer un dossier uniquement dans le premier.
4. Basculer sur le second et ouvrir Export.
5. Vérifier que le dossier du premier n'apparaît pas.

Ce scénario valide la séparation entre deux projets, y compris lorsque l'identité Extensible Storage d'un gabarit est héritée, et couvre `BUG-EXPORT-017`.
