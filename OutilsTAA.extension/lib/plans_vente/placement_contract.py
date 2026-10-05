# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Contrat métier de placement des artefacts Plans de vente."""


class PlacementRole(object):
    MAIN_VIEW = "MainView"
    LOCATION_VIEW = "LocationView"
    INTERIOR_SCHEDULE = "InteriorSchedule"
    EXTERIOR_SCHEDULE = "ExteriorSchedule"


class PlacementKind(object):
    VIEWPORT = "Viewport"
    SCHEDULE = "Schedule"


class AnchorKey(object):
    MAIN_VIEW = "main_view"
    LOCATION_VIEW = "location_view"
    INTERIOR_SCHEDULE = "interior_schedule"
    EXTERIOR_SCHEDULE = "exterior_schedule"


_ROLE_CONTRACT = {
    PlacementRole.MAIN_VIEW: (PlacementKind.VIEWPORT, AnchorKey.MAIN_VIEW),
    PlacementRole.LOCATION_VIEW: (
        PlacementKind.VIEWPORT,
        AnchorKey.LOCATION_VIEW,
    ),
    PlacementRole.INTERIOR_SCHEDULE: (
        PlacementKind.SCHEDULE,
        AnchorKey.INTERIOR_SCHEDULE,
    ),
    PlacementRole.EXTERIOR_SCHEDULE: (
        PlacementKind.SCHEDULE,
        AnchorKey.EXTERIOR_SCHEDULE,
    ),
}


class PlacementArtifact(object):
    """Référence stable et explicite d'un élément futur à placer."""

    def __init__(
        self,
        housing_key,
        role,
        element_unique_id,
        element_name,
        placement_kind,
        anchor_key,
    ):
        self.housing_key = housing_key or ""
        self.role = role or ""
        self.element_unique_id = element_unique_id or ""
        self.element_name = element_name or ""
        self.placement_kind = placement_kind or ""
        self.anchor_key = anchor_key or ""
        self.validate()

    def validate(self):
        if not self.housing_key:
            raise ValueError("Identifiant logement manquant.")
        if self.role not in _ROLE_CONTRACT:
            raise ValueError("Rôle de placement inconnu : {}".format(self.role or "?"))
        if not self.element_unique_id:
            raise ValueError("UniqueId Revit manquant pour le rôle {}.".format(self.role))
        if not self.element_name:
            raise ValueError("Nom d'élément manquant pour le rôle {}.".format(self.role))

        expected_kind, expected_anchor = _ROLE_CONTRACT[self.role]
        if self.placement_kind != expected_kind:
            raise ValueError(
                "Type de placement incohérent pour {} : {} attendu.".format(
                    self.role,
                    expected_kind,
                )
            )
        if self.anchor_key != expected_anchor:
            raise ValueError(
                "Ancrage incohérent pour {} : {} attendu.".format(
                    self.role,
                    expected_anchor,
                )
            )
        return self


def placement_artifact(housing_key, role, element_unique_id, element_name):
    if role not in _ROLE_CONTRACT:
        raise ValueError("Rôle de placement inconnu : {}".format(role or "?"))

    placement_kind, anchor_key = _ROLE_CONTRACT[role]
    return PlacementArtifact(
        housing_key=housing_key,
        role=role,
        element_unique_id=element_unique_id,
        element_name=element_name,
        placement_kind=placement_kind,
        anchor_key=anchor_key,
    )


class HousingPlacementContract(object):
    """Regroupe les artefacts d'un logement sans coordonnées de feuille."""

    def __init__(self, housing_key, artifacts):
        self.housing_key = housing_key or ""
        self.artifacts = list(artifacts or [])
        self._validate()

    def _validate(self):
        if not self.housing_key:
            raise ValueError("Identifiant logement manquant.")

        seen_roles = set()
        seen_anchors = set()
        for artifact in self.artifacts:
            artifact.validate()
            if artifact.housing_key != self.housing_key:
                raise ValueError(
                    "Un artefact appartient à un autre logement : {}.".format(
                        artifact.housing_key
                    )
                )
            if artifact.role in seen_roles:
                raise ValueError(
                    "Le rôle {} est présent plusieurs fois.".format(artifact.role)
                )
            if artifact.anchor_key in seen_anchors:
                raise ValueError(
                    "L'ancrage {} est présent plusieurs fois.".format(
                        artifact.anchor_key
                    )
                )
            seen_roles.add(artifact.role)
            seen_anchors.add(artifact.anchor_key)

    def by_role(self, role):
        for artifact in self.artifacts:
            if artifact.role == role:
                return artifact
        return None
