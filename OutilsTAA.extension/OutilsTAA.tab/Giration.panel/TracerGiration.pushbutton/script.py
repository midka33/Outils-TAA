# -*- coding: utf-8 -*-
"""TAA Giration - prototype de trace par clics (non dynamique).

Ce point d'entree est volontairement ASCII pour le parseur pyRevit.
Cible : Revit 2025.4, moteur IronPython de pyRevit 5.x.
"""
import math
import os
import sys

CURRENT = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.abspath(os.path.join(CURRENT, '..'))
UI_DIR = os.path.join(PANEL, 'ui')
EXTENSION = os.path.abspath(os.path.join(PANEL, '..', '..'))
for path in (EXTENSION, PANEL, UI_DIR):
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)

from pyrevit import revit, forms
from Autodesk.Revit import DB
from Autodesk.Revit.UI.Selection import ObjectSnapTypes
from Autodesk.Revit.Exceptions import OperationCanceledException

from lib.giration.data.vehicles import get_all_vehicles
from lib.giration.geometry.vector2d import Vector2D
from lib.giration.services.kinematics import TrajectoryPoint
from lib.giration.services.manual_solver import segment_to_rear_axle
from lib.giration.revit.detail_graphics import create_graphics
from giration_main_window import GirationMainWindow


def _metres(feet):
    return DB.UnitUtils.ConvertFromInternalUnits(feet, DB.UnitTypeId.Meters)


def _position(point):
    return Vector2D(_metres(point.X), _metres(point.Y))


def main():
    if not revit.doc or not revit.uidoc:
        forms.alert('Ouvrez un projet Revit.', title='TAA - Giration')
        return
    view = revit.doc.ActiveView
    if view.ViewType not in (DB.ViewType.FloorPlan, DB.ViewType.CeilingPlan,
                             DB.ViewType.EngineeringPlan, DB.ViewType.AreaPlan):
        forms.alert('Ouvrez une vue en plan.', title='TAA - Giration')
        return
    dialog = GirationMainWindow(get_all_vehicles())
    if not dialog.ShowDialog() or not dialog.vehicle:
        return
    selected = dialog.vehicle
    reverse = dialog.reverse
    selection = revit.uidoc.Selection
    try:
        origin = selection.PickPoint(getattr(ObjectSnapTypes, 'None'), 'TAA : origine du pare-chocs arriere')
        direction = selection.PickPoint(getattr(ObjectSnapTypes, 'None'), 'TAA : indiquez le sens avant du vehicule')
        dx = direction.X - origin.X
        dy = direction.Y - origin.Y
        if dx * dx + dy * dy < 1e-5:
            raise ValueError('Orientation initiale non definie')
        theta = math.atan2(dy, dx)
        trajectory = [TrajectoryPoint(_position(origin), theta)]
        while True:
            try:
                point = selection.PickPoint(getattr(ObjectSnapTypes, 'None'),
                    'TAA : cible ESSIEU ARRIERE suivant; Echap = terminer')
            except OperationCanceledException:
                break
            try:
                extension = segment_to_rear_axle(selected, trajectory[-1],
                                                  _position(point), reverse=reverse)
                trajectory.extend(extension[1:])
            except ValueError as exc:
                forms.alert(str(exc), title='Giration - segment refuse')
    except OperationCanceledException:
        return
    except Exception as exc:
        forms.alert(str(exc), title='Giration - entree')
        return
    if len(trajectory) < 2:
        forms.alert('Aucun segment trace.', title='Giration')
        return
    try:
        with forms.ProgressBar(title='TAA Giration - creation : {value}/{max_value}', cancellable=False) as bar:
            ids = create_graphics(revit.doc, view, selected, trajectory,
                                  progress=bar.update_progress)
        forms.alert('{0} courbes de detail creees (prototype non certifie).'.format(len(ids)),
                    title='Giration')
    except Exception as exc:
        forms.alert('Echec de la creation Revit: {0}'.format(exc), title='Giration')
        raise


if __name__ == '__main__':
    main()
