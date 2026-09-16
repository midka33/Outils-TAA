# -*- coding: utf-8 -*-
import json
from System.Windows import DragDrop, DragDropEffects, DataObject, SystemParameters, Thickness
from System.Windows.Controls import TreeViewItem
from System.Windows.Input import MouseButtonState, Keyboard, Key, ModifierKeys
from System.Windows.Media import SolidColorBrush, Color


class PublicationTreeDragDrop(object):
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

    def _item(self, source):
        current = source
        seen = set()
        while current is not None:
            if isinstance(current, TreeViewItem):
                return current
            marker = id(current)
            if marker in seen:
                return None
            seen.add(marker)
            try:
                current = getattr(current, "Parent", None)
            except Exception:
                return None
        return None

    def _all(self):
        result = []
        try:
            roots = list(self.window.PublicationTree.Items)
        except Exception:
            return result
        for root in roots:
            self._collect(root, result)
        return result

    def _collect(self, node, result):
        if not isinstance(node, TreeViewItem):
            return
        result.append(node)
        try:
            children = list(node.Items)
        except Exception:
            return
        for child in children:
            self._collect(child, result)

    def _nodes(self, kind):
        result = []
        for node in self._all():
            tag = getattr(node, "Tag", None)
            if not tag or len(tag) < 2 or tag[0] != kind:
                continue
            if kind == "FOLDER":
                if getattr(tag[1], "persistent", False) and str(tag[1].id) != "default":
                    result.append(node)
            elif kind == "CARNET":
                if getattr(tag[1], "persistent", False) and getattr(tag[1], "id", None):
                    result.append(node)
            elif getattr(tag[2], "persistent", False) and getattr(tag[1], "unique_id", None):
                result.append(node)
        return result

    def _key(self, tag):
        if tag[0] == "FOLDER":
            return "FOLDER:" + str(tag[1].id)
        if tag[0] == "CARNET":
            return "CARNET:" + str(tag[1].id)
        return "SHEET:" + str(tag[2].id) + ":" + str(tag[1].unique_id)

    def _valid_key(self, node):
        tag = getattr(node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET", "SHEET"):
            return None
        if tag[0] == "FOLDER" and (not getattr(tag[1], "persistent", False) or str(tag[1].id) == "default"):
            return None
        if tag[0] == "CARNET" and not getattr(tag[1], "persistent", False):
            return None
        if tag[0] == "SHEET" and not getattr(tag[2], "persistent", False):
            return None
        return self._key(tag)

    def _select(self, keys):
        self.selected = []
        for key in keys:
            if key and key not in self.selected:
                self.selected.append(key)
        selected = set(self.selected)
        for kind in ("FOLDER", "CARNET", "SHEET"):
            for node in self._nodes(kind):
                if self._key(node.Tag) in selected:
                    node.Background = self.SELECTED_BRUSH
                    node.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
                else:
                    node.ClearValue(TreeViewItem.BackgroundProperty)
                    node.ClearValue(TreeViewItem.ForegroundProperty)

    def _ordered(self, node):
        tag = node.Tag
        if tag[0] in ("FOLDER", "CARNET"):
            return [self._key(n.Tag) for n in self._nodes(tag[0])]
        parent = getattr(node, "Parent", None)
        if parent is None:
            return []
        cid = str(tag[2].id)
        return [self._key(n.Tag) for n in list(parent.Items) if getattr(n, "Tag", None) and n.Tag[0] == "SHEET" and str(n.Tag[2].id) == cid]

    def _mouse_down(self, sender, args):
        node = self._item(args.OriginalSource)
        self.drag_node = node
        self.drag_started = False
        key = self._valid_key(node) if node is not None else None
        if key is None:
            if node is None:
                self._select([])
            return
        modifiers = Keyboard.Modifiers
        if modifiers & ModifierKeys.Shift and self.selected:
            ordered = self._ordered(node)
            try:
                a = ordered.index(self.selected[-1])
                b = ordered.index(key)
                self._select(ordered[min(a, b):max(a, b) + 1])
            except ValueError:
                self._select([key])
            args.Handled = True
        elif modifiers & ModifierKeys.Control:
            values = list(self.selected)
            if key in values:
                values.remove(key)
            else:
                values.append(key)
            self._select(values)
            args.Handled = True
        else:
            self._select([key])

    def _mouse_move(self, sender, args):
        if self.drag_node is None or self.drag_started or args.LeftButton != MouseButtonState.Pressed:
            return
        try:
            p = args.GetPosition(self.drag_node)
            if abs(p.X) < SystemParameters.MinimumHorizontalDragDistance and abs(p.Y) < SystemParameters.MinimumVerticalDragDistance:
                return
        except Exception:
            pass
        tag = getattr(self.drag_node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET", "SHEET"):
            return
        if not self.selected:
            self._select([self._key(tag)])
        kind = tag[0]
        items = [key for key in self.selected if key.startswith(kind + ":")]
        if not items:
            return
        self.drag_started = True
        data = DataObject()
        data.SetData(self.DATA_FORMAT, json.dumps({"kind": kind, "items": items}))
        try:
            DragDrop.DoDragDrop(self.drag_node, data, DragDropEffects.Move)
        finally:
            self.drag_node = None
            self.drag_started = False
            self._clear_drop_indicator()

    def _payload(self, args):
        try:
            if args.Data.GetDataPresent(self.DATA_FORMAT):
                raw = args.Data.GetData(self.DATA_FORMAT)
                return json.loads(str(raw)) if raw else None
        except Exception:
            pass
        return None

    def _mode(self, target, args):
        try:
            h = float(target.ActualHeight)
            y = args.GetPosition(target).Y
            if h > 0:
                third = h / 3.0
                if y < third:
                    return "BEFORE"
                if y > h - third:
                    return "AFTER"
        except Exception:
            pass
        return "INSIDE"

    def _folder_descendant(self, source_id, parent_id):
        current = parent_id
        seen = set()
        while current is not None and str(current) not in seen:
            if str(current) == str(source_id):
                return True
            seen.add(str(current))
            folder = self.window._folders_by_id.get(current)
            if folder is None:
                return False
            current = getattr(folder, "parent_id", None)
        return False

    def _target_mode(self, payload, target, args):
        tag = getattr(target, "Tag", None)
        if not payload or not tag or len(tag) < 2:
            return None
        kind = payload.get("kind")
        keys = payload.get("items", [])
        if kind == "FOLDER" and tag[0] == "FOLDER":
            ids = [x.split(":", 1)[1] for x in keys if ":" in x]
            if not ids or str(tag[1].id) == "default":
                return None
            for source_id in ids:
                if str(source_id) == str(tag[1].id) or self._folder_descendant(source_id, tag[1].id):
                    return None
            return self._mode(target, args)
        if kind == "CARNET" and tag[0] in ("FOLDER", "CARNET"):
            ids = [x.split(":", 1)[1] for x in keys if ":" in x]
            if tag[0] == "CARNET" and str(tag[1].id) in [str(x) for x in ids]:
                return None
            return "FOLDER" if tag[0] == "FOLDER" else self._mode(target, args)
        if kind == "SHEET" and tag[0] in ("SHEET", "CARNET"):
            if tag[0] == "CARNET":
                return "APPEND" if all(len(x.split(":", 2)) == 3 and x.split(":", 2)[1] == str(tag[1].id) for x in keys) else None
            if self._key(tag) in keys:
                return None
            return self._mode(target, args) if all(len(x.split(":", 2)) == 3 and x.split(":", 2)[1] == str(tag[2].id) for x in keys) else None
        return None

    def _show_drop_indicator(self, node, mode):
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
        self._select(self.selected)

    def _drag_over(self, sender, args):
        target = self._item(args.OriginalSource)
        payload = self._payload(args)
        mode = self._target_mode(payload, target, args) if target is not None else None
        if mode is None:
            self._clear_drop_indicator()
            args.Effects = DragDropEffects.None
        else:
            self._show_drop_indicator(target, mode)
            args.Effects = DragDropEffects.Move
        args.Handled = True

    def _drag_leave(self, sender, args):
        self._clear_drop_indicator()

    def _expanded(self):
        folders = [str(n.Tag[1].id) for n in self._folder_nodes() if getattr(n, "IsExpanded", False) and getattr(n, "Tag", None)]
        carnets = [str(n.Tag[1].id) for n in self._nodes("CARNET") if getattr(n, "IsExpanded", False)]
        return folders, carnets

    def _folder_nodes(self):
        return [n for n in self._all() if getattr(n, "Tag", None) and n.Tag[0] == "FOLDER"]

    def _restore_expanded(self, state):
        folders, carnets = state
        folders = set(folders or [])
        carnets = set(carnets or [])
        for n in self._folder_nodes():
            if str(n.Tag[1].id) in folders:
                n.IsExpanded = True
        for n in self._nodes("CARNET"):
            if str(n.Tag[1].id) in carnets:
                n.IsExpanded = True

    def _next_sibling(self, values, target_id, moving):
        values = [v for v in values if str(getattr(v, "id", "")) not in moving]
        values.sort(key=lambda v: getattr(v, "sort_order", 0))
        for i, value in enumerate(values):
            if str(value.id) == str(target_id):
                return values[i + 1].id if i + 1 < len(values) else None
        return None

    def _move_folders(self, payload, target, mode):
        ids = [x.split(":", 1)[1] for x in payload["items"] if ":" in x]
        folder = target.Tag[1]
        if mode == "INSIDE":
            return self.window.controller.move_folders_many(ids, folder.id, None)
        siblings = [f for f in self.window._folders if str(getattr(f, "parent_id", None)) == str(getattr(folder, "parent_id", None))]
        before = folder.id if mode == "BEFORE" else self._next_sibling(siblings, folder.id, set(ids))
        return self.window.controller.move_folders_many(ids, folder.parent_id, before)

    def _move_carnets(self, payload, target, mode):
        ids = [x.split(":", 1)[1] for x in payload["items"] if ":" in x]
        if target.Tag[0] == "FOLDER":
            return self.window.controller.move_persistent_many(ids, target.Tag[1].id, None)
        carnet = target.Tag[1]
        siblings = [c for c in self.window._carnets if str(getattr(c, "folder_id", None)) == str(getattr(carnet, "folder_id", None))]
        before = carnet.id if mode == "BEFORE" else self._next_sibling(siblings, carnet.id, set(ids))
        return self.window.controller.move_persistent_many(ids, carnet.folder_id, before)

    def _move_sheets(self, payload, target, mode):
        selected_ids = []
        carnet_id = None
        for key in payload["items"]:
            parts = key.split(":", 2)
            if len(parts) != 3:
                return False
            carnet_id = parts[1] if carnet_id is None else carnet_id
            if parts[1] != carnet_id:
                return False
            selected_ids.append(parts[2])
        target_carnet = target.Tag[2] if target.Tag[0] == "SHEET" else target.Tag[1]
        if str(target_carnet.id) != str(carnet_id):
            return False
        carnet = next((c for c in self.window._carnets if str(getattr(c, "id", "")) == str(carnet_id)), None)
        if carnet is None or not carnet.persistent:
            return False
        selected = [i for i in carnet.items if str(i.unique_id) in selected_ids]
        remaining = [i for i in carnet.items if str(i.unique_id) not in selected_ids]
        if not selected:
            return False
        if target.Tag[0] == "CARNET":
            index = len(remaining)
        else:
            uid = str(target.Tag[1].unique_id)
            if uid in selected_ids:
                return False
            target_index = next((i for i, item in enumerate(remaining) if str(item.unique_id) == uid), len(remaining))
            index = target_index if mode == "BEFORE" else target_index + 1
        carnet.items = remaining[:index] + selected + remaining[index:]
        self.window.controller.save_persistent(carnet)
        return True

    def _drop(self, sender, args):
        target = self._item(args.OriginalSource)
        payload = self._payload(args)
        mode = self._target_mode(payload, target, args) if target is not None else None
        if mode is None:
            self._clear_drop_indicator()
            args.Handled = True
            return
        try:
            expanded = self._expanded()
            if payload["kind"] == "FOLDER":
                moved = self._move_folders(payload, target, mode)
            elif payload["kind"] == "CARNET":
                moved = self._move_carnets(payload, target, mode)
            else:
                moved = self._move_sheets(payload, target, mode)
            if moved:
                self._select([])
                self.window._selected_set = None
                self.window._selected_item = None
                self.window._selected_kind = None
                self.window._selected_folder = None
                self.window._refresh_tree()
                self._restore_expanded(expanded)
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
