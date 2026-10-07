# -*- coding: utf-8 -*-
"""Commande native DWG : à poster seulement après la fermeture modale Export."""


def command_id(ui_application):
    from Autodesk.Revit.UI import PostableCommand, RevitCommandId
    command = getattr(PostableCommand, "ExportOptionsExportSetupsDWGOrDXF", None)
    if command is None:
        raise RuntimeError("Cette version de Revit n'expose pas les réglages DWG/DXF.")
    result = RevitCommandId.LookupPostableCommandId(command)
    if result is None or not ui_application.CanPostCommand(result):
        raise RuntimeError("Revit ne permet pas de mettre en attente les réglages DWG/DXF.")
    return result


def post_settings(ui_application):
    # CanPostCommand ne garantit pas que la commande sera disponible plus tard.
    ui_application.PostCommand(command_id(ui_application))
