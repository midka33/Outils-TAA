"""Modèle métier d'un carnet de publication."""


class PublicationSet(object):
    """Conteneur logique d'éléments publiables."""

    def __init__(self, name, items=None, source=None, output_directory=None,
                 filename_template_id=None):
        self.name = name
        self.items = list(items or [])
        self.source = source
        self.output_directory = output_directory
        self.filename_template_id = filename_template_id
