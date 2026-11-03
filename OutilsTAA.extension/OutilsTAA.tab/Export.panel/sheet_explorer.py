# -*- coding: utf-8 -*-
"""Explorateur de feuilles Export : source Revit distincte du tree de publication."""

import json
import os

from System.Windows import DragDrop, DragDropEffects, DataObject, Visibility, GridLength, GridUnitType
from System.Windows.Controls import ListBoxItem, TextBlock, ContextMenu, MenuItem
from System.Windows.Input import Keyboard, ModifierKeys, MouseButtonState, Key
from System.Windows.Media import VisualTreeHelper


class SheetExplorer(object):
    DATA_FORMAT = "OutilsTAA.Export.AvailableSheets"
    # Les en-têtes de groupe portent un Tag préfixé : ils ne doivent jamais
    # entrer dans la sélection des feuilles (BUG-EXPORT-053).
    GROUP_TAG_PREFIX = "GROUP:"

    def __init__(self, window, sheets):
        self.window = window
        self.sheets = dict((str(sheet.UniqueId), sheet) for sheet in sheets
                           if sheet is not None and getattr(sheet, "UniqueId", None))
        self.selected_ids = set()
        self._collapsed_groups = set()
        self._rendering = False
        self._mouse_point = None
        self._last_width = 310.0
        # Les feuilles sources ne changent pas pendant que la fenêtre est
        # ouverte : l'ordre trié et les regroupements sont calculés une fois
        # (BUG-EXPORT-055).
        self._ordered_sheets = sorted(
            self.sheets.values(),
            key=lambda s: ((s.SheetNumber or "").lower(),
                           (s.Name or "").lower()))
        self._group_cache = {}
        self._settings_path = os.path.join(
            os.environ.get("APPDATA") or os.path.expanduser("~"),
            "OutilsTAA", "export_sheet_explorer.json")
        self._restore_settings()
        self._parameters = list(window.controller.get_context().get("parameters") or [])
        window.SheetExplorerGrouping.ItemsSource = (
            ["Liste simple", "Par numéro", "Par nom"] +
            ["Paramètre : " + name for name in self._parameters]
        )
        window.SheetExplorerGrouping.SelectedIndex = 0
        self._updating_parameter_values = False
        window.SheetExplorerParameter.ItemsSource = (
            ["Tous les paramètres"] + self._parameters)
        window.SheetExplorerParameter.SelectedIndex = 0
        window.SheetExplorerValue.ItemsSource = ["Toutes les valeurs"]
        window.SheetExplorerValue.SelectedIndex = 0
        window.SheetExplorerList.PreviewKeyDown += self._key_down
        # Preview et bubble : le contrôle TreeViewItem peut consommer
        # l'événement avant le TreeView. AddHandler reçoit aussi Handled.
        from System.Windows import UIElement
        window.PublicationTree.AddHandler(
            UIElement.PreviewDragOverEvent, self._drag_over, True)
        window.PublicationTree.AddHandler(
            UIElement.PreviewDropEvent, self._drop, True)
        window.Closing += self._closing
        self._build_context_menu()
        self.refresh()

    @staticmethod
    def _logger():
        try:
            from pyrevit import script
            return script.get_logger()
        except Exception:
            return None

    def _log_warning(self, message):
        # Règle BUG-EXPORT-025 : une erreur ne doit jamais être masquée
        # sans laisser de trace, même quand l'interface reste utilisable.
        logger = self._logger()
        if logger is not None:
            try:
                logger.warning(message)
            except Exception:
                pass

    @classmethod
    def _group_from_tag(cls, tag):
        """Nom de groupe porté par un tag d'en-tête, sinon None."""
        value = str(tag) if tag else ""
        if value.startswith(cls.GROUP_TAG_PREFIX):
            return value[len(cls.GROUP_TAG_PREFIX):]
        return None

    def _restore_settings(self):
        self._visible = True
        if os.path.isfile(self._settings_path):
            try:
                with open(self._settings_path, "r") as handle:
                    state = json.load(handle)
                self._visible = bool(state.get("visible", True))
                self._last_width = max(210.0, min(520.0, float(state.get("width", 310))))
            except Exception:
                # Un premier lancement sans fichier est normal ; un fichier
                # illisible doit laisser une trace, pas rester silencieux.
                self._log_warning(
                    "Preferences de l'explorateur illisibles ({0}) ; "
                    "valeurs par defaut retenues.".format(self._settings_path))
        self._apply_visibility()

    def _apply_visibility(self):
        w = self.window
        w.SheetExplorerPanel.Visibility = Visibility.Visible if self._visible else Visibility.Collapsed
        w.SheetExplorerSplitter.Visibility = Visibility.Visible if self._visible else Visibility.Collapsed
        w.SheetExplorerColumn.Width = GridLength(self._last_width if self._visible else 0, GridUnitType.Pixel)
        w.SheetExplorerSplitterColumn.Width = GridLength(5 if self._visible else 0, GridUnitType.Pixel)
        w.SheetExplorerToggle.Content = "◀ Feuilles" if self._visible else "▶ Feuilles"

    def toggle(self):
        if self._visible:
            self._last_width = max(210, float(self.window.SheetExplorerColumn.ActualWidth))
        self._visible = not self._visible
        self._apply_visibility()

    def _closing(self, sender, args):
        if self._visible:
            self._last_width = max(210, float(self.window.SheetExplorerColumn.ActualWidth))
        try:
            directory = os.path.dirname(self._settings_path)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            with open(self._settings_path, "w") as handle:
                json.dump({"visible": self._visible, "width": self._last_width}, handle)
        except Exception:
            self._log_warning(
                "Preferences de l'explorateur non enregistrees ({0}).".format(
                    self._settings_path))

    def _used_paths(self):
        result = {}
        containers = dict((str(x.id), x) for x in
                          list(self.window._folders) + list(self.window._carnets))
        for publication in self.window._carnets:
            parts = [publication.name]
            parent = getattr(publication, "folder_id", None)
            visited = set()
            while parent is not None and str(parent) not in visited:
                visited.add(str(parent))
                value = containers.get(str(parent))
                if value is None:
                    break
                parts.insert(0, value.name)
                parent = getattr(value, "parent_id", None)
                if parent is None and hasattr(value, "folder_id"):
                    parent = value.folder_id
            path = " / ".join(parts)
            for item in publication.items or []:
                result.setdefault(str(item.unique_id), []).append(path)
        return result

    def _group(self, sheet, mode):
        # BUG-EXPORT-055 : LookupParameter est un appel Revit coûteux et la
        # recherche appelle refresh() à chaque frappe. Les valeurs de
        # paramètres ne changent pas pendant que la fenêtre est ouverte :
        # le regroupement est calculé une fois par (feuille, mode).
        key = (str(sheet.UniqueId), mode)
        cached = self._group_cache.get(key)
        if cached is not None:
            return cached
        result = self._compute_group(sheet, mode)
        self._group_cache[key] = result
        return result

    def _compute_group(self, sheet, mode):
        if mode == 1:
            return (sheet.SheetNumber or "")[:2].upper() or "Sans numéro"
        if mode == 2:
            return (sheet.Name or "")[:1].upper() or "Sans nom"
        if mode >= 3 and mode - 3 < len(self._parameters):
            try:
                parameter = sheet.LookupParameter(self._parameters[mode - 3])
                if parameter is not None:
                    return parameter.AsString() or parameter.AsValueString() or "Non renseigné"
            except Exception:
                pass
            return "Non renseigné"
        return ""

    @staticmethod
    def _parameter_value(sheet, name):
        if not name:
            return ""
        try:
            parameter = sheet.LookupParameter(name)
            if parameter is None:
                return ""
            return parameter.AsString() or parameter.AsValueString() or ""
        except Exception:
            return ""

    def parameter_changed(self):
        w = self.window
        parameter = w.SheetExplorerParameter.SelectedItem
        self._updating_parameter_values = True
        try:
            values = set()
            if parameter and parameter != "Tous les paramètres":
                values = set(self._parameter_value(sheet, parameter)
                             for sheet in self._ordered_sheets)
            w.SheetExplorerValue.ItemsSource = (
                ["Toutes les valeurs"] + sorted(values))
            w.SheetExplorerValue.SelectedIndex = 0
        finally:
            self._updating_parameter_values = False
        self.refresh()

    def value_changed(self):
        if not self._updating_parameter_values:
            self.refresh()

    def refresh(self):
        w = self.window
        query = (w.SheetExplorerSearch.Text or "").strip().lower()
        unused = bool(w.SheetExplorerUnused.IsChecked)
        mode = max(0, w.SheetExplorerGrouping.SelectedIndex)
        used = self._used_paths()
        selected_parameter = w.SheetExplorerParameter.SelectedItem
        selected_value = w.SheetExplorerValue.SelectedItem
        filter_parameter = (selected_parameter
                            if selected_parameter != "Tous les paramètres" else None)
        filter_value = (selected_value
                        if selected_value != "Toutes les valeurs" else None)
        old_scroll = None
        try:
            old_scroll = self._scroll_offset()
        except Exception:
            pass
        self._rendering = True
        try:
            w.SheetExplorerList.Items.Clear()
            # Ordre trié calculé une fois à l'ouverture (BUG-EXPORT-055) ;
            # seuls le filtre, le regroupement et les indicateurs sont
            # réévalués ici.
            ordered = self._ordered_sheets
            rows = []
            for sheet in ordered:
                uid = str(sheet.UniqueId)
                if query not in (sheet.SheetNumber or "").lower() and query not in (sheet.Name or "").lower():
                    continue
                if unused and uid in used:
                    continue
                if filter_parameter and filter_value is not None:
                    if self._parameter_value(sheet, filter_parameter) != filter_value:
                        continue
                rows.append((self._group(sheet, mode), sheet))
            if mode == 2:
                rows.sort(key=lambda entry: (entry[0], (entry[1].Name or "").lower()))
            elif mode >= 3:
                rows.sort(key=lambda entry: (entry[0], (entry[1].SheetNumber or "").lower()))
            group = None
            for heading, sheet in rows:
                if mode and heading != group:
                    group = heading
                    header = ListBoxItem()
                    header.Tag = self.GROUP_TAG_PREFIX + heading
                    header.Content = TextBlock(Text=("> " if heading in self._collapsed_groups else "v ") + heading)
                    w.SheetExplorerList.Items.Add(header)
                if mode and heading in self._collapsed_groups:
                    continue
                uid = str(sheet.UniqueId)
                entry = ListBoxItem()
                entry.Tag = uid
                entry.Content = "{0} — {1}{2}".format(
                    sheet.SheetNumber or "", sheet.Name or "",
                    "  ✓" if uid in used else "")
                if uid in used:
                    entry.ToolTip = "Déjà ajoutée :\n" + "\n".join(used[uid])
                w.SheetExplorerList.Items.Add(entry)
                if uid in self.selected_ids:
                    entry.IsSelected = True
        finally:
            self._rendering = False
        if old_scroll is not None:
            self._restore_scroll(old_scroll)
        self._update_count()

    def _scroll_offset(self):
        viewer = self._scroll_viewer()
        return viewer.VerticalOffset if viewer else None

    def _scroll_viewer(self):
        def find(root):
            if root is None:
                return None
            from System.Windows.Controls import ScrollViewer
            if isinstance(root, ScrollViewer):
                return root
            for i in range(VisualTreeHelper.GetChildrenCount(root)):
                found = find(VisualTreeHelper.GetChild(root, i))
                if found:
                    return found
            return None
        return find(self.window.SheetExplorerList)

    def _restore_scroll(self, value):
        viewer = self._scroll_viewer()
        if viewer is not None:
            viewer.ScrollToVerticalOffset(value)

    def selection_changed(self, args):
        if self._rendering:
            return
        for item in args.RemovedItems:
            tag = getattr(item, "Tag", None)
            if tag and self._group_from_tag(tag) is None:
                self.selected_ids.discard(str(tag))
        for item in args.AddedItems:
            tag = getattr(item, "Tag", None)
            if tag and self._group_from_tag(tag) is None:
                self.selected_ids.add(str(tag))
            elif item is not None and getattr(item, "IsSelected", False):
                # BUG-EXPORT-053 : un en-tête de groupe attrapé par une
                # sélection Maj est désélectionné et ne compte jamais comme
                # une feuille.
                item.IsSelected = False
        self._update_count()

    def _key_down(self, sender, args):
        if args.Key == Key.A and (Keyboard.Modifiers & ModifierKeys.Control):
            self._rendering = True
            try:
                for item in self.window.SheetExplorerList.Items:
                    tag = getattr(item, "Tag", None)
                    # BUG-EXPORT-053 : Ctrl+A sélectionne les feuilles
                    # visibles, jamais les en-têtes de groupe.
                    if tag and self._group_from_tag(tag) is None:
                        item.IsSelected = True
                        self.selected_ids.add(str(tag))
            finally:
                self._rendering = False
            self._update_count()
            args.Handled = True

    def _update_count(self):
        count = len(self.selected_ids)
        self.window.SheetExplorerSelectionInfo.Text = "{0} feuille(s) sélectionnée(s)".format(count)
        self.window.SheetExplorerAddButton.Content = "Ajouter ({0})".format(count)
        self.window.SheetExplorerAddButton.IsEnabled = count > 0

    def _build_context_menu(self):
        menu = ContextMenu()
        current = MenuItem()
        current.Header = "Ajouter au dossier sélectionné"
        current.Click += lambda sender, args: self.add_to_current()
        menu.Items.Add(current)
        choose = MenuItem()
        choose.Header = "Ajouter à un autre dossier…"
        choose.Click += lambda sender, args: self.choose_destination()
        menu.Items.Add(choose)
        self.window.SheetExplorerList.ContextMenu = menu

    def _current_destination(self):
        w = self.window
        if w._selected_kind == "FOLDER" and w._selected_folder:
            return w._selected_folder.id
        if w._selected_set:
            return w._selected_set.id
        return None

    def _items(self):
        # L'ordre affiché fait foi : les feuilles sélectionnées suivent
        # l'ordre trié calculé à l'ouverture (BUG-EXPORT-055).
        ordered = [sheet for sheet in self._ordered_sheets
                   if str(sheet.UniqueId) in self.selected_ids]
        return self.window.controller.export_service.build_publication_items(ordered)

    def add_to_current(self):
        self.add_to(self._current_destination())

    def choose_destination(self):
        from pyrevit import forms
        folders = list(self.window._folders) + list(self.window._carnets)
        # Liste de couples plutôt qu'un dictionnaire : deux dossiers de même
        # nom ne doivent pas se masquer silencieusement (l'identifiant
        # désambiguïse l'étiquette).
        options = sorted(
            (x for x in folders
             if str(x.id) != "default" and getattr(x, "persistent", True)),
            key=lambda x: self._destination_label(x),
        )
        labels = [self._destination_label(x) for x in options]
        selected = forms.SelectFromList.show(labels, title="Dossier de destination")
        if not selected:
            return
        match = next((x for x in options
                      if self._destination_label(x) == selected), None)
        if match is not None:
            self.add_to(match.id)

    @staticmethod
    def _destination_label(folder):
        return "{0} [{1}]".format(folder.name, folder.id)

    def add_to(self, destination):
        from pyrevit import forms, script
        if not destination:
            forms.alert("Sélectionnez un dossier de publication cible.", title="Export")
            return
        try:
            added, ignored = self.window.controller.add_sheets_to_folder(self._items(), destination)
            if added:
                manager = self.window._drag_drop_manager
                expanded = manager._expanded()
                offset = manager._scroll_offset()
                self.window._refresh_tree()
                manager._restore_expanded(expanded)
                manager.expand_to_key("CARNET:" + str(destination))
                manager._restore_scroll(offset)
            self.refresh()
            self.window.SheetExplorerSelectionInfo.Text = "{0} ajoutée(s), {1} ignorée(s)".format(added, ignored)
        except Exception as exc:
            script.get_logger().exception("Ajout de feuilles impossible")
            forms.alert("Ajout impossible : {0}".format(exc), title="Export")

    def mouse_down(self, args):
        node = args.OriginalSource
        while node is not None and not isinstance(node, ListBoxItem):
            try:
                node = VisualTreeHelper.GetParent(node)
            except Exception:
                node = None
        tag = getattr(node, "Tag", None)
        group = self._group_from_tag(tag)
        if group is not None:
            if group in self._collapsed_groups:
                self._collapsed_groups.remove(group)
            else:
                self._collapsed_groups.add(group)
            self.refresh()
            args.Handled = True
            self._mouse_point = None
            return
        self._mouse_point = args.GetPosition(self.window.SheetExplorerList)

    def mouse_move(self, args):
        if args.LeftButton != MouseButtonState.Pressed or self._mouse_point is None:
            return
        point = args.GetPosition(self.window.SheetExplorerList)
        if abs(point.X - self._mouse_point.X) + abs(point.Y - self._mouse_point.Y) < 8:
            return
        self._mouse_point = None
        if not self.selected_ids:
            return
        payload = DataObject()
        payload.SetData(self.DATA_FORMAT, json.dumps(sorted(self.selected_ids)))
        DragDrop.DoDragDrop(self.window.SheetExplorerList, payload, DragDropEffects.Copy)

    def _destination_from_event(self, args):
        node = self.window._drag_drop_manager._item(args.OriginalSource)
        if node is None or not getattr(node, "Tag", None):
            return None
        tag = node.Tag
        if tag[0] == "SHEET":
            return tag[2].id
        if tag[0] == "CARNET" and getattr(tag[1], "persistent", False):
            return tag[1].id
        if tag[0] == "FOLDER":
            return tag[1].id
        return None

    def _drag_over(self, sender, args):
        if not args.Data.GetDataPresent(self.DATA_FORMAT):
            return
        manager = self.window._drag_drop_manager
        manager._auto_scroll(args)
        node = manager._item(args.OriginalSource)
        destination = self._destination_from_event(args)
        valid = destination is not None and str(destination) != "default"
        manager._hover_expand(node, "APPEND" if valid else None)
        if valid:
            manager._show_drop_indicator(node, "APPEND")
        else:
            manager._clear_drop_indicator()
        args.Effects = DragDropEffects.Copy if valid else DragDropEffects.None
        args.Handled = True

    def _drop(self, sender, args):
        if not args.Data.GetDataPresent(self.DATA_FORMAT):
            return
        destination = self._destination_from_event(args)
        self.window._drag_drop_manager._clear_drop_indicator()
        if destination and str(destination) != "default":
            try:
                ids = set(json.loads(str(args.Data.GetData(self.DATA_FORMAT))))
                self.selected_ids = ids.intersection(set(self.sheets))
                self.add_to(destination)
            except Exception as exc:
                # BUG-EXPORT-054 : un dépôt échoué doit être visible pour
                # l'utilisateur, jamais silencieux (règle BUG-EXPORT-025).
                logger = self._logger()
                if logger is not None:
                    try:
                        logger.exception(
                            "Depot de l'explorateur de feuilles impossible")
                    except Exception:
                        pass
                from pyrevit import forms
                forms.alert("Ajout impossible : {0}".format(exc), title="Export")
        args.Handled = True

