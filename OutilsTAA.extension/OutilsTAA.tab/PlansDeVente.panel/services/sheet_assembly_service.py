# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Étape 07B — assemblage d'une feuille à partir d'une feuille modèle."""

SHEET_ASSEMBLY_BUILD = "stage07b-user-selected-sheet-v3"

from common.transaction import RevitTransaction
from plans_vente.location_naming import location_view_name
from plans_vente.schedule_naming import schedule_name
from plans_vente.sheet_layout import default_sheet_anchors
from plans_vente.sheet_template import required_placeholder_names


class TitleBlockTypeCandidate(object):
    def __init__(self, unique_id, family_name, type_name, element_id_value=None):
        self.unique_id = unique_id or ""
        self.family_name = family_name or ""
        self.type_name = type_name or ""
        self.element_id_value = element_id_value

    @property
    def label(self):
        if self.family_name and self.type_name:
            return "{} : {}".format(self.family_name, self.type_name)
        if self.type_name:
            return self.type_name
        if self.element_id_value is not None:
            return "Cartouche #{}".format(self.element_id_value)
        return "Cartouche"


class SheetTemplateCandidate(object):
    def __init__(
        self,
        unique_id,
        sheet_number,
        sheet_name,
        title_block_label,
    ):
        self.unique_id = unique_id or ""
        self.sheet_number = sheet_number or ""
        self.sheet_name = sheet_name or ""
        self.title_block_label = title_block_label or ""

    @property
    def label(self):
        prefix = self.sheet_number or "Sans numéro"
        if self.sheet_name:
            return "{} — {}".format(prefix, self.sheet_name)
        return prefix


class SheetTemplateInspection(object):
    def __init__(
        self,
        sheet_unique_id,
        sheet_label,
        is_valid,
        summary,
        title_block_label="",
    ):
        self.sheet_unique_id = sheet_unique_id or ""
        self.sheet_label = sheet_label or ""
        self.is_valid = bool(is_valid)
        self.summary = summary or ""
        self.title_block_label = title_block_label or ""


class _TemplateLayout(object):
    def __init__(
        self,
        sheet,
        title_block_type,
        points,
        viewport_type_ids,
    ):
        self.sheet = sheet
        self.title_block_type = title_block_type
        self.points = dict(points or {})
        self.viewport_type_ids = dict(viewport_type_ids or {})


class SheetAssemblyReadiness(object):
    def __init__(
        self,
        housing_key,
        main_view_name="",
        location_view_name_value="",
        interior_schedule_name="",
        exterior_schedule_name="",
        missing=None,
    ):
        self.housing_key = housing_key or ""
        self.main_view_name = main_view_name or ""
        self.location_view_name = location_view_name_value or ""
        self.interior_schedule_name = interior_schedule_name or ""
        self.exterior_schedule_name = exterior_schedule_name or ""
        self.missing = list(missing or [])

    @property
    def is_ready(self):
        return not self.missing

    @property
    def summary(self):
        if self.is_ready:
            return (
                "Prêt : vue logement, repérage et 2 nomenclatures détectés."
            )
        return "Manquant : {}.".format(", ".join(self.missing))


class SheetAssemblyResult(object):
    def __init__(
        self,
        housing_key,
        sheet_number,
        sheet_name,
        title_block_label,
        main_view_name,
        location_view_name_value,
        interior_schedule_name,
        exterior_schedule_name,
        template_sheet_label="",
    ):
        self.housing_key = housing_key or ""
        self.sheet_number = sheet_number or ""
        self.sheet_name = sheet_name or ""
        self.title_block_label = title_block_label or ""
        self.main_view_name = main_view_name or ""
        self.location_view_name = location_view_name_value or ""
        self.interior_schedule_name = interior_schedule_name or ""
        self.exterior_schedule_name = exterior_schedule_name or ""
        self.template_sheet_label = template_sheet_label or ""


