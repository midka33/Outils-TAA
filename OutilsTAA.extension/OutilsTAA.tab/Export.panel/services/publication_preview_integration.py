# -*- coding: utf-8 -*-
"""Intégration des flux avancés de publication dans Export."""

import os

from pyrevit import forms
from System import Guid

from publication_preview_service import PublicationPreviewService
from publication_preview_window import PublicationPreviewWindow
from publication_batch_service import PublicationBatchService
from publication_history_service import PublicationHistoryService
from export_report_window import PublicationReportWindow
from carnet_manager_window import CarnetManagerWindow
from publication_tree_drag_drop import PublicationTreeDragDrop
from publication_settings import PublicationSettings
from publication_set import PublicationSet
from publication_folder import PublicationFolder


def install_preview_on_export_window(export_window_class):
    """Installe l'aperçu, la publication de dossier et les handlers WPF."""
    original_selection_changed = getattr(export_window_class, "Tree_SelectedItemChanged", None)
    original_init = export_window_class.__init__

    def init_with_tree_features(self, controller, repository):
        original_init(self, controller, repository)
        if not hasattr(self, "_publication_tree_drag_drop"):
            self._publication_tree_drag_drop = PublicationTreeDragDrop(self)
        self._publication_history_service = _history_service()

    def selection_changed_with_folder_action(self, sender, args):
        if original_selection_changed is not None:
            original_selection_changed(self, sender, args)
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            count = len(_folder_targets(self, self._selected_folder))
            self.PublishButton.Content = "Publier le dossier « {0} »".format(self._selected_folder.name)
            self.PublishButton.IsEnabled = count > 0

    def publish_click_with_preview(self, sender, args):
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            targets = [self._make_sheet_target()]
            return _preview_then_publish_single(self, targets)

        if self._selected_kind == "CARNET" and self._selected_set is not None:
            self._set_folder_name_compat(self._selected_set)
            return _preview_then_publish_single(self, [self._selected_set])

        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            return _preview_then_publish_folder(self, _folder_targets(self, self._selected_folder))

        forms.alert("Sélectionnez un carnet ou une mise en page dans l'arborescence.", title="Publication")

    def manager_click_with_folder(self, sender, args):
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

    def update_selection_info(self):
        if self._selected_kind == "CARNET" and self._selected_set is not None:
            count = len(self._selected_set.items or [])
            self.SelectionInfo.Text = "Carnet sélectionné : {0} • {1} mise(s) en page.".format(self._selected_set.name, count)
            self.PublishButton.Content = "Publier le carnet « {0} »".format(self._selected_set.name)
            self.PublishButton.IsEnabled = count > 0
            return
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            self.SelectionInfo.Text = "Mise en page sélectionnée : {0} — {1}.".format(self._selected_item.sheet_number or "", self._selected_item.sheet_name or "")
            self.PublishButton.Content = "Publier la mise en page"
            self.PublishButton.IsEnabled = True
            return
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            count = len(_folder_targets(self, self._selected_folder))
            self.SelectionInfo.Text = "Dossier sélectionné : {0} • {1} carnet(s) publiable(s).".format(self._selected_folder.name, count)
            self.PublishButton.Content = "Publier le dossier « {0} »".format(self._selected_folder.name)
            self.PublishButton.IsEnabled = count > 0
            return
        self._set_no_selection()

    def set_no_selection_compat(self, sender=None, args=None):
        self.SelectedNodeText.Text = "Sélectionnez un dossier, un carnet ou une mise en page dans l'arborescence."
        self.SelectionInfo.Text = "Aucune publication sélectionnée."
        self.PublishButton.Content = "Publier…"
        self.PublishButton.IsEnabled = False
        self.FilenamePreviewText.Text = "—"
        self._set_inheritance_ui(False, {})

    def new_folder_click(self, sender, args):
        name = forms.ask_for_string(default="Nouveau dossier", prompt="Nom du dossier", title="Export")
        if not name or not name.strip():
            return
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

    def make_sheet_target(self):
        parent = self._selected_set
        settings = self._resolve_settings(parent)
        return PublicationSet(
            name=parent.name,
            items=[self._selected_item],
            source=parent.source,
            output_directory=settings.output_directory,
            filename_template_id=parent.filename_template_id,
            set_id=str(Guid.NewGuid()),
            persistent=False,
            folder_id=parent.folder_id,
            publication_settings=settings)

    def folder_name_compat(self, publication_set):
        folder = self._folder_for_set(publication_set)
        return folder.name if folder is not None else "Général"

    def set_folder_name_compat(self, publication_set):
        publication_set.folder_name = self._folder_name_compat(publication_set)

    def profile_changed(self, sender, args):
        return self.Profile_SelectionChanged(sender, args)

    def filename_token_changed(self, sender, args):
        return

    def insert_filename_token_click(self, sender, args):
        return self.FilenameToken_InsertClick(sender, args)

    def modified_only_changed(self, sender, args):
        if self._loading_settings:
            return
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            self._save_folder_settings("modified_only")
        elif self._selected_set is not None:
            self._save_selected_field("modified_only")

    if not hasattr(export_window_class, "_update_selection_info"):
        export_window_class._update_selection_info = update_selection_info
    if not hasattr(export_window_class, "_set_no_selection"):
        export_window_class._set_no_selection = set_no_selection_compat
    if not hasattr(export_window_class, "_make_sheet_target"):
        export_window_class._make_sheet_target = make_sheet_target
    if not hasattr(export_window_class, "_folder_name"):
        export_window_class._folder_name = folder_name_compat
    if not hasattr(export_window_class, "Publish_Click"):
        export_window_class.Publish_Click = publish_click_with_preview
    if not hasattr(export_window_class, "OpenCarnetManager_Click"):
        export_window_class.OpenCarnetManager_Click = manager_click_with_folder
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
    if not hasattr(export_window_class, "ModifiedOnlyChanged"):
        export_window_class.ModifiedOnlyChanged = modified_only_changed

    export_window_class.__init__ = init_with_tree_features
    export_window_class.Tree_SelectedItemChanged = selection_changed_with_folder_action
    export_window_class.OpenCarnetManager_Click = manager_click_with_folder
    export_window_class.Publish_Click = publish_click_with_preview


