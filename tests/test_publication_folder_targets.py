# -*- coding: utf-8 -*-
"""Tests de résolution des carnets associés à un dossier Export."""

from __future__ import print_function

from publication_folder_targets import PublicationFolderTargetService


class _Folder(object):
    def __init__(self, folder_id, parent_id=None):
        self.id = folder_id
        self.parent_id = parent_id


class _Carnet(object):
    def __init__(self, name, folder_id):
        self.name = name
        self.folder_id = folder_id


def test_folder_targets_include_root_folder():
    folders = [_Folder("A")]
    carnets = [_Carnet("Carnet A", "A"), _Carnet("Carnet B", "B")]

    result = PublicationFolderTargetService.get_targets(folders, carnets, "A")

    assert [item.name for item in result] == ["Carnet A"]


def test_folder_targets_include_descendant_folders():
    folders = [
        _Folder("ROOT"),
        _Folder("CHILD", "ROOT"),
        _Folder("GRANDCHILD", "CHILD"),
        _Folder("OTHER"),
    ]
    carnets = [
        _Carnet("A", "ROOT"),
        _Carnet("B", "OTHER"),
        _Carnet("C", "CHILD"),
        _Carnet("D", "GRANDCHILD"),
    ]

    result = PublicationFolderTargetService.get_targets(folders, carnets, "ROOT")

    assert [item.name for item in result] == ["A", "C", "D"]


def test_folder_targets_preserve_carnet_order():
    folders = [_Folder("ROOT"), _Folder("CHILD", "ROOT")]
    carnets = [
        _Carnet("C", "CHILD"),
        _Carnet("A", "ROOT"),
        _Carnet("B", "CHILD"),
    ]

    result = PublicationFolderTargetService.get_targets(folders, carnets, "ROOT")

    assert [item.name for item in result] == ["C", "A", "B"]
