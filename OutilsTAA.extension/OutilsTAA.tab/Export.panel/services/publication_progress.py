# -*- coding: utf-8 -*-
"""Progression réelle de publication, sans dépendance WPF ni API Revit.

Le plan garde des unités métier fixes, mais accepte une fraction réelle à
l'intérieur de l'unité active. Cette fraction peut provenir de la barre native
Revit ou d'un traitement contrôlé feuille par feuille (livraison/renommage).
Aucun temps restant ni numéro de feuille n'est inventé.
"""

from __future__ import unicode_literals

import logging
from contextlib import contextmanager


PHASES = {
    "prepare": "Préparation",
    "pdf": "Export PDF",
    "pdf_delivery": "Livraison PDF",
    "dwg": "Export DWG",
    "dwg_delivery": "Livraison DWG",
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
    """Plan global : unités réelles + fraction de l'unité active."""

    def __init__(self, targets, settings, callback=None):
        if len(targets) != len(settings):
            raise ValueError("Un réglage effectif est requis pour chaque carnet.")
        self.callback = callback
        self.warnings = []
        self.targets = []
        self.completed = set()
        self.active_fraction = 0.0
        self._last_percent = 0
        self.state = {
            "phase": "Préparation",
            "phase_key": "prepare",
            "current": 0,
            "total": 1,
            "percent": 0,
            "carnet_name": "—",
            "item_label": "Préparation de la publication",
            "message": "Publication en cours",
            "status": "running",
            "detail_current": 0,
            "detail_total": 0,
            "detail_label": "unités",
        }

        for index, target in enumerate(targets):
            value = settings[index]
            item_count = len(getattr(target, "items", []) or [])
            keys = ["prepare"]

            if value.pdf_enabled:
                keys.append("pdf")
                if value.pdf_mode != "COMBINED":
                    keys.append("pdf_delivery")

            if value.dwg_enabled:
                keys.append("dwg")
                if item_count > 1:
                    keys.append("dwg_delivery")

            keys.append("finalize")
            self.targets.append(
                TargetProgress(self, index, target.name, keys)
            )
            self.state["total"] += len(keys)

    def start(self):
        self._emit()

    def target(self, index):
        return self.targets[index]

    def _emit(self):
        self.state["current"] = len(self.completed)
        raw = 100.0 * (
            len(self.completed) + max(0.0, min(1.0, self.active_fraction))
        ) / float(self.state["total"])
        percent = int(raw)
        if percent < self._last_percent:
            percent = self._last_percent
        if self.state.get("status") != "finished":
            percent = min(percent, 99)
        self._last_percent = percent
        self.state["percent"] = percent

        if self.callback is not None:
            try:
                self.callback(dict(self.state))
            except Exception as exc:
                logging.getLogger("OutilsTAA").exception(
                    "Échec de l'affichage de progression"
                )
                self.warnings.append(
                    "Affichage de progression interrompu : {0}".format(exc)
                )
                self.callback = None

    def finish(self, report):
        """Appelé après consolidation du rapport, jamais dans un finally."""
        if len(self.completed) != self.state["total"] - 1:
            raise RuntimeError(
                "Plan de progression incomplet : publication interrompue."
            )
        self.active_fraction = 0.0
        self.state.update(
            phase=PHASES["finalize"],
            phase_key="finalize",
            item_label="Rapport de publication",
            carnet_name="—",
            detail_current=0,
            detail_total=0,
            detail_label="unités",
        )
        self.completed.add(("report", "finalize"))
        self.state.update(
            status="finished",
            message="Publication terminée — voir le rapport",
        )
        self._last_percent = 100
        self.state["percent"] = 100
        self._emit()
        report.setdefault("warnings", []).extend(self.warnings)

    def interrupt(self):
        self.active_fraction = 0.0
        self.state.update(
            status="interrupted",
            message="Publication interrompue",
        )
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
        self.parent.active_fraction = 0.0
        self.parent.state.update(
            phase=PHASES[key],
            phase_key=key,
            carnet_name=self.name,
            item_label=item_label or PHASES[key],
            message="{0} en cours…".format(item_label or PHASES[key]),
            detail_current=0,
            detail_total=0,
            detail_label="unités",
        )
        self.parent._emit()

    def native_progress(self, key, position, upper, caption):
        """Relaie une progression réellement fournie par Revit."""
        if key not in self.started or upper <= 0:
            return
        fraction = float(position) / float(upper)
        self.parent.active_fraction = max(
            self.parent.active_fraction,
            max(0.0, min(1.0, fraction)),
        )
        self.parent.state.update(
            phase=PHASES[key],
            phase_key=key,
            carnet_name=self.name,
            item_label=caption or "Traitement Revit",
            message=caption or "Traitement Revit en cours…",
            detail_current=int(position),
            detail_total=int(upper),
            detail_label="progression Revit",
        )
        self.parent._emit()

    def detail(self, key, current, total, item_label,
               detail_label="mises en page", message=None):
        """Signale une unité fine réellement terminée par Outils TAA."""
        if key not in self.started:
            raise ValueError("Unité non commencée : {0}".format(key))
        total = int(total or 0)
        current = int(current or 0)
        fraction = (
            float(current) / float(total)
            if total > 0 else 0.0
        )
        self.parent.active_fraction = max(
            self.parent.active_fraction,
            max(0.0, min(1.0, fraction)),
        )
        self.parent.state.update(
            phase=PHASES[key],
            phase_key=key,
            carnet_name=self.name,
            item_label=item_label or PHASES[key],
            message=message or "{0} / {1} {2}".format(
                current, total, detail_label
            ),
            detail_current=current,
            detail_total=total,
            detail_label=detail_label,
        )
        self.parent._emit()

    def end(self, key, message="Unité traitée"):
        if key not in self.started:
            raise ValueError("Unité non commencée : {0}".format(key))
        self.parent.completed.add((self.index, key))
        self.parent.active_fraction = 0.0
        self.parent.state["message"] = message
        self.parent._emit()

    def end_if_started(self, key, message="Unité traitée"):
        if key in self.started:
            self.end(key, message)

    def finalize(self, success, empty=False):
        """Complète explicitement les unités non exécutées avant finalisation."""
        for key in self.keys:
            if key == "finalize" or (self.index, key) in self.parent.completed:
                continue
            if success and not empty:
                raise RuntimeError(
                    "Unité non traitée : {0} / {1}".format(self.name, key)
                )
            self.begin(key)
            self.end(
                key,
                "Non exécutée — périmètre vide"
                if empty else "Non exécutée après erreur — voir le rapport",
            )
        self.begin("finalize", "Historique et résultats du carnet")
        self.end("finalize")