def _history_service():
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(root, "OutilsTAA", "Export", "publication_history.json")
    return PublicationHistoryService(path)


def _current_states(window, publication_set):
    states = {}
    service = window.controller.publication_service
    for item in getattr(publication_set, "items", []) or []:
        key = window._publication_history_service.item_key(item)
        version_guid = None
        try:
            element_id = service._resolve_current_sheet_id(item)
            element = service.document.GetElement(element_id) if element_id is not None else None
            version_guid = getattr(element, "VersionGuid", None) if element is not None else None
        except Exception:
            version_guid = None
        states[key] = window._publication_history_service.fingerprint(item, version_guid)
    return states


def _effective_publication_target(window, target):
    """Retourne le carnet réellement publié selon MODIFIED_ONLY."""
    settings = window._resolve_settings(target)
    if not settings.modified_only:
        return target, settings, None
    current_states = _current_states(window, target)
    selected, classified = window._publication_history_service.candidates(
        target, current_states, modified_only=True)
    filtered = PublicationSet(
        name=target.name,
        items=selected,
        source=target.source,
        output_directory=settings.output_directory,
        filename_template_id=target.filename_template_id,
        set_id=target.id,
        persistent=target.persistent,
        folder_id=target.folder_id,
        publication_settings=settings)
    filtered.folder_name = getattr(target, "folder_name", None)
    return filtered, settings, {"states": current_states, "classified": classified}


def _build_preview(window, targets):
    preview_service = PublicationPreviewService(window.controller.publication_service, window.filename_service)
    previews = []
    for target in targets:
        effective_target, settings, history_info = _effective_publication_target(window, target)
        try:
            effective_target.folder_name = window._folder_name(target)
        except Exception:
            pass
        preview = preview_service.build(
            effective_target, settings,
            history_service=window._publication_history_service,
            current_states=(history_info or {}).get("states"),
            classified=(history_info or {}).get("classified"),
            modified_only=bool(settings.modified_only))
        previews.append(preview)
    return _merge_previews(previews)


def _preview_then_publish_single(window, targets):
    preview = _build_preview(window, targets)
    dialog = PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return
    _publish_targets(window, targets)


def _publish_targets(window, targets):
    all_results, all_errors, all_warnings = [], [], []
    all_success = True
    output_directory = None

    for publication_set in targets:
        effective_target, settings, history_info = _effective_publication_target(window, publication_set)
        errors = settings.validate()
        if errors:
            all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in errors])
            all_success = False
            continue
        output_directory = settings.output_directory
        try:
            result = window.controller.publish(
                effective_target,
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
        all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in result.get("errors", [])])
        all_warnings.extend(["{0} : {1}".format(publication_set.name, w) for w in result.get("warnings", [])])
        success = bool(result.get("success"))
        all_success = all_success and success

        if success and history_info:
            window._publication_history_service.record_publication(
                publication_set,
                history_info.get("states", {}),
                successful=True,
                output_paths=[r.get("path") for r in result.get("results", []) if r.get("path")])

    report = {
        "success": all_success,
        "carnet": "Publication : carnet/mise en page",
        "results": all_results,
        "errors": all_errors,
        "warnings": all_warnings,
        "output_directory": output_directory or ""
    }
    PublicationReportWindow(report, owner=window).ShowDialog()


def _preview_then_publish_folder(window, targets):
    preview = _build_preview(window, targets)
    if not targets:
        preview["errors"].append(
            "Le dossier « {0} » ne contient aucun carnet publiable.".format(window._selected_folder.name))

    dialog = PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return

    effective_targets = []
    for target in targets:
        effective_target, settings, history_info = _effective_publication_target(window, target)
        effective_target._history_info = history_info
        effective_target._resolved_settings = settings
        effective_targets.append(effective_target)

    batch_service = PublicationBatchService(window.controller.publication_service)
    report_data = batch_service.publish(
        effective_targets,
        lambda target: getattr(target, "_resolved_settings", window._resolve_settings(target)),
        window._folder_for_set)

    for effective_target in effective_targets:
        history_info = getattr(effective_target, "_history_info", None)
        if history_info and report_data.get("success"):
            window._publication_history_service.record_publication(
                effective_target,
                history_info.get("states", {}),
                successful=True)

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
