# -*- coding: utf-8 -*-
from plans_vente.view_grouping import master_view_name, normalize_scale


def test_scale_accepts_plain_or_revit_style_notation():
    assert normalize_scale("50") == 50
    assert normalize_scale("1:50") == 50
    assert normalize_scale(75) == 75


def test_scale_rejects_invalid_values():
    for value in ("", "1:0", "0", "-50", "50.5", "abc", True, "24001"):
        try:
            normalize_scale(value)
        except ValueError:
            pass
        else:
            raise AssertionError("Valeur invalide acceptée: {!r}".format(value))


def test_master_name_is_deterministic_by_level_scale_and_source():
    first = master_view_name("Niveau 0A", 50, "12345678-AAAA-BBBB-CCCC-11223344")
    second = master_view_name("Niveau 0A", "1:50", "12345678-AAAA-BBBB-CCCC-11223344")
    other_scale = master_view_name("Niveau 0A", 100, "12345678-AAAA-BBBB-CCCC-11223344")
    other_source = master_view_name("Niveau 0A", 50, "12345678-AAAA-BBBB-CCCC-55667788")

    assert first == second
    assert first.startswith("PDV MASTER - Niveau 0A - 1-50 - ")
    assert first != other_scale
    assert first != other_source


def test_master_name_sanitizes_level_label():
    value = master_view_name("Niveau [0] / A", 50, "ABCDEF123456")
    assert "[" not in value
    assert "]" not in value
    assert "/" not in value
