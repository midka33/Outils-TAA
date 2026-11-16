# -*- coding: utf-8 -*-
"""Stockage JSON collaboratif sûr pour Export V1.2.

La production cible Revit 2025.4 / IronPython utilise un handle .NET exclusif
sur le partage SMB. Le fallback Python pur existe uniquement pour les tests hors
Revit et les environnements sans System.IO.
"""

import copy
import errno
import getpass
import io
import json
import os
import shutil
import socket
import time
import uuid
from datetime import datetime


class StorageError(Exception):
    pass


class StorageUnavailableError(StorageError):
    pass


class StorageAccessDeniedError(StorageError):
    pass


class StorageCorruptedError(StorageError):
    pass


class StorageLockTimeoutError(StorageError):
    pass


class ConcurrentModificationError(StorageError):
    pass


class ProjectIdentityMismatchError(StorageError):
    pass


def _exception_name(exc):
    try:
        return exc.GetType().FullName
    except Exception:
        return exc.__class__.__name__


def _hresult_code(exc):
    try:
        return int(exc.HResult) & 0xFFFF
    except Exception:
        return None


def _is_access_denied(exc):
    name = _exception_name(exc)
    if "UnauthorizedAccessException" in name:
        return True
    code = getattr(exc, "errno", None)
    return code in (errno.EACCES, errno.EPERM)


def _is_sharing_violation(exc):
    # ERROR_SHARING_VIOLATION / ERROR_LOCK_VIOLATION.
    return _hresult_code(exc) in (32, 33)


def _raise_storage_io(exc, prefix):
    if _is_access_denied(exc):
        raise StorageAccessDeniedError(
            "{} : {}".format(prefix, exc)
        )
    raise StorageUnavailableError(
        "{} : {}".format(prefix, exc)
    )


class _DotNetExclusiveLock(object):
    """Verrou inter-processus/SMB basé sur FileShare.None."""

    def __init__(self, path, timeout_seconds=4.0, retry_seconds=0.10):
        self.path = path
        self.timeout_seconds = float(timeout_seconds)
        self.retry_seconds = float(retry_seconds)
        self._stream = None

    def __enter__(self):
        from System.IO import FileAccess, FileMode, FileShare, FileStream

        directory = os.path.dirname(self.path)
        try:
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de préparer le dossier du verrou Export",
            )

        none_share = getattr(FileShare, "None")
        deadline = time.time() + self.timeout_seconds
        last_exc = None

        while True:
            try:
                self._stream = FileStream(
                    self.path,
                    FileMode.OpenOrCreate,
                    FileAccess.ReadWrite,
                    none_share,
                )
                return self
            except Exception as exc:
                last_exc = exc
                if _is_access_denied(exc):
                    _raise_storage_io(
                        exc,
                        "Accès refusé au verrou de configuration Export",
                    )
                if not _is_sharing_violation(exc):
                    _raise_storage_io(
                        exc,
                        "Impossible d'ouvrir le verrou de configuration Export",
                    )
                if time.time() >= deadline:
                    raise StorageLockTimeoutError(
                        "La configuration Export est déjà en cours de "
                        "modification par un autre utilisateur."
                    )
                time.sleep(self.retry_seconds)

        # Garde le dernier message disponible pour les débogueurs.
        if last_exc is not None:
            raise last_exc

    def __exit__(self, exc_type, exc_value, traceback):
        if self._stream is not None:
            try:
                self._stream.Close()
            finally:
                try:
                    self._stream.Dispose()
                except Exception:
                    pass
                self._stream = None
        return False


class _PortableExclusiveLock(object):
    """Fallback de CI hors .NET.

    Il n'est pas le verrou de production SMB. L'exclusivité de production est
    fournie par _DotNetExclusiveLock.
    """

    def __init__(self, path, timeout_seconds=4.0, retry_seconds=0.05):
        self.path = path
        self.timeout_seconds = float(timeout_seconds)
        self.retry_seconds = float(retry_seconds)
        self._fd = None

    def __enter__(self):
        directory = os.path.dirname(self.path)
        try:
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de préparer le dossier du verrou Export",
            )

        deadline = time.time() + self.timeout_seconds
        while True:
            try:
                self._fd = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                )
                return self
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    if time.time() >= deadline:
                        raise StorageLockTimeoutError(
                            "La configuration Export est déjà en cours de "
                            "modification par un autre utilisateur."
                        )
                    time.sleep(self.retry_seconds)
                    continue
                _raise_storage_io(
                    exc,
                    "Impossible d'ouvrir le verrou de configuration Export",
                )

    def __exit__(self, exc_type, exc_value, traceback):
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None
                try:
                    os.remove(self.path)
                except OSError:
                    pass
        return False


