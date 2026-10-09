# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Création du plan de repérage et surbrillance du logement."""

from common.transaction import RevitTransaction
from plans_vente.location_naming import location_view_name
from plans_vente.placement_contract import PlacementRole, placement_artifact


class LocationTemplateCandidate(object):
    def __init__(self, unique_id, name):
        self.unique_id = unique_id or ""
        self.name = name or ""

    @property
    def label(self):
        return self.name


class FilledRegionTypeCandidate(object):
    def __init__(self, unique_id, name):
        self.unique_id = unique_id or ""
        self.name = name or ""

    @property
    def label(self):
        return self.name


class LocationPlanResult(object):
    def __init__(
        self,
        housing_key,
        view_name,
        view_unique_id,
        region_count,
        template_name,
        fill_type_name,
        placement=None,
    ):
        self.housing_key = housing_key or ""
        self.view_name = view_name or ""
        self.view_unique_id = view_unique_id or ""
        self.region_count = int(region_count or 0)
        self.template_name = template_name or ""
        self.fill_type_name = fill_type_name or ""
        self.placement = placement


class LocationPlanService(object):
    """Service Revit de l'Étape 04B."""

    def __init__(self, document, plan_view_service, crop_geometry_service):
        if document is None:
            raise ValueError("Document Revit manquant.")
        if plan_view_service is None:
            raise ValueError("Service de vues plan manquant.")
        if crop_geometry_service is None:
            raise ValueError("Service de géométrie de contour manquant.")
        self.document = document
        self.plan_view_service = plan_view_service
        self.crop_geometry_service = crop_geometry_service

    def source_views_for_housing(self, housing):
        level_name = self._single_level_name(housing)
        return [
            item for item in self.plan_view_service.list_primary_floor_plans(level_name)
            if not item.name.startswith("PDV_")
        ]

    def list_view_templates(self):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewPlan, ViewType

        result = []
        for view in (FilteredElementCollector(self.document)
                     .OfClass(ViewPlan)
                     .WhereElementIsNotElementType()
                     .ToElements()):
            if not bool(getattr(view, "IsTemplate", False)):
                continue
            if getattr(view, "ViewType", None) != ViewType.FloorPlan:
                continue
            result.append(LocationTemplateCandidate(
                unique_id=str(getattr(view, "UniqueId", "") or ""),
                name=str(getattr(view, "Name", "") or ""),
            ))
        return sorted(result, key=lambda item: item.name.lower())

    def list_filled_region_types(self):
        from Autodesk.Revit.DB import FilledRegionType, FilteredElementCollector

        result = []
        for region_type in (FilteredElementCollector(self.document)
                            .OfClass(FilledRegionType)
                            .WhereElementIsElementType()
                            .ToElements()):
            result.append(FilledRegionTypeCandidate(
                unique_id=str(getattr(region_type, "UniqueId", "") or ""),
                name=self._element_type_name(region_type),
            ))
        return sorted(result, key=lambda item: item.name.lower())

    def create_location_plan(
        self,
        housing,
        source_view_unique_id,
        filled_region_type_unique_id,
        template_unique_id=None,
        target_scale=None,
        crop_reference_view_unique_id=None,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        level_name = self._single_level_name(housing)
        source_view = self._get_element(source_view_unique_id, "Sélectionnez une vue source de repérage.")
        region_type = self._get_element(filled_region_type_unique_id, "Sélectionnez un type de zone remplie.")
        template = self.document.GetElement(template_unique_id) if template_unique_id else None
        crop_reference_view = (
            self.document.GetElement(crop_reference_view_unique_id)
            if crop_reference_view_unique_id
            else None
        )

        source_level = getattr(getattr(source_view, "GenLevel", None), "Name", None)
        if source_level != level_name:
            raise ValueError("La vue source de repérage doit appartenir au niveau « {} ».".format(level_name))

        from Autodesk.Revit.DB import ViewDuplicateOption
        if not source_view.CanViewBeDuplicated(ViewDuplicateOption.Duplicate):
            raise ValueError("Cette vue ne peut pas être dupliquée pour le plan de repérage.")

        target_name = location_view_name(housing.key)
        self._ensure_view_name_available(target_name)

        highlight_result = self.crop_geometry_service.build_optimized_crop(
            housing.room_unique_ids,
            source_view,
            0.0,
        )
        if not highlight_result.mode.startswith("Contour optimisé"):
            raise ValueError(
                "Le contour global du logement n'a pas pu être construit de façon "
                "fiable pour le repérage. Aucun rectangle de secours n'est utilisé "
                "pour éviter de surligner une zone extérieure au logement."
            )

        if template is not None:
            if not bool(getattr(template, "IsTemplate", False)):
                raise ValueError("Le gabarit de repérage sélectionné n'est plus un gabarit de vue.")

        created_view = None
        region_count = 0
        with RevitTransaction(self.document, "Plans de vente - Repérage {}".format(housing.key)):
            new_view_id = source_view.Duplicate(ViewDuplicateOption.Duplicate)
            created_view = self.document.GetElement(new_view_id)
            if created_view is None:
                raise RuntimeError("Revit n'a pas retourné la vue de repérage dupliquée.")
            created_view.Name = target_name

            if template is not None:
                try:
                    created_view.ViewTemplateId = template.Id
                except Exception as error:
                    raise ValueError("Impossible d'appliquer le gabarit de repérage : {}".format(error))

            if target_scale:
                try:
                    created_view.Scale = int(target_scale)
                except Exception as error:
                    raise ValueError(
                        "Impossible d'appliquer l'échelle 1:{} au repérage : {}.".format(
                            int(target_scale),
                            error,
                        )
                    )

                if int(getattr(created_view, "Scale", 0) or 0) != int(target_scale):
                    raise ValueError(
                        "Revit n'a pas conservé l'échelle 1:{} sur le repérage.".format(
                            int(target_scale)
                        )
                    )

            if crop_reference_view is not None:
                self._copy_crop_from_reference(
                    crop_reference_view,
                    created_view,
                )

            self._create_global_filled_region(
                created_view,
                region_type,
                highlight_result.curve_loop,
            )
            region_count = 1

        return LocationPlanResult(
            housing_key=housing.key,
            view_name=created_view.Name,
            view_unique_id=str(getattr(created_view, "UniqueId", "") or ""),
            region_count=region_count,
            template_name=str(getattr(template, "Name", "") or "") if template is not None else "Conserver la vue source",
            fill_type_name=self._element_type_name(region_type),
            placement=placement_artifact(
                housing.key,
                PlacementRole.LOCATION_VIEW,
                str(getattr(created_view, "UniqueId", "") or ""),
                created_view.Name,
            ),
        )

    def _copy_crop_from_reference(self, reference_view, target_view):
        """Copie le crop 2D du repérage modèle sur le niveau cible.

        Le contour est conservé en XY et translaté uniquement suivant Z entre
        les niveaux. Cela reproduit la même fenêtre de repérage sur tous les
        étages au lieu d'hériter du crop de la vue source choisie.
        """
        from Autodesk.Revit.DB import CurveLoop, Transform, XYZ

        try:
            reference_manager = reference_view.GetCropRegionShapeManager()
            target_manager = target_view.GetCropRegionShapeManager()
        except Exception as error:
            raise ValueError(
                "Impossible d'accéder au crop du repérage modèle : {}.".format(
                    error
                )
            )

        try:
            reference_loops = list(reference_manager.GetCropShape() or [])
        except Exception as error:
            raise ValueError(
                "Impossible de lire le crop du repérage modèle : {}.".format(
                    error
                )
            )

        if not reference_loops:
            raise ValueError(
                "Le repérage modèle ne fournit aucun contour de crop exploitable."
            )

        delta_z = self._view_level_elevation(target_view) - self._view_level_elevation(
            reference_view
        )
        translation = Transform.CreateTranslation(
            XYZ(0.0, 0.0, float(delta_z))
        )

        transformed = []
        for source_loop in reference_loops:
            target_loop = CurveLoop()
            for curve in source_loop:
                target_loop.Append(
                    curve.CreateTransformed(translation)
                )
            transformed.append(target_loop)

        # SetCropShape ne prend qu'une boucle. Les crops scindés sont ramenés
        # au rectangle de référence via CropBox ci-dessous.
        applied_shape = False
        if len(transformed) == 1:
            try:
                if target_manager.IsCropRegionShapeValid(transformed[0]):
                    target_manager.SetCropShape(transformed[0])
                    applied_shape = True
            except Exception:
                applied_shape = False

        if not applied_shape:
            self._copy_rectangular_crop_box(
                reference_view,
                target_view,
            )

        try:
            target_view.CropBoxActive = bool(
                getattr(reference_view, "CropBoxActive", True)
            )
        except Exception:
            try:
                target_view.CropBoxActive = True
            except Exception:
                pass

        try:
            target_view.CropBoxVisible = bool(
                getattr(reference_view, "CropBoxVisible", False)
            )
        except Exception:
            pass

        self._copy_annotation_crop(
            reference_manager,
            target_manager,
        )

    def _copy_rectangular_crop_box(self, reference_view, target_view):
        """Copie les limites locales XY du CropBox en conservant le plan cible."""
        from Autodesk.Revit.DB import BoundingBoxXYZ

        reference_box = getattr(reference_view, "CropBox", None)
        target_box = getattr(target_view, "CropBox", None)
        if reference_box is None or target_box is None:
            raise ValueError(
                "Impossible de recopier le rectangle de crop du repérage modèle."
            )

        copied = BoundingBoxXYZ()
        copied.Transform = target_box.Transform
        copied.Min = self._xyz(
            reference_box.Min.X,
            reference_box.Min.Y,
            target_box.Min.Z,
        )
        copied.Max = self._xyz(
            reference_box.Max.X,
            reference_box.Max.Y,
            target_box.Max.Z,
        )
        target_view.CropBox = copied

    @staticmethod
    def _copy_annotation_crop(reference_manager, target_manager):
        try:
            if not bool(reference_manager.CanHaveAnnotationCrop):
                return
            if not bool(target_manager.CanHaveAnnotationCrop):
                return
        except Exception:
            return

        try:
            target_manager.AnnotationCropActive = bool(
                reference_manager.AnnotationCropActive
            )
        except Exception:
            pass

        for property_name in (
            "LeftAnnotationCropOffset",
            "RightAnnotationCropOffset",
            "TopAnnotationCropOffset",
            "BottomAnnotationCropOffset",
        ):
            try:
                setattr(
                    target_manager,
                    property_name,
                    getattr(reference_manager, property_name),
                )
            except Exception:
                pass

    @staticmethod
    def _view_level_elevation(view):
        level = getattr(view, "GenLevel", None)
        try:
            return float(getattr(level, "Elevation", 0.0) or 0.0)
        except Exception:
            return 0.0

    @staticmethod
    def _xyz(x_value, y_value, z_value):
        from Autodesk.Revit.DB import XYZ
        return XYZ(
            float(x_value),
            float(y_value),
            float(z_value),
        )

    def _create_global_filled_region(self, view, region_type, curve_loop):
        from Autodesk.Revit.DB import CurveLoop, FilledRegion
        from System.Collections.Generic import List

        if curve_loop is None or curve_loop.IsOpen():
            raise ValueError("Le contour global du logement n'est pas fermé.")

        boundaries = List[CurveLoop]()
        boundaries.Add(curve_loop)
        try:
            return FilledRegion.Create(
                self.document,
                region_type.Id,
                view.Id,
                boundaries,
            )
        except Exception as error:
            raise ValueError(
                "Revit n'a pas pu créer la zone remplie globale de repérage : {}".format(
                    error
                )
            )

    def _ensure_view_name_available(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, View
        for view in (FilteredElementCollector(self.document)
                     .OfClass(View)
                     .WhereElementIsNotElementType()
                     .ToElements()):
            if str(getattr(view, "Name", "") or "") == target_name:
                raise ValueError(
                    "La vue « {} » existe déjà. La mise à jour sera traitée à l'Étape 08.".format(target_name))

    def _get_element(self, unique_id, error_message):
        if not unique_id:
            raise ValueError(error_message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(error_message)
        return element

    @staticmethod
    def _element_type_name(element_type):
        """Lit le nom d'un ElementType de façon fiable sous IronPython/pyRevit."""
        if element_type is None:
            return ""

        try:
            from Autodesk.Revit.DB import Element
            value = Element.Name.GetValue(element_type)
            if value:
                return str(value)
        except Exception:
            pass

        try:
            value = getattr(element_type, "Name", None)
            if value:
                return str(value)
        except Exception:
            pass

        return ""

    @staticmethod
    def _single_level_name(housing):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        levels = list(getattr(housing, "level_names", []) or [])
        if len(levels) != 1:
            raise ValueError(
                "Le prototype de repérage V1 attend un logement sur un seul niveau. Niveaux détectés : {}.".format(
                    ", ".join(levels) if levels else "aucun"))
        return levels[0]
