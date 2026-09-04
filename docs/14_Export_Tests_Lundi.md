# Export — Checklist de tests Revit 2025.4

**Projet :** Outils TAA  
**Module :** Export  
**Étape :** 07 — Historique et `MODIFIED_ONLY`  
**Environnement cible :** Revit 2025.4 / pyRevit 5.x  
**Date prévue :** lundi

## Consignes

- Effectuer les tests dans Revit 2025.4 / pyRevit 5.x.
- Ne pas modifier le code pendant la campagne de tests.
- Pour chaque test, noter `OK`, `KO` ou `NON TESTÉ`.
- En cas d'erreur, copier le message IronPython complet.
- Si possible, conserver une capture d'écran pour les erreurs UI.
- Un test `KO` doit être signalé avec le contexte précis.

Format recommandé : `TEST-01 : OK` ou `TEST-02 : KO` suivi du message exact.

---

# 1. Lancement et interface

## TEST-01 — Ouverture Export
Ouvrir Revit 2025.4 puis `Outils TAA > Export`.

**Attendu :** la fenêtre Export s'ouvre sans erreur IronPython/WPF.

## TEST-02 — Arborescence
Vérifier `Dossier > Carnet > Mise en page`.

**Attendu :** aucun doublon et uniquement les mises en page du projet courant.

## TEST-03 — Création d'un dossier
Créer un dossier, fermer puis rouvrir Export.

**Attendu :** le dossier est conservé.

---

# 2. Gestion des carnets

## TEST-04 — Créer un carnet dans un dossier
Sélectionner un dossier, créer un carnet et ajouter plusieurs feuilles.

**Attendu :** le carnet apparaît dans le dossier sélectionné, pas dans `Général`.

## TEST-05 — Persistance du carnet
Fermer puis rouvrir Export.

**Attendu :** le carnet et ses feuilles sont conservés.

## TEST-06 — Carnet par paramètre
Créer un carnet basé sur un paramètre, par exemple `Sous-titre`.

**Attendu :** le mode `PARAMETER` est conservé après réouverture.

## TEST-07 — Filtrage par projet
Ouvrir un autre projet Revit.

**Attendu :** les carnets d'un autre projet ne sont pas considérés comme appartenant au projet courant.

---

# 3. Organisation et glisser-déposer

## TEST-08 — Déplacer un carnet vers un dossier
Glisser un carnet vers un autre dossier.

**Attendu :** le carnet change de dossier.

## TEST-09 — Réordonner les carnets
Créer A, B, C ; déplacer C avant A ; fermer et rouvrir Export.

**Attendu :** ordre `C, A, B`, conservé après réouverture.

## TEST-10 — Sélection multiple Ctrl
Sélectionner plusieurs carnets avec `Ctrl + clic`.

**Attendu :** les carnets sélectionnés sont visuellement identifiés.

## TEST-11 — Déplacement groupé
Sélectionner plusieurs carnets et les déplacer vers un dossier.

**Attendu :** tous sont déplacés et leur ordre relatif est conservé.

## TEST-12 — Insertion groupée
Sélectionner plusieurs carnets et les déposer avant un carnet cible.

**Attendu :** ils sont insérés avant la cible dans le même ordre.

## TEST-13 — Ordre des mises en page
Mettre volontairement les feuilles dans l'ordre `A103, A101, A102`.

**Attendu :** Export conserve cet ordre et ne trie pas automatiquement par numéro ou nom.

---

# 4. Réglages PDF / DWG

## TEST-14 — PDF
Tester PDF activé/désactivé et PDF combiné/séparé.

**Attendu :** les réglages sont respectés.

## TEST-15 — DWG
Tester DWG activé/désactivé et DWG combiné/séparé.

**Attendu :** les réglages sont respectés.

## TEST-16 — True Color
Activer True Color et produire un DWG.

**Attendu :** vérifier le résultat réel du DWG.

## TEST-17 — Destination persistante
Définir une destination, fermer puis rouvrir Export.

**Attendu :** destination conservée.

---

# 5. Héritage

## TEST-18 — Héritage dossier → carnet
Définir au dossier `PDF = oui`, `DWG = non`, puis sélectionner un carnet.

**Attendu :** le carnet récupère ces valeurs par héritage.

## TEST-19 — Surcharge carnet
Modifier uniquement PDF au niveau carnet.

**Attendu :** PDF provient du carnet et DWG reste hérité du dossier.

## TEST-20 — Ne pas casser l'héritage
Modifier un autre paramètre du carnet.

**Attendu :** les paramètres non modifiés restent hérités.

