# Outils TAA — Instructions obligatoires pour les IA et agents de développement

**Statut :** Règles d'exécution obligatoires  
**Périmètre :** Tous les modules et tous les fichiers du repository  
**Cible :** Revit 2025.4 / pyRevit 5.x

---

## 1. Règle fondamentale

Ce fichier constitue le point d'entrée des consignes destinées à toute IA, agent de code ou assistant intervenant sur le repository **Outils-TAA**.

Une IA qui intervient sur ce repository doit considérer les règles ci-dessous comme des **contraintes de développement**, et non comme de simples recommandations.

La documentation fonctionnelle et technique reste la référence détaillée. En cas de doute, consulter les documents concernés avant de modifier le code.

---

## 2. AVANT TOUTE MODIFICATION DE CODE — OBLIGATOIRE

Avant de créer, modifier, supprimer ou déplacer du code :

1. Lire `docs/11_BUGS_Prevention_Registry.md`.
2. Rechercher les bugs et règles préventives concernant le module ou la zone de code modifiée.
3. Lire la documentation technique ou fonctionnelle associée si elle existe.
4. Identifier les risques de régression liés à la modification.
5. Prévoir le test ou contrôle permettant de vérifier la modification.

**Il est interdit de modifier le code avant cette vérification.**

---

## 3. TOUT CHANGEMENT DE COMPORTEMENT DOIT ÊTRE DOCUMENTÉ — OBLIGATOIRE

Lorsqu'une modification change, ajoute, supprime ou précise le comportement d'un outil, la documentation de cet outil doit être mise à jour dans le même travail.

Sont notamment concernés :

- ajout d'une fonctionnalité ;
- suppression d'une fonctionnalité ;
- modification d'un comportement existant ;
- modification d'une règle métier ;
- modification du parcours utilisateur ;
- modification des paramètres ou options disponibles ;
- modification des formats d'entrée ou de sortie ;
- modification des règles de publication/export ;
- modification de l'organisation ou du fonctionnement interne lorsqu'elle a un impact pour l'utilisateur ou pour les autres développeurs.

### Procédure obligatoire

```text
Modification de comportement
↓
Identifier la documentation de référence de l'outil
↓
Modifier le code
↓
Mettre à jour la documentation correspondante
↓
Mettre à jour les tests si nécessaire
↓
Vérifier la cohérence code ↔ documentation
↓
Commit
```

Pour les outils disposant d'une documentation dédiée, celle-ci constitue la référence fonctionnelle à maintenir à jour. Par exemple :

- **Export** → `docs/09_Export.md` ;
- **Calculs des pièces** → `docs/10_RoomCalculator.md` ;
- règles transversales → documentation générale `docs/`.

**Il est interdit de considérer une modification fonctionnelle comme terminée si le comportement documenté n'a pas été mis à jour.**

Une modification purement interne sans impact fonctionnel ou comportemental ne nécessite pas systématiquement une modification de la documentation utilisateur, mais doit être documentée dans la documentation technique lorsque son architecture, son contrat ou sa maintenance sont concernés.

---

## 4. TRAITEMENT OBLIGATOIRE D'UN BUG

Lorsqu'un bug, une exception, une erreur de comportement ou une régression est rencontré :

```text
Bug
↓
Reproduction
↓
Recherche dans le registre
↓
Cause racine
↓
Correction
↓
Test anti-régression
↓
Mise à jour du registre
↓
Mise à jour de la documentation de l'outil si le comportement change
↓
Vérification finale
↓
Commit
```

### 4.1 Bug déjà connu

Si le problème correspond à un bug déjà présent dans `docs/11_BUGS_Prevention_Registry.md` :

- appliquer la règle préventive existante ;
- vérifier que la correction ne réintroduit pas le problème ;
- exécuter le test anti-régression associé ;
- compléter le registre si le nouveau cas apporte une information utile.

### 4.2 Nouveau bug significatif

Tout nouveau bug significatif doit être ajouté **avant de considérer la correction terminée**.

L'entrée doit obligatoirement contenir :

- identifiant unique ;
- symptôme ;
- cause racine ;
- correction ;
- règle préventive ;
- test / contrôle anti-régression.

Les identifiants suivent les conventions du registre :

- `BUG-EXPORT-XXX`
- `BUG-ROOMCALC-XXX`
- `BUG-COMMON-XXX`
- `BUG-UI-XXX`
- `BUG-REVIT-XXX`
- `BUG-TEST-XXX`

**Une correction de bug n'est jamais considérée comme terminée tant que sa capitalisation dans le registre et son test anti-régression ne sont pas réalisés, lorsque ces éléments sont applicables.**

---

## 5. AVANT CHAQUE COMMIT — OBLIGATOIRE

Avant tout commit contenant une modification ou création de code :

1. Relire `docs/11_BUGS_Prevention_Registry.md`.
2. Vérifier les règles préventives applicables.
3. Vérifier les tests anti-régression concernés.
4. Vérifier que tout nouveau bug significatif rencontré pendant le travail est capitalisé.
5. Vérifier que toute modification de comportement a entraîné la mise à jour de la documentation de l'outil concerné.
6. Vérifier que la documentation technique impactée a été mise à jour si nécessaire.
7. Vérifier que les changements restent compatibles avec Revit 2025.4 / pyRevit 5.x.

**Un commit ne doit pas être considéré comme prêt si cette checklist n'est pas satisfaite.**

---

## 6. RÈGLE DE PROPRIÉTÉ DES HANDLERS ET SERVICES

Chaque comportement doit avoir un propriétaire canonique.

En particulier :

