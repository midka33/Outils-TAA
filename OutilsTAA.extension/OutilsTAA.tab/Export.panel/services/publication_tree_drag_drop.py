# -*- coding: utf-8 -*-
"""Glisser-déposer des carnets dans l'arborescence Export."""

from System.Windows import DragDrop, DragDropEffects
from System.Windows.Controls import TreeViewItem
from System.Windows.Input import MouseButtonState
from System.Windows.Media import VisualTreeHelper


class PublicationTreeDragDrop(object):
    """Ajoute le déplacement des carnets entre dossiers et leur réordonnancement."""

    def __init__(self, window):
        self.window = window
        self.drag_node = None
        self.drag_started = False
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

    def _mouse_down(self, sender, args):
        self.drag_node = self._tree_item_from_source(args.OriginalSource)
        self.drag_started = False

    def _mouse_move(self, sender, args):
        if self.drag_node is None or self.drag_started:
            return
        if args.LeftButton != MouseButtonState.Pressed:
            return
        tag = getattr(self.drag_node, "Tag", None)
        if not tag or tag[0] != "CARNET":
            return
        self.drag_started = True
        data = tag[1]
        try:
            DragDrop.DoDragDrop(self.drag_node, data, DragDropEffects.Move)
        finally:
            self.drag_node = None
            self.drag_started = False

    def _get_dragged_set(self, args):
        try:
            formats = args.Data.GetFormats()
            for fmt in formats:
                value = args.Data.GetData(fmt)
                if getattr(value, "id", None) and hasattr(value, "folder_id"):
                    return value
        except Exception:
            pass
        return None

    def _drag_over(self, sender, args):
        target = self._tree_item_from_source(args.OriginalSource)
        source = self._get_dragged_set(args)
        if target is not None and self._is_valid_drop(source, target):
            args.Effects = DragDropEffects.Move
        else:
            args.Effects = DragDropEffects.None
        args.Handled = True

    def _drop(self, sender, args):
        target_node = self._tree_item_from_source(args.OriginalSource)
        source = self._get_dragged_set(args)
        if target_node is None or source is None:
            return
        tag = getattr(target_node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET"):
            return
        if not getattr(source, "persistent", False):
            return

        if tag[0] == "FOLDER":
            folder_id = tag[1].id
            before_set_id = None
        else:
            target_carnet = tag[1]
            folder_id = getattr(target_carnet, "folder_id", None)
            before_set_id = target_carnet.id
            if source.id == before_set_id:
                return

        try:
            moved = self.window.controller.move_persistent(
                source.id, folder_id, before_set_id
            )
            if moved:
                self.window._selected_set = None
                self.window._selected_item = None
                self.window._selected_kind = None
                self.window._selected_folder = None
                self.window._refresh_tree()
                self.window._update_selection_info()
        except Exception as exc:
            try:
                from pyrevit import forms
                forms.alert("Impossible de déplacer le carnet.\n\n{0}".format(exc), title="Export")
            except Exception:
                pass
        args.Handled = True

    @staticmethod
    def _is_valid_drop(source, target_node):
        if source is None or not getattr(source, "persistent", False):
            return False
        tag = getattr(target_node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET"):
            return False
        if tag[0] == "CARNET" and getattr(tag[1], "id", None) == getattr(source, "id", None):
            return False
        return True
