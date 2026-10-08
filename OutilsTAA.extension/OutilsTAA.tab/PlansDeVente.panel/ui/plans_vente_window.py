# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre principale — détection des logements et prototype de contour optimisé."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary
from plans_vente.defaults import preferred_housing_parameter_index
from plans_vente.view_grouping import normalize_scale


class ParameterChoice(object):
    def __init__(self, label, descriptor):
        self.label = label
        self.descriptor = descriptor


class HousingRow(object):
    def __init__(self, housing):
        self.Housing = housing
        self.Key = housing.key
        self.RoomCount = housing.room_count
        self.Levels = housing.levels_label


class SourceViewChoice(object):
    def __init__(self, candidate):
        self.Candidate = candidate
        self.Label = candidate.label


class ScheduleTemplateChoice(object):
    def __init__(self, candidate):
        self.Candidate = candidate
        self.Label = candidate.label


class LocationChoice(object):
    def __init__(self, candidate, label=None):
        self.Candidate = candidate
        self.Label = label if label is not None else candidate.label


class RoomTagChoice(object):
    def __init__(self, candidate):
        self.Candidate = candidate
        self.Label = candidate.label


class DimensionChoice(object):
    def __init__(self, candidate):
        self.Candidate = candidate
        self.Label = candidate.label


