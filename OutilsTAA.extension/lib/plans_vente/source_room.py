# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Read-only source context. Geometry exposed to V1 engines is in host coordinates.

The underlying Revit element and references always remain in source coordinates.
No document, element id or transform is serialized; context lives for one analysis.
"""


def element_id_value(value):
    number = getattr(value, 'Value', None)
    return int(number if number is not None else value.IntegerValue)


def point_to_host(point, transform):
    return transform.OfPoint(point) if transform is not None else point


def point_to_source(point, transform):
    return transform.Inverse.OfPoint(point) if transform is not None else point


def curve_to_host(curve, transform):
    return curve.CreateTransformed(transform) if transform is not None else curve


def bounds_to_host(bounds, transform, xyz_factory):
    """Transform all eight corners, including the bounding box's own frame."""
    points = [point_to_host(point_to_host(xyz_factory(x, y, z),
                                        getattr(bounds, 'Transform', None)), transform)
              for x in (bounds.Min.X, bounds.Max.X)
              for y in (bounds.Min.Y, bounds.Max.Y)
              for z in (bounds.Min.Z, bounds.Max.Z)]
    return (xyz_factory(min(p.X for p in points), min(p.Y for p in points), min(p.Z for p in points)),
            xyz_factory(max(p.X for p in points), max(p.Y for p in points), max(p.Z for p in points)))


class _Values(object):
    def __init__(self, **values):
        self.__dict__.update(values)


class _HostBoundarySegment(object):
    def __init__(self, segment, transform):
        self._segment = segment
        self._transform = transform

    def GetCurve(self):
        return curve_to_host(self._segment.GetCurve(), self._transform)

    def __getattr__(self, name):
        return getattr(self._segment, name)


class SourceRoom(object):
    """An instance-specific room, never passed as a Revit Element argument."""
    def __init__(self, source_document, room_element, link_instance=None,
                 transform_to_host=None, source_name='Fichier actif'):
        self.source_document = source_document
        self.room_element = room_element
        self.room_unique_id = str(room_element.UniqueId)
        self.revit_link_instance = link_instance
        self.link_instance_unique_id = str(link_instance.UniqueId) if link_instance is not None else ''
        self.source_kind = 'linked' if link_instance is not None else 'host'
        self.source_key = self.link_instance_unique_id or 'HOST'
        self.source_name = source_name
        self.transform_to_host = transform_to_host
        self._inverse_transform = transform_to_host.Inverse if transform_to_host is not None else None
        self._host_level = None
        self.output_suffix = '-L{}'.format(element_id_value(link_instance.Id)) if link_instance is not None else ''

    @property
    def identity(self):
        return (self.source_key, self.room_unique_id)

    @property
    def UniqueId(self):
        # Revit UniqueIds cannot contain '|'. This key is not a Revit UniqueId.
        if self.revit_link_instance is None:
            return self.room_unique_id
        return 'LINK|{}|{}'.format(self.link_instance_unique_id, self.room_unique_id)

    @property
    def Location(self):
        location = getattr(self.room_element, 'Location', None)
        point = getattr(location, 'Point', None)
        return _Values(Point=point_to_host(point, self.transform_to_host)) if point is not None else location

    @property
    def Level(self):
        if self._host_level is not None:
            return self._host_level
        level = self.room_element.Level
        if level is None or self.transform_to_host is None:
            return level
        from Autodesk.Revit.DB import XYZ
        elevation = point_to_host(XYZ(0, 0, level.ProjectElevation), self.transform_to_host).Z
        self._host_level = _Values(Name=level.Name, Elevation=elevation, ProjectElevation=elevation, Id=level.Id)
        return self._host_level

    def GetBoundarySegments(self, options):
        return [[_HostBoundarySegment(segment, self.transform_to_host) for segment in loop]
                for loop in self.room_element.GetBoundarySegments(options) or []]

    def IsPointInRoom(self, point):
        return self.room_element.IsPointInRoom(point_to_host(point, self._inverse_transform))

    def get_BoundingBox(self, view):
        from Autodesk.Revit.DB import BoundingBoxXYZ, XYZ
        bounds = self.room_element.get_BoundingBox(None)
        if bounds is None:
            return None
        result = BoundingBoxXYZ()
        result.Min, result.Max = bounds_to_host(bounds, self.transform_to_host, XYZ)
        return result

    def tag_id(self, link_element_id):
        if self.revit_link_instance is not None:
            return link_element_id(self.revit_link_instance.Id, self.room_element.Id)
        return link_element_id(self.room_element.Id)

    def __getattr__(self, name):
        return getattr(self.room_element, name)


