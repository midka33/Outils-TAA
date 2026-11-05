# -*- coding: utf-8 -*-
"""Charge le Theme.xaml EXISTANT de l'extension avant affichage WPF."""
import os


def apply_theme(window):
    from System import Uri, UriKind
    from System.Windows import ResourceDictionary
    from System.Windows.Media import FontFamily
    # services/ -> Giration.panel/ -> OutilsTAA.tab/ -> OutilsTAA.extension/
    extension = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              '..', '..', '..'))
    path = os.path.join(extension, 'resources', 'ui', 'Theme.xaml')
    if not os.path.isfile(path):
        raise IOError('Theme Outils TAA introuvable: ' + path)
    theme = ResourceDictionary()
    theme.Source = Uri(os.path.abspath(path), UriKind.Absolute)
    window.Resources.MergedDictionaries.Add(theme)
    window.FontFamily = FontFamily('Segoe UI')
    window.FontSize = 13
    window.Background = theme['TaaBackground']
    window.Foreground = theme['TaaText']
