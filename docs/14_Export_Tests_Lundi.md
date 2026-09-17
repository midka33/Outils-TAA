# Export — Checklist de tests Revit 2025.4

**Projet :** Outils TAA  
**Module :** Export  
**Étape :** 07 — Historique et `MODIFIED_ONLY`  
**Environnement cible :** Revit 2025.4 / pyRevit 5.x  
**Date prévue :** lundi

## Consignes

- Effectuer les tests dans Revit 2025.4 / pyRevit 5.x.
- Ne pas modifier le code pendant la campagne de tests.
- Pour chaque test, noter `OK`, `KO` ou `NON TESTÉ`.
- En cas d'erreur, copier le message IronPython complet.
- Si possible, conserver une capture d'écran pour les erreurs UI.
- Un test `KO` doit être signalé avec le contexte précis.

Format recommandé : `TEST-01 : OK` ou `TEST-02 : KO` suivi du message exact.

---

# 1. Lancement et interface

## TEST-01 — Ouverture Export
Ouvrir Revit 2025.4 puis `Outils TAA > Export`.

**Attendu :** la fenêtre Export s'ouvre sans erreur IronPython/WPF.

## TEST-02 — Arborescence
Vérifier `Dossier > Carnet > Mise en page`.

**Attendu :** aucun doublon et uniquement les mises en page du projet courant.

## TEST-03 — Création d'un dossier
Créer un dossier, fermer puis rouvrir Export.

**Attendu :** le dossier est conservé.

---

# 2. Gestion des carnets

## TEST-04 — Créer un carnet dans un dossier
Sélectionner un dossier, créer un carnet et ajouter plusieurs feuilles.

**Attendu :** le carnet apparaît dans le dossier sélectionné, pas dans `Général`.

## TEST-05 — Persistance du carnet
Fermer puis rouvrir Export.

**Attendu :** le carnet et ses feuilles sont conservés.

## TEST-06 — Carnet par paramètre
Créer un carnet basé sur un paramètre, par exemple `Sous-titre`.

**Attendu :** le mode `PARAMETER` est conservé après réouverture.

## TEST-07 — Filtrage par projet
Ouvrir un autre projet Revit.

**Attendu :** les carnets d'un autre projet ne sont pas considérés comme appartenant au projet courant.

---

# 3. Organisation et glisser-déposer

## TEST-08 — Déplacer un carnet vers un dossier
Glisser un carnet vers un autre dossier.

**Attendu :** le carnet change de dossier.

## TEST-09 — Réordonner les carnets
Créer A, B, C ; déplacer C avant A ; fermer et rouvrir Export.

**Attendu :** ordre `C, A, B`, conservé après réouverture.

## TEST-10 — Sélection multiple Ctrl
Sélectionner plusieurs carnets avec `Ctrl + clic`.

**Attendu :** les carnets sélectionnés sont visuellement identifiés.

## TEST-11 — Déplacement groupé
Sélectionner plusieurs carnets et les déplacer vers un dossier.

**Attendu :** tous sont déplacés et leur ordre relatif est conservé.

## TEST-12 — Insertion groupée
Sélectionner plusieurs carnets et les déposer avant un carnet cible.

**Attendu :** ils sont insérés avant la cible dans le même ordre.

## TEST-13 — Ordre des mises en page
Mettre volontairement les feuilles dans l'ordre `A103, A101, A102`.

**Attendu :** Export conserve cet ordre et ne trie pas automatiquement par numéro ou nom.

---

# 4. Réglages PDF / DWG

## TEST-14 — PDF
Tester PDF activé/désactivé et PDF combiné/séparé.

**Attendu :** les réglages sont respectés.

## TEST-15 — DWG
Tester DWG activé/désactivé et DWG combiné/séparé.

**Attendu :** les réglages sont respectés.

## TEST-16 — True Color
Activer True Color et produire un DWG.

**Attendu :** vérifier le résultat réel du DWG.

## TEST-17 — Destination persistante
Définir une destination, fermer puis rouvrir Export.

**Attendu :** destination conservée.

---

# 5. Héritage

## TEST-18 — Héritage dossier → carnet
Définir au dossier `PDF = oui`, `DWG = non`, puis sélectionner un carnet.

**Attendu :** le carnet récupère ces valeurs par héritage.

## TEST-19 — Surcharge carnet
Modifier uniquement PDF au niveau carnet.

**Attendu :** PDF provient du carnet et DWG reste hérité du dossier.

