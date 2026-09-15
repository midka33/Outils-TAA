# -*- coding: utf-8 -*-
"""Sélection des carnets publiables pour un dossier Export."""


class PublicationFolderTargetService(object):
    """Détermine les carnets rattachés à un dossier et à ses sous-dossiers."""

    @staticmethod
    def get_descendant_folder_ids(folders, root_folder_id):
        """Retourne l'identifiant du dossier racine et ceux de ses descendants."""
        folder_ids = set([root_folder_id])
        changed = True
        while changed:
            changed = False
            for folder in folders or []:
                parent_id = getattr(folder, "parent_id", None)
                folder_id = getattr(folder, "id", None)
                if folder_id in folder_ids:
                    continue
                if parent_id in folder_ids:
                    folder_ids.add(folder_id)
                    changed = True
        return folder_ids

    @classmethod
    def get_targets(cls, folders, carnets, root_folder_id):
        """Retourne les carnets du dossier et de tous ses sous-dossiers.

        L'ordre fourni par ``carnets`` est volontairement conservé afin de ne
        pas modifier l'ordre manuel défini dans l'arborescence de publication.
        Le filtrage par projet courant est réalisé en amont par ExportWindow.
        """
        folder_ids = cls.get_descendant_folder_ids(folders, root_folder_id)
        return [
            carnet for carnet in (carnets or [])
            if getattr(carnet, "folder_id", None) in folder_ids
        ]
