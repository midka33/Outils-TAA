# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Gestion des préférences locales Outils TAA."""

import codecs
import json
import os


class SettingsStore(object):
    """Interface minimale pour les préférences persistantes."""

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError


class JsonSettingsStore(SettingsStore):
    """Stockage JSON atomique réutilisable pour des préférences locales."""

    def __init__(self, storage_path):
        if not storage_path:
            raise ValueError("Le chemin de stockage est obligatoire.")
        self.storage_path = storage_path

    def get(self, key, default=None):
        return self._read().get(key, default)

    def set(self, key, value):
        data = self._read()
        data[key] = value
        self._write(data)

    def update(self, values):
        data = self._read()
        data.update(dict(values or {}))
        self._write(data)

    def as_dict(self):
        return dict(self._read())

    def replace(self, values):
        self._write(dict(values or {}))

    def _read(self):
        if not os.path.exists(self.storage_path):
            return {}
        try:
            with codecs.open(self.storage_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, data):
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        temporary_path = self.storage_path + ".tmp"
        with codecs.open(temporary_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rename(temporary_path, self.storage_path)
