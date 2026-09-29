# -*- coding: utf-8 -*-
"""Publication des PDF temporaires sous les noms annoncés dans l'aperçu."""
import os
import re
import shutil
import tempfile


def validate_names(names):
    """Refuse les chemins et collisions Windows avant tout export."""
    seen = set()
    for name in names:
        if (not name or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
                or name.rstrip('. ') != name or not name.lower().endswith('.pdf')):
            raise ValueError("Nom PDF non valide : {0}".format(name))
        stem = name.split('.')[0].upper()
        if stem in ('CON', 'PRN', 'AUX', 'NUL') or re.match(r'^(COM[1-9]|LPT[1-9])$', stem):
            raise ValueError("Nom PDF réservé par Windows : {0}".format(name))
        key = name.lower()
        if key in seen:
            raise ValueError("Collision de noms PDF : {0}. Ajoutez {{numero}} au modèle.".format(name))
        seen.add(key)


def _native_key(name):
    """Clé conservatrice pour comparer les numéros après nettoyage par Revit."""
    stem, ext = os.path.splitext(name)
    if ext.lower() != '.pdf' or not stem.lower().startswith('taa_'):
        return None
    return ''.join(character.lower() for character in stem[4:]
                   if character.isalnum())


def validate_native_keys(source_names):
    """Évite une association ambiguë entre deux numéros après nettoyage."""
    seen = set()
    for name in source_names:
        key = _native_key(name)
        if not key or key in seen:
            raise ValueError("Numéros de feuilles ambigus pour les PDF séparés : {0}".format(name))
        seen.add(key)


def reconcile_native_pdfs(staging, source_names):
    """Retrouve les PDF Revit malgré une substitution des caractères interdits.

    Une correspondance n'est acceptée que si chaque clé est unique et si tous
    les PDF produits ont été attribués à une feuille. L'ordre ne sert jamais.
    """
    validate_names(source_names)
    validate_native_keys(source_names)
    actual = [name for name in os.listdir(staging)
              if os.path.isfile(os.path.join(staging, name)) and name.lower().endswith('.pdf')]
    by_key = {}
    for name in actual:
        key = _native_key(name)
        if not key or key in by_key:
            raise RuntimeError("PDF natifs ambigus : {0}".format(', '.join(sorted(actual))))
        by_key[key] = name
    if len(actual) != len(source_names) or set(by_key) != set(_native_key(name) for name in source_names):
        raise RuntimeError("Impossible d'associer les PDF natifs aux feuilles. "
                           "Attendus : {0} ; produits : {1}".format(
                               ', '.join(source_names), ', '.join(sorted(actual))))
    # Deux phases évitent qu'un renommage ne remplace un autre PDF natif.
    for index, expected in enumerate(source_names):
        actual_name = by_key[_native_key(expected)]
        os.rename(os.path.join(staging, actual_name),
                  os.path.join(staging, '.taa-reconcile-{0}.tmp'.format(index)))
    for index, expected in enumerate(source_names):
        os.rename(os.path.join(staging, '.taa-reconcile-{0}.tmp'.format(index)),
                  os.path.join(staging, expected))


def deliver_named_pdfs(output_directory, source_names, target_names, export_callback):
    """Exporte une fois puis livre les fichiers contrôlés avec restauration sur erreur.

    Le callback reçoit un répertoire neuf. Aucun ordre de fichiers n'est utilisé
    pour deviner l'association feuille/PDF. Les anciens fichiers restent intacts
    tant que tous les PDF attendus ne sont pas effectivement produits.
    """
    if not source_names or len(source_names) != len(target_names):
        raise ValueError("Correspondance feuilles/noms PDF invalide.")
    validate_names(source_names)
    validate_names(target_names)
    staging = tempfile.mkdtemp(prefix='.taa-pdf-', dir=output_directory)
    moved, backups = [], []
    try:
        if not export_callback(staging):
            raise RuntimeError("Revit a retourné False pour l'export PDF séparé.")
        for name in source_names:
            path = os.path.join(staging, name)
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                raise RuntimeError("PDF attendu absent ou vide : {0}".format(name))
        backup_dir = os.path.join(staging, 'backups')
        os.mkdir(backup_dir)
        for index, (source, target) in enumerate(zip(source_names, target_names)):
            destination = os.path.join(output_directory, target)
            if os.path.exists(destination):
                if not os.path.isfile(destination):
                    raise RuntimeError("La destination n'est pas un fichier : {0}".format(destination))
                backup = os.path.join(backup_dir, str(index) + '.pdf')
                os.rename(destination, backup)
                backups.append((backup, destination))
            os.rename(os.path.join(staging, source), destination)
            moved.append((destination, os.path.join(staging, source)))
    except Exception as exc:
        rollback_errors = []
        for destination, source in reversed(moved):
            try:
                os.rename(destination, source)
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        for backup, destination in reversed(backups):
            try:
                os.rename(backup, destination)
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        detail = " Restauration incomplète : " + '; '.join(rollback_errors) if rollback_errors else ''
        raise RuntimeError("{0}. Fichiers temporaires conservés dans {1}.{2}".format(exc, staging, detail))
    # Un problème de nettoyage ne doit pas transformer une livraison réussie en échec.
    shutil.rmtree(staging, ignore_errors=True)
    return [os.path.join(output_directory, name) for name in target_names]