## TEST-20 — Ne pas casser l'héritage
Modifier un autre paramètre du carnet.

**Attendu :** les paramètres non modifiés restent hérités.

## TEST-21 — Retour à l'héritage
Cliquer `Revenir à l'héritage du dossier`.

**Attendu :** les surcharges locales disparaissent et les valeurs redeviennent héritées.

---

# 6. Nommage

## TEST-22 — Variables simples
Tester `{carnet}`, `{numero}`, `{nom}`, `{nom_complet}`, `{projet}`, `{date}`, `{indice}`, `{dossier}`.

**Attendu :** les valeurs produites sont correctes.

## TEST-23 — Paramètre Revit
Tester `{parametre:Sous-titre}`.

**Attendu :** la valeur réelle du paramètre est utilisée.

## TEST-24 — Caractères interdits
Tester un nom contenant `/ \\ : * ? " < > |`.

**Attendu :** le nom est correctement sécurisé pour Windows.

---

# 7. Prévisualisation

## TEST-25 — Prévisualisation carnet
Sélectionner un carnet puis cliquer `Publier`.

**Attendu :** aucun export immédiat ; la fenêtre de prévisualisation apparaît.

## TEST-26 — Informations de prévisualisation
Vérifier carnet, mise en page, format, mode, nom final, destination et statut.

**Attendu :** toutes les informations sont cohérentes.

## TEST-27 — Feuille manquante
Utiliser un carnet contenant une référence devenue introuvable.

**Attendu :** la feuille est signalée comme manquante.

## TEST-28 — Collision
Publier une fois puis relancer exactement la même publication.

**Attendu :** les fichiers existants sont signalés comme collisions.

## TEST-29 — Annulation
Ouvrir la prévisualisation puis cliquer `Annuler`.

**Attendu :** aucun nouveau fichier n'est produit.

## TEST-30 — Confirmation
Confirmer une publication.

**Attendu :** les fichiers sont réellement produits.

---

# 8. Publication d'un dossier

## TEST-31 — Publication récursive
Créer une structure `DCE/Plans/Carnet A`, `DCE/Plans/Carnet B`, `DCE/Coupes/Carnet C`, sélectionner `DCE` puis publier.

**Attendu :** A + B + C sont pris en compte.

## TEST-32 — Destinations différentes
Configurer une destination différente pour A, B et C puis publier DCE.

**Attendu :** chaque carnet utilise sa propre destination.

## TEST-33 — Rapport global
Publier un dossier contenant plusieurs carnets.

**Attendu :** un rapport global permet d'identifier le résultat de chaque carnet, feuille et livrable.

---

# 9. Étape 07 — Historique / MODIFIED_ONLY

## TEST-34 — Première publication
Créer un carnet jamais publié, activer `MODIFIED_ONLY` et publier.

**Attendu :** toutes les feuilles sont `NEW` et toutes sont publiées.

## TEST-35 — Deuxième publication sans modification
Ne rien modifier et relancer `MODIFIED_ONLY`.

**Attendu :** les feuilles sont `UNCHANGED`, aucune feuille n'est proposée et la confirmation est bloquée.

## TEST-36 — Une seule feuille modifiée
Modifier une seule mise en page puis relancer Export.

**Attendu :** la feuille modifiée est `MODIFIED`, les autres `UNCHANGED`, et `MODIFIED_ONLY` ne retient que la feuille modifiée.

## TEST-37 — Nouvelle feuille
Ajouter une nouvelle mise en page au carnet puis relancer `MODIFIED_ONLY`.

**Attendu :** la nouvelle feuille est `NEW` et est publiée.

## TEST-38 — État impossible à comparer
Si possible, observer une feuille dont l'état ne peut pas être déterminé.

**Attendu :** état `UNKNOWN` et republication par sécurité.

## TEST-39 — Publication échouée
Si possible, provoquer une erreur de publication puis relancer `MODIFIED_ONLY`.

**Attendu :** l'historique ne doit pas enregistrer une publication comme réussie si elle a échoué.

## TEST-40 — PDF séparé + MODIFIED_ONLY
PDF séparé ; modifier une seule feuille ; publier en `MODIFIED_ONLY`.

**Attendu :** seul le livrable de la feuille modifiée est produit.

## TEST-41 — DWG séparé + MODIFIED_ONLY
DWG séparé ; modifier une seule feuille ; publier en `MODIFIED_ONLY`.

**Attendu :** seul le livrable de la feuille modifiée est produit.

