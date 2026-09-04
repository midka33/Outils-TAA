# -*- coding: utf-8 -*-
"""Intégration des flux avancés de publication dans Export."""

from pyrevit import forms
from System import Guid

from publication_preview_service import PublicationPreviewService
from publication_preview_window import PublicationPreviewWindow
from publication_batch_service import PublicationBatchService
from export_report_window import PublicationReportWindow
from carnet_manager_window import CarnetManagerWindow
from publication_tree_drag_drop import PublicationTreeDragDrop
from publication_settings import PublicationSettings
from publication_set import PublicationSet


def install_preview_on_export_window(export_window_class):
    """Installe aperçu, publication de dossier et réorganisation par glisser-déposer.

    Cette intégration reste compatible avec les versions intermédiaires de
    ExportWindow : certaines méthodes d'événements ont été déplacées entre
    les étapes de développement. On fournit donc ici les handlers historiques
    manquants avant d'installer les wrappers de prévisualisation.
    """
    original_publish_click = getattr(export_window_class, "Publish_Click", None)
    original_selection_changed = getattr(export_window_class, "Tree_SelectedItemChanged", None)
    original_manager_click = getattr(export_window_class, "OpenCarnetManager_Click", None)
    original_init = export_window_class.__init__

    def init_with_tree_features(self, controller, repository):
        original_init(self, controller, repository)
        if not hasattr(self, "_publication_tree_drag_drop"):
            self._publication_tree_drag_drop = PublicationTreeDragDrop(self)

    def selection_changed_with_folder_action(self, sender, args):
        if original_selection_changed is not None:
            original_selection_changed(self, sender, args)
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            count = len(_folder_targets(self, self._selected_folder))
            self.PublishButton.Content = "Publier le dossier « {0} »".format(self._selected_folder.name)
            self.PublishButton.IsEnabled = count > 0

    def manager_click_with_folder(self, sender, args):
        # Le dossier actuellement sélectionné devient le dossier cible des nouveaux carnets.
        target_folder_id = "default"
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            target_folder_id = self._selected_folder.id
        elif self._selected_set is not None:
            target_folder_id = getattr(self._selected_set, "folder_id", None) or "default"

        manager = CarnetManagerWindow(
            self.controller, owner=self, target_folder_id=target_folder_id
        )
        manager.ShowDialog()
        if manager.result:
            for carnet in manager.result:
                if not carnet.persistent:
                    self.session_carnets.append(carnet)
            self._refresh_tree()

    def publish_click_with_preview(self, sender, args):
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            targets = [self._make_sheet_target()]
            return _preview_then_publish_single(self, targets, original_publish_click)

        if self._selected_kind == "CARNET" and self._selected_set is not None:
            self._selected_set.folder_name = self._folder_name(self._selected_set)
            targets = [self._selected_set]
            return _preview_then_publish_single(self, targets, original_publish_click)

        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            targets = _folder_targets(self, self._selected_folder)
            return _preview_then_publish_folder(self, targets)

        if original_publish_click is not None:
            return original_publish_click(self, sender, args)
        forms.alert("Sélectionnez un carnet ou une mise en page dans l'arborescence.", title="Publication")

    # ------------------------------------------------------------------
    # Handlers historiques manquants dans certaines versions d'ExportWindow
    # ------------------------------------------------------------------
    def publish_click_base(self, sender, args):
        """Publication réelle appelée uniquement après validation/aperçu."""
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            targets = [self._make_sheet_target()]
        elif self._selected_kind == "CARNET" and self._selected_set is not None:
            targets = [self._selected_set]
        else:
            forms.alert("Sélectionnez un carnet ou une mise en page dans l'arborescence.", title="Publication")
            return

        all_results, all_errors, all_warnings = [], [], []
        all_success = True
        report_output_directory = None

        for publication_set in targets:
            # Toujours utiliser les réglages effectifs afin de respecter
            # l'héritage Dossier -> Carnet.
            settings = self._resolve_settings(publication_set)
            errors = settings.validate()
            if errors:
                all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in errors])
                all_success = False
                continue

            report_output_directory = settings.output_directory
            try:
                result = self.controller.publish(
                    publication_set,
                    settings.output_directory,
                    export_pdf=settings.pdf_enabled,
                    export_dwg=settings.dwg_enabled,
                    pdf_combined=settings.pdf_mode == "COMBINED",
                    dwg_combined=settings.dwg_mode == "COMBINED",
                    dwg_setup_name=settings.dwg_setup_name,
                    dwg_true_color=settings.dwg_true_color)
            except Exception as exc:
                result = {"success": False, "results": [], "errors": [str(exc)], "warnings": []}

            for item_result in result.get("results", []):
                row = dict(item_result)
                row["carnet"] = publication_set.name
                all_results.append(row)
            all_errors.extend(["{0} : {1}".format(publication_set.name, e)
                               for e in result.get("errors", [])])
            all_warnings.extend(["{0} : {1}".format(publication_set.name, w)
                                 for w in result.get("warnings", [])])
            all_success = all_success and bool(result.get("success"))

        selection_label = "mise en page" if self._selected_kind == "SHEET" else "carnet"
        report = {
            "success": all_success,
            "carnet": "Publication : {0}".format(selection_label),
            "results": all_results,
            "errors": all_errors,
            "warnings": all_warnings,
            "output_directory": report_output_directory or ""
        }
        PublicationReportWindow(report, owner=self).ShowDialog()

    def manager_click_base(self, sender, args):
        target_folder_id = "default"
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            target_folder_id = self._selected_folder.id
        elif self._selected_set is not None:
            target_folder_id = getattr(self._selected_set, "folder_id", None) or "default"
        manager = CarnetManagerWindow(self.controller, owner=self, target_folder_id=target_folder_id)
        manager.ShowDialog()
        if manager.result:
            for carnet in manager.result:
                if not carnet.persistent:
                    self.session_carnets.append(carnet)
            self._refresh_tree()

    def new_folder_click(self, sender, args):
        name = forms.ask_for_string(default="Nouveau dossier", prompt="Nom du dossier", title="Export")
        if not name or not name.strip():
            return
        from publication_folder import PublicationFolder
        folder = PublicationFolder(name.strip(), str(Guid.NewGuid()), None, True)
        self.controller.save_folder(folder)
        self._refresh_tree()

    def folder_changed(self, sender, args):
        if self._loading_settings or self._selected_set is None or self.FolderCombo.SelectedItem is None:
            return
        self._selected_set.folder_id = self.FolderCombo.SelectedItem.id
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)
        self._refresh_tree()

    def browse_output_click(self, sender, args):
        folder = forms.pick_folder(title="Choisir le dossier de publication")
        if not folder:
            return
        self.OutputDirectoryTextBox.Text = folder
        if self._selected_kind == "FOLDER":
            self._save_folder_settings("output_directory")
        else:
            self._save_selected_field("output_directory")

    def delete_node_click(self, sender, args):
        node = self.PublicationTree.SelectedItem
        if node is None or not getattr(node, "Tag", None):
            return
        tag = node.Tag
        kind, value = tag[0], tag[1]
        if kind == "CARNET":
            if not forms.alert("Supprimer le carnet « {0} » ?".format(value.name), title="Export", yes=True, no=True):
                return
            if value.persistent:
                self.repository.delete(value.id)
            else:
                self.session_carnets = [c for c in self.session_carnets if c.id != value.id]
        elif kind == "FOLDER":
            if value.id == "default":
                forms.alert("Le dossier Général ne peut pas être supprimé.", title="Export")
                return
            if not forms.alert("Supprimer le dossier « {0} » ? Il doit être vide.".format(value.name), title="Export", yes=True, no=True):
                return
            if not self.controller.delete_folder(value.id):
                forms.alert("Le dossier n'est pas vide ou ne peut pas être supprimé.", title="Export")
                return
        else:
            return
        self._selected_set = None
        self._selected_item = None
        self._selected_kind = None
        self._selected_folder = None
        self._refresh_tree()
        self._update_selection_info()

    def profile_changed(self, sender, args):
        return self.Profile_SelectionChanged(sender, args)

    def filename_token_changed(self, sender, args):
        return

    def insert_filename_token_click(self, sender, args):
        return self.FilenameToken_InsertClick(sender, args)

    def _folder_name_compat(self, publication_set):
        try:
            return self._folder_name(publication_set)
        except Exception:
            folder = self._folder_for_set(publication_set)
            return folder.name if folder is not None else "Général"

    # Exposer les handlers uniquement lorsqu'ils n'existent pas déjà.
    if not hasattr(export_window_class, "Publish_Click"):
        export_window_class.Publish_Click = publish_click_base
    if not hasattr(export_window_class, "OpenCarnetManager_Click"):
        export_window_class.OpenCarnetManager_Click = manager_click_base
    if not hasattr(export_window_class, "NewFolder_Click"):
        export_window_class.NewFolder_Click = new_folder_click
    if not hasattr(export_window_class, "FolderChanged"):
        export_window_class.FolderChanged = folder_changed
    if not hasattr(export_window_class, "BrowseOutput_Click"):
        export_window_class.BrowseOutput_Click = browse_output_click
    if not hasattr(export_window_class, "DeleteNode_Click"):
        export_window_class.DeleteNode_Click = delete_node_click
    if not hasattr(export_window_class, "ProfileChanged"):
        export_window_class.ProfileChanged = profile_changed
    if not hasattr(export_window_class, "FilenameTokenChanged"):
        export_window_class.FilenameTokenChanged = filename_token_changed
    if not hasattr(export_window_class, "InsertFilenameToken_Click"):
        export_window_class.InsertFilenameToken_Click = insert_filename_token_click

    export_window_class.__init__ = init_with_tree_features
    export_window_class.Tree_SelectedItemChanged = selection_changed_with_folder_action
    export_window_class.OpenCarnetManager_Click = manager_click_with_folder
    export_window_class.Publish_Click = publish_click_with_preview


