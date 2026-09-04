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

## 3. TRAITEMENT OBLIGATOIRE D'UN BUG

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
Vérification finale
↓
Commit
```

### 3.1 Bug déjà connu

Si le problème correspond à un bug déjà présent dans `docs/11_BUGS_Prevention_Registry.md` :

- appliquer la règle préventive existante ;
- vérifier que la correction ne réintroduit pas le problème ;
- exécuter le test anti-régression associé ;
- compléter le registre si le nouveau cas apporte une information utile.

### 3.2 Nouveau bug significatif

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

## 4. AVANT CHAQUE COMMIT — OBLIGATOIRE

Avant tout commit contenant une modification ou création de code :

1. Relire `docs/11_BUGS_Prevention_Registry.md`.
2. Vérifier les règles préventives applicables.
3. Vérifier les tests anti-régression concernés.
4. Vérifier que tout nouveau bug significatif rencontré pendant le travail est capitalisé.
5. Vérifier que la documentation impactée a été mise à jour.
6. Vérifier que les changements restent compatibles avec Revit 2025.4 / pyRevit 5.x.

**Un commit ne doit pas être considéré comme prêt si cette checklist n'est pas satisfaite.**

---

## 5. RÈGLE DE PROPRIÉTÉ DES HANDLERS ET SERVICES

Chaque comportement doit avoir un propriétaire canonique.

En particulier :

- les handlers d'une fenêtre WPF doivent avoir un propriétaire clairement identifié ;
- une couche d'intégration ne doit pas recréer silencieusement des handlers déjà présents ;
- les couches de compatibilité ne doivent pas multiplier les alias sans nécessité ;
- toute injection dynamique de méthode doit être documentée et testée.

Lorsqu'une refactorisation déplace une méthode, rechercher toutes ses références avant suppression ou remplacement.

---

## 6. RÈGLES TECHNIQUES CRITIQUES

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

## 7. TESTS ET LIMITES DE L'ENVIRONNEMENT

Une validation statique ou un test Python hors Revit ne remplace pas un test dans l'environnement cible lorsqu'une fonctionnalité dépend de :

- Revit API ;
- WPF / .NET ;
- pyRevit ;
- moteur PDF Revit ;
- export DWG ;
- comportement graphique de Revit.

Si l'environnement Revit 2025.4 réel n'est pas disponible, l'IA doit le signaler explicitement et ne doit pas présenter une validation théorique comme un test Revit réel.

---

## 8. RÉFÉRENCES À CONSULTER

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

## 9. PRIORITÉ DES RÈGLES

En cas de conflit apparent :

1. contraintes de sécurité et de plateforme ;
2. contraintes explicites du projet ;
3. architecture et standards du repository ;
4. documentation fonctionnelle et technique ;
5. préférences d'implémentation.

Une IA ne doit pas contourner une règle documentée simplement parce qu'une autre implémentation semble plus rapide.

---

## 10. CHECKLIST RAPIDE POUR UNE IA

Avant de répondre « terminé » :

- [ ] `docs/11_BUGS_Prevention_Registry.md` consulté.
- [ ] Règles applicables identifiées.
- [ ] Cause racine identifiée en cas de bug.
- [ ] Correction réalisée.
- [ ] Test anti-régression réalisé ou défini.
- [ ] Nouveau bug capitalisé si nécessaire.
- [ ] Documentation mise à jour si nécessaire.
- [ ] Compatibilité Revit 2025.4 / pyRevit 5.x vérifiée.
- [ ] Aucun handler ou service existant supprimé sans vérifier ses références.
- [ ] Commit seulement après validation de cette checklist.

**Cette checklist est obligatoire pour tout agent IA intervenant sur Outils-TAA.**
