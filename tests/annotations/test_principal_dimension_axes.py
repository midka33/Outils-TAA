# -*- coding: utf-8 -*-
"""Garantie metier : deux grandes cotes entre faces finies, jamais longueurs de mur."""

import math
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from annotations import principal_dimension_axes as axes


def rectangle(width, depth):
    return [(0., 0., width, 0.),
            (width, 0., width, depth),
            (width, depth, 0., depth),
            (0., depth, 0., 0.)]


def test_piece_rectangulaire_deux_grandes_dimensions_perpendiculaires():
    result = axes.principal_pairs(rectangle(7., 3.5))
    assert len(result) == 2
    assert sorted(round(pair.distance, 5) for pair in result) == [3.5, 7.]
    first, second = result
    dot = first.tangent[0]*second.tangent[0] + first.tangent[1]*second.tangent[1]
    assert abs(dot) < 0.001
    assert axes.principal_reference_indexes(rectangle(7., 3.5)) == {0, 1, 2, 3}


def test_piece_rectangulaire_tournee_conserve_deux_dimensions():
    angle = math.radians(32.)
    ca, sa = math.cos(angle), math.sin(angle)

    def turn(x, y):
        return (ca*x - sa*y, sa*x + ca*y)

    raw = rectangle(9., 4.)
    rotated = []
    for x0, y0, x1, y1 in raw:
        a = turn(x0, y0)
        b = turn(x1, y1)
        rotated.append(a + b)
    pairs = axes.principal_pairs(rotated)
    assert len(pairs) == 2
    assert sorted(round(p.distance, 5) for p in pairs) == [4., 9.]


def test_direction_non_perpendiculaire_ne_devient_pas_seconde_cote(monkeypatch):
    class Pair(object):
        def __init__(self, tangent, score, i, j):
            self.tangent = tangent
            self.score = score
            self.first_index = i
            self.second_index = j
    offered = [
        Pair((1., 0.), 50., 0, 1),
        Pair((math.cos(math.radians(25.)), math.sin(math.radians(25.))), 45., 2, 3),
        Pair((0., 1.), 30., 4, 5),
    ]
    monkeypatch.setattr(axes, "dominant_dimension_pairs",
                        lambda segments, **kwargs: offered)
    chosen = axes.principal_pairs(rectangle(8., 4.))
    assert chosen == [offered[0], offered[2]]
    assert axes.principal_reference_indexes(rectangle(8., 4.)) == {0, 1, 4, 5}


def test_une_seule_famille_de_faces_opposees_ne_genere_pas_une_cote_parallele():
    # Deux murs opposes horizontaux, aucune paire perpendiculaire exploitable.
    segments = [(0., 0., 8., 0.), (8., 3., 0., 3.)]
    pairs = axes.principal_pairs(segments)
    assert len(pairs) == 1
    assert round(pairs[0].distance, 3) == 3.
    assert axes.principal_reference_indexes(segments) == {0, 1}


def test_pas_de_paire_de_faces_pas_de_cotation():
    assert axes.principal_pairs([(0., 0., 5., 0.)]) == []
    assert axes.principal_reference_indexes([(0., 0., 5., 0.)]) == set()


def test_adaptateur_nutilise_pas_longueur_mur_de_secours():
    path = (LIB.parent / "OutilsTAA.tab" / "Annotations.panel" /
            "services" / "annotations_service.py")
    source = path.read_text(encoding="utf-8")
    import ast
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "GenericDimensions")
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_fallback_length_indexes")
    # Retourne une liste vide, independamment du nombre de paires initiales.
    assert len(method.body) == 1
    assert isinstance(method.body[0], ast.Return)
    assert isinstance(method.body[0].value, ast.List)
    assert len(method.body[0].value.elts) == 0
