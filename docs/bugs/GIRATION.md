# Registre — Giration (branche expérimentale)

## BUG-GIRATION-001 — Syntaxe/encodage dans script.py
**Symptôme :** SyntaxError sur f-string puis UnicodeDecodeError lors du
chargement dans pyRevit. **Cause constatée :** f-string incompatible avec le
moteur IronPython 2.7; la cause précise de UnicodeDecodeError dans la copie
installée n'a pas été reproduite localement. **Correction :** code de point
d'entrée intégralement ASCII, sans f-string et cookie UTF-8 ; syntaxe compatible
Python 2.7. **Prévention :** analyse syntaxique des entrées et comparaison des
SHA local/installé. **Anti-régression :** chargement dans Revit 2025.4 requis.

## BUG-GIRATION-002 — Orientation erronée des arcs
**Symptôme :** cap incohérent pour certains virages ; point de référence
carrosserie confondu avec essieu. **Cause :** intégration par centre de courbure
et addition incorrecte des rotations. **Correction :** intégration exacte de
l'essieu arrière en fonction de l'abscisse signée et conversion explicite vers
l'origine de carrosserie. **Prévention :** convention de référence documentée.
**Anti-régression :** virages gauche/droite, marche arrière, raccordement et
rayon théorique contrôlés par pytest.

## BUG-GIRATION-003 — Fausse enveloppe et véhicules prétendument SDIS
**Symptôme :** « enveloppe balayée » n'était qu'une liste de rectangles ;
références fictives `SDIS33-VEH-xxx`. **Cause :** substitution de données et
de représentation provisoires à des données validées. **Correction :** sortie
renommée/qualifiée d'empreintes et traces de coins, catalogue marqué
`verified=False`, références réglementaires retirées, modèle 3-essieux exclu.
**Prévention :** statut de preuve et convention de mesure obligatoires.
**Anti-régression :** tests d'empreintes et vérification de la source/metadata.

## BUG-GIRATION-004 — Fenêtre WPF et chemins du thème
**Symptôme probable :** WPF plante si `StaticResource TaaCard` est lu avant
le chargement du thème, et chemin `..` remontant trop haut. **Cause :** thème
chargé après parsing XAML, chemin relatif incorrect. **Correction :** XAML
n'utilise que `DynamicResource` pour les clés du thème ; chemin absolu calculé
depuis l'extension ; import module distinct `giration_theme`. **Prévention :**
aucune ressource statique introuvable avant parsing. **Anti-régression :** XML
vérifié hors Revit, ouverture WPF sous Revit requise.
