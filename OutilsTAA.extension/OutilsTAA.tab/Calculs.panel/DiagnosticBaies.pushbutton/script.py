# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""Bouton Diagnostic des baies — lecture seule."""
__title__ = "Diagnostic\ndes baies"
__doc__ = "Analyse les cotes des fenêtres et portes sans modifier le projet. Export CSV."
import os,sys
HERE=os.path.dirname(__file__)
PANEL=os.path.abspath(os.path.join(HERE,".."))
EXT=os.path.abspath(os.path.join(PANEL,"..",".."))
for folder in (os.path.join(EXT,"lib"),os.path.join(PANEL,"services"),os.path.join(PANEL,"ui")):
    if folder not in sys.path:
        sys.path.insert(0,folder)
def main():
    from pyrevit import revit, forms
    from baies_diagnostic_service import BaiesDiagnosticService
    from baies_diagnostic_window import BaiesDiagnosticWindow
    doc=revit.doc
    if doc is None or getattr(doc,"IsFamilyDocument",False):
        forms.alert("Ouvrez un projet Revit et non une famille.",title="Diagnostic des baies",warn_icon=True)
        return
    BaiesDiagnosticWindow(BaiesDiagnosticService(doc)).ShowDialog()
if __name__=="__main__":
    main()
