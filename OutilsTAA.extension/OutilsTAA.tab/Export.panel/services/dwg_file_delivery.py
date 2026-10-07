# -*- coding: utf-8 -*-
"""Livraison contrôlée des DWG natifs sous les noms TAA attendus."""
from __future__ import unicode_literals

import os
import re
import shutil
import tempfile
import unicodedata


def _text(value):
    try:
        return unicode(value)
    except NameError:
        return str(value)


def _key(value):
    value = _text(value or "")
    try:
        value = unicodedata.normalize("NFKD", value)
    except Exception:
        pass
    return "".join(ch.lower() for ch in value if ch.isalnum())


def validate_dwg_names(names):
    """Refuse les noms Windows invalides et les collisions avant export."""
    seen = set()
    for name in names or []:
        if (not name or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
                or name.rstrip(". ") != name
                or not name.lower().endswith(".dwg")):
            raise ValueError("Nom DWG non valide : {0}".format(name))
        stem = name.split(".")[0].upper()
        if stem in ("CON", "PRN", "AUX", "NUL") or re.match(
                r"^(COM[1-9]|LPT[1-9])$", stem):
            raise ValueError("Nom DWG réservé par Windows : {0}".format(name))
        normalized = name.lower()
        if normalized in seen:
            raise ValueError(
                "Collision de noms DWG : {0}. Ajustez le modèle de nommage."
                .format(name)
            )
        seen.add(normalized)


def _primary_candidates(staging):
    return [
        name for name in os.listdir(staging)
        if os.path.isfile(os.path.join(staging, name))
        and name.lower().endswith(".dwg")
    ]


def reconcile_native_dwgs(staging, items):
    """Associe chaque feuille à son DWG natif sans dépendre du mot « Feuille ».

    Revit ajoute son propre préfixe/libellé au nom des DWG d'un lot. On utilise
    donc le numéro de feuille, puis le nom de feuille comme désambiguïsation.
    Une association ambiguë échoue explicitement au lieu de renommer au hasard.
    """
    actual = _primary_candidates(staging)
    used = set()
    matched = []

    for item in items or []:
        number_key = _key(getattr(item, "sheet_number", None))
        name_key = _key(getattr(item, "sheet_name", None))
        if not number_key:
            raise RuntimeError(
                "DWG : numéro de feuille indisponible pour le rapprochement."
            )

        candidates = [
            name for name in actual
            if name not in used and number_key in _key(os.path.splitext(name)[0])
        ]

        if len(candidates) > 1 and name_key:
            narrowed = [
                name for name in candidates
                if name_key in _key(os.path.splitext(name)[0])
            ]
            if narrowed:
                candidates = narrowed

        if len(candidates) != 1:
            raise RuntimeError(
                "Impossible d'associer le DWG natif à la feuille {0} — {1}. "
                "Candidats : {2}.".format(
                    getattr(item, "sheet_number", "") or "sans numéro",
                    getattr(item, "sheet_name", "") or "sans nom",
                    ", ".join(sorted(candidates)) or "aucun",
                )
            )

        used.add(candidates[0])
        matched.append(candidates[0])

    return matched


def _backup_destination(destination, backup_dir, backups):
    if not os.path.exists(destination):
        return
    if not os.path.isfile(destination):
        raise RuntimeError(
            "La destination DWG n'est pas un fichier : {0}".format(destination)
        )
    backup = os.path.join(backup_dir, str(len(backups)) + ".bak")
    os.rename(destination, backup)
    backups.append((backup, destination))


def deliver_named_dwgs(output_directory, items, target_names, export_callback,
                        progress_callback=None):
    """Exporte un lot une fois, puis renomme/livre chaque DWG avec rollback.

    Les fichiers auxiliaires non identifiés comme DWG principaux (XRefs, PNG,
    JPG...) sont également livrés dans le dossier DWG du carnet.
    """
    items = list(items or [])
    target_names = list(target_names or [])
    if not items or len(items) != len(target_names):
        raise ValueError("Correspondance feuilles/noms DWG invalide.")
    validate_dwg_names(target_names)

    staging = tempfile.mkdtemp(prefix=".taa-dwg-", dir=output_directory)
    backup_dir = tempfile.mkdtemp(prefix=".taa-dwg-backup-", dir=output_directory)
    moved = []
    backups = []

    try:
        if not export_callback(staging):
            raise RuntimeError("Revit a retourné False pour l'export DWG.")

        source_names = reconcile_native_dwgs(staging, items)
        source_set = set(source_names)
        delivered = []

        for index, (item, source_name, target_name) in enumerate(
                zip(items, source_names, target_names), 1):
            source = os.path.join(staging, source_name)
            destination = os.path.join(output_directory, target_name)
            if not os.path.isfile(source) or os.path.getsize(source) == 0:
                raise RuntimeError(
                    "DWG attendu absent ou vide : {0}".format(source_name)
                )
            _backup_destination(destination, backup_dir, backups)
            os.rename(source, destination)
            moved.append((destination, source))
            delivered.append(destination)
            if progress_callback is not None:
                progress_callback(index, len(items), item, destination)

        auxiliary = []
        for name in list(os.listdir(staging)):
            if name in source_set:
                continue
            source = os.path.join(staging, name)
            if not os.path.isfile(source):
                continue
            destination = os.path.join(output_directory, name)
            _backup_destination(destination, backup_dir, backups)
            os.rename(source, destination)
            moved.append((destination, source))
            auxiliary.append(destination)

    except Exception as exc:
        rollback_errors = []
        for destination, source in reversed(moved):
            try:
                if os.path.exists(destination):
                    os.rename(destination, source)
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        for backup, destination in reversed(backups):
            try:
                if os.path.exists(backup):
                    os.rename(backup, destination)
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        detail = (
            " Restauration incomplète : " + "; ".join(rollback_errors)
            if rollback_errors else ""
        )
        raise RuntimeError(
            "{0}. Fichiers temporaires conservés dans {1}.{2}".format(
                exc, staging, detail
            )
        )

    shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(backup_dir, ignore_errors=True)
    return {"paths": delivered, "auxiliary": auxiliary}
