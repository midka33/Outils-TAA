# -*- coding: utf-8 -*-
"""Fenêtre WPF principale du module Export."""

import os

from pyrevit import forms
from taa_ui_theme import apply_theme
from System import Guid
from System.Windows import FontWeights, Thickness, VerticalAlignment
from System.Windows.Controls import TreeViewItem, TextBlock, StackPanel, Orientation, Grid
from System.Windows.Media import Brushes
from System.Windows.Shapes import Path as IconPath

from export_report_window import PublicationReportWindow
from carnet_sheets_window import CarnetSheetsWindow
from carnet_manager_window import CarnetManagerWindow
from publication_folder import PublicationFolder, _folder_targets
from publication_overview import formats_for, summarize_publication
from publication_settings import PublicationSettings
from publication_set import PublicationSet
from filename_service import FilenameService
from publication_profile_service import PublicationProfileService
from settings_resolver import SettingsResolver
from publication_tree_drag_drop import PublicationTreeDragDrop


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
        apply_theme(self)
        self._load_context()
        self._drag_drop_manager = PublicationTreeDragDrop(self)

    def _load_context(self):
        sheets = self.controller.export_service.get_sheets()
        self.current_project_unique_ids = set(sheet.UniqueId for sheet in sheets if sheet is not None and getattr(sheet, "UniqueId", None))
        self.PdfQualityCombo.ItemsSource = list(PublicationSettings.PDF_QUALITIES)
        self._load_dwg_setups()
        self._load_profiles()
        self.FilenameTokenCombo.ItemsSource = ["{carnet}", "{numero}", "{nom}", "{nom_complet}", "{projet}", "{date}", "{indice}", "{dossier}", "{parametre:Nom}"]
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
        self._carnets = [c for c in self.controller.list_persistent() if self._belongs_to_current_project(c)]
        for c in self.session_carnets:
            if self._belongs_to_current_project(c):
                self._carnets.append(c)
        self._folders_by_id = dict((f.id, f) for f in self._folders)
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

    def _node_header(self, text, icon_key, bold=False):
        """Pictogrammes vectoriels sans dépendance à une police d'icônes."""
        panel = StackPanel(Orientation=Orientation.Horizontal)
        icon = IconPath()
        icon.Data = self.FindResource(icon_key)
        icon.Stroke = self.FindResource("TaaAccentPressed")
        icon.StrokeThickness = 1.5
        icon.Width = 20
        icon.Height = 20
        icon.Margin = Thickness(0, 0, 8, 0)
        label = TextBlock(Text=text)
        label.VerticalAlignment = VerticalAlignment.Center
        if bold:
            label.FontWeight = FontWeights.SemiBold
        panel.Children.Add(icon)
        panel.Children.Add(label)
        return panel

    def _make_folder_node(self, folder):
        node = TreeViewItem()
        node.AllowDrop = True
        node.Tag = ("FOLDER", folder)
        node.Header = self._node_header(folder.name, "TaaFolderIcon", True)
        return node

    def _make_carnet_node(self, carnet):
        node = TreeViewItem()
        node.AllowDrop = True
        node.Tag = ("CARNET", carnet)
        node.Header = self._node_header(carnet.name, "TaaBookIcon")
        # L'ordre de la liste est volontaire : il représente l'ordre manuel
        # défini par l'utilisateur dans l'arborescence de publication.
        for item in (carnet.items or []):
            child = TreeViewItem()
            child.AllowDrop = True
            child.Tag = ("SHEET", item, carnet)
            child.Header = self._sheet_header(item, self._resolve_settings(carnet))
            node.Items.Add(child)
        return node

    def _sheet_header(self, item, settings):
        """Affiche les formats effectifs sur des pictogrammes de feuille."""
        text = "{0} — {1}".format(item.sheet_number or "", item.sheet_name or "")
        formats = formats_for(settings)
        if not formats:
            panel = self._node_header(text, "TaaSheetIcon")
            panel.ToolTip = "Aucun format activé"
            return panel
        panel = StackPanel(Orientation=Orientation.Horizontal)
        for name in formats:
            color = Brushes.Firebrick if name == "PDF" else Brushes.DodgerBlue
            badge = Grid(Width=25, Height=27, Margin=Thickness(0, 0, 5, 0))
            icon = IconPath(Data=self.FindResource("TaaSheetIcon"), Stroke=color,
                            StrokeThickness=1.4, Width=20, Height=22)
            label = TextBlock(Text=name, FontSize=7, FontWeight=FontWeights.Bold,
                              Foreground=color, VerticalAlignment=VerticalAlignment.Bottom)
            badge.Children.Add(icon)
            badge.Children.Add(label)
            panel.Children.Add(badge)
        panel.Children.Add(TextBlock(Text=text, VerticalAlignment=VerticalAlignment.Center))
        panel.ToolTip = " + ".join(formats)
        return panel

    def _update_publication_overview(self):
        """Actualise les formats et le périmètre sans reconstruire la sélection."""
        def refresh(nodes):
            for node in nodes:
                tag = node.Tag
                if tag and tag[0] == "SHEET":
                    node.Header = self._sheet_header(tag[1], self._resolve_settings(tag[2]))
                refresh(node.Items)
        refresh(self.PublicationTree.Items)
        targets = []
        context = "Aucune publication sélectionnée."
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            targets = _folder_targets(self, self._selected_folder)
            context = "Dossier : {0} | Périmètre : dossier et sous-dossiers".format(self._selected_folder.name)
        elif self._selected_set is not None:
            targets = [self._selected_set]
            folder = self._folder_for_set(self._selected_set)
            chain = self.settings_resolver.folder_chain(folder, self._folders)
            path = " / ".join(f.name for f in reversed(chain))
            scope = "cette mise en page" if self._selected_kind == "SHEET" else "tout le carnet"
            context = "Dossier : {0} | Carnet : {1} | Périmètre : {2}".format(path, self._selected_set.name, scope)
        self.PublicationSummaryText.Text = context
        if targets:
            self.PublicationSummaryText.Text += "\n" + summarize_publication(
                targets, self._resolve_settings,
                self._selected_item if self._selected_kind == "SHEET" else None)

    def _belongs_to_current_project(self, publication_set):
        return publication_set is not None and any(item is not None and item.unique_id in self.current_project_unique_ids for item in (publication_set.items or []))

    def _folder_for_set(self, publication_set):
        return self._folders_by_id.get(getattr(publication_set, "folder_id", None))

    def _resolve_settings(self, publication_set):
        return self.settings_resolver.resolve(publication_set, folder=self._folder_for_set(publication_set), folders=self._folders)

    def _setting_source(self, publication_set, field):
        return self.settings_resolver.source_for(publication_set, field, folder=self._folder_for_set(publication_set), folders=self._folders)

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
        self.PublicationSummaryText.Text = "Aucune publication sélectionnée."
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
        effective = self._resolve_settings(self._selected_set)
        self._loading_settings = True
        self._loading_profile = True
        try:
            if self._selected_kind == "SHEET":
                item = self._selected_item
                self.SelectedNodeText.Text = "Mise en page : {0} — {1}\nPublication : cette mise en page uniquement.".format(item.sheet_number or "", item.sheet_name or "")
            else:
                self.SelectedNodeText.Text = "{0} • {1} mise(s) en page\nPublication : carnet entier.".format(self._selected_set.name, len(self._selected_set.items or []))
            self.PdfQualityCombo.SelectedItem = effective.pdf_quality
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
        self._update_publication_overview()

    def _load_folder_settings(self):
        folder = self._selected_folder
        if folder is None:
            return
        settings = self.settings_resolver.resolve(None, folder=folder, folders=self._folders)
        self._loading_settings = True
        self._loading_profile = True
        try:
            self.SelectedNodeText.Text = "Dossier : {0}\nLes réglages définis ici sont hérités par les sous-dossiers et les carnets.".format(folder.name)
            self.PdfQualityCombo.SelectedItem = settings.pdf_quality
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
            self._update_folder_inheritance_info(folder)
            self.ProfileInfoText.Text = "Réglages effectifs : les valeurs non définies ici proviennent des dossiers parents."
        finally:
            self._loading_profile = False
            self._loading_settings = False
        self._update_filename_preview(settings)
        self._update_publication_overview()

    def _inheritance_description(self, publication_set, folder):
        groups = []
        labels = {}
        for field in self.INHERITABLE_FIELDS:
            label = self.settings_resolver.source_label(
                publication_set, field, folder=folder, folders=self._folders)
            if label not in labels:
                labels[label] = []
                groups.append(label)
            labels[label].append(self._field_label(field))
        return " | ".join("{0} : {1}".format(label, ", ".join(labels[label]))
                          for label in groups)

    def _update_folder_inheritance_info(self, folder):
        settings = folder.publication_settings
        local = settings is not None and any(
            getattr(settings, field, None) is not None for field in self.INHERITABLE_FIELDS)
        self.RevertInheritanceButton.Content = "Revenir à l'héritage du parent"
        self.RevertInheritanceButton.IsEnabled = bool(folder.parent_id and local)
        self.InheritanceInfoText.Text = self._inheritance_description(None, folder)

    def _update_inheritance_info(self, publication_set):
        sources = dict((field, self._setting_source(publication_set, field)) for field in self.INHERITABLE_FIELDS)
        self._set_inheritance_ui(True, sources)
        self.InheritanceInfoText.Text = self._inheritance_description(
            publication_set, self._folder_for_set(publication_set))

    def _set_inheritance_ui(self, enabled, sources):
        self.InheritanceInfoText.Text = ""
        self.RevertInheritanceButton.Content = "Revenir à l’héritage du dossier"
        self.RevertInheritanceButton.IsEnabled = enabled and self._selected_set is not None and any(sources.get(field) == "Carnet" for field in self.INHERITABLE_FIELDS)

    @staticmethod
    def _field_label(field):
        labels = {"pdf_quality": "qualité PDF", "pdf_enabled": "PDF", "pdf_mode": "mode PDF", "dwg_enabled": "DWG", "dwg_mode": "mode DWG", "dwg_setup_name": "configuration DWG", "dwg_true_color": "True Color", "output_directory": "destination", "filename_template": "nommage"}
        return labels.get(field, field)

    def RevertInheritance_Click(self, sender, args):
        if self._selected_kind == "FOLDER":
            folder = self._selected_folder
            if folder is None or not folder.parent_id or folder.publication_settings is None:
                return
            # Action explicite sur ce dossier uniquement, jamais sur ses descendants.
            for field in self.INHERITABLE_FIELDS:
                setattr(folder.publication_settings, field, None)
            self.controller.save_folder(folder)
            self._load_folder_settings()
            return
        if self._selected_set is None or self._selected_set.publication_settings is None:
            return
        settings = self._selected_set.publication_settings
        for field in self.INHERITABLE_FIELDS:
            setattr(settings, field, None)
        self._selected_set.publication_settings = settings
        self._selected_set.output_directory = None
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)
        self._load_selected_settings()

    def _control_value(self, field):
        values = {
            "pdf_quality": int(self.PdfQualityCombo.SelectedItem or 300),
            "pdf_enabled": bool(self.PdfCheckBox.IsChecked),
            "pdf_mode": "COMBINED" if self.PdfCombinedRadio.IsChecked else "SEPARATE",
            "dwg_enabled": bool(self.DwgCheckBox.IsChecked),
            "dwg_mode": "COMBINED" if self.DwgCombinedRadio.IsChecked else "SEPARATE",
            "dwg_setup_name": self.DwgSetupCombo.SelectedItem or None,
            "dwg_true_color": bool(self.DwgTrueColorCheckBox.IsChecked),
            "output_directory": (self.OutputDirectoryTextBox.Text or "").strip() or None,
            "filename_template": self.FilenameTemplateTextBox.Text or "{carnet}"
        }
        return values.get(field)

    def _save_selected_field(self, field):
        if self._selected_set is None or self._loading_settings or field not in self.INHERITABLE_FIELDS:
            return
        settings = self._selected_set.publication_settings or PublicationSettings()
        setattr(settings, field, self._control_value(field))
        self._selected_set.publication_settings = settings
        self._selected_set.output_directory = settings.output_directory
        if self._selected_set.persistent:
            self.controller.save_persistent(self._selected_set)
        self._update_inheritance_info(self._selected_set)
        self._update_filename_preview(self._resolve_settings(self._selected_set))
        self._update_publication_overview()

    def _save_selected_settings(self):
        return

    def _save_folder_settings(self, field=None):
        folder = self._selected_folder
        if folder is None or self._loading_settings:
            return
        settings = folder.publication_settings or PublicationSettings()
        if field is None:
            return
        setattr(settings, field, self._control_value(field))
        folder.publication_settings = settings
        self.controller.save_folder(folder)
        self._load_folder_settings()

    def _apply_profile_values(self, values):
        if not values or self._selected_set is None:
            return
        settings = self._selected_set.publication_settings or PublicationSettings()
        settings.pdf_enabled = bool(values.get("pdf_enabled", True))
        settings.pdf_quality = values.get("pdf_quality") or 300
        settings.pdf_mode = values.get("pdf_mode", "COMBINED")
        settings.dwg_enabled = bool(values.get("dwg_enabled", True))
        settings.dwg_mode = values.get("dwg_mode", "SEPARATE")
        settings.dwg_setup_name = values.get("dwg_setup_name")
        settings.dwg_true_color = bool(values.get("dwg_true_color", True))
        self._selected_set.publication_settings = settings
        self._loading_settings = True
        try:
            self.PdfQualityCombo.SelectedItem = settings.pdf_quality
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
        self._update_inheritance_info(self._selected_set)
        self._update_filename_preview(self._resolve_settings(self._selected_set))
        self._update_publication_overview()

    def _update_filename_preview(self, settings):
        try:
            if self._selected_set is None:
                self.FilenamePreviewText.Text = "—"
                return
            folder = self._folder_for_set(self._selected_set)
            item = self._selected_item if self._selected_kind == "SHEET" else None
            preview, unknown = self.filename_service.resolve(
                settings.filename_template or "{carnet}", self._selected_set,
                item=item, folder_name=getattr(folder, "name", None))
            if unknown:
                preview += " — Variables non résolues : " + ", ".join(unknown)
            self.FilenamePreviewText.Text = preview or "—"
        except Exception as exc:
            self.FilenamePreviewText.Text = "Aperçu indisponible : {0}".format(exc)

    def FilenameToken_InsertClick(self, sender, args):
        token = self.FilenameTokenCombo.SelectedItem
        if not token:
            return
        text = self.FilenameTemplateTextBox.Text or ""
        self.FilenameTemplateTextBox.Text = text + token
        self._save_selected_field("filename_template")

    def SettingsChanged(self, sender, args):
        if self._loading_settings:
            return
        mapping = {
            "PdfQualityCombo": "pdf_quality",
            "PdfCheckBox": "pdf_enabled", "PdfCombinedRadio": "pdf_mode", "PdfSeparateRadio": "pdf_mode",
            "DwgCheckBox": "dwg_enabled", "DwgCombinedRadio": "dwg_mode", "DwgSeparateRadio": "dwg_mode",
            "DwgSetupCombo": "dwg_setup_name", "DwgTrueColorCheckBox": "dwg_true_color",
            "OutputDirectoryTextBox": "output_directory", "FilenameTemplateTextBox": "filename_template"
        }
        field = mapping.get(getattr(sender, "Name", ""))
        if self._selected_kind == "FOLDER":
            self._save_folder_settings(field)
        else:
            self._save_selected_field(field)


class _ResolvedCarnetView(object):
    def __init__(self, name, items):
        self.name = name
        self.items = items
