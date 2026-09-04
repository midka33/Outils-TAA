# -*- coding: utf-8 -*-
"""Fenêtre WPF principale du module Export."""

import os

from pyrevit import forms
from System import Guid
from System.Windows import FontWeights
from System.Windows.Controls import TreeViewItem, TextBlock

from export_report_window import PublicationReportWindow
from carnet_sheets_window import CarnetSheetsWindow
from carnet_manager_window import CarnetManagerWindow
from publication_folder import PublicationFolder
from publication_settings import PublicationSettings
from publication_set import PublicationSet
from filename_service import FilenameService
from publication_profile_service import PublicationProfileService
from settings_resolver import SettingsResolver


class ExportWindow(forms.WPFWindow):
    """Interface principale de publication, organisée comme un Publisher."""

    INHERITABLE_FIELDS = PublicationSettings.FIELDS

    def __init__(self, controller, repository):
        self.controller = controller
        self.repository = repository
        self.session_carnets = []
        self.current_project_unique_ids = set()
        self._loading_settings = False
        self._loading_profile = False
        self._loading_inheritance = False
        self._folders = []
        self._carnets = []
        self._selected_set = None
        self._selected_item = None
        self._selected_kind = None
        self._selected_folder = None
        self.filename_service = FilenameService(controller.document)
        self.profile_service = PublicationProfileService()
        self.settings_resolver = SettingsResolver(self.profile_service)
        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._load_context()

    def _load_context(self):
        sheets = self.controller.export_service.get_sheets()
        self.current_project_unique_ids = set(
            sheet.UniqueId for sheet in sheets
            if sheet is not None and getattr(sheet, "UniqueId", None))
        self._load_dwg_setups()
        self._load_profiles()
        self.FilenameTokenCombo.ItemsSource = [
            "{carnet}", "{numero}", "{nom}", "{nom_complet}",
            "{projet}", "{date}", "{indice}", "{dossier}",
            "{parametre:Nom}"
        ]
        self._refresh_tree()
        self._update_selection_info()

    def _load_profiles(self):
        self.ProfileCombo.ItemsSource = self.profile_service.list_profiles()
        self.ProfileCombo.SelectedIndex = -1

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
        node.Header = TextBlock(Text=carnet.name)
        for item in sorted(carnet.items or [],
                           key=lambda x: ((x.sheet_number or ""), (x.sheet_name or ""))):
            child = TreeViewItem()
            child.Tag = ("SHEET", item, carnet)
            child.Header = TextBlock(Text="{0} — {1}".format(
                item.sheet_number or "", item.sheet_name or ""))
            node.Items.Add(child)
        return node

    def _belongs_to_current_project(self, publication_set):
        return publication_set is not None and any(
            item is not None and item.unique_id in self.current_project_unique_ids
            for item in (publication_set.items or []))

    def _folder_for_set(self, publication_set):
        return self._folders_by_id.get(getattr(publication_set, "folder_id", None))

    def _resolve_settings(self, publication_set):
        folder = self._folder_for_set(publication_set)
        return self.settings_resolver.resolve(publication_set, folder=folder)

    def _setting_source(self, publication_set, field):
        folder = self._folder_for_set(publication_set)
        return self.settings_resolver.source_for(publication_set, field, folder=folder)

    def Tree_SelectedItemChanged(self, sender, args):
        node = self.PublicationTree.SelectedItem
        self._selected_set = None
        self._selected_item = None
        self._selected_kind = None
        self._selected_folder = None
        if node is None or not getattr(node, "Tag", None):
            self._set_no_selection()
            return
        tag = node.Tag
        if tag[0] == "CARNET":
            self._selected_kind = "CARNET"
            self._selected_set = tag[1]
            self._load_selected_settings()
            self._update_selection_info()
            return
        if tag[0] == "SHEET":
            self._selected_kind = "SHEET"
            self._selected_item = tag[1]
            self._selected_set = tag[2]
            self._load_selected_settings()
            self._update_selection_info()
            return
        self._selected_kind = "FOLDER"
        self._selected_folder = tag[1]
        self._load_folder_settings()
        self._update_selection_info()

    def _set_no_selection(self):
        self.SelectedNodeText.Text = "Sélectionnez un dossier, un carnet ou une mise en page dans l'arborescence."
        self.SelectionInfo.Text = "Aucune publication sélectionnée."
        self.PublishButton.Content = "Publier…"
        self.PublishButton.IsEnabled = False
        self.FilenamePreviewText.Text = "—"
        self._set_inheritance_ui(False, {})
        self._loading_profile = True
        try:
            self.ProfileCombo.SelectedIndex = -1
        finally:
            self._loading_profile = False

    def Tree_MouseDoubleClick(self, sender, args):
        node = self.PublicationTree.SelectedItem
        if node is None or not getattr(node, "Tag", None):
            return
        tag = node.Tag
        if tag[0] == "CARNET":
            value = tag[1]
            if value.persistent:
                resolution = self.controller.resolve_persistent(value)
                value = _ResolvedCarnetView(value.name, resolution.items)
            CarnetSheetsWindow(value, owner=self).ShowDialog()

    def _load_selected_settings(self):
        if self._selected_set is None:
            return
        folder = self._folder_for_set(self._selected_set)
        effective = self._resolve_settings(self._selected_set)
        self._loading_settings = True
        self._loading_profile = True
        try:
            if self._selected_kind == "SHEET":
                item = self._selected_item
                self.SelectedNodeText.Text = (
                    "Mise en page : {0} — {1}\nPublication : cette mise en page uniquement."
                ).format(item.sheet_number or "", item.sheet_name or "")
            else:
                self.SelectedNodeText.Text = "{0} • {1} mise(s) en page\nPublication : carnet entier.".format(
                    self._selected_set.name, len(self._selected_set.items or []))
            self.FolderCombo.ItemsSource = self._folders
            self.FolderCombo.SelectedIndex = -1
            for index, value in enumerate(self._folders):
                if value.id == self._selected_set.folder_id:
                    self.FolderCombo.SelectedIndex = index
                    break
            self.PdfCheckBox.IsChecked = effective.pdf_enabled
            self.PdfCombinedRadio.IsChecked = effective.pdf_mode == "COMBINED"
            self.PdfSeparateRadio.IsChecked = effective.pdf_mode == "SEPARATE"
            self.DwgCheckBox.IsChecked = effective.dwg_enabled
            self.DwgCombinedRadio.IsChecked = effective.dwg_mode == "COMBINED"
            self.DwgSeparateRadio.IsChecked = effective.dwg_mode == "SEPARATE"
            self.DwgTrueColorCheckBox.IsChecked = effective.dwg_true_color
            self.OutputDirectoryTextBox.Text = effective.output_directory or ""
            self.FilenameTemplateTextBox.Text = effective.filename_template or "{carnet}"
            self.DwgSetupCombo.SelectedItem = effective.dwg_setup_name or ""
            self.ProfileCombo.SelectedIndex = -1
            self._update_inheritance_info(self._selected_set)
        finally:
            self._loading_profile = False
            self._loading_settings = False
        self._update_filename_preview(effective)

    def _load_folder_settings(self):
        folder = self._selected_folder
        if folder is None:
            return
        settings = folder.publication_settings or PublicationSettings()
        self._loading_settings = True
        self._loading_profile = True
        try:
            self.SelectedNodeText.Text = "Dossier : {0}\nLes réglages définis ici sont hérités par les carnets du dossier.".format(folder.name)
            self.FolderCombo.ItemsSource = self._folders
            self.FolderCombo.SelectedIndex = -1
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
            self.ProfileCombo.SelectedIndex = -1
            self._set_inheritance_ui(False, {})
            self.ProfileInfoText.Text = "Réglages du dossier : les carnets peuvent les hériter ou les remplacer."
        finally:
            self._loading_profile = False
            self._loading_settings = False
        self._update_filename_preview(settings)

    def _update_inheritance_info(self, publication_set):
        sources = dict((field, self._setting_source(publication_set, field))
                       for field in self.INHERITABLE_FIELDS)
        self._set_inheritance_ui(True, sources)
        inherited = [field for field in self.INHERITABLE_FIELDS if sources[field] == "Dossier"]
        if inherited:
            self.InheritanceInfoText.Text = "🔗 Hérité du dossier : {0}".format(
                ", ".join(self._field_label(field) for field in inherited))
        else:
            self.InheritanceInfoText.Text = "✏️ Réglages définis au niveau du carnet."

    def _set_inheritance_ui(self, enabled, sources):
        self.InheritanceInfoText.Text = ""
        self.RevertInheritanceButton.IsEnabled = enabled and bool(
            self._selected_set is not None and
            any(sources.get(field) == "Carnet" for field in self.INHERITABLE_FIELDS))

    @staticmethod
    def _field_label(field):
        labels = {
            "pdf_enabled": "PDF", "pdf_mode": "mode PDF",
            "dwg_enabled": "DWG", "dwg_mode": "mode DWG",
            "dwg_setup_name": "configuration DWG", "dwg_true_color": "True Color",
            "output_directory": "destination", "filename_template": "nommage"
        }
        return labels.get(field, field)

    def RevertInheritance_Click(self, sender, args):
        if self._selected_set is None:
            return
        settings = self._selected_set.publication_settings
        if settings is None:
            return
        for field in self.INHERITABLE_FIELDS:
            setattr(settings, field, None)
        self._selected_set.publication_settings = settings
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)
        self._load_selected_settings()

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
        self._update_inheritance_info(self._selected_set)
        self._update_filename_preview(settings)

    def _save_folder_settings(self):
        folder = self._selected_folder
        if folder is None or self._loading_settings:
            return
        settings = folder.publication_settings or PublicationSettings()
        settings.pdf_enabled = bool(self.PdfCheckBox.IsChecked)
        settings.pdf_mode = "COMBINED" if self.PdfCombinedRadio.IsChecked else "SEPARATE"
        settings.dwg_enabled = bool(self.DwgCheckBox.IsChecked)
        settings.dwg_mode = "COMBINED" if self.DwgCombinedRadio.IsChecked else "SEPARATE"
        settings.dwg_true_color = bool(self.DwgTrueColorCheckBox.IsChecked)
        settings.output_directory = (self.OutputDirectoryTextBox.Text or "").strip() or None
        settings.filename_template = self.FilenameTemplateTextBox.Text or "{carnet}"
        settings.dwg_setup_name = self.DwgSetupCombo.SelectedItem or None
        folder.publication_settings = settings
        self.controller.save_folder(folder)
        self._update_filename_preview(settings)

    def _apply_profile_values(self, values):
        if not values or self._selected_set is None:
            return
        settings = self._selected_set.publication_settings or PublicationSettings()
        settings.pdf_enabled = bool(values.get("pdf_enabled", True))
        settings.pdf_mode = values.get("pdf_mode", "COMBINED")
        settings.dwg_enabled = bool(values.get("dwg_enabled", True))
        settings.dwg_mode = values.get("dwg_mode", "SEPARATE")
        settings.dwg_setup_name = values.get("dwg_setup_name")
        settings.dwg_true_color = bool(values.get("dwg_true_color", True))
        self._selected_set.publication_settings = settings
        self._loading_settings = True
        try:
            self.PdfCheckBox.IsChecked = settings.pdf_enabled
            self.PdfCombinedRadio.IsChecked = settings.pdf_mode == "COMBINED"
            self.PdfSeparateRadio.IsChecked = settings.pdf_mode == "SEPARATE"
            self.DwgCheckBox.IsChecked = settings.dwg_enabled
            self.DwgCombinedRadio.IsChecked = settings.dwg_mode == "COMBINED"
            self.DwgSeparateRadio.IsChecked = settings.dwg_mode == "SEPARATE"
            self.DwgTrueColorCheckBox.IsChecked = settings.dwg_true_color
            self.DwgSetupCombo.SelectedItem = settings.dwg_setup_name or ""
        finally:
            self._loading_settings = False
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)
        self.ProfileInfoText.Text = "Profil appliqué au carnet. La destination et le nommage peuvent toujours être hérités du dossier."
        self._update_inheritance_info(self._selected_set)
        self._update_filename_preview(settings)

    def ProfileChanged(self, sender, args):
        if self._loading_profile or self._selected_set is None:
            return
        name = self.ProfileCombo.SelectedItem
        if not name:
            return
        values = self.profile_service.get(name)
        if not values:
            return
        self._loading_profile = True
        try:
            self._apply_profile_values(values)
        finally:
            self._loading_profile = False

    def SaveProfile_Click(self, sender, args):
        if self._selected_set is None:
            forms.alert("Sélectionnez d'abord un carnet ou une mise en page.", title="Profil")
            return
        name = forms.ask_for_string(default="Mon profil", prompt="Nom du profil à enregistrer", title="Profil de publication")
        if not name or not name.strip():
            return
        try:
            self._save_selected_settings()
            saved_name = self.profile_service.save(name.strip(), self._selected_set.publication_settings)
        except Exception as exc:
            forms.alert("Impossible d'enregistrer le profil : {0}".format(exc), title="Profil")
            return
        self._load_profiles()
        self._loading_profile = True
        try:
            self.ProfileCombo.SelectedItem = saved_name
        finally:
            self._loading_profile = False
        self.ProfileInfoText.Text = "Profil personnalisé enregistré : {0}.".format(saved_name)

    def DeleteProfile_Click(self, sender, args):
        name = self.ProfileCombo.SelectedItem
        if not name:
            forms.alert("Sélectionnez un profil personnalisé à supprimer.", title="Profil")
            return
        if name in self.profile_service.DEFAULT_PROFILES:
            forms.alert("Les profils intégrés ne peuvent pas être supprimés.", title="Profil")
            return
        if not forms.alert("Supprimer le profil « {0} » ?".format(name), title="Profil", yes=True, no=True):
            return
        if self.profile_service.delete(name):
            self._load_profiles()
            self.ProfileInfoText.Text = "Profil supprimé. Les réglages actuels du carnet restent inchangés."

    def _update_filename_preview(self, settings=None):
        if self._selected_set is None and settings is None:
            self.FilenamePreviewText.Text = "—"
            return
        if settings is None:
            settings = self._resolve_settings(self._selected_set)
        template = getattr(settings, "filename_template", None) or "{carnet}"
        item = self._selected_item
        try:
            publication_set = self._selected_set
            if publication_set is None:
                self.FilenamePreviewText.Text = "—"
                return
            pdf_name, unknown = self.filename_service.filename(template, publication_set,
                                                                 item=item, extension=".pdf")
            self.FilenamePreviewText.Text = (
                "{}  ⚠ variables inconnues : {}".format(pdf_name, ", ".join(unknown))
                if unknown else pdf_name)
        except Exception as exc:
            self.FilenamePreviewText.Text = "Erreur de nommage : {}".format(exc)

    def FilenameTokenChanged(self, sender, args):
        return

    def InsertFilenameToken_Click(self, sender, args):
        token = self.FilenameTokenCombo.SelectedItem
        if not token:
            return
        text = self.FilenameTemplateTextBox.Text or ""
        start = self.FilenameTemplateTextBox.SelectionStart
        length = self.FilenameTemplateTextBox.SelectionLength
        self.FilenameTemplateTextBox.Text = text[:start] + token + text[start + length:]
        self.FilenameTemplateTextBox.SelectionStart = start + len(token)
        self.FilenameTemplateTextBox.Focus()
        if self._selected_kind == "FOLDER":
            self._save_folder_settings()
        else:
            self._save_selected_settings()

    def SettingsChanged(self, sender, args):
        if self._selected_kind == "FOLDER":
            self._save_folder_settings()
        else:
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

    def _update_selection_info(self):
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
        if self._selected_kind == "FOLDER":
            self.SelectionInfo.Text = "Dossier sélectionné : les réglages ci-dessus seront hérités par ses carnets."
            self.PublishButton.Content = "Publier…"
            self.PublishButton.IsEnabled = False
            return
        self._set_no_selection()

    def BrowseOutput_Click(self, sender, args):
        folder = forms.pick_folder(title="Choisir le dossier de publication")
        if folder:
            self.OutputDirectoryTextBox.Text = folder
            if self._selected_kind == "FOLDER":
                self._save_folder_settings()
            elif self._selected_set is not None:
                self._save_selected_settings()

    def DeleteNode_Click(self, sender, args):
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

    def _make_sheet_target(self):
        parent = self._selected_set
        settings = self._resolve_settings(parent)
        target = PublicationSet(
            name=parent.name, items=[self._selected_item], source=parent.source,
            output_directory=settings.output_directory,
            filename_template_id=parent.filename_template_id,
            set_id=str(Guid.NewGuid()), persistent=False,
            folder_id=parent.folder_id, publication_settings=settings)
        target.folder_name = self._folder_name(parent)
        return target

    def _folder_name(self, publication_set):
        folder = self._folders_by_id.get(getattr(publication_set, "folder_id", None))
        return folder.name if folder is not None else ""

    def Publish_Click(self, sender, args):
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            targets = [self._make_sheet_target()]
        elif self._selected_kind == "CARNET" and self._selected_set is not None:
            self._selected_set.folder_name = self._folder_name(self._selected_set)
            targets = [self._selected_set]
        else:
            forms.alert("Sélectionnez un carnet ou une mise en page dans l'arborescence.", title="Publication")
            return
        all_results, all_errors, all_warnings = [], [], []
        all_success = True
        report_output_directory = None
        for publication_set in targets:
            settings = self._resolve_settings(publication_set)
            errors = settings.validate()
            if errors:
                all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in errors])
                all_success = False
                continue
            report_output_directory = settings.output_directory
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
        selection_label = "mise en page" if self._selected_kind == "SHEET" else "carnet"
        report = {"success": all_success, "carnet": "Publication : {0}".format(selection_label),
                  "results": all_results, "errors": all_errors, "warnings": all_warnings,
                  "output_directory": report_output_directory or ""}
        PublicationReportWindow(report, owner=self).ShowDialog()

    def Close_Click(self, sender, args):
        self.Close()


class _ResolvedCarnetView(object):
    """Vue légère utilisée par la fenêtre de consultation d'un carnet."""

    def __init__(self, name, items):
        self.name = name
        self.items = items
        self.persistent = False