## TEST-21 — Retour à l'héritage
Cliquer `Revenir à l'héritage du dossier`.

**Attendu :** les surcharges locales disparaissent et les valeurs redeviennent héritées.

---

# 6. Nommage

## TEST-22 — Variables simples
Tester `{carnet}`, `{numero}`, `{nom}`, `{nom_complet}`, `{projet}`, `{date}`, `{indice}`, `{dossier}`.

**Attendu :** les valeurs produites sont correctes.

## TEST-23 — Paramètre Revit
Tester `{parametre:Sous-titre}`.

**Attendu :** la valeur réelle du paramètre est utilisée.

## TEST-24 — Caractères interdits
Tester un nom contenant `/ \\ : * ? " < > |`.

**Attendu :** le nom est correctement sécurisé pour Windows.

---

# 7. Prévisualisation

## TEST-25 — Prévisualisation carnet
Sélectionner un carnet puis cliquer `Publier`.

**Attendu :** aucun export immédiat ; la fenêtre de prévisualisation apparaît.

## TEST-26 — Informations de prévisualisation
Vérifier carnet, mise en page, format, mode, nom final, destination et statut.

**Attendu :** toutes les informations sont cohérentes.

## TEST-27 — Feuille manquante
Utiliser un carnet contenant une référence devenue introuvable.

**Attendu :** la feuille est signalée comme manquante.

## TEST-28 — Collision
Publier une fois puis relancer exactement la même publication.

**Attendu :** les fichiers existants sont signalés comme collisions.

## TEST-29 — Annulation
Ouvrir la prévisualisation puis cliquer `Annuler`.

**Attendu :** aucun nouveau fichier n'est produit.

## TEST-30 — Confirmation
Confirmer une publication.

**Attendu :** les fichiers sont réellement produits.

---

# 8. Publication d'un dossier

## TEST-31 — Publication récursive
Créer une structure `DCE/Plans/Carnet A`, `DCE/Plans/Carnet B`, `DCE/Coupes/Carnet C`, sélectionner `DCE` puis publier.

**Attendu :** A + B + C sont pris en compte.

## TEST-32 — Destinations différentes
Configurer une destination différente pour A, B et C puis publier DCE.

**Attendu :** chaque carnet utilise sa propre destination.

## TEST-33 — Rapport global
Publier un dossier contenant plusieurs carnets.

**Attendu :** un rapport global permet d'identifier le résultat de chaque carnet, feuille et livrable.

---

# 9. Étape 07 — Historique / MODIFIED_ONLY

## TEST-34 — Première publication
Créer un carnet jamais publié, activer `MODIFIED_ONLY` et publier.

**Attendu :** toutes les feuilles sont `NEW` et toutes sont publiées.

## TEST-35 — Deuxième publication sans modification
Ne rien modifier et relancer `MODIFIED_ONLY`.

**Attendu cible :** les feuilles sont `UNCHANGED` et aucune feuille inutile n'est proposée.

## TEST-36 — Une seule feuille modifiée
Modifier une seule mise en page puis relancer Export.

**Attendu :** la feuille modifiée est `MODIFIED`, les autres `UNCHANGED`, et `MODIFIED_ONLY` ne retient que la feuille modifiée.

## TEST-37 — Nouvelle feuille
Ajouter une nouvelle mise en page au carnet puis relancer `MODIFIED_ONLY`.

**Attendu :** la nouvelle feuille est `NEW` et est publiée.

## TEST-38 — État impossible à comparer
Si possible, observer une feuille dont l'état ne peut pas être déterminé.

**Attendu :** état `UNKNOWN` et republication par sécurité.

## TEST-39 — Publication échouée
Si possible, provoquer une erreur de publication puis relancer `MODIFIED_ONLY`.

**Attendu :** l'historique ne doit pas enregistrer une publication comme réussie si elle a échoué.

## TEST-40 — PDF séparé + MODIFIED_ONLY
PDF séparé ; modifier une seule feuille ; publier en `MODIFIED_ONLY`.

**Attendu :** seul le livrable de la feuille modifiée est produit.

## TEST-41 — DWG séparé + MODIFIED_ONLY
DWG séparé ; modifier une seule feuille ; publier en `MODIFIED_ONLY`.

**Attendu :** seul le livrable de la feuille modifiée est produit.

## TEST-42 — PDF combiné + MODIFIED_ONLY
PDF combiné ; modifier une seule feuille ; publier en `MODIFIED_ONLY`.

**Attendu :** observer précisément le comportement et vérifier que le livrable combiné reste cohérent. Noter le résultat pour validation de la règle métier.