def _has_dotnet_io():
    try:
        from System.IO import FileStream  # noqa: F401
        return True
    except Exception:
        return False


def exclusive_file_lock(path, timeout_seconds=4.0, retry_seconds=0.10):
    """Retourne le verrou approprié à l'environnement courant."""
    if _has_dotnet_io():
        return _DotNetExclusiveLock(
            path,
            timeout_seconds=timeout_seconds,
            retry_seconds=retry_seconds,
        )
    return _PortableExclusiveLock(
        path,
        timeout_seconds=timeout_seconds,
        retry_seconds=retry_seconds,
    )


class SharedJsonStorage(object):
    """Lecture/écriture révisionnée d'un JSON partagé Export."""

    DEFAULT_BACKUP_LIMIT = 20

    def __init__(
            self,
            config_path,
            lock_path,
            backups_path,
            project_identity,
            lock_timeout_seconds=4.0,
            lock_retry_seconds=0.10,
            backup_limit=DEFAULT_BACKUP_LIMIT,
            lock_factory=None):
        if not config_path:
            raise ValueError("Le chemin export.json est obligatoire.")
        if not lock_path:
            raise ValueError("Le chemin export.lock est obligatoire.")
        if not backups_path:
            raise ValueError("Le dossier backups est obligatoire.")
        if not project_identity:
            raise ValueError("L'identité du projet partagé est obligatoire.")

        self.config_path = config_path
        self.lock_path = lock_path
        self.backups_path = backups_path
        self.project_identity = str(project_identity)
        self.lock_timeout_seconds = float(lock_timeout_seconds)
        self.lock_retry_seconds = float(lock_retry_seconds)
        self.backup_limit = max(1, int(backup_limit))
        self.lock_factory = lock_factory or exclusive_file_lock
        self.known_revision = None
        self.known_write_id = None

    def _lock(self):
        return self.lock_factory(
            self.lock_path,
            timeout_seconds=self.lock_timeout_seconds,
            retry_seconds=self.lock_retry_seconds,
        )

    @staticmethod
    def _revision(data):
        if not data:
            return 0
        try:
            value = int(data.get("storage_revision", 0))
        except Exception:
            raise StorageCorruptedError(
                "La révision de la configuration Export est invalide."
            )
        if value < 0:
            raise StorageCorruptedError(
                "La révision de la configuration Export est invalide."
            )
        return value

    def _validate_project_identity(self, data):
        identity = data.get("project_identity")
        if not identity:
            raise ProjectIdentityMismatchError(
                "La configuration partagée ne contient pas d'identité projet."
            )
        if str(identity).lower() != self.project_identity.lower():
            raise ProjectIdentityMismatchError(
                "La configuration partagée appartient à un autre projet."
            )

    def _validate_data(self, data):
        if not isinstance(data, dict):
            raise StorageCorruptedError(
                "Le fichier de configuration Export doit contenir un objet JSON."
            )
        self._validate_project_identity(data)
        self._revision(data)
        return data

    def _read_unlocked(self, allow_missing=True):
        if not os.path.exists(self.config_path):
            if allow_missing:
                return None
            raise StorageUnavailableError(
                "La configuration Export partagée est introuvable."
            )

        try:
            with io.open(self.config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except ValueError as exc:
            raise StorageCorruptedError(
                "La configuration Export partagée contient un JSON invalide : "
                "{}".format(exc)
            )
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de lire la configuration Export partagée",
            )

        return self._validate_data(data)

    def probe_access(self):
        """Vérifie que le dossier partagé est lisible et inscriptible.

        Le probe ne crée ni ne modifie export.json et n'acquiert pas le verrou
        métier. Il écrit uniquement un petit fichier temporaire unique dans le
        même dossier, puis le supprime. Si export.json existe, il est également
        relu et validé afin de ne jamais masquer une corruption ou une identité
        projet différente.
        """
        directory = os.path.dirname(self.config_path)
        probe_path = None
        try:
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)

            probe_name = ".export-access-{}.tmp".format(uuid.uuid4().hex)
            probe_path = os.path.join(directory, probe_name)
            with io.open(probe_path, "w", encoding="utf-8") as handle:
                handle.write("Outils TAA Export access probe")
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except Exception:
                    pass
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Le dossier partagé Outils TAA est inaccessible en écriture",
            )
        finally:
            if probe_path and os.path.exists(probe_path):
                try:
                    os.remove(probe_path)
                except Exception:
                    pass

        data = self._read_unlocked(allow_missing=True)
        self.known_revision = self._revision(data)
        self.known_write_id = (
            data.get("last_write_id") if data is not None else None
        )
        return data

    def read(self):
        """Relit la source partagée et met à jour la révision connue."""
        data = self._read_unlocked(allow_missing=True)
        self.known_revision = self._revision(data)
        self.known_write_id = (
            data.get("last_write_id") if data is not None else None
        )
        return data

    refresh = read

    def has_external_change(self):
        """Indique si le disque porte une révision différente de celle chargée."""
        if self.known_revision is None:
            return False
        data = self._read_unlocked(allow_missing=True)
        return self._revision(data) != self.known_revision

    def _write_temporary(self, payload):
        directory = os.path.dirname(self.config_path)
        try:
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de préparer le dossier de configuration Export",
            )

        temp_name = ".export.{}.tmp".format(uuid.uuid4().hex)
        temp_path = os.path.join(directory, temp_name)

        try:
            with io.open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(
                    payload,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except Exception:
                    pass
        except Exception as exc:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            _raise_storage_io(
                exc,
                "Impossible d'écrire le fichier temporaire Export",
            )

        return temp_path

    def _validate_temporary(self, temp_path):
        try:
            with io.open(temp_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except ValueError as exc:
            raise StorageCorruptedError(
                "Le fichier temporaire Export est invalide : {}".format(exc)
            )
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de relire le fichier temporaire Export",
            )
        self._validate_data(data)
        return data

    def _ensure_backup_directory(self):
        try:
            if not os.path.isdir(self.backups_path):
                os.makedirs(self.backups_path)
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de préparer les sauvegardes Export",
            )

    def _backup_path(self, revision):
        self._ensure_backup_directory()
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name = "export_{}_revision-{}_{}.json".format(
            stamp,
            int(revision),
            uuid.uuid4().hex[:8],
        )
        return os.path.join(self.backups_path, name)

    def _dotnet_replace(self, temp_path, backup_path):
        from System.IO import File
        File.Replace(temp_path, self.config_path, backup_path)

    def _portable_replace(self, temp_path, backup_path):
        shutil.copy2(self.config_path, backup_path)
        replacer = getattr(os, "replace", None)
        if replacer is not None:
            replacer(temp_path, self.config_path)
        else:
            os.rename(temp_path, self.config_path)

    def _replace_existing(self, temp_path, backup_path):
        try:
            if _has_dotnet_io():
                self._dotnet_replace(temp_path, backup_path)
            else:
                self._portable_replace(temp_path, backup_path)
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de remplacer la configuration Export partagée",
            )

    def _move_first_file(self, temp_path):
        try:
            if _has_dotnet_io():
                from System.IO import File
                File.Move(temp_path, self.config_path)
            else:
                os.rename(temp_path, self.config_path)
        except Exception as exc:
            _raise_storage_io(
                exc,
                "Impossible de créer la configuration Export partagée",
            )

    def _rotate_backups(self):
        try:
            if not os.path.isdir(self.backups_path):
                return
            paths = [
                os.path.join(self.backups_path, name)
                for name in os.listdir(self.backups_path)
                if name.startswith("export_") and name.endswith(".json")
            ]
            paths.sort(
                key=lambda path: (
                    os.path.getmtime(path),
                    os.path.basename(path),
                ),
                reverse=True,
            )
            for path in paths[self.backup_limit:]:
                try:
                    os.remove(path)
                except Exception:
                    pass
        except Exception:
            # La rotation ne doit jamais invalider une écriture déjà réussie.
            pass

    @staticmethod
    def _diagnostic_user():
        try:
            return getpass.getuser()
        except Exception:
            return os.environ.get("USERNAME") or ""

    @staticmethod
    def _diagnostic_machine():
        return (
            os.environ.get("COMPUTERNAME")
            or os.environ.get("HOSTNAME")
            or socket.gethostname()
        )

    def _prepare_payload(self, data, next_revision):
        payload = dict(data or {})

        identity = payload.get("project_identity")
        if identity and str(identity).lower() != self.project_identity.lower():
            raise ProjectIdentityMismatchError(
                "La configuration à enregistrer appartient à un autre projet."
            )
        payload["project_identity"] = self.project_identity
        payload["storage_revision"] = int(next_revision)
        payload["last_write_id"] = str(uuid.uuid4())
        payload["last_write_utc"] = datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        payload["last_write_user"] = self._diagnostic_user()
        payload["last_write_machine"] = self._diagnostic_machine()
        return payload

    def mutate(self, mutator, default_factory=None):
        """Applique une mutation sous un seul verrou et contrôle de révision.

        Le callback reçoit une copie modifiable des données les plus récentes et
        doit retourner (changed, result). Si changed est faux, aucune écriture
        ni incrément de révision n'est réalisé.
        """
        if self.known_revision is None:
            raise RuntimeError(
                "La configuration doit être lue avant toute mutation partagée."
            )
        if mutator is None:
            raise ValueError("Le callback de mutation est obligatoire.")

        temp_path = None
        with self._lock():
            current = self._read_unlocked(allow_missing=True)
            current_revision = self._revision(current)

            if current_revision != self.known_revision:
                raise ConcurrentModificationError(
                    "La configuration Export a été modifiée par un autre "
                    "utilisateur. Actualisez avant d'enregistrer."
                )

            if current is None:
                working = (
                    default_factory()
                    if default_factory is not None
                    else {
                        "project_identity": self.project_identity,
                    }
                )
            else:
                working = copy.deepcopy(current)

            changed, result = mutator(working)
            if not changed:
                return result

            payload = self._prepare_payload(
                working,
                current_revision + 1,
            )
            temp_path = self._write_temporary(payload)
            try:
                self._validate_temporary(temp_path)

                if current is None:
                    self._move_first_file(temp_path)
                    temp_path = None
                else:
                    backup_path = self._backup_path(current_revision)
                    self._replace_existing(temp_path, backup_path)
                    temp_path = None
                    self._rotate_backups()
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

            self.known_revision = payload["storage_revision"]
            self.known_write_id = payload["last_write_id"]
            return result

    def write(self, data):
        """Écrit uniquement depuis la révision précédemment lue.

        Appeler read()/refresh() avant la première écriture. Une révision disque
        différente déclenche ConcurrentModificationError sans remplacer le JSON.
        """
        if self.known_revision is None:
            raise RuntimeError(
                "La configuration doit être lue avant toute écriture partagée."
            )

        temp_path = None
        with self._lock():
            current = self._read_unlocked(allow_missing=True)
            current_revision = self._revision(current)

            if current_revision != self.known_revision:
                raise ConcurrentModificationError(
                    "La configuration Export a été modifiée par un autre "
                    "utilisateur. Actualisez avant d'enregistrer."
                )

            payload = self._prepare_payload(
                data,
                current_revision + 1,
            )
            temp_path = self._write_temporary(payload)
            try:
                self._validate_temporary(temp_path)

                if current is None:
                    self._move_first_file(temp_path)
                    temp_path = None
                else:
                    backup_path = self._backup_path(current_revision)
                    self._replace_existing(temp_path, backup_path)
                    temp_path = None
                    self._rotate_backups()
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

            self.known_revision = payload["storage_revision"]
            self.known_write_id = payload["last_write_id"]
            return payload
