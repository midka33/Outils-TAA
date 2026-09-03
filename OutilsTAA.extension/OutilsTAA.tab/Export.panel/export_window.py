# -*- coding: utf-8 -*-
"""Fenêtre WPF principale du module Export."""

import os

from pyrevit import forms
from System.Windows import Visibility

from export_report_window import PublicationReportWindow
from carnet_sheets_window import CarnetSheetsWindow
from carnet_manager_window import CarnetManagerWindow


class PreviewRow(object):
    """Ligne d'aperçu affichée dans le DataGrid WPF."""
    def __init__(self, name, count, status="Prêt"):
        self.Name = name
        self.Count = count
        self.Status = status


class ExportWindow(forms.WPFWindow):
    """Interface principale de publication des carnets."""
    def __init__(self, controller, repository):
        self.controller = controller
        self.repository = repository
        self.selected_publication_sets = []
        self.session_carnets = []
        self.current_project_unique_ids = set()
        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._load_context()

    def _load_context(self):
        sheets = self.controller.export_service.get_sheets()
        self.current_project_unique_ids = set(
            sheet.UniqueId for sheet in sheets
            if sheet is not None and getattr(sheet, "UniqueId", None)
        )
        self._load_dwg_setups()
        self._refresh_persistent_carnets()
        self._update_selection_info()

    def _load_dwg_setups(self):
        try:
            setups = self.controller.publication_service.dwg_service.get_predefined_setups()
        except Exception:
            setups = []
        self.DwgSetupCombo.ItemsSource = [""] + list(setups)
        self.DwgSetupCombo.SelectedIndex = 0

    def _refresh_persistent_carnets(self):
        rows = []
        for publication_set in self.controller.list_persistent():
            # Un carnet persistant n'est affiché que s'il contient au moins
            # une feuille appartenant au document Revit actuellement ouvert.
            if not self._belongs_to_current_project(publication_set):
                continue
            resolution = self.controller.resolve_persistent(publication_set)
            rows.append(_CarnetListEntry(publication_set, resolution.missing_count))

        for publication_set in self.session_carnets:
            if self._belongs_to_current_project(publication_set):
                rows.append(_CarnetListEntry(publication_set, 0, persistent=False))

        self.PersistentCarnetsList.ItemsSource = rows
        self._restore_checked_carnets()

    def _belongs_to_current_project(self, publication_set):
        """Vérifie qu'un carnet contient une feuille du document actif."""
        if publication_set is None:
            return False
        return any(
            item is not None and item.unique_id in self.current_project_unique_ids
            for item in (publication_set.items or [])
        )

    def _restore_checked_carnets(self):
        selected_ids = set(
            carnet.id for carnet in self.selected_publication_sets if carnet is not None
        )
        for index in range(self.PersistentCarnetsList.Items.Count):
            entry = self.PersistentCarnetsList.Items[index]
            entry.IsSelected = entry.publication_set.id in selected_ids
        self._sync_selection_from_grid(refresh_preview=False)

    def OpenCarnetManager_Click(self, sender, args):
        manager = CarnetManagerWindow(self.controller, owner=self)
        manager.ShowDialog()
        if manager.result:
            # Les carnets paramétriques et manuels persistants sont déjà
            # présents dans le repository : ne pas les ajouter une seconde fois
            # dans la collection de session.
            for carnet in manager.result:
                if not carnet.persistent:
                    self.session_carnets.append(carnet)
            self._refresh_persistent_carnets()

    def CarnetCheckChanged(self, sender, args):
        self._sync_selection_from_grid()

    def _sync_selection_from_grid(self, refresh_preview=True):
        self.selected_publication_sets = [
            self.PersistentCarnetsList.Items[index].publication_set
            for index in range(self.PersistentCarnetsList.Items.Count)
            if self.PersistentCarnetsList.Items[index].IsSelected
        ]
        if refresh_preview:
            self._show_selected_preview()
        self._update_selection_info()

    def _show_selected_preview(self):
        rows = []
        missing_total = 0
        for publication_set in self.selected_publication_sets:
            if publication_set.persistent:
                resolution = self.controller.resolve_persistent(publication_set)
                items = resolution.items
                missing_total += resolution.missing_count
            else:
                items = publication_set.items
            rows.append(PreviewRow(publication_set.name, len(items)))
        self.PreviewGrid.ItemsSource = rows
        if missing_total:
            self.MissingInfo.Visibility = Visibility.Visible
            self.MissingInfo.Text = (
                "ATTENTION : {0} élément(s) sont introuvables dans le document courant. "
                "Ils ne seront pas publiés."
            ).format(missing_total)
        else:
            self.MissingInfo.Visibility = Visibility.Collapsed

    def _update_selection_info(self):
        sheet_total = 0
        for carnet in self.selected_publication_sets:
            if carnet.persistent:
                try:
                    sheet_total += len(self.controller.resolve_persistent(carnet).items)
                except Exception:
                    sheet_total += len(carnet.items)
            else:
                sheet_total += len(carnet.items)
        self.CarnetsSelectionInfo.Text = (
            "{0} carnet(s) sélectionné(s) • {1} feuille(s) publiable(s).".format(
                len(self.selected_publication_sets), sheet_total
            ) if self.selected_publication_sets else "Cochez les carnets à publier."
        )

    def SelectAllCarnets_Click(self, sender, args):
        for index in range(self.PersistentCarnetsList.Items.Count):
            self.PersistentCarnetsList.Items[index].IsSelected = True
        self._sync_selection_from_grid()

    def UnselectAllCarnets_Click(self, sender, args):
        for index in range(self.PersistentCarnetsList.Items.Count):
            self.PersistentCarnetsList.Items[index].IsSelected = False
        self._sync_selection_from_grid()

    def ConsultCarnet_Click(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is None:
            forms.alert("Sélectionnez un carnet à consulter.", title="Export")
            return
        self._open_carnet_contents(entry.publication_set)

    def Carnet_MouseDoubleClick(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is not None:
            self._open_carnet_contents(entry.publication_set)

    def _open_carnet_contents(self, publication_set):
        if publication_set.persistent:
            resolution = self.controller.resolve_persistent(publication_set)
            resolved = _ResolvedCarnetView(publication_set.name, resolution.items)
        else:
            resolved = publication_set
        CarnetSheetsWindow(resolved, owner=self).ShowDialog()

    def _publish_one(self, publication_set, output_directory, export_pdf,
                     export_dwg, pdf_combined, dwg_combined, setup_name,
                     true_color):
        return self.controller.publish(
            publication_set, output_directory, export_pdf=export_pdf,
            export_dwg=export_dwg, pdf_combined=pdf_combined,
            dwg_combined=dwg_combined, dwg_setup_name=setup_name,
            dwg_true_color=true_color
        )

    def Publish_Click(self, sender, args):
        if not self.selected_publication_sets:
            forms.alert("Cochez au moins un carnet dans la liste.", title="Publication")
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

        all_results, all_errors, all_warnings = [], [], []
        all_success = True
        for publication_set in self.selected_publication_sets:
            try:
                result = self._publish_one(
                    publication_set, output_directory.strip(), export_pdf,
                    export_dwg, pdf_combined, dwg_combined, setup_name, true_color
                )
            except Exception as exc:
                result = {"success": False, "carnet": publication_set.name,
                          "results": [], "errors": [str(exc)], "warnings": []}
            for item_result in result.get("results", []):
                item_result = dict(item_result)
                item_result["carnet"] = publication_set.name
                all_results.append(item_result)
            for error in result.get("errors", []):
                all_errors.append("{0} : {1}".format(publication_set.name, error))
            for warning in result.get("warnings", []):
                all_warnings.append("{0} : {1}".format(publication_set.name, warning))
            if not result.get("success"):
                all_success = False

        report = {
            "success": all_success,
            "carnet": ("{0} carnet(s)".format(len(self.selected_publication_sets))
                        if len(self.selected_publication_sets) > 1
                        else self.selected_publication_sets[0].name),
            "results": all_results, "errors": all_errors,
            "warnings": all_warnings, "output_directory": output_directory.strip()
        }
        PublicationReportWindow(report, owner=self).ShowDialog()

    def BrowseOutput_Click(self, sender, args):
        folder = forms.pick_folder(title="Choisir le dossier de publication")
        if folder:
            self.OutputDirectoryTextBox.Text = folder

    def DeleteCarnet_Click(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is None:
            return
        publication_set = entry.publication_set
        if not publication_set.persistent:
            self.session_carnets = [c for c in self.session_carnets if c.id != publication_set.id]
        else:
            confirmed = forms.alert(
                "Supprimer le carnet « {0} » ?".format(publication_set.name),
                title="Export", yes=True, no=True
            )
            if not confirmed:
                return
            self.repository.delete(publication_set.id)
        self.selected_publication_sets = [
            c for c in self.selected_publication_sets if c.id != publication_set.id
        ]
        self._refresh_persistent_carnets()
        self._show_selected_preview()

    def Close_Click(self, sender, args):
        self.Close()


class _CarnetListEntry(object):
    """Objet d'affichage d'un carnet persistant ou de session."""
    def __init__(self, publication_set, missing_count, persistent=True):
        self.publication_set = publication_set
        self.IsSelected = False
        self.Name = publication_set.name
        self.Count = len(publication_set.items)
        if missing_count:
            self.Status = "{0} manquant(s)".format(missing_count)
        elif not persistent:
            self.Status = "Session"
        else:
            self.Status = "Disponible"


class _ResolvedCarnetView(object):
    """Vue minimale utilisée pour afficher un carnet résolu."""
    def __init__(self, name, items):
        self.name = name
        self.items = list(items or [])
