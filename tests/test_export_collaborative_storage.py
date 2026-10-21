# -*- coding: utf-8 -*-
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SERVICES = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Export.panel",
    "services",
)
if SERVICES not in sys.path:
    sys.path.insert(0, SERVICES)

from project_storage_resolver import (
    ProjectStorageResolver,
    StoragePaths,
    canonicalize_windows_path,
    central_project_identity,
    shared_paths_from_central,
)


class FakeDocument(object):
    def __init__(self, is_workshared, central=None, path_name=""):
        self.IsWorkshared = is_workshared
        self._central = central
        self.PathName = path_name

    def GetWorksharingCentralModelPath(self):
        return self._central


def identity_converter(value):
    return value


def test_unc_central_resolves_shared_export_json():
    doc = FakeDocument(
        True,
        central=r"\\SERVEUR\PROJETS\PROJET_A\Projet_Central.rvt",
        path_name=r"C:\Users\Alice\Projet_Central_Alice.rvt",
    )
    resolver = ProjectStorageResolver(
        model_path_converter=identity_converter
    )

    result = resolver.resolve(doc, r"C:\Local\fallback.json")

    assert result.mode == StoragePaths.MODE_SHARED
    assert result.central_path == (
        r"\\SERVEUR\PROJETS\PROJET_A\Projet_Central.rvt"
    )
    assert result.shared_config_path == (
        r"\\SERVEUR\PROJETS\PROJET_A\OutilsTAA\export.json"
    )
    assert result.shared_lock_path.endswith(r"OutilsTAA\export.lock")
    assert result.shared_backups_path.endswith(r"OutilsTAA\backups")
    assert result.local_config_path == r"C:\Local\fallback.json"


def test_local_copy_path_does_not_change_shared_storage():
    first = FakeDocument(
        True,
        central=r"\\SERVEUR\P\A\Central.rvt",
        path_name=r"C:\Users\Alice\Central_Alice.rvt",
    )
    second = FakeDocument(
        True,
        central=r"\\SERVEUR\P\A\Central.rvt",
        path_name=r"D:\RevitLocal\Central_Bob.rvt",
    )
    resolver = ProjectStorageResolver(
        model_path_converter=identity_converter
    )

    left = resolver.resolve(first, r"C:\A.json")
    right = resolver.resolve(second, r"C:\B.json")

    assert left.shared_config_path == right.shared_config_path
    assert left.project_identity == right.project_identity


def test_mapped_drive_is_canonicalized_to_unc_when_registry_mapping_exists():
    mapping = {"P": r"\\SERVEUR\PROJETS"}

    path = canonicalize_windows_path(
        r"P:\PROJET_A\Projet_Central.rvt",
        mapped_drive_resolver=lambda letter: mapping.get(letter),
    )

    assert path == r"\\SERVEUR\PROJETS\PROJET_A\Projet_Central.rvt"


def test_mapped_drive_and_unc_produce_same_project_identity():
    mapping = {"P": r"\\SERVEUR\PROJETS"}
    mapped = canonicalize_windows_path(
        r"P:\PROJET_A\Central.rvt",
        mapped_drive_resolver=lambda letter: mapping.get(letter),
    )
    unc = canonicalize_windows_path(
        r"\\SERVEUR\PROJETS\PROJET_A\Central.rvt"
    )

    assert central_project_identity(mapped) == central_project_identity(unc)


def test_non_workshared_document_uses_local_fallback():
    resolver = ProjectStorageResolver(
        model_path_converter=identity_converter
    )
    result = resolver.resolve(
        FakeDocument(False, central=None, path_name=r"C:\Projet\A.rvt"),
        r"C:\Local\A.json",
    )

    assert result.mode == StoragePaths.MODE_LOCAL
    assert not result.uses_shared_storage
    assert result.shared_config_path is None
    assert result.local_config_path == r"C:\Local\A.json"


def test_detached_or_missing_central_uses_local_fallback():
    resolver = ProjectStorageResolver(
        model_path_converter=identity_converter
    )
    result = resolver.resolve(
        FakeDocument(True, central=None),
        r"C:\Local\detached.json",
    )

    assert result.mode == StoragePaths.MODE_LOCAL
    assert result.shared_config_path is None


def test_converter_failure_uses_local_fallback():
    def broken(_):
        raise RuntimeError("conversion impossible")

    resolver = ProjectStorageResolver(model_path_converter=broken)
    result = resolver.resolve(
        FakeDocument(True, central="model-path"),
        r"C:\Local\fallback.json",
    )

    assert result.mode == StoragePaths.MODE_LOCAL


def test_different_central_files_keep_distinct_identities_even_same_folder():
    first = central_project_identity(
        r"\\SERVEUR\P\Projet\Central_A.rvt"
    )
    second = central_project_identity(
        r"\\SERVEUR\P\Projet\Central_B.rvt"
    )

    assert first != second


def test_shared_paths_are_derived_with_ntpath_cross_platform():
    paths = shared_paths_from_central(
        r"\\SERVEUR\P\Projet\Central.rvt"
    )

    assert paths["root"] == r"\\SERVEUR\P\Projet\OutilsTAA"
    assert paths["config"] == (
        r"\\SERVEUR\P\Projet\OutilsTAA\export.json"
    )


def test_path_identity_is_case_insensitive_like_windows():
    upper = central_project_identity(
        r"\\SERVEUR\PROJETS\Projet\Central.rvt"
    )
    lower = central_project_identity(
        r"\\serveur\projets\projet\central.rvt"
    )

    assert upper == lower