## TEST-42 — PDF combiné + MODIFIED_ONLY
PDF combiné ; modifier une seule feuille ; publier en `MODIFIED_ONLY`.

**Attendu :** le PDF combiné est produit à partir du périmètre filtré. Vérifier précisément son contenu et son nom.

## TEST-43 — Publication multiple + MODIFIED_ONLY
Créer A, B et C. Modifier une seule feuille dans B puis publier le dossier en `MODIFIED_ONLY`.

**Attendu :** A = aucune publication ; B = seule la feuille modifiée ; C = aucune publication.

---

# 10. Test anti-régression du workflow complet

## TEST-44 — Workflow complet
Effectuer : `Ouverture Export → Dossier → Carnet → Mise en page → Retour dossier → Gestionnaire carnet → Création carnet → Réglages → Profil → Prévisualisation → Publication → Rapport`.

**Attendu :** aucun `AttributeError`, aucune erreur WPF/IronPython, aucun handler manquant et aucun blocage inattendu.

Ce test vise notamment les régressions liées aux handlers `Publish_Click`, `_set_no_selection`, `_update_selection_info`, `_make_sheet_target`, `FolderChanged`, `BrowseOutput_Click`, `DeleteNode_Click` et `OpenCarnetManager_Click`.

---

# 11. Intégration complète Stage 07

## TEST-45 — Contrôle MODIFIED_ONLY dans l'interface
Sélectionner un carnet et rechercher le contrôle permettant d'activer/désactiver `MODIFIED_ONLY`.

**Attendu :** le contrôle est visible, compréhensible et son état est correctement reflété dans l'interface.

## TEST-46 — Persistance du réglage MODIFIED_ONLY
Activer `MODIFIED_ONLY`, fermer Export puis le rouvrir.

**Attendu :** le réglage reste activé pour le carnet concerné et ne modifie pas involontairement les autres carnets.

## TEST-47 — Prévisualisation filtrée
Publier un carnet déjà historisé après avoir modifié une seule feuille, avec `MODIFIED_ONLY` actif.

**Attendu :** seules les feuilles `NEW`, `MODIFIED` ou `UNKNOWN` sont proposées ; les `UNCHANGED` sont exclues.

## TEST-48 — Publication simple filtrée
Depuis un carnet, publier avec `MODIFIED_ONLY` après modification d'une seule feuille.

**Attendu :** seule la feuille candidate est envoyée au moteur de publication.

## TEST-49 — Publication multiple filtrée
Sélectionner un dossier contenant plusieurs carnets ; ne modifier qu'une feuille d'un seul carnet ; publier le dossier avec `MODIFIED_ONLY`.

**Attendu :** les carnets sans changement ne génèrent pas de publication inutile.

## TEST-50 — Historique après publication réussie
Effectuer une publication réussie puis fermer/réouvrir Export.

**Attendu :** l'historique contient la publication réussie, la date, les livrables produits et l'état par feuille.

## TEST-51 — États dans prévisualisation et rapport
Utiliser un carnet contenant des feuilles `NEW`, `MODIFIED` et `UNCHANGED`.

**Attendu :** les états sont compréhensibles et cohérents entre interface, prévisualisation et rapport.

## TEST-52 — Conservation de l'historique lors d'une publication partielle
Publier trois feuilles, modifier une seule puis republier avec `MODIFIED_ONLY`.

**Attendu :** l'historique conserve les trois feuilles et met à jour uniquement l'état de la feuille republiée.

## TEST-53 — Aucun livrable vide lorsque tout est inchangé
Après une publication réussie, ne modifier aucune feuille et relancer `MODIFIED_ONLY` en PDF combiné puis DWG combiné.

**Attendu :** aucun fichier vide n'est créé et la confirmation est bloquée.

## TEST-54 — Héritage de MODIFIED_ONLY dossier → carnet
Activer `MODIFIED_ONLY` au niveau d'un dossier, puis sélectionner plusieurs carnets sans surcharge locale.

**Attendu :** tous les carnets héritent de la valeur du dossier. Désactiver ensuite le réglage sur un seul carnet : seul celui-ci devient localement désactivé.

## TEST-55 — Historique indépendant entre projets Revit
Publier un carnet dans un premier projet, puis ouvrir un autre projet contenant un carnet portant le même nom.

**Attendu :** le second projet ne réutilise pas l'historique du premier ; ses feuilles sont `NEW` à la première publication.

