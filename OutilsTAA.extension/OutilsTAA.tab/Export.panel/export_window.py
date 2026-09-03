"""Fenêtre WPF du module Export.

La fenêtre ne contient pas de logique Revit : elle dialogue avec
CarnetController et prépare les données pour le futur moteur PDF/DWG.
"""

import os

from pyrevit import forms, revit

from carnet_view_model import CarnetListItem


class PreviewRow(object):
    """Ligne d'aperçu affichée dans le DataGrid WPF."""

    def __init__(self, name, count, status="Prêt"):
        self.Name = name
        self.Count = count
        self.Status = status


class ExportWindow(forms.WPFWindow):
    """Interface de création et de gestion des carnets Export."""

    def __init__(self, controller, repository):
        self.controller = controller
        self.repository = repository
        self.current_items = []
        self.current_persistent = None
        self._context = None

        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._load_context()

    def _load_context(self):
        self._context = self.controller.get_context()
        self.ParameterCombo.ItemsSource = self._context["parameters"]

        if self.ParameterCombo.Items.Count:
            self.ParameterCombo.SelectedIndex = 0

        self._refresh_persistent_carnets()
        self._update_mode()

    def _refresh_persistent_carnets(self):
        rows = []
        for publication_set in self.controller.list_persistent():
            resolution = self.controller.resolve_persistent(publication_set)
            rows.append(
                _CarnetListEntry(
                    publication_set,
                    resolution.missing_count
                )
            )
        self.PersistentCarnetsList.ItemsSource = rows

    def _update_mode(self):
        if self.ModeParameter.IsChecked:
            self.ManualPanel.Visibility = forms.Visibility.Collapsed
            self.CreateButton.Content = "Créer les carnets"
            self._update_parameter_preview()
        else:
            self.ManualPanel.Visibility = forms.Visibility.Visible
            self.CreateButton.Content = "Enregistrer le carnet" if self.ModeManual.IsChecked else "Utiliser la sélection"
            self._show_manual_selection()

    def _update_parameter_preview(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            self.ParameterInfo.Text = "Aucun paramètre disponible."
            self.PreviewGrid.ItemsSource = []
            return

        preview = self.controller.get_parameter_preview(parameter_name)
        self.ParameterInfo.Text = (
            "{0} feuille(s) • {1} carnet(s) détecté(s) • {2} feuille(s) affectée(s)."
            .format(
                preview["sheet_count"],
                preview["carnet_count"],
                preview["assigned_sheet_count"]
            )
        )

        rows = []
        for item in preview["values"]:
            rows.append(PreviewRow(item["value"], item["count"]))
        self.PreviewGrid.ItemsSource = rows
        self.MissingInfo.Visibility = forms.Visibility.Collapsed

    def _show_manual_selection(self):
        if self.current_items:
            self.ManualSelectionInfo.Text = "{0} feuille(s) sélectionnée(s).".format(
                len(self.current_items)
            )
            self.PreviewGrid.ItemsSource = [
                PreviewRow(
                    item.sheet_number,
                    1,
                    item.sheet_name
                )
                for item in self.current_items
            ]
        else:
            self.ManualSelectionInfo.Text = "Aucune sélection."
            self.PreviewGrid.ItemsSource = []

    def ParameterCombo_SelectionChanged(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._update_parameter_preview()

    def Mode_Checked(self, sender, args):
        self._update_mode()

    def SelectSheets_Click(self, sender, args):
        from Autodesk.Revit.DB import ViewSheet
        from pyrevit import forms as pyrevit_forms

        sheets = self.controller.export_service.get_sheets()
        selected = pyrevit_forms.SelectFromList.show(
            sheets,
            title="Sélectionner les feuilles",
            multiselect=True,
            name_attr="Name",
            description_attr="SheetNumber"
        )

        if selected:
            self.current_items = self.controller.export_service.build_publication_items(
                selected
            )
        else:
            self.current_items = []
        self._show_manual_selection()

    def PersistentCarnet_SelectionChanged(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is None:
            self.current_persistent = None
            return

        self.current_persistent = entry.publication_set
        resolution = self.controller.resolve_persistent(self.current_persistent)

        rows = [
            PreviewRow(item.sheet_number, 1, item.sheet_name)
            for item in resolution.items
        ]
        self.PreviewGrid.ItemsSource = rows

        if resolution.missing_count:
            self.MissingInfo.Visibility = forms.Visibility.Visible
            self.MissingInfo.Text = (
                "ATTENTION : {0} élément(s) du carnet sont introuvables dans "
                "le document courant. Ils ne seront pas publiés tant qu'ils "
                "n'auront pas été réaffectés."
            ).format(resolution.missing_count)
        else:
            self.MissingInfo.Visibility = forms.Visibility.Collapsed

    def Create_Click(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._create_parameter_carnets()
            return

        if not self.current_items:
            forms.alert(
                "Sélectionnez au moins une feuille.",
                title="Export"
            )
            return

        name = self.CarnetNameTextBox.Text
        if not name or not name.strip():
            forms.alert(
                "Saisissez un nom de carnet.",
                title="Export"
            )
            return

        if self.ModeManual.IsChecked and self.PersistentCheckBox.IsChecked:
            self.controller.create_manual_persistent(name, self.current_items)
            self._refresh_persistent_carnets()
            forms.alert("Carnet enregistré.", title="Export")
        else:
            self.controller.create_manual_temporary(name, self.current_items)
            forms.alert("Carnet temporaire préparé pour la session.", title="Export")

    def _create_parameter_carnets(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            forms.alert("Aucun paramètre sélectionné.", title="Export")
            return

        carnets = self.controller.create_from_parameter(parameter_name)
        self.PreviewGrid.ItemsSource = [
            PreviewRow(carnet.name, len(carnet.items))
            for carnet in carnets
        ]

        forms.alert(
            "{0} carnet(s) préparé(s) à partir de « {1} ».".format(
                len(carnets),
                parameter_name
            ),
            title="Export"
        )

    def DeleteCarnet_Click(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is None:
            return

        if not forms.alert(
            "Supprimer le carnet « {0} » ?".format(entry.publication_set.name),
            title="Export",
            yes=True,
            no=True
        ):
            return

        self.repository.delete(entry.publication_set.id)
        self.current_persistent = None
        self._refresh_persistent_carnets()
        self.PreviewGrid.ItemsSource = []
        self.MissingInfo.Visibility = forms.Visibility.Collapsed

    def Close_Click(self, sender, args):
        self.Close()


class _CarnetListEntry(object):
    """Objet d'affichage d'un carnet persistant dans la liste WPF."""

    def __init__(self, publication_set, missing_count):
        self.publication_set = publication_set
        self.DisplayName = "{0} — {1}".format(
            publication_set.name,
            "ATTENTION : {0} manquant(s)".format(missing_count)
            if missing_count
            else "{0} feuille(s)".format(len(publication_set.items))
        )
