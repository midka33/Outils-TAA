# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Contrat explicite de la feuille modèle Plans de vente 07B."""


TEMPLATE_MAIN_VIEW_NAME = "PDV_MODELE_VUE"
TEMPLATE_LOCATION_VIEW_NAME = "PDV_MODELE_REPERAGE"
TEMPLATE_INTERIOR_SCHEDULE_NAME = "PDV_MODELE_NOM_INT"
TEMPLATE_EXTERIOR_SCHEDULE_NAME = "PDV_MODELE_NOM_EXT"


ROLE_TO_PLACEHOLDER_NAME = {
    "main_view": TEMPLATE_MAIN_VIEW_NAME,
    "location_view": TEMPLATE_LOCATION_VIEW_NAME,
    "interior_schedule": TEMPLATE_INTERIOR_SCHEDULE_NAME,
    "exterior_schedule": TEMPLATE_EXTERIOR_SCHEDULE_NAME,
}


def required_placeholder_names():
    return dict(ROLE_TO_PLACEHOLDER_NAME)


def role_for_placeholder_name(name):
    value = str(name or "")
    for role, expected_name in ROLE_TO_PLACEHOLDER_NAME.items():
        if value == expected_name:
            return role
    return None
