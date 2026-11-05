# -*- coding: utf-8 -*-
"""Adaptateur Revit: dessiner des courbes de detail dans une vue en plan.

Aucun calcul metier ici. Appeler apres les operations de selection UI.
Les elements generes sont une VISUALISATION PROTOTYPE, non une enveloppe
balayee reglementaire et non une trajectoire persistante editable.
"""
from Autodesk.Revit import DB


def _feet(value_m):
    return DB.UnitUtils.ConvertToInternalUnits(value_m, DB.UnitTypeId.Meters)


def _xyz(point, elevation):
    return DB.XYZ(_feet(point.x), _feet(point.y), elevation)


def _draw_polyline(document, view, points, z, line_style=None):
    results = []
    for p1, p2 in zip(points[:-1], points[1:]):
        a, b = _xyz(p1, z), _xyz(p2, z)
        if a.DistanceTo(b) <= 0.0033:  # Revit: ignorer les segments trop courts
            continue
        line = DB.Line.CreateBound(a, b)
        curve = document.Create.NewDetailCurve(view, line)
        if line_style is not None:
            curve.LineStyle = line_style
        results.append(curve)
    return results


def create_graphics(document, view, vehicle, trajectory, show_wheels=True,
                    show_vehicle=True, show_corner_tracks=True):
    """Creer seulement des DetailCurves dans la vue cible, en une transaction.

    N'ecrit RIEN dans les vues autres que celle selectionnee.
    Retourne les ElementIds pour des controles manuels, sans persistance.
    """
    from ..services.kinematics import AckermannKinematics
    if not trajectory or view.IsTemplate:
        raise ValueError('Vue ou trajectoire incorrecte')
    engine = AckermannKinematics(vehicle)
    z = view.Origin.Z
    transaction = DB.Transaction(document, 'TAA - Giration prototype')
    transaction.Start()
    elements = []
    try:
        # Axe de reference : l'essieu arriere.
        rear_axle = []
        for state in trajectory:
            from ..geometry.vector2d import Vector2D
            rear_axle.append(state.position + Vector2D.from_angle(
                state.angle, vehicle.rear_overhang))
        elements.extend(_draw_polyline(document, view, rear_axle, z))
        if show_wheels:
            for line in engine.calculate_wheel_trajectories(trajectory).values():
                elements.extend(_draw_polyline(document, view, line, z))
        if show_corner_tracks:
            footprints = engine.calculate_swept_area(trajectory)
            for i in range(4):
                elements.extend(_draw_polyline(document, view,
                                               [corners[i] for corners in footprints], z))
        if show_vehicle:
            footprints = engine.calculate_swept_area(trajectory)
            for corners in (footprints[0], footprints[-1]):
                ring = list(corners) + [corners[0]]
                elements.extend(_draw_polyline(document, view, ring, z))
        transaction.Commit()
        return [element.Id for element in elements]
    except Exception:
        transaction.RollBack()
        raise
