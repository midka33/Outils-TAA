# Export — Préparation TEST-14 — 2026-09-28

Base analysée : `afe840753217f81b298f1cec6b71a393e8982908`.

## Corrections

- PDF séparés : un appel natif par carnet, association explicite par numéro de
  feuille dans un répertoire temporaire, puis noms personnalisés TAA.
- Contrôle des sorties manquantes/vides, collisions Windows et restauration des
  fichiers précédents en cas d'échec de livraison ; dossier de récupération signalé.
- Modèle de nommage hérité transmis sur une copie de publication.
- Une seule instance du gestionnaire de glisser-déposer, propriétaire ExportWindow.
- Quatre tests obsolètes remis en cohérence ; capitalisation centrale 020–024.
- Surcouche stage07 conservée ; aucun raccordement Stage 08 ajouté.

## Validation hors Revit

Commande : `python -m pytest -q --import-mode=importlib` (pytest requis).
Résultat : **97 tests réussis**. Le test du contrat API emploie des doubles :
il ne prouve pas le fonctionnement natif PDF/WPF dans Revit.

Références de contrat consultées : documentation Autodesk PDFExportOptions
SetNamingRule et TableCellCombinedParameterData ; catégorie OST_Sheets et
paramètre SHEET_NUMBER. La vérification API native Revit 2025.4 reste ouverte.

## Vérification dans Revit 2025.4

1. Recharger la branche corrigée et redémarrer Revit.
2. Ouvrir Export, créer un dossier/carnet et ajouter deux feuilles : parents ouverts.
3. Déplacer deux éléments avec Ctrl, vérifier qu'ils ne sont déplacés qu'une fois.
4. Sélectionner le carnet et appliquer « PDF séparés ».
5. Saisir `{carnet}-{numero}-{nom}` comme modèle et une destination de test.
6. Vérifier les noms dans l'aperçu, publier, comparer les vrais fichiers au rapport
   et ouvrir chaque PDF pour confirmer la bonne feuille.
7. Définir aussi ce modèle au niveau dossier, puis un carnet qui en hérite ; vérifier
   les mêmes noms sans transformer l'héritage en surcharge.
8. Republier dans la même destination : remplacement correct des PDF précédents.
9. Essayer `{carnet}` avec deux feuilles : erreur de collision avant export.
10. Tester PDF combiné puis enregistrement/suppression d'un profil personnalisé.

Conserver les anciens résultats TEST-14 comme historique. Ajouter le nouveau résultat
avec le commit testé, les noms attendus/réels et le traceback complet en cas d'échec.
**Statut Revit : ÉCHEC signalé sur `858f858`, 2026-09-28.**

Le rapport montrait des lignes « ERREUR / Export terminé. », un compteur
« 1 erreur(s) » et aucun PDF publié selon l'utilisateur. La cause native reste
à identifier : l'erreur globale était masquée par l'interface.

Le correctif de diagnostic BUG-EXPORT-025 affiche désormais le texte complet en
bas du rapport (sélectionnable avec Ctrl+A / Ctrl+C après clic dans la zone).
Après mise à jour et redémarrage Revit, rejouer le même export puis transmettre
ce texte. L'export PDF réel reste bloquant pour TEST-14.

**Diagnostic du 2026-09-29 :** `DPC : PDF séparé — erreur : Nom PDF non valide :
taa_PC 09*.pdf`. Le contrôle Windows a arrêté le traitement avant
`Document.Export`. Le correctif BUG-EXPORT-026 accepte ce numéro sans modifier
la feuille, puis vérifie les noms réellement produits par Revit. Après mise
à jour, refaire un export du carnet DPC et vérifier chaque PDF. En cas de
nouvelle erreur, conserver le message complet et le dossier temporaire indiqué.
