# -*- coding: utf-8 -*-
"""Aller-retour natif DWG : cache temporaire, isolé par document et session Revit.

Seul le chemin du JSON est conservé dans les envvars pyRevit. Aucun objet Revit
ou WPF, callback Idling ou fenêtre n'est conservé entre deux exécutions.
"""
import hashlib
import json
import os
import tempfile
from copy import copy

from carnet_repository import CarnetRepository
from publication_source import PublicationSource


class DwgUiSession(object):
    def __init__(self, repository, document, envvars):
        scope = "{}|{}|{}".format(repository.storage_path, os.getpid(), document.GetHashCode())
        self.key = "TAA_DWG_RETURN_" + hashlib.sha256(scope.encode("utf-8")).hexdigest()
        self.envvars = envvars

    def save(self, state):
        descriptor, path = tempfile.mkstemp(prefix="taa-dwg-return-", suffix=".json")
        try:
            with os.fdopen(descriptor, "w") as handle:
                json.dump(state, handle, ensure_ascii=True)
            old_path = self.envvars.get_envvar(self.key)
            if old_path and os.path.isfile(old_path):
                os.remove(old_path)
            self.envvars.set_envvar(self.key, path)
        except Exception:
            if os.path.isfile(path):
                os.remove(path)
            raise

    def load(self):
        path = self.envvars.get_envvar(self.key)
        if not path:
            return None
        with open(path, "r") as handle:
            return json.load(handle)

    def clear(self):
        path = self.envvars.get_envvar(self.key)
        if path and os.path.isfile(path):
            os.remove(path)
        self.envvars.set_envvar(self.key, None)


def capture(window):
    manager = window._drag_drop_manager
    current = window.PublicationTree.SelectedItem
    carnets = []
    for carnet in window.session_carnets:
        target = copy(carnet)
        target.source = target.source or PublicationSource(PublicationSource.MANUAL)
        carnets.append(CarnetRepository._to_dict(target))
    return {"carnets": carnets,
            "selection": [manager._key(tag) for tag in manager.selected_tags()],
            "active": manager._key(current.Tag) if current is not None else None,
            "expanded": [manager._key(node.Tag) for node in manager._all() if node.IsExpanded]}


def restore(window, state):
    if not state:
        return
    restored = []
    for value in state.get("carnets", []):
        carnet = CarnetRepository._from_dict(value)
        carnet.persistent = False
        restored.append(carnet)
    window.session_carnets = restored
    window._refresh_tree()
    manager = window._drag_drop_manager
    for node in manager._all():
        key = manager._key(node.Tag)
        node.IsExpanded = key in state.get("expanded", [])
        if key == state.get("active"):
            node.IsSelected = True
    # Restaurer le périmètre Ctrl/Maj après l'événement de sélection native.
    manager._select(state.get("selection", []))