def _folder_targets(window, folder):
    """Retourne les carnets du dossier et de ses sous-dossiers, sans doublons."""
    if folder is None:
        return []
    descendant_ids = set([folder.id])
    changed = True
    while changed:
        changed = False
        for candidate in window._folders:
            if candidate.id in descendant_ids:
                continue
            if candidate.parent_id in descendant_ids:
                descendant_ids.add(candidate.id)
                changed = True

    targets = []
    seen = set()
    for carnet in window._carnets:
        if carnet.folder_id not in descendant_ids:
            continue
        key = carnet.id or id(carnet)
        if key in seen:
            continue
        carnet.folder_name = window._folder_name_compat(carnet)
        targets.append(carnet)
        seen.add(key)
    return targets


def _build_preview(window, targets):
    preview_service = PublicationPreviewService(
        window.controller.publication_service, window.filename_service)
    previews = []
    for target in targets:
        settings = window._resolve_settings(target)
        target.folder_name = window._folder_name_compat(target)
        previews.append(preview_service.build(target, settings))
    return _merge_previews(previews)


def _preview_then_publish_single(window, targets, original_publish_click):
    preview = _build_preview(window, targets)
    dialog = PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return
    # original_publish_click est toujours disponible après installation du
    # handler de compatibilité ci-dessus.
    return window.__class__.Publish_Click.__original_base__(window, None, None) if hasattr(window.__class__.Publish_Click, "__original_base__") else _publish_base_fallback(window)