## TEST-43 — Publication multiple + MODIFIED_ONLY
Créer A, B et C. Modifier une seule feuille dans B puis publier le dossier en `MODIFIED_ONLY`.

**Attendu :** A = aucune feuille ; B = seule la feuille modifiée ; C = aucune feuille.

---

# 10. Test anti-régression du workflow complet

## TEST-44 — Workflow complet
Effectuer : `Ouverture Export → Dossier → Carnet → Mise en page → Retour dossier → Gestionnaire carnet → Création carnet → Réglages → Profil → Prévisualisation → Publication → Rapport`.

**Attendu :** aucun `AttributeError`, aucune erreur WPF/IronPython, aucun handler manquant et aucun blocage inattendu.

Ce test vise notamment les régressions liées aux handlers `Publish_Click`, `_set_no_selection`, `_update_selection_info`, `_make_sheet_target`, `FolderChanged`, `BrowseOutput_Click`, `DeleteNode_Click` et `OpenCarnetManager_Click`.

---

# 11. Nouveaux tests — intégration complète Stage 07

Ces tests complètent la première campagne afin de couvrir les éléments Stage 07 restant à intégrer : interface, persistance du réglage, prévisualisation, publication simple/multiple, historique et rapport.

## TEST-45 — Contrôle MODIFIED_ONLY dans l'interface

Sélectionner un carnet et rechercher le contrôle permettant d'activer/désactiver `MODIFIED_ONLY`.

**Attendu :** le contrôle est visible, compréhensible et son état est correctement reflété dans l'interface.

## TEST-46 — Persistance du réglage MODIFIED_ONLY

Activer `MODIFIED_ONLY`, fermer Export puis le rouvrir.

**Attendu :** le réglage reste activé pour le carnet concerné et ne modifie pas involontairement les autres carnets.

## TEST-47 — Prévisualisation filtrée

Publier un carnet déjà historisé après avoir modifié une seule feuille, avec `MODIFIED_ONLY` actif.

**Attendu :** la prévisualisation ne présente comme publiables que les feuilles `NEW`, `MODIFIED` ou `UNKNOWN` selon la règle de sécurité ; les feuilles `UNCHANGED` sont clairement identifiées ou exclues de la publication.

## TEST-48 — Publication simple filtrée

Depuis un carnet, publier avec `MODIFIED_ONLY` après modification d'une seule feuille.

**Attendu :** seule la feuille devant être republiée est effectivement envoyée au moteur de publication.

## TEST-49 — Publication multiple filtrée

Sélectionner un dossier contenant plusieurs carnets ; ne modifier qu'une feuille d'un seul carnet ; publier le dossier avec `MODIFIED_ONLY`.

**Attendu :** les carnets sans changement ne génèrent pas de publication inutile et seul le contenu nécessaire du carnet modifié est publié.

## TEST-50 — Historique après publication réussie

Effectuer une publication réussie puis fermer/réouvrir Export et relancer l'analyse du carnet.

**Attendu :** l'historique contient la publication réussie, la date, les livrables produits et l'état par feuille. La publication suivante sans modification doit reconnaître les feuilles comme `UNCHANGED`.

## TEST-51 — Affichage de l'état dans l'interface et le rapport

Utiliser un carnet contenant des feuilles `NEW`, `MODIFIED` et `UNCHANGED`, puis consulter la prévisualisation et le rapport.

**Attendu :** les états sont compréhensibles et cohérents entre l'interface, la prévisualisation et le rapport.

---

# Tableau de résultats

```text
TEST-01 :
TEST-02 :
TEST-03 :
TEST-04 :
TEST-05 :
TEST-06 :
TEST-07 :
TEST-08 :
TEST-09 :
TEST-10 :
TEST-11 :
TEST-12 :
TEST-13 :
TEST-14 :
TEST-15 :
TEST-16 :
TEST-17 :
TEST-18 :
TEST-19 :
TEST-20 :
TEST-21 :
TEST-22 :
TEST-23 :
TEST-24 :
TEST-25 :
TEST-26 :
TEST-27 :
TEST-28 :
TEST-29 :
TEST-30 :
TEST-31 :
TEST-32 :
TEST-33 :
TEST-34 :
TEST-35 :
TEST-36 :
TEST-37 :
TEST-38 :
TEST-39 :
TEST-40 :
TEST-41 :
TEST-42 :
TEST-43 :
TEST-44 :
TEST-45 :
TEST-46 :
TEST-47 :
TEST-48 :
TEST-49 :
TEST-50 :
TEST-51 :
```

# Notes / erreurs

```text
____________________________________________________________

____________________________________________________________

____________________________________________________________

____________________________________________________________

____________________________________________________________
```