- les handlers d'une fenêtre WPF doivent avoir un propriétaire clairement identifié ;
- une couche d'intégration ne doit pas recréer silencieusement des handlers déjà présents ;
- les couches de compatibilité ne doivent pas multiplier les alias sans nécessité ;
- toute injection dynamique de méthode doit être documentée et testée.

Lorsqu'une refactorisation déplace une méthode, rechercher toutes ses références avant suppression ou remplacement.

---

## 7. RÈGLES TECHNIQUES CRITIQUES

Avant toute modification, vérifier notamment :

- API réellement disponible dans Revit 2025.4 ;
- membres et enums .NET réellement attendus ;
- compatibilité IronPython / pyRevit ;
- encodage UTF-8 des fichiers Python ;
- bindings et Attached Properties WPF ;
- références Revit persistantes (`UniqueId` plutôt qu'`ElementId` sérialisé) ;
- séparation entre configuration héritée et surcharge locale ;
- imports et risques de collision de modules ;
- comportement réel dans Revit lorsque la modification concerne WPF, Revit API ou export.

Les règles détaillées et les cas historiques se trouvent dans le registre des bugs.

---

## 8. TESTS ET LIMITES DE L'ENVIRONNEMENT

Une validation statique ou un test Python hors Revit ne remplace pas un test dans l'environnement cible lorsqu'une fonctionnalité dépend de :

- Revit API ;
- WPF / .NET ;
- pyRevit ;
- moteur PDF Revit ;
- export DWG ;
- comportement graphique de Revit.

Si l'environnement Revit 2025.4 réel n'est pas disponible, l'IA doit le signaler explicitement et ne doit pas présenter une validation théorique comme un test Revit réel.

### 8.1 EXÉCUTION OBLIGATOIRE DES TESTS PYTEST AU RACCORDEMENT

Lorsqu'une fonctionnalité ou un Stage a été développé isolément et que des tests `pytest` ont été créés, leur simple présence dans `tests/` ne constitue **jamais** une validation.

Au moment du raccordement au reste du système, tous les tests `pytest` créés ou impactés doivent être **réellement exécutés** avant de considérer le raccordement comme terminé.

Le cycle obligatoire est :

```text
Développement isolé
        ↓
Tests pytest créés
        ↓
Raccordement au système existant
        ↓
Exécution réelle des pytest concernés
        ↓
Correction des échecs éventuels
        ↓
Nouvelle exécution
        ↓
Tests pytest validés
        ↓
Tests Revit / pyRevit concernés
        ↓
Validation du Stage
```

Checklist obligatoire lors de chaque raccordement :

- [ ] Identifier tous les tests `pytest` créés ou impactés.
- [ ] Exécuter réellement ces tests dans l'environnement Python disponible.
- [ ] Vérifier le résultat complet des tests.
- [ ] Corriger tous les échecs avant de poursuivre.
- [ ] Relancer les tests après correction.
- [ ] Après raccordement à Revit/pyRevit, exécuter les tests Revit concernés.
- [ ] Pour PDF/DWG/WPF/Revit API, compléter par les tests fonctionnels dans Revit 2025.4.
- [ ] Ne jamais présenter un test non exécuté comme « réussi ».

> **Un test pytest créé mais jamais exécuté est un test préparé, pas un test validé.**

Cette règle s'applique notamment aux tests préparés pendant les développements Stage 01 à Stage 08 et aux futurs raccordements de l'outil Export.

---

## 9. RÉFÉRENCES À CONSULTER

| Besoin | Référence |
|---|---|
| Vision et philosophie | `docs/01_Vision_Philosophie.md` |
| Architecture générale | `docs/02_Architecture_Generale.md` |
| Standards de développement | `docs/03_Standards_Developpement.md` |
| UI / WPF | `docs/04_UI_Guidelines.md` |
| API interne | `docs/05_Internal_API.md` |
| Développement avec IA | `docs/06_AI_Development_Guide.md` |
| Workflow Git | `docs/07_Git_Workflow.md` |
| Tests | `docs/08_Testing.md` |
| Module Export | `docs/09_Export.md` |
| RoomCalculator / Calculs des pièces | `docs/10_RoomCalculator.md` |
| Registre des bugs | `docs/11_BUGS_Prevention_Registry.md` |
| Publication multiple Export | `docs/12_Export_Stage06_Publication_Multiple.md` |

---

## 10. PRIORITÉ DES RÈGLES

En cas de conflit apparent :

1. contraintes de sécurité et de plateforme ;
2. contraintes explicites du projet ;
3. architecture et standards du repository ;
4. documentation fonctionnelle et technique ;
5. préférences d'implémentation.

Une IA ne doit pas contourner une règle documentée simplement parce qu'une autre implémentation semble plus rapide.

---

## 11. CHECKLIST RAPIDE POUR UNE IA

Avant de répondre « terminé » :

- [ ] `docs/11_BUGS_Prevention_Registry.md` consulté.
- [ ] Règles applicables identifiées.
- [ ] Cause racine identifiée en cas de bug.
- [ ] Correction réalisée.
- [ ] Test anti-régression réalisé ou défini.
- [ ] Nouveau bug capitalisé si nécessaire.
- [ ] Documentation de l'outil mise à jour si le comportement a changé.
- [ ] Documentation technique mise à jour si nécessaire.
- [ ] Code et documentation cohérents.
- [ ] Compatibilité Revit 2025.4 / pyRevit 5.x vérifiée.
- [ ] Aucun handler ou service existant supprimé sans vérifier ses références.
- [ ] Pour tout raccordement : tous les `pytest` concernés ont été exécutés réellement et leur résultat vérifié.
- [ ] Commit seulement après validation de cette checklist.

**Cette checklist est obligatoire pour tout agent IA intervenant sur Outils-TAA.**
