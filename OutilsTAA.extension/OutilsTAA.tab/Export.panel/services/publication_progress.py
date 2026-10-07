# -*- coding: utf-8 -*-
"""Plan de publication à unités fixes, sans dépendance UI ni API Revit.

Une unité est traitée après retour de l'opération, même en échec. Une unité
empêchée est explicitement classée non exécutée ; elle ne devient pas un succès.
Le rapport métier reste la source de vérité. Aucun temps ni feuille n'est estimé.
"""

from __future__ import unicode_literals

import logging
from contextlib import contextmanager


PHASES = {
    "prepare": "Préparation",
    "pdf": "Export PDF",
    "delivery": "Livraison des fichiers",
    "dwg": "Export DWG",
    "finalize": "Finalisation",
}


def progress_kwargs(progress):
    """Conserve exactement l'ancien appel lorsque le reporter est absent."""
    return {"progress": progress} if progress is not None else {}


@contextmanager
def operation(progress, key, item_label=""):
    """Encadre une opération réelle sans intercepter son diagnostic métier."""
    if progress is not None:
        progress.begin(key, item_label)
    try:
        yield
    except Exception:
        if progress is not None:
            progress.end(key, "Échec de l'unité — voir le rapport")
        raise
    else:
        if progress is not None:
            progress.end(key)


class PublicationProgress(object):
    """Plan global immuable : réglages résolus, puis une unité par opération.

Le contrat commun current/total/message est enrichi par les phases et carnets.
Le callback reçoit une copie d'état ; sa défaillance ne doit jamais interrompre
une livraison de fichiers ou provoquer un deuxième appel d'export.
"""

    def __init__(self, targets, settings, callback=None):
        if len(targets) != len(settings):
            raise ValueError("Un réglage effectif est requis pour chaque carnet.")
        self.callback = callback
        self.warnings = []
        self.targets = []
        self.completed = set()
        self.state = {"phase": "Préparation", "phase_key": "prepare",
                      "current": 0, "total": 1, "percent": 0,
                      "carnet_name": "—", "item_label": "Préparation de la publication",
                      "message": "Publication en cours", "status": "running"}
        for index, target in enumerate(targets):
            value = settings[index]
            keys = ["prepare"]
            if value.pdf_enabled:
                keys.append("pdf")
                if value.pdf_mode != "COMBINED":
                    keys.append("delivery")
            if value.dwg_enabled:
                # Un groupe DWG par carnet, quel que soit le nombre d'appels.
                keys.append("dwg")
            keys.append("finalize")
            self.targets.append(TargetProgress(self, index, target.name, keys))
            self.state["total"] += len(keys)

    def start(self):
        self._emit()

    def target(self, index):
        return self.targets[index]

    def _emit(self):
        self.state["current"] = len(self.completed)
        self.state["percent"] = int(100 * len(self.completed) // self.state["total"])
        if self.callback is not None:
            try:
                self.callback(dict(self.state))
            except Exception as exc:
                logging.getLogger("OutilsTAA").exception("Échec de l'affichage de progression")
                self.warnings.append("Affichage de progression interrompu : {0}".format(exc))
                self.callback = None

    def finish(self, report):
        """Appelé après consolidation du rapport, jamais dans un finally."""
        if len(self.completed) != self.state["total"] - 1:
            raise RuntimeError("Plan de progression incomplet : publication interrompue.")
        self.state.update(phase=PHASES["finalize"], phase_key="finalize",
                          item_label="Rapport de publication", carnet_name="—")
        self.completed.add(("report", "finalize"))
        self.state.update(status="finished", message="Publication terminée — voir le rapport")
        self._emit()
        report.setdefault("warnings", []).extend(self.warnings)

    def interrupt(self):
        self.state.update(status="interrupted", message="Publication interrompue")
        self._emit()


class TargetProgress(object):
    """Vue d'un carnet sur le compteur global, sans remise à zéro."""

    def __init__(self, parent, index, name, keys):
        self.parent = parent
        self.index = index
        self.name = name
        self.keys = tuple(keys)
        self.started = set()

    def begin(self, key, item_label=""):
        if key not in self.keys:
            raise ValueError("Unité absente du plan : {0}".format(key))
        self.started.add(key)
        self.parent.state.update(phase=PHASES[key], phase_key=key,
                                 carnet_name=self.name, item_label=item_label or PHASES[key],
                                 message="{0} en cours…".format(item_label or PHASES[key]))
        self.parent._emit()

    def end(self, key, message="Unité traitée"):
        if key not in self.started:
            raise ValueError("Unité non commencée : {0}".format(key))
        self.parent.completed.add((self.index, key))
        self.parent.state["message"] = message
        self.parent._emit()

    def end_if_started(self, key, message="Unité traitée"):
        if key in self.started:
            self.end(key, message)

    def finalize(self, success, empty=False):
        """L'historique/rapport du carnet doit être traité avant cet appel.

En cas d'erreur ou de périmètre vide, classer explicitement les opérations
empêchées. Un succès ne permet jamais de compléter silencieusement le plan.
"""
        for key in self.keys:
            if key == "finalize" or (self.index, key) in self.parent.completed:
                continue
            if success and not empty:
                raise RuntimeError("Unité non traitée : {0} / {1}".format(self.name, key))
            self.begin(key)
            self.end(key, "Non exécutée — périmètre vide" if empty else
                     "Non exécutée après erreur — voir le rapport")
        self.begin("finalize", "Historique et résultats du carnet")
        self.end("finalize")
