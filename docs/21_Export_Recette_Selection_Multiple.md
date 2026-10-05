# Export — Recette de sélection multiple avant release

**Cible : Revit 2025.4 / pyRevit 5.x.**

**Statut : à exécuter dans Revit.** Les tests Python ne valident pas WPF ni les fichiers natifs.

Préparer un carnet **Plans** avec A01/A02/A03/A04 et un carnet **Coupes** avec
B01/B02, dans cet ordre. Choisir un dossier de sortie de test. Préparer aussi
un sous-dossier contenant un carnet et deux destinations distinctes.

| Test | Manipulation | Résultat attendu |
|---|---|---|
| MS-01 | Sélectionner A01 puis Ctrl+A03, PDF séparés | Résumé : 1 carnet, 2 feuilles ; aperçu et livraison : A01 et A03 uniquement |
| MS-02 | Même sélection, PDF combiné | Un PDF de 2 pages dans l'ordre A01/A03, sans A02/A04 |
| MS-03 | Cliquer A01 puis Maj+A03 | A01/A02/A03 retenues ; résumé mis à jour immédiatement |
| MS-04 | Ctrl-sélectionner Plans et Coupes, réglages/destinations différents | Chaque carnet utilise ses propres réglages et destination ; un aperçu et un rapport globaux |
| MS-05 | Ctrl-sélectionner A01, A03 et B02 | 2 carnets, 3 feuilles ; PDF combiné : un fichier A01/A03 et un fichier B02 |
| MS-06 | Sélectionner Plans + A01 ; puis un dossier + son sous-dossier + un carnet enfant | Aucun doublon ; parent complet prioritaire ; chemins de dossier conservés |
| MS-07 | Retirer avec Ctrl toutes les lignes ; puis naviguer au clavier | Publication désactivée à sélection vide ; le clavier réactive uniquement son élément courant |
| MS-08 | Aperçu seul ; Annuler la confirmation ; puis deux carnets produisant le même chemin | Aucun export pour aperçu/annulation ; collision signalée et confirmation bloquée |
| MS-09 | Sélection A01/A03 : PDF séparé/DWG séparé, PDF combiné/DWG séparé, PDF séparé/DWG combiné, les deux combinés | Seules A01/A03 transmises ; contenu, noms, références DWG et chemins conformes à l'aperçu |
| MS-10 | Publication partielle, puis carnet complet ; fermer/rouvrir Export ; déplacer une sélection persistante | Carnet original conserve ses 4 feuilles, réglages et ordre ; déplacement/parents ouverts toujours opérationnels |

Compléments MS-04 : essayer deux carnets temporaires et un carnet complet avec
une seule feuille d'un autre carnet. Vérifier le libellé **Publier la sélection**
et le nom de l'élément actif du panneau de réglages.

Complément MS-02 : placer un PDF complet existant sous le même nom. Vérifier
l'avertissement de remplacement, puis annuler ou changer la destination pour
conserver les deux versions.

Pour chaque échec : noter le test, les éléments sélectionnés, les modes PDF/DWG,
le nombre de feuilles annoncé et joindre le diagnostic du rapport. Ne pas cocher
ces tests sur la seule base des résultats Python.
