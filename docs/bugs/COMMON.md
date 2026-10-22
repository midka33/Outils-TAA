# Registre des bugs — Commun

**Statut :** Référence active de développement et de non-régression  
**Cible :** Revit 2025.4 / pyRevit 5.x

Bugs transversaux communs à plusieurs modules.

Avant toute modification liée à ce périmètre, lire les fiches applicables
et exécuter les tests anti-régression cités.

---

### BUG-COMMON-002 — Fichiers temporaires suivis dans les archives source

**Symptôme :** l’archive de `main` au commit `44503dff` contient deux fichiers
`docs/09_Export_Project_Persistence*.tmp`.

**Cause racine :** ces fichiers temporaires étaient suivis par Git ; un simple
nettoyage du répertoire de travail ou une exclusion locale ne les retire pas
des archives d’une release.

**Correction :** suppression des deux fichiers suivis et ajout d’exclusions
pour temporaires et caches Python dans `.gitignore`.

**Règle préventive :** vérifier le contenu de l’archive du commit à publier,
pas seulement l’état du répertoire de travail.

**Anti-régression :** le workflow Export inspecte `git archive HEAD` et bloque
les suffixes temporaires/cache, modèles Revit, dessins DWG et MSI ; contrôle
négatif sur le commit d’origine et positif sur l’arbre préparé.

---

### BUG-COMMON-003 — Les nouveaux modules d'annotation échouent avec (Name)

**Symptôme :** Cotation et Étiquetage automatiques affichent chacun
\`0 annotation(s) créée(s)\` pour deux plans comportant respectivement 40 et
44 pièces. Le rapport signale
\`hors groupe : annulé sans annotation isolée (Name)\`.

**Cause racine :** l'adaptateur initial lisait directement \`room.Name\` et
\`room.Level.Name\` en assemblant les entrées du moteur Plans de vente.
IronPython peut lever \`AttributeError: Name\` sur ces éléments Revit.
Les services Plans de vente, eux, utilisaient déjà des accesseurs robustes.

**Correction :** lecture du nom de pièce via
\`get_Parameter(BuiltInParameter.ROOM_NAME).AsString()\`, du numéro via
\`ROOM_NUMBER\`, et des noms d'éléments via \`Element.Name.GetValue\`.
Validation de niveau avec ce même accesseur. Isolation transactionnelle par
pièce hors groupe et ajout du traceback complet au rapport.

**Règle préventive :** aucun accès direct à \`Room.Name\`,
\`GroupType.Name\`, \`Level.Name\` ni aux noms de styles Revit sans
l'accesseur robuste. Tout nouveau module reprenant un service validé
doit tester aussi sa couche d'adaptation et non seulement les imports.

**Anti-régression :** \`tests/annotations/test_annotation_runtime_mocks.py\`
simule une pièce dont \`Name\` lève \`AttributeError("Name")\` ;
\`tests/annotations/test_annotation_beta_contract.py\` vérifie les scripts.
Recette utilisateur dans Revit 2025.4 obligatoire.