class SheetAssemblyService(object):
    """Prototype 07B : reproduit la composition d'une feuille modèle."""

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self.build_id = SHEET_ASSEMBLY_BUILD

    def list_sheet_templates(self):
        """Liste toutes les feuilles ; l'utilisateur choisit explicitement.

        Aucun contenu de feuille n'est inspecté ici. La validation des vues,
        nomenclatures et du cartouche n'est faite qu'après sélection d'une
        feuille par l'utilisateur.
        """
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet

        result = []
        for sheet in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            result.append(
                SheetTemplateCandidate(
                    unique_id=str(getattr(sheet, "UniqueId", "") or ""),
                    sheet_number=str(
                        getattr(sheet, "SheetNumber", "") or ""
                    ),
                    sheet_name=str(getattr(sheet, "Name", "") or ""),
                    title_block_label="",
                )
            )

        return sorted(result, key=lambda item: item.label.lower())

    def inspect_sheet_template(self, template_sheet_unique_id):
        if not template_sheet_unique_id:
            return SheetTemplateInspection(
                "",
                "",
                False,
                "Sélectionnez une feuille modèle.",
            )

        sheet = self.document.GetElement(template_sheet_unique_id)
        if sheet is None:
            return SheetTemplateInspection(
                template_sheet_unique_id,
                "",
                False,
                "La feuille sélectionnée n'existe plus.",
            )

        sheet_label = "{} — {}".format(
            getattr(sheet, "SheetNumber", "") or "Sans numéro",
            getattr(sheet, "Name", "") or "",
        ).rstrip(" —")

        try:
            layout = self._template_layout(sheet)
        except Exception as error:
            return SheetTemplateInspection(
                template_sheet_unique_id,
                sheet_label,
                False,
                str(error) or repr(error),
            )

        title_block_label = "{} : {}".format(
            self._family_name(layout.title_block_type),
            self._element_type_name(layout.title_block_type),
        ).strip(" :")

        return SheetTemplateInspection(
            template_sheet_unique_id,
            sheet_label,
            True,
            "Feuille modèle valide : 2 vues, 2 nomenclatures et 1 cartouche détectés.",
            title_block_label=title_block_label,
        )

    def create_sheet_from_template(
        self,
        housing,
        template_sheet_unique_id,
        main_view_unique_id,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        template_sheet = self._get_element(
            template_sheet_unique_id,
            "Sélectionnez une feuille modèle valide.",
        )
        layout = self._template_layout(template_sheet)

        main_view = self._get_element(
            main_view_unique_id,
            "Sélectionnez une vue logement générée.",
        )

        readiness = self.readiness(housing, main_view_unique_id)
        if not readiness.is_ready:
            raise ValueError(
                "La feuille ne peut pas être assemblée. {}".format(
                    readiness.summary
                )
            )

        location = self._find_named_view(location_view_name(housing.key))
        interior = self._find_named_schedule(schedule_name(housing.key, "INT"))
        exterior = self._find_named_schedule(schedule_name(housing.key, "EXT"))

        self._validate_placeable_view(main_view, "vue logement")
        self._validate_placeable_view(location, "plan de repérage")
        self._validate_schedule_not_placed(interior, "nomenclature intérieure")
        self._validate_schedule_not_placed(exterior, "nomenclature extérieure")

        sheet_number = "PDV-{}".format(housing.key)
        sheet_name = "Plan de vente - {}".format(housing.key)
        self._ensure_sheet_identity_available(sheet_number, sheet_name)

        from Autodesk.Revit.DB import (
            ScheduleSheetInstance,
            ViewSheet,
            Viewport,
            XYZ,
        )

        sheet = None
        with RevitTransaction(
            self.document,
            "Plans de vente - Feuille {}".format(housing.key),
        ):
            sheet = ViewSheet.Create(
                self.document,
                layout.title_block_type.Id,
            )
            if sheet is None:
                raise RuntimeError("Revit n'a pas retourné la feuille créée.")

            sheet.SheetNumber = sheet_number
            sheet.Name = sheet_name

            main_point = layout.points["main_view"]
            location_point = layout.points["location_view"]
            interior_point = layout.points["interior_schedule"]
            exterior_point = layout.points["exterior_schedule"]

            main_viewport = Viewport.Create(
                self.document,
                sheet.Id,
                main_view.Id,
                XYZ(main_point[0], main_point[1], 0.0),
            )
            location_viewport = Viewport.Create(
                self.document,
                sheet.Id,
                location.Id,
                XYZ(location_point[0], location_point[1], 0.0),
            )

            self._apply_viewport_type(
                main_viewport,
                layout.viewport_type_ids.get("main_view"),
            )
            self._apply_viewport_type(
                location_viewport,
                layout.viewport_type_ids.get("location_view"),
            )

            ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                interior.Id,
                XYZ(interior_point[0], interior_point[1], 0.0),
            )
            ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                exterior.Id,
                XYZ(exterior_point[0], exterior_point[1], 0.0),
            )

        template_label = "{} — {}".format(
            getattr(template_sheet, "SheetNumber", "") or "Sans numéro",
            getattr(template_sheet, "Name", "") or "",
        ).rstrip(" —")

        return SheetAssemblyResult(
            housing_key=housing.key,
            sheet_number=sheet.SheetNumber,
            sheet_name=sheet.Name,
            title_block_label="{} : {}".format(
                self._family_name(layout.title_block_type),
                self._element_type_name(layout.title_block_type),
            ),
            main_view_name=str(getattr(main_view, "Name", "") or ""),
            location_view_name_value=str(getattr(location, "Name", "") or ""),
            interior_schedule_name=str(getattr(interior, "Name", "") or ""),
            exterior_schedule_name=str(getattr(exterior, "Name", "") or ""),
            template_sheet_label=template_label,
        )

    def list_title_block_types(self):
        from Autodesk.Revit.DB import (
            BuiltInCategory,
            FamilySymbol,
            FilteredElementCollector,
        )

        result = []
        symbols = (
            FilteredElementCollector(self.document)
            .OfClass(FamilySymbol)
            .OfCategory(BuiltInCategory.OST_TitleBlocks)
            .WhereElementIsElementType()
            .ToElements()
        )

        for symbol in symbols:
            result.append(
                TitleBlockTypeCandidate(
                    unique_id=str(getattr(symbol, "UniqueId", "") or ""),
                    family_name=self._family_name(symbol),
                    type_name=self._element_type_name(symbol),
                    element_id_value=self._element_id_value(symbol.Id),
                )
            )

        return sorted(result, key=lambda item: item.label.lower())

    def readiness(self, housing, main_view_unique_id):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        main_view = self._get_element(
            main_view_unique_id,
            "Sélectionnez une vue logement générée.",
        )

        missing = []
        if not self._is_placeable_main_view(main_view, housing.key):
            missing.append("vue logement compatible")

        location = self._find_named_view(location_view_name(housing.key))
        if location is None:
            missing.append("plan de repérage")

        interior = self._find_named_schedule(schedule_name(housing.key, "INT"))
        if interior is None:
            missing.append("nomenclature intérieure")

        exterior = self._find_named_schedule(schedule_name(housing.key, "EXT"))
        if exterior is None:
            missing.append("nomenclature extérieure")

        return SheetAssemblyReadiness(
            housing_key=housing.key,
            main_view_name=str(getattr(main_view, "Name", "") or ""),
            location_view_name_value=str(getattr(location, "Name", "") or "")
            if location is not None else "",
            interior_schedule_name=str(getattr(interior, "Name", "") or "")
            if interior is not None else "",
            exterior_schedule_name=str(getattr(exterior, "Name", "") or "")
            if exterior is not None else "",
            missing=missing,
        )

    def create_sheet(
        self,
        housing,
        title_block_type_unique_id,
        main_view_unique_id,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        title_block = self._get_title_block_type(title_block_type_unique_id)
        main_view = self._get_element(
            main_view_unique_id,
            "Sélectionnez une vue logement générée.",
        )

        readiness = self.readiness(housing, main_view_unique_id)
        if not readiness.is_ready:
            raise ValueError(
                "La feuille ne peut pas être assemblée. {}".format(
                    readiness.summary
                )
            )

        location = self._find_named_view(location_view_name(housing.key))
        interior = self._find_named_schedule(schedule_name(housing.key, "INT"))
        exterior = self._find_named_schedule(schedule_name(housing.key, "EXT"))

        self._validate_placeable_view(main_view, "vue logement")
        self._validate_placeable_view(location, "plan de repérage")
        self._validate_schedule_not_placed(interior, "nomenclature intérieure")
        self._validate_schedule_not_placed(exterior, "nomenclature extérieure")

        sheet_number = "PDV-{}".format(housing.key)
        sheet_name = "Plan de vente - {}".format(housing.key)
        self._ensure_sheet_identity_available(sheet_number, sheet_name)

        from Autodesk.Revit.DB import (
            ScheduleSheetInstance,
            ViewSheet,
            Viewport,
            XYZ,
        )

        sheet = None
        with RevitTransaction(
            self.document,
            "Plans de vente - Feuille {}".format(housing.key),
        ):
            sheet = ViewSheet.Create(self.document, title_block.Id)
            if sheet is None:
                raise RuntimeError("Revit n'a pas retourné la feuille créée.")

            sheet.SheetNumber = sheet_number
            sheet.Name = sheet_name

            outline = sheet.Outline
            anchors = default_sheet_anchors(
                outline.Min.U,
                outline.Min.V,
                outline.Max.U,
                outline.Max.V,
            )

            main_anchor = anchors["main_view"]
            location_anchor = anchors["location_view"]
            interior_anchor = anchors["interior_schedule"]
            exterior_anchor = anchors["exterior_schedule"]

            Viewport.Create(
                self.document,
                sheet.Id,
                main_view.Id,
                XYZ(main_anchor.x, main_anchor.y, 0.0),
            )
            Viewport.Create(
                self.document,
                sheet.Id,
                location.Id,
                XYZ(location_anchor.x, location_anchor.y, 0.0),
            )
            ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                interior.Id,
                XYZ(interior_anchor.x, interior_anchor.y, 0.0),
            )
            ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                exterior.Id,
                XYZ(exterior_anchor.x, exterior_anchor.y, 0.0),
            )

        return SheetAssemblyResult(
            housing_key=housing.key,
            sheet_number=sheet.SheetNumber,
            sheet_name=sheet.Name,
            title_block_label="{} : {}".format(
                self._family_name(title_block),
                self._element_type_name(title_block),
            ),
            main_view_name=str(getattr(main_view, "Name", "") or ""),
            location_view_name_value=str(getattr(location, "Name", "") or ""),
            interior_schedule_name=str(getattr(interior, "Name", "") or ""),
            exterior_schedule_name=str(getattr(exterior, "Name", "") or ""),
        )

    def _validate_placeable_view(self, view, role_label):
        from Autodesk.Revit.DB import FilteredElementCollector, Viewport

        for viewport in (
            FilteredElementCollector(self.document)
            .OfClass(Viewport)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if getattr(viewport, "ViewId", None) == view.Id:
                raise ValueError(
                    "La {} « {} » est déjà placée sur une feuille.".format(
                        role_label,
                        getattr(view, "Name", ""),
                    )
                )

    def _validate_schedule_not_placed(self, schedule, role_label):
        from Autodesk.Revit.DB import FilteredElementCollector, ScheduleSheetInstance

        for instance in (
            FilteredElementCollector(self.document)
            .OfClass(ScheduleSheetInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if getattr(instance, "ScheduleId", None) == schedule.Id:
                raise ValueError(
                    "La {} « {} » est déjà placée sur une feuille.".format(
                        role_label,
                        getattr(schedule, "Name", ""),
                    )
                )

    def _is_placeable_main_view(self, view, housing_key):
        name = str(getattr(view, "Name", "") or "")
        return name.startswith("PDV PROTO - {} - ".format(housing_key))

    def _find_named_view(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, View

        for view in (
            FilteredElementCollector(self.document)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if bool(getattr(view, "IsTemplate", False)):
                continue
            if str(getattr(view, "Name", "") or "") == target_name:
                return view
        return None

    def _find_named_schedule(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSchedule

        for schedule in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSchedule)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if str(getattr(schedule, "Name", "") or "") == target_name:
                return schedule
        return None

    def _template_layout(self, sheet):
        from Autodesk.Revit.DB import (
            BuiltInCategory,
            FilteredElementCollector,
            ScheduleSheetInstance,
            ViewSheet,
        )

        if sheet is None or not isinstance(sheet, ViewSheet):
            raise ValueError("La feuille modèle sélectionnée n'est plus valide.")

        required = required_placeholder_names()
        points = {}
        viewport_type_ids = {}

        for viewport_id in list(sheet.GetAllViewports() or []):
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            name = str(getattr(view, "Name", "") or "")
            for role in ("main_view", "location_view"):
                if name != required[role]:
                    continue
                if role in points:
                    raise ValueError(
                        "Le rôle {} est présent plusieurs fois sur la feuille modèle.".format(
                            role
                        )
                    )
                center = viewport.GetBoxCenter()
                points[role] = (float(center.X), float(center.Y))
                try:
                    viewport_type_ids[role] = viewport.GetTypeId()
                except Exception:
                    viewport_type_ids[role] = None

        for instance in (
            FilteredElementCollector(self.document, sheet.Id)
            .OfClass(ScheduleSheetInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            schedule = self.document.GetElement(instance.ScheduleId)
            name = str(getattr(schedule, "Name", "") or "")
            for role in ("interior_schedule", "exterior_schedule"):
                if name != required[role]:
                    continue
                if role in points:
                    raise ValueError(
                        "Le rôle {} est présent plusieurs fois sur la feuille modèle.".format(
                            role
                        )
                    )
                point = instance.Point
                points[role] = (float(point.X), float(point.Y))

        missing = [
            required[role]
            for role in (
                "main_view",
                "location_view",
                "interior_schedule",
                "exterior_schedule",
            )
            if role not in points
        ]
        if missing:
            raise ValueError(
                "Feuille modèle incomplète. Élément(s) manquant(s) : {}.".format(
                    ", ".join(missing)
                )
            )

        title_blocks = list(
            FilteredElementCollector(self.document, sheet.Id)
            .OfCategory(BuiltInCategory.OST_TitleBlocks)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        if len(title_blocks) != 1:
            raise ValueError(
                "La feuille modèle doit contenir exactement un cartouche."
            )

        title_block_type = self.document.GetElement(
            title_blocks[0].GetTypeId()
        )
        if title_block_type is None:
            raise ValueError(
                "Impossible de retrouver le type de cartouche de la feuille modèle."
            )

        return _TemplateLayout(
            sheet=sheet,
            title_block_type=title_block_type,
            points=points,
            viewport_type_ids=viewport_type_ids,
        )

    @staticmethod
    def _apply_viewport_type(viewport, viewport_type_id):
        if viewport is None or viewport_type_id is None:
            return
        try:
            viewport.ChangeTypeId(viewport_type_id)
        except Exception:
            pass

    def _get_title_block_type(self, unique_id):
        if not unique_id:
            raise ValueError("Sélectionnez un type de cartouche.")

        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError("Le type de cartouche sélectionné n'existe plus.")

        try:
            from Autodesk.Revit.DB import BuiltInCategory
            category_id = element.Category.Id
            expected = int(BuiltInCategory.OST_TitleBlocks)
            actual = self._element_id_value(category_id)
            if actual != expected:
                raise ValueError("L'élément sélectionné n'est pas un cartouche.")
        except ValueError:
            raise
        except Exception:
            raise ValueError("Impossible de valider le type de cartouche.")

        return element

    def _get_element(self, unique_id, error_message):
        if not unique_id:
            raise ValueError(error_message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(error_message)
        return element

    def _ensure_sheet_identity_available(self, sheet_number, sheet_name):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet

        for sheet in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if str(getattr(sheet, "SheetNumber", "") or "") == sheet_number:
                raise ValueError(
                    "La feuille numéro « {} » existe déjà. "
                    "La mise à jour sera traitée à l'Étape 08.".format(
                        sheet_number
                    )
                )
            if str(getattr(sheet, "Name", "") or "") == sheet_name:
                raise ValueError(
                    "La feuille « {} » existe déjà. "
                    "La mise à jour sera traitée à l'Étape 08.".format(
                        sheet_name
                    )
                )

    @staticmethod
    def _family_name(element_type):
        try:
            family = getattr(element_type, "Family", None)
            value = getattr(family, "Name", None)
            if value:
                return str(value)
        except Exception:
            pass
        try:
            value = getattr(element_type, "FamilyName", None)
            if value:
                return str(value)
        except Exception:
            pass
        return ""

    @staticmethod
    def _element_type_name(element_type):
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
    def _element_id_value(element_id):
        value = getattr(element_id, "Value", None)
        if value is not None:
            return int(value)
        return int(element_id.IntegerValue)
