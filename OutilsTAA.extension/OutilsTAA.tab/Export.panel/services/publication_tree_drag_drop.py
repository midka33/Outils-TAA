# -*- coding: utf-8 -*-
import json
from System import DateTime
from System.Windows import (
    DragDrop,
    DragDropEffects,
    DataObject,
    SystemParameters,
    Thickness,
)
from System.Windows.Controls import TreeViewItem, ScrollViewer
from System.Windows.Input import MouseButtonState, Keyboard, Key, ModifierKeys
from System.Windows.Media import VisualTreeHelper


class PublicationTreeDragDrop(object):
    DATA_FORMAT = "OutilsTAA.Export.DragPayload"
    def __init__(self, window):
        self.window = window
        self.SELECTED_BRUSH = window.FindResource("TaaSelection")
        self.DROP_BRUSH = window.FindResource("TaaAccent")
        self.DROP_BACKGROUND = window.FindResource("TaaSelection")
        self.selected_foreground = window.FindResource("TaaText")
        self.drag_node = None
        self.drag_started = False
        self._mouse_down_point = None
        self._hover_node = None
        self._hover_mode = None
        self._hover_since = None
        self._post_drop_selection = None
        self.selected = []
        self._selection_explicit = False
        self.drop_node = None
        self.drop_mode = None
        tree = window.PublicationTree
        tree.AllowDrop = True
        tree.PreviewMouseLeftButtonDown += self._mouse_down
        tree.PreviewMouseMove += self._mouse_move
        tree.PreviewKeyDown += self._key_down
        tree.DragOver += self._drag_over
        tree.DragLeave += self._drag_leave
        tree.Drop += self._drop

    def _key_down(self, sender, args):
        if args.Key in (Key.Up, Key.Down, Key.Left, Key.Right, Key.Home, Key.End):
            self._select([], fallback_to_native=True)

    def _item(self, source):
        """Retrouve le TreeViewItem depuis n'importe quel enfant visuel WPF."""
        current = source
        seen = set()
        while current is not None:
            if isinstance(current, TreeViewItem):
                return current

            marker = id(current)
            if marker in seen:
                return None
            seen.add(marker)

            parent = None
            try:
                parent = VisualTreeHelper.GetParent(current)
            except Exception:
                parent = None

            if parent is None:
                try:
                    parent = getattr(current, "Parent", None)
                except Exception:
                    parent = None

            if parent is None:
                try:
                    parent = getattr(current, "TemplatedParent", None)
                except Exception:
                    parent = None

            current = parent
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
        return self._key(tag)

    def _select(self, keys, fallback_to_native=False, notify=True):
        self._selection_explicit = not fallback_to_native
        self.selected = []
        for key in keys:
            if key and key not in self.selected:
                self.selected.append(key)
        selected = set(self.selected)
        for kind in ("FOLDER", "CARNET", "SHEET"):
            for node in self._selection_nodes(kind):
                if self._key(node.Tag) in selected:
                    node.Background = self.SELECTED_BRUSH
                    node.Foreground = self.selected_foreground
                else:
                    node.ClearValue(TreeViewItem.BackgroundProperty)
                    node.ClearValue(TreeViewItem.ForegroundProperty)
        if notify:
            self.window._publication_selection_changed()

    def selected_tags(self):
        """Utilise la sélection Ctrl/Maj ; repli sur la sélection native au clavier."""
        tags = [node.Tag for node in self._all()
                if getattr(node, "Tag", None) and self._key(node.Tag) in self.selected]
        if tags or self._selection_explicit:
            return tags
        node = self.window.PublicationTree.SelectedItem
        return [node.Tag] if node is not None and getattr(node, "Tag", None) else []

    def _selection_nodes(self, kind):
        return [node for node in self._all() if getattr(node, "Tag", None)
                and node.Tag[0] == kind and self._valid_key(node)]

    def _ordered(self, node):
        tag = node.Tag
        if tag[0] in ("FOLDER", "CARNET"):
            return [self._key(n.Tag) for n in self._selection_nodes(tag[0])]
        parent = getattr(node, "Parent", None)
        if parent is None:
            return []
        cid = str(tag[2].id)
        return [self._key(n.Tag) for n in list(parent.Items) if getattr(n, "Tag", None) and n.Tag[0] == "SHEET" and str(n.Tag[2].id) == cid]

    def _mouse_down(self, sender, args):
        node = self._item(args.OriginalSource)
        self.drag_node = node
        self.drag_started = False
        try:
            self._mouse_down_point = args.GetPosition(
                self.window.PublicationTree
            )
        except Exception:
            self._mouse_down_point = None
        key = self._valid_key(node) if node is not None else None
        if key is None:
            self._select([], fallback_to_native=True)
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
        if (
            self.drag_node is None
            or self.drag_started
            or args.LeftButton != MouseButtonState.Pressed
        ):
            return

        # Utiliser un vrai delta depuis MouseDown. L'ancienne version
        # comparait la position locale dans la ligne, ce qui pouvait lancer
        # un drag presque immédiatement selon l'endroit cliqué.
        if self._mouse_down_point is not None:
            try:
                current = args.GetPosition(self.window.PublicationTree)
                dx = abs(current.X - self._mouse_down_point.X)
                dy = abs(current.Y - self._mouse_down_point.Y)
                if (
                    dx < SystemParameters.MinimumHorizontalDragDistance
                    and dy < SystemParameters.MinimumVerticalDragDistance
                ):
                    return
            except Exception:
                pass
        tag = getattr(self.drag_node, "Tag", None)
        if not tag or tag[0] not in ("FOLDER", "CARNET", "SHEET"):
            return
        if not self.selected:
            self._select([self._key(tag)])
        kind = tag[0]
        movable = set(self._key(n.Tag) for n in self._nodes(kind))
        if self._key(tag) not in movable:
            return
        items = [key for key in self.selected if key in movable]
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
                if (
                    str(source_id) == str(tag[1].id)
                    or self._folder_descendant(source_id, tag[1].id)
                ):
                    return None
            return self._mode(target, args)

        if kind == "CARNET" and tag[0] in ("FOLDER", "CARNET"):
            ids = [x.split(":", 1)[1] for x in keys if ":" in x]
            if (
                tag[0] == "CARNET"
                and str(tag[1].id) in [str(x) for x in ids]
            ):
                return None
            if tag[0] == "FOLDER":
                # Le centre d'un vrai dossier signifie « déplacer dedans ».
                return "FOLDER"
            # Un dossier de publication reste un dossier feuille : on l'insère
            # avant/après, sans faire croire qu'il peut contenir un sous-dossier.
            mode = self._mode(target, args)
            return "BEFORE" if mode == "BEFORE" else "AFTER"

        if kind == "SHEET" and tag[0] in ("SHEET", "CARNET"):
            if tag[0] == "CARNET":
                return "APPEND"
            if self._key(tag) in keys:
                return None
            mode = self._mode(target, args)
            return "BEFORE" if mode == "BEFORE" else "AFTER"

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
        self._select(self.selected, fallback_to_native=not self._selection_explicit, notify=False)

    def _scroll_viewer(self):
        """Retrouve le ScrollViewer interne du TreeView."""
        def find(node):
            if node is None:
                return None
            if isinstance(node, ScrollViewer):
                return node
            try:
                count = VisualTreeHelper.GetChildrenCount(node)
            except Exception:
                return None
            for index in range(count):
                try:
                    child = VisualTreeHelper.GetChild(node, index)
                except Exception:
                    continue
                result = find(child)
                if result is not None:
                    return result
            return None

        return find(self.window.PublicationTree)

    def _auto_scroll(self, args):
        """Scroll doux lorsque le pointeur approche du haut/bas de l'arbre."""
        viewer = self._scroll_viewer()
        if viewer is None:
            return
        try:
            tree = self.window.PublicationTree
            point = args.GetPosition(tree)
            height = float(tree.ActualHeight)
            margin = 28.0
            if point.Y < margin:
                viewer.LineUp()
            elif point.Y > height - margin:
                viewer.LineDown()
        except Exception:
            return

    def _hover_expand(self, target, mode):
        """Ouvre automatiquement un dossier après ~700 ms de survol."""
        tag = getattr(target, "Tag", None)
        can_expand = (
            tag
            and tag[0] in ("FOLDER", "CARNET")
            and mode in ("FOLDER", "APPEND", "INSIDE")
            and not bool(getattr(target, "IsExpanded", False))
        )
        if not can_expand:
            self._hover_node = None
            self._hover_mode = None
            self._hover_since = None
            return

        if target is not self._hover_node or mode != self._hover_mode:
            self._hover_node = target
            self._hover_mode = mode
            self._hover_since = DateTime.UtcNow
            return

        if self._hover_since is None:
            self._hover_since = DateTime.UtcNow
            return

        try:
            elapsed = (DateTime.UtcNow - self._hover_since).TotalMilliseconds
            if elapsed >= 700:
                target.IsExpanded = True
                self._hover_since = None
        except Exception:
            return

    def _scroll_offset(self):
        viewer = self._scroll_viewer()
        if viewer is None:
            return None
        try:
            return float(viewer.VerticalOffset)
        except Exception:
            return None

    def _restore_scroll(self, offset):
        if offset is None:
            return
        viewer = self._scroll_viewer()
        if viewer is None:
            return
        try:
            viewer.ScrollToVerticalOffset(offset)
        except Exception:
            pass

    def expand_to_key(self, key):
        """Déplie les parents d'un nœud, utile après création/déplacement."""
        if not key:
            return
        node = next(
            (
                value
                for value in self._all()
                if getattr(value, "Tag", None)
                and self._key(value.Tag) == key
            ),
            None,
        )
        current = node
        while current is not None:
            try:
                parent = getattr(current, "Parent", None)
            except Exception:
                parent = None
            if isinstance(parent, TreeViewItem):
                parent.IsExpanded = True
            current = parent

    def _drag_over(self, sender, args):
        self._auto_scroll(args)
        target = self._item(args.OriginalSource)
        payload = self._payload(args)
        mode = (
            self._target_mode(payload, target, args)
            if target is not None else None
        )
        if mode is None:
            self._hover_expand(None, None)
            self._clear_drop_indicator()
            args.Effects = DragDropEffects.None
        else:
            self._hover_expand(target, mode)
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
        """Déplace des mises en page comme des fichiers entre deux dossiers.

        Le format de stockage reste PublicationSet pour compatibilité, mais
        l'utilisateur peut désormais glisser des feuilles d'un dossier de
        publication vers un autre.
        """
        keys = list(payload.get("items", []) or [])
        if not keys:
            return False

        by_id = dict(
            (str(getattr(value, "id", "")), value)
            for value in self.window._carnets
            if getattr(value, "id", None)
        )

        selected_keys = set(keys)
        moved = []
        touched = []
        snapshots = {}

        # L'ordre visuel de l'arbre prévaut sur l'ordre des Ctrl+clic.
        for node in self._all():
            tag = getattr(node, "Tag", None)
            if not tag or tag[0] != "SHEET":
                continue
            key = self._key(tag)
            if key not in selected_keys:
                continue
            source = tag[2]
            if not getattr(source, "persistent", False):
                return False
            moved.append((source, tag[1]))

        if len(moved) != len(selected_keys):
            return False

        target_set = target.Tag[2] if target.Tag[0] == "SHEET" else target.Tag[1]
        if not getattr(target_set, "persistent", False):
            return False

        # Snapshot mémoire pour pouvoir restaurer l'UI en cas d'échec de sauvegarde.
        all_sets = []
        for source, item in moved:
            if source not in all_sets:
                all_sets.append(source)
        if target_set not in all_sets:
            all_sets.append(target_set)
        for value in all_sets:
            snapshots[str(value.id)] = list(value.items or [])

        try:
            moved_ids_by_set = {}
            for source, item in moved:
                moved_ids_by_set.setdefault(str(source.id), set()).add(
                    str(item.unique_id)
                )

            for source in all_sets:
                selected_ids = moved_ids_by_set.get(str(source.id), set())
                if not selected_ids:
                    continue
                source.items = [
                    item for item in (source.items or [])
                    if str(item.unique_id) not in selected_ids
                ]
                if source not in touched:
                    touched.append(source)

            moving_items = [item for source, item in moved]
            destination = list(target_set.items or [])

            if target.Tag[0] == "CARNET":
                index = len(destination)
            else:
                target_uid = str(target.Tag[1].unique_id)
                if any(
                    str(item.unique_id) == target_uid
                    for item in moving_items
                ):
                    return False
                target_index = next(
                    (
                        index
                        for index, item in enumerate(destination)
                        if str(item.unique_id) == target_uid
                    ),
                    len(destination),
                )
                index = (
                    target_index
                    if mode == "BEFORE"
                    else target_index + 1
                )

            target_set.items = (
                destination[:index]
                + moving_items
                + destination[index:]
            )
            if target_set not in touched:
                touched.append(target_set)

            for value in touched:
                self.window.controller.save_persistent(value)

            self._post_drop_selection = [
                "SHEET:{0}:{1}".format(
                    target_set.id,
                    item.unique_id,
                )
                for item in moving_items
            ]
            return True

        except Exception:
            for value in all_sets:
                value.items = list(
                    snapshots.get(str(value.id), value.items or [])
                )
            raise

    def _drop(self, sender, args):
        target = self._item(args.OriginalSource)
        payload = self._payload(args)
        mode = (
            self._target_mode(payload, target, args)
            if target is not None else None
        )
        if mode is None:
            self._clear_drop_indicator()
            args.Handled = True
            return

        try:
            expanded = self._expanded()
            scroll_offset = self._scroll_offset()
            self._post_drop_selection = None

            if payload["kind"] == "FOLDER":
                moved = self._move_folders(payload, target, mode)
            elif payload["kind"] == "CARNET":
                moved = self._move_carnets(payload, target, mode)
            else:
                moved = self._move_sheets(payload, target, mode)

            if moved:
                post_selection = (
                    list(self._post_drop_selection)
                    if self._post_drop_selection
                    else list(payload.get("items", []) or [])
                )

                self.window._selected_set = None
                self.window._selected_item = None
                self.window._selected_kind = None
                self.window._selected_folder = None

                self.window._refresh_tree()
                self._restore_expanded(expanded)
                for key in post_selection:
                    self.expand_to_key(key)
                self._restore_scroll(scroll_offset)
                self._select(post_selection)
                self.window._update_selection_info()

        except Exception as exc:
            try:
                from pyrevit import forms
                forms.alert(
                    "Impossible de réorganiser les éléments.\n\n{0}".format(exc),
                    title="Export",
                )
            except Exception:
                pass
        finally:
            self._hover_node = None
            self._hover_mode = None
            self._hover_since = None
            self._post_drop_selection = None
            self._clear_drop_indicator()

        args.Handled = True
