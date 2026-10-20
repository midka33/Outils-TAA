# -*- coding: utf-8 -*-
"""Résolution du stockage collaboratif Export V1.2.

Ce module reste importable hors Revit afin que les règles de chemin soient
testables en CI. Les imports Revit et Windows sont effectués à la demande.
"""

import ntpath


class StoragePaths(object):
    """Résultat de résolution du stockage Export pour un document."""

    MODE_SHARED = "SHARED"
    MODE_LOCAL = "LOCAL"

    def __init__(
            self,
            mode,
            local_config_path,
            central_path=None,
            project_identity=None,
            shared_config_path=None,
            shared_lock_path=None,
            shared_backups_path=None,
            warning=None):
        self.mode = mode
        self.local_config_path = local_config_path
        self.central_path = central_path
        self.project_identity = project_identity
        self.shared_config_path = shared_config_path
        self.shared_lock_path = shared_lock_path
        self.shared_backups_path = shared_backups_path
        self.warning = warning

    @property
    def uses_shared_storage(self):
        return self.mode == self.MODE_SHARED and bool(self.shared_config_path)


def _registry_mapped_drive(letter):
    """Résout une lettre de lecteur mappée vers son UNC lorsque possible."""
    letter = str(letter or "").strip().rstrip(":").upper()
    if len(letter) != 1:
        return None

    # CPython Windows.
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Network\{}".format(letter),
        )
        try:
            value, _ = winreg.QueryValueEx(key, "RemotePath")
            return str(value) if value else None
        finally:
            winreg.CloseKey(key)
    except Exception:
        pass

    # IronPython / .NET.
    try:
        from Microsoft.Win32 import Registry
        key = Registry.CurrentUser.OpenSubKey(
            r"Network\{}".format(letter)
        )
        if key is None:
            return None
        try:
            value = key.GetValue("RemotePath")
            return str(value) if value else None
        finally:
            key.Close()
    except Exception:
        return None


def canonicalize_windows_path(path, mapped_drive_resolver=None):
    """Normalise un chemin Windows et favorise un UNC pour un lecteur mappé."""
    if not path:
        return None

    value = str(path).strip().replace("/", "\\")
    if not value:
        return None

    value = ntpath.normpath(value)

    # Un UNC reste un UNC.
    if value.startswith("\\\\"):
        return value

    drive, tail = ntpath.splitdrive(value)
    if drive and len(drive) >= 2 and drive[1] == ":":
        resolver = mapped_drive_resolver or _registry_mapped_drive
        try:
            remote = resolver(drive[0])
        except Exception:
            remote = None
        if remote:
            remote = ntpath.normpath(str(remote).replace("/", "\\"))
            return ntpath.normpath(
                remote.rstrip("\\") + "\\" + tail.lstrip("\\")
            )

    return value


def central_project_identity(central_path):
    """Construit l'identité commune à toutes les copies locales du central."""
    canonical = canonicalize_windows_path(central_path)
    if not canonical:
        return None
    return "CENTRAL:" + ntpath.normcase(canonical)


def shared_paths_from_central(central_path):
    """Dérive les chemins OutilsTAA à côté du fichier central."""
    canonical = canonicalize_windows_path(central_path)
    if not canonical:
        return None

    directory = ntpath.dirname(canonical)
    if not directory:
        return None

    root = ntpath.join(directory, "OutilsTAA")
    return {
        "root": root,
        "config": ntpath.join(root, "export.json"),
        "lock": ntpath.join(root, "export.lock"),
        "backups": ntpath.join(root, "backups"),
    }


def _default_model_path_converter(model_path):
    from Autodesk.Revit.DB import ModelPathUtils
    return ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)


def get_central_user_visible_path(
        document,
        model_path_converter=None,
        mapped_drive_resolver=None):
    """Retourne le chemin central Windows canonique, sinon None."""
    if document is None:
        return None

    try:
        is_workshared = getattr(document, "IsWorkshared")
    except Exception:
        is_workshared = None

    if is_workshared is False:
        return None

    try:
        model_path = document.GetWorksharingCentralModelPath()
    except Exception:
        return None

    if not model_path:
        return None

    converter = model_path_converter or _default_model_path_converter
    try:
        visible = converter(model_path)
    except Exception:
        return None

    return canonicalize_windows_path(
        visible,
        mapped_drive_resolver=mapped_drive_resolver,
    )


class ProjectStorageResolver(object):
    """Résout stockage partagé préféré et stockage local de secours."""

    def __init__(self, model_path_converter=None, mapped_drive_resolver=None):
        self.model_path_converter = model_path_converter
        self.mapped_drive_resolver = mapped_drive_resolver

    def resolve(self, document, local_config_path):
        if not local_config_path:
            raise ValueError("Le chemin local de secours est obligatoire.")

        central = get_central_user_visible_path(
            document,
            model_path_converter=self.model_path_converter,
            mapped_drive_resolver=self.mapped_drive_resolver,
        )

        if not central:
            return StoragePaths(
                StoragePaths.MODE_LOCAL,
                local_config_path=local_config_path,
                warning=(
                    "Aucun modèle central Windows exploitable : "
                    "configuration Export locale."
                ),
            )

        paths = shared_paths_from_central(central)
        if paths is None:
            return StoragePaths(
                StoragePaths.MODE_LOCAL,
                local_config_path=local_config_path,
                warning=(
                    "Chemin du modèle central inexploitable : "
                    "configuration Export locale."
                ),
            )

        return StoragePaths(
            StoragePaths.MODE_SHARED,
            local_config_path=local_config_path,
            central_path=central,
            project_identity=central_project_identity(central),
            shared_config_path=paths["config"],
            shared_lock_path=paths["lock"],
            shared_backups_path=paths["backups"],
        )
