# Déploiement agence — extension pyRevit centralisée sur serveur

**Décision de déploiement :** 12 novembre 2026  
**Statut :** méthode effectivement utilisée dans l'agence, rapportée par l'utilisateur ; procédure de fiabilisation ci-dessous à appliquer/contrôler poste par poste.  
**Périmètre :** Outils TAA, Revit 2025.4, pyRevit installé sur chaque poste.

## 1. Architecture retenue

**Mode principal de déploiement dans l'agence :** une seule copie active du dossier de l'extension Outils TAA réside sur un serveur de fichiers accessible aux collaborateurs. Chaque ordinateur conserve sa propre installation de Revit et de pyRevit et référence, dans les chemins d'extensions pyRevit, l'emplacement réseau commun.

Le dossier source du dépôt est `OutilsTAA.extension/` ; le nom réel du dossier et son chemin sur le serveur sont ceux configurés par l'agence. Aucun chemin UNC ou lecteur réseau spécifique n'est imposé par le code ou cette documentation.

```text
Serveur de l'agence
└── <partage réseau>
    └── OutilsTAA.extension/      # copie active commune

Poste A : Revit + pyRevit ──► emplacement réseau commun
Poste B : Revit + pyRevit ──► emplacement réseau commun
Poste C : Revit + pyRevit ──► emplacement réseau commun
```

Les mises à jour ne nécessitent **pas** de recopier l'extension ni d'exécuter un installateur sur chaque poste : l'administrateur du partage remplace le dossier commun sur le serveur. Le remplacement des fichiers n'entraîne pas un rechargement automatique garanti dans les sessions Revit déjà ouvertes.

L'installateur CMD livré avec les releases reste une **méthode alternative** de distribution, notamment pour un poste isolé ; il n'est **pas** le flux de déploiement courant de l'agence. Les notes d'installation des releases passées restent des documents historiques exacts pour leurs livrables.

## 2. Première configuration d'un poste

1. Installer/configurer Revit et pyRevit sur le poste selon les prérequis habituels.
2. Donner au collaborateur accès en lecture au partage réseau.
3. Ajouter l'emplacement de l'extension partagée aux chemins d'extensions pyRevit sur ce poste, sans créer une seconde copie locale d'Outils TAA.
4. Fermer puis rouvrir Revit : vérifier que le ruban **Outils TAA** apparaît et qu'une commande de test s'ouvre.

**Observation sur le terrain (12/11/2026) :** lorsqu'un emplacement d'extension est ajouté alors que Revit est déjà ouvert, le ruban peut être absent pendant cette session ; un redémarrage de Revit l'a fait apparaître sur les postes concernés. Un rechargement de pyRevit peut être essayé, mais le redémarrage demeure la procédure d'activation conseillée pour l'agence.

## 3. Mise à jour du dossier partagé

**Avant publication :**
- choisir une release identifiée (tag/version/commit GitHub) ; ne pas publier une branche expérimentale comme une version stable ;
- préparer la nouvelle copie dans un répertoire temporaire distinct du dossier actif, puis contrôler le contenu de l'extension ;
- effectuer les essais sur un poste pilote, en gardant la version active inchangée ;
- sauvegarder le dossier actuellement en production pour permettre un retour arrière ;
- prévenir les collaborateurs et choisir une fenêtre de maintenance où aucune commande Outils TAA n'est en cours.

**Publication :**
- réserver les écritures du dossier partagé à la personne responsable du déploiement ;
- remplacer la copie active par la version préparée, sans copier fichier par fichier pendant une utilisation en cours ;
- prévenir les utilisateurs que les sessions Revit ouvertes peuvent conserver des scripts en mémoire tout en accédant à des fichiers modifiés : **ne pas promettre une bascule à chaud** ;
- demander un redémarrage de Revit sur les postes avant de reprendre les commandes.

**Contrôle après publication :** sur un poste pilote puis sur les postes concernés, vérifier le ruban, l'ouverture des fenêtres **Export**, **Calculs des pièces**, **Plans de vente**, et rejouer une opération représentative des modules réellement utilisés (par exemple un export PDF/DWG sur une maquette de test). Consigner la version exacte, la version de pyRevit, le résultat et les éventuels écarts.

**Retour arrière :** si un défaut est constaté, interrompre l'utilisation de l'extension, restaurer le dossier de sauvegarde, faire redémarrer Revit et retester. Ne pas modifier les maquettes de production pour diagnostiquer un problème de déploiement.

## 4. Disponibilité, sécurité et compatibilité

- Le partage réseau devient une dépendance d'exécution : disponibilité réseau, droits de lecture, performances et chemins accessibles doivent être vérifiés. Une déconnexion serveur peut rendre l'extension indisponible ou entraîner des erreurs.
- Les utilisateurs ordinaires doivent avoir des droits de **lecture** ; limiter l'**écriture** aux responsables du déploiement, puisque les scripts sont exécutés depuis le partage.
- Utiliser un emplacement réseau stable et documenté. Ne pas introduire dans GitHub de chemins internes réels, identifiants ou secrets.
- **Cible officielle du dépôt au 12/11/2026 : Revit 2025.4 / pyRevit 5.x.**
- **pyRevit 7.0.0 :** fonctionnement apparent d'Outils TAA observé par l'utilisateur sur certains postes, mais aucune campagne complète de non-régression sous cette version n'est documentée. Il s'agit d'une compatibilité **observée, non validée**.
- Sur des postes où Revit 2023 est installé, pyRevit 7.0.0 peut afficher `Ambiguous host product "23.1.10.4"` pour deux identifications de Revit 2023. Ce message est rapporté par l'utilisateur ; il n'établit pas à lui seul un défaut d'Outils TAA ni une validation pyRevit 7. Son éventuelle résolution relève du diagnostic pyRevit.
- Ne pas confondre le **partage du code de l'extension** avec un **partage des réglages métier par projet** : la configuration collaborative du module Export relève d'un développement distinct.

## 5. Traçabilité et critères de validation

| Élément | État au 12/11/2026 |
| --- | --- |
| Déploiement centralisé par dossier sur serveur | **En usage à l'agence**, confirmé par l'utilisateur |
| Référencement du chemin sur chaque poste | **En usage**, confirmé par l'utilisateur |
| Ruban absent immédiatement après ajout du chemin dans Revit déjà ouvert | **Observé** sur certains postes |
| Ruban visible après redémarrage de Revit | **Observé** sur les postes concernés |
| Installation locale par CMD comme mode principal agence | **Non retenue** ; alternative toujours disponible |
| Compatibilité complète avec pyRevit 7.0.0 | **À tester** ; fonctionnement apparent constaté |
| Mise à jour à chaud sans redémarrage et bascule sans interruption | **Non garantie / non validée** |
| Tests automatisés / recette Revit associés à cette modification documentaire | **Non exécutés** (aucun code modifié) |

**Prochaine action recommandée :** constituer une courte matrice de recette pyRevit 5.x / 7.0.0 et tester sur un poste pilote le passage d'une version partagée à une autre, le redémarrage et le retour arrière. Cette procédure n'implique aucune modification des modules métier.
