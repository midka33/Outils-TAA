# -*- coding: utf-8 -*-
"""Glisser-déposer des dossiers, carnets et mises en page dans l'arborescence Export."""

import json

from System.Windows import DragDrop, DragDropEffects, DataObject, SystemParameters, Thickness
from System.Windows.Controls import TreeViewItem
from System.Windows.Input import MouseButtonState, Keyboard, Key
from System.Windows.Media import SolidColorBrush, Color


class PublicationTreeDragDrop(object):
    """Gère sélection multiple, déplacement et réordonnancement."""

    DATA_FORMAT = "OutilsTAA.Export.DragPayload"
    SELECTED_BRUSH = SolidColorBrush(Color.FromRgb(250, 100, 31))
    DROP_BRUSH = SolidColorBrush(Color.FromRgb(250, 100, 31))
    DROP_BACKGROUND = SolidColorBrush(Color.FromArgb(45, 250, 100, 31))

    def __init__(self, window):
        self.window = window
        self.drag_node = None
        self.drag_started = False
        self.selected = []
        self.drop_node = None
        self.drop_mode = None
        tree = window.PublicationTree
        tree.AllowDrop = True
        tree.PreviewMouseLeftButtonDown += self._mouse_down
        tree.PreviewMouseMove += self._mouse_move
        tree.DragOver += self._drag_over
        tree.DragLeave += self._drag_leave
        tree.Drop += self._drop

    def _tree_item_from_source(self, source):
        """Remonte uniquement la hiérarchie logique WPF, sans VisualTreeHelper."""
        current = source
        visited = set()
        while current is not None:
            if isinstance(current, TreeViewItem):
                return current
            marker = id(current)
            if marker in visited:
                return None
            visited.add(marker)
            try:
                current = getattr(current, "Parent", None)
            except Exception:
                return None
            if current is None:
                try:
                    current = getattr(source, "TemplatedParent", None)
                except Exception:
                    return None
        return None

    def _all_tree_items(self):
        result = []
        try:
            roots = list(self.window.PublicationTree.Items)
        except Exception:
            return result
        for root in roots:
            self._collect_tree_items(root, result)
        return result

    def _collect_tree_items(self, node, result):
        if not isinstance(node, TreeViewItem):
            return
        result.append(node)
        try:
            children = list(node.Items)
        except Exception:
            return
        for child in children:
            self._collect_tree_items(child, result)

    def _persistent_nodes(self, kind):
        result = []
        for node in self._all_tree_items():
            tag = getattr(node, "Tag", None)
            if not tag or len(tag) < 2 or tag[0] != kind:
                continue
            if kind == "CARNET":
                value = tag[1]
                if getattr(value, "persistent", False) and getattr(value, "id", None):
                    result.append(node)
            elif kind == "FOLDER":
                value = tag[1]
                if (getattr(value, "persistent", False)
                        and getattr(value, "id", None)
                        and str(value.id) != "default"):
                    result.append(node)
            else:
                item = tag[1]
                carnet = tag[2]
                if getattr(carnet, "persistent", False) and getattr(item, "unique_id", None):
                    result.append(node)
        return result

    def _folder_nodes(self):
        return [node for node in self._all_tree_items()
                if getattr(node, "Tag", None) and node.Tag[0] == "FOLDER"]

    def _selection_key(self, tag):
        if tag[0] == "FOLDER":
            return "FOLDER:" + str(tag[1].id)
        if tag[0] == "CARNET":
            return "CARNET:" + str(tag[1].id)
        return "SHEET:" + str(tag[2].id) + ":" + str(tag[1].unique_id)

    def _refresh_visual_selection(self):
        selected = set(self.selected)
        for kind in ("FOLDER", "CARNET", "SHEET"):
            for node in self._persistent_nodes(kind):
                if self._selection_key(node.Tag) in selected:
                    node.Background = self.SELECTED_BRUSH
                    node.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
                else:
                    node.ClearValue(TreeViewItem.BackgroundProperty)
                    node.ClearValue(TreeViewItem.ForegroundProperty)

    def _set_selection(self, keys):
        self.selected = []
        for key in keys:
            if key and key not in self.selected:
                self.selected.append(key)
        self._refresh_visual_selection()

    def _selection_from_node(self, node):
        tag = getattr(node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET", "SHEET"):
            return None
        if tag[0] == "FOLDER":
            if not getattr(tag[1], "persistent", False) or str(getattr(tag[1], "id", "")) == "default":
                return None
        elif tag[0] == "CARNET" and not getattr(tag[1], "persistent", False):
            return None
        elif tag[0] == "SHEET" and not getattr(tag[2], "persistent", False):
            return None
        return self._selection_key(tag)

    def _ordered_keys(self, node):
        tag = node.Tag
        if tag[0] == "FOLDER":
            return [self._selection_key(n.Tag) for n in self._persistent_nodes("FOLDER")]
        if tag[0] == "CARNET":
            return [self._selection_key(n.Tag) for n in self._persistent_nodes("CARNET")]
        parent = getattr(node, "Parent", None)
        if parent is None:
            return []
        carnet = tag[2]
        return [self._selection_key(child.Tag) for child in list(parent.Items)
                if getattr(child, "Tag", None) and child.Tag[0] == "SHEET"
                and str(child.Tag[2].id) == str(carnet.id)]

    def _mouse_down(self, sender, args):
        node = self._tree_item_from_source(args.OriginalSource)
        self.drag_node = node
        self.drag_started = False
        if node is None:
            self._set_selection([])
            return
        key = self._selection_from_node(node)
        if key is None:
            return
        ctrl = Keyboard.IsKeyDown(Key.LeftCtrl) or Keyboard.IsKeyDown(Key.RightCtrl)
        shift = Keyboard.IsKeyDown(Key.LeftShift) or Keyboard.IsKeyDown(Key.RightShift)
        if shift and self.selected:
            ordered = self._ordered_keys(node)
            try:
                a = ordered.index(self.selected[-1])
                b = ordered.index(key)
                self._set_selection(ordered[min(a, b):max(a, b) + 1])
            except ValueError:
                self._set_selection([key])
            args.Handled = True
        elif ctrl:
            keys = list(self.selected)
            if key in keys:
                keys.remove(key)
            else:
                keys.append(key)
            self._set_selection(keys)
            args.Handled = True
        else:
            self._set_selection([key])

    def _mouse_move(self, sender, args):
        if self.drag_node is None or self.drag_started or args.LeftButton != MouseButtonState.Pressed:
            return
        try:
            point = args.GetPosition(self.drag_node)
            if abs(point.X) < SystemParameters.MinimumHorizontalDragDistance and abs(point.Y) < SystemParameters.MinimumVerticalDragDistance:
                return
        except Exception:
            pass
        tag = getattr(self.drag_node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET", "SHEET"):
            return
        if tag[0] == "FOLDER" and (not getattr(tag[1], "persistent", False) or str(getattr(tag[1], "id", "")) == "default"):
            return
        if tag[0] == "CARNET" and not getattr(tag[1], "persistent", False):
            return
        if tag[0] == "SHEET" and not getattr(tag[2], "persistent", False):
            return
        if not self.selected:
            self._set_selection([self._selection_key(tag)])
        kind = tag[0]
        payload = [key for key in self.selected if key.startswith(kind + ":")]
        if not payload:
            return
        self.drag_started = True
        data = DataObject()
        data.SetData(self.DATA_FORMAT, json.dumps({"kind": kind, "items": payload}))
        try:
            DragDrop.DoDragDrop(self.drag_node, data, DragDropEffects.Move)
        finally:
            self.drag_node = None
            self.drag_started = False
            self._clear_drop_indicator()

    def _get_payload(self, args):
        try:
            if args.Data.GetDataPresent(self.DATA_FORMAT):
                raw = args.Data.GetData(self.DATA_FORMAT)
                return json.loads(str(raw)) if raw else None
        except Exception:
            pass
        return None

    def _folder_is_descendant(self, folder_id, potential_parent_id):
        current_id = potential_parent_id
        visited = set()
        while current_id and current_id not in visited:
            if str(current_id) == str(folder_id):
                return True
            visited.add(str(current_id))
            folder = self.window._folders_by_id.get(current_id)
            if folder is None:
                return False
            current_id = getattr(folder, "parent_id", None)
        return False

    def _folder_drop_mode(self, target, args):
        try:
            height = float(target.ActualHeight)
            point = args.GetPosition(target)
            if height > 0:
                third = height / 3.0
                if point.Y < third:
                    return "BEFORE"
                if point.Y > height - third:
                    return "AFTER"
        except Exception:
            pass
        return "INSIDE"

    def _target_mode(self, payload, target, args=None):
        tag = getattr(target, "Tag", None)
        if not tag or len(tag) < 2:
            return None
        kind = payload.get("kind")
        keys = payload.get("items", [])
        if kind == "FOLDER" and tag[0] == "FOLDER":
            ids = [x.split(":", 1)[1] for x in keys if ":" in x]
            if not ids:
                return None
            target_id = str(tag[1].id)
            if target_id == "default":
                return None
            for source_id in ids:
                if source_id == target_id or source_id == "default":
                    return None
                if self._folder_is_descendant(source_id, target_id):
                    return None
            return self._folder_drop_mode(target, args) if args is not None else "INSIDE"
        if kind == "CARNET" and tag[0] in ("FOLDER", "CARNET"):
            ids = [x.split(":", 1)[1] for x in keys if ":" in x]
            if tag[0] == "CARNET" and str(tag[1].id) in [str(x) for x in ids]:
                return None
            return "FOLDER" if tag[0] == "FOLDER" else "BEFORE"
        if kind == "SHEET" and tag[0] in ("SHEET", "CARNET"):
            if tag[0] == "CARNET":
                return "APPEND" if all(len(x.split(":", 2)) == 3 and x.split(":", 2)[1] == str(tag[1].id) for x in keys) else None
            target_key = self._selection_key(tag)
            if target_key in keys:
                return None
            return "BEFORE" if all(len(x.split(":", 2)) == 3 and x.split(":", 2)[1] == str(tag[2].id) for x in keys) else None
        return None

    def _show_drop_indicator(self, node, mode):
        if self.drop_node is node and self.drop_mode == mode:
            return
        self._clear_drop_indicator()
        self.drop_node = node
        self.drop_mode = mode
        node.BorderBrush = self.DROP_BRUSH
        if mode == "BEFORE":
            node.BorderThickness = Thickness(0, 2, 0, 0)
        elif mode == "AFTER":
            node.BorderThickness = Thickness(0, 0, 0, 2)
        else:
            node.BorderThickness = Thickness(2, 2, 2, 2)
            node.Background = self.DROP_BACKGROUND

    def _clear_drop_indicator(self):
        if self.drop_node is not None:
            try:
                self.drop_node.ClearValue(TreeViewItem.BorderBrushProperty)
                self.drop_node.ClearValue(TreeViewItem.BorderThicknessProperty)
                self.drop_node.ClearValue(TreeViewItem.BackgroundProperty)
            except Exception:
                pass
        self.drop_node = None
        self.drop_mode = None
        self._refresh_visual_selection()

    def _drag_over(self, sender, args):
        target = self._tree_item_from_source(args.OriginalSource)
        payload = self._get_payload(args)
        mode = self._target_mode(payload, target, args) if target is not None and payload is not None else None
        if mode is None:
            self._clear_drop_indicator()
            args.Effects = DragDropEffects.None
        else:
            self._show_drop_indicator(target, mode)
            args.Effects = DragDropEffects.Move
        args.Handled = True

    def _drag_leave(self, sender, args):
        self._clear_drop_indicator()

    def _expanded_ids(self):
        folders = []
        carnets = []
        for node in self._folder_nodes():
            if getattr(node, "IsExpanded", False):
                tag = getattr(node, "Tag", None)
                if tag and getattr(tag[1], "id", None):
                    folders.append(str(tag[1].id))
        for node in self._persistent_nodes("CARNET"):
            if getattr(node, "IsExpanded", False):
                tag = getattr(node, "Tag", None)
                if tag and getattr(tag[1], "id", None):
                    carnets.append(str(tag[1].id))
        return folders, carnets

    def _restore_expanded_ids(self, expanded):
        folder_ids, carnet_ids = expanded
        wanted_folders = set(str(value) for value in folder_ids or [])
        wanted_carnets = set(str(value) for value in carnet_ids or [])
        for node in self._folder_nodes():
            tag = getattr(node, "Tag", None)
            if tag and str(getattr(tag[1], "id", "")) in wanted_folders:
                node.IsExpanded = True
        for node in self._persistent_nodes("CARNET"):
            tag = getattr(node, "Tag", None)
            if tag and str(getattr(tag[1], "id", "")) in wanted_carnets:
                node.IsExpanded = True

    def _next_folder_sibling_id(self, target, moving_ids):
        target_folder = target.Tag[1]
        siblings = [folder for folder in self.window._folders
                    if str(getattr(folder, "parent_id", None)) == str(getattr(target_folder, "parent_id", None))
                    and str(getattr(folder, "id", "")) not in moving_ids]
        siblings.sort(key=lambda value: getattr(value, "sort_order", 0))
        for index, folder in enumerate(siblings):
            if str(folder.id) == str(target_folder.id) and index + 1 < len(siblings):
                return siblings[index + 1].id
        return None

    def _drop(self, sender, args):
        target = self._tree_item_from_source(args.OriginalSource)
        payload = self._get_payload(args)
        mode = self._target_mode(payload, target, args) if target is not None and payload is not None else None
        if mode is None:
            self._clear_drop_indicator()
            args.Handled = True
            return
        try:
            expanded = self._expanded_ids()
            if payload["kind"] == "FOLDER":
                moved = self._move_folders(payload, target, mode)
            elif payload["kind"] == "CARNET":
                ids = [x.split(":", 1)[1] for x in payload["items"]]
                if target.Tag[0] == "FOLDER":
                    moved = self.window.controller.move_persistent_many(ids, target.Tag[1].id, None)
                else:
                    moved = self.window.controller.move_persistent_many(ids, target.Tag[1].folder_id, target.Tag[1].id)
            else:
                moved = self._move_sheets(payload, target)
            if moved:
                self._set_selection([])
                self.window._selected_set = None
                self.window._selected_item = None
                self.window._selected_kind = None
                self.window._selected_folder = None
                self.window._refresh_tree()
                self._restore_expanded_ids(expanded)
                self.window._update_selection_info()
        except Exception as exc:
            try:
                from pyrevit import forms
                forms.alert("Impossible de réorganiser les éléments.\n\n{0}".format(exc), title="Export")
            except Exception:
                pass
        finally:
            self._clear_drop_indicator()
        args.Handled = True

    def _move_folders(self, payload, target, mode):
        keys = payload.get("items", [])
        ids = [key.split(":", 1)[1] for key in keys if ":" in key]
        if not ids or target.Tag[0] != "FOLDER":
            return False
        target_folder = target.Tag[1]
        if mode == "INSIDE":
            parent_id = target_folder.id
            before_id = None
        else:
            parent_id = target_folder.parent_id
            before_id = target_folder.id if mode == "BEFORE" else self._next_folder_sibling_id(target, set(ids))
        return self.window.controller.move_folders_many(ids, parent_id, before_id)

    def _move_sheets(self, payload, target):
        keys = payload.get("items", [])
        carnet_id = None
        selected_ids = []
        for key in keys:
            parts = key.split(":", 2)
            if len(parts) != 3:
                return False
            if carnet_id is None:
                carnet_id = parts[1]
            if parts[1] != carnet_id:
                return False
            selected_ids.append(parts[2])
        if not carnet_id or not selected_ids:
            return False
        target_carnet = target.Tag[2] if target.Tag[0] == "SHEET" else target.Tag[1]
        if str(target_carnet.id) != str(carnet_id):
            return False
        carnet = next((value for value in self.window._carnets if str(getattr(value, "id", "")) == str(carnet_id)), None)
        if carnet is None or not carnet.persistent:
            return False
        selected = [item for item in carnet.items if str(item.unique_id) in selected_ids]
        if not selected:
            return False
        remaining = [item for item in carnet.items if str(item.unique_id) not in selected_ids]
        if target.Tag[0] == "CARNET":
            index = len(remaining)
        else:
            target_uid = str(target.Tag[1].unique_id)
            if target_uid in selected_ids:
                return False
            index = next((i for i, item in enumerate(remaining) if str(item.unique_id) == target_uid), len(remaining))
        carnet.items = remaining[:index] + selected + remaining[index:]
        self.window.controller.save_persistent(carnet)
        return True
