# Calculs des pièces — Campagne de validation Revit 2025.4

**Statut :** Fonctionnel validé — revalidation visuelle du patch UI/icône requise  
**Branche :** `feature/calculs-pieces-migration`  
**Environnement :** Revit 2025.4 / pyRevit 5.x  
**Prérequis :** travailler sur une copie d'un projet ou une maquette de test.

---

## 1. Objectif

Cette campagne valide les comportements impossibles à certifier hors Revit :

- chargement pyRevit ;
- WPF réel ;
- API Revit ;
- paramètres ;
- unités ;
- écriture ;
- transaction / Undo ;
- persistance.

La CI hors Revit a déjà validé **71 tests**. Le 1er octobre 2026, l'utilisateur a confirmé que les tests fonctionnels Revit étaient OK avant le correctif visuel demandé (icône du ruban + compacité de la fenêtre).

---

## 2. Préparation de la maquette de test

Préparer au minimum trois pièces appartenant au même groupe.

Exemple :

| Pièce | Groupe | Surface / valeur source |
|---|---|---:|
| P01 | A | 20 |
| P02 | A | 15 |
| P03 | A | 10 |

Prévoir un paramètre destination modifiable commun aux trois pièces.

Résultat de référence :

```text
20 + 15 + 10 = 45
```

Après calcul, les trois pièces du groupe A doivent recevoir 45 dans le paramètre destination compatible.

Si possible, préparer également :

- une pièce d'un autre niveau ou non visible dans la vue active ;
- une pièce avec `Area == 0` ou non placée ;
- une pièce avec source vide dans un groupe ayant d'autres valeurs valides ;
- un groupe B ;
- un paramètre destination readonly ;
- un paramètre partagé ;
- deux paramètres homonymes distincts ;
- un paramètre Surface et un paramètre Volume pour le test d'incompatibilité.

---

## 3. TEST-CALC-01 — Chargement du bouton

1. Recharger pyRevit.
2. Ouvrir l'onglet Outils TAA.
3. Ouvrir le panneau Calculs.
4. Vérifier le bouton **Calculs des pièces**.
5. Cliquer sur le bouton.

### Attendu

- aucune erreur Python ;
- aucune erreur XAML ;
- la fenêtre **Calculs des pièces** s'ouvre.

---

## 4. TEST-CALC-02 — Interface

Vérifier :

- titre Calculs des pièces ;
- texte **Toutes les pièces du projet** ;
- absence de choix Vue active / Toutes les pièces / Pièces sélectionnées ;
- filtre optionnel ;
- Regrouper par ;
- Additionner ;
- Paramètre destination ;
- unité de sortie ;
- état / progression ;
- bouton Calculer en action principale ;
- interface lisible sans défilement horizontal ;
- sur un écran 1920 × 1080, tous les réglages courants sont accessibles sans défilement vertical ;
- le ScrollViewer ne devient utile qu'après réduction importante de la fenêtre ;
- l'icône **Plan 2×2 + somme Σ** apparaît dans le ruban.

### Attendu

L'interface reste cohérente avec le design Outils TAA. L'accent des fenêtres utilise le TAA Orange UI `#FD8B5A`, tandis que l'icône du ruban peut utiliser la référence de marque `#FA641F`.

---

## 5. TEST-CALC-03 — Collecte du projet entier

1. Se placer dans une vue où certaines pièces du projet ne sont pas visibles.
2. Ouvrir Calculs des pièces.
3. Noter le compteur de pièces.

### Attendu

Le compteur correspond au périmètre du projet, pas à la seule vue active.

Une pièce hors vue active ne doit pas disparaître pour cette raison.

---

## 6. TEST-CALC-04 — Pièce à surface nulle / non placée

Vérifier qu'une pièce à surface nulle ou non placée n'est pas supprimée silencieusement du périmètre source.

### Attendu

Elle peut ensuite être ignorée si les paramètres nécessaires au calcul sont invalides, mais cette exclusion doit apparaître dans le comportement/rapport et ne doit pas provenir d'un filtre de vue ou de `Area == 0`.

---

## 7. TEST-CALC-05 — Listes de paramètres

Vérifier les listes :

### Regrouper par

Doit proposer les paramètres exploitables des pièces.

### Additionner

Doit proposer les paramètres numériques.

### Paramètre destination

Doit proposer les types d'écriture pris en charge et éviter les destinations globalement readonly.

### Attendu

Les listes sont cohérentes avec les paramètres réels du projet.

---

## 8. TEST-CALC-06 — Calcul nominal

Configurer :

```text
Groupe = A
20 + 15 + 10
Destination = paramètre compatible
```

Cliquer Calculer puis confirmer.

### Attendu

- total = 45 ;
- P01 = 45 ;
- P02 = 45 ;
- P03 = 45 ;
- le rapport annonce trois écritures réussies ;
- aucune erreur.

---

## 9. TEST-CALC-07 — Une source vide dans un groupe valide

Créer :

```text
P01 groupe A = 20
P02 groupe A = 15
P03 groupe A = source vide
```

### Attendu

Le total du groupe vaut 35.

P03 appartient toujours au groupe et doit recevoir 35 dans la destination, même si sa propre valeur source n'a pas contribué à la somme.

Le rapport peut signaler que P03 a été ignorée comme contributeur au calcul.

---

## 10. TEST-CALC-08 — Plusieurs groupes

Exemple :

```text
A : 20 + 15 = 35
B : 10 + 5 = 15
```

### Attendu

