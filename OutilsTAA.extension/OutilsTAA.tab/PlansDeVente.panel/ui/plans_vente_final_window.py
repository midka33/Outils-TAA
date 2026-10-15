# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Interface finale Étape 09 — création batch des plans de vente."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary
from plans_vente.defaults import preferred_housing_parameter_index
from plans_vente.housing_filter import FILTER_OPERATORS
from plans_vente_advanced_window import PlansVenteAdvancedWindow


class ParameterChoice(object):
    def __init__(self, label, descriptor):
        self.label = label
        self.descriptor = descriptor


class FilterOperatorChoice(object):
    def __init__(self, key, label):
        self.key = key
        self.label = label

    def __str__(self):
        return self.label


class SheetTemplateChoice(object):
    def __init__(self, candidate):
        self.Candidate = candidate
        self.Label = candidate.label

    def __str__(self):
        return self.Label


class HousingRow(object):
    def __init__(self, housing):
        self.Housing = housing
        self.Key = housing.key
        self.RoomCount = housing.room_count
        self.LevelCount = len(housing.level_names or [])
        self.Levels = housing.levels_label


class PlansVenteFinalWindow(forms.WPFWindow):

    UI_BUILD = "stage09b1-sheet-per-level-v3"

    def __init__(self, controller):
        self.controller = controller
        self._parameter_choices = []
        self._active_descriptor = None
        self._all_housings = []
        self._filtered_housings = []
        self._housing_rows = []
        self._sheet_template_choices = []
        self._sheet_templates_loaded = False
        self._template_inspection = None
        self._multilevel_mode = "sheet_per_level"
        self._busy = False
        self._settings = {
            "skip_existing": True,
            "crop_margin_mm": 500.0,
            "auto_scale": True,
            "allowed_scales": [50, 75, 100, 125, 150],
            "detailed_report": True,
            "log_warnings": True,
            "building_parameter_name": "",
            "typology_parameter_name": "",
        }

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(
            current_dir,
            "plans_vente_final.xaml",
        )
        forms.WPFWindow.__init__(self, xaml_path)

        self._load_theme()
        self._load_filter_operators()
        self._load_context()

    def _load_theme(self):
        panel_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        extension_dir = os.path.abspath(
            os.path.join(panel_dir, "..", "..")
        )
        resource_path = os.path.join(
            extension_dir,
            "resources",
            "ui",
            "taa_theme.xaml",
        )
        load_resource_dictionary(self, resource_path)

    def _load_filter_operators(self):
        choices = [
            FilterOperatorChoice(key, label)
            for key, label in FILTER_OPERATORS
        ]
        self.FilterOperatorCombo.ItemsSource = choices
        self.FilterOperatorCombo.SelectedIndex = 0 if choices else -1

    def _load_context(self):
        self.StatusText.Text = "Lecture des pièces et paramètres..."
        try:
            context = self.controller.load_context()
        except Exception as error:
            self.StatusText.Text = "Impossible de lire les pièces."
            forms.alert(
                str(error),
                title="Plans de vente",
                warn_icon=True,
            )
            self.CreateBatchButton.IsEnabled = False
            return

        self._parameter_choices = self._build_parameter_choices(
            context.parameters
        )
        self.FilterParameterCombo.ItemsSource = self._parameter_choices

        if not self._parameter_choices:
            self.StatusText.Text = (
                "Aucun paramètre texte n'a été trouvé sur les pièces."
            )
            self.CreateBatchButton.IsEnabled = False
            return

        preferred_index = preferred_housing_parameter_index(
            context.parameters
        )
        if preferred_index < 0 or preferred_index >= len(
            self._parameter_choices
        ):
            preferred_index = 0

        self._active_descriptor = (
            self._parameter_choices[preferred_index].descriptor
        )
        self.FilterParameterCombo.SelectedIndex = preferred_index

        self._analyze_housings()
        self._load_sheet_templates()

    @staticmethod
    def _build_parameter_choices(descriptors):
        descriptors = list(descriptors or [])
        counts = {}
        for descriptor in descriptors:
            key = descriptor.name.lower()
            counts[key] = counts.get(key, 0) + 1

        choices = []
        for descriptor in descriptors:
            label = descriptor.name
            if counts.get(descriptor.name.lower(), 0) > 1:
                label = "{} [{}]".format(
                    descriptor.name,
                    PlansVenteFinalWindow._identity_label(descriptor),
                )
            choices.append(ParameterChoice(label, descriptor))
        return choices

    @staticmethod
    def _identity_label(descriptor):
        kind = getattr(descriptor, "identity_kind", "")
        if kind == "SHARED_GUID":
            return "partagé"
        if kind == "BUILT_IN":
            return "Revit"
        if kind == "DEFINITION":
            return "projet"
        return "nom"

    def _analyze_housings(self):
        if self._active_descriptor is None:
            return

        self.StatusText.Text = (
            "Analyse des logements avec « {} »...".format(
                self._active_descriptor.name
            )
        )
        try:
            result = self.controller.analyze(
                self._active_descriptor
            )
        except Exception as error:
            self._all_housings = []
            self._filtered_housings = []
            self._refresh_scope()
            forms.alert(
                str(error),
                title="Plans de vente — Analyse",
                warn_icon=True,
            )
            return

        self._all_housings = list(result.housings or [])
        self._refresh_scope()

        message = "{} logement(s), {} pièce(s) affectée(s).".format(
            result.housing_count,
            result.room_count,
        )
        if result.empty_value_count:
            message += " {} pièce(s) sans identifiant ignorée(s).".format(
                result.empty_value_count
            )
        self.StatusText.Text = message

    def ScopeModeChanged(self, sender, args):
        if not hasattr(self, "FilterPanel"):
            return
        filtered = bool(
            getattr(self.FilteredHousingRadio, "IsChecked", False)
        )
        self.FilterPanel.IsEnabled = filtered
        self._refresh_scope()

    def FilterChoiceChanged(self, sender, args):
        if not hasattr(self, "FilterValueTextBox"):
            return
        operator = self._selected_filter_operator()
        no_value = operator in ("is_empty", "is_not_empty")
        self.FilterValueTextBox.IsEnabled = not no_value
        self._refresh_scope()

    def FilterValueChanged(self, sender, args):
        if not hasattr(self, "HousingGrid"):
            return
        self._refresh_scope()

    def _refresh_scope(self):
        housings = list(self._all_housings or [])
        filtered_mode = bool(
            getattr(self.FilteredHousingRadio, "IsChecked", False)
        )

        if filtered_mode and housings:
            item = self.FilterParameterCombo.SelectedItem
            descriptor = (
                getattr(item, "descriptor", None)
                if item is not None
                else None
            )
            operator = self._selected_filter_operator()
            expected = str(
                getattr(self.FilterValueTextBox, "Text", "") or ""
            )

            if descriptor is not None and operator:
                try:
                    housings = self.controller.filter_housings(
                        housings,
                        descriptor,
                        operator,
                        expected,
                    )
                except Exception as error:
                    housings = []
                    self.StatusText.Text = (
                        "Filtre invalide : {}"
                    ).format(str(error) or repr(error))

        self._filtered_housings = list(housings)
        self._housing_rows = [
            HousingRow(housing)
            for housing in self._filtered_housings
        ]
        self.HousingGrid.ItemsSource = self._housing_rows

        count = len(self._filtered_housings)
        total = len(self._all_housings)
        if filtered_mode:
            self.ScopeSummaryText.Text = (
                "{} logement(s) correspondant(s) seront traités."
            ).format(count)
        else:
            self.ScopeSummaryText.Text = (
                "{} logement(s) détecté(s) seront traités."
            ).format(count)

        self.HousingGridCaption.Text = (
            "Affichage de {} logement(s) sur {}"
        ).format(count, total)

        self._refresh_creation_state()

    def _selected_filter_operator(self):
        item = self.FilterOperatorCombo.SelectedItem
        return getattr(item, "key", "") if item is not None else ""

    def SheetTemplateDropDownOpened(self, sender, args):
        if not self._sheet_templates_loaded:
            self._load_sheet_templates()

    def _load_sheet_templates(self):
        try:
            candidates = self.controller.sheet_templates()
        except Exception as error:
            self._sheet_template_choices = []
            self.SheetTemplateCombo.ItemsSource = []
            self.TemplateDetailsText.Text = (
                "Erreur de lecture des feuilles : {}"
            ).format(str(error) or repr(error))
            return

        self._sheet_template_choices = [
            SheetTemplateChoice(candidate)
            for candidate in candidates
        ]
        self.SheetTemplateCombo.ItemsSource = (
            self._sheet_template_choices
        )
        self._sheet_templates_loaded = True

        self.SheetTemplateCombo.SelectedIndex = -1
        if self._sheet_template_choices:
            self.TemplateDetailsText.Text = (
                "Choisissez la feuille qui sert de modèle de plan de vente."
            )
            self.TemplatePreviewTitle.Text = (
                "Aucun modèle sélectionné"
            )
        else:
            self.TemplateDetailsText.Text = (
                "Aucune feuille modèle n'a été trouvée."
            )
        self._refresh_creation_state()

    def SheetTemplateChanged(self, sender, args):
        self._template_inspection = None
        choice = self._selected_sheet_template()
        if choice is None or self._active_descriptor is None:
            self.TemplateDetailsText.Text = (
                "Choisissez une feuille modèle."
            )
            self.TemplatePreviewTitle.Text = (
                "Aucun modèle sélectionné"
            )
            self._refresh_creation_state()
            return

        try:
            inspection = (
                self.controller.inspect_full_generation_template(
                    choice.unique_id,
                    self._active_descriptor,
                )
            )
            self._template_inspection = inspection
        except Exception as error:
            self.TemplateDetailsText.Text = (
                "Modèle non exploitable : {}"
            ).format(str(error) or repr(error))
            self.TemplatePreviewTitle.Text = choice.label
            self._render_template_preview(None)
            self._refresh_creation_state()
            return

        self.TemplatePreviewTitle.Text = (
            inspection.template_sheet_label
        )
        self._render_template_preview(inspection)
        self.TemplateDetailsText.Text = (
            "Échelle logement : 1:{}\n"
            "Nomenclatures : {}\n"
            "Repérage : {}\n"
            "Étiquette : {}\n"
            "Cote : {}"
        ).format(
            inspection.reference_scale or "?",
            len(inspection.schedule_names),
            inspection.location_view_name or "non détecté",
            inspection.room_tag_type_name or "non détecté",
            inspection.dimension_type_name or "non détecté",
        )

        if inspection.warnings:
            self.StatusText.Text = (
                "Modèle analysé avec {} avertissement(s)."
            ).format(len(inspection.warnings))
        else:
            self.StatusText.Text = "Feuille modèle prête."

        self._refresh_creation_state()

    def TemplatePreviewCanvas_SizeChanged(self, sender, args):
        if self._template_inspection is not None:
            self._render_template_preview(self._template_inspection)

    def _render_template_preview(self, inspection):
        from System.Windows import FontWeights, Thickness, TextWrapping, Visibility
        from System.Windows.Controls import Canvas, TextBlock
        from System.Windows.Media import Brushes
        from System.Windows.Shapes import Rectangle

        if not hasattr(self, "TemplatePreviewCanvas"):
            return

        canvas = self.TemplatePreviewCanvas
        try:
            canvas.Children.Clear()
        except Exception:
            return

        placeholder = getattr(self, "TemplatePreviewPlaceholder", None)
        if (
            inspection is None
            or not getattr(inspection, "preview_bounds", None)
            or not getattr(inspection, "preview_items", None)
        ):
            if placeholder is not None:
                placeholder.Visibility = Visibility.Visible
            return

        if placeholder is not None:
            placeholder.Visibility = Visibility.Collapsed

        try:
            width = float(canvas.ActualWidth or 0.0)
            height = float(canvas.ActualHeight or 0.0)
        except Exception:
            return
        if width <= 10.0 or height <= 10.0:
            return

        bounds = inspection.preview_bounds
        if len(bounds) != 4:
            return
        min_x, min_y, max_x, max_y = [float(value) for value in bounds]
        sheet_width = max_x - min_x
        sheet_height = max_y - min_y
        if sheet_width <= 0.0 or sheet_height <= 0.0:
            return

        margin = 12.0
        usable_w = max(1.0, width - (2.0 * margin))
        usable_h = max(1.0, height - (2.0 * margin))
        scale = min(usable_w / sheet_width, usable_h / sheet_height)
        draw_w = sheet_width * scale
        draw_h = sheet_height * scale
        origin_x = (width - draw_w) / 2.0
        origin_y = (height - draw_h) / 2.0

        sheet_rect = Rectangle()
        sheet_rect.Width = draw_w
        sheet_rect.Height = draw_h
        sheet_rect.Stroke = Brushes.LightGray
        sheet_rect.StrokeThickness = 1.0
        sheet_rect.Fill = Brushes.White
        Canvas.SetLeft(sheet_rect, origin_x)
        Canvas.SetTop(sheet_rect, origin_y)
        canvas.Children.Add(sheet_rect)

        for item in inspection.preview_items or []:
            try:
                item_min_x = float(item.get("min_x"))
                item_min_y = float(item.get("min_y"))
                item_max_x = float(item.get("max_x"))
                item_max_y = float(item.get("max_y"))
            except Exception:
                continue

            left = origin_x + ((item_min_x - min_x) * scale)
            top = origin_y + ((max_y - item_max_y) * scale)
            item_w = max(4.0, (item_max_x - item_min_x) * scale)
            item_h = max(4.0, (item_max_y - item_min_y) * scale)

            kind = str(item.get("kind", "") or "")

            rect = Rectangle()
            rect.Width = item_w
            rect.Height = item_h
            rect.StrokeThickness = 2.0 if kind in (
                "main_view",
                "location_view",
                "schedule",
            ) else 1.0
            if kind == "main_view":
                rect.Stroke = Brushes.OrangeRed
            elif kind == "location_view":
                rect.Stroke = Brushes.DarkOrange
            elif kind == "schedule":
                rect.Stroke = Brushes.SteelBlue
            else:
                rect.Stroke = Brushes.DarkGray
            rect.Fill = Brushes.Transparent
            Canvas.SetLeft(rect, left)
            Canvas.SetTop(rect, top)
            canvas.Children.Add(rect)

            label = TextBlock()
            label.Text = str(item.get("label", "") or "")
            label.FontSize = 10.0
            label.FontWeight = (
                FontWeights.SemiBold
                if kind in ("main_view", "location_view", "schedule")
                else FontWeights.Normal
            )
            label.TextWrapping = TextWrapping.Wrap
            label.Margin = Thickness(3)
            label.MaxWidth = max(1.0, item_w - 6.0)
            label.MaxHeight = max(1.0, item_h - 6.0)
            Canvas.SetLeft(label, left + 2.0)
            Canvas.SetTop(label, top + 2.0)
            canvas.Children.Add(label)

    def _selected_sheet_template(self):
        item = self.SheetTemplateCombo.SelectedItem
        return (
            getattr(item, "Candidate", None)
            if item is not None
            else None
        )

    def MultiLevelModeChanged(self, sender, args):
        required = (
            "MultiLevelOneSheetRadio",
            "MultiLevelOneSheetPerLevelRadio",
            "MultiLevelIgnoreRadio",
        )
        if not all(hasattr(self, name) for name in required):
            return

        if bool(self.MultiLevelIgnoreRadio.IsChecked):
            self._multilevel_mode = "ignore"
        elif bool(self.MultiLevelOneSheetPerLevelRadio.IsChecked):
            self._multilevel_mode = "sheet_per_level"
        else:
            self._multilevel_mode = "one_sheet"

        self._refresh_creation_state()

    def _refresh_creation_state(self):
        if not hasattr(self, "CreateBatchButton"):
            return

        count = len(self._filtered_housings or [])
        ready = (
            count > 0
            and self._active_descriptor is not None
            and self._selected_sheet_template() is not None
            and self._template_inspection is not None
            and not self._busy
        )
        self.CreateBatchButton.IsEnabled = bool(ready)

        if count == 1:
            self.CreateBatchButton.Content = (
                "Créer le plan de vente"
            )
        else:
            self.CreateBatchButton.Content = (
                "Créer les {} plans de vente".format(count)
            )

        multilevel = len(
            [
                housing
                for housing in self._filtered_housings
                if len(housing.level_names or []) > 1
            ]
        )
        details = "{} logement(s) sélectionné(s).".format(count)
        if multilevel:
            details += " {} multi-niveau(x).".format(multilevel)
            if self._multilevel_mode != "ignore":
                details += (
                    (
                        " Mode « une feuille par niveau » disponible en 09B.1."
                        if self._multilevel_mode == "sheet_per_level"
                        else " Mode multi-vues prévu en 09B.2."
                    )
                )
        self.CreationInfoText.Text = details

    def AdvancedOptions_Click(self, sender, args):
        dialog = PlansVenteAdvancedWindow(
            parameter_choices=self._parameter_choices,
            active_descriptor=self._active_descriptor,
            settings=self._settings,
            owner=self,
        )
        dialog.ShowDialog()
        if not dialog.accepted:
            return

        previous_key = getattr(
            self._active_descriptor,
            "identity_key",
            None,
        )
        new_descriptor = dialog.active_descriptor
        new_key = getattr(new_descriptor, "identity_key", None)

        self._settings = dict(dialog.settings)
        self._active_descriptor = new_descriptor

        new_index = self._parameter_choice_index(
            new_descriptor
        )
        if new_index >= 0:
            self.FilterParameterCombo.SelectedIndex = new_index

        if previous_key != new_key:
            self._analyze_housings()
            # Le contrat du modèle dépend du paramètre logement actif.
            self.SheetTemplateChanged(None, None)
        else:
            self._refresh_scope()
            self._refresh_creation_state()

        self.StatusText.Text = (
            "Options avancées enregistrées."
        )

    def _parameter_choice_index(self, descriptor):
        target = getattr(descriptor, "identity_key", None)
        for index, choice in enumerate(self._parameter_choices):
            candidate = getattr(choice, "descriptor", None)
            if candidate is descriptor:
                return index
            if (
                target
                and getattr(candidate, "identity_key", None) == target
            ):
                return index
        return -1

    def CreateBatch_Click(self, sender, args):
        if self._busy:
            return

        template = self._selected_sheet_template()
        if (
            template is None
            or self._active_descriptor is None
            or self._template_inspection is None
        ):
            forms.alert(
                "Choisissez une feuille modèle valide avant de lancer la création.",
                title="Plans de vente",
                warn_icon=True,
            )
            return

        selected = list(self._filtered_housings or [])
        if not selected:
            forms.alert(
                "Aucun logement ne correspond à la portée choisie.",
                title="Plans de vente",
                warn_icon=True,
            )
            return

        multilevel = [
            housing
            for housing in selected
            if len(housing.level_names or []) > 1
        ]
        single_level = [
            housing
            for housing in selected
            if len(housing.level_names or []) <= 1
        ]

        deferred_multilevel = []
        if self._multilevel_mode == "ignore":
            processable = single_level
            deferred_multilevel = multilevel
        elif self._multilevel_mode == "sheet_per_level":
            processable = list(single_level)
            for housing in multilevel:
                processable.extend(
                    self.controller.split_housing_by_level(housing)
                )
        else:
            # 09B.2 : une seule feuille comportant plusieurs vues logement.
            # Ce mode reste protégé tant que l'assemblage multi-viewports
            # n'est pas validé dans Revit.
            processable = single_level
            deferred_multilevel = multilevel

        if not processable and deferred_multilevel:
            forms.alert(
                (
                    "La sélection contient uniquement des logements multi-niveaux.\n\n"
                    "Le mode « une feuille par niveau » est disponible en 09B.1. "
                    "Le mode « une feuille par logement, une vue par niveau » "
                    "sera activé en 09B.2 après validation de l'assemblage "
                    "multi-viewports."
                ),
                title="Plans de vente — Étape 09B",
                warn_icon=True,
            )
            return

        existing_count = 0
        if self._settings.get("skip_existing", True):
            for housing in processable:
                try:
                    if self.controller.plan_exists(housing.key):
                        existing_count += 1
                except Exception:
                    pass

        message = (
            "Créer les plans de vente maintenant ?\n\n"
            "Feuille modèle : {}\n"
            "Logements correspondant au filtre : {}\n"
            "Sorties à générer : {}\n"
            "Plans existants à ignorer : {}\n"
            "Logements multi-niveaux reportés : {}\n\n"
            "Chaque logement est généré dans sa propre transaction complète. "
            "Un échec sur un logement n'interrompt pas les suivants."
        ).format(
            template.label,
            len(selected),
            len(processable),
            existing_count,
            len(deferred_multilevel),
        )

        confirmed = forms.alert(
            message,
            title="Plans de vente — Création par lot",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self._run_batch(
            processable,
            deferred_multilevel,
            template,
        )

    def _run_batch(
        self,
        processable,
        deferred_multilevel,
        template,
    ):
        self._busy = True
        self._refresh_creation_state()

        created = []
        skipped = []
        failures = []
        warnings = []

        total = len(processable)
        try:
            for index, housing in enumerate(processable, 1):
                self.StatusText.Text = (
                    "Création {}/{} — {}..."
                ).format(index, total, housing.key)

                if self._settings.get("skip_existing", True):
                    try:
                        if self.controller.plan_exists(housing.key):
                            skipped.append(
                                "{} : plan déjà existant".format(
                                    housing.key
                                )
                            )
                            continue
                    except Exception as error:
                        warnings.append(
                            "{} : contrôle doublon impossible ({})".format(
                                housing.key,
                                str(error) or repr(error),
                            )
                        )

                try:
                    result = self.controller.generate_full_plan(
                        housing=housing,
                        descriptor=self._active_descriptor,
                        template_sheet_unique_id=template.unique_id,
                        allowed_scales=self._settings.get(
                            "allowed_scales"
                        ),
                        crop_margin_mm=self._settings.get(
                            "crop_margin_mm",
                            500.0,
                        ),
                        auto_fit_main_view=self._settings.get(
                            "auto_scale",
                            True,
                        ),
                        building_parameter_name=self._settings.get(
                            "building_parameter_name",
                            "",
                        ),
                        typology_parameter_name=self._settings.get(
                            "typology_parameter_name",
                            "",
                        ),
                    )
                    created.append(result)
                    if self._settings.get("log_warnings", True):
                        for warning in result.warnings or []:
                            warnings.append(
                                "{} : {}".format(
                                    housing.key,
                                    warning,
                                )
                            )
                except Exception as error:
                    failures.append(
                        "{} : {}".format(
                            housing.key,
                            str(error) or repr(error),
                        )
                    )

            for housing in deferred_multilevel or []:
                if self._multilevel_mode == "ignore":
                    reason = "logement multi-niveaux ignoré par l'utilisateur"
                else:
                    reason = (
                        "logement multi-niveaux — mode une feuille / plusieurs vues "
                        "prévu en 09B.2"
                    )
                skipped.append(
                    "{} : {}".format(housing.key, reason)
                )
        finally:
            self._busy = False
            self._refresh_creation_state()

        self.StatusText.Text = (
            "{} plan(s) créé(s), {} ignoré(s), {} échec(s)."
        ).format(
            len(created),
            len(skipped),
            len(failures),
        )

        if self._settings.get("detailed_report", True):
            self._show_batch_report(
                created,
                skipped,
                failures,
                warnings,
            )
        elif failures:
            forms.alert(
                (
                    "{} plan(s) créé(s).\n"
                    "{} logement(s) en échec."
                ).format(
                    len(created),
                    len(failures),
                ),
                title="Plans de vente — Résultat du lot",
                warn_icon=True,
            )

    def _show_batch_report(
        self,
        created,
        skipped,
        failures,
        warnings,
    ):
        lines = [
            "Création terminée.",
            "",
            "Plans créés : {}".format(len(created)),
            "Logements ignorés : {}".format(len(skipped)),
            "Échecs : {}".format(len(failures)),
        ]

        if created:
            lines.append("")
            lines.append("Créés :")
            lines.extend(
                "- {}".format(result.housing_key)
                for result in created[:30]
            )

        if skipped:
            lines.append("")
            lines.append("Ignorés :")
            lines.extend(
                "- {}".format(value)
                for value in skipped[:20]
            )

        if failures:
            lines.append("")
            lines.append("Échecs :")
            lines.extend(
                "- {}".format(value)
                for value in failures[:20]
            )

        if warnings and self._settings.get(
            "log_warnings",
            True,
        ):
            lines.append("")
            lines.append("Avertissements :")
            lines.extend(
                "- {}".format(value)
                for value in warnings[:20]
            )
            if len(warnings) > 20:
                lines.append(
                    "- ... {} autre(s) avertissement(s)".format(
                        len(warnings) - 20
                    )
                )

        forms.alert(
            "\n".join(lines),
            title="Plans de vente — Rapport de création",
            warn_icon=bool(failures),
        )

    def Close_Click(self, sender, args):
        self.Close()
