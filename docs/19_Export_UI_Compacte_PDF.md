# Export — Interface compacte et paramètres PDF

## État

Implémentation terminée et validation Revit 2025.4 confirmée par l'utilisateur le 2026-10-01.
Références consultées : 04_UI_Guidelines, 09_Export, registre des bugs et les trois
images officielles de docs/assets/ui. Les captures du retour utilisateur précisent
les pictogrammes PDF/DWG, le bloc d'héritage et les groupes du dialogue PDF.

## Périmètre

- Police courante conservée à 13 px, fenêtre initiale 1320 × 760 unités WPF.
- Profil compact, héritage sur une ligne de 30 px, détails en infobulle.
- PDF et DWG sur des rangées repliables ; destination et nommage directs.
- Options avancées repliées ; résumé et actions toujours hors du défilement.
- Aperçu de consultation sans publication ; flux Publier/confirmation conservé.
- Dialogue PDF : sept cases natives, vectoriel/raster, défauts, annuler, appliquer.
- Arrière-plan désactivé avec explication : limitation du flux synchrone TAA.
- Sous-dossier du carnet activé par défaut en séparé, désactivable explicitement.
- Icônes vectorielles PDF/DWG, Export sans texte intégré et mieux cadré.

Seuls les ajustements métier nécessaires aux contrôles demandés sont réalisés :
champs de réglages, transmission aux options PDF, préférence de dossier partagé
par aperçu/export. Les handlers de sélection, suppression, drag-and-drop et ordre
ne sont pas modifiés dans cette passe.

## Vérifications

205 tests Python réellement exécutés : `python -m pytest -q --import-mode=importlib`.
La couverture ajoute héritage, profils et persistance de chaque option, transmission
aux deux modes natifs avec doubles d'API, export séparé sécurisé, annulation et
sauvegarde différentielle, sous-dossiers et chemins d'aperçu, handlers XAML,
destination manuelle et aperçu sans publication. XML et ressources vérifiés,
encodages UTF-8, absence de syntaxe Python 3 dans le code de production modifié,
PNG contrôlés et diff relu.

Les tests automatisés ont été exécutés hors Revit ; la validation complémentaire a ensuite
été réalisée dans Revit 2025.4 par l'utilisateur, y compris le sélecteur de paramètres,
le rendu compact et les workflows concernés.

## Test court dans Revit 2025.4

1. Récupérer la branche feat/export-taa-ui puis recharger pyRevit. Vérifier l'icône
   agrandie et les feuilles PDF/DWG/both, sans changer la sélection de l'arbre.
2. En 1920 × 1080 / Windows 100 %, ouvrir Export et sélectionner un dossier puis un
   carnet : PDF, DWG, destination et nommage visibles sans scroll ; résumé/Aperçu/
   Publier fixes. Répéter à 125 %, puis réduire la fenêtre : retour à la ligne et
   défilement de secours, aucun contrôle superposé ou hors d'atteinte.
3. Modifier une option PDF au parent, contrôler l'héritage au carnet. Ouvrir la
   fenêtre PDF : tester Annuler, Appliquer, défauts, puis sauvegarder un profil et
   le réappliquer. Vérifier la persistance après fermeture/réouverture.
4. Exporter un carnet PDF combiné, puis séparé, en vectoriel et raster avec options
   visibles (plans de référence, cadrages). Comparer aux choix natifs Revit ; tester
   les DPI 144/600. Vérifier noms, nombre de fichiers et rapport.
5. Tester le sous-dossier activé/désactivé en séparé avec PDF+DWG, vérifier les chemins
   dans l'aperçu puis sur disque. Tester destination tapée, profils, retour à
   l'héritage, déplacement Ctrl/Maj et conservation des dossiers ouverts.

| Contrôle réel | État |
|---|---|
| Full HD 100 % — réglages courants sans scroll | OK |
| Full HD 125 % et réduction manuelle | OK |
| Options PDF et comparaison native Revit 2025.4 | OK |
| Profils/héritage, sous-dossiers, aperçu/publication PDF/DWG | OK |
| Arbre, ordre, multi-sélection et drag-and-drop | OK |

## Fichiers de cette passe

La liste ci-dessous est relative à la racine du dépôt et inclut créations et modifications.

```text
CHANGELOG.md
OutilsTAA.extension/OutilsTAA.tab/Export.panel/Export.pushbutton/icon.dark.png
OutilsTAA.extension/OutilsTAA.tab/Export.panel/Export.pushbutton/icon.png
OutilsTAA.extension/OutilsTAA.tab/Export.panel/export_window.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/pdf_settings.xaml
OutilsTAA.extension/OutilsTAA.tab/Export.panel/pdf_settings_window.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/pdf_export_service.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/pdf_options.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/publication_paths.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/publication_preview_service.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/publication_profile_service.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/publication_service.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/services/publication_settings.py
OutilsTAA.extension/OutilsTAA.tab/Export.panel/ui.xaml
OutilsTAA.extension/resources/ui/Theme.xaml
OutilsTAA.extension/resources/ui/icons/export-16.png
OutilsTAA.extension/resources/ui/icons/export-32.png
OutilsTAA.extension/resources/ui/icons/export-96.png
OutilsTAA.extension/resources/ui/icons/export.svg
ROADMAP.md
docs/04_UI_Guidelines.md
docs/09_Export.md
docs/11_BUGS_Prevention_Registry.md
docs/18_Export_Charte_UI_V1.md
docs/19_Export_UI_Compacte_PDF.md
tests/test_export_ui_completion.py
tests/test_folder_inheritance_ui.py
tests/test_pdf_advanced_ui.py
tests/test_pdf_delivery.py
tests/test_publication_folder_paths.py
tests/test_taa_ui_contract.py
```

## Validation finale

- Sélecteur de paramètres de feuilles : **OK**
- Sélecteur Informations sur le projet : **OK**
- Anciens modèles de nommage : **compatibles**
- PDF combiné : paramètres de feuille issus de la première feuille du carnet
- Validation utilisateur dans Revit 2025.4 : **OK — 2026-10-01**