class PlansVenteWindow(forms.WPFWindow):

    def __init__(self, controller):
        self.controller = controller
        self._choices = []
        self._housing_rows = []
        self._source_view_choices = []
        self._schedule_choices = []
        self._location_source_choices = []
        self._location_template_choices = []
        self._location_fill_choices = []
        self._room_tag_type_choices = []
        self._room_tag_type_labels = []
        self._room_tag_type_error = ""
        self._room_tag_view_choices = []
        self._dimension_type_choices = []
        self._dimension_type_labels = []
        self._dimension_type_error = ""
        self._dimension_view_choices = []
        self._active_descriptor = None

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(current_dir, "plans_vente.xaml")
        forms.WPFWindow.__init__(self, xaml_path)

        self._load_theme()
        self._load_context()
        self._clear_prototype_selection()
        self._clear_schedule_selection()
        self._load_location_static_choices()
        self._clear_location_source_selection()
        self._clear_room_tag_views()
        self._load_room_tag_types()
        self._clear_dimension_views()
        self._load_dimension_types()

    def _load_theme(self):
        panel_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        extension_dir = os.path.abspath(os.path.join(panel_dir, "..", ".."))
        resource_path = os.path.join(
            extension_dir,
            "resources",
            "ui",
            "taa_theme.xaml",
        )
        load_resource_dictionary(self, resource_path)

    def _load_context(self):
        self.StatusText.Text = "Lecture des pièces et paramètres..."
        context = self.controller.load_context()

        self.RoomCountText.Text = "{} pièce(s) détectée(s).".format(
            context.rooms_count
        )

        self._choices = self._build_parameter_choices(context.parameters)
        self.HousingParameterCombo.ItemsSource = self._choices

        if self._choices:
            self.HousingParameterCombo.SelectedIndex = preferred_housing_parameter_index(
                context.parameters
            )
            self.AnalyzeButton.IsEnabled = True
            self.StatusText.Text = (
                "Choisissez le paramètre logement puis lancez l'analyse."
            )
        else:
            self.AnalyzeButton.IsEnabled = False
            self.StatusText.Text = (
                "Aucun paramètre texte n'a été trouvé sur les pièces."
            )

    @staticmethod
    def _build_parameter_choices(descriptors):
        descriptors = list(descriptors or [])
        name_counts = {}

        for descriptor in descriptors:
            key = descriptor.name.lower()
            name_counts[key] = name_counts.get(key, 0) + 1

        choices = []
        for descriptor in descriptors:
            label = descriptor.name
            if name_counts.get(descriptor.name.lower(), 0) > 1:
                label = "{} [{}]".format(
                    descriptor.name,
                    PlansVenteWindow._identity_label(descriptor),
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

    def Analyze_Click(self, sender, args):
        item = self.HousingParameterCombo.SelectedItem
        descriptor = getattr(item, "descriptor", None) if item is not None else None

        self.AnalyzeButton.IsEnabled = False
        try:
            result = self.controller.analyze(descriptor)
            self._housing_rows = [
                HousingRow(housing)
                for housing in result.housings
            ]
            self.HousingGrid.ItemsSource = self._housing_rows

            self.HousingCountText.Text = "{} logement(s) détecté(s).".format(
                result.housing_count
            )

            message = "{} logement(s), {} pièce(s) affectée(s).".format(
                result.housing_count,
                result.room_count,
            )
            if result.empty_value_count:
                message += " {} pièce(s) sans valeur ignorée(s).".format(
                    result.empty_value_count
                )
            if result.skipped_room_count:
                message += " {} élément(s) invalide(s) ignoré(s).".format(
                    result.skipped_room_count
                )

            self.StatusText.Text = message
            self._active_descriptor = descriptor
            self._clear_prototype_selection()
            self._load_schedule_templates(descriptor)
        except Exception as error:
            self.StatusText.Text = "Erreur pendant l'analyse."
            forms.alert(
                str(error),
                title="Plans de vente — Analyse",
                warn_icon=True,
            )
        finally:
            self.AnalyzeButton.IsEnabled = bool(self._choices)

    def HousingSelectionChanged(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        if housing is None:
            self._clear_prototype_selection()
            self._clear_room_tag_views()
            self._clear_dimension_views()
            self._update_schedule_button_state()
            return

        try:
            candidates = self.controller.source_views_for_housing(housing)
        except Exception as error:
            self._clear_prototype_selection()
            self.PrototypeInfoText.Text = str(error)
            return

        self._source_view_choices = [
            SourceViewChoice(candidate)
            for candidate in candidates
        ]
        self.SourceViewCombo.ItemsSource = self._source_view_choices
        self.SourceViewCombo.SelectedIndex = 0 if self._source_view_choices else -1
        self.CreatePrototypeButton.IsEnabled = bool(self._source_view_choices)

        if self._source_view_choices:
            self.PrototypeInfoText.Text = (
                "Le prototype crée une vue dépendante avec un contour optimisé "
                "à partir de l'union réelle des pièces du logement."
            )
        else:
            self.PrototypeInfoText.Text = (
                "Aucune vue plan principale duplicable n'a été trouvée pour ce niveau."
            )

        self._load_location_sources(housing)
        self._load_room_tag_views(housing)
        self._load_dimension_views(housing)
        self._update_schedule_button_state()

    def SourceViewChanged(self, sender, args):
        item = self.SourceViewCombo.SelectedItem
        candidate = getattr(item, "Candidate", None) if item is not None else None
        if candidate is not None and getattr(candidate, "scale", 0):
            self.TargetScaleTextBox.Text = str(candidate.scale)

        self.CreatePrototypeButton.IsEnabled = (
            self.HousingGrid.SelectedItem is not None
            and candidate is not None
        )

    def CreatePrototype_Click(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        view_item = self.SourceViewCombo.SelectedItem
        candidate = (
            getattr(view_item, "Candidate", None)
            if view_item is not None
            else None
        )

        if housing is None or candidate is None:
            forms.alert(
                "Sélectionnez un logement et une vue source.",
                title="Plans de vente — Prototype",
                warn_icon=True,
            )
            return

        try:
            margin_mm = self._parse_margin_mm()
            target_scale = self._parse_target_scale()
        except Exception as error:
            forms.alert(
                str(error),
                title="Plans de vente — Prototype",
                warn_icon=True,
            )
            return

        confirmed = forms.alert(
            (
                "Créer une vue dépendante réelle pour le logement « {} » ?\n\n"
                "Vue source : {}\n"
                "Échelle : 1:{}\n"
                "Marge de crop : {} mm\n"
                "Contour : union optimisée des pièces\n\n"
                "Cette opération ajoute une vue au projet mais ne supprime rien."
            ).format(
                housing.key,
                candidate.name,
                target_scale,
                self._format_number(margin_mm),
            ),
            title="Plans de vente — Prototype contour optimisé",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self.CreatePrototypeButton.IsEnabled = False
        try:
            result = self.controller.create_view_prototype(
                housing=housing,
                source_view_unique_id=candidate.unique_id,
                margin_mm=margin_mm,
                target_scale=target_scale,
            )

            status = "Vue prototype créée : {} — {}.".format(
                result.view_name,
                result.crop_mode,
            )
            if result.warning:
                status += " Avertissement : {}".format(result.warning)
            self.StatusText.Text = status

            message = (
                "Vue dépendante créée avec succès.\n\n"
                "Nom : {}\n"
                "Vue source : {}\n"
                "Vue principale PDV : {}\n"
                "Échelle : 1:{}\n"
                "Logement : {}\n"
                "Crop : {}"
            ).format(
                result.view_name,
                result.source_view_name,
                result.master_view_name,
                result.target_scale,
                result.housing_key,
                result.crop_mode,
            )

            if result.warning:
                message += "\n\nAvertissement :\n{}".format(result.warning)

            self._load_room_tag_views(housing)
            self._load_dimension_views(housing)

            forms.alert(
                message,
                title="Plans de vente — Prototype",
                warn_icon=bool(result.warning),
            )
        except Exception as error:
            self.StatusText.Text = "Échec du prototype contour optimisé."
            forms.alert(
                str(error),
                title="Plans de vente — Prototype",
                warn_icon=True,
            )
        finally:
            self.CreatePrototypeButton.IsEnabled = (
                self.HousingGrid.SelectedItem is not None
                and self.SourceViewCombo.SelectedItem is not None
            )

    def ScheduleTemplateChanged(self, sender, args):
        self._update_schedule_button_state()

    def CreateSchedules_Click(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        interior_item = self.InteriorScheduleCombo.SelectedItem
        exterior_item = self.ExteriorScheduleCombo.SelectedItem
        interior = getattr(interior_item, "Candidate", None) if interior_item is not None else None
        exterior = getattr(exterior_item, "Candidate", None) if exterior_item is not None else None

        if housing is None or self._active_descriptor is None or interior is None or exterior is None:
            forms.alert(
                "Sélectionnez un logement et les deux nomenclatures modèles.",
                title="Plans de vente — Nomenclatures",
                warn_icon=True,
            )
            return

        confirmed = forms.alert(
            (
                "Créer les nomenclatures du logement « {} » ?\n\n"
                "Intérieure : {}\n"
                "Extérieure : {}\n"
                "Filtre logement : {} = {}\n\n"
                "Les nomenclatures modèles ne seront pas modifiées."
            ).format(
                housing.key, interior.name, exterior.name,
                self._active_descriptor.name, housing.key,
            ),
            title="Plans de vente — Nomenclatures",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self.CreateSchedulesButton.IsEnabled = False
        try:
            result = self.controller.create_schedule_prototype(
                housing=housing,
                descriptor=self._active_descriptor,
                interior_template_unique_id=interior.unique_id,
                exterior_template_unique_id=exterior.unique_id,
            )
            self.StatusText.Text = "Nomenclatures créées pour {} : {} / {}.".format(
                result.housing_key, result.interior_name, result.exterior_name)
            forms.alert(
                (
                    "Nomenclatures créées avec succès.\n\n"
                    "Intérieure : {}\n"
                    "Extérieure : {}\n"
                    "Logement : {}"
                ).format(result.interior_name, result.exterior_name, result.housing_key),
                title="Plans de vente — Nomenclatures",
            )
        except Exception as error:
            self.StatusText.Text = "Échec de la création des nomenclatures."
            forms.alert(str(error), title="Plans de vente — Nomenclatures", warn_icon=True)
        finally:
            self._update_schedule_button_state()

    def _load_schedule_templates(self, descriptor):
        self._clear_schedule_selection()
        if descriptor is None:
            return
        try:
            candidates = self.controller.schedule_templates(descriptor)
        except Exception as error:
            self.ScheduleInfoText.Text = str(error)
            return

        self._schedule_choices = [ScheduleTemplateChoice(candidate) for candidate in candidates]
        self.InteriorScheduleCombo.ItemsSource = self._schedule_choices
        self.ExteriorScheduleCombo.ItemsSource = self._schedule_choices
        if self._schedule_choices:
            self.InteriorScheduleCombo.SelectedIndex = 0
            self.ExteriorScheduleCombo.SelectedIndex = 1 if len(self._schedule_choices) > 1 else 0
            self.ScheduleInfoText.Text = "{} nomenclature(s) compatible(s) avec « {} ».".format(
                len(self._schedule_choices), descriptor.name)
        else:
            self.ScheduleInfoText.Text = "Aucune nomenclature modèle contenant le champ « {} ».".format(
                descriptor.name)
        self._update_schedule_button_state()

    def _clear_schedule_selection(self):
        self._schedule_choices = []
        self.InteriorScheduleCombo.ItemsSource = []
        self.ExteriorScheduleCombo.ItemsSource = []
        self.InteriorScheduleCombo.SelectedIndex = -1
        self.ExteriorScheduleCombo.SelectedIndex = -1
        self.CreateSchedulesButton.IsEnabled = False
        self.ScheduleInfoText.Text = "Analysez les logements pour charger les nomenclatures compatibles."

    def _update_schedule_button_state(self):
        self.CreateSchedulesButton.IsEnabled = (
            self.HousingGrid.SelectedItem is not None
            and self._active_descriptor is not None
            and self.InteriorScheduleCombo.SelectedItem is not None
            and self.ExteriorScheduleCombo.SelectedItem is not None
        )

    def LocationChoiceChanged(self, sender, args):
        self._update_location_button_state()

    def CreateLocationPlan_Click(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        source_item = self.LocationSourceCombo.SelectedItem
        fill_item = self.LocationFillTypeCombo.SelectedItem
        template_item = self.LocationTemplateCombo.SelectedItem
        source = getattr(source_item, "Candidate", None) if source_item is not None else None
        fill_type = getattr(fill_item, "Candidate", None) if fill_item is not None else None
        template = getattr(template_item, "Candidate", None) if template_item is not None else None

        if housing is None or source is None or fill_type is None:
            forms.alert(
                "Sélectionnez un logement, une vue source et un type de zone remplie.",
                title="Plans de vente — Repérage",
                warn_icon=True,
            )
            return

        template_name = template.name if template is not None else "Conserver la vue source"
        confirmed = forms.alert(
            (
                "Créer le plan de repérage du logement « {} » ?\n\n"
                "Vue source : {}\n"
                "Gabarit : {}\n"
                "Surbrillance : {}\n\n"
                "La vue source ne sera pas modifiée."
            ).format(housing.key, source.name, template_name, fill_type.name),
            title="Plans de vente — Plan de repérage",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self.CreateLocationPlanButton.IsEnabled = False
        try:
            result = self.controller.create_location_plan_prototype(
                housing=housing,
                source_view_unique_id=source.unique_id,
                filled_region_type_unique_id=fill_type.unique_id,
                template_unique_id=template.unique_id if template is not None else None,
            )
            self.StatusText.Text = "Plan de repérage créé : {}.".format(result.view_name)
            forms.alert(
                (
                    "Plan de repérage créé avec succès.\n\n"
                    "Vue : {}\n"
                    "Logement : {}\n"
                    "Zones remplies : {}\n"
                    "Gabarit : {}\n"
                    "Type : {}"
                ).format(
                    result.view_name, result.housing_key, result.region_count,
                    result.template_name, result.fill_type_name,
                ),
                title="Plans de vente — Plan de repérage",
            )
        except Exception as error:
            self.StatusText.Text = "Échec de la création du plan de repérage."
            forms.alert(str(error), title="Plans de vente — Repérage", warn_icon=True)
        finally:
            self._update_location_button_state()

    def _load_location_static_choices(self):
        try:
            templates = self.controller.location_view_templates()
            fill_types = self.controller.location_filled_region_types()
        except Exception as error:
            self.LocationInfoText.Text = str(error)
            return

        self._location_template_choices = [LocationChoice(None, "Conserver la vue source")] + [
            LocationChoice(candidate) for candidate in templates
        ]
        self._location_fill_choices = [LocationChoice(candidate) for candidate in fill_types]
        self.LocationTemplateCombo.ItemsSource = self._location_template_choices
        self.LocationFillTypeCombo.ItemsSource = self._location_fill_choices
        self.LocationTemplateCombo.SelectedIndex = 0
        self.LocationFillTypeCombo.SelectedIndex = 0 if self._location_fill_choices else -1

    def _load_location_sources(self, housing):
        self._clear_location_source_selection()
        if housing is None:
            return
        try:
            candidates = self.controller.location_source_views_for_housing(housing)
        except Exception as error:
            self.LocationInfoText.Text = str(error)
            return

        self._location_source_choices = [LocationChoice(candidate) for candidate in candidates]
        self.LocationSourceCombo.ItemsSource = self._location_source_choices
        self.LocationSourceCombo.SelectedIndex = 0 if self._location_source_choices else -1
        if self._location_source_choices:
            self.LocationInfoText.Text = "La vue source sera dupliquée ; le logement sera surligné par zone remplie."
        else:
            self.LocationInfoText.Text = "Aucune vue plan source disponible pour ce niveau."
        self._update_location_button_state()

    def _clear_location_source_selection(self):
        self._location_source_choices = []
        self.LocationSourceCombo.ItemsSource = []
        self.LocationSourceCombo.SelectedIndex = -1
        self.CreateLocationPlanButton.IsEnabled = False
        self.LocationInfoText.Text = "Sélectionnez un logement pour préparer le plan de repérage."

    def _update_location_button_state(self):
        self.CreateLocationPlanButton.IsEnabled = (
            self.HousingGrid.SelectedItem is not None
            and self.LocationSourceCombo.SelectedItem is not None
            and self.LocationFillTypeCombo.SelectedItem is not None
        )


    def RoomTagChoiceChanged(self, sender, args):
        self._update_room_tag_button_state()

    def CreateRoomTags_Click(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        view_item = self.RoomTagViewCombo.SelectedItem
        type_index = int(self.RoomTagTypeCombo.SelectedIndex)
        view = getattr(view_item, "Candidate", None) if view_item is not None else None
        type_item = (
            self._room_tag_type_choices[type_index]
            if 0 <= type_index < len(self._room_tag_type_choices)
            else None
        )
        tag_type = getattr(type_item, "Candidate", None) if type_item is not None else None

        if housing is None or view is None or tag_type is None:
            forms.alert(
                "Sélectionnez un logement, une vue logement et un type d'étiquette.",
                title="Plans de vente — Étiquettes",
                warn_icon=True,
            )
            return

        confirmed = forms.alert(
            (
                "Créer les étiquettes des pièces du logement « {} » ?\n\n"
                "Vue logement : {}\n"
                "Type d'étiquette : {}\n"
                "Pièces : {}\n\n"
                "Le moteur cherche d'abord une position entièrement dans la "
                "pièce et sans collision avec les autres étiquettes."
            ).format(
                housing.key,
                view.name,
                tag_type.label,
                housing.room_count,
            ),
            title="Plans de vente — Étiquettes",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self.CreateRoomTagsButton.IsEnabled = False
        try:
            result = self.controller.create_room_tags(
                housing=housing,
                target_view_unique_id=view.unique_id,
                room_tag_type_unique_id=tag_type.unique_id,
            )

            status = "{} étiquette(s) créée(s) dans {}.".format(
                result.created_count,
                result.view_name,
            )
            if result.adjusted_count:
                status += " {} repositionnée(s).".format(result.adjusted_count)
            if result.warning_count:
                status += " {} avertissement(s).".format(result.warning_count)
            self.StatusText.Text = status

            message = (
                "Étiquettes créées avec succès.\n\n"
                "Logement : {}\n"
                "Vue : {}\n"
                "Type : {}\n"
                "Créées : {}\n"
                "Repositionnées : {}"
            ).format(
                result.housing_key,
                result.view_name,
                result.tag_type_name,
                result.created_count,
                result.adjusted_count,
            )
            if result.warnings:
                message += "\n\nAvertissements :\n- " + "\n- ".join(result.warnings)

            forms.alert(
                message,
                title="Plans de vente — Étiquettes",
                warn_icon=bool(result.warnings),
            )
        except Exception as error:
            self.StatusText.Text = "Échec de la création des étiquettes."
            build_id = self.controller.room_tag_build_id()
            forms.alert(
                "{}\n\nMoteur étiquettes : {}".format(error, build_id),
                title="Plans de vente — Étiquettes",
                warn_icon=True,
            )
        finally:
            self._update_room_tag_button_state()

    def _load_room_tag_types(self):
        self._room_tag_type_error = ""
        try:
            candidates = self.controller.room_tag_types()
        except Exception as error:
            self._room_tag_type_error = str(error) or repr(error)
            candidates = []

        self._room_tag_type_choices = [
            RoomTagChoice(candidate)
            for candidate in candidates
        ]
        self._room_tag_type_labels = []
        for index, choice in enumerate(self._room_tag_type_choices):
            label = str(getattr(choice, "Label", "") or "").strip()
            if not label:
                label = "Type d'étiquette #{}".format(index + 1)
            self._room_tag_type_labels.append(label)

        # Ne pas utiliser DisplayMemberPath ici : sous IronPython/WPF, le
        # binding sur les wrappers Python peut rendre des lignes présentes mais
        # visuellement vides. Des chaînes simples sont affichées directement.
        self.RoomTagTypeCombo.ItemsSource = self._room_tag_type_labels
        self.RoomTagTypeCombo.SelectedIndex = (
            0 if self._room_tag_type_labels else -1
        )

        if self._room_tag_type_error:
            self.RoomTagInfoText.Text = (
                "Erreur de collecte des types d'étiquettes : {}"
            ).format(self._room_tag_type_error)
        elif self._room_tag_type_labels:
            self.RoomTagInfoText.Text = "{} type(s) d'étiquette chargé(s).".format(
                len(self._room_tag_type_labels)
            )
        else:
            self.RoomTagInfoText.Text = (
                "0 type d'étiquette de pièce trouvé dans le document hôte. "
                "Chargez au moins une famille de catégorie Étiquette de pièce."
            )

    def _load_room_tag_views(self, housing):
        self._clear_room_tag_views()
        if housing is None:
            return

        try:
            candidates = self.controller.room_tag_target_views(housing)
        except Exception as error:
            self.RoomTagInfoText.Text = str(error)
            return

        self._room_tag_view_choices = [
            RoomTagChoice(candidate)
            for candidate in candidates
        ]
        self.RoomTagViewCombo.ItemsSource = self._room_tag_view_choices
        self.RoomTagViewCombo.SelectedIndex = (
            0 if self._room_tag_view_choices else -1
        )

        if self._room_tag_type_error:
            self.RoomTagInfoText.Text = (
                "Erreur de collecte des types d'étiquettes : {}"
            ).format(self._room_tag_type_error)
        elif self._room_tag_view_choices:
            self.RoomTagInfoText.Text = (
                "Le centre est testé dans la pièce ; le moteur recherche une "
                "position alternative en cas de débordement ou collision. "
                "{} type(s) d'étiquette disponible(s)."
            ).format(len(self._room_tag_type_labels))
        else:
            self.RoomTagInfoText.Text = (
                "Créez d'abord une vue logement avec le contour optimisé. "
                "{} type(s) d'étiquette disponible(s)."
            ).format(len(self._room_tag_type_labels))
        self._update_room_tag_button_state()

    def _clear_room_tag_views(self):
        self._room_tag_view_choices = []
        self.RoomTagViewCombo.ItemsSource = []
        self.RoomTagViewCombo.SelectedIndex = -1
        self.CreateRoomTagsButton.IsEnabled = False
        self.RoomTagInfoText.Text = (
            "Sélectionnez un logement puis une vue logement générée."
        )

    def _update_room_tag_button_state(self):
        self.CreateRoomTagsButton.IsEnabled = (
            self.HousingGrid.SelectedItem is not None
            and self.RoomTagViewCombo.SelectedItem is not None
            and self.RoomTagTypeCombo.SelectedItem is not None
        )

    def DimensionChoiceChanged(self, sender, args):
        self._update_dimension_button_state()

    def CreateDimensions_Click(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        view_item = self.DimensionViewCombo.SelectedItem
        type_index = int(self.DimensionTypeCombo.SelectedIndex)
        view = getattr(view_item, "Candidate", None) if view_item is not None else None
        type_item = (
            self._dimension_type_choices[type_index]
            if 0 <= type_index < len(self._dimension_type_choices)
            else None
        )
        dimension_type = (
            getattr(type_item, "Candidate", None)
            if type_item is not None
            else None
        )

        if housing is None or view is None or dimension_type is None:
            forms.alert(
                "Sélectionnez un logement, une vue logement et un type de cote.",
                title="Plans de vente — Cotations",
                warn_icon=True,
            )
            return

        confirmed = forms.alert(
            (
                "Créer deux cotations principales par pièce pour le logement « {} » ?\n\n"
                "Vue logement : {}\n"
                "Type de cote : {}\n"
                "Pièces : {}\n\n"
                "Prototype 06F : placement intérieur avec évitement des étiquettes, "
                "équipements et autres cotes. Les conflits résiduels sont signalés. "
                "Les références aux faces de murs et aux bords de sols sont conservées. "
                "Une pièce atypique ne bloque plus les autres."
            ).format(
                housing.key,
                view.name,
                dimension_type.label,
                housing.room_count,
            ),
            title="Plans de vente — Cotations",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self.CreateDimensionsButton.IsEnabled = False
        try:
            result = self.controller.create_dimensions(
                housing=housing,
                target_view_unique_id=view.unique_id,
                dimension_type_unique_id=dimension_type.unique_id,
            )

            status = (
                "{} cote(s) créée(s) dans {} — {} pièce(s) complètes, "
                "{} partielle(s), {} ignorée(s)."
            ).format(
                result.created_count,
                result.view_name,
                result.full_room_count,
                result.partial_room_count,
                result.skipped_room_count,
            )
            if result.warning_count:
                status += " {} avertissement(s).".format(result.warning_count)
            self.StatusText.Text = status

            message = (
                "Cotations créées avec succès.\n\n"
                "Logement : {}\n"
                "Vue : {}\n"
                "Type : {}\n"
                "Pièces analysées : {}\n"
                "Cotes créées : {}\n"
                "Pièces avec 2 cotes : {}\n"
                "Pièces avec 1 cote : {}\n"
                "Pièces sans cote : {}"
            ).format(
                result.housing_key,
                result.view_name,
                result.dimension_type_name,
                result.room_count,
                result.created_count,
                result.full_room_count,
                result.partial_room_count,
                result.skipped_room_count,
            )
            message += "\nMoteur cotations : {}".format(self.controller.dimension_build_id())
            if result.warnings:
                message += "\n\nAvertissements :\n- " + "\n- ".join(result.warnings)

            forms.alert(
                message,
                title="Plans de vente — Cotations",
                warn_icon=bool(result.warnings),
            )
        except Exception as error:
            self.StatusText.Text = "Échec de la création des cotations."
            message = "{}\n\nMoteur cotations : {}".format(
                str(error),
                self.controller.dimension_build_id(),
            )
            forms.alert(
                message,
                title="Plans de vente — Cotations",
                warn_icon=True,
            )
        finally:
            self._update_dimension_button_state()

    def _load_dimension_types(self):
        self._dimension_type_choices = []
        self._dimension_type_labels = []
        self._dimension_type_error = ""
        try:
            candidates = self.controller.dimension_types()
        except Exception as error:
            self._dimension_type_error = str(error) or repr(error)
            self.DimensionTypeCombo.ItemsSource = []
            self.DimensionTypeCombo.SelectedIndex = -1
            self.DimensionInfoText.Text = (
                "Erreur de collecte des types de cote : {}"
            ).format(self._dimension_type_error)
            self._update_dimension_button_state()
            return

        self._dimension_type_choices = [
            DimensionChoice(candidate)
            for candidate in candidates
        ]
        self._dimension_type_labels = [
            choice.Label or "Type de cote #{}".format(index + 1)
            for index, choice in enumerate(self._dimension_type_choices)
        ]
        self.DimensionTypeCombo.ItemsSource = self._dimension_type_labels
        self.DimensionTypeCombo.SelectedIndex = (
            0 if self._dimension_type_labels else -1
        )

        if self._dimension_type_labels:
            self.DimensionInfoText.Text = (
                "{} type(s) de cote linéaire chargé(s)."
            ).format(len(self._dimension_type_labels))
        else:
            self.DimensionInfoText.Text = (
                "0 type de cote linéaire trouvé dans le document hôte."
            )
        self._update_dimension_button_state()

    def _load_dimension_views(self, housing):
        self._clear_dimension_views()
        if housing is None:
            return

        try:
            candidates = self.controller.dimension_target_views(housing)
        except Exception as error:
            self.DimensionInfoText.Text = str(error)
            return

        self._dimension_view_choices = [
            DimensionChoice(candidate)
            for candidate in candidates
        ]
        self.DimensionViewCombo.ItemsSource = self._dimension_view_choices
        self.DimensionViewCombo.SelectedIndex = (
            0 if self._dimension_view_choices else -1
        )

        if self._dimension_type_error:
            self.DimensionInfoText.Text = (
                "Erreur de collecte des types de cote : {}"
            ).format(self._dimension_type_error)
        elif self._dimension_view_choices:
            self.DimensionInfoText.Text = (
                "Prototype 06F : placement intérieur des cotes, étiquettes préservées, "
                "références aux faces et bords de sols conservées. "
                "{} type(s) disponible(s)."
            ).format(len(self._dimension_type_labels))
        else:
            self.DimensionInfoText.Text = (
                "Créez d'abord une vue logement avec le contour optimisé. "
                "{} type(s) de cote disponible(s)."
            ).format(len(self._dimension_type_labels))
        self._update_dimension_button_state()

    def _clear_dimension_views(self):
        self._dimension_view_choices = []
        self.DimensionViewCombo.ItemsSource = []
        self.DimensionViewCombo.SelectedIndex = -1
        self.CreateDimensionsButton.IsEnabled = False
        self.DimensionInfoText.Text = (
            "Sélectionnez un logement puis une vue logement générée."
        )

    def _update_dimension_button_state(self):
        self.CreateDimensionsButton.IsEnabled = (
            self.HousingGrid.SelectedItem is not None
            and self.DimensionViewCombo.SelectedItem is not None
            and self.DimensionTypeCombo.SelectedItem is not None
        )

    def _clear_prototype_selection(self):
        self._source_view_choices = []
        self.SourceViewCombo.ItemsSource = []
        self.SourceViewCombo.SelectedIndex = -1
        self.TargetScaleTextBox.Text = "50"
        self.CreatePrototypeButton.IsEnabled = False
        self.PrototypeInfoText.Text = (
            "Sélectionnez d'abord un logement dans le tableau."
        )

    def _parse_target_scale(self):
        raw = (self.TargetScaleTextBox.Text or "").strip()
        return normalize_scale(raw)

    def _parse_margin_mm(self):
        raw = (self.CropMarginTextBox.Text or "").strip().replace(",", ".")
        if not raw:
            raise ValueError("Saisissez une marge de crop.")
        try:
            value = float(raw)
        except Exception:
            raise ValueError("La marge de crop doit être un nombre.")
        if value < 0:
            raise ValueError("La marge de crop ne peut pas être négative.")
        return value

    @staticmethod
    def _format_number(value):
        if float(value).is_integer():
            return str(int(value))
        return str(value)

    def Close_Click(self, sender, args):
        self.Close()