Chaque pièce reçoit uniquement le total de son groupe.

---

## 11. TEST-CALC-09 — Filtre métier

1. Choisir un paramètre de filtre.
2. Saisir une valeur exacte.
3. Lancer le calcul.

### Attendu

Seules les pièces correspondant au filtre sont utilisées.

Revenir à **Aucun filtre** doit rétablir toutes les pièces du projet.

---

## 12. TEST-CALC-10 — Annulation avant écriture

1. Configurer un calcul valide.
2. Cliquer Calculer.
3. Dans la confirmation, choisir Non.

### Attendu

Aucun paramètre Revit n'est modifié.

---

## 13. TEST-CALC-11 — Undo / transaction

1. Effectuer un calcul valide.
2. Vérifier les valeurs.
3. Utiliser Annuler dans Revit.

### Attendu

Une opération **Outils TAA - Calculs des pièces** est annulable et les valeurs précédentes sont restaurées.

---

## 14. TEST-CALC-12 — Destination absente ou readonly

Tester une configuration où une destination n'est pas disponible ou n'est pas modifiable sur au moins une pièce.

### Attendu

- aucune erreur silencieuse ;
- les écritures valides peuvent continuer lorsque le cas est local ;
- les échecs sont indiqués dans le rapport ;
- aucune écriture n'est déclarée réussie si elle a été annulée par rollback.

---

## 15. TEST-CALC-13 — Paramètre partagé

Utiliser un paramètre partagé comme source, groupe ou destination.

Fermer puis rouvrir l'outil.

### Attendu

Le paramètre est résolu correctement, notamment via son GUID lorsqu'il est disponible.

---

## 16. TEST-CALC-14 — Paramètres homonymes

Si la maquette permet d'avoir deux paramètres portant le même nom mais des identités différentes :

### Attendu

- ils ne sont pas fusionnés silencieusement ;
- l'interface permet de les distinguer ;
- une résolution ambiguë uniquement par nom doit être refusée plutôt que choisir arbitrairement.

---

## 17. TEST-CALC-15 — Compatibilité Surface / Surface

Choisir :

```text
Source : Surface
Destination : paramètre Surface modifiable
```

### Attendu

Le calcul est accepté et la valeur Revit écrite reste correcte.

---

## 18. TEST-CALC-16 — Incompatibilité Surface / Volume

Choisir :

```text
Source : Surface
Destination : Volume
```

### Attendu

Le calcul est bloqué avant transaction avec un message de compatibilité compréhensible.

---

## 19. TEST-CALC-17 — Unités

Avec une source Double mesurable :

1. vérifier les unités proposées ;
2. vérifier le libellé dans la langue de Revit ;
3. tester Automatique ;
4. si pertinent, tester une unité explicite sur une sortie String ou Integer.

### Attendu

- seules des unités compatibles sont proposées ;
- aucune conversion basée sur le nom du paramètre ;
- les résultats écrits/affichés sont cohérents.

---

## 20. TEST-CALC-18 — Persistance

1. Choisir groupe, source, destination, filtre et éventuellement unité.
2. Fermer l'outil.
3. Rouvrir l'outil.

### Attendu

Les choix encore valides sont restaurés.

Aucun objet Revit périmé ne doit être sérialisé.

---

## 21. TEST-CALC-19 — Anciennes préférences RoomTools

À exécuter uniquement sur un poste possédant encore :

```text
%APPDATA%/RoomTools/settings.json
```

### Attendu

- les anciens noms de paramètres peuvent être repris lorsqu'ils correspondent sans ambiguïté ;
- l'ancien tag manuel d'unité ne doit pas être converti artificiellement vers une unité Revit incompatible.

---

## 22. TEST-CALC-20 — Rapport

Après un calcul comportant au moins un avertissement ou une anomalie :

### Attendu

Le rapport affiche de manière compréhensible :

- nombre de succès ;
- nombre d'échecs ;
- pièces ignorées ;
- avertissements ;
- erreur de transaction si applicable.

---

## 23. Critère de validation

La campagne est considérée validée lorsque :

- TEST-CALC-01 à TEST-CALC-20 sont rejoués selon les cas disponibles ;
- aucun blocage majeur ne subsiste ;
- les écarts constatés sont soit corrigés, soit documentés explicitement ;
- les tests automatisés restent verts après les corrections ;
- la PR de migration peut sortir du mode Draft uniquement après cette validation.

Pour chaque test, noter :

```text
OK
KO
NON APPLICABLE
Observation / capture / erreur éventuelle
```


---

## 24. Revalidation après correctif visuel du 1er octobre 2026

Les tests fonctionnels ont été déclarés OK avant ce correctif.

Après mise à jour de la branche, il suffit de rejouer prioritairement :

### VISUAL-CALC-01 — Ruban

- recharger pyRevit ;
- vérifier que le bouton Calculs des pièces affiche le pictogramme validé **Plan 2×2 + somme Σ** ;
- vérifier sa lisibilité en taille de ruban.

### VISUAL-CALC-02 — Fenêtre 1920 × 1080

- ouvrir la fenêtre sur un écran 1920 × 1080 ;
- vérifier que Source, Filtre, Calcul, Unité de sortie, État, Fermer et Calculer sont visibles sans scroll vertical ;
- vérifier que la taille des textes reste confortable ;
- réduire fortement la hauteur de la fenêtre et vérifier que le ScrollViewer prend alors le relais.

Si ces deux contrôles sont OK et qu'aucune régression fonctionnelle n'est constatée, la campagne peut être considérée close.
