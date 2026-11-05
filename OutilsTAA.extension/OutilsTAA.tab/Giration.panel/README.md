# Giration (prototype technique)

Reprise intégrale de la base géométrique et de la commande de démonstration.
**Non validé dans Revit. Ne pas utiliser pour certifier un accès pompier,
une conformité de voirie ou une giration constructeur.**

## Installation (overlay de test)

Copier le contenu de `OutilsTAA.extension/` par-dessus une copie installée de
la suite Outils TAA. Laisser les autres panneaux inchangés. Effectuer le test
uniquement dans un fichier Revit de démonstration.

Le `script.py` d'entrée a un encodage ASCII sans BOM. Les autres fichiers Python
utilisent UTF-8 avec cookie en première ligne. Le thème commun doit exister
à `OutilsTAA.extension/resources/ui/Theme.xaml` dans l'installation globale.

## Utilisation

Voir `docs/25_Giration_Vehicules.md` pour le protocole et les limitations.
La commande est **un prototype par clics** ; elle ne possède ni prévisualisation
continue ni enregistrement rééditable. Échap termine la saisie des points.

## Retour d'essais

Transmettre la console pyRevit, les exceptions, une capture du plan et le
comportement de l'interface avant de qualifier le prototype P0.
