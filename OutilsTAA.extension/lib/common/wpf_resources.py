# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Chargement de ResourceDictionary WPF communs."""


def load_resource_dictionary(window, xaml_path):
    """Charge un dictionnaire XAML externe dans une fenêtre WPF."""
    if window is None:
        raise ValueError("Fenêtre WPF manquante.")
    if not xaml_path:
        raise ValueError("Chemin du ResourceDictionary manquant.")

    from System.IO import FileAccess, FileMode, FileStream
    from System.Windows.Markup import XamlReader

    stream = FileStream(xaml_path, FileMode.Open, FileAccess.Read)
    try:
        resource_dictionary = XamlReader.Load(stream)
    finally:
        stream.Close()

    window.Resources.MergedDictionaries.Add(resource_dictionary)
    return resource_dictionary