def _publish_base_fallback(window):
    """Fallback si le wrapper n'a pas pu conserver le handler de base."""
    if window._selected_kind == "SHEET" and window._selected_item is not None:
        targets = [window._make_sheet_target()]
    elif window._selected_kind == "CARNET" and window._selected_set is not None:
        targets = [window._selected_set]
    else:
        return

    all_results, all_errors, all_warnings = [], [], []
    all_success = True
    report_output_directory = None
    for publication_set in targets:
        settings = window._resolve_settings(publication_set)
        errors = settings.validate()
        if errors:
            all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in errors])
            all_success = False
            continue
        report_output_directory = settings.output_directory
        try:
            result = window.controller.publish(
                publication_set, settings.output_directory,
                export_pdf=settings.pdf_enabled, export_dwg=settings.dwg_enabled,
                pdf_combined=settings.pdf_mode == "COMBINED",
                dwg_combined=settings.dwg_mode == "COMBINED",
                dwg_setup_name=settings.dwg_setup_name,
                dwg_true_color=settings.dwg_true_color)
        except Exception as exc:
            result = {"success": False, "results": [], "errors": [str(exc)], "warnings": []}
        all_results.extend(result.get("results", []))
        all_errors.extend(result.get("errors", []))
        all_warnings.extend(result.get("warnings", []))
        all_success = all_success and bool(result.get("success"))

    report = {
        "success": all_success,
        "carnet": "Publication",
        "results": all_results,
        "errors": all_errors,
        "warnings": all_warnings,
        "output_directory": report_output_directory or ""
    }
    PublicationReportWindow(report, owner=window).ShowDialog()


def _preview_then_publish_folder(window, targets):
    preview = _build_preview(window, targets)
    if not targets:
        preview["errors"].append(
            "Le dossier « {0} » ne contient aucun carnet publiable.".format(
                window._selected_folder.name
            )
        )

    dialog = PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return

    batch_service = PublicationBatchService(window.controller.publication_service)
    report_data = batch_service.publish(
        targets, window._resolve_settings, window._folder_for_set
    )
    report = {
        "success": report_data.get("success", False),
        "carnet": "Publication : dossier « {0} »".format(window._selected_folder.name),
        "results": report_data.get("results", []),
        "errors": report_data.get("errors", []),
        "warnings": report_data.get("warnings", []),
        "output_directory": "; ".join(report_data.get("output_directories", []))
    }
    PublicationReportWindow(report, owner=window).ShowDialog()


def _merge_previews(previews):
    rows = []
    errors = []
    warnings = []
    directories = []
    for preview in previews:
        rows.extend(preview.get("rows", []))
        errors.extend(preview.get("errors", []))
        warnings.extend(preview.get("warnings", []))
        directory = preview.get("directory")
        if directory and directory not in directories:
            directories.append(directory)

    if len(directories) == 1:
        directory = directories[0]
    elif directories:
        directory = "Plusieurs destinations ({0})".format(len(directories))
    else:
        directory = ""

    return {"rows": rows, "errors": errors, "warnings": warnings,
            "directory": directory, "count": len(rows)}