def room_inputs(housing):
    """Preserve V1 strings for host rooms; pass explicit objects for linked rooms."""
    snapshots = getattr(housing, 'rooms', None)
    if snapshots is None:
        return housing.room_unique_ids
    return [getattr(r, 'source_room', None) or r.unique_id for r in snapshots]


def resolve_room(document, value):
    if isinstance(value, SourceRoom):
        if not getattr(value.room_element, 'IsValidObject', True):
            raise ValueError('{} : pièce devenue indisponible ; relancer l’analyse.'.format(value.source_name))
        return value
    return document.GetElement(value)


AUTO_HOST_LEVEL_PREFIX = 'PDV_AUTO_'
HOST_LEVEL_TOLERANCE = 1.0 / 304.8


def _auto_host_level_name(elevation):
    """Nom stable des niveaux techniques créés dans le document SITE."""
    return '{}{:+07.3f}'.format(
        AUTO_HOST_LEVEL_PREFIX,
        float(elevation) * 0.3048,
    )


def _unique_host_level_name(levels, elevation):
    base = _auto_host_level_name(elevation)
    existing = set(
        str(getattr(level, 'Name', '') or '')
        for level in levels or []
    )
    if base not in existing:
        return base

    index = 2
    while True:
        candidate = '{} ({})'.format(base, index)
        if candidate not in existing:
            return candidate
        index += 1


def _create_host_level(document, levels, elevation):
    """Crée le niveau SITE manquant à l'altitude transformée du lien."""
    from Autodesk.Revit.DB import Level, Transaction

    def create_level():
        level = Level.Create(document, elevation)
        if level is None:
            raise RuntimeError(
                "Revit n'a pas retourné le niveau SITE créé."
            )
        level.Name = _unique_host_level_name(levels, elevation)
        return level

    if bool(getattr(document, 'IsModifiable', False)):
        return create_level()

    transaction = Transaction(
        document,
        'Plans de vente - Création niveau SITE',
    )
    transaction.Start()
    try:
        level = create_level()
        transaction.Commit()
        return level
    except Exception:
        try:
            transaction.RollBack()
        except Exception:
            pass
        raise


def host_level_name(housing, document):
    """Résout le niveau hôte par altitude et crée automatiquement le niveau absent."""
    sources = [r.source_room for r in getattr(housing, 'rooms', [])
               if getattr(r, 'source_room', None) is not None and r.source_room.source_kind == 'linked']
    if not sources:
        return None

    from Autodesk.Revit.DB import FilteredElementCollector, Level

    elevations = [r.Level.ProjectElevation for r in sources if r.Level is not None]
    if not elevations or max(elevations) - min(elevations) > HOST_LEVEL_TOLERANCE:
        raise ValueError('{} : sélectionner un seul niveau source.'.format(housing.source_name))

    target_elevation = elevations[0]
    levels = list(FilteredElementCollector(document).OfClass(Level).ToElements())
    matches = [
        level for level in levels
        if abs(level.ProjectElevation - target_elevation) <= HOST_LEVEL_TOLERANCE
    ]

    if len(matches) > 1:
        names = ', '.join(
            sorted(str(getattr(level, 'Name', '') or '?') for level in matches)
        )
        raise ValueError(
            '{} / logement {} : plusieurs niveaux SITE existent à {:.3f} m ({}) ; '
            'conserver un seul niveau à cette altitude avant génération.'.format(
                housing.source_name,
                housing.filter_key,
                target_elevation * 0.3048,
                names,
            )
        )

    if len(matches) == 1:
        return str(matches[0].Name)

    level = _create_host_level(
        document,
        levels,
        target_elevation,
    )
    return str(level.Name)
