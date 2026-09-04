# -*- coding: utf-8 -*-
"""Glisser-déposer des carnets dans l'arborescence Export."""

from System.Windows import DragDrop, DragDropEffects, DataObject
from System.Windows.Controls import TreeViewItem
from System.Windows.Input import MouseButtonState, Keyboard
from System.Windows.Media import VisualTreeHelper, SolidColorBrush, Color


class PublicationTreeDragDrop(object):
    """Gère sélection multiple, déplacement et réordonnancement des carnets."""

    DATA_FORMAT = "OutilsTAA.Export.PublicationSets"
    SELECTED_BRUSH = SolidColorBrush(Color.FromRgb(250, 100, 31))

    def __init__(self, window):
        self.window = window
        self.drag_node = None
        self.drag_started = False
        self.selected_ids = []
        tree = window.PublicationTree
        tree.PreviewMouseLeftButtonDown += self._mouse_down
        tree.PreviewMouseMove += self._mouse_move
        tree.DragOver += self._drag_over
        tree.Drop += self._drop

    def _tree_item_from_source(self, source):
        current = source
        while current is not None:
            if isinstance(current, TreeViewItem):
                return current
            try:
                current = VisualTreeHelper.GetParent(current)
            except Exception:
                return None
        return None

    def _all_tree_items(self):
        result = []
        self._collect_tree_items(self.window.PublicationTree, result)
        return result

    def _collect_tree_items(self, parent, result):
        try:
            count = VisualTreeHelper.GetChildrenCount(parent)
        except Exception:
            return
        for index in range(count):
            try:
                child = VisualTreeHelper.GetChild(parent, index)
            except Exception:
                continue
            if isinstance(child, TreeViewItem):
                result.append(child)
            self._collect_tree_items(child, result)

    def _persistent_carnet_nodes(self):
        nodes = []
        for node in self._all_tree_items():
            tag = getattr(node, "Tag", None)
            if not tag or len(tag) < 2 or tag[0] != "CARNET":
                continue
            publication_set = tag[1]
            if getattr(publication_set, "persistent", False) and getattr(publication_set, "id", None):
                nodes.append(node)
        return nodes

    def _find_node_by_id(self, set_id):
        for node in self._persistent_carnet_nodes():
            tag = getattr(node, "Tag", None)
            if tag and tag[1].id == set_id:
                return node
        return None

    def _refresh_visual_selection(self):
        selected = set(self.selected_ids)
        for node in self._persistent_carnet_nodes():
            tag = getattr(node, "Tag", None)
            if not tag:
                continue
            if tag[1].id in selected:
                node.Background = self.SELECTED_BRUSH
                node.Foreground = SolidColorBrush(Color.FromRgb(255, 255, 255))
            else:
                node.ClearValue(TreeViewItem.BackgroundProperty)
                node.ClearValue(TreeViewItem.ForegroundProperty)

    def _set_selection(self, ids):
        self.selected_ids = []
        for set_id in ids:
            if set_id and set_id not in self.selected_ids:
                self.selected_ids.append(set_id)
        self._refresh_visual_selection()

    def _mouse_down(self, sender, args):
        node = self._tree_item_from_source(args.OriginalSource)
        self.drag_node = node
        self.drag_started = False

        if node is None:
            self._set_selection([])
            return

        tag = getattr(node, "Tag", None)
        if not tag or len(tag) < 2 or tag[0] != "CARNET":
            # Une sélection multiple ne concerne que les carnets persistants.
            return

        publication_set = tag[1]
        if not getattr(publication_set, "persistent", False):
            return

        set_id = publication_set.id
        ctrl = Keyboard.IsKeyDown(System.Windows.Input.Key.LeftCtrl) if False else False
        # IronPython peut accéder directement aux touches WPF via Keyboard.
        ctrl = Keyboard.IsKeyDown(System.Windows.Input.Key.LeftCtrl) or Keyboard.IsKeyDown(System.Windows.Input.Key.RightCtrl)
        shift = Keyboard.IsKeyDown(System.Windows.Input.Key.LeftShift) or Keyboard.IsKeyDown(System.Windows.Input.Key.RightShift)

        if shift and self.selected_ids:
            nodes = self._persistent_carnet_nodes()
            ordered_ids = []
            for item in nodes:
                item_tag = getattr(item, "Tag", None)
                if item_tag and item_tag[1].id:
                    ordered_ids.append(item_tag[1].id)
            try:
                anchor = self.selected_ids[-1]
                start = ordered_ids.index(anchor)
                end = ordered_ids.index(set_id)
                low = min(start, end)
                high = max(start, end)
                self._set_selection(ordered_ids[low:high + 1])
            except ValueError:
                self._set_selection([set_id])
            args.Handled = True
        elif ctrl:
            ids = list(self.selected_ids)
            if set_id in ids:
                ids.remove(set_id)
            else:
                ids.append(set_id)
            self._set_selection(ids)
            args.Handled = True
        else:
            self._set_selection([set_id])
            # Laisser WPF sélectionner normalement le carnet pour conserver
            # le comportement existant de l'interface.

    def _mouse_move(self, sender, args):
        if self.drag_node is None or self.drag_started:
            return
        if args.LeftButton != MouseButtonState.Pressed:
            return

        tag = getattr(self.drag_node, "Tag", None)
        if not tag or len(tag) < 2 or tag[0] != "CARNET":
            return

        source_set = tag[1]
        if not getattr(source_set, "persistent", False):
            return

        if source_set.id not in self.selected_ids:
            self._set_selection([source_set.id])

        selected_ids = list(self.selected_ids)
        if not selected_ids:
            return

        self.drag_started = True
        data = DataObject()
        data.SetData(self.DATA_FORMAT, selected_ids)
        data.SetData("OutilsTAA.Export.PublicationSet", source_set)

        try:
            DragDrop.DoDragDrop(self.drag_node, data, DragDropEffects.Move)
        finally:
            self.drag_node = None
            self.drag_started = False

    def _get_dragged_ids(self, args):
        try:
            if args.Data.GetDataPresent(self.DATA_FORMAT):
                value = args.Data.GetData(self.DATA_FORMAT)
                return list(value or [])
        except Exception:
            pass
        return []

    def _drag_over(self, sender, args):
        target = self._tree_item_from_source(args.OriginalSource)
        set_ids = self._get_dragged_ids(args)
        if target is not None and self._is_valid_drop(set_ids, target):
            args.Effects = DragDropEffects.Move
        else:
            args.Effects = DragDropEffects.None
        args.Handled = True

    def _drop(self, sender, args):
        target_node = self._tree_item_from_source(args.OriginalSource)
        set_ids = self._get_dragged_ids(args)
        if target_node is None or not set_ids:
            return

        tag = getattr(target_node, "Tag", None)
        if not tag or len(tag) < 2 or tag[0] not in ("FOLDER", "CARNET"):
            return

        if tag[0] == "FOLDER":
            folder_id = tag[1].id
            before_set_id = None
        else:
            target_carnet = tag[1]
            folder_id = getattr(target_carnet, "folder_id", None)
            before_set_id = target_carnet.id
            if before_set_id in set_ids:
                return

        try:
            moved = self.window.controller.move_persistent_many(
                set_ids, folder_id, before_set_id
            )
            if moved:
                self._set_selection([])
                self.window._selected_set = None
                self.window._selected_item = None
                self.window._selected_kind = None
                self.window._selected_folder = None
                self.window._refresh_tree()
                self.window._update_selection_info()
        except Exception as exc:
            try:
                from pyrevit import forms
                forms.alert("Impossible de déplacer le ou les carnets.\n\n{0}".format(exc), title="Export")
            except Exception:
                pass
        args.Handled = True

    @staticmethod
    def _is_valid_drop(set_ids, target_node):
        if not set_ids:
            return False
        tag = getattr(target_node, "Tag", None)
        if not tag or len(tag) < 2 or tag[0] not in ("FOLDER", "CARNET"):
            return False
        if tag[0] == "CARNET" and getattr(tag[1], "id", None) in set_ids:
            return False
        return True
