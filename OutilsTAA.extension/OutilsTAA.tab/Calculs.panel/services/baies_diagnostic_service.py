# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""Analyse en lecture seule Revit 2025.4 des fenêtres et portes.
Ni boîte englobante ni cote nominale ne prouve la surface en tableau.
"""
import json
from baies_diagnostic.evaluator import evaluate, aggregate_by_type
from baies_diagnostic.facade_scope import is_facade_family, facade_status, exclusion_reason, rule_16_status

def _text(value):
    try:
        return unicode(value) if value is not None else u""
    except NameError:
        return str(value) if value is not None else u""
    except Exception:
        return u"?"

def _eid(element):
    try:
        return _text(element.Id.Value)
    except Exception:
        try:
            return _text(element.Id.IntegerValue)
        except Exception:
            return u""

def _room(room):
    try:
        return u"{} - {}".format(_text(room.Number), _text(room.Name)) if room else u""
    except Exception:
        return u""


def _element_name(element, db, fallback=u""):
    """Retourne Element.Name sans erreur de binding IronPython sur ElementType.

    La propriété .Name de certains FamilySymbol / Family peut lever
    AttributeError('Name') malgré sa présence dans l'API Revit.
    """
    if element is None:
        return fallback
    try:
        name = db.Element.Name.GetValue(element)
        if name:
            return _text(name)
    except Exception:
        pass
    try:
        name = element.Name
        if name:
            return _text(name)
    except Exception:
        pass
    # Dernier recours spécifique aux types de familles.
    try:
        parameter = element.get_Parameter(db.BuiltInParameter.SYMBOL_NAME_PARAM)
        if parameter:
            name = parameter.AsString()
            if name:
                return _text(name)
    except Exception:
        pass
    return fallback


class BaiesDiagnosticService(object):
    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant")
        self.document=document

    @staticmethod
    def _db():
        import Autodesk.Revit.DB as DB
        return DB

    def _parameters(self, element, origin):
        DB=self._db()
        if element is None:
            return []
        result=[]
        for p in element.Parameters:
            try:
                if not p.HasValue or p.StorageType != DB.StorageType.Double:
                    continue
                if not p.Definition.GetDataType().Equals(DB.SpecTypeId.Length):
                    continue
                name=_text(p.Definition.Name)
                lower=name.lower()
                if not any(part in lower for part in
                    (u"largeur",u"hauteur",u"width",u"height",u"rough",u"tableau",u"baie",u"ouverture",u"vitrage",u"hors tout",u"hors-tout")):
                    continue
                value=float(DB.UnitUtils.ConvertFromInternalUnits(p.AsDouble(), DB.UnitTypeId.Meters))
                if 0 < value < 100:
                    result.append(dict(name=name,value_m=round(value,6),origin=origin))
            except Exception:
                continue
        return result

    def _snapshot(self, dbdoc, instance, source, source_id, category):
        symbol=instance.Symbol
        if symbol is None:
            raise ValueError("Type manquant")
        family=symbol.Family
        # Familles/types Revit : .Name peut lever AttributeError sous IronPython.
        family_name=_element_name(family, self._db(), u"Famille inconnue #{}".format(_eid(family)))
        type_name=_element_name(symbol, self._db(), u"Type inconnu #{}".format(_eid(symbol)))
        params=self._parameters(instance,"occurrence")+self._parameters(symbol,"type")
        outcome=evaluate(params)
        selected=outcome["selected"] or {}
        try:
            host=instance.Host
        except Exception:
            host=None
        function=u""
        try:
            function=_text(host.WallType.Function)
        except Exception:
            pass
        try:
            room_from=_room(instance.FromRoom)
            room_to=_room(instance.ToRoom)
        except Exception:
            room_from=room_to=u""
        bounds=u""
        try:
            bbox=instance.get_BoundingBox(None)
            if bbox:
                bounds=u"{:.3f} / {:.3f} / {:.3f}".format(
                   abs(bbox.Max.X-bbox.Min.X)*0.3048,
                   abs(bbox.Max.Y-bbox.Min.Y)*0.3048,
                   abs(bbox.Max.Z-bbox.Min.Z)*0.3048)
        except Exception:
            pass
        host_category=_text(host.Category.Name) if host and host.Category else u""
        classification=facade_status(family_name, host_category, function, type_name)
        return dict(source=source,source_id=source_id,document=_text(dbdoc.Title),
                    category=category,family=family_name,
                    type=type_name,element_id=_eid(instance),
                    unique_id=_text(instance.UniqueId),
                    host_id=_eid(host) if host else u"",
                    host_category=host_category,
                    wall_function=function,from_room=room_from,to_room=room_to,
                    facade_status=classification,
                    rule_16_status=rule_16_status(family_name,type_name,host_category,function),
                    method=selected.get("method",u""),
                    width_m=selected.get("width_m",u""),
                    height_m=selected.get("height_m",u""),
                    area_m2=round(selected["area_m2"],4) if selected else u"",
                    width_parameter=selected.get("width_parameter",u""),
                    height_parameter=selected.get("height_parameter",u""),
                    width_origin=selected.get("width_origin",u""),
                    height_origin=selected.get("height_origin",u""),
                    status=outcome["status"],reason=outcome["reason"],
                    bounding_box_xyz_m=bounds,
                    parameters_json=json.dumps(params,ensure_ascii=False,sort_keys=True),
                    candidates_json=json.dumps(outcome["candidates"],ensure_ascii=False,sort_keys=True),
                    reglementaire_valide=u"NON : vérification de la baie et du contexte nécessaire")

    def _collect(self, document, source, source_id, rows, alerts, excluded,
                 facade_only=False, exclude_lanterns=True, exclude_mrx=True):
        DB=self._db()
        for bic, category in ((DB.BuiltInCategory.OST_Windows,u"Fenêtre"),
                              (DB.BuiltInCategory.OST_Doors,u"Porte")):
            try:
                for element in DB.FilteredElementCollector(document).OfCategory(bic).WhereElementIsNotElementType():
                    try:
                        if isinstance(element,DB.FamilyInstance):
                            if facade_only:
                                symbol=element.Symbol
                                family=symbol.Family if symbol else None
                                if not is_facade_family(_element_name(family, DB)):
                                    continue
                            symbol=element.Symbol
                            family=symbol.Family if symbol else None
                            name=_element_name(family, DB)
                            type_name=_element_name(symbol, DB)
                            try:
                                host=element.Host
                                host_category=_text(host.Category.Name) if host and host.Category else u""
                            except Exception:
                                host_category=u""
                            reason=exclusion_reason(name, type_name, host_category)
                            should_hide=((reason=="LANTERNEAU" and exclude_lanterns)
                                         or (reason=="MRX" and exclude_mrx))
                            if should_hide:
                                excluded.append(dict(source=source,source_id=source_id,
                                    category=category, family=name, type=type_name,
                                    element_id=_eid(element),unique_id=_text(element.UniqueId),
                                    reason=reason))
                                continue
                            rows.append(self._snapshot(document,element,source,source_id,category))
                    except Exception as error:
                        alerts.append(dict(source=source,element_id=_eid(element),
                                           message=u"Impossible de lire l'occurrence : {}".format(_text(error))))
            except Exception as error:
                alerts.append(dict(source=source,element_id=u"",
                                   message=u"Collecte {} impossible : {}".format(category,_text(error))))

    def analyze(self, include_links=False, facade_only=False,
                exclude_lanterns=True, exclude_mrx=True):
        DB=self._db()
        rows, alerts, excluded=[], [], []
        self._collect(self.document,u"Projet hôte",u"HOST",rows,alerts,excluded,
                      facade_only=facade_only,exclude_lanterns=exclude_lanterns,
                      exclude_mrx=exclude_mrx)
        if include_links:
            try:
                for link in DB.FilteredElementCollector(self.document).OfClass(DB.RevitLinkInstance):
                    source=u"{} [{}]".format(_text(link.Name),_eid(link))
                    try:
                        linked=link.GetLinkDocument()
                        if linked is None:
                            alerts.append(dict(source=source,element_id=_eid(link),
                                               message=u"Lien non chargé : ignoré"))
                        else:
                            self._collect(linked,source,_text(link.UniqueId),rows,alerts,excluded,
                                          facade_only=facade_only,exclude_lanterns=exclude_lanterns,
                                          exclude_mrx=exclude_mrx)
                    except Exception as error:
                        alerts.append(dict(source=source,element_id=_eid(link),
                                           message=u"Lien ignoré : {}".format(_text(error))))
            except Exception as error:
                alerts.append(dict(source=u"Projet hôte",element_id=u"",
                                   message=u"Collecte des liens impossible : {}".format(_text(error))))
        return rows,aggregate_by_type(rows),alerts,excluded
