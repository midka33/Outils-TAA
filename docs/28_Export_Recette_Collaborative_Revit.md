# Export V1.2 — Recette Revit collaborative multi-postes

**Issue :** #25  
**PR :** #30  
**Cible :** Autodesk Revit 2025.4 / pyRevit 5.x / Windows / SMB  
**Statut :** prête à exécuter — validation réelle sur deux postes requise avant fusion

Cette recette couvre uniquement les points qui ne peuvent pas être validés de
façon fiable par la CI hors Revit.

## 1. Préparation

Utiliser deux postes Windows distincts, nommés ci-dessous **Poste A** et
**Poste B**, avec deux utilisateurs Revit différents.

Conditions :

- même version Outils TAA issue de la PR #30 ;
- même modèle central Revit sur partage Windows ;
- chaque utilisateur ouvre sa propre copie locale du central ;
- droits lecture/écriture sur le dossier du central ;
- aucun `export.json` partagé préexistant pour COLLAB-07 ;
- conserver une copie d'une ancienne configuration locale sur Poste A pour le
  test de migration.

Le fichier partagé attendu est :

```text
<dossier du central>\OutilsTAA\export.json
```

## 2. COLLAB-01 — Même configuration à l'ouverture

1. Sur Poste A, ouvrir Export.
2. Créer une arborescence simple :
   - DCE
   - Plans
   - Coupes
3. Régler PDF + DWG sur un dossier.
4. Fermer Export.
5. Sur Poste B, ouvrir Export.

**Attendu :**

- `Configuration : Partagée` sur les deux postes ;
- même chemin de configuration ;
- même arborescence ;
- mêmes réglages PDF/DWG ;
- aucune synchronisation Revit nécessaire.

## 3. COLLAB-02 — Actualiser après une modification distante

1. Garder Export ouvert sur les deux postes.
2. Sur A, créer un dossier et déplacer plusieurs mises en page dedans.
3. Revenir sur la fenêtre Export de B.

**Attendu :**

- B signale qu'une version plus récente est disponible ;
- l'arbre n'est pas remplacé automatiquement ;
- après clic sur **Actualiser**, B retrouve exactement l'organisation de A ;
- B peut publier cette sélection.

## 4. COLLAB-03 — Dossier vide conservé

1. Sur A, créer un dossier avec sous-dossier et paramètres.
2. Retirer toutes les mises en page du dossier parent.
3. Sur B, Actualiser.

**Attendu :**

- le dossier vide existe toujours ;
- son sous-dossier reste présent ;
- ses paramètres sont conservés.

## 5. COLLAB-04 — Nommage DWG partagé

1. Sur A, activer PDF combiné.
2. Définir un nommage DWG indépendant, par exemple `{numero} {nom}`.
3. Sur B, Actualiser.

**Attendu :**

- B retrouve le même réglage ;
- le champ DWG reste indépendant ;
- aperçu et publication utilisent cette règle.

## 6. COLLAB-05 — Conflit de deux utilisateurs

1. A et B ouvrent Export sur la même révision.
2. A modifie un dossier et enregistre.
3. Sans Actualiser, B modifie à son tour le même état.

**Attendu :**

- l'enregistrement de B est refusé ;
- les données de A restent intactes ;
- B reçoit un message lui demandant d'Actualiser ;
- après Actualiser, B peut refaire sa modification.

## 7. COLLAB-06 — Panne réseau et corruption

### 6A — Réseau indisponible au démarrage

1. Rendre temporairement le partage inaccessible à B.
2. Ouvrir Export.

**Attendu :**

- `Configuration : Locale — serveur indisponible` ;
- bouton **Réessayer** ;
- aucune tentative d'écrasement du JSON serveur.

### 6B — Retour réseau

1. Rétablir le partage.
2. Cliquer **Réessayer**.

**Attendu :**

- retour en `Configuration : Partagée` ;
- aucune remontée automatique des données locales de secours.

### 6C — JSON corrompu

1. Sur une copie de test uniquement, rendre `export.json` invalide.
2. Ouvrir Export.

**Attendu :**

- ouverture collaborative bloquée avec message explicite ;
- aucun fallback local silencieux ;
- le fichier corrompu n'est pas remplacé.

## 8. COLLAB-07 — Migration locale initiale

1. Supprimer le `export.json` partagé de l'environnement de test.
2. Conserver sur Poste A une ancienne configuration locale non vide.
3. Ouvrir Export sur A.

**Attendu :**

- proposition explicite d'import ;
- résumé des données détectées ;
- si **Non**, aucun import et la proposition ne revient pas à chaque ouverture ;
- si **Oui**, création de la configuration partagée ;
- le fichier local reste intact.

Rejouer une fois avec B créant `export.json` pendant que A a la confirmation ouverte.

**Attendu :**

- import A annulé ;
- configuration B conservée ;
- aucune fusion automatique.

## 9. COLLAB-08 — Isolation entre projets

1. Ouvrir deux modèles centraux différents.
2. Créer des arborescences différentes.

**Attendu :**

- chemins `OutilsTAA\export.json` distincts ;
- aucune donnée d'un projet dans l'autre.

## 10. COLLAB-09 — Copie locale et central

1. Vérifier sur A et B le chemin affiché.
2. Les deux utilisateurs doivent être ouverts sur des copies locales différentes
   du même central.

**Attendu :**

- chemin partagé identique ;
- identité projet commune ;
- le chemin de la copie locale n'influence pas le stockage collaboratif.

Tester aussi :

- modèle non partagé ;
- modèle détaché.

**Attendu :** mode local.

## 11. COLLAB-10 — Non-régression publication

Sur au moins un poste, vérifier successivement :

- PDF combiné ;
- PDF séparé ;
- DWG ;
- aperçu ;
- publication récursive d'un dossier ;
- sélection multiple ;
- glisser-déposer ;
- déplacement de mises en page entre dossiers.

**Attendu :** comportement identique à la version validée avant la V1.2.

## 12. COLLAB-11 — Poste sans droits administrateur

Effectuer la recette sur un poste utilisateur standard sans élévation.

**Attendu :**

- aucune demande administrateur ;
- seules les permissions du partage Windows sont nécessaires.

## 13. Validation finale

Ne passer la PR #30 en Ready for review que si :

- COLLAB-01 à COLLAB-11 sont validés ;
- les workflows Export sont verts ;
- le workflow `Export — configuration collaborative` est vert ;
- aucun test n'a nécessité de modifier manuellement le modèle central pour
  sauvegarder la configuration Export.

Consigner dans l'issue #25 :

- date ;
- noms logiques des deux postes (A/B, sans donnée sensible) ;
- résultat de chaque COLLAB ;
- éventuels écarts ;
- décision Go / No-Go.
