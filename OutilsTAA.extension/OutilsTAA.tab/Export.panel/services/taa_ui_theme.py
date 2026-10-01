# -*- coding: utf-8 -*-
"""Charge le thème commun après le XAML et avant l'affichage de la fenêtre."""
import os


def apply_theme(window):
    """Charge par chemin absolu pour ne pas dépendre du répertoire de pyRevit."""
    from System import Uri, UriKind
    from System.Windows import ResourceDictionary
    from System.Windows.Media import FontFamily
    path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "..", "..", "..", "resources", "ui", "Theme.xaml"))
    theme = ResourceDictionary()
    theme.Source = Uri(path, UriKind.Absolute)
    window.Resources.MergedDictionaries.Add(theme)
    window.FontFamily = FontFamily("Segoe UI")
    window.FontSize = 13
    window.Background = theme["TaaBackground"]
    window.Foreground = theme["TaaText"]
    window.UseLayoutRounding = True
