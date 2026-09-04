# -*- coding: utf-8 -*-
"""Gestion des profils de publication du module Export."""

import json
import os


class PublicationProfileService(object):
    """Persiste des profils de réglages techniques de publication."""

    SCHEMA_VERSION = 1

    DEFAULT_PROFILES = {
        "PDF + DWG": {
            "pdf_enabled": True,
            "pdf_mode": "COMBINED",
            "dwg_enabled": True,
            "dwg_mode": "SEPARATE",
            "dwg_setup_name": None,
            "dwg_true_color": True
        },
        "PDF seul": {
            "pdf_enabled": True,
            "pdf_mode": "COMBINED",
            "dwg_enabled": False,
            "dwg_mode": "SEPARATE",
            "dwg_setup_name": None,
            "dwg_true_color": True
        },
        "PDF séparés": {
            "pdf_enabled": True,
            "pdf_mode": "SEPARATE",
            "dwg_enabled": False,
            "dwg_mode": "SEPARATE",
            "dwg_setup_name": None,
            "dwg_true_color": True
        },
        "DWG seul": {
            "pdf_enabled": False,
            "pdf_mode": "COMBINED",
            "dwg_enabled": True,
            "dwg_mode": "SEPARATE",
            "dwg_setup_name": None,
            "dwg_true_color": True
        },
        "PDF + DWG combinés": {
            "pdf_enabled": True,
            "pdf_mode": "COMBINED",
            "dwg_enabled": True,
            "dwg_mode": "COMBINED",
            "dwg_setup_name": None,
            "dwg_true_color": True
        }
    }

    def __init__(self, storage_path=None):
        self.storage_path = storage_path or self._default_storage_path()

    @staticmethod
    def _default_storage_path():
        app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
        directory = os.path.join(app_data, "Outils-TAA", "Export")
        return os.path.join(directory, "publication_profiles.json")

    def list_profiles(self):
        """Retourne les profils intégrés puis les profils personnalisés."""
        data = self._read()
        custom = data.get("profiles", {})
        names = list(self.DEFAULT_PROFILES.keys())
        for name in sorted(custom.keys()):
            if name not in names:
                names.append(name)
        return names

    def get(self, name):
        """Retourne une copie des réglages d'un profil."""
        if not name:
            return None
        if name in self.DEFAULT_PROFILES:
            return dict(self.DEFAULT_PROFILES[name])
        return dict((self._read().get("profiles", {}) or {}).get(name, {})) or None

    def save(self, name, settings):
        """Enregistre un profil personnalisé à partir des réglages courants."""
        name = (name or "").strip()
        if not name:
            raise ValueError("Le nom du profil est obligatoire.")
        if name in self.DEFAULT_PROFILES:
            raise ValueError("Ce nom est réservé à un profil intégré.")

        data = self._read()
        data.setdefault("profiles", {})[name] = self._settings_to_dict(settings)
        self._write(data)
        return name

    def delete(self, name):
        """Supprime uniquement un profil personnalisé."""
        if not name or name in self.DEFAULT_PROFILES:
            return False
        data = self._read()
        profiles = data.setdefault("profiles", {})
        if name not in profiles:
            return False
        del profiles[name]
        self._write(data)
        return True

    @staticmethod
    def _settings_to_dict(settings):
        return {
            "pdf_enabled": bool(settings.pdf_enabled),
            "pdf_mode": settings.pdf_mode,
            "dwg_enabled": bool(settings.dwg_enabled),
            "dwg_mode": settings.dwg_mode,
            "dwg_setup_name": settings.dwg_setup_name,
            "dwg_true_color": bool(settings.dwg_true_color)
        }

    def _read(self):
        if not os.path.exists(self.storage_path):
            return {"schema_version": self.SCHEMA_VERSION, "profiles": {}}
        try:
            with open(self.storage_path, "r") as handle:
                data = json.load(handle)
        except Exception:
            # Un fichier de profils corrompu ne doit pas empêcher Export de démarrer.
            return {"schema_version": self.SCHEMA_VERSION, "profiles": {}}
        if not isinstance(data, dict):
            return {"schema_version": self.SCHEMA_VERSION, "profiles": {}}
        data.setdefault("schema_version", self.SCHEMA_VERSION)
        data.setdefault("profiles", {})
        return data

    def _write(self, data):
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        temporary_path = self.storage_path + ".tmp"
        with open(temporary_path, "w") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rename(temporary_path, self.storage_path)