## TEST-56 — Contenu réel d'un PDF/DWG combiné filtré
Après avoir publié un carnet, modifier une seule feuille et activer `MODIFIED_ONLY`. Tester PDF combiné et DWG combiné.

**Attendu :** le nouveau livrable combiné ne contient que le périmètre sélectionné ; aucune feuille `UNCHANGED` n'est exportée.

---

# Tableau de résultats

```text
TEST-01 :ok
TEST-02 :ok
TEST-03 :ok
TEST-04 : ok 
TEST-05 : ok
TEST-06 : ok
TEST-07 : ok
TEST-08 : ok
TEST-09 : ok
TEST-10 : ok
TEST-11 : ok
TEST-12 : ok
TEST-13 : ok
TEST-14 : ko pdf en séparé d'un carnet creer un crash de revit. l'usage des profil fait crasher l'app
IronPython Traceback:
Traceback (most recent call last):
 File "C:\Users\AKDIM\AppData\Roaming\pyRevit\Extensions\Outils-TAA\OutilsTAA.extension\OutilsTAA.tab\Export.panel\Export.pushbutton\script.py", line 291, in <module>
 File "C:\Users\AKDIM\AppData\Roaming\pyRevit\Extensions\Outils-TAA\OutilsTAA.extension\OutilsTAA.tab\Export.panel\Export.pushbutton\script.py", line 287, in main
 File "C:\Users\AKDIM\AppData\Roaming\pyRevit\Extensions\Outils-TAA\OutilsTAA.extension\OutilsTAA.tab\Export.panel\services\publication_preview_integration.py", line 81, in publish_click_with_preview
AttributeError: 'ExportWindow' object has no attribute '_set_folder_name_compat'

Script Executor Traceback:
System.MissingMemberException: 'ExportWindow' object has no attribute '_set_folder_name_compat'
 at IronPython.Runtime.Binding.MetaUserObject.FastGetBinderHelper.<>c__DisplayClass16_0.<FallbackError>b__1(CallSite site, Object self, CodeContext context)
 at IronPython.Runtime.Types.GetMemberDelegates.SlotDict(CallSite site, Object self, CodeContext context)
 at System.Dynamic.UpdateDelegates.UpdateAndExecute2[T0,T1,TRet](CallSite site, T0 arg0, T1 arg1)
 at IronPython.Compiler.Ast.DynamicGetMemberExpression.GetMemberInstruction.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.Interpreter.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.LightLambda.Run4[T0,T1,T2,T3,TRet](T0 arg0, T1 arg1, T2 arg2, T3 arg3)
 at IronPython.Compiler.PythonCallTargets.OriginalCallTarget3(PythonFunction function, Object arg0, Object arg1, Object arg2)
 at CallSite.Target(Closure, CallSite, Object, Object, RoutedEventArgs)
 at System.Dynamic.UpdateDelegates.UpdateAndExecute3[T0,T1,T2,TRet](CallSite site, T0 arg0, T1 arg1, T2 arg2)
 at _Scripting_(Object[], Object, RoutedEventArgs)
 at System.Windows.EventRoute.InvokeHandlersImpl(Object source, RoutedEventArgs args, Boolean reRaised)
 at System.Windows.UIElement.RaiseEventImpl(DependencyObject sender, RoutedEventArgs args)
 at System.Windows.Controls.Primitives.ButtonBase.OnClick()
 at System.Windows.Controls.Button.OnClick()
 at System.Windows.Controls.Primitives.ButtonBase.OnMouseLeftButtonUp(MouseButtonEventArgs e)
 at System.Windows.RoutedEventArgs.InvokeHandler(Delegate handler, Object target)
 at System.Windows.EventRoute.InvokeHandlersImpl(Object source, RoutedEventArgs args, Boolean reRaised)
 at System.Windows.UIElement.ReRaiseEventAs(DependencyObject sender, RoutedEventArgs args, RoutedEvent newEvent)
 at System.Windows.RoutedEventArgs.InvokeHandler(Delegate handler, Object target)
 at System.Windows.EventRoute.InvokeHandlersImpl(Object source, RoutedEventArgs args, Boolean reRaised)
 at System.Windows.UIElement.RaiseEventImpl(DependencyObject sender, RoutedEventArgs args)
 at System.Windows.UIElement.RaiseTrustedEvent(RoutedEventArgs args)
 at System.Windows.Input.InputManager.ProcessStagingArea()
 at System.Windows.Interop.HwndMouseInputProvider.ReportInput(IntPtr hwnd, InputMode mode, Int32 timestamp, RawMouseActions actions, Int32 x, Int32 y, Int32 wheel)
 at System.Windows.Interop.HwndMouseInputProvider.FilterMessage(IntPtr hwnd, WindowMessage msg, IntPtr wParam, IntPtr lParam, Boolean& handled)
 at System.Windows.Interop.HwndSource.InputFilterMessage(IntPtr hwnd, Int32 msg, IntPtr wParam, IntPtr lParam, Boolean& handled)
 at MS.Win32.HwndWrapper.WndProc(IntPtr hwnd, Int32 msg, IntPtr wParam, IntPtr lParam, Boolean& handled)
 at System.Windows.Threading.ExceptionWrapper.InternalRealCall(Delegate callback, Object args, Int32 numArgs)
 at System.Windows.Threading.ExceptionWrapper.TryCatchWhen(Object source, Delegate callback, Object args, Int32 numArgs, Delegate catchHandler)
 at System.Windows.Threading.Dispatcher.LegacyInvokeImpl(DispatcherPriority priority, TimeSpan timeout, Delegate method, Object args, Int32 numArgs)
 at MS.Win32.HwndSubclass.SubclassWndProc(IntPtr hwnd, Int32 msg, IntPtr wParam, IntPtr lParam)
 at MS.Win32.UnsafeNativeMethods.DispatchMessage(MSG& msg)
 at System.Windows.Threading.Dispatcher.PushFrameImpl(DispatcherFrame frame)
 at System.Windows.Window.ShowHelper(Object booleanBox)
 at System.Windows.Window.Show()
 at System.Windows.Window.ShowDialog()
 at Microsoft.Scripting.Interpreter.FuncCallInstruction`2.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.Interpreter.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.LightLambda.Run3[T0,T1,T2,TRet](T0 arg0, T1 arg1, T2 arg2)
 at System.Dynamic.UpdateDelegates.UpdateAndExecute2[T0,T1,TRet](CallSite site, T0 arg0, T1 arg1)
 at Microsoft.Scripting.Interpreter.DynamicInstruction`3.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.Interpreter.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.LightLambda.Run1[T0,TRet](T0 arg0)
 at System.Dynamic.UpdateDelegates.UpdateAndExecute2[T0,T1,TRet](CallSite site, T0 arg0, T1 arg1)
 at Microsoft.Scripting.Interpreter.DynamicInstruction`3.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.Interpreter.Run(InterpretedFrame frame)
 at Microsoft.Scripting.Interpreter.LightLambda.Run2[T0,T1,TRet](T0 arg0, T1 arg1)
 at IronPython.Compiler.PythonScriptCode.RunWorker(CodeContext ctx)
 at IronPython.Compiler.RuntimeScriptCode.InvokeTarget(Scope scope)
 at Microsoft.Scripting.Hosting.CompiledCode.Execute(ScriptScope scope)
 at PyRevitLabs.PyRevit.Runtime.IronPythonEngine.Execute(ScriptRuntime& runtime)
