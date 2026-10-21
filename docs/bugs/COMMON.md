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