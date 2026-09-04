# -*- coding: utf-8 -*-
"""Fenêtre WPF principale du module Export."""

import os

from pyrevit import forms
from System import Guid
from System.Windows import Visibility
from System.Windows.Controls import TreeViewItem, CheckBox, TextBlock
from System.Windows import Thickness
from System.Windows import FontWeights

from export_report_window import PublicationReportWindow
from carnet_sheets_window import CarnetSheetsWindow
from carnet_manager_window import CarnetManagerWindow
from publication_folder import PublicationFolder
from publication_settings import PublicationSettings


class ExportWindow(forms.WPFWindow):
    """Interface principale de publication, organisée comme un Publisher."""

    def __init__(self, controller, repository):
        self.controller = controller
        self.repository = repository
        self.selected_publication_sets = []
        self.session_carnets = []
        self.current_project_unique_ids = set()
        self._loading_settings = False
        self._folders = []
        self._carnets = []
        self._selected_set = None
        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._load_context()

    def _load_context(self):
        sheets = self.controller.export_service.get_sheets()
        self.current_project_unique_ids = set(
            sheet.UniqueId for sheet in sheets
            if sheet is not None and getattr(sheet, "UniqueId", None))
        self._load_dwg_setups()
        self._refresh_tree()
        self._update_selection_info()

    def _load_dwg_setups(self):
        try:
            setups = self.controller.publication_service.dwg_service.get_predefined_setups()
        except Exception:
            setups = []
        self.DwgSetupCombo.ItemsSource = [""] + list(setups)
        self.DwgSetupCombo.SelectedIndex = 0

    def _refresh_tree(self):
        self._folders = self.controller.list_folders()
        self._carnets = [c for c in self.controller.list_persistent()
                         if self._belongs_to_current_project(c)]
        for c in self.session_carnets:
            if self._belongs_to_current_project(c):
                self._carnets.append(c)

        self.PublicationTree.Items.Clear()
        folder_items = {}
        for folder in self._folders:
            if folder.parent_id:
                continue
            node = self._make_folder_node(folder)
            self.PublicationTree.Items.Add(node)
            folder_items[folder.id] = node

        changed = True
        while changed:
            changed = False
            for folder in self._folders:
                if folder.id in folder_items or not folder.parent_id:
                    continue
                parent = folder_items.get(folder.parent_id)
                if parent is not None:
                    node = self._make_folder_node(folder)
                    parent.Items.Add(node)
                    folder_items[folder.id] = node
                    changed = True

        for carnet in self._carnets:
            parent = folder_items.get(carnet.folder_id)
            if parent is None and folder_items:
                parent = next(iter(folder_items.values()))
            if parent is not None:
                parent.Items.Add(self._make_carnet_node(carnet))

        self._folders_by_id = dict((f.id, f) for f in self._folders)
        self._load_selected_settings()

    def _make_folder_node(self, folder):
        node = TreeViewItem()
        node.Tag = ("FOLDER", folder)
        header = TextBlock()
        header.Text = folder.name
        header.FontWeight = FontWeights.Bold
        node.Header = header
        return node

    def _make_carnet_node(self, carnet):
        node = TreeViewItem()
        node.Tag = ("CARNET", carnet)
        check = CheckBox()
        check.Content = carnet.name
        check.IsChecked = self._is_selected(carnet)
        check.Tag = carnet
        check.Margin = Thickness(0, 1, 0, 1)
        check.Checked += self.CarnetChecked
        check.Unchecked += self.CarnetChecked
        node.Header = check
        for item in sorted(carnet.items or [], key=lambda x: ((x.sheet_number or ""), (x.sheet_name or ""))):
            child = TreeViewItem()
            child.Tag = ("SHEET", item)
            child.Header = TextBlock(Text="{0} — {1}".format(
                item.sheet_number or "", item.sheet_name or ""))
            node.Items.Add(child)
        return node

    def _is_selected(self, carnet):
        return any(c.id == carnet.id for c in self.selected_publication_sets)

    def _belongs_to_current_project(self, publication_set):
        return publication_set is not None and any(
            item is not None and item.unique_id in self.current_project_unique_ids
            for item in (publication_set.items or []))

    def CarnetChecked(self, sender, args):
        carnet = sender.Tag
        if sender.IsChecked:
            if not self._is_selected(carnet):
                self.selected_publication_sets.append(carnet)
        else:
            self.selected_publication_sets = [c for c in self.selected_publication_sets
                                              if c.id != carnet.id]
        self._update_selection_info()

    def Tree_SelectedItemChanged(self, sender, args):
        node = self.PublicationTree.SelectedItem
        if node is None or not getattr(node, "Tag", None):
            return
        kind, value = node.Tag
        if kind == "CARNET":
            self._selected_set = value
            self._load_selected_settings()
        elif kind == "SHEET":
            self.SelectedNodeText.Text = "Mise en page : {0} — {1}".format(
                value.sheet_number or "", value.sheet_name or "")

    def Tree_MouseDoubleClick(self, sender, args):
        node = self.PublicationTree.SelectedItem
        if node is None or not getattr(node, "Tag", None):
            return
        kind, value = node.Tag
        if kind == "CARNET":
            if value.persistent:
                resolution = self.controller.resolve_persistent(value)
                value = _ResolvedCarnetView(value.name, resolution.items)
            CarnetSheetsWindow(value, owner=self).ShowDialog()

    def _load_selected_settings(self):
        if self._selected_set is None:
            return
        settings = self._selected_set.publication_settings
        if settings is None:
            settings = PublicationSettings(output_directory=self._selected_set.output_directory)
            self._selected_set.publication_settings = settings
        self._loading_settings = True
        try:
            self.SelectedNodeText.Text = "{0} • {1} mise(s) en page".format(
                self._selected_set.name, len(self._selected_set.items or []))
            self.FolderCombo.ItemsSource = self._folders
            for index, folder in enumerate(self._folders):
                if folder.id == self._selected_set.folder_id:
                    self.FolderCombo.SelectedIndex = index
                    break
            self.PdfCheckBox.IsChecked = settings.pdf_enabled
            self.PdfCombinedRadio.IsChecked = settings.pdf_mode == "COMBINED"
            self.PdfSeparateRadio.IsChecked = settings.pdf_mode == "SEPARATE"
            self.DwgCheckBox.IsChecked = settings.dwg_enabled
            self.DwgCombinedRadio.IsChecked = settings.dwg_mode == "COMBINED"
            self.DwgSeparateRadio.IsChecked = settings.dwg_mode == "SEPARATE"
            self.DwgTrueColorCheckBox.IsChecked = settings.dwg_true_color
            self.OutputDirectoryTextBox.Text = settings.output_directory or ""
            self.FilenameTemplateTextBox.Text = settings.filename_template or "{carnet}"
            self.DwgSetupCombo.SelectedItem = settings.dwg_setup_name or ""
        finally:
            self._loading_settings = False

    def _save_selected_settings(self):
        if self._selected_set is None or self._loading_settings:
            return
        settings = self._selected_set.publication_settings or PublicationSettings()
        settings.pdf_enabled = bool(self.PdfCheckBox.IsChecked)
        settings.pdf_mode = "COMBINED" if self.PdfCombinedRadio.IsChecked else "SEPARATE"
        settings.dwg_enabled = bool(self.DwgCheckBox.IsChecked)
        settings.dwg_mode = "COMBINED" if self.DwgCombinedRadio.IsChecked else "SEPARATE"
        settings.dwg_true_color = bool(self.DwgTrueColorCheckBox.IsChecked)
        settings.output_directory = (self.OutputDirectoryTextBox.Text or "").strip() or None
        settings.filename_template = self.FilenameTemplateTextBox.Text or "{carnet}"
        settings.dwg_setup_name = self.DwgSetupCombo.SelectedItem or None
        self._selected_set.publication_settings = settings
        self._selected_set.output_directory = settings.output_directory
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)

    def SettingsChanged(self, sender, args):
        self._save_selected_settings()

    def FolderChanged(self, sender, args):
        if self._loading_settings or self._selected_set is None or self.FolderCombo.SelectedItem is None:
            return
        self._selected_set.folder_id = self.FolderCombo.SelectedItem.id
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)
            self._refresh_tree()

    def OpenCarnetManager_Click(self, sender, args):
        manager = CarnetManagerWindow(self.controller, owner=self)
        manager.ShowDialog()
        if manager.result:
            for carnet in manager.result:
                if not carnet.persistent:
                    self.session_carnets.append(carnet)
            self._refresh_tree()

    def NewFolder_Click(self, sender, args):
        name = forms.ask_for_string(default="Nouveau dossier", prompt="Nom du dossier", title="Export")
        if not name or not name.strip():
            return
        folder = PublicationFolder(name.strip(), str(Guid.NewGuid()), None, True)
        self.controller.save_folder(folder)
        self._refresh_tree()

    def SelectAllCarnets_Click(self, sender, args):
        self.selected_publication_sets = list(self._carnets)
        self._refresh_tree()
        self._update_selection_info()

    def UnselectAllCarnets_Click(self, sender, args):
        self.selected_publication_sets = []
        self._refresh_tree()
        self._update_selection_info()

    def _update_selection_info(self):
        total = sum(len(c.items or []) for c in self.selected_publication_sets)
        self.SelectionInfo.Text = (
            "{0} carnet(s) sélectionné(s) • {1} mise(s) en page.".format(
                len(self.selected_publication_sets), total)
            if self.selected_publication_sets else "Cochez les carnets à publier.")

    def BrowseOutput_Click(self, sender, args):
        folder = forms.pick_folder(title="Choisir le dossier de publication")
        if folder and self._selected_set is not None:
            self.OutputDirectoryTextBox.Text = folder
            self._save_selected_settings()

    def DeleteNode_Click(self, sender, args):
        node = self.PublicationTree.SelectedItem
        if node is None or not getattr(node, "Tag", None):
            return
        kind, value = node.Tag
        if kind == "CARNET":
            if not forms.alert("Supprimer le carnet « {0} » ?".format(value.name),
                               title="Export", yes=True, no=True):
                return
            if value.persistent:
                self.repository.delete(value.id)
            else:
                self.session_carnets = [c for c in self.session_carnets if c.id != value.id]
            self.selected_publication_sets = [c for c in self.selected_publication_sets if c.id != value.id]
        elif kind == "FOLDER":
            if value.id == "default":
                forms.alert("Le dossier Général ne peut pas être supprimé.", title="Export")
                return
            if not forms.alert("Supprimer le dossier « {0} » ? Il doit être vide.".format(value.name),
                               title="Export", yes=True, no=True):
                return
            if not self.controller.delete_folder(value.id):
                forms.alert("Le dossier n'est pas vide ou ne peut pas être supprimé.", title="Export")
                return
        self._selected_set = None
        self._refresh_tree()
        self._update_selection_info()

    def Publish_Click(self, sender, args):
        if not self.selected_publication_sets:
            forms.alert("Cochez au moins un carnet dans l'arborescence.", title="Publication")
            return
        all_results, all_errors, all_warnings = [], [], []
        all_success = True
        for publication_set in self.selected_publication_sets:
            settings = publication_set.publication_settings or PublicationSettings(
                output_directory=publication_set.output_directory)
            errors = settings.validate()
            if errors:
                all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in errors])
                all_success = False
                continue
            try:
                result = self.controller.publish(
                    publication_set, settings.output_directory,
                    export_pdf=settings.pdf_enabled, export_dwg=settings.dwg_enabled,
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
            all_success = all_success and bool(result.get("success"))

        report = {"success": all_success,
                  "carnet": "{0} carnet(s)".format(len(self.selected_publication_sets)),
                  "results": all_results, "errors": all_errors,
                  "warnings": all_warnings,
                  "output_directory": "Réglages propres à chaque carnet"}
        PublicationReportWindow(report, owner=self).ShowDialog()

    def Close_Click(self, sender, args):
        self.Close()


class _ResolvedCarnetView(object):
    def __init__(self, name, items):
        self.name = name
        self.items = list(items or [])
