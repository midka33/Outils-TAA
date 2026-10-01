# -*- coding: utf-8 -*-
"""Catalogue et lecture des paramètres de nommage, sans dépendance WPF."""
from __future__ import unicode_literals

try:
    text_type = unicode
except NameError:
    text_type = str


class NamingVariable(object):
    def __init__(self, label, token):
        self.Label = label
        self.Token = token


class NamingParameters(object):
    SCOPES = ("feuille", "info_projet", "feuille_id", "info_projet_id", "parametre")

    def __init__(self, document):
        self.document = document

    def project_info(self):
        return getattr(self.document, "ProjectInformation", None)

    def _key(self, parameter):
        """Identité durable : paramètre natif, GUID partagé ou UniqueId projet."""
        try:
            if parameter.IsShared:
                return "guid=" + text_type(parameter.GUID)
            identifier = parameter.Id
            value = getattr(identifier, "Value", None)
            if value is None:
                value = identifier.IntegerValue
            if value < 0:
                return "builtin=" + text_type(value)
            definition = self.document.GetElement(identifier)
            return "uid=" + definition.UniqueId
        except Exception:
            return None

    def _parameters(self, element):
        try:
            return list(element.Parameters)
        except Exception:
            return []

    def catalogue(self, sheets):
        """Union des paramètres présents, y compris vides et en lecture seule."""
        result = []
        scopes = (("feuille", "Feuille", sheets),
                  ("info_projet", "Informations sur le projet", [self.project_info()]))
        for scope, label, elements in scopes:
            names = {}
            for element in elements:
                for parameter in self._parameters(element):
                    try:
                        name = text_type(parameter.Definition.Name)
                        if not name or parameter.StorageType.ToString() == "None":
                            continue
                        names.setdefault(name, set()).add(self._key(parameter))
                    except Exception:
                        continue
            for name in sorted(names, key=lambda value: value.lower()):
                keys = names[name]
                if len(keys) > 1 or "{" in name or "}" in name or name != name.strip():
                    for key in sorted(value for value in keys if value is not None):
                        result.append(NamingVariable(
                            "{0} — {1} ({2})".format(label, name, key),
                            "{{{0}_id:{1}}}".format(scope, key)))
                else:
                    result.append(NamingVariable("{0} — {1}".format(label, name),
                                                 "{{{0}:{1}}}".format(scope, name)))
        return result

    def read(self, scope, selector, item):
        if scope.startswith("info_projet"):
            element = self.project_info()
        else:
            try:
                element = self.document.GetElement(item.unique_id)
            except Exception:
                element = None
        if element is None:
            return ""
        try:
            if scope.endswith("_id"):
                matches = [p for p in self._parameters(element) if self._key(p) == selector]
            elif hasattr(element, "GetParameters"):
                matches = list(element.GetParameters(selector))
            else:
                # Compatibilité avec les adaptateurs historiques du service.
                parameter = element.LookupParameter(selector)
                matches = [parameter] if parameter is not None else []
            if len(matches) != 1:
                return ""
            return self._value(matches[0])
        except Exception:
            return ""

    def _value(self, parameter):
        if not getattr(parameter, "HasValue", True):
            return ""
        storage = parameter.StorageType.ToString()
        if storage == "String":
            return text_type(parameter.AsString() or "")
        value = parameter.AsValueString()
        if value is not None and value != "":
            return text_type(value)
        if storage == "Integer":
            return text_type(parameter.AsInteger())
        if storage == "Double":
            return text_type(parameter.AsDouble())
        if storage == "ElementId":
            referenced = self.document.GetElement(parameter.AsElementId())
            return text_type(getattr(referenced, "Name", "") or "")
        return ""
