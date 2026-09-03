# -*- coding: utf-8 -*-
"""Fenêtre WPF du module Export."""

import os

from pyrevit import forms
from System.Windows import Visibility

from export_report_window import PublicationReportWindow


class PreviewRow(object):
    """Ligne d'aperçu affichée dans le DataGrid WPF."""

    def __init__(self, name, count, status="Prêt"):
        self.Name = name
        self.Count = count
        self.Status = status


class ExportWindow(forms.WPFWindow):
    """Interface de création, gestion et publication des carnets Export."""

    def __init__(self, controller, repository):
        self.controller = controller
        self.repository = repository
        self.current_items = []
        self.current_persistent = None
        self.session_carnets = []

        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._load_context()

    def _load_context(self):
        context = self.controller.get_context()
        self.ParameterCombo.ItemsSource = context["parameters"]
        if self.ParameterCombo.Items.Count:
            self.ParameterCombo.SelectedIndex = 0
        self._load_dwg_setups()
        self._refresh_persistent_carnets()
        self._update_mode()

    def _load_dwg_setups(self):
        """Charge les configurations DWG natives disponibles dans Revit."""
        try:
            setups = self.controller.publication_service.dwg_service.get_predefined_setups()
        except Exception:
            setups = []

        values = [""] + list(setups)
        self.DwgSetupCombo.ItemsSource = values
        self.DwgSetupCombo.SelectedIndex = 0

    def _refresh_persistent_carnets(self):
        rows = []
        for publication_set in self.controller.list_persistent():
            resolution = self.controller.resolve_persistent(publication_set)
            rows.append(_CarnetListEntry(publication_set, resolution.missing_count))

        for publication_set in self.session_carnets:
            rows.append(_CarnetListEntry(publication_set, 0, persistent=False))

        self.PersistentCarnetsList.ItemsSource = rows

    def _update_mode(self):
        if self.ModeParameter.IsChecked:
            self.ManualPanel.Visibility = Visibility.Collapsed
            self.CreateButton.Content = "Créer les carnets"
            self._update_parameter_preview()
        else:
            self.ManualPanel.Visibility = Visibility.Visible
            self.CreateButton.Content = (
                "Enregistrer le carnet"
                if self.ModeManual.IsChecked
                else "Utiliser la sélection"
            )
            self._show_manual_selection()

    def _update_parameter_preview(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            self.ParameterInfo.Text = "Aucun paramètre disponible."
            self.PreviewGrid.ItemsSource = []
            return

        preview = self.controller.get_parameter_preview(parameter_name)
        self.ParameterInfo.Text = (
            "{0} feuille(s) • {1} carnet(s) détecté(s) • "
            "{2} feuille(s) affectée(s)."
        ).format(
            preview["sheet_count"],
            preview["carnet_count"],
            preview["assigned_sheet_count"]
        )

        self.PreviewGrid.ItemsSource = [
            PreviewRow(item["value"], item["count"])
            for item in preview["values"]
        ]
        self.MissingInfo.Visibility = Visibility.Collapsed

    def _show_manual_selection(self):
        if not self.current_items:
            self.ManualSelectionInfo.Text = "Aucune sélection."
            self.PreviewGrid.ItemsSource = []
            return

        self.ManualSelectionInfo.Text = "{0} feuille(s) sélectionnée(s).".format(
            len(self.current_items)
        )
        self.PreviewGrid.ItemsSource = [
            PreviewRow(item.sheet_number, 1, item.sheet_name)
            for item in self.current_items
        ]

    def _get_publication_set(self):
        """Retourne le carnet actuellement publiable."""
        if self.current_persistent is not None:
            if self.current_persistent.persistent:
                return self.controller.resolve_persistent(self.current_persistent)
            return self.current_persistent

        if self.current_items:
            name = self.CarnetNameTextBox.Text
            if name and name.strip():
                return self.controller.create_manual_temporary(
                    name.strip(), self.current_items
                )

        return None

    def ParameterCombo_SelectionChanged(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._update_parameter_preview()

    def Mode_Checked(self, sender, args):
        self._update_mode()

    def SelectSheets_Click(self, sender, args):
        sheets = self.controller.export_service.get_sheets()
        selected = forms.SelectFromList.show(
            sheets,
            title="Sélectionner les feuilles",
            multiselect=True,
            name_attr="SheetNumber",
            description_attr="Name"
        )
        self.current_items = (
            self.controller.export_service.build_publication_items(selected)
            if selected else []
        )
        self.current_persistent = None
        self._show_manual_selection()

    def PersistentCarnet_SelectionChanged(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        self.current_persistent = entry.publication_set if entry else None
        if self.current_persistent is None:
            return

        if self.current_persistent.persistent:
            resolution = self.controller.resolve_persistent(self.current_persistent)
            items = resolution.items
            missing_count = resolution.missing_count
        else:
            items = self.current_persistent.items
            missing_count = 0

        self.PreviewGrid.ItemsSource = [
            PreviewRow(item.sheet_number, 1, item.sheet_name)
            for item in items
        ]

        if missing_count:
            self.MissingInfo.Visibility = Visibility.Visible
            self.MissingInfo.Text = (
                "ATTENTION : {0} élément(s) du carnet sont introuvables "
                "dans le document courant. Ils ne seront pas publiés."
            ).format(missing_count)
        else:
            self.MissingInfo.Visibility = Visibility.Collapsed

    def Create_Click(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._create_parameter_carnets()
            return

        if not self.current_items:
            forms.alert("Sélectionnez au moins une feuille.", title="Export")
            return

        name = self.CarnetNameTextBox.Text
        if not name or not name.strip():
            forms.alert("Saisissez un nom de carnet.", title="Export")
            return

        if self.ModeManual.IsChecked and self.PersistentCheckBox.IsChecked:
            self.controller.create_manual_persistent(name, self.current_items)
            self._refresh_persistent_carnets()
            forms.alert("Carnet enregistré.", title="Export")
        else:
            carnet = self.controller.create_manual_temporary(name, self.current_items)
            self.session_carnets.append(carnet)
            self._refresh_persistent_carnets()
            forms.alert("Carnet temporaire préparé pour la session.", title="Export")

    def _create_parameter_carnets(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            forms.alert("Aucun paramètre sélectionné.", title="Export")
            return

        carnets = self.controller.create_from_parameter(parameter_name)
        self.session_carnets.extend(carnets)
        self._refresh_persistent_carnets()
        self.PreviewGrid.ItemsSource = [
            PreviewRow(carnet.name, len(carnet.items))
            for carnet in carnets
        ]
        forms.alert(
            "{0} carnet(s) préparé(s) à partir de « {1} ».\n"
            "Ils sont disponibles dans la liste des carnets pour publication."
            .format(len(carnets), parameter_name),
            title="Export"
        )

    def BrowseOutput_Click(self, sender, args):
        """Ouvre le sélecteur de dossier pyRevit."""
        folder = forms.pick_folder(title="Choisir le dossier de publication")
        if folder:
            self.OutputDirectoryTextBox.Text = folder

    def Publish_Click(self, sender, args):
        """Lance la publication puis affiche le rapport détaillé."""
        publication_set = self._get_publication_set()
        if publication_set is None:
            forms.alert(
                "Sélectionnez un carnet enregistré ou préparez une sélection manuelle.",
                title="Publication"
            )
            return

        output_directory = self.OutputDirectoryTextBox.Text
        if not output_directory or not output_directory.strip():
            forms.alert("Choisissez un dossier de destination.", title="Publication")
            return

        export_pdf = bool(self.PdfCheckBox.IsChecked)
        export_dwg = bool(self.DwgCheckBox.IsChecked)
        pdf_combined = bool(self.PdfCombinedRadio.IsChecked)
        dwg_combined = bool(self.DwgCombinedRadio.IsChecked)
        setup_name = self.DwgSetupCombo.SelectedItem or None
        true_color = bool(self.DwgTrueColorCheckBox.IsChecked)

        if not export_pdf and not export_dwg:
            forms.alert("Sélectionnez au moins un format.", title="Publication")
            return

        result = self.controller.publish(
            publication_set,
            output_directory.strip(),
            export_pdf=export_pdf,
            export_dwg=export_dwg,
            pdf_combined=pdf_combined,
            dwg_combined=dwg_combined,
            dwg_setup_name=setup_name,
            dwg_true_color=true_color
        )

        result["output_directory"] = output_directory.strip()

        report_window = PublicationReportWindow(result, owner=self)
        report_window.show_dialog()

    def DeleteCarnet_Click(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is None:
            return

        if not entry.publication_set.persistent:
            self.session_carnets = [
                carnet for carnet in self.session_carnets
                if carnet.id != entry.publication_set.id
            ]
            self.current_persistent = None
            self._refresh_persistent_carnets()
            self.PreviewGrid.ItemsSource = []
            return

        confirmed = forms.alert(
            "Supprimer le carnet « {0} » ?".format(entry.publication_set.name),
            title="Export",
            yes=True,
            no=True
        )
        if not confirmed:
            return

        self.repository.delete(entry.publication_set.id)
        self.current_persistent = None
        self._refresh_persistent_carnets()
        self.PreviewGrid.ItemsSource = []
        self.MissingInfo.Visibility = Visibility.Collapsed

    def Close_Click(self, sender, args):
        self.Close()


class _CarnetListEntry(object):
    """Objet d'affichage d'un carnet persistant ou de session."""

    def __init__(self, publication_set, missing_count, persistent=True):
        self.publication_set = publication_set
        suffix = (
            "ATTENTION : {0} manquant(s)".format(missing_count)
            if missing_count
            else "{0} feuille(s)".format(len(publication_set.items))
        )
        if not persistent:
            suffix += " — session"
        self.DisplayName = "{0} — {1}".format(publication_set.name, suffix)
