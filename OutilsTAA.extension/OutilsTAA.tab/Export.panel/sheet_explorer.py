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

    def __init__(self, window, sheets):
        self.window = window
        self.sheets = dict((str(sheet.UniqueId), sheet) for sheet in sheets
                           if sheet is not None and getattr(sheet, "UniqueId", None))
        self.selected_ids = set()
        self._collapsed_groups = set()
        self._rendering = False
        self._mouse_point = None
        self._last_width = 310.0
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
        window.SheetExplorerList.PreviewKeyDown += self._key_down
        window.PublicationTree.PreviewDragOver += self._drag_over
        window.PublicationTree.PreviewDrop += self._drop
        window.Closing += self._closing
        self._build_context_menu()
        self.refresh()

    def _restore_settings(self):
        self._visible = True
        try:
            with open(self._settings_path, "r") as handle:
                state = json.load(handle)
            self._visible = bool(state.get("visible", True))
            self._last_width = max(210.0, min(520.0, float(state.get("width", 310))))
        except Exception:
            pass
        self._apply_visibility()

    def _apply_visibility(self):
        w = self.window
        w.SheetExplorerPanel.Visibility = Visibility.Visible if self._visible else Visibility.Collapsed
        w.SheetExplorerSplitter.Visibility = Visibility.Visible if self._visible else Visibility.Collapsed
        w.SheetExplorerColumn.Width = GridLength(self._last_width if self._visible else 0, GridUnitType.Pixel)
        w.SheetExplorerSplitterColumn.Width = GridLength(5 if self._visible else 0, GridUnitType.Pixel)
        w.SheetExplorerToggle.Content = "Masquer les feuilles" if self._visible else "Afficher les feuilles"

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
            pass

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

    def refresh(self):
        w = self.window
        query = (w.SheetExplorerSearch.Text or "").strip().lower()
        unused = bool(w.SheetExplorerUnused.IsChecked)
        mode = max(0, w.SheetExplorerGrouping.SelectedIndex)
        used = self._used_paths()
        old_scroll = None
        try:
            old_scroll = self._scroll_offset()
        except Exception:
            pass
        self._rendering = True
        try:
            w.SheetExplorerList.Items.Clear()
            ordered = sorted(self.sheets.values(),
                             key=lambda s: ((s.SheetNumber or "").lower(),
                                            (s.Name or "").lower()))
            rows = []
            for sheet in ordered:
                uid = str(sheet.UniqueId)
                if query not in (sheet.SheetNumber or "").lower() and query not in (sheet.Name or "").lower():
                    continue
                if unused and uid in used:
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
                    header.Tag = "GROUP:" + heading
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
            uid = getattr(item, "Tag", None)
            if uid:
                self.selected_ids.discard(str(uid))
        for item in args.AddedItems:
            uid = getattr(item, "Tag", None)
            if uid:
                self.selected_ids.add(str(uid))
        self._update_count()

    def _key_down(self, sender, args):
        if args.Key == Key.A and (Keyboard.Modifiers & ModifierKeys.Control):
            self._rendering = True
            try:
                for item in self.window.SheetExplorerList.Items:
                    if getattr(item, "Tag", None):
                        item.IsSelected = True
                        self.selected_ids.add(str(item.Tag))
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
        ordered = sorted((self.sheets[uid] for uid in self.selected_ids if uid in self.sheets),
                         key=lambda s: ((s.SheetNumber or "").lower(), (s.Name or "").lower()))
        return self.window.controller.export_service.build_publication_items(ordered)

    def add_to_current(self):
        self.add_to(self._current_destination())

    def choose_destination(self):
        from pyrevit import forms
        folders = list(self.window._folders) + list(self.window._carnets)
        options = dict(("{0} [{1}]".format(x.name, x.id), x.id) for x in folders
                       if str(x.id) != "default" and getattr(x, "persistent", True))
        selected = forms.SelectFromList.show(sorted(options), title="Dossier de destination")
        if selected:
            self.add_to(options[selected])

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
        if tag and str(tag).startswith("GROUP:"):
            group = str(tag)[6:]
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
        args.Effects = DragDropEffects.Copy if valid else DragDropEffects.None
        args.Handled = True

    def _drop(self, sender, args):
        if not args.Data.GetDataPresent(self.DATA_FORMAT):
            return
        destination = self._destination_from_event(args)
        if destination and str(destination) != "default":
            try:
                ids = set(json.loads(str(args.Data.GetData(self.DATA_FORMAT))))
                self.selected_ids = ids.intersection(set(self.sheets))
                self.add_to(destination)
            except Exception:
                pass
        args.Handled = True
