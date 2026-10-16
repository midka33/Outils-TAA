# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Interface finale Étape 09 — création batch des plans de vente."""

import os
import time

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

    UI_BUILD = "stage09-rc2"

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
        self._template_preview_path = None
        self._multilevel_mode = "sheet_per_level"
        self._multilevel_template_info = None
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
        self._multilevel_template_info = None
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
            template_mode = self.controller.detect_multilevel_template_mode(
                choice.unique_id
            )
            self._multilevel_template_info = template_mode
            self._multilevel_mode = str(
                template_mode.get("mode", "sheet_per_level")
            )
        except Exception as error:
            self.TemplateDetailsText.Text = (
                "Modèle non exploitable : {}"
            ).format(str(error) or repr(error))
            self.TemplatePreviewTitle.Text = choice.label
            self._show_sheet_preview(None, None)
            self._refresh_creation_state()
            return

        self.TemplatePreviewTitle.Text = (
            inspection.template_sheet_label
        )
        self._export_and_show_sheet_preview(choice, inspection)
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
        if self._multilevel_template_info is not None:
            self.TemplateDetailsText.Text += (
                "\nMulti-niveaux : {}"
            ).format(
                self._multilevel_template_info.get(
                    "summary",
                    "comportement automatique",
                )
            )
            if hasattr(self, "MultiLevelInfoText"):
                self.MultiLevelInfoText.Text = (
                    self._multilevel_template_info.get(
                        "summary",
                        "Comportement multi-niveaux détecté automatiquement.",
                    )
                )

        if inspection.warnings:
            self.StatusText.Text = (
                "Modèle analysé avec {} avertissement(s)."
            ).format(len(inspection.warnings))
        else:
            self.StatusText.Text = "Feuille modèle prête."

        self._refresh_creation_state()

    def TemplatePreviewOverlay_SizeChanged(self, sender, args):
        if self._template_inspection is not None:
            self._render_preview_overlays()

    def _export_and_show_sheet_preview(self, choice, inspection):
        import tempfile

        try:
            base_name = "OutilsTAA_PDV_preview_{}".format(
                abs(hash(str(choice.unique_id or "")))
            )
            output_base = os.path.join(
                tempfile.gettempdir(),
                base_name,
            )
            image_path = self.controller.export_sheet_preview(
                choice.unique_id,
                output_base,
            )
            self._template_preview_path = image_path
            self._show_sheet_preview(image_path, inspection)
        except Exception as error:
            self._template_preview_path = None
            self._show_sheet_preview(None, inspection)
            self.StatusText.Text = (
                "Feuille analysée, mais aperçu image indisponible : {}"
            ).format(str(error) or repr(error))

    def _show_sheet_preview(self, image_path, inspection):
        from System.Windows import Visibility

        preview_placeholder = getattr(
            self,
            "TemplatePreviewPlaceholder",
            None,
        )
        bitmap = self._load_bitmap(image_path)
        if bitmap is None:
            if hasattr(self, "TemplatePreviewImage"):
                self.TemplatePreviewImage.Source = None
            if preview_placeholder is not None:
                preview_placeholder.Visibility = Visibility.Visible
            self._clear_preview_overlays()
            return

        self.TemplatePreviewImage.Source = bitmap
        if preview_placeholder is not None:
            preview_placeholder.Visibility = Visibility.Collapsed
        self._render_preview_overlays()

    @staticmethod
    def _load_bitmap(image_path):
        if not image_path or not os.path.exists(image_path):
            return None
        try:
            from System import Uri, UriKind
            from System.Windows.Media.Imaging import (
                BitmapCacheOption,
                BitmapImage,
            )

            bitmap = BitmapImage()
            bitmap.BeginInit()
            bitmap.CacheOption = BitmapCacheOption.OnLoad
            bitmap.UriSource = Uri(
                os.path.abspath(image_path),
                UriKind.Absolute,
            )
            bitmap.EndInit()
            bitmap.Freeze()
            return bitmap
        except Exception:
            return None

    def _clear_preview_overlays(self):
        for name in (
            "TemplatePreviewOverlay",
        ):
            canvas = getattr(self, name, None)
            if canvas is None:
                continue
            try:
                canvas.Children.Clear()
            except Exception:
                pass

    def _render_preview_overlays(self):
        inspection = self._template_inspection
        if (
            inspection is None
            or not getattr(inspection, "preview_bounds", None)
            or not getattr(inspection, "preview_items", None)
        ):
            self._clear_preview_overlays()
            return

        self._render_overlay_canvas(
            self.TemplatePreviewOverlay,
            inspection,
            compact=True,
        )

    def _render_overlay_canvas(self, canvas, inspection, compact=False):
        from System.Windows import FontWeights, Thickness, TextWrapping
        from System.Windows.Controls import Canvas, TextBlock
        from System.Windows.Media import Brushes
        from System.Windows.Shapes import Rectangle

        try:
            canvas.Children.Clear()
            width = float(canvas.ActualWidth or 0.0)
            height = float(canvas.ActualHeight or 0.0)
        except Exception:
            return
        if width <= 10.0 or height <= 10.0:
            return

        bounds = inspection.preview_bounds
        if len(bounds) != 4:
            return
        min_x, min_y, max_x, max_y = [float(v) for v in bounds]
        sheet_width = max_x - min_x
        sheet_height = max_y - min_y
        if sheet_width <= 0.0 or sheet_height <= 0.0:
            return

        scale = min(width / sheet_width, height / sheet_height)
        draw_w = sheet_width * scale
        draw_h = sheet_height * scale
        origin_x = (width - draw_w) / 2.0
        origin_y = (height - draw_h) / 2.0

        labels = {
            "main_view": "Vue logement 1",
            "main_view_extra": "Vue logement 2",
            "location_view": "Repérage",
            "schedule": "Nomenclature",
        }

        for item in inspection.preview_items or []:
            kind = str(item.get("kind", "") or "")
            if kind not in labels:
                continue

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

            rect = Rectangle()
            rect.Width = item_w
            rect.Height = item_h
            rect.StrokeThickness = 3.0 if not compact else 2.0
            rect.Stroke = (
                Brushes.OrangeRed
                if kind in ("main_view", "main_view_extra")
                else (
                    Brushes.DarkOrange
                    if kind == "location_view"
                    else Brushes.DodgerBlue
                )
            )
            rect.Fill = Brushes.Transparent
            Canvas.SetLeft(rect, left)
            Canvas.SetTop(rect, top)
            canvas.Children.Add(rect)

            if compact and item_w < 45.0:
                continue

            label = TextBlock()
            label.Text = labels[kind]
            label.FontSize = 11.0
            label.FontWeight = FontWeights.SemiBold
            label.Foreground = rect.Stroke
            label.Background = Brushes.White
            label.Padding = Thickness(3, 1, 3, 1)
            label.TextWrapping = TextWrapping.NoWrap
            Canvas.SetLeft(label, left + 3.0)
            Canvas.SetTop(label, max(0.0, top - 20.0))
            canvas.Children.Add(label)

    def _selected_sheet_template(self):
        item = self.SheetTemplateCombo.SelectedItem
        return (
            getattr(item, "Candidate", None)
            if item is not None
            else None
        )

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

        self.CreationInfoText.Text = (
            "{} logement(s) sélectionné(s).".format(count)
        )

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
        if self._multilevel_mode == "sheet_per_level":
            processable = list(single_level)
            for housing in multilevel:
                processable.extend(
                    self.controller.split_housing_by_level(housing)
                )
        else:
            # Modèle avec 2 vues logement : une feuille unique multi-niveaux.
            processable = list(single_level) + list(multilevel)

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
        batch_started_at = time.time()

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
                    is_multilevel = len(
                        getattr(housing, "level_names", []) or []
                    ) > 1
                    if (
                        is_multilevel
                        and self._multilevel_mode == "one_sheet"
                    ):
                        result = self.controller.generate_multilevel_one_sheet(
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
                    else:
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

        finally:
            self._busy = False
            self._refresh_creation_state()

        elapsed_seconds = max(0.0, time.time() - batch_started_at)

        self.StatusText.Text = (
            "{} plan(s) créé(s), {} ignoré(s), {} échec(s) — {}."
        ).format(
            len(created),
            len(skipped),
            len(failures),
            self._format_duration(elapsed_seconds),
        )

        if self._settings.get("detailed_report", True):
            self._show_batch_report(
                created,
                skipped,
                failures,
                warnings,
                elapsed_seconds,
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

    @staticmethod
    def _format_duration(seconds):
        total = int(round(float(seconds or 0.0)))
        minutes, secs = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return "{} h {:02d} min {:02d} s".format(
                hours,
                minutes,
                secs,
            )
        if minutes:
            return "{} min {:02d} s".format(minutes, secs)
        return "{} s".format(secs)

    def _show_batch_report(
        self,
        created,
        skipped,
        failures,
        warnings,
        elapsed_seconds,
    ):
        lines = [
            "Création terminée.",
            "",
            "Plans créés : {}".format(len(created)),
            "Logements ignorés : {}".format(len(skipped)),
            "Échecs : {}".format(len(failures)),
            "Durée totale : {}".format(
                self._format_duration(elapsed_seconds)
            ),
        ]

        if created:
            lines.append(
                "Temps moyen / plan créé : {}".format(
                    self._format_duration(
                        float(elapsed_seconds) / float(len(created))
                    )
                )
            )

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
