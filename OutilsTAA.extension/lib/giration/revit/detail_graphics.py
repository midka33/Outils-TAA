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


def _draw_polyline(document, view, points, z, line_style=None, progress=None):
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
        if progress is not None:
            progress(1)
    return results


def create_graphics(document, view, vehicle, trajectory, show_wheels=True,
                    show_vehicle=True, show_corner_tracks=True, progress=None):
    """Creer seulement des DetailCurves dans la vue cible, en une transaction.

    N'ecrit RIEN dans les vues autres que celle selectionnee.
    Retourne les ElementIds pour des controles manuels, sans persistance.
    """
    from ..services.kinematics import AckermannKinematics
    if not trajectory or view.IsTemplate:
        raise ValueError('Vue ou trajectoire incorrecte')
    engine = AckermannKinematics(vehicle)
    z = view.Origin.Z
    total_steps = (len(trajectory) - 1) * (1 + (4 if show_wheels else 0)
                   + (4 if show_corner_tracks else 0)) + (8 if show_vehicle else 0)
    processed = [0]
    if progress is not None:
        progress(0, max(1, total_steps))

    def advance(amount):
        processed[0] += amount
        if progress is not None and processed[0] % 20 == 0:
            progress(processed[0], max(1, total_steps))

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
        elements.extend(_draw_polyline(document, view, rear_axle, z, progress=advance))
        if show_wheels:
            for line in engine.calculate_wheel_trajectories(trajectory).values():
                elements.extend(_draw_polyline(document, view, line, z, progress=advance))
        if show_corner_tracks:
            footprints = engine.calculate_swept_area(trajectory)
            for i in range(4):
                elements.extend(_draw_polyline(document, view,
                                               [corners[i] for corners in footprints], z, progress=advance))
        if show_vehicle:
            footprints = engine.calculate_swept_area(trajectory)
            for corners in (footprints[0], footprints[-1]):
                ring = list(corners) + [corners[0]]
                elements.extend(_draw_polyline(document, view, ring, z, progress=advance))
        transaction.Commit()
        if progress is not None:
            progress(total_steps, max(1, total_steps))
        return [element.Id for element in elements]
    except Exception:
        transaction.RollBack()
        raise
