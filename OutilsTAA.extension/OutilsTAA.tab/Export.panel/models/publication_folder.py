# -*- coding: utf-8 -*-
"""Modèle métier d'un dossier de publication Export."""


class PublicationFolder(object):
    """Dossier persistant contenant des carnets de publication."""

    def __init__(self, name, folder_id=None, parent_id=None, persistent=True,
                 publication_settings=None):
        self.id = folder_id
        self.name = name
        self.parent_id = parent_id
        self.persistent = persistent
        self.publication_settings = publication_settings
