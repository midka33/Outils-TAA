"""Accès Revit centralisé.

Les modules métier doivent privilégier ces adaptateurs plutôt que de disperser
les appels à l'API Revit dans l'interface utilisateur.
"""


def get_active_document(uiapp):
    """Retourne le document Revit actif."""
    if uiapp is None:
        raise ValueError("UIApp Revit manquant.")
    return uiapp.ActiveUIDocument.Document