TEST-15 : ko publier un dwg fait crasher revit avec le message revit a rencontré une erreur fatale et ne peut pas continuer
TEST-16 : ko car test 15
TEST-17 : ok
TEST-18 : ok
TEST-19 : ok
TEST-20 : ok
TEST-21 : ok
TEST-22 : ko pas d'affichage dans aperçu du nom
TEST-23 : ko pas d'affichage dans aperçu du nom
TEST-24 : ko une fois un mise en page changer pour avoir un caractêre spéciale; impossible de mettre a jour le nommage de la mise en page.
TEST-25 : ok
TEST-26 : ok
TEST-27 : non testé
TEST-28 : non testé
TEST-29 : ok
TEST-30 : ok
TEST-31 :
TEST-32 :
TEST-33 :
TEST-34 :
TEST-35 :
TEST-36 :
TEST-37 :
TEST-38 :
TEST-39 :
TEST-40 :
TEST-41 :
TEST-42 :
TEST-43 :
TEST-44 :
TEST-45 :
TEST-46 :
TEST-47 :
TEST-48 :
TEST-49 :
TEST-50 :
TEST-51 :
TEST-52 :
TEST-53 :
TEST-54 :
TEST-55 :
TEST-56 :
```

# Notes / erreurs

```text
____________________________________________________________

____________________________________________________________

____________________________________________________________

____________________________________________________________

____________________________________________________________
```
