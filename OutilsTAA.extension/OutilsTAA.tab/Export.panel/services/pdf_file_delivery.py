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
