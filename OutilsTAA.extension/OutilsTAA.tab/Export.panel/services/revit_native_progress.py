# -*- coding: utf-8 -*-
"""Relais léger de la progression native Revit vers la progression TAA."""
from __future__ import unicode_literals


class RevitNativeProgressBridge(object):
    """Écoute Application.ProgressChanged uniquement pendant un appel Export."""

    def __init__(self, document, progress, phase_key):
        self.document = document
        self.progress = progress
        self.phase_key = phase_key
        self.application = getattr(document, "Application", None)
        self._attached = False
        self._last = None

    def __enter__(self):
        if self.progress is None or self.application is None:
            return self
        try:
            self.application.ProgressChanged += self._handle
            self._attached = True
        except Exception:
            self._attached = False
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._attached:
            try:
                self.application.ProgressChanged -= self._handle
            except Exception:
                pass
        self._attached = False
        return False

    def _handle(self, sender, args):
        """Ne modifie jamais le document ; relaie seulement les données natives."""
        try:
            upper = int(getattr(args, "UpperRange", 0) or 0)
            position = int(getattr(args, "Position", 0) or 0)
            if upper <= 0:
                return
            if position < 0:
                position = 0
            if position > upper:
                position = upper
            caption = getattr(args, "Caption", None) or "Traitement Revit"
            key = (position, upper, str(caption))
            if key == self._last:
                return
            self._last = key
            self.progress.native_progress(
                self.phase_key,
                position,
                upper,
                str(caption),
            )
        except Exception:
            # La télémétrie UI ne doit jamais interrompre Document.Export.
            return
