# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Journal minimal ecrit et ferme AVANT les appels sensibles Revit.

Ne contient ni chemin de maquette ni données personnelles, uniquement
phase/numero de piece/vues. Un crash natif ne passe pas par except.
"""

import datetime
import os
import tempfile

TRACE_PATH = os.path.join(tempfile.gettempdir(),
                          "OutilsTAA_Annotations_crashtrace.log")


def trace(stage, view="", room="", details=""):
    try:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = u"{} | {} | {} | {} | {}\n".format(
            stamp, stage, view, room, details)
        with open(TRACE_PATH, "ab") as stream:
            stream.write(line.encode("utf-8", "replace"))
            stream.flush()
    except Exception:
        # Aucun echec d'ecriture de journal ne doit interdire
        # le fonctionnement normal de l'extension.
        pass
