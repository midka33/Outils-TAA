# -*- coding: utf-8 -*-
"""Résumé du périmètre configuré, indépendant de WPF et du moteur Revit."""


def formats_for(settings):
    return [name for name, enabled in (("PDF", settings.pdf_enabled),
                                       ("DWG", settings.dwg_enabled)) if enabled]


def summarize_publication(targets, resolve_settings, selected_item=None):
    """Compte les occurrences prévues ; l'aperçu valide ensuite les feuilles."""
    count = 0
    formats = set()
    qualities = set()
    inactive = 0
    for target in targets:
        settings = resolve_settings(target)
        size = 1 if selected_item is not None else len(target.items or [])
        active = formats_for(settings)
        if not active:
            inactive += size
            continue
        count += size
        formats.update(active)
        if settings.pdf_enabled:
            qualities.add(settings.pdf_quality)
    text = "{0} carnet(s) | {1} mise(s) en page prévue(s) | {2}".format(
        len(targets), count, " + ".join(f for f in ("PDF", "DWG") if f in formats) or "Aucun format activé")
    if qualities:
        text += " | PDF : {0} DPI".format(" / ".join(str(q) for q in sorted(qualities)))
    if inactive:
        text += " | {0} sans format activé".format(inactive)
    return text
